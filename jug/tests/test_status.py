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
