import jug.mapreduce
import math

def double(x):
    val = math.sqrt(2.)*math.sqrt(2.)
    return x*val

two = jug.mapreduce.map(double, [])
