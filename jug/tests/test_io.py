import jug.jug
from jug.tests.utils import simple_execute
from jug.backends.dict_store import dict_store
from .task_reset import task_reset
from jug.task import describe

@task_reset
def test_describe():
    jugfile = 'jug/tests/jugfiles/simple.py'
    store, space = jug.jug.init(jugfile, 'dict_store')
    simple_execute()
    t = space['vals'][0]
    desc = describe(t)
    assert len(desc['args']) == len(t.args)

