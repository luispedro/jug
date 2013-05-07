from jug import TaskGenerator

@TaskGenerator
def zero():
    return 0

@TaskGenerator
def range10():
    return list(range(10))

@TaskGenerator
def double(x):
    return 2*x

r = range10()
z = zero()
r0 = r[z]
z2  = double(r0)
