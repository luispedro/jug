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
from StringIO import StringIO
try:
    import cPickle as pickle
except ImportError:
    import pickle
import numpy as np
from zlib import compress, decompress

__all__ = ['encode', 'decode']

def encode(object):
    '''
    s = encode(object)

    Return a string (byte-array) representation of object.

    Parameters
    ----------
      object : Any thing that is pickle()able
    Returns
    -------
      s : string (byte array).

    See
    ---
      `decode`
    '''
    if object is None:
        return ''
    prefix = 'P'
    write = pickle.dump
    if isinstance(object, np.ndarray):
        prefix = 'N'
        write = (lambda f,a: np.save(a,f))
    output = StringIO()
    write(object, output)
    return compress(prefix + output.getvalue())

def decode(s):
    '''
    object = decode(s)

    Reverses `encode`.
    Parameters
    ----------
      s : a string representation of the object.
    Returns
    -------
      object : the object
    '''
    if not s:
        return None
    s = decompress(s)
    prefix = s[0]
    s = s[1:]
    if prefix == 'P':
        return pickle.loads(s)
    elif prefix == 'N':
        s = StringIO(s)
        return np.load(s)
    else:
        raise IOError("jug.backend.encode: unknown prefix '%s'" % prefix)
    
