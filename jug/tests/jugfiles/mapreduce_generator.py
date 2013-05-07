from jug import TaskGenerator
import jug.mapreduce
import math

@TaskGenerator
def double(x):
    return x*2

@TaskGenerator
def sum2(a,b):
    return (a+b)

sumtwo = jug.mapreduce.mapreduce(sum2, double, list(range(10)))
