# -*- coding: utf-8 -*-
# Copyright (C) 2009-2014, Luis Pedro Coelho <luis@luispedro.org>
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


import os

from .task import Task, Tasklet, value

__all__ = [
    'timed_path',
    'identity',
    'CustomHash',
    ]

def _return_first(one, two):
    '''
    one = _return_first(one, two)

    Used internally to implement jug.util.timed_path
    '''
    return one

def timed_path(path):
    '''
    opath = timed_path(ipath)

    Returns a Task object that simply returns `path` with the exception that it uses the
    paths mtime (modification time) in the hash. Thus, if the file contents change, this triggers
    an invalidation of the results (which propagates).

    Parameters
    ----------
    ipath : str
        A filesystem path

    Returns
    -------
    opath : str
        A task equivalent to ``(lambda: ipath)``.
    '''
    mtime = os.stat_result(os.stat(path)).st_mtime
    return Task(_return_first, path, mtime)

def _identity(x):
    return x

def identity(x):
    '''
    x = identity(x)

    `identity` implements the identity function as a Task
    (i.e., value(identity(x)) == x)

    This seems pointless, but if x is, for example, a very large list, then
    using the output of this function might be much faster than using x directly.

    Parameters
    ----------
    x : any object

    Returns
    -------
    x : x
    '''
    if isinstance(x, (Task, Tasklet)):
        return x
    t = Task(_identity, x)
    t.name = 'identity'
    return t

class CustomHash(object):
    '''
    value = CustomHash(obj, hash_function)

    Set a custom hash function

    This is an advanced feature and you can shoot yourself in the foot with it.
    Make sure you know what you are doing. In particular, hash_function should
    be a strong hash: ``hash_function(obj0) == hash_function(obj1)`` is taken
    to imply that ``obj0 == obj1``

    Parameters
    ----------
    obj : any object
    hash_function : function
        This should take your object and return a str
    '''
    def __init__(self, obj, hash_function):
        self.obj = obj
        self.hash_function = hash_function

    def __jug_hash__(self):
        return self.hash_function(self.obj)

    def __jug_value__(self):
        return value(self.obj)
