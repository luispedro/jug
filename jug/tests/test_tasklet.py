import inspect
import os

from .task_reset import task_reset_at_exit, task_reset
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




def _tasklet_hash(f):
    from jug import Task, Tasklet
    return Tasklet(Task(abs, -1), f).__jug_hash__()


@task_reset
def test_lambda_hash_consts():
    assert _tasklet_hash(lambda v: v + 1) != _tasklet_hash(lambda v: v + 2)
    assert _tasklet_hash(lambda v: v + 1) == _tasklet_hash(lambda v: v + 1)


@task_reset
def test_lambda_hash_names():
    def gx(): return lambda v: v.real
    def gy(): return lambda v: v.imag
    assert _tasklet_hash(gx()) != _tasklet_hash(gy())


@task_reset
def test_lambda_hash_closure():
    def make(x):
        return lambda v: v + x
    assert _tasklet_hash(make(1)) != _tasklet_hash(make(2))
    assert _tasklet_hash(make(1)) == _tasklet_hash(make(1))


@task_reset
def test_lambda_hash_defaults():
    assert _tasklet_hash(lambda v, x=1: v + x) != _tasklet_hash(lambda v, x=2: v + x)
    assert _tasklet_hash(lambda v, *, x=1: v + x) != _tasklet_hash(lambda v, *, x=2: v + x)


@task_reset
def test_lambda_hash_unpicklable_closure():
    import sys
    def make(m):
        return lambda v: m
    # Must not raise
    _tasklet_hash(make(sys))
    _tasklet_hash(make(lambda: 0))
