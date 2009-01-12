from juglib import lock
def test_twice():
    assert lock.get('foo')
    assert not lock.get('foo')
    lock.release('foo')

    assert lock.get('foo')
    assert not lock.get('foo')
    lock.release('foo')

def test_twolocks():
    assert lock.get('foo')
    assert lock.get('bar')
    assert not lock.get('foo')
    assert not lock.get('bar')
    lock.release('foo')
    lock.release('bar')

