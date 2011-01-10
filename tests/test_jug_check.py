import jug.jug
import jug.task
from jug.task import Task
from jug.backends.dict_store import dict_store
from tests.task_reset import task_reset
from jug.options import Options, default_options

import random
jug.jug.silent = True

def test_jug_check():
    N = 16
    A = [False for i in xrange(N)]
    def setAi(i):
        A[i] = True
        return i
    def first_two(one, two):
        return one+two

    setall = [Task(setAi, i) for i in xrange(N)]
    check = Task(first_two, setall[0], setall[1])
    check2 = Task(first_two, setall[1], setall[2])
    store = dict_store()
    jug.task.Task.store = store
    e = None
    try:
        jug.jug.check(store, default_options)
    except SystemExit, e:
        pass
    assert e is not None
    assert e.code == 1
    savedtasks = jug.task.alltasks[:]
    jug.jug.execute(store, default_options)
    jug.task.alltasks = savedtasks

    e = None
    try:
        jug.jug.check(store, default_options)
        assert False
    except SystemExit, e:
        pass
    assert e is not None
    assert e.code == 0

