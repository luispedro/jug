from jug.backends.file_store import file_store, file_based_lock, file_keepalive_based_lock
from jug.backends.dict_store import dict_store
from jug.tests.task_reset import task_reset
from jug.backends import memoize_store
from nose.tools import with_setup
from jug import Task
from time import sleep

_storedir = 'jugtests'
def _remove_file_store():
    file_store.remove_store(_storedir)

@with_setup(teardown=_remove_file_store)
def test_twice():
    lock = file_based_lock(_storedir, 'foo')
    assert lock.get()
    assert not lock.get()
    lock.release()

    assert lock.get()
    assert not lock.get()
    lock.release()

@with_setup(teardown=_remove_file_store)
def test_twolocks():
    foo = file_based_lock(_storedir, 'foo')
    bar = file_based_lock(_storedir, 'bar')
    assert foo.get()
    assert bar.get()
    assert not foo.get()
    assert not bar.get()
    foo.release()
    bar.release()


@with_setup(teardown=_remove_file_store)
def test_fail_and_lock():
    lock = file_based_lock(_storedir, 'foo')
    assert not lock.is_failed()
    assert not lock.is_locked()

    assert not lock.fail()
    assert not lock.is_failed()
    assert not lock.is_locked()

    assert lock.get()
    assert not lock.is_failed()
    assert lock.is_locked()

    assert lock.fail()
    assert lock.is_failed()
    assert lock.is_locked()

    assert lock.fail()
    assert lock.is_failed()
    assert lock.is_locked()

    assert not lock.get()
    assert lock.is_failed()
    assert lock.is_locked()

    lock.release()
    assert not lock.is_failed()
    assert not lock.is_locked()


def double(x):
    return x*2

@task_reset
@with_setup(teardown=_remove_file_store)
def test_memoize_lock():
    Task.store = file_store(_storedir)

    t = Task(double, 2)
    assert t.lock()

    Task.store = memoize_store(Task.store, list_base=True)
    assert t.is_locked()
    t2 = Task(double, 2)
    assert t2.is_locked()

@with_setup(teardown=_remove_file_store)
def test_lock_bytes():
    store = file_store(_storedir)
    lock = store.getlock('foo')
    lock2 = store.getlock(b'foo')
    assert lock.fullname == lock2.fullname

def test_lock_bytes2():
    store = dict_store()
    lock = store.getlock('foo')
    lock2 = store.getlock(b'foo')
    lock.get()
    assert lock2.is_locked()

@with_setup(teardown=_remove_file_store)
def test_lock_keepalive():
    lock = file_keepalive_based_lock(_storedir, 'foo')
    assert lock.monitor is None
    assert lock.get()
    assert lock.monitor.poll() is None
    p = lock.monitor
    assert not lock.get()
    assert p == lock.monitor, "A new process was started and shouldn't"
    assert lock.monitor.poll() is None
    lock.release()

    # Give max 5 secs for subprocess to return an exitcode
    for i in range(25):
        ret = p.poll()
        if ret is None:
            sleep(.2)
        else:
            break

    assert ret == -9  # SIGKILL

    assert lock.get()
    assert p != lock.monitor, "A new process should have been started but wasn't"
    assert lock.monitor.poll() is None
    p = lock.monitor
    assert not lock.get()
    assert lock.monitor.poll() is None
    assert p == lock.monitor, "A new process was started and shouldn't"
    lock.release()

    # Give max 5 secs for subprocess to return an exitcode
    for i in range(25):
        ret = p.poll()
        if ret is None:
            sleep(.2)
        else:
            break

    assert ret == -9  # SIGKILL
