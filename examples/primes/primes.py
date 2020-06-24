from jug import TaskGenerator

@TaskGenerator
def is_prime(n):
    from time import sleep

    # Sleep for 1 second, this runs too fast and is not a good demo
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
    with open('output.txt', 'wt') as output:
        output.write("Found {0} primes <= 100.\n".format(n))

primes100 = []
for n in range(2, 101):
    primes100.append(is_prime(n))

n_primes = count_primes(primes100)
write_output(n_primes)
