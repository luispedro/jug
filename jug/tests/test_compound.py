import inspect
import os

import jug.compound
import jug.mapreduce
import numpy as np
from jug.backends.dict_store import dict_store
from jug.tests.utils import simple_execute
from jug.compound import CompoundTask
from jug.tests.test_mapreduce import mapper, reducer, dfs_run
from jug.tests.task_reset import task_reset


_jugdir = os.path.abspath(inspect.getfile(inspect.currentframe()))
_jugdir = os.path.join(os.path.dirname(_jugdir), 'jugfiles')


@task_reset
def test_compound():
    jug.task.Task.store = dict_store()
    A = np.random.rand(10000)
    x = CompoundTask(jug.mapreduce.mapreduce,reducer, mapper, A)
    dfs_run(x)
    y = CompoundTask(jug.mapreduce.mapreduce,reducer, mapper, A)

    assert y.can_load()
    assert y.result == x.result


@task_reset
def test_w_barrier():
    jugfile = os.path.join(_jugdir, 'compound_wbarrier.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    simple_execute()
    store, space = jug.jug.init(jugfile, store)
    simple_execute()
    assert 'sixteen' in space
    assert space['sixteen'].result == 16


@task_reset
def test_non_simple():
    jugfile = os.path.join(_jugdir, 'compound_nonsimple.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    simple_execute()
    store, space = jug.jug.init(jugfile, store)
    simple_execute()
    store, space = jug.jug.init(jugfile, store)
    simple_execute()
    assert 'sixteen' in space
    assert space['sixteen'].result == 16

@task_reset
def test_compound_jugfile():
    jugfile = os.path.join(_jugdir, 'compound.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    simple_execute()
    assert 'sixteen' in space
    assert space['sixteen'].result == 16
    store, space = jug.jug.init(jugfile, store)
    assert 'sixteen' in space
    assert space['sixteen'].result == 16

@task_reset
def test_debug():
    from jug.jug import execution_loop
    from jug.task import alltasks
    from jug.options import default_options
    options = default_options.copy()
    options.debug = True
    jugfile = os.path.join(_jugdir, 'compound.py')

    store, space = jug.jug.init(jugfile, 'dict_store')
    execution_loop(alltasks, options)
    assert 'sixteen' in space
    assert space['sixteen'].result == 16
    store, space = jug.jug.init(jugfile, store)
    assert 'sixteen' in space
    assert space['sixteen'].result == 16

