#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (C) 2017, Luis Pedro Coelho <luis@luispedro.org>
# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.


from . import SubCommand

__all__ = ['DemoCommand']


class DemoCommand(SubCommand):
    '''Create demo directory.

    '''
    name = "demo"

    def run(self, *args, **kwargs):
        import os
        from os import path
        print('''
Jug will create a directory called 'jug-demo/' with a file called 'primes.py'
inside.

You can test jug by switching to that directory and running the commands:

    jug status primes.py

followed by

    jug execute primes.py

Upon termination of the process, results will be in a file called 'output.txt'.

PARALLEL USAGE

You can speed up the process by running several 'jug execute' in parallel:

    jug execute primes.py &
    jug execute primes.py &
    jug execute primes.py &
    jug execute primes.py &

TROUBLE SHOOTING:

Should you run into issues, you can run the internal tests for jug with

    jug test-jug


FURTHER READING

The online documentation contains further reading. You can read the next
tutorial here:

http://jug.readthedocs.io/en/latest/decrypt-example.html
''')
        if path.exists('jug-demo'):
            print("Jug-demo previously created")
            return
        os.mkdir('jug-demo')
        output = open('jug-demo/primes.py', 'wt')
        output.write(r'''
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
''')
        output.close()

demo = DemoCommand()
