import inspect
import os

import jug.jug
from jug.tests.utils import simple_execute
from jug.task import describe
from .task_reset import task_reset
from .utils import remove_files

_jugdir = os.path.abspath(inspect.getfile(inspect.currentframe()))
_jugdir = os.path.join(os.path.dirname(_jugdir), 'jugfiles')


@task_reset
def test_describe():
    jugfile = os.path.join(_jugdir, 'simple.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    simple_execute()
    t = space['vals'][0]
    desc = describe(t)
    assert len(desc['args']) == len(t.args)

@remove_files(['x.pkl', 'x.meta.yaml', 'x.meta.json'], ['testing_TO_DELETE.jugdata'])
@task_reset
def test_describe_load():
    jugfile = os.path.join(_jugdir, 'write_with_meta.py')
    store, space = jug.jug.init(jugfile, 'testing_TO_DELETE.jugdata')
    simple_execute()
    x = space['x']
    desc = describe(x)
    import json
    assert desc == json.load(open('x.meta.json'))
    import yaml
    assert desc == yaml.load(open('x.meta.yaml'))
