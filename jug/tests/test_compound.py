import jug.compound
import jug.mapreduce
import numpy as np
from jug.backends.dict_store import dict_store
from jug.compound import CompoundTask
from jug.tests.test_mapreduce import mapper, reducer, dfs_run
from jug.tests.task_reset import task_reset

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
    from jug.options import default_options
    store, space = jug.jug.init('jug/tests/jugfiles/compound_wbarrier.py', 'dict_store')
    jug.jug.execute(store, default_options)
    store, space = jug.jug.init('jug/tests/jugfiles/compound_wbarrier.py', store)
    jug.jug.execute(store, default_options)
    assert 'sixteen' in space
    assert space['sixteen'].result == 16

