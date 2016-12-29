# -*- coding: utf-8 -*-
# Copyright (C) 2008-2016, Luis Pedro Coelho <luis@luispedro.org>
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


from six.moves import cPickle as pickle
from six import BytesIO
import six
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
    output = BytesIO()
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
    prefix = six.b('P')
    write = lambda f,a: pickle.dump(f, a, protocol=pickle.HIGHEST_PROTOCOL)
    try:
        import numpy as np
        if type(object) == np.ndarray:
            prefix = six.b('N')
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
        MAX_BLOCK = 2000000000
        if len(s) > MAX_BLOCK:
            self.stream.write(self.C.compress(s[:MAX_BLOCK]))
            self.write(s[MAX_BLOCK:])
        else:
            self.stream.write(self.C.compress(s))

    def flush(self):
        self.stream.write(self.C.flush())
        self.stream.flush()

class decompress_stream(object):
    def __init__(self, stream, block=8192):
        self.stream = stream
        self.D = zlib.decompressobj()
        self.block = block
        self.lastread = six.b('')
        self.queue = six.b('')

    def read(self, nbytes):
        if len(self.queue) >= nbytes:
            res = self.queue[:nbytes]
            self.queue = self.queue[nbytes:]
            self.lastread = res
            return res
        res = self.queue
        self.queue = six.b('')

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
        import six
        qi = self.queue.find(six.b('\n'))
        if qi >= 0:
            qi += 1
            res = self.queue[:qi]
            self.queue = self.queue[qi:]
            return res
        line = six.b('')
        while True:
            block = self.read(self.block)
            if not block:
                return line
            ln = block.find(six.b('\n'))
            if ln == -1:
                line += block
            else:
                ln += 1
                line += block[:ln]
                self.seek(ln-len(block), 1)
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
    return decode_from(BytesIO(s))

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
    elif prefix == six.b('P'):
        return pickle.load(stream)
    elif prefix == six.b('N'):
        import numpy as np
        return np.load(stream)
    else:
        raise IOError("jug.backend.decode_from: unknown prefix '%s'" % prefix)
