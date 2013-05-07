from jug import TaskGenerator
from jug.utils import CustomHash

hash_called = 0

def bad_hash(x):
    global hash_called
    hash_called += 1
    return ('%s' % x).encode('utf-8')

@TaskGenerator
def double(x):
    return 2*x

one = CustomHash(1, bad_hash)

two = double(one)

