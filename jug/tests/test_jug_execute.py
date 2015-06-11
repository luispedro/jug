import inspect
import os

import jug.jug
import jug.task
from jug.task import Task
from jug.tests.utils import simple_execute
from jug.backends.dict_store import dict_store
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

