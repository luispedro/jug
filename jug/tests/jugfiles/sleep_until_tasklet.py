from jug import TaskGenerator

@TaskGenerator
def double(xs):
    return [x*2 for x in xs]

vs = [2,4]
vs = double(vs)
v0 = vs[0]
v02 = double([v0])

