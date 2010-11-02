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

def product(vals):
    import operator
    return reduce(operator.mul, vals)

@task_reset
def test_mapreduce_barrier():
    store, space = jug.jug.init('tests/jugfiles/barrier_mapreduce.py', 'dict_store')
    assert 'values' not in space
    jug.jug.execute(store)
    store, space = jug.jug.init('tests/jugfiles/barrier_mapreduce.py', store)
    assert 'values' in space
    assert space['values'] == product(range(20))
    jug.jug.execute(store)

