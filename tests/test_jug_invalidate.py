from nose.tools import with_setup
import jug.jug
import jug.task
from jug.task import Task
from jug.backends.dict_store import dict_store
import random
jug.jug.silent = True

def _setup():
    jug.task.Task.store = dict_store()
def _teardown():
    jug.task.alltasks = []
task_reset = with_setup(_setup, _teardown)

@task_reset
def test_jug_invalidate():
    def setAi(i):
        A[i] = True
    N = 1024
    A = [False for i in xrange(N)]
    setall = [Task(setAi, i) for i in xrange(N)]
    store = dict_store()
    jug.task.Task.store = store
    for t in setall: t.run()
    jug.jug.invalidate(store, setall[0].name)
    assert not store.store.keys(), store.store.keys()
    jug.task.Task.store = dict_store()
