import inspect
import os

import jug.jug
import jug.task
from jug.task import Task
from jug.backends.dict_store import dict_store
from jug.tests.task_reset import task_reset
from jug.tests.utils import simple_execute
from jug.options import default_options

jug.jug.silent = True


_jugdir = os.path.abspath(inspect.getfile(inspect.currentframe()))
_jugdir = os.path.join(os.path.dirname(_jugdir), 'jugfiles')


def test_jug_check():
    N = 16
    A = [False for i in range(N)]
    def setAi(i):
        A[i] = True
        return i
    def first_two(one, two):
        return one+two

    setall = [Task(setAi, i) for i in range(N)]
    check = Task(first_two, setall[0], setall[1])
    check2 = Task(first_two, setall[1], setall[2])
    store = dict_store()
    jug.task.Task.store = store
    try:
        jug.jug.check(store, default_options)
    except SystemExit as e:
        assert e.code == 1
    else:
        assert False
    savedtasks = jug.task.alltasks[:]
    simple_execute()
    jug.task.alltasks = savedtasks

    try:
        jug.jug.check(store, default_options)
        assert False
    except SystemExit as e:
        assert e.code == 0
    else:
        assert False


@task_reset
def test_tasklet():
    jugfile = os.path.join(_jugdir, 'sleep_until_tasklet.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    assert 'four' not in space
    simple_execute()
    store, space = jug.jug.init(jugfile, store)
    assert jug.jug._check_or_sleep_until(store, False) == 0
    assert jug.jug._check_or_sleep_until(store, True) == 0
