from jug.backends.encode import encode, decode
import numpy as np
def test_encode():
    assert decode(encode(None)) is None
    assert decode(encode([])) == []
    assert decode(encode(range(33))) == range(33)
    assert np.all(decode(encode(np.arange(33))) == np.arange(33))

