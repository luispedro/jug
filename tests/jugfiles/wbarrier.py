from jug import barrier, Task
import math

def double(x):
# this tests an important regression:
# using __import__ for the jugfile with barrier() would make this code **not** work
    val = math.sqrt(2.)*math.sqrt(2.)
    return x*val

two = Task(double,1)
barrier()
four = Task(double, two)

def make_call(f, arg):
    return f(arg)
eight = Task(make_call, double, four)
