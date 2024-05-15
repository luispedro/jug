import jug.backends.encode
from jug.backends.file_store import file_store
from jug.hash import hash_one

import pytest
import os
from io import BytesIO

def test_encode_decode_empty_string():
    # This is a regression test for
    # https://github.com/luispedro/jug/issues/39
    s = BytesIO()
    jug.backends.encode.encode_to('', s)
    val = jug.backends.encode.decode_from(BytesIO(s.getvalue()))
    assert val == ''

def test_create_pack(tmpdir):
    tmpdir = str(tmpdir)

    data = {
            hash_one('k0') : 1,
            hash_one('k1') : 2,
            hash_one('k2') : [1,2,3],
            hash_one('k3') : {1: 2, 'a': 'b'},
            # k4 is larger and will not be packed by default
            hash_one('k4') : {hash_one(k):hash_one(k*5+1001) for k in range(320)},
            }

    def assert_contains_data(st, data):
        for k,v in data.items():
            assert st.load(k) == v
        assert len(st.list()) == len(data)
    fs = file_store(tmpdir)
    for k,v in data.items():
        fs.dump(v, k)
    assert_contains_data(fs, data)
    fs.close()


    fs = file_store(tmpdir)
    assert_contains_data(fs, data)
    packed = fs.update_pack()
    assert packed > 0
    assert_contains_data(fs, data)
    fs.close()

    fs = file_store(tmpdir)
    assert_contains_data(fs, data)
    fs.remove(hash_one('k0'))
    del data[hash_one('k0')]
    assert_contains_data(fs, data)
    fs.close()

    fs = file_store(tmpdir)
    assert_contains_data(fs, data)
    fs.close()

class MockHash:
    def __init__(self, h):
        self.h = h

    def hash(self):
        return self.h

def test_pack_cleanup(tmpdir):
    tmpdir = str(tmpdir)
    fs = file_store(tmpdir)
    assert len(list(fs.listlocks())) == 0
    key1 = b'jugisbestthingever'
    key2 = b'jug_key2'
    ob1 = [1]
    ob2 = [1, 2]
    fs.dump(ob1, key1)
    fs.dump(ob2, key2)

    assert len(list(fs.list())) == 2
    assert fs.cleanup([MockHash(key1), MockHash(key2)], keeplocks=False) == 0

    assert len(list(fs.list())) == 2
    packed = fs.update_pack()
    assert packed == 2
    assert fs.cleanup([MockHash(key1), MockHash(key2)], keeplocks=False) == 0
    assert len(list(fs.list())) == 2

    fs.close()

    fs = file_store(tmpdir)
    assert len(list(fs.list())) == 2


def test_lock_permissions(tmpdir):
    tmpdir = str(tmpdir)
    os.makedirs(tmpdir, exist_ok=True)
    fs = file_store(tmpdir)
    lock = fs.getlock(hash_one('k0'))
    assert lock.get()
    lock.release()
    os.chmod(tmpdir + '/locks', 0o444)
    with pytest.raises(PermissionError):
        lock.get()

