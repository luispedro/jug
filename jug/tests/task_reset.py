from nose.tools import with_setup
import jug.task
from jug.backends.dict_store import dict_store
from jug.hooks import reset_all_hooks

def _setup():
    jug.task.Task.store = dict_store()
    while jug.task.alltasks:
        jug.task.alltasks.pop()

def _teardown():
    jug.task.Task.store = None
    while jug.task.alltasks:
        jug.task.alltasks.pop()
    reset_all_hooks()

task_reset = with_setup(_setup, _teardown)
