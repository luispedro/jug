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
def test_recursive():
    from sys import version_info
    if version_info[0] == 2 and version_info[1] == 6:
        "We skip this test on Python 2.6"
        return
    jugfile = find_test_jugfile('barrier_recurse.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    assert 's2' not in space
    simple_execute()
    store, space = jug.jug.init(jugfile, store)
    assert 's2' in space

