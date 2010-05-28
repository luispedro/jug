import jug.mapreduce
import numpy as np
from jug.backends.dict_store import dict_store

def mapper(x):
    return x**2
def reducer(x, y):
    return x + y
def dfs_run(t):
    for dep in t.dependencies():
        dfs_run(dep)
    t.run()

def test_mapreduce():
    np.random.seed(33)
    jug.task.Task.store = dict_store()
    A = np.random.rand(10000)
    t = jug.mapreduce.mapreduce(reducer, mapper, A)
    dfs_run(t)
    assert np.abs(t.result - (A**2).sum()) < 1.

