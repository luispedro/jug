import md5
import os
from os.path import exists
import pickle
import options
from data import atomic_pickle_dump

class Task(object):
    '''
    Task
    ----

    T = Task(f, dependencies, fwkwargs)

    Defines a task, which is roughly equivalent to

    f( *[dep() for dep in dependencies], **fkwargs)

    '''
    def __init__(self,name,f,dependencies, kwdependencies):
        self.name = name
        self.f = f
        self.dependencies = dependencies
        self.kwdependencies = kwdependencies
        self.finished = False

    def run(self):
        '''
        task.run()

        Performs the task.
        '''
        assert self.can_run()
        assert not self.finished
        args = [value(dep) for dep in self.dependencies]
        kwargs = dict((key,value(dep)) for key,dep in self.kwdependencies.iteritems())
        self.result = self.f(*args,**kwargs)
        name = self._filename()
        atomic_pickle_dump(self.result,name)

    def can_run(self):
        '''
        bool = task.can_run()

        Returns true if all the dependencies are finished.
        '''
        def is_available(dep):
            return type(dep) != Task or dep.finished
        return all(is_available(dep) for dep in (self.dependencies + self.kwdependencies.values()))

    def load(self):
        '''
        self.load()

        Loads the results from file.
        '''
        assert self.can_load()
        self.result = pickle.load(file(self._filename()))
        self.finished = True

    def can_load(self):
        '''
        bool = task.can_load()
        '''
        return self.can_run() and exists(self._filename())

    def _filename(self):
        M = md5.md5()
        for dep in self.dependencies:
            if type(dep) == Task: M.update(dep._filename())
            else: M.update(pickle.dumps(dep))
        for n, dep in self.kwdependencies.iteritems():
            M.update(n)
            if type(dep) == Task: M.update(dep._filename())
            else: M.update(pickle.dumps(dep))
        M.update(pickle.dumps(self.name))
        D = M.hexdigest()
        return os.path.join(options.datadir,D[0],D[1],D[2:])

def value(obj):
    if type(obj) == Task:
        assert obj.finished
        return obj.result
    return obj

