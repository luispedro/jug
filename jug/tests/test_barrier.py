import jug.jug
import jug.subcommands.execute
from .task_reset import task_reset_at_exit, task_reset
from jug.tests.utils import simple_execute, find_test_jugfile
from jug.options import default_options
from functools import reduce


@task_reset
def test_barrier():
    jugfile = find_test_jugfile('wbarrier.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    assert 'four' not in space
    simple_execute()
    store, space = jug.jug.init(jugfile, store)
    assert 'four' in space

    # This is a regression test:
    # a test version of jug would fail here:
    simple_execute()

def product(vals):
    import operator
    return reduce(operator.mul, vals)

@task_reset
def test_mapreduce_barrier():
    jugfile = find_test_jugfile('barrier_mapreduce.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    assert 'values' not in space
    simple_execute()
    store, space = jug.jug.init(jugfile, store)
    assert 'values' in space
    assert space['values'] == product(list(range(20)))
    simple_execute()

@task_reset
def test_barrier_once():
    import sys
    options = default_options.copy()
    options.jugdir = 'dict_store'
    options.jugfile = find_test_jugfile('wbarrier.py')
    jug.subcommands.execute.execute(options)
    assert 'four' in dir(sys.modules['wbarrier'])

@task_reset
def test_bvalue():
    jugfile = find_test_jugfile('bvalue.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    assert 'four' not in space
    simple_execute()
    store, space = jug.jug.init(jugfile, store)
    assert 'four' in space
    assert space['four'] == 4

@task_reset
def test_bvalue_nested():
    jugfile = find_test_jugfile('bvalue_nested.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    assert 'vals' not in space
    simple_execute()
    store, space = jug.jug.init(jugfile, store)
    assert space['vals'] == {'first': [1], 'last': (3,)}
    simple_execute()
    assert [d.value() for d in space['doubled']] == [2, 6]

@task_reset
def test_bvalue_error_propagates():
    # Errors computing the value (here, an IndexError in a Tasklet) must not
    # be treated as an unsatisfied barrier
    import pytest
    options = default_options.copy()
    options.jugdir = 'dict_store'
    options.jugfile = find_test_jugfile('bvalue_error.py')
    options.execute_nr_wait_cycles = 2
    options.execute_wait_cycle_time = 0
    with pytest.raises(SystemExit) as e:
        jug.subcommands.execute.execute(options)
    assert e.value.code == 1


@task_reset
def test_recursive():
    jugfile = find_test_jugfile('barrier_recurse.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    assert 's2' not in space
    simple_execute()
    store, space = jug.jug.init(jugfile, store)
    assert 's2' in space


@task_reset
def test_barrier_failed_task_not_retried(monkeypatch):
    # With a barrier, waiting must be bounded overall (not nr_wait_cycles in
    # each re-load of the jugfile) and a failed task must not be re-run
    import pytest
    from jug.hooks import register_hook
    for keep_failed in (False, True):
        options = default_options.copy()
        options.jugdir = 'dict_store'
        options.jugfile = find_test_jugfile('failing_barrier.py')
        options.execute_keep_going = True
        options.execute_keep_failed = keep_failed
        options.execute_nr_wait_cycles = 3
        options.execute_wait_cycle_time = 0
        sleeps = []
        monkeypatch.setattr('time.sleep', sleeps.append)
        executed = []
        register_hook('execute.task-pre-execute', executed.append)
        with pytest.raises(SystemExit) as e:
            jug.subcommands.execute.execute(options)
        assert e.value.code == 1
        assert len(executed) == 1
        assert len(sleeps) == 3
