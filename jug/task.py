# -*- coding: utf-8 -*-
# Copyright (C) 2008-2016, Luis Pedro Coelho <luis@luispedro.org>
# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
# LICENSE: MIT
'''
Task: contains the Task class.

This is the main class for using jug.

There are two main alternatives:

- Use the ``Task`` class directly to build up tasks, such as ``Task(function, arg0, ...)``.
- Rely on the ``TaskGenerator`` decorator as a shortcut for this.
'''


from .hash import new_hash_object, hash_update, hash_one

__all__ = [
    'Task',
    'Tasklet',
    'recursive_dependencies',
    'TaskGenerator',
    'iteratetask',
    'value',
    ]

alltasks = []

class _getitem(object):
    __slots__ = ('slice',)
    def __init__(self, slice):
        self.slice = slice

    def __call__(self, obj):
        obj = value(obj)
        slice = value(self.slice)
        return obj[slice]

    def __jug_hash__(self):
        return hash_one(('jug.task._getitem', self.slice))

    def __repr__(self):
        return 'jug.task._getitem(%s)' % self.slice
    def __str__(self):
        return 'jug.task._getitem(%s)' % self.slice

class TaskletMixin(object):
    __slots__ = ()
    def __getitem__(self, slice):
        return Tasklet(self, _getitem(slice))

