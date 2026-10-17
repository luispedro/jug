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


def _hash_in_subprocess(code, seed):
    import os
    import subprocess
    import sys
    env = dict(os.environ, PYTHONHASHSEED=str(seed))
    return subprocess.check_output(
            [sys.executable, '-c', 'from jug.hash import hash_one\n' + code],
            env=env).strip()


def test_hash_stable_across_processes():
    # Strings hash differently in each process (unless PYTHONHASHSEED is
    # fixed), so iteration order of sets & dicts must not leak into the hash
    cases = [
        "print(hash_one(set(['a', 'b', 'c', 'd', 'e'])))",
        "print(hash_one(frozenset(['a', 'b', 'c', 'd', 'e'])))",
        "print(hash_one({'a': 1, 'b': 2, 'c': 3, 'd': 4}))",
        "print(hash_one({frozenset(['a', 'b', 'c']): 1}))",
        "import numpy as np\n"
            "print(hash_one(np.array(['a', 'b', None, 3], dtype=object)))",
    ]
    for code in cases:
        hashes = set(_hash_in_subprocess(code, seed) for seed in (1, 2, 3))
        assert len(hashes) == 1, code


def test_hash_frozenset():
    assert hash_one(frozenset([1, 2, 3])) == hash_one(frozenset([3, 2, 1]))
    assert hash_one(frozenset([1, 2, 3])) != hash_one(frozenset([1, 2]))
    assert hash_one(frozenset([1, 2, 3])) != hash_one(set([1, 2, 3]))


def test_hash_numpy_object():
    A = np.array(['a', 'b', None, 3], dtype=object)
    assert hash_one(A) == hash_one(A.copy())
    assert hash_one(A) != hash_one(A[::-1])
    assert hash_one(A) != hash_one(A.reshape((2, 2)))
    B = A.copy()
    B[0] = 'z'
    assert hash_one(A) != hash_one(B)
