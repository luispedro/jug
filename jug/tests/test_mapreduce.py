import numpy as np

import jug.mapreduce
from jug.backends.dict_store import dict_store
from jug.mapreduce import _break_up, _get_function
from jug import value, TaskGenerator
from jug.tests.task_reset import task_reset

def mapper(x):
    return x**2
def reducer(x, y):
    return x + y
def dfs_run(t):
    for dep in t.dependencies():
        dfs_run(dep)
    t.run()

def test_get_function():
    oid = id(reducer)
    assert oid == id(_get_function(reducer))
    task_reducer = TaskGenerator(reducer)
    assert oid == id(_get_function(task_reducer))


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

@task_reset
def test_reduce():
    np.random.seed(33)
    jug.task.Task.store = dict_store()
    A = np.random.rand(128)
    A = (A*32).astype(int) # This makes the reduction exactly cummutative (instead of approximately so as with floating point)
    t = jug.mapreduce.reduce(reducer, A)
    dfs_run(t)
    assert t.value() == reduce(reducer,A)

def test_break_up():
    for i in xrange(2,105):
        assert reduce(lambda a,b: a+b, _break_up(range(100), i), []) == range(100)

@task_reset
def test_empty_mapreduce():
    store, space = jug.jug.init('jug/tests/jugfiles/empty_mapreduce.py', 'dict_store')
    space['two'].run()
    assert space['two'].result == []

@task_reset
def test_taskgenerator_mapreduce():
    store, space = jug.jug.init('jug/tests/jugfiles/mapreduce_generator.py', 'dict_store')
    space['two'].run()
    assert space['two'].result == []

