from nose.tools import with_setup
import jug.jug
import jug.task
from jug.task import Task
from jug.backends.dict_store import dict_store
from jug.options import Options, default_options
from jug.tests.task_reset import task_reset
import random
jug.jug.silent = True


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

    opts = Options(default_options)
    opts.invalid_name = setall[0].name
    jug.jug.invalidate(store, opts)
    assert not store.store.keys(), store.store.keys()
    jug.task.Task.store = dict_store()
