from jug import TaskGenerator
from time import sleep

@TaskGenerator
def is_prime(n):
    sleep(1.)
    for j in range(2,n-1):
        if (n % j) == 0:
            return False
    return True

primes100 = [is_prime(n) for n in range(2,101)]
