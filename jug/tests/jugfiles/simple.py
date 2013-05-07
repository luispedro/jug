from jug import TaskGenerator

@TaskGenerator
def double(x):
    return x*2

@TaskGenerator
def sum2(a, b):
    return a + b

@TaskGenerator
def plus1(x):
    return x + 1

vals = list(range(8))
vals = list(map(double, vals))
vals = list(map(plus1, vals))
vals = [sum2(v, 2) for v in vals]
vals = [sum2(v, v) for v in vals]
