from jug.backends.dict_store import dict_store
from jug.tests.utils import simple_execute
from jug.tests.task_reset import task_reset
import jug.jug

@task_reset
def test_w_barrier():
    store, space = jug.jug.init('jug/tests/jugfiles/custom_hash_function.py', 'dict_store')
    simple_execute()
    assert space['hash_called']
