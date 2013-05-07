# This tests an important regression:
# adding the module to the module map *before* execfile()ing the jugfile makes
# this not work.

from jug import barrier, Task, value
import jug.mapreduce
import math
from functools import reduce

def double(x):
    val = math.sqrt(2.)*math.sqrt(2.)
    return x*val

two = jug.mapreduce.map(double, list(range(20)))
barrier()
def product(vals):
    import operator
    return reduce(operator.mul, vals)
values = product(value(two))
