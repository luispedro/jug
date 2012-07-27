from jug import TaskGenerator
import jug.mapreduce
import math

@TaskGenerator
def double(x):
    val = math.sqrt(2.)*math.sqrt(2.)
    return x*val

two = jug.mapreduce.map(double, range(10))
