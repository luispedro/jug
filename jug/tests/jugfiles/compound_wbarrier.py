from jug import barrier, value, TaskGenerator
from jug.compound import CompoundTaskGenerator

@TaskGenerator
def double(x):
    return 2*x

@CompoundTaskGenerator
def twice(x):
    x2 = double(x)
    barrier()
    return double(value(x2))

four = double(2)
sixteen = twice(four)

