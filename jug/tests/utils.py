import inspect
from os import path
import pytest

@pytest.fixture(scope='function')
def tmp_file_store(tmpdir):
    from jug.backends.file_store import file_store
    from jug import task
    prev = task.Task.store
    yield file_store(str(tmpdir))
    task.Task.store = prev


def simple_execute():
    from jug.jug import execution_loop
    from jug.task import alltasks
    from jug.options import parse
    execution_loop(alltasks, parse(['execute']))

_jugdir = path.abspath(inspect.getfile(inspect.currentframe()))
_jugdir = path.join(path.dirname(_jugdir), 'jugfiles')

def find_test_jugfile(jugfile):
    return path.join(_jugdir, jugfile)

