import jug
from jug.io import NoLoad
import random

@jug.TaskGenerator
def gauss():
    return random.gauss(0, 1)

@jug.TaskGenerator
def sum_partials(ts):
    total = 0.0

    for t in ts:
        total+= jug.value(t.t)
    return total

@jug.TaskGenerator
def double(x):
    return 2*x

map_ts = [gauss() for i in range(10)]
x = sum_partials([NoLoad(t) for t in map_ts])
final = double(x)
