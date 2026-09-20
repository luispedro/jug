import jug.jug
import jug.task
from jug.task import Task
from jug.tests.utils import simple_execute
from jug.backends.dict_store import dict_store
from jug.options import parse
from .task_reset import task_reset_at_exit, task_reset
from .utils import find_test_jugfile
import pytest

import random
jug.jug.silent = True


@task_reset
def test_jug_execute_simple():
    N = 1024
    random.seed(232)
    A = [False for i in range(N)]
    def setAi(i):
        A[i] = True
    setall = [Task(setAi, i) for i in range(N)]
    store = dict_store()
    jug.task.Task.store = store
    simple_execute()
    assert False not in A
    assert max(store.counts.values()) < 4

@task_reset
def test_jug_execute_deps():
    N = 256
    random.seed(234)
    A = [False for i in range(N)]
    def setAi(i, other):
        A[i] = True
    idxs = list(range(N))
    random.shuffle(idxs)
    prev = None
    for idx in idxs:
        prev = Task(setAi, idx, prev)
    store = dict_store()
    jug.task.Task.store = store
    simple_execute()
    assert False not in A
    assert max(store.counts.values()) < 5

@pytest.mark.parametrize('jugfile',
      ['tasklet_simple.py',
      'tasklets.py',
      'barrier_mapreduce.py',
      'compound_nonsimple.py',
      'slice_task.py'])
def test_aggressive_unload(jugfile):
    from jug.jug import execution_loop
    from jug.task import alltasks

    options = parse(['execute'])
    options.aggressive_unload = True
    options.execute_name = None
    options.execute_pattern = None
    store, space = jug.jug.init(find_test_jugfile(jugfile), 'dict_store')
    execution_loop(alltasks, options)

@task_reset
def test_target_exact():
    from jug.jug import execution_loop
    from jug.task import alltasks
    options = parse(['execute'])
    options.jugfile = find_test_jugfile('simple.py')
    # Test if restricting to this target we skip the other tasks
    options.execute_name = "simple.double"

    store, space = jug.jug.init(options.jugfile, 'dict_store')
    execution_loop(alltasks, options)

    assert len(store.store) < len(alltasks)
    assert len(store.store) == 8

def _execute_with(jugfile, **kwargs):
    from jug.jug import execution_loop
    from jug.task import alltasks
    options = parse(['execute'])
    options.jugfile = find_test_jugfile(jugfile)
    for k, v in kwargs.items():
        setattr(options, k, v)
    store, space = jug.jug.init(options.jugfile, 'dict_store')
    execution_loop(alltasks, options)
    return store


@task_reset
def test_name_bare_function():
    # sum_2 is a function name (module-less): matches exactly
    store = _execute_with('simple_multiple.py', execute_name='sum_2')
    assert len(store.store) == 8


@task_reset
def test_name_is_strict():
    # 'sum_' is a prefix of function names, but not a function name
    store = _execute_with('simple_multiple.py', execute_name='sum_')
    assert len(store.store) == 0
    store = _execute_with('simple_multiple.py', execute_name='simple_multiple.sum_')
    assert len(store.store) == 0


@task_reset
def test_name_glob():
    store = _execute_with('simple_multiple.py', execute_name='sum_*')
    assert len(store.store) == 16


@task_reset
def test_pattern_substring():
    # The previous behaviour of --target: match anywhere
    store = _execute_with('simple_multiple.py', execute_pattern='simple_multiple.sum_')
    assert len(store.store) == 16


@task_reset
def test_pattern_regex():
    # the $ anchor is only possible with a regular expression
    store = _execute_with('simple_multiple.py', execute_pattern='/sum_[23]$/')
    assert len(store.store) == 16


@task_reset
def test_name_and_pattern_combined():
    store = _execute_with('simple_multiple.py', execute_name='sum_*', execute_pattern='/sum_2/')
    assert len(store.store) == 8

@task_reset
def test_failed_task_keep_going():
    from jug.jug import execution_loop
    from jug.task import alltasks
    options = parse(['execute'])
    options.jugfile = find_test_jugfile('failing.py')
    # these 3 silence errors during execution and ensure jug isn't kept waiting
    options.execute_keep_going = True
    options.execute_nr_wait_cycles = 1
    options.execute_wait_cycle_time = 0
    # keep_failed ensures errored tasks are marked as failed
    options.execute_keep_failed = True

    options.execute_name = None
    options.execute_pattern = None
    store, space = jug.jug.init(options.jugfile, 'dict_store')
    # the failing.py jugfile has a total of 20 reachable tasks
    assert len(alltasks) == 20
    # Keep a copy of all tasks to check for failed tasks later
    alltasks_copy = alltasks[:]

    execution_loop(alltasks, options)

    # 14 results + 3 failures
    assert len(store.store) == 17
    # 3 tasks should remain in waiting state due to 3 failures upstream
    assert len(alltasks) == 3
    assert len([x for x in alltasks_copy if x.is_failed()]) == 3

@task_reset
def test_failed_task():
    from jug.jug import execution_loop
    from jug.task import alltasks
    from jug.tests.jugfiles.exceptions import FailingTask
    options = parse(['execute'])
    options.jugfile = find_test_jugfile('failing.py')
    # keep_failed ensures errored tasks are marked as failed
    options.execute_keep_failed = True
    options.execute_name = None
    options.execute_pattern = None

    store, space = jug.jug.init(options.jugfile, 'dict_store')
    # the failing.py jugfile has a total of 20 reachable tasks
    assert len(alltasks) == 20
    # Keep a copy of all tasks to check for failed tasks later
    alltasks_copy = alltasks[:]

    try:
        execution_loop(alltasks, options)
    except FailingTask:  # Using a custom exception to make sure we don't silence any errors
        pass

    # The third task fails so we get 2 results and 1 failed lock
    # NOTE: This might be incorrect if order of execution is not guaranteed
    assert len(store.store) == 3
    # 10 tasks could be run and were taken. Only the 10 waiting remain
    assert len(alltasks) == 10
    assert len([x for x in alltasks_copy if x.is_failed()]) == 1
