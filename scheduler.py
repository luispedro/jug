from task import Task
tasks = []

def _possible_args2(args,kwargs):
    from jugfileparser import ParamSearch
    for i,a in enumerate(args):
        if type(a) == ParamSearch:
            for v in a.values:
                args[i] = v
                for r in _possible_args2(args,kwargs):
                    yield r
                return

    for k, v in kwargs.items():
        if type(v) == ParamSearch:
            del kwargs[k]
            for p in v.values:
                kwargs[v.name] = p
                for r in _possible_args2(args,kwargs):
                    yield r
            return
    yield list(args), kwargs

def _possible_args(a,b):
    print a,b, '->',
    res = list(_possible_args2(a,b))
    print res
    return res

def convert_to_tasks(computation):
    return [Task(computation.name, computation.f, arg, kwargs) for arg,kwargs in _possible_args(computation.args,computation.kwargs)]

