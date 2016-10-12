import inspect
import os

import jug.jug
import jug.task
from jug.task import Task
from jug.backends.dict_store import dict_store
from jug.options import Options, default_options
from jug.tests.utils import simple_execute
from jug.tests.task_reset import task_reset
jug.jug.silent = True


_jugdir = os.path.abspath(inspect.getfile(inspect.currentframe()))
_jugdir = os.path.join(os.path.dirname(_jugdir), 'jugfiles')


@task_reset
def test_jug_invalidate():
    def setAi(i):
        A[i] = True
    N = 1024
    A = [False for i in range(N)]
    setall = [Task(setAi, i) for i in range(N)]
    store = dict_store()
    jug.task.Task.store = store
    for t in setall: t.run()

    opts = Options(default_options)
    opts.invalid_name = setall[0].name
    jug.jug.invalidate(store, opts)
    assert not list(store.store.keys()), list(store.store.keys())
    jug.task.Task.store = dict_store()

@task_reset
def test_complex():
    jugfile = os.path.join(_jugdir, 'tasklets.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    simple_execute()

    store, space = jug.jug.init(jugfile, store)
    opts = Options(default_options)
    opts.invalid_name = space['t'].name
    h = space['t'].hash()
    assert store.can_load(h)
    jug.jug.invalidate(store, opts)
    assert not store.can_load(h)

@task_reset
def test_cleanup():
    jugfile = os.path.join(_jugdir, 'tasklets.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    h = space['t'].hash()
    simple_execute()

    opts = Options(default_options)
    opts.cleanup_locks_only = True
    assert store.can_load(h)
    jug.jug.cleanup(store, opts)
    assert store.can_load(h)
    opts.cleanup_locks_only = False
    jug.jug.cleanup(store, opts)
    assert not store.can_load(h)

