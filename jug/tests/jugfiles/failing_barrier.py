from jug import TaskGenerator, barrier
from jug.tests.jugfiles.exceptions import FailingTask

@TaskGenerator
def fail():
    raise FailingTask

@TaskGenerator
def plus1(x):
    return x + 1

a = fail()
b = plus1(a)
barrier()
c = plus1(b)