class Task(TaskletMixin):
    '''
    T = Task(f, dep0, dep1,..., kw_arg0=kw_val0, kw_arg1=kw_val1, ...)

    Defines a task, which will call::

        f(dep0, dep1,..., kw_arg0=kw_val0, kw_arg1=kw_val1, ...)

    See Also
    --------

    TaskGenerator : function
    '''
    store = None
    # __slots__ = ('name', 'f', 'args', 'kwargs', '_hash','_lock')
    def __init__(self, f, *args, **kwargs):
        if getattr(f, 'func_name', '') == '<lambda>':
            raise ValueError('''jug.Task does not work with lambda functions!

Write an email to the authors if you feel you have a strong reason to use them (they are a bit
tricky to support since the general code relies on the function name)''')

        self.name = '%s.%s' % (f.__module__, f.__name__)
        self.f = f
        self.args = args
        self.kwargs = kwargs
        alltasks.append(self)

    def run(self, force=False, save=True, debug_mode=False):
        '''
        task.run(force=False, save=True)

        Performs the task.

        Parameters
        ----------
        force : boolean, optional
            if true, always run the task (even if it ran before)
            (default: False)
        save : boolean, optional
            if true, save the result to the store
            (default: True)
        '''
        assert self.can_run()
        if debug_mode: self._check_hash()
        self._result = self._execute()
        if save:
            name = self.hash()
            self.store.dump(self._result, name)
        if debug_mode: self._check_hash()
        return self._result

    def _execute(self):
        args = [value(dep) for dep in self.args]
        kwargs = dict((key,value(dep)) for key,dep in self.kwargs.items())
        return self.f(*args,**kwargs)


    def _get_result(self):
        if not hasattr(self, '_result'): self.load()
        return self._result

    result = property(_get_result, doc='Result value')
    def value(self):
        return self.result


    def can_run(self):
        '''
        bool = task.can_run()

        Returns true if all the dependencies have their results available.
        '''
        for dep in self.dependencies():
            if not hasattr(dep, '_result') and not dep.can_load():
                return False
        return True

    def is_loaded(self):
        '''
        loaded = task.is_loaded()

        Returns True if the task is already loaded
        '''
        return hasattr(self, '_result')

    def load(self):
        '''
        t.load()

        Loads the results from the storage backend.

        This function *always* loads from the backend even if the task is
        already loaded. You can use `is_loaded` as a check if you want to avoid
        this behaviour.

        Returns
        -------
        Nothing
        '''
        assert self.can_load()
        self._result = self.store.load(self.hash())

    def invalidate(self):
        '''
        t.invalidate()

        Equivalent to ``t.store.remove(t.hash())``. Useful for interactive use
        (i.e., in ``jug shell`` mode).
        '''
        self.store.remove(self.hash())

    def unload(self):
        '''
        t.unload()

        Unload results (can be useful for saving memory).
        '''
        if hasattr(self, '_result'):
            del self._result

    def unload_recursive(self):
        '''
        t.unload_recursive()

        Equivalent to::

            for tt in recursive_dependencies(t): tt.unload()
        '''
        def checked_unload_recursive(t, visited):
            if id(t) not in visited:
                visited.add(id(t))
                t.unload()
                for dep in t.dependencies():
                    checked_unload_recursive(dep, visited)

        checked_unload_recursive(self, set())

    def dependencies(self):
        '''
        for dep in task.dependencies():
            ...

        Iterates over all the first-level dependencies of task `t`

        Parameters
        ----------
        self : Task

        Returns
        -------
        deps : generator
            A generator over all of `self`'s dependencies

        See Also
        --------
        recursive_dependencies : retrieve dependencies recursively
        '''
        queue = [self.args, self.kwargs.values()]
        while queue:
            deps = queue.pop()
            for dep in deps:
                if isinstance(dep, (Task, Tasklet)):
                    yield dep
                elif isinstance(dep, (list, tuple)):
                    queue.append(dep)
                elif isinstance(dep, dict):
                    queue.append(iter(dep.values()))


    def can_load(self, store=None):
        '''
        bool = task.can_load()

        Returns whether result is available.
        '''
        if store is None:
            store = self.store
        return store.can_load(self.hash())

    def hash(self):
        '''
        fname = t.hash()

        Returns the hash for this task.

        The results are cached, so the first call can be much slower than
        subsequent calls.
        '''
        return self.__jug_hash__()

    def _compute_set_hash(self):
        M = new_hash_object()
        hash_update(M,
                    [('name', self.name.encode('utf-8'))
                    ,('args', self.args)
                    ,('kwargs', self.kwargs)
                    ])
        value = M.hexdigest().encode('utf-8')
        self.__jug_hash__ = lambda : value
        return value


    def _check_hash(self):
        if self.hash() != self._compute_set_hash():
            hash_error_msg = ('jug error: Hash value of task (name: %s) changed unexpectedly.\n' % self.name)
            hash_error_msg += 'Typical cause is that a Task function changed the value of an argument (which messes up downstream computations).'
            raise RuntimeError(hash_error_msg)
    def __jug_hash__(self):
        return self._compute_set_hash()


    def __str__(self):
        '''String representation'''
        return 'Task: %s()' % self.name

    def __repr__(self):
        '''Detailed representation'''
        return 'Task(%s, args=%s, kwargs=%s)' % (self.name, self.args, self.kwargs)

    def lock(self):
        '''
        locked = task.lock()

        Tries to lock the task for the current process.

        Returns True if the lock was acquired. The correct usage pattern is::

            locked = task.lock()
            if locked:
                task.run()
            else:
                # someone else is already running this task!

        Not that using can_lock() can lead to race conditions. The above
        is the only fully correct method.

        Returns
        -------
        locked : boolean
            Whether the lock was obtained.
        '''
        if not hasattr(self, '_lock'):
            self._lock = self.store.getlock(self.hash())
        return self._lock.get()

    def unlock(self):
        '''
        task.unlock()

        Releases the lock.

        If the lock was not held, this may remove another thread's lock!
        '''
        self._lock.release()

    def is_locked(self):
        '''
        is_locked = t.is_locked()

        Note that only calling lock() and checking the result atomically checks
        for the lock(). This function can be much faster, though, and, therefore
        is sometimes useful.

        Returns
        -------
        is_locked : boolean
            Whether the task **appears** to be locked.

        See Also
        --------
        lock : create lock
        unlock : destroy lock
        '''
        if not hasattr(self, '_lock'):
            self._lock = self.store.getlock(self.hash())
        return self._lock.is_locked()

