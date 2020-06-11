import pytest

import jug.jug
from jug.tests.utils import simple_execute
from jug.task import describe
from .task_reset import task_reset_at_exit, task_reset
from .utils import find_test_jugfile


@task_reset
def test_describe():
    jugfile = find_test_jugfile('simple.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    simple_execute()
    t = space['vals'][0]
    desc = describe(t)
    assert len(desc['args']) == len(t.args)

@pytest.fixture
def __remove_files():
    yield
    from os import unlink
    from shutil import rmtree
    for f in ['x.pkl', 'x.meta.yaml', 'x.meta.json']:
        try:
            unlink(f)
        except:
            pass
    try:
        rmtree('testing_TO_DELETE.jugdata')
    except:
        pass

@task_reset
def test_describe_load(__remove_files):
    jugfile = find_test_jugfile('write_with_meta.py')
    store, space = jug.jug.init(jugfile, 'testing_TO_DELETE.jugdata')
    simple_execute()
    x = space['x']
    desc = describe(x)
    import json
    assert desc == json.load(open('x.meta.json'))
    import yaml
    assert desc == yaml.safe_load(open('x.meta.yaml'))
