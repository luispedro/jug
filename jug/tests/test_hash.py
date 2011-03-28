from jug.hash import new_hash_object, hash_update
import numpy as np


def _hash_simple(obj):
    return hash_update(new_hash_object(), [(0,obj)]).hexdigest()

def test_hash_numpy():
    A = np.arange(10, dtype=np.float32)
    dig0 = _hash_simple(A)
    A += 1
    dig1 = _hash_simple(A)
    assert dig0 != dig1
    A = np.zeros((20,20), np.float32)
    A[2,::2] = np.arange(10)
    dig2 = _hash_simple(A[2,::2])
    assert dig0 == dig2
    dig3 = _hash_simple(A[2,::2].astype(np.float64))
    assert dig3 != dig0
