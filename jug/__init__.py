# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
# Copyright (C) 2008-2016, Luis Pedro Coelho <luis@luispedro.org>
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

'''
============================================
JUG: Coarse Level Parallelisation for Python
============================================

The main use of jug is from the command line::

    jug status jugfile.py
    jug execute jugfile.py

Where ``jugfile.py`` is a Python script using the ``jug`` library.
'''

from .task import TaskGenerator, Task, Tasklet, value, CachedFunction, iteratetask
from .compound import CompoundTaskGenerator, CompoundTask
from .barrier import barrier, bvalue
from .options import set_jugdir

from .jug import init
from .backends import file_store, dict_store, redis_store

from .jug_version import __version__

__all__ = [
    'Task',
    'Tasklet',
    'TaskGenerator',
    'iteratetask',
    'value',
    'CachedFunction',
    'barrier',
    'bvalue',

    'set_jugdir',

    'init',
    'file_store',
    'dict_store',
    'redis_store',
    ]

