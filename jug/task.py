# -*- coding: utf-8 -*-
# Copyright (C) 2008-2012, Luis Pedro Coelho <luis@luispedro.org>
# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
# LICENSE: MIT
'''
Task: contains the Task class.

This is the main class for using jug.

There are two main alternatives:

- Use the ``Task`` class directly to build up tasks, such as ``Task(function, arg0, ...)``.
- Rely on the ``TaskGenerator`` decorator as a shortcut for this.
'''

from __future__ import division
from .hash import new_hash_object, hash_update

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
    def __init__(self, slice):
        self.slice = slice
    def __call__(self, obj):
        return obj[self.slice]

    def __repr__(self):
        return 'jug.task._getitem(%s)' % self.slice
    def __str__(self):
        return 'jug.task._getitem(%s)' % self.slice

class TaskletMixin(object):
    def __getitem__(self, slice):
        return Tasklet(self, _getitem(slice))

class Task(TaskletMixin):
    '''
    T = Task(f, dep0, dep1,..., kw_arg0=kw_val0, kw_arg1=kw_val1, ...)

    Defines a task, which is roughly equivalent to::

        f(dep0, dep1,..., kw_arg0=kw_val0, kw_arg1=kw_val1, ...)

    '''
    store = None
    # __slots__ = ('name', 'f', 'args', 'kwargs', '_hash','_lock')
    def __init__(self, f, *args, **kwargs):
        if f.func_name == '<lambda>':
            raise ValueError('''jug.Task does not work with lambda functions!

Write an email to the authors if you feel you have a strong reason to use them (they are a bit
tricky to support since the general code relies on the function name)''')

        self.name = '%s.%s' % (f.__module__, f.__name__)
        self.f = f
        self.args = args
        self.kwargs = kwargs
        alltasks.append(self)

    def run(self, force=False, save=True):
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
        self._result = self._execute()
        if save:
            name = self.hash()
            self.store.dump(self._result, name)
        return self._result

    def _execute(self):
        args = [value(dep) for dep in self.args]
        kwargs = dict((key,value(dep)) for key,dep in self.kwargs.iteritems())
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
        self.unload()
        for dep in self.dependencies():
            dep.unload_recursive()


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
                    queue.append(dep.itervalues())


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

    def __jug_hash__(self):
        M = new_hash_object()
        M.update(self.name)
        hash_update(M, enumerate(self.args))
        hash_update(M, self.kwargs.iteritems())
        value = M.hexdigest()
        self.__jug_hash__ = lambda : value
        return value


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
    def __init__(self, base, f):
        '''
        Tasklet equivalent to::

            f(value(base))
        '''
        self.base = base
        self.f = f
        self.unload = self.base.unload
        self.unload_recursive = self.base.unload_recursive

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
        M = new_hash_object()
        M.update('Tasklet')
        hash_update(M, [
                ('base', self.base),
                ('f', self.f),
            ])
        return M.hexdigest()

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
        return dict((x,value(y)) for x,y in elem.iteritems())
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

    Parameters
    ----------
    f : function
        Any function except unnamed (lambda) functions

    Returns
    -------
    value : result
        Result of calling ``f(*args,**kwargs)``
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
    ``Task(f, arg0, arg1)``
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

