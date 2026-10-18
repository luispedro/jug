from jug import TaskGenerator, bvalue

@TaskGenerator
def three():
    return [1, 2, 3]

t = three()
x = bvalue(t[5])
