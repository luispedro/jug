import jug.backends.encode
from six import BytesIO

def test_encode_decode_empty_string():
    # This is a regression test for
    # https://github.com/luispedro/jug/issues/39
    s = BytesIO()
    jug.backends.encode.encode_to('', s)
    val = jug.backends.encode.decode_from(BytesIO(s.getvalue()))
    assert val == ''
