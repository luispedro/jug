import inspect
import pytest
import os

import jug.jug
import jug.task
import jug.subcommands.check
from jug.task import Task
from jug.backends.dict_store import dict_store
from jug.tests.task_reset import task_reset_at_exit, task_reset
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
        jug.subcommands.check.check(store, default_options)
    except SystemExit as e:
        assert e.code == 1
    else:
        assert False
    savedtasks = jug.task.alltasks[:]
    simple_execute()
    jug.task.alltasks = savedtasks

    try:
        jug.subcommands.check.check(store, default_options)
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
    assert jug.subcommands.check._check_or_sleep_until(store, False) == 0
    assert jug.subcommands.check._check_or_sleep_until(store, True) == 0


@task_reset
def test_sleep_until_barrier_reload():
    import pytest
    jugfile = os.path.join(_jugdir, 'wbarrier.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    assert space['__jug__hasbarrier__']
    simple_execute()
    jug.jug.init(jugfile, store)
    simple_execute()
    # simple_execute() removes the executed tasks from alltasks
    jug.jug.init(jugfile, store)
    assert len(jug.task.alltasks) == 3

    options = default_options.copy()
    options.jugfile = jugfile
    options.jugdir = store
    with pytest.raises(SystemExit) as e:
        jug.subcommands.check.sleep_until.run(options, store, space)
    assert e.value.code == 0
    # The re-loaded jugfile has 3 tasks; they must not be duplicated
    assert len(jug.task.alltasks) == 3


def _run_jug(*args):
    '''Runs ``jug *args`` (in a clean task list) and returns its exit code'''
    import pytest
    del jug.task.alltasks[:]
    with pytest.raises(SystemExit) as e:
        jug.jug.main(['jug', *args, '--verbose', 'quiet', '--will-cite'])
    del jug.task.alltasks[:]
    return 0 if e.value.code is None else e.value.code


@task_reset
def test_check_selection(tmpdir, capsys):
    jugfile = os.path.join(_jugdir, 'simple_multiple.py')
    jugdir = str(tmpdir.join('jugdata'))
    assert _run_jug('execute', jugfile, '--jugdir', jugdir, '--name', 'sum_2') == 0

    def check(*extra):
        return _run_jug('check', jugfile, '--jugdir', jugdir, *extra)
    assert check() == 1
    assert check('--name', 'sum_2') == 0
    assert check('--name', 'sum_3') == 1
    # loose match: sum_2 and sum_3
    assert check('--pattern', 'sum_') == 1
    assert check('--pattern', '/sum_2$/') == 0
    assert check('--exclude-name', 'sum_3', '--exclude-pattern', 'tract') == 0
    assert check('--name', 'sum_*', '--exclude-name', 'sum_3') == 0
    assert check('--exclude-name', 'sum_3') == 1
    assert capsys.readouterr().err == ''


@task_reset
def test_check_no_match(tmpdir, capsys):
    jugfile = os.path.join(_jugdir, 'simple_multiple.py')
    jugdir = str(tmpdir.join('jugdata'))
    assert _run_jug('execute', jugfile, '--jugdir', jugdir) == 0
    assert _run_jug('check', jugfile, '--jugdir', jugdir) == 0
    capsys.readouterr()
    # A typo must not look like "all done"
    for cmd in ['check', 'sleep-until']:
        assert _run_jug(cmd, jugfile, '--jugdir', jugdir, '--name', 'sum_4') == 1
        assert 'no task matches' in capsys.readouterr().err
    assert _run_jug('check', jugfile, '--jugdir', jugdir,
                    '--exclude-pattern', '/^simple_multiple\\./') == 1
    assert 'no task matches' in capsys.readouterr().err


@task_reset
def test_check_barrier(tmpdir):
    # Matching tasks may be defined after the barrier, so check cannot say
    # that they are all done
    jugfile = os.path.join(_jugdir, 'barrier_exclude.py')
    jugdir = str(tmpdir.join('jugdata'))
    assert _run_jug('check', jugfile, '--jugdir', jugdir, '--name', 'after') == 1
    assert _run_jug('check', jugfile, '--jugdir', jugdir, '--name', 'nonexistent') == 1
    assert _run_jug('execute', jugfile, '--jugdir', jugdir,
                    '--exclude-name', 'after_skipped') == 0
    assert _run_jug('check', jugfile, '--jugdir', jugdir) == 1
    assert _run_jug('check', jugfile, '--jugdir', jugdir, '--name', 'after') == 0
    assert _run_jug('check', jugfile, '--jugdir', jugdir, '--exclude-name', 'after_skipped') == 0


@task_reset
def test_sleep_until_selection_barrier(tmpdir, monkeypatch):
    import time
    jugfile = os.path.join(_jugdir, 'barrier_exclude.py')
    jugdir = str(tmpdir.join('jugdata'))
    ran = []

    def fake_sleep(_):
        # Emulate a worker which runs everything except after_skipped
        ran.append([t.name for t in jug.task.alltasks])
        for t in list(jug.task.alltasks):
            if t.name != 'barrier_exclude.after_skipped' \
                    and not t.can_load() and t.can_run():
                t.run()
    monkeypatch.setattr(time, 'sleep', fake_sleep)

    assert _run_jug('sleep-until', jugfile, '--jugdir', jugdir, '--name', 'after') == 0
    # First, it waited for the tasks before the barrier (even though they do
    # not match), then (after re-loading) for the matching tasks
    assert len(ran) == 2
    assert set(ran[0]) == {'barrier_exclude.before'}
    assert 'barrier_exclude.after' in ran[1]

    assert _run_jug('check', jugfile, '--jugdir', jugdir, '--name', 'after') == 0
    assert _run_jug('check', jugfile, '--jugdir', jugdir, '--name', 'after_skipped') == 1


@task_reset
def test_sleep_until_selection_done(tmpdir, monkeypatch):
    import time
    jugfile = os.path.join(_jugdir, 'simple_multiple.py')
    jugdir = str(tmpdir.join('jugdata'))
    assert _run_jug('execute', jugfile, '--jugdir', jugdir, '--name', 'sum_2') == 0

    def fail_sleep(_):
        raise AssertionError('should not sleep')
    monkeypatch.setattr(time, 'sleep', fail_sleep)
    assert _run_jug('sleep-until', jugfile, '--jugdir', jugdir, '--name', 'sum_2') == 0
    assert _run_jug('sleep-until', jugfile, '--jugdir', jugdir,
                    '--exclude-pattern', '/sum_3|subtract/') == 0


@pytest.mark.parametrize('cmd,prefix', [('check', 'check'), ('sleep-until', 'sleep_until')])
def test_parse_selection(cmd, prefix):
    from jug.options import parse
    options = parse([cmd])
    assert getattr(options, f'{prefix}_name') is None
    assert getattr(options, f'{prefix}_pattern') is None
    assert getattr(options, f'{prefix}_exclude_name') == []
    assert getattr(options, f'{prefix}_exclude_pattern') == []

    options = parse([cmd, '--name', 'a', '--exclude-name', 'b', '--exclude-pattern', 'c',
                     '--exclude-name', 'd'])
    assert getattr(options, f'{prefix}_name') == 'a'
    assert getattr(options, f'{prefix}_exclude_name') == ['b', 'd']
    assert getattr(options, f'{prefix}_exclude_pattern') == ['c']

    with pytest.raises(SystemExit):
        parse([cmd, '--name', 'a', '--pattern', 'b'])
    with pytest.raises(SystemExit):
        parse([cmd, '--exclude-pattern', ''])
