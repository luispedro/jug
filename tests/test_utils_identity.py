from jug.utils import identity
from .task_reset import task_reset

@task_reset
def test_utils_identity():
    identity(2).run() == 2

