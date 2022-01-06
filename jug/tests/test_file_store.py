import jug.backends.encode
from jug.backends.file_store import file_store
from jug.hash import hash_one

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
