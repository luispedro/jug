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

from __future__ import division

'''
Store: handle the file-system based backstore.
'''
try:
    import cPickle as pickle
except:
    import pickle
import os
from os import path, mkdir, fdopen
from os.path import dirname
import tempfile
import options

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
    fd, fname = tempfile.mkstemp('.pp','jugtemp',options.tempdir)
    F = fdopen(fd,'w')
    pickle.dump(object,F)
    F.close()
    create_directories(dirname(outname))
    os.rename(fname,outname)

def obj2fname(obj):
    '''
    fname = obj2fname(obj)

    Returns the filename used to save the object obj
    '''
    M = md5.md5()
    S = pickle.dumps(func,args)
    M.update(S)
    D = M.hexdigest()
    return D[0] + '/' + D[1] + '/' + D[2:] + '.pp'

# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
