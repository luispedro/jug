from jug import TaskGenerator, bvalue

@TaskGenerator
def three():
    return [1, 2, 3]

@TaskGenerator
def double(x):
    return 2*x

t = three()
vals = bvalue({'first': [t[0]], 'last': (t[2],)})
doubled = [double(v) for v in vals['first'] + list(vals['last'])]
