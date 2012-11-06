# -*- coding: utf-8 -*-
# Copyright (C) 2011-2012, Luis Pedro Coelho <luis@luispedro.org>
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

from __future__ import print_function
import sys

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
    import cPickle as pickle
    try:
        import numpy as np
    except ImportError:
        np = None
    for e in elems:
        if type(e) in (int,str,float):
            M.update(str(e) )
        elif type(e) == buffer:
            M.update(e)
        elif hasattr(e, '__jug_hash__'):
            M.update(e.__jug_hash__())
        elif type(e) in (list, tuple):
            M.update( repr( type(e) ) )
            hash_update(M, e)
        elif type(e) == dict:
            # Will have to extract the items and assert that they are
            # sorted....
            items = e.items()
            items.sort() # <-- Default sort
            items.insert( 0, 'dict' )
            hash_update(M,items)
        elif type(e) == set:
            items = list( e )
            items.sort()
            items.insert(0, 'set' )
            hash_update(M, items)
        elif np is not None and type(e) == np.ndarray:
            M.update('np.ndarray')
            if e.dtype == np.dtype('O'):
                # It is not so flat, so get into it
                hash_update(M, list( e.flatten() ) )
            else:
                M.update(pickle.dumps(e.dtype))
                M.update(pickle.dumps(e.shape))
                try:
                    buffer_ = e.data
                    M.update(buffer_)
                except:
                    M.update(e.copy().data)
        else:
            print("WARNING: Trying to hash object of unknown composition:", repr(type(e)), file = sys.stderr )
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
    return h.hexdigest()

