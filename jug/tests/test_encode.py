from io import BytesIO
from jug.backends.encode import compress_stream, decompress_stream, encode, decode
import numpy as np
def test_encode():
    assert decode(encode(None)) is None
    assert decode(encode([])) == []
    assert decode(encode(list(range(33)))) == list(range(33))

def test_numpy():
    assert np.all(decode(encode(np.arange(33))) == np.arange(33))

    x = decode(encode({'res': np.arange(1024*1024)}))
    assert np.all(x['res'] == np.arange(1024*1024))


def test_decompress_stream_seek():
    s = encode(list(range(33)))
    st = decompress_stream(BytesIO(s))
    first = st.read(6)
    st.seek(-6, 1)
    second = st.read(6)
    assert first == second

    st = decompress_stream(BytesIO(s))
    first = st.read(6)
    st.seek(-6, 1)
    second = st.read(8)
    assert first == second[:6]

    st = decompress_stream(BytesIO(s))
    st.seek( 6, 1)
    st.seek(-6, 1)
    second = st.read(8)
    assert first == second[:6]

def test_decompress_stream_seek_keeps_queue():
    import zlib
    data = bytes(range(256)) * 4
    st = decompress_stream(BytesIO(zlib.compress(data)), block=64)
    assert st.read(100) == data[:100]
    st.seek(-50, 1)
    # served from the queue, which still holds 40 bytes afterwards
    assert st.read(10) == data[50:60]
    st.seek(-5, 1)
    assert st.read(20) == data[55:75]


def test_decompress_stream_seek_too_far():
    import pytest
    st = decompress_stream(BytesIO(encode(list(range(33)))))
    st.read(6)
    with pytest.raises(ValueError):
        st.seek(-7, 1)


def test_decode_large_is_fast():
    # Decoding used to be quadratic in the size of the largest single read
    # (pickle reads a large bytes object at once): 64 MiB took over 90 seconds
    import os
    from time import time
    data = os.urandom(64 << 20)
    s = encode(data)
    start = time()
    assert decode(s) == data
    assert time() - start < 10.


def test_decompress_stream_readline():
    text = b"1\n2\n3\n4"
    s = BytesIO()
    cstream = compress_stream(s)
    cstream.write(text)
    cstream.flush()
    dstream = decompress_stream(BytesIO(s.getvalue()))
    assert dstream.readline() == b"1\n"
    assert dstream.readline() == b"2\n"
    assert dstream.readline() == b"3\n"
    assert dstream.readline() == b"4"
    assert dstream.readline() == b""


class Derived(np.ndarray):
    def __new__(cls, value):
        return np.ndarray.__new__(cls, value)

def test_numpy_derived():
    a = Derived([1,2,3])
    assert type(decode(encode(a))) == type(a)
