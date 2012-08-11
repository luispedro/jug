from jug import barrier, Task, bvalue
import math

def double(x):
    return 2*x

two = Task(double,1)
two = bvalue(two)
four = 2*two
