import jug.jug

def test_barrier():
    store, module = jug.jug.init('tests.jugfiles.wbarrier', 'dict_store')
    assert module is None
    jug.task.alltasks[0].run()
    store, module = jug.jug.init('tests.jugfiles.wbarrier', store)
    assert module is not None

