from time import sleep
from os import system
from nose.tools import with_setup

import jug.utils
import jug.task                             
from jug.backends.dict_store import dict_store

def _remove_test_file():
    system("rm test_file")

@with_setup(teardown=_remove_test_file)
def test_util_timed_path():
    Task = jug.task.Task
    jug.task.Task.store = dict_store()
    system("touch test_file")
    t0 = jug.utils.timed_path('test_file')
    t1 = jug.utils.timed_path('test_file')
    assert t0.hash() == t1.hash()
    sleep(1.1)
    system("touch test_file")
    t1 = jug.utils.timed_path('test_file')
    assert t0.hash() != t1.hash()
    assert t0.run() == 'test_file'
    assert t1.run() == 'test_file'

