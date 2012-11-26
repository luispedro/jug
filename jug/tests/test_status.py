from jug.subcommands import status
from jug.tests.task_reset import task_reset
from jug.tests.utils import simple_execute
from jug.options import default_options
import jug

@task_reset
def test_nocache():
    store, space = jug.jug.init('jug/tests/jugfiles/simple.py', 'dict_store')
    simple_execute()

    options = default_options.copy()
    options.jugdir = store
    options.jugfile = 'jug/tests/jugfiles/simple.py'
    options.verbose = 'quiet'
    assert status.status(options) == 8 * 4

@task_reset
def test_cache():
    store, space = jug.jug.init('jug/tests/jugfiles/simple.py', 'dict_store')

    options = default_options.copy()
    options.jugdir = store
    options.jugfile = 'jug/tests/jugfiles/simple.py'
    options.verbose = 'quiet'
    options.status_mode = 'cached'
    options.status_cache_file = ':memory:'

    assert status.status(options) == 0
    simple_execute()
    assert status.status(options) == 8 * 4

@task_reset
def test_cache_bvalue():
    store, space = jug.jug.init('jug/tests/jugfiles/bvalue.py', 'dict_store')

    options = default_options.copy()
    options.jugdir = store
    options.jugfile = 'jug/tests/jugfiles/bvalue.py'
    options.verbose = 'quiet'
    options.status_mode = 'cached'
    options.status_cache_file = ':memory:'

    assert status.status(options) == 0
    simple_execute()
    assert status.status(options) == 1

