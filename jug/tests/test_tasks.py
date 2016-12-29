import inspect
import os

import jug.task
from jug.tests.task_reset import task_reset
from jug.tests.utils import simple_execute


_jugdir = os.path.abspath(inspect.getfile(inspect.currentframe()))
_jugdir = os.path.join(os.path.dirname(_jugdir), 'jugfiles')


Task = jug.task.Task

def add1(x):
    return x + 1
def add2(x):
    return x + 2

def _assert_tsorted(tasks):
    from itertools import chain
    for i,ti in enumerate(tasks):
        for j,tj in enumerate(tasks[i+1:]):
            for dep in chain(ti.args, ti.kwargs.values()):
                if type(dep) is list:
                    assert tj not in dep
                else:
                    assert tj is not dep

@task_reset
def test_topological_sort():
    bases = [jug.task.Task(add1,i) for i in range(10)]
    derived = [jug.task.Task(add1,t) for t in bases]
    derived2 = [jug.task.Task(add1,t) for t in derived]
    derived3 = [jug.task.Task(add1,t) for t in derived]
    
    alltasks = bases + derived
    jug.task.topological_sort(alltasks)
    assert len(alltasks) == len(bases) + len(derived)
    _assert_tsorted(alltasks)
    
    alltasks.reverse()
    jug.task.topological_sort(alltasks)
    assert len(alltasks) == len(bases) + len(derived)
    _assert_tsorted(alltasks)

    alltasks = bases + derived
    alltasks.reverse()
    jug.task.topological_sort(alltasks)
    assert len(alltasks) == len(bases) + len(derived)
    _assert_tsorted(alltasks)

    alltasks = derived + bases
    jug.task.topological_sort(alltasks)
    assert len(alltasks) == len(bases) + len(derived)
    _assert_tsorted(alltasks)

    alltasks = derived + bases + derived2
    jug.task.topological_sort(alltasks)
    assert len(alltasks) == len(bases) + len(derived) + len(derived2)
    _assert_tsorted(alltasks)

    alltasks = derived + bases + derived2 + derived3
    jug.task.topological_sort(alltasks)
    assert len(alltasks) == len(bases) + len(derived) + len(derived2) + len(derived3)
    _assert_tsorted(alltasks)

@task_reset
def test_topological_sort_kwargs():
    def add2(x):
        return x + 2
    def sumlst(lst,param):
        return sum(lst)

    bases = [jug.task.Task(add2,x=i) for i in range(10)]
    derived = [jug.task.Task(sumlst,lst=bases,param=p) for p in range(4)]

    alltasks = bases + derived
    jug.task.topological_sort(alltasks)
    assert len(alltasks) == len(bases) + len(derived)
    _assert_tsorted(alltasks)
    
    alltasks.reverse()
    jug.task.topological_sort(alltasks)
    assert len(alltasks) == len(bases) + len(derived)
    _assert_tsorted(alltasks)

    alltasks = bases + derived
    alltasks.reverse()
    jug.task.topological_sort(alltasks)
    assert len(alltasks) == len(bases) + len(derived)
    _assert_tsorted(alltasks)

    alltasks = derived + bases
    jug.task.topological_sort(alltasks)
    assert len(alltasks) == len(bases) + len(derived)
    _assert_tsorted(alltasks)

def data():
    return list(range(20))
def mult(r,f):
    return [f*rr for rr in r]
def reduce(r):
    return sum(r)

@task_reset
def test_topological_sort_canrun():
    Task = jug.task.Task
    input = Task(data)
    for f in range(80):
        Task(reduce, Task(mult,input,f))

    alltasks = jug.task.alltasks
    jug.task.topological_sort(alltasks)
    assert len(alltasks) == len(set(t.hash() for t in alltasks))
    for t in alltasks:
        assert t.can_run()
        t.run()

@task_reset
def test_load_after_run():
    T = jug.task.Task(add1,1)
    T.run()
    assert T.can_load()

