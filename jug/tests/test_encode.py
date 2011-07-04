from StringIO import StringIO
from jug.backends.encode import decompress_stream, encode, decode
import numpy as np
def test_encode():
    assert decode(encode(None)) is None
    assert decode(encode([])) == []
    assert decode(encode(range(33))) == range(33)
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
