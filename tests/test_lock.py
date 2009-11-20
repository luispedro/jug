from jug.backends.file_store import file_based_lock

def test_twice():
    lock = file_based_lock('jugtests', 'foo')
    assert lock.get()
    assert not lock.get()
    lock.release()

    assert lock.get()
    assert not lock.get()
    lock.release()

def test_twolocks():
    foo = file_based_lock('jugtests', 'foo')
    bar = file_based_lock('jugtests', 'bar')
    assert foo.get()
    assert bar.get()
    assert not foo.get()
    assert not bar.get()
    foo.release()
    bar.release()

