from jug import Task, TaskGenerator
from jug import mapreduce



def double(x):
    return 2*x

def double2(x):
    return 2*x

@TaskGenerator
def do_sum(partials):
    return sum(partials)

data = list(range(16))

partial = [Task(double, x) for x in data]
repartial = mapreduce.map(double2, partial, map_step=2)

final = do_sum(repartial)

