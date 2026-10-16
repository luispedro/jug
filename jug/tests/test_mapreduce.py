import inspect
import os

import numpy as np
from functools import reduce

import jug.mapreduce
import jug.utils

from jug.backends.dict_store import dict_store
from jug.tests.utils import simple_execute
from jug.mapreduce import _break_up, _get_function
from jug import value, TaskGenerator
from .task_reset import task_reset_at_exit, task_reset


_jugdir = os.path.abspath(inspect.getfile(inspect.currentframe()))
_jugdir = os.path.join(os.path.dirname(_jugdir), 'jugfiles')


def mapper(x):
    return x**2
def reducer(x, y):
    return x + y
def dfs_run(t):
    for dep in t.dependencies():
        dfs_run(dep)
    t.run()

def mapper2(x,y):
    return x+y

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
    ts = jug.mapreduce.map(mapper, A)
    simple_execute()
    ts = value(ts)
    assert np.all(ts == np.array(list(map(mapper,A))))

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
    for i in range(2,105):
        assert reduce(lambda a,b: a+b, _break_up(list(range(100)), i), []) == list(range(100))

@task_reset
def test_empty_mapreduce():
    jugfile = os.path.join(_jugdir, 'empty_mapreduce.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    simple_execute()
    assert value(space['two']) == []

@task_reset
def test_taskgenerator_mapreduce():
    jugfile = os.path.join(_jugdir, 'mapreduce_generator.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    simple_execute()
    assert space['sumtwo'].result == 2*sum(range(10))

@task_reset
def test_taskgenerator_map():
    jugfile = os.path.join(_jugdir, 'mapgenerator.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    assert not space['s'].can_run()
    simple_execute()
    assert len(value(space['v2s'])) == 16
    assert len(value(space['v4s'])) == 16

@task_reset
def test_currymap():
    np.random.seed(33)
    jug.task.Task.store = dict_store()
    A = np.random.rand(100)
    ts = jug.mapreduce.currymap(mapper2, list(zip(A,A)))
    simple_execute()
    assert np.allclose(np.array(value(ts)) , A*2)


@task_reset
def test_map_slicing():
    jug.task.Task.store = dict_store()
    A = list(range(23))
    ts = jug.mapreduce.map(mapper, A)
    simple_execute()
    expected = [mapper(a) for a in A]
    assert value(ts[-1]) == expected[-1]
    assert value(ts[-23]) == expected[-23]
    for s in [slice(None, None, 2),
              slice(1, 9, 3),
              slice(None, None, -1),
              slice(20, 2, -3),
              slice(5, 3),
              slice(3, 100)]:
        assert value(ts[s]) == expected[s]
        assert len(ts[s]) == len(expected[s])
        for s2 in [slice(None, None, 2),
                   slice(1, None),
                   slice(None, None, -1),
                   slice(1, 4, -1)]:
            assert value(ts[s][s2]) == expected[s][s2]
            assert len(ts[s][s2]) == len(expected[s][s2])
        sub = ts[s]
        for i in range(-len(sub), len(sub)):
            assert value(sub[i]) == expected[s][i]


@task_reset
def test_map_slice_hash_unchanged():
    # The hashes of stride-1 slices (which already worked) must not change
    jug.task.Task.store = dict_store()
    ts = jug.mapreduce.map(mapper, list(range(23)))
    a = ts[2:8][1:3]
    b = jug.mapreduce.block_access_slice(ts, (3, 5, 1))
    assert a.__jug_hash__() == b.__jug_hash__()
