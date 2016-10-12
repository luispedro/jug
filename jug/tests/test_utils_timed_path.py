from time import sleep
from os import system
from .utils import remove_files

import jug.utils
import jug.task
from jug import value
from jug.backends.dict_store import dict_store

def _remove_test_file():
    system("rm test_file")

@remove_files(['test_file'])
def test_util_timed_path():
    from jug.hash import hash_one
    jug.task.Task.store = dict_store()
    system("touch test_file")
    t0 = jug.utils.timed_path('test_file')
    t1 = jug.utils.timed_path('test_file')
    h0 = hash_one(t0)
    h1 = hash_one(t1)
    assert h0 == h1
    sleep(1.1)
    system("touch test_file")
    h1 = hash_one(t1)
    assert h0 != h1
    assert value(t0) == 'test_file'
    assert value(t1) == 'test_file'

