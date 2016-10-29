import os
import jug.backends.redis_store
import jug.backends.file_store
import jug.backends.dict_store
from jug.backends.redis_store import redis
from nose.tools import with_setup
from nose import SkipTest
import six

_storedir = 'jugtests'
def _remove_file_store():
    jug.backends.file_store.file_store.remove_store(_storedir)

if not os.getenv('TEST_REDIS'):
    redis = None

try:
    redisConnectionError = redis.ConnectionError
except:
    redisConnectionError = SystemError

def test_stores():
    def load_get(store):
        try:
            assert len(list(store.list())) == 0
            key = six.b('jugisbestthingever')
            assert not store.can_load(key)
            object = list(range(232))
            store.dump(object, key)
            assert store.can_load(key)
            assert store.load(key) == object

            flist = list(store.list())
            assert len(flist) == 1
            assert flist[0] == key

            store.remove(key)
            assert not store.can_load(key)
            store.close()
        except redisConnectionError:
            raise SkipTest()


    def lock(store):
        try:
            assert len(list(store.listlocks())) == 0
            key = six.b('jugisbestthingever')
            lock = store.getlock(key)
            assert not lock.is_locked()
            assert lock.get()
            assert not lock.get()
            lock2 = store.getlock(key)
            assert not lock2.get()
            assert len(list(store.listlocks())) == 1
            lock.release()
            assert lock2.get()
            lock2.release()
            store.close()
        except redisConnectionError:
            raise SkipTest()
    def lock_remove(store):
        try:
            assert len(list(store.listlocks())) == 0
            key = six.b('jugisbestthingever')
            lock = store.getlock(key)
            assert not lock.is_locked()
            assert lock.get()
            assert not lock.get()
            assert len(list(store.listlocks())) == 1
            store.remove_locks()
            assert len(list(store.listlocks())) == 0
            store.close()
        except redisConnectionError:
            raise SkipTest()
    functions = (load_get, lock, lock_remove)
    stores = [
            lambda: jug.backends.file_store.file_store('jugtests'),
            jug.backends.dict_store.dict_store,
            ]
    if redis is not None:
        stores.append(
            lambda: jug.redis_store.redis_store('redis:')
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
    arr = arr.reshape((10,10))
    key = 'mykey'
    store.dump(arr, key)
    arr2 = store.load(key)
    assert np.all(arr2 == arr)
    store.remove(key)
    store.close()

@with_setup(teardown=_remove_file_store)
def test_numpy_array_no_compress():
    try:
        import numpy as np
    except ImportError:
        raise SkipTest()
    store = jug.backends.file_store.file_store(_storedir, compress_numpy=False)
    arr = np.arange(100) % 17
    arr = arr.reshape((10,10))
    key = 'mykey'
    store.dump(arr, key)
    arr2 = store.load(key)
    assert np.all(arr2 == arr)
    store.remove(key)
    store.close()
