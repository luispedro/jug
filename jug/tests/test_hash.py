from jug.hash import hash_one
from jug.unsafe import NoHash
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

def test_hash_numpy_copy():
    X = np.arange(10)
    assert hash_one(X[::-1]) != hash_one(X)
    assert hash_one(X.copy()) == hash_one(X)
    assert hash_one(X[::-1].copy()) == hash_one(X[::-1])

def test_hash_set():
    assert hash_one(set([1,2,3])) != hash_one([1,2,3])



def test_unsafe_nohash():
    assert hash_one([1,2,NoHash(3)]) == hash_one([1,2,NoHash(7)])

def test_hash_stable_across_python_versions():
    # These digests were computed with pickle protocol 4 (the default up to
    # Python 3.13). Hashes must not depend on the interpreter's default
    # pickle protocol (which is 5 from Python 3.14), or cached results would
    # be invalidated when upgrading Python.
    assert hash_one([1, 'a', (2, 3)]) == b'072067f4dcf1ed6f65eebc9ac81bb629179c0c9f'
    assert hash_one({'k': 1.5}) == b'2048fd3dccf8b1a8bdf8d55839918fff0a308a1c'


def test_hash_ignores_pickle_default_protocol(monkeypatch):
    import pickle
    expected = hash_one([1, 'a', (2, 3)])
    monkeypatch.setattr(pickle, 'DEFAULT_PROTOCOL', 5 if pickle.DEFAULT_PROTOCOL != 5 else 3)
    assert hash_one([1, 'a', (2, 3)]) == expected
