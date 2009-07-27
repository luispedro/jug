# -*- coding: utf-8 -*-
# Copyright (C) 2008, Luís Pedro Coelho <lpc@cmu.edu>
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
Store: handle the file-system based backstore.
'''
from __future__ import division

try:
    import cPickle as pickle
except ImportError:
    import pickle
import numpy as np
import os
from os import path, mkdir, fdopen
from os.path import dirname, exists
import tempfile
import options
from gzip import GzipFile

def create_directories(dname):
    '''
    create_directories(dname)

    Recursively create directories.
    '''
    if dname.endswith('/'): dname = dname[:-1]
    head, tail = path.split(dname)
    if head: create_directories(head)
    try:
        mkdir(dname)
    except OSError:
        pass

def atomic_pickle_dump(object, outname):
    '''
    atomic_pickle_dump(outname, object)

    Performs the same as

    pickle.dump(object, file(outname,'w')

    but does it in a way that is guaranteed to be atomic even over NFS.
    '''
    # Rename is atomic in NFS, but we need to create the temporary file in
    # the same directory as the result.
    #
    # Don't mess unless you know what you are doing!

    # Format:
    #   If extension is .npy.gz, then it's a gzipped numpy npy file
    #   If extension is .pp.gz, then it's a gzipped python pickle
    #   If extension is .pp, then it's a python pickle
    #   If extension is empty and file is empty, then it's None
    if object is None:
        create_directories(dirname(outname))
        F=file(outname,'w')
        F.close()
        return
    extension = '.pp.gz'
    write = pickle.dump
    if isinstance(object, np.ndarray):
        extension = '.npy.gz'
        write = (lambda f,a: np.save(a,f))
    outname = outname + extension
    fd, fname = tempfile.mkstemp(extension,'jugtemp',options.tempdir)
    os.close(fd)
    F = GzipFile(fname,'w')
    write(object,F)
    F.close()
    create_directories(dirname(outname))
    os.rename(fname,outname)
dump = atomic_pickle_dump

def _fsize(fname):
    '''Returns file size'''
    return os.stat_result(os.stat(fname)).st_size

def can_load(fname):
    '''
    can = can_load(fname)

    '''
    return exists(fname + '.pp.gz') or exists(fname) or exists(fname + '.npy.gz')

def load(fname):
    '''
    obj = load(fname)

    Loads the objects. Equivalent to pickle.load(), but a bit smarter at times.
    '''
    if exists(fname) and _fsize(fname) == 0:
        return None
    elif exists(fname + '.pp.gz'):
        return pickle.load(GzipFile(fname + '.pp.gz'))
    elif exists(fname + '.pp'):
        return pickle.load(fname + '.pp')
    elif exists(fname + '.npy'):
        return np.load(fname + '.npy')
    elif exists(fname + '.npy.gz'):
        return np.load(GzipFile(fname + '.npy.gz'))
    else:
        return pickle.load(fname)

# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
