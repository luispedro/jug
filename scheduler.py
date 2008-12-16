from task import Task
tasks = []

def _possible_args(input):
    for k, v in input.items():
        if type(k) == ParamSearch:
            for p in v:
                input[k] = p
                for r in _possible_args(input):
                    yield r
            return
    yield input

def convert_to_tasks(computation):
    return [Task(computation.name, computation.f, arg) for arg in _possible_args(computation.kwargs)]

