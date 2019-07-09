import inspect
import os

import jug.jug
import jug.task
import jug.subcommands.invalidate
import jug.subcommands.cleanup
import jug.subcommands.shell
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
    jug.subcommands.invalidate.invalidate(store, opts)
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
    jug.subcommands.invalidate.invalidate(store, opts)
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
    jug.subcommands.cleanup.cleanup(store, opts)
    assert store.can_load(h)
    opts.cleanup_locks_only = False
    jug.subcommands.cleanup.cleanup(store, opts)
    assert not store.can_load(h)

@task_reset
def test_shell_invalidate():
    jugfile = os.path.join(_jugdir, 'iteratetask.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    tasks = jug.task.alltasks[:]
    simple_execute()
    loaded = sum([t.can_load() for t in tasks])
    assert loaded == len(tasks)
    jug.subcommands.shell.invalidate(tasks, {}, tasks[0])
    loaded = sum([t.can_load() for t in tasks])
    print(loaded)
    print(len(tasks) - 2)
    assert loaded == len(tasks) - 2

@task_reset
def test_cleanup_failed_only():
    jugfile = os.path.join(_jugdir, 'tasklets.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    h = space['t'].hash()

    # With locked tasks we need to bypass execute waiting mechanisms
    from jug.task import alltasks
    from jug.jug import execution_loop

    opts = Options(default_options)
    opts.execute_nr_wait_cycles = 1
    opts.execute_wait_cycle_time = 0
    opts.execute_keep_failed = True
    execution_loop(alltasks, opts)

    # Fail one task manually
    lock = store.getlock(h)
    assert lock.get()
    assert lock.fail()
    assert lock.is_failed()

    # Keep locks should not remove failed tasks
    opts = Options(default_options)
    opts.cleanup_keep_locks = True
    jug.subcommands.cleanup.cleanup(store, opts)

    assert lock.is_locked()
    assert lock.is_failed()

    # Failed only should remove failed tasks
    opts = Options(default_options)
    opts.cleanup_failed_only = True
    jug.subcommands.cleanup.cleanup(store, opts)

    assert not lock.is_locked()
    assert not lock.is_failed()
