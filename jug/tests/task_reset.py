import pytest
import jug.task
from jug.backends.dict_store import dict_store
from jug.hooks import reset_all_hooks

@pytest.fixture(scope='function')
def task_reset_at_exit():
    jug.task.Task.store = dict_store()
    while jug.task.alltasks:
        jug.task.alltasks.pop()

    yield

    jug.task.Task.store = None
    while jug.task.alltasks:
        jug.task.alltasks.pop()
    reset_all_hooks()

def task_reset(f):
    return pytest.mark.usefixtures('task_reset_at_exit')(f)
