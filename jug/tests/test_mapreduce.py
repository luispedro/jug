import numpy as np

import jug.mapreduce
from jug.backends.dict_store import dict_store
from jug.mapreduce import _break_up
from jug import value
from jug.tests.task_reset import task_reset

def mapper(x):
    return x**2
def reducer(x, y):
    return x + y
def dfs_run(t):
    for dep in t.dependencies():
        dfs_run(dep)
    t.run()

@task_reset
def test_mapreduce():
    np.random.seed(33)
    jug.task.Task.store = dict_store()
    A = np.random.rand(10000)
    t = jug.mapreduce.mapreduce(reducer, mapper, A)
    dfs_run(t)
    assert np.abs(t.result - (A**2).sum()) < 1.

@task_reset
def test_map():
    np.random.seed(33)
    jug.task.Task.store = dict_store()
    A = np.random.rand(10000)
    t = jug.mapreduce.map(mapper, A)
    dfs_run(t)
    ts = value(t)
    assert np.all(ts == np.array(map(mapper,A)))



def test_break_up():
    for i in xrange(2,105):
        assert reduce(lambda a,b: a+b, _break_up(range(100), i), []) == range(100)

@task_reset
def test_empty_mapreduce():
    store, space = jug.jug.init('jug/tests/jugfiles/empty_mapreduce.py', 'dict_store')
    space['two'].run()
    assert space['two'].result == []
