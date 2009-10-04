# -*- coding: utf-8 -*-
# Copyright (C) 2008, Luís Pedro Coelho <lpc@cmu.edu>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.
'''
Task: contains the Task class.

This is the main unit of jug.
'''

from __future__ import division
import hashlib
import os
import store
import options
import cPickle as pickle
import lock

alltasks = []

class Task(object):
    '''
    Task
    ----

    T = Task(f, dependencies, fwkwargs)

    Defines a task, which is roughly equivalent to

    f( *[dep() for dep in dependencies], **fkwargs)

    '''
    def __init__(self,f,*dependencies, **kwdependencies):
        if f.func_name == '<lambda>':
            raise ValueError('''jug.Task does not work with lambda functions!

Write an email to the authors if you feel you have a strong reason to use them (they are a bit
tricky to support since the general code relies on the function name)''')

        kwargs = dict( (k,v) for k,v in kwdependencies.iteritems() if k.startswith('task_') )
        for k in kwargs:
            del kwdependencies[k]

        self.name = '%s.%s' % (f.__module__, f.__name__)
        self.f = f
        self.dependencies = dependencies
        self.kwdependencies = kwdependencies
        self.finished = False
        self.loaded = False
        self._can_load = False
        self.print_result = kwargs.get('task_print_result',False)
        alltasks.append(self)
        self.hash = None

    def run(self, force=False):
        '''
        task.run(force=False)

        Performs the task.

        Parameters
        ----------
          * force: if True, always run the task (even if it ran before)
        '''
        assert self.can_run()
        assert force or not self.finished
        args = [value(dep) for dep in self.dependencies]
        kwargs = dict((key,value(dep)) for key,dep in self.kwdependencies.iteritems())
        self._result = self.f(*args,**kwargs)
        name = self.filename()
        store.dump(self._result,name)
        self.finished = True
        if self.print_result:
            print self._result
        return self._result

    def _get_result(self):
        if not self.finished: self.load()
        return self._result

    result = property(_get_result,doc='Result value')


    def can_run(self):
        '''
        bool = task.can_run()

        Returns true if all the dependencies are finished.
        '''
        def is_available(dep):
            if type(dep) == Task: return dep.finished or dep.can_load()
            if type(dep) == list: return all(is_available(sub) for sub in dep)
            return True # If dependency is not list nor task, it's a literal value
        return all(is_available(dep) for dep in (list(self.dependencies) + self.kwdependencies.values()))

    def load(self):
        '''
        t.load()

        Loads the results from file.
        '''
        assert self.can_load()
        self._result = store.load(self.filename())
        self.finished = True

    def unload(self):
        '''
        t.unload()

        Unload results (can be useful for saving memory)
        '''
        self._result = None
        self.finished = False

    def unload_recursive(self):
        '''
        t.unload_recursive()

        '''
        def _dependency_walk(task):
            for dep in list(task.dependencies) + task.kwdependencies.values():
                if type(dep) == Task:
                    for d in _dependency_walk(dep):
                        yield d
                yield dep
        for dep in _dependency_walk(self):
            if type(dep) == Task:
                dep.unload()
        self.unload()

    def can_load(self):
        '''
        bool = task.can_load()
        '''
        if self.finished: return True
        if not self._can_load:
            self._can_load = store.can_load(self.filename())
        return self._can_load

    def filename(self,hash_only=False):
        '''
        fname = t.filename()

        Returns the filename that holds the result of this task.
        '''
        if self.hash is None:
            M = hashlib.md5()
            def update(*args):
                if not args: return
                names,elems = args
                for n,e in zip(names,elems):
                    M.update(pickle.dumps(n))
                    if type(e) == Task:
                        M.update(e.filename(hash_only=True))
                    elif type(e) == list:
                        update(*zip(*enumerate(e)))
                    elif type(e) == dict:
                        update(e.keys(),e.values())
                    else:
                        M.update(pickle.dumps(e))
            M.update(self.name)
            update(*zip(*enumerate(self.dependencies)))
            update(*zip(*self.kwdependencies.items()))
            M.update(pickle.dumps(self.name))
            self.hash = M.hexdigest()
        if hash_only: return self.hash
        return os.path.join(options.jugdir,self.hash[0],self.hash[1],self.hash[2:])

    def __str__(self):
        '''String representation'''
        return 'Task: %s()' % self.name

    def __repr__(self):
        '''Detailed representation'''
        return 'Task(%s,dependencies=%s,kwdependencies=%s)' % (self.name,self.dependencies,self.kwdependencies)

    def lock(self):
        '''
        locked = task.lock()

        Tries to lock the task for the current process.
        Returns true if the lock was obtained.
        '''
        return lock.get(self.filename(hash_only=True))

    def unlock(self):
        '''
        task.unlock()

        Releases the lock.
        If the lock was not held, this may remove another
        thread's lock!
        '''
        lock.release(self.filename(hash_only=True))

    def is_locked(self):
        return lock.is_locked(self.filename(hash_only=True))


