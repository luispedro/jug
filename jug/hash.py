# Copyright (C) 2011-2026, Luis Pedro Coelho <luis@luispedro.org>
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
'''
Hashing of task arguments

Tasks are identified by a hash of their function and arguments, computed
with the functions in this module. Objects can customize how they are hashed
by implementing a ``__jug_hash__()`` method returning ``bytes``.
'''

# The pickle protocol is pinned (rather than using pickle's default, which
# changes between Python versions: 4 up to Python 3.13, 5 from 3.14) so that
# task hashes, and thus cached results, are stable across interpreter versions.
# Do not change this without a compatibility plan: it invalidates all hashes.
_PICKLE_PROTOCOL = 4

def hash_update(M, elems):
    '''
    M = hash_update(M, elems)

    Update the hash object ``M`` with the sequence ``elems``.

    Objects which define a ``__jug_hash__()`` method (which must return
    ``bytes``) are hashed by calling it. Lists, tuples, sets, frozensets,
    dictionaries and numpy arrays are handled specially (recursively, and
    independently of the iteration order for sets and dictionaries). Any
    other object is hashed by pickling it.

    Parameters
    ----------
    M : hashlib object
        An object on which the update method will be called
    elems : sequence of 2-tuples
        Pairs of ``(name, object)``

    Returns
    -------
    M : hashlib object
        This is the same object as the argument
    '''
    import pickle

    try:
        import numpy as np
    except ImportError:
        np = None
    for n,e in elems:
        M.update(pickle.dumps(n, protocol=_PICKLE_PROTOCOL))
        if hasattr(e, '__jug_hash__'):
            M.update(e.__jug_hash__())
        elif type(e) in (list, tuple):
            M.update(repr(type(e)).encode('utf-8'))
            hash_update(M, enumerate(e))
        elif type(e) in (set, frozenset):
            M.update(b'set' if type(e) == set else b'frozenset')
            # With randomized hashing, different runs of Python might result in
            # different orders, so sort. We cannot trust that all the elements
            # in the set will be comparable, so we convert them to their hashes
            # beforehand.
            items = [hash_one(el) for el in e]
            items.sort()
            hash_update(M, enumerate(items))
        elif type(e) == dict:
            M.update(b'dict')
            items = [(hash_one(k),v) for k,v in e.items()]
            items.sort(key=(lambda k_v:k_v[0]))

            hash_update(M, items)
        elif np is not None and type(e) == np.ndarray:
            M.update(b'np.ndarray')
            M.update(pickle.dumps(e.dtype, protocol=_PICKLE_PROTOCOL))
            M.update(pickle.dumps(e.shape, protocol=_PICKLE_PROTOCOL))
            if e.dtype.hasobject:
                # The buffer of an object array holds pointers, which differ
                # between processes, so hash the elements themselves
                hash_update(M, enumerate(e.ravel().tolist()))
            else:
                try:
                    buffer = e.data
                    M.update(buffer)
                except BufferError:
                    # Non-contiguous arrays do not expose a contiguous buffer
                    M.update(e.copy().data)
        else:
            if isinstance(e, (list, tuple)) and _contains_task(e):
                raise TypeError(
                    f'jug: Tasks inside a {type(e).__name__} (a subclass of '
                    'list/tuple, such as a namedtuple) are not supported. '
                    'Use a plain list, tuple, or dict instead.')
            M.update(pickle.dumps(e, protocol=_PICKLE_PROTOCOL))
    return M

def _contains_task(obj):
    '''Returns whether ``obj`` contains a Task or Tasklet (recursively)'''
    from .task import Task, Tasklet
    queue = [obj]
    while queue:
        e = queue.pop()
        if isinstance(e, (Task, Tasklet)):
            return True
        elif hasattr(e, '__jug_dependencies__'):
            queue.extend(e.__jug_dependencies__())
        elif isinstance(e, (list, tuple, set, frozenset)):
            queue.extend(e)
        elif isinstance(e, dict):
            queue.extend(e.values())
    return False

def new_hash_object():
    '''
    M = new_hash_object()

    Returns a new hash object

    Returns
    -------
    M : hashlib object
    '''
    import hashlib
    return hashlib.sha1()

def hash_one(obj):
    '''
    hvalue = hash_one(obj)

    Compute a hash from a single object

    Parameters
    ----------
    obj : object
        Any object that jug can hash (picklable, or implementing
        ``__jug_hash__``)

    Returns
    -------
    hvalue : bytes
        Hexadecimal digest
    '''
    h = new_hash_object()
    hash_update(h, [('hash1', obj)])
    return h.hexdigest().encode('utf-8')