@task_reset
def test_hash_same_func():
    T0 = jug.task.Task(add1,0)
    T1 = jug.task.Task(add1,1)

    assert T0.hash() != T1.hash()
    
@task_reset
def test_hash_different_func():
    T0 = jug.task.Task(add1,0)
    T1 = jug.task.Task(add2,0)

    assert T0.hash() != T1.hash()


@task_reset
def test_taskgenerator():
    @jug.task.TaskGenerator
    def double(x):
        return 2*x
    T=double(2)
    assert type(T) == jug.task.Task


@task_reset
def test_unload():
    T0 = jug.task.Task(add1,0)
    assert not hasattr(T0, '_result')
    assert T0.can_run()
    T0.run()
    assert hasattr(T0, '_result')
    assert T0.result == 1
    T0.unload()
    assert T0.result == 1

@task_reset
def test_unload_recursive():
    T0 = jug.task.Task(add1,0)
    T1 = jug.task.Task(add1,T0)
    T2 = jug.task.Task(add1,T1)
    assert not hasattr(T0, '_result')
    T0.run()
    T1.run()
    T2.run()
    assert hasattr(T0, '_result')

    T2.unload_recursive()
    assert not hasattr(T0, '_result')

def identity(x):
    return x

@task_reset
def test_cachedfunction():
    assert jug.task.CachedFunction(identity,123) == 123
    assert jug.task.CachedFunction(identity,'mixture') == 'mixture'

@task_reset
def test_npyload():
    import numpy as np
    A = np.arange(23)
    assert np.all(jug.task.CachedFunction(identity,A) == A)

@jug.task.TaskGenerator
def double(x):
    return 2 * x

@task_reset
def test_value():
    two = double(1)
    four = double(two)
    eight = double(four)
    two.run()
    four.run()
    eight.run()
    assert jug.task.value(eight) == 8

@task_reset
def test_dict_sort_run():
    tasks = [double(1), double(2), Task(identity,2) ]
    tasks += [Task(identity,{ 'one' : tasks[2], 'two' : tasks[0], 'three' : { 1 : tasks[1], 0 : tasks[0] }})]
    jug.task.topological_sort(tasks)
    for t in tasks:
        assert t.can_run()
        t.run()
    assert tasks[-1].result == { 'one' : 2, 'two' : 2, 'three' : {1 : 4, 0: 2}}

@task_reset
def test_unload_recursive_result_property():
    two = double(1)
    four = double(two)
    two.run()
    four.run()
    four.unload_recursive ()
    assert not hasattr(four, '_result')
    assert not hasattr(two, '_result')

# Crashed in version 0.7.3
@task_reset
def test_unload_wnoresult():
    t = Task(add2, 3)
    t.unload()

@task_reset
def test_starts_unloaded():
    t = Task(add2, 3)
    assert not t.is_loaded()

@task_reset
def test__str__repr__():
    t = Task(add2, 3)
    assert str(t).find('add2') >= 0
    assert repr(t).find('add2') >= 0
    assert repr(t).find('3') >= 0


def add_tuple(a_b):
    a,b = a_b
    return a + b

@task_reset
def test_unload_recursive_tuple():
    T0 = jug.task.Task(add1,0)
    T1 = jug.task.Task(add1,T0)
    T2 = jug.task.Task(add_tuple,(T0,T1))
    T3 = jug.task.Task(add1, T2)
    assert not hasattr(T0, '_result')
    T0.run()
    T1.run()
    T2.run()
    T3.run()
    assert hasattr(T0, '_result')

    T3.unload_recursive()
    assert not hasattr(T0, '_result')

@task_reset
def test_builtin_function():
    import numpy as np
    jugfile = os.path.join(_jugdir, 'builtin_function.py')
    store, space = jug.jug.init(jugfile, 'dict_store')
    simple_execute()
    a8 = jug.task.value(space['a8'])
    assert np.all(a8 == np.arange(8))
