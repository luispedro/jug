import jug.backends.encode
from jug.backends.file_store import file_store
from jug.hash import hash_one

import pytest
import os
import sys
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


def test_pack_decode_error_does_not_leak_sys_path(tmpdir):
    tmpdir = str(tmpdir)
    os.makedirs(os.path.join(tmpdir, 'packs'), exist_ok=True)
    with open(os.path.join(tmpdir, 'packs', 'jugpack'), 'wb') as out:
        out.write(b'not-a-valid-pack')

    before = list(sys.path)
    with pytest.raises(Exception):
        file_store(tmpdir)
    assert sys.path == before


def test_pack_native_formats(tmpdir):
    np = pytest.importorskip('numpy')
    tmpdir = str(tmpdir)
    fs = file_store(tmpdir)
    data = {
            hash_one('arr'): np.arange(4),
            hash_one('farr'): np.array([1.5, 2.5]),
            hash_one('none'): None,
            hash_one('list'): [1, 2, 3],
            }
    for k, v in data.items():
        fs.dump(v, k)
    assert fs.update_pack() == len(data)
    fs.close()

    fs = file_store(tmpdir)
    assert len(fs.list()) == len(data)
    for k, v in data.items():
        if isinstance(v, np.ndarray):
            assert np.all(fs.load(k) == v)
        else:
            assert fs.load(k) == v
    fs.close()


def test_pack_polars(tmpdir):
    pl = pytest.importorskip('polars')
    tmpdir = str(tmpdir)
    fs = file_store(tmpdir)
    df = pl.DataFrame({'a': [1, 2]})
    k = hash_one('df')
    fs.dump(df, k)
    fs.update_pack()
    fs.close()

    fs = file_store(tmpdir)
    assert fs.load(k).equals(df)
    fs.close()


def test_dump_failure_removes_tempfile(tmpdir):
    import threading
    tmpdir = str(tmpdir)
    fs = file_store(tmpdir)
    with pytest.raises(TypeError):
        fs.dump(threading.Lock(), hash_one('lock'))
    assert os.listdir(fs.tempdir()) == []
    assert not fs.can_load(hash_one('lock'))


def test_structured_object_array(tmpdir):
    np = pytest.importorskip('numpy')
    tmpdir = str(tmpdir)
    a = np.array([(1, 'one'), (2, [2])], dtype=[('x', int), ('y', object)])
    for compress_numpy in (False, True):
        fs = file_store(tmpdir, compress_numpy=compress_numpy)
        k = hash_one(('structured', compress_numpy))
        fs.dump(a, k)
        b = fs.load(k)
        assert b.dtype == a.dtype
        assert list(b['x']) == [1, 2]
        assert list(b['y']) == ['one', [2]]


def test_remove_does_not_rewrite_pack(tmpdir):
    tmpdir = str(tmpdir)
    fs = file_store(tmpdir)
    k = hash_one('k1')
    fs.dump([1], k)
    assert fs.remove(k)
    assert not fs.remove(k)
    assert not os.path.exists(os.path.join(tmpdir, 'packs'))


def test_pack_concurrent_stores(tmpdir):
    tmpdir = str(tmpdir)
    k1, k2, k3 = [hash_one(k) for k in ['k1', 'k2', 'k3']]
    fs = file_store(tmpdir)
    for k in [k1, k2, k3]:
        fs.dump([k], k)
    assert fs.update_pack() == 3

    # Two processes with the store open: changes made by one must not be
    # undone by the other
    fs1 = file_store(tmpdir)
    fs2 = file_store(tmpdir)
    assert fs1.remove(k1)
    assert fs2.remove(k2)

    fs = file_store(tmpdir)
    assert fs.list() == [k3]
    assert not fs.can_load(k1)
    assert not fs.can_load(k2)


def test_pack_keeps_newer_file(tmpdir):
    # A key can be both in the pack and on disk, with the file holding the
    # newer value: update_pack() must pack the file, not the stale packed
    # value (and must not then delete the file)
    tmpdir = str(tmpdir)
    k1 = hash_one('k1')

    fs = file_store(tmpdir)
    fs.dump('OLD', k1)

    # A second process opens the store before the pack is created, so its
    # in-memory pack does not have k1
    other = file_store(tmpdir)

    assert fs.update_pack() == 1
    # The second process now writes a new value. Because k1 is not in its
    # (stale) in-memory pack, the pack is left alone and only a file is
    # written, so k1 is now both packed and on disk.
    other.dump('NEW', k1)
    assert os.path.exists(fs._getfname(k1))

    # Packing again must preserve the newer value from the file (it used to
    # re-pack the stale packed value and then delete the file)
    fs = file_store(tmpdir)
    assert fs.update_pack() == 1
    assert fs.load(k1) == 'NEW'
    assert file_store(tmpdir).load(k1) == 'NEW'


def test_pack_write_failure_releases_lock(tmpdir, monkeypatch):
    import jug.backends.file_store
    tmpdir = str(tmpdir)
    k1, k2 = hash_one('k1'), hash_one('k2')
    fs = file_store(tmpdir)
    fs.dump([1], k1)
    assert fs.update_pack() == 1
    fs.dump([2], k2)

    def failing_encode_to(obj, output):
        raise OSError('disk full')
    monkeypatch.setattr(jug.backends.file_store, 'encode_to', failing_encode_to)
    with pytest.raises(OSError):
        fs.update_pack()
    monkeypatch.undo()
    assert not fs.getlock('pack-save').is_locked()
    assert os.listdir(fs.tempdir()) == []

    fs = file_store(tmpdir)
    assert fs.load(k1) == [1]
    assert fs.load(k2) == [2]
    assert fs.remove(k1)


def test_fsync_dir_after_rename(tmpdir, monkeypatch):
    # The directory must be synced *after* the rename for the rename to be
    # durable, so, when fsync_dir is called, the destination must exist
    import jug.backends.file_store as file_store_mod
    from jug.utils import sync_move
    synced = []
    def fsync_dir(fname):
        assert os.path.exists(fname)
        synced.append(fname)
    monkeypatch.setattr(file_store_mod, 'fsync_dir', fsync_dir)

    fs = file_store(str(tmpdir / 'jugdata'))
    fs.dump(1, hash_one('k0'))
    assert synced == [fs._getfname(hash_one('k0'))]

    fs.update_pack()
    assert synced[-1] == fs._packfile()

    src = str(tmpdir / 'src')
    dst = str(tmpdir / 'dst')
    with open(src, 'w') as f:
        f.write('data')
    sync_move(src, dst)
    assert synced[-1] == dst


def test_metadata_packed(tmpdir):
    class FakeTask:
        def hash(self):
            return hash_one('k0')
    tmpdir = str(tmpdir)
    t = FakeTask()
    fs = file_store(tmpdir)
    assert not fs.metadata(t)['computed']
    fs.dump(3, t.hash())
    assert fs.metadata(t)['computed']
    assert fs.update_pack() == 1
    assert fs.metadata(t)['computed']
