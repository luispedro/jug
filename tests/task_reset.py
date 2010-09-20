from nose.tools import with_setup
import jug.task
from jug.backends.dict_store import dict_store

def _setup():
    jug.task.Task.store = dict_store()
    while jug.task.alltasks:
        jug.task.alltasks.pop()

def _teardown():
    jug.task.Task.store = None
    while jug.task.alltasks:
        jug.task.alltasks.pop()

task_reset = with_setup(_setup, _teardown)
