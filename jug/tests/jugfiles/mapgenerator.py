from jug import mapreduce, TaskGenerator

@TaskGenerator
def double(x):
    return 2*x

vs = list(range(16))
v2s = mapreduce.map(double, vs)
