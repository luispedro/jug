from jug import barrier, value, TaskGenerator
from jug.utils import identity
from jug.compound import CompoundTaskGenerator

@TaskGenerator
def double(x):
    return 2*x

@CompoundTaskGenerator
def twice(x):
    return (double(x), double(x))

@TaskGenerator
def tadd(y):
    return y[0] + y[1]

eight = twice(4)
barrier()
eight = identity(eight)
barrier()
sixteen = tadd(eight)


