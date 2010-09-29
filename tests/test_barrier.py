import jug.jug
from tests.task_reset import task_reset

@task_reset
def test_barrier():
    store, space = jug.jug.init('tests/jugfiles/wbarrier.py', 'dict_store')
    assert 'four' not in space
    jug.jug.execute(store)
    store, space = jug.jug.init('tests/jugfiles/wbarrier.py', store)
    assert 'four' in space

    # This is a regression test:
    # a test version of jug would fail here:
    jug.jug.execute(store)
