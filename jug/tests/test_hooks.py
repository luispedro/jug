import pytest

from jug.hooks import register_hook, register_hook_once, reset_all_hooks, jug_hook

A = []
def inc_A():
    A.append(0)


@pytest.fixture(scope='function')
def reset_hooks_at_exit():
    yield
    reset_all_hooks()
    del A[:] # A.clear() is not available in Python 2.x

def test_basic(reset_hooks_at_exit):
    assert len(A) == 0
    register_hook('execute.task-executed1', inc_A)
    jug_hook('execute.task-executed1')
    assert len(A) == 1

def test_register_twice(reset_hooks_at_exit):
    register_hook('execute.task-executed1', inc_A)
    register_hook('execute.task-executed1', inc_A)
    jug_hook('execute.task-executed1')
    assert len(A) == 2

def test_reset_all_hooks(reset_hooks_at_exit):
    register_hook('execute.task-executed1', inc_A)
    jug_hook('execute.task-executed1')
    assert len(A) == 1
    reset_all_hooks()
    jug_hook('execute.task-executed1')
    assert len(A) == 1

def test_register_once(reset_hooks_at_exit):
    assert len(A) == 0
    register_hook_once('execute.task-executed1', 'just-testing-mate', inc_A)
    register_hook_once('execute.task-executed1', 'just-testing-mate', inc_A)
    register_hook_once('execute.task-executed1', 'just-testing-mate', inc_A)
    register_hook_once('execute.task-executed1', 'just-testing-mate', inc_A)
    register_hook_once('execute.task-executed1', 'just-testing-mate', inc_A)
    assert len(A) == 0
    jug_hook('execute.task-executed1')
    assert len(A) == 1

def test_bad_name():
    with pytest.raises(ValueError):
        register_hook('my_bad_hook', inc_A)

