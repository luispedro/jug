from nose.tools import with_setup
import jug.task
from jug.backends.dict_store import dict_store

def _setup():
    jug.task.Task.store = dict_store()
def _teardown():
    jug.task.alltasks = []
task_reset = with_setup(_setup, _teardown)
