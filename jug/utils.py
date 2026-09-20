# Copyright (C) 2009-2026, Luis Pedro Coelho <luis@luispedro.org>
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


import argparse
import fnmatch
import os
import re
import sys

from .task import Task, TaskGenerator, Tasklet, value

__all__ = [
    'timed_path',
    'identity',
    'jug_execute',
    'CustomHash',
    'sync_move',
    'cached_glob',
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

class CustomHash:
    '''
    value = CustomHash(obj, hash_function)

    Set a custom hash function

    This is an advanced feature and you can shoot yourself in the foot with it.
    Make sure you know what you are doing. In particular, hash_function should
    be a strong hash: ``hash_function(obj0) == hash_function(obj1)`` is taken
    to imply that ``obj0 == obj1``. The hash function should return a ``bytes``
    object.

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

    Returns an  object that returns `path` when passed to a jug Task with the
    exception that it uses the paths mtime (modification time) and the file
    size in the hash. Thus, if the file is touched or changes size, this
    triggers an invalidation of the results (which propagates to all dependent
    tasks).

    Parameters
    ----------
    path : str
        A filesystem path

    Returns
    -------
    opath : str
        A task equivalent to ``(lambda: path)``.
    '''
    return CustomHash(path, hash_with_mtime_size)


def prepare_task_matcher(pattern):
    '''Build a loose matcher from a ``--pattern`` string

    The pattern is interpreted as follows:

    - ``/regex/``: a regular expression (searched anywhere in the task name)
    - contains a ``.``: a full task name, but matched *anywhere* in the name
      (so ``mod.func`` also matches ``mod.func_other``)
    - otherwise: a function name, matched as ``\\.pattern`` anywhere in the
      task name (so ``func`` also matches ``mod.func_other``)

    For strict matching, use :func:`prepare_name_matcher`.

    Parameters
    ----------
    pattern : str

    Returns
    -------
    matcher : callable
        ``matcher(task_name)`` returns a true value if the name matches
    '''
    if re.match(r'/.*/', pattern):
        # Looks like a regular expression
        regex = re.compile(pattern.strip('/'))

    elif '.' in pattern:
        # Looks like a full task name
        regex = re.compile(pattern.replace('.', '\\.'))

    else:
        # A bare function name perhaps?
        regex = re.compile(r'\.' + pattern)

    return regex.search


def prepare_name_matcher(name):
    '''Build a strict matcher from a ``--name`` string

    A task name is ``module.function``. ``name`` must match the whole task
    name or a trailing part of it starting after a ``.``, so that
    ``mod.func`` and ``func`` both match the task ``pkg.mod.func`` but
    ``func`` does not match ``pkg.mod.func_other``.

    ``name`` may contain shell-style wildcards (see :mod:`fnmatch`), the
    most useful being ``*`` (any sequence of characters, including ``.``) and
    ``?``: ``func*`` matches both ``mod.func`` and ``mod.func_other``.

    Parameters
    ----------
    name : str

    Returns
    -------
    matcher : callable
        ``matcher(task_name)`` returns a bool
    '''
    regex = re.compile(fnmatch.translate(name))

    def matcher(task_name):
        pos = 0
        while True:
            if regex.match(task_name, pos):
                return True
            # try again from just after the next dot
            pos = task_name.find('.', pos) + 1
            if pos == 0:
                return False
    return matcher


def prepare_matcher_from_options(name=None, pattern=None):
    '''Combine ``--name`` and ``--pattern`` into a single matcher

    A task must satisfy all the criteria that are given (i.e., not ``None``).

    Returns
    -------
    matcher : callable or None
        ``None`` if neither criterion was given
    '''
    matchers = []
    if name is not None:
        matchers.append(prepare_name_matcher(name))
    if pattern is not None:
        matchers.append(prepare_task_matcher(pattern))
    if not matchers:
        return None
    return lambda task_name: all(m(task_name) for m in matchers)


class _DeprecatedTargetAction(argparse.Action):
    '''Store the value, but warn that this option name is deprecated'''
    def __call__(self, parser, namespace, values, option_string=None):
        sys.stderr.write(
            f"jug: warning: {option_string} is deprecated and will be removed "
            "in a future version. It now behaves like --name (strict match on "
            "the task name, '*' is a wildcard). Use --pattern for the previous "
            "behaviour (substring or /regex/ match).\n")
        setattr(namespace, self.dest, values)


def add_task_selection_options(parser, name_dest, pattern_dest, required, what):
    '''Add ``--name`` and ``--pattern`` (and deprecated ``--target``) to parser

    Used by the subcommands that select tasks by name (``execute`` and
    ``invalidate``).

    Parameters
    ----------
    parser : argparse parser
    name_dest, pattern_dest : str
        ``dest`` for ``--name`` (which ``--target`` and ``--invalid`` also
        write to) and ``--pattern``
    required : bool
        Whether one of them must be given
    what : str
        What is being selected (used in the help strings)
    '''
    group = parser.add_mutually_exclusive_group(required=required)
    group.add_argument('--name', action='store', dest=name_dest,
                       metavar='NAME',
                       help=(f"{what} whose name is NAME. NAME is either "
                             "the full task name (module.function) or the "
                             "end of it (function), and may contain "
                             "wildcards (e.g., 'function*')"))
    group.add_argument('--pattern', action='store', dest=pattern_dest,
                       metavar='PATTERN',
                       help=(f"{what} whose name contains PATTERN (or matches "
                             "PATTERN if given as /regex/). Note that "
                             "'function' also matches 'function_other'; "
                             "use --name for exact matching"))
    group.add_argument('--target', '--invalid', action=_DeprecatedTargetAction,
                       dest=name_dest, metavar='NAME',
                       help='Deprecated: use --name (or --pattern)')


@TaskGenerator
def jug_execute(args, check_exit=True, run_after=None, return_value=None):
    '''jug_execute(args, check_exit=True, run_after=None, return_value=None)

    Wrapper around ``subprocess.call()``

    The ``run_after`` and ``return_value`` arguments are used only for setting
    dependencies.

    Examples
    --------

    ::

        create_input_tmp = jug_execute(['cp', 'input', 'input.tmp'])
        jug_execute(['wc', '-l', 'input.tmp'], run_after=create_input_tmp)

        # Use the return_value argument:

        oname = 'input.tmp'
        oname = jug_execute(['cp', 'input', oname], return_value=oname)
        jug_execute(['wc', '-l', oname]) # <- Now depends on previous task


    Parameters
    ----------
    args : list of str
    check_exit : boolean, optional
        If true (default), then a non-zero exit results in an exception
    run_after : any, optional
        This is unused by the function, but can be used to order different
        calls to jug_execute
    return_value : any, optional
        A value to return. Used to induce task dependencies
    '''
    import subprocess
    ret = subprocess.call(args)
    if check_exit and ret != 0:
        raise SystemError("Error in system")
    return return_value

def sync_move(src, dst):
    '''Sync the file and move it

    This ensures that the move is truly atomic

    Parameters
    ----------
    src : filename
        Source file
    dst: filename
        Destination file
    '''
    from jug.backends.file_store import fsync_dir
    from os import rename
    fsync_dir(src)
    rename(src, dst)

def glob_sort(pat):
    '''Glob and sort

    Parameters
    ----------
    pat: Same as glob.glob

    Returns
    -------
    files : list of str
    '''
    from glob import glob
    rs = glob(pat)
    rs.sort()
    return rs

def cached_glob(pat):
    '''
    A short-hand for

        from jug import CachedFunction
        from glob import glob
        CachedFunction(glob, pattern)

    with the extra bonus that results are returned *sorted*

    Parameters
    ----------
    pat: Same as glob.glob

    Returns
    -------
    files : list of str
    '''
    from .task import Task
    t = Task(glob_sort, pat)
    if not t.can_load():
        return t.run()
    return t.value()

