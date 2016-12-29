# -*- coding: utf-8 -*-
# Copyright (C) 2011-2013, Luis Pedro Coelho <luis@luispedro.org>
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

def hash_update(M, elems):
    '''
    M = hash_update(M, elems)

    Update the hash object ``M`` with the sequence ``elems``.

    Parameters
    ----------
    M : hashlib object
        An object on which the update method will be called
    elems : sequence of 2-tuples

    Returns
    -------
    M : hashlib object
        This is the same object as the argument
    '''
    from six.moves import cPickle as pickle
    from six.moves import map
    import six

    try:
        import numpy as np
    except ImportError:
        np = None
    for n,e in elems:
        M.update(pickle.dumps(n))
        if hasattr(e, '__jug_hash__'):
            M.update(e.__jug_hash__())
        elif type(e) in (list, tuple):
            M.update(repr(type(e)).encode('utf-8'))
            hash_update(M, enumerate(e))
        elif type(e) == set:
            M.update(six.b('set'))
            # With randomized hashing, different runs of Python might result in
            # different orders, so sort. We cannot trust that all the elements
            # in the set will be comparable, so we convert them to their hashes
            # beforehand.
            items = list(map(hash_one, e))
            items.sort()
            hash_update(M, enumerate(items))
        elif type(e) == dict:
            M.update(six.b('dict'))
            items = [(hash_one(k),v) for k,v in e.items()]
            items.sort(key=(lambda k_v:k_v[0]))

            hash_update(M, items)
        elif np is not None and type(e) == np.ndarray:
            M.update(six.b('np.ndarray'))
            M.update(pickle.dumps(e.dtype))
            M.update(pickle.dumps(e.shape))
            try:
                buffer = e.data
                M.update(buffer)
            except:
                M.update(e.copy().data)
        else:
            M.update(pickle.dumps(e))
    return M

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
        Hashable object

    Returns
    -------
    hvalue : str
    '''
    h = new_hash_object()
    hash_update(h, [('hash1', obj)])
    return h.hexdigest().encode('utf-8')

