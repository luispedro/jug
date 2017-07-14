from time import sleep

from jug import TaskGenerator

@TaskGenerator
def is_prime(n):
    sleep(1.)
    for j in range(2, n - 1):
        if (n % j) == 0:
            return False
    return True

@TaskGenerator
def count_primes(ps):
    return sum(ps)

@TaskGenerator
def write_output(n):
    output = open('output.txt', 'wt')
    output.write("Found {0} primes <= 100.\n".format(n))
    output.close()

primes100 = []
for n in range(2, 101):
    primes100.append(is_prime(n))

n_primes = count_primes(primes100)
write_output(n_primes)
