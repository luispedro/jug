# -*- coding: utf-8 -*-
# Copyright (C) 2008-2009, Luís Pedro Coelho <lpc@cmu.edu>
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
import errno
from os import path, mkdir, fdopen
from os.path import dirname, exists
import tempfile
import options
from gzip import GzipFile

def _fsize(fname):
    '''Returns file size'''
    return os.stat_result(os.stat(fname)).st_size


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
    except OSError, e:
        if e.errno != errno.EEXIST:
            raise


class file_store(object):
    def __init__(self, dname):
        '''
        file_store(dname)

        Recursively create directories.
        '''
        if dname.endswith('/'): dname = dname[:-1]
        self.jugdir = dname
        head, tail = path.split(dname)
        if head: create_directories(head)
        create_directories(options.tempdir)
        try:
            mkdir(dname)
        except OSError, e:
            if e.errno != errno.EEXIST:
                raise

    def _getfname(self, outname):
        return path.join(self.jugdir, outname[0], outname[1], outname[2:])


    def dump(self, object, outname):
        '''
        dump(outname, object)

        Performs the same as

        pickle.dump(object, file(outname,'w')

        but does it in a way that is guaranteed to be atomic even over NFS.
        '''
        # Rename is atomic in NFS, but we need to create the temporary file in
        # the same directory as the result.
        #
        # Don't mess unless you know what you are doing!
        outname = self._getfname(outname)

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


    def can_load(self, fname):
        '''
        can = can_load(fname)
        '''
        fname = self._getfname(fname)
        return exists(fname + '.pp.gz') or exists(fname) or exists(fname + '.npy.gz')

    def load(self, fname):
        '''
        obj = load(fname)

        Loads the objects. Equivalent to pickle.load(), but a bit smarter at times.
        '''
        fname = self._getfname(fname)
        if exists(fname) and _fsize(fname) == 0:
            return None
        elif exists(fname + '.pp.gz'):
            return pickle.load(GzipFile(fname + '.pp.gz'))
        elif exists(fname + '.npy.gz'):
            return np.load(GzipFile(fname + '.npy.gz'))
        else:
            return pickle.load(fname)

    def remove(self, fname):
        '''
        was_removed = remove(fname)

        Remove the entry associated with fname.

        Returns whether any entry was actually removed.
        '''
        fname = self._getfname(fname)
        possible = [fname,fname+'.pp.gz',fname+'.npy.gz']
        for p in possible:
            if os.path.exists(p):
                os.unlink(p)
                return True
        return False

    def cleanup(self, active):
        '''
        cleanup()

        Implement 'cleanup' command
        '''
        files = set()
        for path,_,fs in os.walk(self.jugdir):
            for f in fs:
                files.add(path+'/'+f)
        for t in tasks:
            fname = t.hash()
            possible = [fname,fname+'.pp.gz',fname+'.npy.gz']
            for p in possible:
                try:
                    files.remove(p)
                except:
                    pass
        for f in files:
            os.unlink(f)
        print 'Removed %s files' % len(files)

    def getlock(self, name):
        return file_based_lock(name)



# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
