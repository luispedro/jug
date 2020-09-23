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
    assert status.status(options) == 8 * 4

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

    assert status.status(options) == 0
    simple_execute()
    assert status.status(options) == 8 * 4

@task_reset
def test_cache_block_status():
    jugfile = os.path.join(_jugdir, 'block_access.py')

    options = default_options.copy()
    options.jugdir = 'dict_store'
    options.jugfile = jugfile
    options.verbose = 'quiet'
    options.status_cache = True
    options.status_cache_file = ':memory:'

    assert status.status(options) == 0

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

    assert status.status(options) == 0
    simple_execute()
    assert status.status(options) == 1

