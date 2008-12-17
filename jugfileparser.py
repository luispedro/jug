from scheduler import tasks, convert_to_tasks

class ParamSearch(object):
    def __init__(self,*args,**kwargs):
        assert len(kwargs) == 1 and not len(args) or not len(kwargs)
        if len(kwargs):
            k,v = kwargs.items()
            self.name = k[0]
            self.values = v[0]
        if len(args):
            self.values = args


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

