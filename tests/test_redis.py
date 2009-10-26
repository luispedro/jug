import jug.redis_store
import pickle
def test_redis():
    redis = jug.redis_store.redis_store('redis:')
    key = 'jugisbestthingever'
    assert not redis.can_load(key)
    object = range(232)
    redis.dump(object, key)
    assert redis.can_load(key)
    assert redis.load(key) == object
    redis.remove(key)
    assert not redis.can_load(key)
    redis.close()

def test_redis_lock():
    redis = jug.redis_store.redis_store('redis:')
    key = 'jugisbestthingever'
    lock = redis.getlock(key)
    assert not lock.is_locked()
    assert lock.get()
    assert not lock.get()
    lock2 = redis.getlock(key)
    assert not lock2.get()
    lock.release()
    assert lock2.get()
    lock2.release()
    redis.close()
