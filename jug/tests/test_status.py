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
