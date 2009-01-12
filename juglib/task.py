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
import md5
import os
from os.path import exists
import pickle
from store import atomic_pickle_dump
import options
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
        assert f.func_name != '<lambda>', '''jug.Task does not work with lambda functions!
Write an email to the authors if you feel you have a strong reason to use them (they are a bit
tricky to support since the general code relies on the function name)'''

        self.name = '%s.%s' % (f.__module__, f.__name__)
        self.f = f
        self.dependencies = dependencies
        self.kwdependencies = kwdependencies
        self.finished = False
        self.loaded = False
        alltasks.append(self)

    def run(self):
        '''
        task.run()

        Performs the task.
        '''
        assert self.can_run()
        assert not self.finished
        args = [value(dep) for dep in self.dependencies]
        kwargs = dict((key,value(dep)) for key,dep in self.kwdependencies.iteritems())
        self._result = self.f(*args,**kwargs)
        name = self._filename()
        atomic_pickle_dump(self._result,name)
        self.finished = True

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
            if type(dep) == Task: return dep.finished
            if type(dep) == list: return all(is_available(sub) for sub in dep)
            return True # If dependency is not list nor task, it's a literal value
        return all(is_available(dep) for dep in (list(self.dependencies) + self.kwdependencies.values()))

    def load(self):
        '''
        self.load()

        Loads the results from file.
        '''
        assert self.can_load()
        self._result = pickle.load(file(self._filename()))
        self.finished = True

    def can_load(self):
        '''
        bool = task.can_load()
        '''
        return exists(self._filename())

    def _filename(self,hash_only=False):
        M = md5.md5()
        def update(*args):
            if not args: return
            names,elems = args
            for n,e in zip(names,elems):
                M.update(pickle.dumps(n))
                if type(e) == Task: 
                    M.update(e._filename())
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
        D = M.hexdigest()
        if hash_only: return D
        return os.path.join(options.jugdir,D[0],D[1],D[2:])

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
        return lock.get(self._filename(hash_only=True))

    def unlock(self):
        '''
        task.unlock()

        Releases the lock.
        If the lock was not held, this may remove another
        thread's lock!
        '''
        lock.release(self._filename(hash_only=True))

    def is_locked(self):
        return lock.is_locked(self._filename(hash_only=True))

def value(obj):
    if type(obj) == Task:
        assert obj.finished
        return obj.result
    if type(obj) == list:
        return [value(elem) for elem in obj]
    if type(obj) == tuple:
        return tuple(value(elem) for elem in obj)
    return obj

def topological_sort(tasks):
    '''
    topological_sort(tasks)

    Sorts a list of tasks topologically in-place. The list is sorted when
    there is never a dependency between tasks[i] and tasks[j] if i < j.
    '''
    sorted = []
    def walk(task,level = 0):
        if level > len(tasks):
            raise ValueError, 'tasks.topological_sort: Cycle detected.'
        for dep in list(task.dependencies) + task.kwdependencies.values():
            if type(dep) is list:
                for ddep in dep:
                    if ddep in tasks:
                        return walk(ddep, level + 1)
            else:
                if dep in tasks:
                    return walk(dep, level + 1)
        return task
    try:
        while tasks:
            t = walk(tasks[0])
            tasks.remove(t)
            sorted.append(t)
    finally:
        # This ensures that even if an exception is raised, we don't lose tasks
        tasks.extend(sorted)


def TaskGenerator(func):
    def ret_task(*args,**kwargs):
        return Task(func,*args,**kwargs)
    return ret_task
# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
