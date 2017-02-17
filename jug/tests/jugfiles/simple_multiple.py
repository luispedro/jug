from jug import TaskGenerator

@TaskGenerator
def sum_2(a):
    return a + 2

@TaskGenerator
def sum_3(a, b):
    return a + b + 3

@TaskGenerator
def subtract(a, b):
    return a - b

vals = list(range(8))
vals = [sum_2(v) for v in vals]
vals = [sum_3(v, v) for v in vals]
vals = [subtract(v, 5) for v in vals]
