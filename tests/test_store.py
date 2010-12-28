import jug.backends.redis_store
import jug.backends.file_store
import jug.backends.dict_store
from jug.backends.redis_store import redis
from nose.tools import with_setup
from nose import SkipTest

_storedir = 'jugtests'
def _remove_file_store():
    jug.backends.file_store.file_store.remove_store(_storedir)


def test_stores():
    def load_get(store):
        try:
            key = 'jugisbestthingever'
            assert not store.can_load(key)
            object = range(232)
            store.dump(object, key)
            assert store.can_load(key)
            assert store.load(key) == object
            store.remove(key)
            assert not store.can_load(key)
            store.close()
        except redis.ConnectionError:
            raise SkipTest()


    def lock(store):
        try:
            key = 'jugisbestthingever'
            lock = store.getlock(key)
            assert not lock.is_locked()
            assert lock.get()
            assert not lock.get()
            lock2 = store.getlock(key)
            assert not lock2.get()
            lock.release()
            assert lock2.get()
            lock2.release()
            store.close()
        except redis.ConnectionError:
            raise SkipTest()
    functions = (load_get, lock)
    stores = (
            lambda: jug.redis_store.redis_store('redis:'),
            lambda: jug.backends.file_store.file_store('jugtests'),
            jug.backends.dict_store.dict_store,
            )
    teardowns = (None, _remove_file_store, None)
    for f in functions:
        for s,tear in zip(stores,teardowns):
            f.teardown = tear
            yield f, s()

@with_setup(teardown=_remove_file_store)
def test_numpy_array():
    try:
        import numpy as np
    except ImportError:
        raise SkipTest()
    store = jug.backends.file_store.file_store(_storedir)
    arr = np.arange(100) % 17
    key = 'mykey'
    store.dump(arr, key)
    arr2 = store.load(key)
    assert np.all(arr2 == arr)
    store.remove(key)
    store.close()
