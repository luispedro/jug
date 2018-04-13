from jug import mapreduce, TaskGenerator

@TaskGenerator
def double(x):
    return 2*x

@TaskGenerator
def sum_all(xs):
    return sum(xs)

vs = list(range(16))
v2s = mapreduce.map(double, vs)

s = sum_all(v2s)
v4s = mapreduce.map(double, v2s)