def topological_sort(tasks):
    '''
    topological_sort(tasks)

    Sorts a list of tasks topologically in-place. The list is sorted when
    there is never a dependency between tasks[i] and tasks[j] if i < j.
    '''
    sorted = []
    whites = set(tasks)
    def dfs(t):
        for dep in recursive_dependencies(t, 1):
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
    for dep in recursive_dependencies(t, max_level=None):
        ...

    Returns a generator that lists all recursive dependencies of task

    Parameters
    ----------
        * t: task
        * max_level: Maximum recursion depth. Set to -1 or None for no recursion limit.
    '''
    if max_level is None:
        max_level = -1
    if type(t) is list:
        for d in t:
            for dd in recursive_dependencies(d, max_level):
                yield dd
        return
    if type(t) is dict:
        for d in t.itervalues():
            for dd in recursive_dependencies(d, max_level):
                yield dd
        return
    if type(t) is Task:
        yield t
        if max_level == 0:
            return
        for dep in t.dependencies:
            for d in recursive_dependencies(dep, max_level-1):
                yield d
        for dep in t.kwdependencies.itervalues():
            for d in recursive_dependencies(dep, max_level-1):
                yield d


def value(elem):
    '''
    value = value(task)

    Loads a task object recursively.
    '''
    if type(elem) is Task:
        return elem.result
    elif type(elem) is list:
        return [value(e) for e in elem]
    elif type(elem) is tuple:
        return tuple([value(e) for e in elem])
    elif type(elem) is dict:
        return dict((x,value(y)) for x,y in elem.iteritems())
    else:
        return elem

def CachedFunction(f,*args,**kwargs):
    '''
    value = CachedFunction(f, *args, **kwargs)

    is the same as

    value = Task(f, *args, **kwargs).result

    That is, it calls the function if the value is available,
    but caches the result for the future.
    '''
    t = Task(f,*args, **kwargs)
    if not t.can_load():
        if not t.can_run():
            raise ValueError('jug.CachedFunction: unable to run task %s' % t)
        t.run()
    return t.result

def TaskGenerator(*args,**kwargs):
    '''
    TaskGenerator

    Use as either

    @TaskGenerator
    def f():
        pass

    or

    @TaskGenerator(arg=1)
    def f():
        pass

    TaskGenerator does not take any non-keyword arguments
    '''
    assert not (args and kwargs), '''TaskGenerator called in a weird way.'''
    if kwargs:
        task_args = [('task_' + k,v) for k,v in kwargs.iteritems()]
        def task_generator(f):
            def gen_task(*args,**kwargs):
                kwargs.update(task_args)
                return Task(f,*args,**kwargs)
            return gen_task
        return task_generator
    assert len(args) == 1, '''TaskGenerator called in a weird way.'''
    func = args[0]
    def gen_task(*args,**kwargs):
        return Task(func,*args,**kwargs)
    return gen_task

# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
