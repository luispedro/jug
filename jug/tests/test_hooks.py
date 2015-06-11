from nose.tools import with_setup, raises

from jug.hooks import register_hook, register_hook_once, reset_all_hooks, jug_hook

A = []
def inc_A():
    A.append(0)

def teardown():
    reset_all_hooks()
    del A[:] # A.clear() is not available in Python 2.x

@with_setup(teardown=teardown)
def test_basic():
    assert len(A) == 0
    register_hook('execute.task-executed1', inc_A)
    jug_hook('execute.task-executed1')
    assert len(A) == 1

@with_setup(teardown=teardown)
def test_register_twice():
    register_hook('execute.task-executed1', inc_A)
    register_hook('execute.task-executed1', inc_A)
    jug_hook('execute.task-executed1')
    assert len(A) == 2

@with_setup(teardown=teardown)
def test_reset_all_hooks():
    register_hook('execute.task-executed1', inc_A)
    jug_hook('execute.task-executed1')
    assert len(A) == 1
    reset_all_hooks()
    jug_hook('execute.task-executed1')
    assert len(A) == 1

@with_setup(teardown=teardown)
def test_register_once():
    assert len(A) == 0
    register_hook_once('execute.task-executed1', 'just-testing-mate', inc_A)
    register_hook_once('execute.task-executed1', 'just-testing-mate', inc_A)
    register_hook_once('execute.task-executed1', 'just-testing-mate', inc_A)
    register_hook_once('execute.task-executed1', 'just-testing-mate', inc_A)
    register_hook_once('execute.task-executed1', 'just-testing-mate', inc_A)
    assert len(A) == 0
    jug_hook('execute.task-executed1')
    assert len(A) == 1

@raises(ValueError)
def test_bad_name():
    register_hook('my_bad_hook', inc_A)

