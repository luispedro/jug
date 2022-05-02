import os
import jug.backends.redis_store
import jug.backends.file_store
import jug.backends.dict_store
import pytest

if not os.getenv('TEST_REDIS'):
    redis = None
else:
    from jug.backends.redis_store import redis

try:
    redisConnectionError = redis.ConnectionError
except:
    redisConnectionError = SystemError

@pytest.fixture(scope='function', params=['file', 'dict', 'redis'])
def store(tmpdir, request):
    if request.param == 'file':
        tmpdir = str(tmpdir)
        yield jug.backends.file_store.file_store(tmpdir)
        jug.backends.file_store.file_store.remove_store(tmpdir)
    elif request.param == 'dict':
        yield jug.backends.dict_store.dict_store()
    elif request.param == 'redis':
        if redis is None:
            pytest.skip()
        try:
            st = jug.redis_store.redis_store('redis:')
            yield st
            st.close()
        except redisConnectionError:
            pytest.skip()

def test_load_get(store):
    assert len(list(store.list())) == 0
    key = b'jugisbestthingever'
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

def test_lock(store):
    assert len(list(store.listlocks())) == 0
    key = b'jugisbestthingever'
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

def test_lock_remove(store):
    assert len(list(store.listlocks())) == 0
    key = b'jugisbestthingever'
    lock = store.getlock(key)
    assert not lock.is_locked()
    assert lock.get()
    assert not lock.get()
    assert len(list(store.listlocks())) == 1
    store.remove_locks()
    assert len(list(store.listlocks())) == 0

def test_lock_fail(store):
    assert len(list(store.listlocks())) == 0
    key = b'jugisbestthingever'
    lock = store.getlock(key)
    assert not lock.is_locked()
    assert lock.get()
    assert not lock.get()
    lock.fail()
    assert lock.is_failed()
    assert len(list(store.listlocks())) == 1
    store.remove_locks()
    assert not lock.is_failed()
    assert len(list(store.listlocks())) == 0

def test_lock_fail_other(store):
    # is_failed should return True even if we can't acquire the lock
    assert len(list(store.listlocks())) == 0
    key = b'jugisbestthingever'
    lock1 = store.getlock(key)
    lock2 = store.getlock(key)
    assert not lock1.is_locked()
    assert not lock2.is_locked()
    assert lock1.get()
    assert not lock2.get()
    assert not lock1.is_failed()
    assert not lock2.is_failed()
    lock1.fail()
    assert lock2.is_failed()
    assert len(list(store.listlocks())) == 1
    store.remove_locks()
    assert not lock1.is_failed()
    assert not lock2.is_failed()
    assert len(list(store.listlocks())) == 0

def test_numpy_array(tmpdir):
    try:
        import numpy as np
    except ImportError:
        pytest.skip()
    store = jug.backends.file_store.file_store(str(tmpdir))
    arr = np.arange(100) % 17
    arr = arr.reshape((10,10))
    key = 'mykey'
    store.dump(arr, key)
    arr2 = store.load(key)
    assert np.all(arr2 == arr)
    store.remove(key)
    store.close()

def test_numpy_array_no_compress(tmpdir):
    try:
        import numpy as np
    except ImportError:
        pytest.skip()
    store = jug.backends.file_store.file_store(str(tmpdir), compress_numpy=False)
    arr = np.arange(100) % 17
    arr = arr.reshape((10,10))
    key = 'mykey'
    store.dump(arr, key)
    arr2 = store.load(key)
    assert np.all(arr2 == arr)
    store.remove(key)
    store.close()
