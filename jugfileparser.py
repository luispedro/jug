from scheduler import tasks, convert_to_tasks

class ParamSearch(object):
    def __init__(self,values):
        self.values = values

class Data(object):
    def __init__(self,fname):
        self.fname = fname

class Compute(object):
    def __init__(self, name, f, *args, **kwargs):
        self.name = name
        self.f = f
        self.args = args
        self.kwargs = kwargs
        tasks.extend(convert_to_tasks(self))

def parse(fname):
    execfile(fname)

