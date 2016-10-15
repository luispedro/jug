# -*- coding: utf-8 -*-
# Copyright (C) 2009-2016, Luis Pedro Coelho <luis@luispedro.org>
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

from .task import Task, TaskGenerator, Tasklet, value

__all__ = [
    'timed_path',
    'identity',
    'CustomHash',
    ]

def _identity(x):
    return x

def identity(x):
    '''
    x = identity(x)

    `identity` implements the identity function as a Task
    (i.e., ``value(identity(x)) == x``)

    This seems pointless, but if ``x`` is, for example, a very large list, then
    using this function might speed up some computations. Consider::

        large = list(range(100000))
        large = jug.utils.identity(large)
        for i in range(100):
            Task(process, large, i)

    This way the list ``large`` is going to get hashed just once. Without the
    call to ``jug.utils.identity``, it would get hashed at each loop iteration.

    https://jug.readthedocs.io/en/latest/utilities.html#identity

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


    You can use the helpers in the ``jug.hash`` module (in particular
    ``hash_one``) to help you. The implementation of ``timed_path`` is a good
    example of how to use a CustomHash::

        def hash_with_mtime_size(path):
            from .hash import hash_one
            st = os.stat_result(os.stat(path))
            mtime = st.st_mtime
            size = st.st_size
            return hash_one((path, mtime, size))

        def timed_path(path):
            return CustomHash(path, hash_with_mtime_size)

    The ``path`` object (a string or bytes) is wrapped with a hashing function
    which checks the file value.

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

def hash_with_mtime_size(path):
    '''hvalue = hash_with_mtime_size(path)

    Computes a hash that depends on the mtime and size of the file ``path``.

    Parameters
    ----------
    path : filepath

    Returns
    -------
    hvalue : bytes
        A hashed version
    '''
    from .hash import hash_one
    st = os.stat_result(os.stat(path))
    mtime = st.st_mtime
    size = st.st_size
    return hash_one((path, mtime, size))


def timed_path(path):
    '''path = timed_path(path)

    Returns a Task object that simply returns `path` with the exception that it
    uses the paths mtime (modification time) and the file size in the hash.
    Thus, if the file is touched or changes size, this triggers an invalidation
    of the results (which propagates to all dependent tasks).

    Parameters
    ----------
    ipath : str
        A filesystem path

    Returns
    -------
    opath : str
        A task equivalent to ``(lambda: ipath)``.
    '''
    return CustomHash(path, hash_with_mtime_size)

@TaskGenerator
def jug_execute(args, check_exit=True, run_after=None):
    '''jug_execute(args, check_exit=True, run_after=None)

    Wrapper around ``subprocess.call()``

    Examples
    --------

    ::

        create_input_tmp = jug_execute(['cp', 'input', 'input.tmp'])
        jug_execute(['wc', '-l', 'input.tmp'], run_after=create_input_tmp)

    Parameters
    ----------
    args : list of str
    check_exit : boolean, optional
        If true (default), then a non-zero exit results in an exception
    run_after : any, optional
        This is unused by the function, but can be used to order different
        calls to jug_execute
    '''
    import subprocess
    ret = subprocess.call(args)
    if check_exit and ret != 0:
        raise SystemError("Error in system")
