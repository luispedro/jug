import pytest

from jug.hooks import register_hook, register_hook_once, reset_all_hooks, jug_hook

A = []
def inc_A():
    A.append(0)


@pytest.fixture(scope='function')
def reset_hooks_at_exit():
    yield
    reset_all_hooks()
    A.clear()


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


def test_exit_when_true(reset_hooks_at_exit):
    from jug.hooks.exit_checks import exit_when_true
    flag = [False]
    exit_when_true(lambda: flag[0])
    jug_hook('execute.task-executed1', (None,))
    flag[0] = True
    with pytest.raises(SystemExit):
        jug_hook('execute.task-executed1', (None,))

def test_exit_when_true_takes_task(reset_hooks_at_exit):
    from jug.hooks.exit_checks import exit_when_true
    exit_when_true(lambda t: t == 'stop', function_takes_Task=True)
    jug_hook('execute.task-executed1', ('go',))
    with pytest.raises(SystemExit):
        jug_hook('execute.task-executed1', ('stop',))
