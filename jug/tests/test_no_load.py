import jug.jug
import jug.subcommands.execute
from .task_reset import task_reset_at_exit, task_reset
from .utils import simple_execute, find_test_jugfile

@task_reset
def test_no_load():
    jugfile = find_test_jugfile('no_load.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    x = space['x']
    assert not x.can_run()
    simple_execute()
    assert     x.can_run()
