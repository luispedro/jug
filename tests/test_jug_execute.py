import jug.jug
import jug.task
from jug.task import Task
from jug.backends.dict_store import dict_store
import random
jug.jug.silent = True

def test_jug_execute_simple():
    N = 1024
    random.seed(232)
    A = [False for i in xrange(N)]
    def setAi(i):
        A[i] = True
    setall = [Task(setAi, i) for i in xrange(N)]
    store = dict_store()
    jug.task.Task.store = store
    jug.jug.execute(store)
    assert False not in A
    assert max(store.counts.values()) < 4

def test_jug_execute_deps():
    N = 256
    random.seed(234)
    A = [False for i in xrange(N)]
    def setAi(i, other):
        A[i] = True
    idxs = range(N)
    random.shuffle(idxs)
    prev = None
    for idx in idxs:
        prev = Task(setAi, idx, prev)
    store = dict_store()
    jug.task.Task.store = store
    jug.jug.execute(store)
    assert False not in A
    assert max(store.counts.values()) < 4

