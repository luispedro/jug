from jug.tests.task_reset import task_reset
from jug.tests.utils import simple_execute
from jug import task
import jug.jug

@task_reset
def test_tasklets():
    store, space = jug.jug.init('jug/tests/jugfiles/tasklets.py', 'dict_store')
    simple_execute()
    assert space['t0'].value() == 0
    assert space['t2'].value() == 4
    assert space['t0_2'].value() == 4
    assert space['t0_2_1'].value() == 5

@task_reset
def test_iteratetask():
    store, space = jug.jug.init('jug/tests/jugfiles/iteratetask.py', 'dict_store')
    simple_execute()
    assert space['t0'].value() == 0
    assert space['t1'].value() == 2
    assert space['t2'].value() == 4

@task_reset
def test_tasklet_dependencies():
    store, space = jug.jug.init('jug/tests/jugfiles/tasklets.py', 'dict_store')
    assert not space['t0_2'].can_run()


@task_reset
def test_tasklet_dependencies():
    store, space = jug.jug.init('jug/tests/jugfiles/slice_task.py', 'dict_store')
    simple_execute()
    assert space['z2'].value() == 0


