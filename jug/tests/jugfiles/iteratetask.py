from jug import Task
from jug.task import iteratetask

def double(xs):
    return [x*2 for x in xs]

vals = [0,1,2]
t = Task(double, vals)
t0,t1,t2 = iteratetask(t, 3)

f2 = Task(double, [t0, t1])

f3 = Task(double, [2,3,4])

