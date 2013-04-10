from jug import TaskGenerator

@TaskGenerator
def double(x):
    return x,2*x

x = 2
y = double(x)
z = double(y[0])

