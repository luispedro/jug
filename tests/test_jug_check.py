import jug.jug
import jug.task
from jug.task import Task
from jug.backends.dict_store import dict_store
from tests.task_reset import task_reset
import random
jug.jug.silent = True


def test_jug_check():
    N = 1024
    A = [False for i in xrange(N)]
    def setAi(i):
        A[i] = True
    setall = [Task(setAi, i) for i in xrange(N)]
    store = dict_store()
    jug.task.Task.store = store
    e = None
    try:
        jug.jug.check(store)
    except SystemExit, e:
        pass
    assert e is not None
    assert e.code == 1
    jug.jug.execute(store)

    e = None
    try:
        jug.jug.check(store)
    except SystemExit, e:
        pass
    assert e is not None
    assert e.code == 0

