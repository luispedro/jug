from task import Task
tasks = []

def _possible_args(args,kwargs):
    from jugfileparser import ParamSearch
    for i,a in enumerate(args):
        if type(a) == ParamSearch:
            for v in a.values:
                args[i] = v
                for a,b in _possible_args(args,kwargs):
                    yield list(a),b.copy()
                return

    for k, v in kwargs.items():
        if type(v) == ParamSearch:
            for p in v.values:
                kwargs[k] = p
                for a,b in _possible_args(args,kwargs):
                    yield list(a),b.copy()
            return
    yield list(args), kwargs

def convert_to_tasks(computation):
    '''
    tasks = convert_to_tasks(computation)

    computation must be a compute object.

    Returns a list of tasks that must be completed in order to
    execute this computation.
    '''
    from jugfileparser import Compute
    args = computation.args
    kwargs = computation.kwargs
    for i,arg in enumerate(args):
        if type(arg) == Compute:
            args[i] = args.tasks[0]
        elif type(arg) == list:
            if type(arg[0]) == Compute:
                args[i] = [it.tasks[0] for it in arg]
    for k,v in kwargs.items():
        if type(v) == Compute:
            kwargs[k] = v.tasks[0]
        elif type(v) == list:
            if type(v[0]) == Compute:
                kwargs[k] = [it.tasks[0] for it in v]
    tasks = [Task(computation.name, computation.f, arg, kwargs) for arg,kwargs in _possible_args(args,kwargs)]
    computation.tasks = tasks
    return tasks

