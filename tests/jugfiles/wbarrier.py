from jug import barrier, TaskGenerator

@TaskGenerator
def double(x):
    return x*2

two = double(1)
barrier()
four = double(two)

