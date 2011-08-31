# -*- coding: utf-8 -*-
# Copyright (C) 2008-2011, Luis Pedro Coelho <luis@luispedro.org>
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
import zlib

__all__ = ['encode', 'decode', 'encode_to', 'decode_from']

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
    output = StringIO()
    encode_to(object, output)
    return output.getvalue()

def encode_to(object, stream):
    '''
    encode_to(object, stream)

    Encodes the object into the stream ``stream``

    Parameters
    ----------
    object : Any object
    stream : file-like object
    '''
    if object is None:
        return
    prefix = 'P'
    write = pickle.dump
    try:
        import numpy as np
        if isinstance(object, np.ndarray):
            prefix = 'N'
            write = (lambda f,a: np.save(a,f))
    except ImportError:
        pass
    stream = compress_stream(stream)
    stream.write(prefix)
    write(object, stream)
    stream.flush()

class compress_stream(object):
    def __init__(self, stream):
        self.stream = stream
        self.C = zlib.compressobj()

    def write(self, s):
        self.stream.write(self.C.compress(s))

    def flush(self):
        self.stream.write(self.C.flush())
        self.stream.flush()

class decompress_stream(object):
    def __init__(self, stream, block=128):
        self.stream = stream
        self.D = zlib.decompressobj()
        self.block = block
        self.lastread = ''
        self.queue = ''

    def read(self, nbytes):
        res = ''
        if self.queue:
            if len(self.queue) >= nbytes:
                res = self.queue[:nbytes]
                self.queue = self.queue[nbytes:]
                return res
            res = self.queue
            self.queue = ''

        if self.D.unconsumed_tail:
            res += self.D.decompress(self.D.unconsumed_tail, nbytes - len(res))
        while len(res) < nbytes:
            buf = self.stream.read(self.block)
            if not buf:
                res += self.D.flush()
                break
            res += self.D.decompress(buf, nbytes - len(res))
        self.lastread = res
        return res

    def seek(self, offset, whence):
        if whence != 1:
            raise NotImplementedError
        while offset > 0:
            nbytes = min(offset, self.block)
            self.read(nbytes)
            offset -= nbytes
        if offset < 0:
            if offset > len(self.lastread):
                raise ValueError('seek too far')
            skip = len(self.lastread) + offset
            self.queue = self.lastread[skip:]

    def readline(self):
        line = ''
        while True:
            block = self.read(self.block)
            if not block:
                return line
            ln = block.find('\n')
            if ln == -1:
                line += block
            else:
                ln += 1
                line += block[:ln]
                self.seek(ln-len(block), 1)
                return line
        return line

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
    return decode_from(StringIO(s))

def decode_from(stream):
    '''
    object = decode_from(stream)

    Decodes the object from the stream ``stream``

    Parameters
    ----------
    stream : file-like object

    Returns
    -------
    object : decoded object
    '''
    stream = decompress_stream(stream)
    prefix = stream.read(1)
    if not prefix:
        return None
    elif prefix == 'P':
        return pickle.load(stream)
    elif prefix == 'N':
        import numpy as np
        return np.load(stream)
    else:
        raise IOError("jug.backend.decode_from: unknown prefix '%s'" % prefix)
