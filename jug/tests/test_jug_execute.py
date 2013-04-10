import jug.jug
import jug.task
from jug.task import Task
from jug.tests.utils import simple_execute
from jug.backends.dict_store import dict_store
import random
jug.jug.silent = True

def test_jug_execute_simple():
    N = 1024
    random.seed(232)
    A = [False for i in range(N)]
    def setAi(i):
        A[i] = True
    setall = [Task(setAi, i) for i in range(N)]
    store = dict_store()
    jug.task.Task.store = store
    simple_execute()
    assert False not in A
    assert max(store.counts.values()) < 4

def test_jug_execute_deps():
    N = 256
    random.seed(234)
    A = [False for i in range(N)]
    def setAi(i, other):
        A[i] = True
    idxs = list(range(N))
    random.shuffle(idxs)
    prev = None
    for idx in idxs:
        prev = Task(setAi, idx, prev)
    store = dict_store()
    jug.task.Task.store = store
    simple_execute()
    assert False not in A
    assert max(store.counts.values()) < 4

from task_reset import task_reset
def test_aggressive_unload():
    from jug.jug import execution_loop
    from jug.task import alltasks
    from jug.options import default_options
    from collections import defaultdict
    options = default_options.copy()
    options.aggressive_unload = True
    @task_reset
    def run_jugfile(jugfile):
        store, space = jug.jug.init(jugfile, 'dict_store')
        execution_loop(alltasks, options, defaultdict(int), defaultdict(int))
    yield run_jugfile, 'jug/tests/jugfiles/tasklet_simple.py'
    yield run_jugfile, 'jug/tests/jugfiles/tasklets.py'
