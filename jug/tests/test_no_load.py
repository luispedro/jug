import inspect
import os

import jug.jug
import jug.subcommands.execute
from jug.tests.task_reset import task_reset
from jug.tests.utils import simple_execute


_jugdir = os.path.abspath(inspect.getfile(inspect.currentframe()))
_jugdir = os.path.join(os.path.dirname(_jugdir), 'jugfiles')


@task_reset
def test_no_load():
    jugfile = os.path.join(_jugdir, 'no_load.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    x = space['x']
    assert not x.can_run()
    simple_execute()
    assert     x.can_run()
