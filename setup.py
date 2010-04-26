# -*- coding: utf-8 -*-
# Copyright (C) 2008-2010, Luis Pedro Coelho <lpc@cmu.edu>
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

from __future__ import division
from sys import exit
try:
    import setuptools
except:
    print '''
setuptools not found. Please install it.

On linux, the package is often called python-setuptools'''
    exit(1)

execfile('jug/jug_version.py')

long_description = '''\
Jug: A Task-Based Parallelization Framework
-------------------------------------------

Jug allows you to write code that is broken up into
tasks and run different tasks on different processors.

It has two storage backends: One uses the filesystem to
communicate between processes and works correctly over NFS,
so you can coordinate processes on different machines. The
other uses a redis database and all it needs is for different
processes to be able to communicate with a common redis server.

Jug is a pure Python implementation and should work on any platform.

*Website*: `http://luispedro.org/software/jug <http://luispedro.org/software/jug>`_

*Video*: On `vimeo <http://vimeo.com/8972696>`_ or `showmedo
<http://showmedo.com/videotutorials/video?name=9750000;fromSeriesID=975>`_ '''

classifiers = [
'Development Status :: 4 - Beta',
'Environment :: Console',
'License :: OSI Approved :: MIT License',
'Operating System :: POSIX',
'Operating System :: OS Independent',
'Programming Language :: Python',
'Topic :: Scientific/Engineering',
'Topic :: Software Development',
'Intended Audience :: Science/Research',
]

setuptools.setup(name = 'Jug',
      version = __version__,
      description = 'A Task Based Parallelization Framework',
      long_description = long_description,
      author = 'Luis Pedro Coelho',
      author_email = 'lpc@cmu.edu',
      license = 'MIT',
      platforms = ['Any'],
      classifiers = classifiers,
      url = 'http://luispedro.org/software/jug',
      packages = setuptools.find_packages(exclude='tests'),
      scripts = ['bin/jug'],
      test_suite = 'nose.collector',
      )


