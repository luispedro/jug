from jug import barrier, TaskGenerator

@TaskGenerator
def double(x):
    return 2*x

s = 1
for i in range(2048):
    s = double(s)

barrier()
s2 = s
for i in range(2048):
    s2 = double(s2)
