from jug import TaskGenerator
from jug.task import return_tuple

@TaskGenerator
def zero():
    return 0

@TaskGenerator
def range10():
    return list(range(10))

@TaskGenerator
def double(x):
    return 2*x

@return_tuple(2)
@TaskGenerator
def plus1(x):
    return x, 1+x

r = range10()
z = zero()
r0 = r[z]
z2  = double(r0)
z2_2,z3 = plus1(z2)

