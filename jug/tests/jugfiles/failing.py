from jug import TaskGenerator
from jug.tests.jugfiles.exceptions import FailingTask

@TaskGenerator
def some_fail(x):
    if x in (2, 5, 8):
        raise FailingTask

    return x

@TaskGenerator
def plus1(x):
    return x + 1

vals = list(map(some_fail, list(range(10))))
vals = list(map(plus1, vals))

# This jugfile has 20 tasks of which 10 are executable and 10 are waiting.
# If the first 10, 3 will fail.
# With full execution this should result in 14 complete tasks, 3 failed and 3 waiting
