import jug.jug
from jug.tests.utils import simple_execute
from jug.backends.dict_store import dict_store
from .task_reset import task_reset
from jug.task import describe
from nose.tools import with_setup

def remove_files(flist, dlist):
    def teardown():
        from os import unlink
        for f in flist:
            try:
                unlink(f)
            except:
                pass
        from shutil import rmtree
        for dir in dlist:
            try:
                rmtree(dir)
            except:
                pass
    return with_setup(None, teardown)

@task_reset
def test_describe():
    jugfile = 'jug/tests/jugfiles/simple.py'
    store, space = jug.jug.init(jugfile, 'dict_store')
    simple_execute()
    t = space['vals'][0]
    desc = describe(t)
    assert len(desc['args']) == len(t.args)

@remove_files(['x.pkl', 'x.meta.yaml', 'x.meta.json'], ['testing_TO_DELETE.jugdata'])
@task_reset
def test_describe():
    jugfile = 'jug/tests/jugfiles/write_with_meta.py'
    store, space = jug.jug.init(jugfile, 'testing_TO_DELETE.jugdata')
    simple_execute()
    x = space['x']
    desc = describe(x)
    import json
    assert desc == json.load(open('x.meta.json'))
    import yaml
    assert desc == yaml.load(open('x.meta.yaml'))
