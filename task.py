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
        self.name = '%s.%s' % (f.__module__, f.__name__)
        self.f = f
        self.dependencies = dependencies
        self.kwdependencies = kwdependencies
        self.finished = False
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
        self.result = self.f(*args,**kwargs)
        name = self._filename()
        atomic_pickle_dump(self.result,name)
        self.finished = True

    def can_run(self):
        '''
        bool = task.can_run()

        Returns true if all the dependencies are finished.
        '''
        def is_available(dep):
            if type(dep) == Task: return dep.finished
            if type(dep) == list: return all(is_available(sub) for sub in dep)
            return True # Value
        return all(is_available(dep) for dep in (list(self.dependencies) + self.kwdependencies.values()))

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
        update(*zip(*enumerate(self.dependencies)))
        update(*zip(*self.kwdependencies.items()))
        M.update(pickle.dumps(self.name))
        D = M.hexdigest()
        if hash_only: return D
        return os.path.join(options.jugdir,D[0],D[1],D[2:])

    def lock(self):
        return lock.get(self._filename(hash_only=True))

    def unlock(self):
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

def TaskGenerator(func):
    def ret_task(*args,**kwargs):
        return Task(func,*args,**kwargs)
    return ret_task
