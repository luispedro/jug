import inspect
import os

from jug.tests.utils import simple_execute
from jug.tests.task_reset import task_reset
import jug.jug


_jugdir = os.path.abspath(inspect.getfile(inspect.currentframe()))
_jugdir = os.path.join(os.path.dirname(_jugdir), 'jugfiles')


@task_reset
def test_w_barrier():
    jugfile = os.path.join(_jugdir, 'custom_hash_function.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    simple_execute()
    assert space['hash_called']
