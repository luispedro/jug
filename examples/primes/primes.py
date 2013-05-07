from jug import TaskGenerator
from time import sleep

@TaskGenerator
def is_prime(n):
    sleep(1.)
    for j in range(2,n-1):
        if (n % j) == 0:
            return False
    return True

primes100 = list(map(is_prime, range(2,101)))
