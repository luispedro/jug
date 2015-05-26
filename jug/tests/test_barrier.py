import inspect
import os

import jug.jug
from jug.tests.task_reset import task_reset
from jug.tests.utils import simple_execute
from jug.options import default_options
from functools import reduce


_jugdir = os.path.abspath(inspect.getfile(inspect.currentframe()))
_jugdir = os.path.join(os.path.dirname(_jugdir), 'jugfiles')


@task_reset
def test_barrier():
    jugfile = os.path.join(_jugdir, 'wbarrier.py')
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
    jugfile = os.path.join(_jugdir, 'barrier_mapreduce.py')
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
    options.jugfile = os.path.join(_jugdir, 'wbarrier.py')
    jug.jug.execute(options)
    assert 'four' in dir(sys.modules['wbarrier'])

@task_reset
def test_bvalue():
    jugfile = os.path.join(_jugdir, 'bvalue.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    assert 'four' not in space
    simple_execute()
    store, space = jug.jug.init(jugfile, store)
    assert 'four' in space
    assert space['four'] == 4


