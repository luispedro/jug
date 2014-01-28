from six import BytesIO
import six
from jug.backends.encode import compress_stream, decompress_stream, encode, decode
import numpy as np
def test_encode():
    assert decode(encode(None)) is None
    assert decode(encode([])) == []
    assert decode(encode(list(range(33)))) == list(range(33))

def test_numpy():
    assert np.all(decode(encode(np.arange(33))) == np.arange(33))


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

def test_decompress_stream_readline():
    text = six.b("1\n2\n3\n4")
    s = BytesIO()
    cstream = compress_stream(s)
    cstream.write(text)
    cstream.flush()
    dstream = decompress_stream(BytesIO(s.getvalue()))
    assert dstream.readline() == six.b("1\n")
    assert dstream.readline() == six.b("2\n")
    assert dstream.readline() == six.b("3\n")
    assert dstream.readline() == six.b("4")
    assert dstream.readline() == six.b("")


class Derived(np.ndarray):
    def __new__(cls, value):
        return np.ndarray.__new__(cls, value)

def test_numpy_derived():
    a = Derived([1,2,3])
    assert type(decode(encode(a))) == type(a)
