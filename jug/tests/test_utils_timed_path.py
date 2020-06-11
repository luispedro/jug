from time import sleep
from os import path

import jug.utils
import jug.task
from jug import value
from jug.backends.dict_store import dict_store

def test_util_timed_path(tmpdir):
    from jug.hash import hash_one
    jug.task.Task.store = dict_store()
    tmpdir = str(tmpdir)
    test_file = path.join(tmpdir, 'test_file')
    with open(test_file, 'wt') as out:
        out.write("Hello World")
    t0 = jug.utils.timed_path(test_file)
    t1 = jug.utils.timed_path(test_file)
    h0 = hash_one(t0)
    h1 = hash_one(t1)
    assert h0 == h1
    sleep(1.1)
    with open(test_file, 'wt') as out:
        out.write("Hello World")
    h1 = hash_one(t1)
    assert h0 != h1
    assert value(t0) == test_file
    assert value(t1) == test_file

