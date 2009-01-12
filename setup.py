# -*- coding: utf-8 -*-
# Copyright (C) 2008, Luís Pedro Coelho <lpc@cmu.edu>
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

from __future__ import division
from sys import exit
try:
    import setuptools
except:
    print '''
setuptools not found. Please install it.

On linux, the package is often called python-setuptools'''
    exit(1)

long_description = '''\
Jug: A Task-Based Parallelization Framework
-------------------------------------------

Jug allows you to write code that is broken up into
tasks and run different tasks on different processors.

It uses the filesystem to communicate between processes and
works correctly over NFS, so you can coordinate processes on
different machines.
'''
setuptools.setup(name = 'Jug',
      version = '0.2',
      description = 'A Task Based Parallelization Framework',
      long_description = long_description,
      author = 'Luís Pedro Coelho',
      author_email = 'lpc@mcu.edu',
      url = 'http://luispedro.org/jug',
      packages = setuptools.find_packages(exclude='tests'),
      scripts = ['jug/jug.py'],
      test_suite = 'nose.collector',
      )


# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
