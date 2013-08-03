from jug import TaskGenerator
from jug.io import write_task_out

@TaskGenerator
def double(x):
    return x*2

@TaskGenerator
def plus1(x):
    return x + 1

x = double(4)
x = plus1(double(x))
write_task_out(x, 'x.pkl', metadata_fname='x.meta.json', metadata_format='json')
write_task_out(x, 'x.pkl', metadata_fname='x.meta.yaml')