class Tasklet(TaskletMixin):
    '''
    Tasklet

    A Tasklet is a light-weight Task.

    It looks like a Task, behaves like a Task, but its results are not saved in
    the backend.

    It is useful for very simple functions and is automatically generated on
    subscripting a Task object::

        t = Task(f, 1)
        tlet = t[0]

    ``tlet`` will be a ``Tasklet``

    See Also
    --------
    Task
    '''

    __slots__ = ('base', 'f')
    def __init__(self, base, f):
        '''
        Tasklet equivalent to::

            f(value(base))
        '''
        self.base = base
        self.f = f

    def unload(self):
        self.base.unload()

    def unload_recursive(self):
        self.base.unload_recursive()

    def dependencies(self):
        yield self.base

    def value(self):
        return self.f(value(self.base))

    def can_load(self):
        return self.base.can_load()

    def _base_hash(self):
        if isinstance(self.base, Tasklet):
            return self.base._base_hash()
        return self.base.hash()

    def __jug_hash__(self):
        import six
        M = new_hash_object()
        M.update(six.b('Tasklet'))
        hash_update(M, [
                ('base', self.base),
                ('f', self.f),
            ])
        return M.hexdigest().encode('utf-8')

def topological_sort(tasks):
    '''
    topological_sort(tasks)

    Sorts a list of tasks topologically in-place. The list is sorted when
    there is never a dependency between tasks[i] and tasks[j] if i < j.
    '''
    sorted = []
    whites = set(tasks)
    def dfs(t):
        for dep in t.dependencies():
            if dep in whites:
                whites.remove(dep)
                dfs(dep)
        sorted.append(t)
    while whites:
        next = whites.pop()
        dfs(next)
    tasks[:] = sorted

def recursive_dependencies(t, max_level=-1):
    '''
    for dep in recursive_dependencies(t, max_level=-1):
        ...

    Returns a generator that lists all recursive dependencies of task

    Parameters
    ----------
    t : Task
        input task
    max_level : integer, optional
      Maximum recursion depth. Set to -1 or None for no recursion limit.

    Returns
    -------
    deps : generator
        A generator over all dependencies
    '''
    if max_level is None:
        max_level = -1
    if max_level == 0:
        return

    for dep in t.dependencies():
        yield dep
        for d2 in recursive_dependencies(dep, max_level - 1):
            yield d2

def value(elem):
    '''
    value = value(obj)

    Loads a task object recursively. This correcly handles lists,
    dictonaries and eny other type handled by the tasks themselves.

    Parameters
    ----------
    obj : object
        Anything that can be pickled or a Task

    Returns
    -------
    value : object
        The result of the task ``obj``
    '''
    if isinstance(elem, (Task, Tasklet)):
        return elem.value()
    elif type(elem) == list:
        return [value(e) for e in elem]
    elif type(elem) == tuple:
        return tuple([value(e) for e in elem])
    elif type(elem) == dict:
        return dict((x,value(y)) for x,y in elem.items())
    elif hasattr(elem, '__jug_value__'):
        return elem.__jug_value__()
    else:
        return elem

def CachedFunction(f,*args,**kwargs):
    '''
    value = CachedFunction(f, *args, **kwargs)

    is equivalent to::

        task = Task(f, *args, **kwargs)
        if not task.can_load():
            task.run()
        value = task.value()

    That is, it calls the function if the value is available,
    but caches the result for the future.

    You can often use ``bvalue`` to achieve similar results::

        task = Task(f, *args, **kwargs)
        value = bvalues(task)

    This alternative method is more flexible, but will only be execute lazily.
    In particular, a ``jug status`` will not see past the ``bvalue`` call until
    ``jug execute`` is called to execute ``f``, while a ``CachedFunction``
    object will always execute.

    Parameters
    ----------
    f : function
        Any function except unnamed (lambda) functions

    Returns
    -------
    value : result
        Result of calling ``f(*args,**kwargs)``

    See Also
    --------
    bvalue : function
        An alternative way to achieve similar results to ``CachedFunction(f)``
        is using ``bvalue``.


    '''
    t = Task(f,*args, **kwargs)
    if not t.can_load():
        if not t.can_run():
            raise ValueError('jug.CachedFunction: unable to run task %s' % t)
        t.run()
    return value(t)

