from jug.hash import new_hash_object, hash_update, hash_one
import numpy as np


def test_hash_numpy():
    A = np.arange(10, dtype=np.float32)
    dig0 = hash_one(A)
    A += 1
    dig1 = hash_one(A)
    assert dig0 != dig1
    A = np.zeros((20,20), np.float32)
    A[2,::2] = np.arange(10)
    dig2 = hash_one(A[2,::2])
    assert dig0 == dig2
    dig3 = hash_one(A[2,::2].astype(np.float64))
    assert dig3 != dig0

def test_dict_mixed():
    value = {
            frozenset([1,2,3]) : 4,
            'hello': 2
    }
    v = hash_one(value)
    assert len(v)
