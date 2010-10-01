from jug import TaskGenerator
from time import sleep

@TaskGenerator
def is_prime(n):
    sleep(1.)
    for j in xrange(2,n-1):
        if (n % j) == 0:
            return False
    return True

primes100 = map(is_prime, xrange(2,101))