class TaskGenerator(object):
    '''
    @TaskGenerator
    def f(arg0, arg1, ...)
        ...

    Turns f from a function into a task generator.

    This means that calling ``f(arg0, arg1)`` results in:
    ``Task(f, arg0, arg1)``. This can make your jug-based code feel very
    similar to what you do with traditional Python.


    Example
    -------

    Add the following to ``jugfile.py``::

        from jug import TaskGenerator

        @TaskGenerator
        def get1():
            return 1

        @TaskGenerator
        def add(a, b):
            return a + b


        x = get1()
        y = add(x, 2)
        y = add(y, y)

    Now, you have 3 tasks:

    1. call ``get1``
    2. call ``add`` with the result of that and the value 2
    2. call ``add`` again with the result of the previous call

    '''
    _jug_is_task_generator = True
    def __init__(self, f):
        self.f = f

    def __getstate__(self):
        from sys import modules
        modname = getattr(self.f, '__module__', None)
        fname = self.f.__name__
        obj = getattr(modules[modname], fname, None)
        if modname is None or (obj is not self and obj is not self.f):
            raise RuntimeError('jug.TaskGenerator could not pickle function.\nA function must be defined at the top-module level')
        return modname,fname

    def __setstate__(self, state):
        from sys import modules
        modname,fname = state
        self.f = getattr(modules[modname], fname)

    def __call__(self, *args, **kwargs):
        return Task(self.f, *args, **kwargs)


# This is lower case to be used like a function
class iteratetask(object):
    '''
    Examples::

        a,b = iteratetask(task, 2)
        for a in iteratetask(task, n):
            ...

    This creates an iterator that over the sequence ``task[0], task[1], ...,
    task[n-1]``.

    Parameters
    ----------
    task : Task(let)
    n : integer

    Returns
    -------
    iterator

    Bugs
    ----
    You need to specify how many elements to use.

    There is no error checking that you have not missed elements at the end!
    '''
    def __init__(self, base, n):
        self.base = base
        self.n = n

    def __getitem__(self, i):
        if i >= self.n: raise IndexError
        return self.base[i]

    def __len__(self):
        return self.n

def _get_check(r, i, n):
    if len(r) != n:
        raise ValueError("Expected a tuple of size {} got {}".format(n, len(r)))
    return r[i]

def return_tuple(n):
    '''
    Wraps a TaskGenerator which returns a tuple of size `n`. Now, the
    TaskGenerator will also return a tuple, allowing for more natural code.

    Examples
    --------

    ::

        @return_tuple(2)
        @TaskGenerator
        def plus1(x):
            return x, 1+x

        x,x1 = plus1(0)





    Parameters
    ----------
    n : int
        Expected size of tuple (this is checked at runtime)
    '''
    from functools import partial
    def wrapper(f):
        def wrapped(*args, **kwargs):
            r = f(*args, **kwargs)
            return tuple([Tasklet(r, partial(_get_check, i=i, n=n)) for i in range(n)])
        return wrapped
    return wrapper

def describe(t):
    '''
    description = describe(t)

    Return a recursive description of the computation.

    Parameters
    ----------
    t : object

    Returns
    -------
    description : obj
    '''
    if isinstance(t, Task):
        description = { 'name': t.name, }
        if len(t.args):
            description['args'] = [describe(a) for a in t.args]
        if len(t.kwargs):
            description['kwargs'] = dict([(k,describe(v)) for k,v in t.kwargs.iteritems()])
        meta = t.store.metadata(t)
        if meta is not None:
            description['meta'] = meta
        return description
    elif isinstance(t, Tasklet):
        return {
                'name': 'tasklet',
                'operation': repr(t.f),
                'base': describe(t.base)
        }
    elif isinstance(t, list):
        return [describe(ti) for ti in t]
    elif isinstance(t, dict):
        return dict([(k,describe(v)) for k,v in t.items()])
    elif isinstance(t, tuple):
        return tuple(list(t))
    return t

