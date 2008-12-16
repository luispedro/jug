class Task(object):
    '''
    Task
    ----

    T = Task(f, dependencies, fwkwargs)

    Defines a task, which is roughly equivalent to

    f( [dep() for dep in dependencies], **fkwargs)

    '''
    def __init__(self,name,f,dependencies,fkwargs={}):
        self.name = name
        self.f = f
        self.dependencies = dependencies
        self.fkwargs = fkwargs
        self.finished = False

    def run(self):
        '''
        task.run()

        Performs the task.
        '''
        assert self.can_run()
        assert not self.finished
        args = [value(dep) for dep in self.dependencies]
        self.result = self.f(self.args,**self.fkwargs)
        name = self._filename()
        atomic_pickle_dump(name,self.result)

    def can_run(self):
        '''
        bool = task.can_run()

        Returns true if all the dependencies are finished.
        '''
        return all(dep.finished for dep in self.dependencies)

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
            M.update(dep._filename())
        M.update(self.f)
        M.update(self.fkwargs)
        D = M.hexdigest()
        return os.path.join(options.datadir,D[0],D[1],D[2:])

def value(obj):
    if type(obj) == Task:
        assert obj.finished
        return obj.result
    return obj

