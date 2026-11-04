import inspect
import os

from jug.options import default_options
from jug.subcommands import status
from .task_reset import task_reset_at_exit, task_reset
from .utils import simple_execute
import jug


_jugdir = os.path.abspath(inspect.getfile(inspect.currentframe()))
_jugdir = os.path.join(os.path.dirname(_jugdir), 'jugfiles')


@task_reset
def test_nocache():
    jugfile = os.path.join(_jugdir, 'simple.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    simple_execute()

    options = default_options.copy()
    options.jugdir = store
    options.jugfile = jugfile
    options.verbose = 'quiet'
    assert sum(status._status(options).finished.values()) == 8 * 4

@task_reset
def test_cache():
    jugfile = os.path.join(_jugdir, 'simple.py')
    store, space = jug.jug.init(jugfile, 'dict_store')

    options = default_options.copy()
    options.jugdir = store
    options.jugfile = jugfile
    options.verbose = 'quiet'
    options.status_cache = True
    options.status_cache_file = ':memory:'

    assert sum(status._status(options).finished.values()) == 0
    simple_execute()
    assert sum(status._status(options).finished.values()) == 8 * 4

@task_reset
def test_cache_block_status():
    jugfile = os.path.join(_jugdir, 'block_access.py')

    options = default_options.copy()
    options.jugdir = 'dict_store'
    options.jugfile = jugfile
    options.verbose = 'quiet'
    options.status_cache = True
    options.status_cache_file = ':memory:'

    assert sum(status._status(options).finished.values()) == 0

@task_reset
def test_cache_bvalue():
    jugfile = os.path.join(_jugdir, 'bvalue.py')
    store, space = jug.jug.init(jugfile, 'dict_store')

    options = default_options.copy()
    options.jugdir = store
    options.jugfile = jugfile
    options.verbose = 'quiet'
    options.status_cache = True
    options.status_cache_file = ':memory:'

    assert sum(status._status(options).finished.values()) == 0
    simple_execute()
    assert sum(status._status(options).finished.values()) == 1


@task_reset
def test_status_exit_code(tmpdir):
    # Like `jug check`, `jug status` exits with 0 iff all tasks are finished
    jugfile = os.path.join(_jugdir, 'simple.py')
    jugdir = str(tmpdir.join('jugdata'))
    def exit_code(subcommand, *extra):
        try:
            jug.jug.main(['jug', subcommand, jugfile, '--jugdir', jugdir, '--verbose', 'quiet'] + list(extra))
        except SystemExit as e:
            return e.code
        assert False

    cache_file = str(tmpdir.join('status.sqlite3'))
    assert exit_code('status') == 1
    assert exit_code('status', '--cache', '--cache-file', cache_file) == 1
    assert not exit_code('execute')
    assert exit_code('status') == 0
    assert exit_code('status', '--cache', '--cache-file', cache_file) == 0


def test_open_connection_closes_on_error(tmpdir, monkeypatch):
    import sqlite3
    import pytest
    connections = []
    orig_connect = sqlite3.connect

    class RecordingConnection:
        def __init__(self, *args):
            self.conn = orig_connect(*args)
            self.closed = False
            connections.append(self)
        def __getattr__(self, name):
            return getattr(self.conn, name)
        def close(self):
            self.closed = True
            self.conn.close()

    monkeypatch.setattr(sqlite3, 'connect', RecordingConnection)
    options = default_options.copy()
    options.status_cache_file = str(tmpdir / 'cache.sqlite3')
    with pytest.raises(sqlite3.OperationalError):
        with status._open_connection(options) as connection:
            connection.execute('SELECT * FROM missing_table')
    assert len(connections) == 1
    assert connections[0].closed


@task_reset
def test_cache_corrupt_file(tmpdir):
    import pytest
    cache_file = tmpdir / 'cache.sqlite3'
    cache_file.write('this is not an sqlite3 database\n' * 64)

    options = default_options.copy()
    options.jugdir = 'dict_store'
    options.jugfile = os.path.join(_jugdir, 'simple.py')
    options.verbose = 'quiet'
    options.status_cache = True
    options.status_cache_file = str(cache_file)
    with pytest.raises(SystemExit) as e:
        status._status(options)
    assert str(cache_file) in str(e.value.code)
    assert '--clear' in str(e.value.code)


@task_reset
def test_cache_cannot_open(tmpdir):
    import pytest
    options = default_options.copy()
    options.jugdir = 'dict_store'
    options.jugfile = os.path.join(_jugdir, 'simple.py')
    options.verbose = 'quiet'
    options.status_cache = True
    options.status_cache_file = str(tmpdir / 'nonexistent-dir' / 'cache.sqlite3')
    with pytest.raises(SystemExit) as e:
        status._status(options)
    assert options.status_cache_file in str(e.value.code)


@task_reset
def test_cache_cannot_write(tmpdir, monkeypatch):
    import sqlite3
    import pytest
    options = default_options.copy()
    options.jugdir = 'dict_store'
    options.jugfile = os.path.join(_jugdir, 'simple.py')
    options.verbose = 'quiet'
    options.status_cache = True
    options.status_cache_file = str(tmpdir / 'cache.sqlite3')

    def fail(*args):
        raise sqlite3.OperationalError('database is locked')
    monkeypatch.setattr(status, 'create_sqlite3', fail)
    with pytest.raises(SystemExit) as e:
        status._status(options)
    assert options.status_cache_file in str(e.value.code)
    assert 'database is locked' in str(e.value.code)


def _run_jug(*args):
    '''Runs ``jug *args`` and returns its exit code'''
    try:
        jug.jug.main(['jug', *args, '--verbose', 'quiet'])
    except SystemExit as e:
        return 0 if e.code is None else e.code
    assert False, 'jug.jug.main did not exit'


def _status_json(capsys, jugfile, jugdir, *extra):
    import json
    capsys.readouterr()
    code = _run_jug('status', jugfile, '--jugdir', jugdir, '--json', *extra)
    out = capsys.readouterr().out
    return code, json.loads(out)


_STATES = ['waiting', 'ready', 'running', 'failed', 'finished']


def _check_json_format(data):
    assert set(data.keys()) == {'jug_version', 'has_barrier', 'tasks', 'total'}
    assert data['jug_version'] == jug.__version__
    for counts in list(data['tasks'].values()) + [data['total']]:
        assert list(counts.keys()) == _STATES
    for st in _STATES:
        assert data['total'][st] == sum(c[st] for c in data['tasks'].values())


@task_reset
def test_json_all_states(tmpdir, capsys):
    from jug.task import alltasks
    jugfile = os.path.join(_jugdir, 'simple.py')
    jugdir = str(tmpdir.join('jugdata'))
    cache_file = str(tmpdir.join('status.sqlite3'))

    assert _run_jug('execute', jugfile, '--jugdir', jugdir, '--name', 'double') == 0
    # Hold the lock of one plus1 task (running) and mark another as failed
    store, _ = jug.jug.init(jugfile, jugdir)
    plus1 = [t for t in alltasks if t.name == 'simple.plus1']
    assert store.getlock(plus1[0].hash()).get()
    lock = store.getlock(plus1[1].hash())
    assert lock.get()
    lock.fail()

    expected = {
        'simple.double': {'waiting': 0, 'ready': 0, 'running': 0, 'failed': 0, 'finished': 8},
        'simple.plus1': {'waiting': 0, 'ready': 6, 'running': 1, 'failed': 1, 'finished': 0},
        'simple.sum2': {'waiting': 16, 'ready': 0, 'running': 0, 'failed': 0, 'finished': 0},
    }
    for extra in [(), ('--cache', '--cache-file', cache_file)]:
        code, data = _status_json(capsys, jugfile, jugdir, *extra)
        _check_json_format(data)
        assert code == 1
        assert data['has_barrier'] is False
        assert data['tasks'] == expected
        assert data['total'] == {'waiting': 16, 'ready': 6, 'running': 1, 'failed': 1, 'finished': 8}

    store.remove_locks()
    assert _run_jug('execute', jugfile, '--jugdir', jugdir) == 0
    for extra in [(), ('--cache', '--cache-file', cache_file)]:
        code, data = _status_json(capsys, jugfile, jugdir, *extra)
        assert code == 0
        assert data['total'] == {'waiting': 0, 'ready': 0, 'running': 0, 'failed': 0, 'finished': 32}


@task_reset
def test_json_keep_failed(tmpdir, capsys):
    # failed tasks are only reported if the worker used --keep-failed
    jugfile = os.path.join(_jugdir, 'failing.py')
    jugdir = str(tmpdir.join('jugdata'))
    assert _run_jug('execute', jugfile, '--jugdir', jugdir,
                    '--keep-going', '--keep-failed', '--nr-wait-cycles', '0') == 1
    code, data = _status_json(capsys, jugfile, jugdir)
    _check_json_format(data)
    assert code == 1
    assert data['tasks']['failing.some_fail']['failed'] == 3
    assert data['tasks']['failing.some_fail']['finished'] == 7
    assert data['tasks']['failing.plus1']['waiting'] == 3
    assert data['tasks']['failing.plus1']['finished'] == 7


@task_reset
def test_json_agrees_with_status(tmpdir, capsys):
    jugfile = os.path.join(_jugdir, 'simple.py')
    jugdir = str(tmpdir.join('jugdata'))
    assert _run_jug('execute', jugfile, '--jugdir', jugdir, '--name', 'double') == 0
    _, data = _status_json(capsys, jugfile, jugdir)

    options = default_options.copy()
    options.jugdir = jugdir
    options.jugfile = jugfile
    options.print_out = lambda *args, **kwargs: None
    ts = status._status(options)
    assert ts.counts() == data['tasks']
    assert ts.totals() == data['total']


@task_reset
def test_json_jugfile_output_goes_to_stderr(tmpdir, capsys):
    import json
    jugfile = tmpdir.join('printing.py')
    jugfile.write('''
from jug import TaskGenerator
print('printed by the jugfile')

@TaskGenerator
def f(x):
    return x
f(1)
''')
    jugdir = str(tmpdir.join('jugdata'))
    capsys.readouterr()
    assert _run_jug('status', str(jugfile), '--jugdir', jugdir, '--json') == 1
    captured = capsys.readouterr()
    assert 'printed by the jugfile' in captured.err
    assert json.loads(captured.out)['total']['ready'] == 1


@task_reset
def test_json_import_error_not_on_stdout(tmpdir, capsys):
    jugfile = tmpdir.join('broken.py')
    jugfile.write('raise RuntimeError("broken jugfile")\n')
    capsys.readouterr()
    assert _run_jug('status', str(jugfile), '--jugdir', str(tmpdir.join('jugdata')), '--json') == 1
    captured = capsys.readouterr()
    assert captured.out == ''
    assert 'broken jugfile' in captured.err


@task_reset
def test_barrier_status(tmpdir, capsys):
    jugfile = os.path.join(_jugdir, 'wbarrier.py')
    jugdir = str(tmpdir.join('jugdata'))
    cache_file = str(tmpdir.join('status.sqlite3'))
    for extra in [(), ('--cache', '--cache-file', cache_file)]:
        code, data = _status_json(capsys, jugfile, jugdir, *extra)
        assert code == 1
        assert data['has_barrier'] is True
        assert data['total']['ready'] == 1

    assert _run_jug('execute', jugfile, '--jugdir', jugdir) == 0
    code, data = _status_json(capsys, jugfile, jugdir)
    assert code == 0
    assert data['has_barrier'] is False
    assert data['total']['finished'] == 3

    # The cache was built when loading stopped at the barrier, so it does not
    # know about the later tasks: the exit code must not claim completion
    code, data = _status_json(capsys, jugfile, jugdir, '--cache', '--cache-file', cache_file)
    assert data['has_barrier'] is True
    assert data['total']['finished'] == 1
    assert code == 1
    # The same applies to the plain output
    assert _run_jug('status', jugfile, '--jugdir', jugdir, '--cache', '--cache-file', cache_file) == 1

    assert _run_jug('status', jugfile, '--jugdir', jugdir,
                    '--cache', '--cache-file', cache_file, '--clear') == 0
    code, data = _status_json(capsys, jugfile, jugdir, '--cache', '--cache-file', cache_file)
    assert code == 0
    assert data['has_barrier'] is False
    assert data['total']['finished'] == 3


@task_reset
def test_cache_without_meta(tmpdir, capsys):
    # A cache built by an older version of jug does not record whether a
    # barrier was hit
    import sqlite3
    jugfile = os.path.join(_jugdir, 'simple.py')
    jugdir = str(tmpdir.join('jugdata'))
    cache_file = str(tmpdir.join('status.sqlite3'))
    assert _run_jug('execute', jugfile, '--jugdir', jugdir) == 0
    _status_json(capsys, jugfile, jugdir, '--cache', '--cache-file', cache_file)
    with sqlite3.connect(cache_file) as connection:
        connection.execute('DROP TABLE meta')
    connection.close()
    code, data = _status_json(capsys, jugfile, jugdir, '--cache', '--cache-file', cache_file)
    assert data['has_barrier'] is None
    assert code == 0


def test_parse_json():
    from jug.options import parse
    assert parse(['status']).status_json is False
    assert parse(['status', '--json']).status_json is True
