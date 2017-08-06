import inspect
import os

import jug.jug
import jug.task
from jug.task import Task
from jug.tests.utils import simple_execute
from jug.backends.dict_store import dict_store
from jug.options import default_options
from .task_reset import task_reset

import random
jug.jug.silent = True


_jugdir = os.path.abspath(inspect.getfile(inspect.currentframe()))
_jugdir = os.path.join(os.path.dirname(_jugdir), 'jugfiles')


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

def test_aggressive_unload():
    from jug.jug import execution_loop
    from jug.task import alltasks
    from jug.options import default_options
    options = default_options.copy()
    options.aggressive_unload = True
    @task_reset
    def run_jugfile(jugfile):
        store, space = jug.jug.init(jugfile, 'dict_store')
        execution_loop(alltasks, options)
    yield run_jugfile, os.path.join(_jugdir, 'tasklet_simple.py')
    yield run_jugfile, os.path.join(_jugdir, 'tasklets.py')
    yield run_jugfile, os.path.join(_jugdir, 'barrier_mapreduce.py')
    yield run_jugfile, os.path.join(_jugdir, 'compound_nonsimple.py')
    yield run_jugfile, os.path.join(_jugdir, 'slice_task.py')

@task_reset
def test_target_exact():
    from jug.jug import execution_loop
    from jug.task import alltasks
    options = default_options.copy()
    options.jugfile = os.path.join(_jugdir, 'simple.py')
    # Test if restricting to this target we skip the other tasks
    options.execute_target = "simple.double"

    store, space = jug.jug.init(options.jugfile, 'dict_store')
    execution_loop(alltasks, options)

    assert len(store.store) < len(alltasks)
    assert len(store.store) == 8

@task_reset
def test_target_wild():
    from jug.jug import execution_loop
    from jug.task import alltasks
    options = default_options.copy()
    options.jugfile = os.path.join(_jugdir, 'simple_multiple.py')
    # Test if restricting to this target we skip the other tasks
    options.execute_target = "simple_multiple.sum_"

    store, space = jug.jug.init(options.jugfile, 'dict_store')
    execution_loop(alltasks, options)

    assert len(store.store) < len(alltasks)
    assert len(store.store) == 16

@task_reset
def test_failed_task_keep_going():
    from jug.jug import execution_loop
    from jug.task import alltasks
    options = default_options.copy()
    options.jugfile = os.path.join(_jugdir, 'failing.py')
    # these 3 silence errors during execution and ensure jug isn't kept waiting
    options.execute_keep_going = True
    options.execute_nr_wait_cycles = 1
    options.execute_wait_cycle_time = 0
    # keep_failed ensures errored tasks are marked as failed
    options.execute_keep_failed = True

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
    options = default_options.copy()
    options.jugfile = os.path.join(_jugdir, 'failing.py')
    # keep_failed ensures errored tasks are marked as failed
    options.execute_keep_failed = True

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
