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


def test_register_time_tasks_twice(reset_hooks_at_exit, capsys):
    from jug.hooks.execution import register_time_tasks
    # A jugfile with barriers is imported several times
    register_time_tasks()
    register_time_tasks()
    jug_hook('execute.finished_post_status')
    assert capsys.readouterr().out.count('TIMES') == 1


def test_exit_checks_register_once(reset_hooks_at_exit):
    from jug.hooks import register
    from jug.hooks.exit_checks import exit_after_n_tasks, exit_after_time, exit_if_file_exists
    # A jugfile with barriers is imported several times
    for _ in range(3):
        exit_after_n_tasks(10)
        exit_after_time(hours=1)
        exit_if_file_exists('__no_such_file__')
    assert len(register._hooks['execute.task-executed1']) == 2
    assert len(register._hooks['execute.task-pre-execute']) == 1

    # Different arguments are separate hooks
    exit_after_n_tasks(20)
    assert len(register._hooks['execute.task-executed1']) == 3


def test_exit_after_n_tasks_counts_from_first_call(reset_hooks_at_exit):
    from jug.hooks.exit_checks import exit_after_n_tasks
    exit_after_n_tasks(2)
    jug_hook('execute.task-executed1', (None,))
    exit_after_n_tasks(2)
    with pytest.raises(SystemExit):
        jug_hook('execute.task-executed1', (None,))


def test_exit_when_true_register_once(reset_hooks_at_exit):
    from jug.hooks import register
    from jug.hooks.exit_checks import exit_when_true
    # Re-loading a jugfile re-creates its functions, with the same code
    src = 'def check():\n    return False\n'
    for _ in range(3):
        space = {}
        exec(compile(src, 'jugfile.py', 'exec'), space)
        exit_when_true(space['check'])
    assert len(register._hooks['execute.task-executed1']) == 1

    # Functions with a closure cannot be told apart by their code, so they
    # are always registered
    for v in [False, True]:
        exit_when_true(lambda: v)
    assert len(register._hooks['execute.task-executed1']) == 3
