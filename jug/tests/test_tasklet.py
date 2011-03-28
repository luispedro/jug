from jug.options import default_options
from jug.tests.task_reset import task_reset
import jug.jug

@task_reset
def test_tasklets():
    store, space = jug.jug.init('jug/tests/jugfiles/tasklets.py', 'dict_store')
    jug.jug.execute(store, default_options)
    assert space['t0'].value() == 0
    assert space['t2'].value() == 4
    assert space['t0_2'].value() == 4
    assert space['t0_2_1'].value() == 5

@task_reset
def test_iteratetask():
    store, space = jug.jug.init('jug/tests/jugfiles/iteratetask.py', 'dict_store')
    jug.jug.execute(store, default_options)
    assert space['t0'].value() == 0
    assert space['t1'].value() == 2
    assert space['t2'].value() == 4
