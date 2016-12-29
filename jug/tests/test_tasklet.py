import inspect
import os

from jug.tests.task_reset import task_reset
from jug.tests.utils import simple_execute
import jug.jug


_jugdir = os.path.abspath(inspect.getfile(inspect.currentframe()))
_jugdir = os.path.join(os.path.dirname(_jugdir), 'jugfiles')


@task_reset
def test_tasklets():
    jugfile = os.path.join(_jugdir, 'tasklets.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    simple_execute()
    assert space['t0'].value() == 0
    assert space['t2'].value() == 4
    assert space['t0_2'].value() == 4
    assert space['t0_2_1'].value() == 5

@task_reset
def test_iteratetask():
    jugfile = os.path.join(_jugdir, 'iteratetask.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    simple_execute()
    assert space['t0'].value() == 0
    assert space['t1'].value() == 2
    assert space['t2'].value() == 4

@task_reset
def test_tasklet_dependencies():
    jugfile = os.path.join(_jugdir, 'tasklets.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    assert not space['t0_2'].can_run()


@task_reset
def test_tasklet_slice_dependencies():
    jugfile = os.path.join(_jugdir, 'slice_task.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    simple_execute()
    assert space['z2'].value() == 0
    assert space['z2_2'].value() == 0
    assert space['z3'].value() == 1


