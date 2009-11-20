from jug.backends.file_store import file_store, file_based_lock
from nose.tools import with_setup

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

