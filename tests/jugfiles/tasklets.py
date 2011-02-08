from jug import Task, Tasklet

def double(xs):
    return [x*2 for x in xs]

def sum2(a, b):
    return a + b

def plus1(x):
    return x + 1

vals = [0,1,2,3,4,5,6,7]
t = Task(double, vals)
t0 = t[0]
t2 = t[2]
t0_2 = Task(sum2, t0, t2)
t0_2_1 = Tasklet(t0_2, plus1)

