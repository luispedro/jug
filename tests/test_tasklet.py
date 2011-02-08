from jug.options import default_options
from tests.task_reset import task_reset
import jug.jug

@task_reset
def test_barrier():
    store, space = jug.jug.init('tests/jugfiles/tasklets.py', 'dict_store')
    jug.jug.execute(store, default_options)
    assert space['t0'].value() == 0
    assert space['t2'].value() == 4
    assert space['t0_2'].value() == 4
    assert space['t0_2_1'].value() == 5
