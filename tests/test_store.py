import jug.backends.redis_store
import jug.backends.file_store
import jug.backends.dict_store
import pickle

_storedir = 'jugtests'
def _remove_file_store():
    jug.backends.file_store.file_store.remove_store(_storedir)

def test_stores():
    def test_load_get(store):
        key = 'jugisbestthingever'
        assert not store.can_load(key)
        object = range(232)
        store.dump(object, key)
        assert store.can_load(key)
        assert store.load(key) == object
        store.remove(key)
        assert not store.can_load(key)
        store.close()

    def test_lock(store):
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

    functions = (test_load_get, test_lock)
    stores = (lambda: jug.redis_store.redis_store('redis:'), lambda: jug.backends.file_store.file_store('jugtests'), jug.backends.dict_store.dict_store)
    teardowns = (None, _remove_file_store, None)
    for f in functions:
        for s,tear in zip(stores,teardowns):
            f.teardown = tear
            yield f, s()

