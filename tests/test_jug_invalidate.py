import jug.jug
import jug.task
from jug.task import Task
from jug.backends.dict_store import dict_store
import random
jug.jug.silent = True

def test_jug_invalidate():
    A = [False for i in xrange(N)]
    def setAi(i):
        A[i] = True
    N = 1024
    setall = [Task(setAi, i) for i in xrange(N)]
    store = dict_store()
    jug.task.Task.store = store
    jug.jug.execute(store)
    jug.jug.invalidate(store, setall[0].name)
    assert not store.store.keys()
