from StringIO import StringIO
from jug.backends.encode import compress_stream, decompress_stream, encode, decode
import numpy as np
def test_encode():
    assert decode(encode(None)) is None
    assert decode(encode([])) == []
    assert decode(encode(range(33))) == range(33)

def test_numpy():
    assert np.all(decode(encode(np.arange(33))) == np.arange(33))


def test_decompress_stream_seek():
    s = encode(range(33))
    st = decompress_stream(StringIO(s))
    first = st.read(6)
    st.seek(-6, 1)
    second = st.read(6)
    assert first == second

    st = decompress_stream(StringIO(s))
    first = st.read(6)
    st.seek(-6, 1)
    second = st.read(8)
    assert first == second[:6]

    st = decompress_stream(StringIO(s))
    st.seek( 6, 1)
    st.seek(-6, 1)
    second = st.read(8)
    assert first == second[:6]

def test_decompress_stream_readline():
    text = "1\n2\n3\n4"
    s = StringIO()
    cstream = compress_stream(s)
    cstream.write(text)
    cstream.flush()
    dstream = decompress_stream(StringIO(s.getvalue()))
    assert dstream.readline() == "1\n"
    assert dstream.readline() == "2\n"
    assert dstream.readline() == "3\n"
    assert dstream.readline() == "4"
    assert dstream.readline() == ""
    
     
