# -*- coding: utf-8 -*-
# Copyright (C) 2008-2010, Luis Pedro Coelho <lpc@cmu.edu>
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
file_store : file-system based data store & locks.
'''
from __future__ import division

try:
    import cPickle as pickle
except ImportError:
    import pickle
import os
from os import path, mkdir, fdopen
from os.path import dirname, exists
import errno
import tempfile
import numpy as np
import shutil
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
        create_directories(self.tempdir())
        try:
            mkdir(dname)
        except OSError, e:
            if e.errno != errno.EEXIST:
                raise

    def tempdir(self):
        return path.join(self.jugdir, 'tempfiles')

    def _getfname(self, name):
        return path.join(self.jugdir, name[0], name[1], name[2:])


    def dump(self, object, name):
        '''
        dump(object, name)

        Performs the same as

        pickle.dump(object, file(name,'w')

        but does it in a way that is guaranteed to be atomic even over NFS.
        '''
        # Rename is atomic in NFS, but we need to create the temporary file in
        # the same directory as the result.
        #
        # Don't mess unless you know what you are doing!
        name = self._getfname(name)

        # Format:
        #   If extension is .npy.gz, then it's a gzipped numpy npy file
        #   If extension is .pp.gz, then it's a gzipped python pickle
        #   If extension is .pp, then it's a python pickle
        #   If extension is empty and file is empty, then it's None
        if object is None:
            create_directories(dirname(name))
            F=file(name,'w')
            F.close()
            return
        extension = '.pp.gz'
        write = pickle.dump
        if isinstance(object, np.ndarray):
            extension = '.npy.gz'
            write = (lambda f,a: np.save(a,f))
        name = name + extension
        fd, fname = tempfile.mkstemp(extension, 'jugtemp', self.tempdir())
        os.close(fd)
        F = GzipFile(fname,'w')
        write(object,F)
        F.close()
        create_directories(dirname(name))
        os.rename(fname, name)


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
            f = GzipFile(fname + '.pp.gz')
            load = pickle.load
        elif exists(fname + '.npy.gz'):
            f = GzipFile(fname + '.npy.gz')
            load = np.load
        else:
            f = file(fname)
            load = pickle.load
        res = load(f)
        f.close()
        return res

    def remove(self, fname):
        '''
        was_removed = remove(fname)

        Remove the entry associated with fname.

        Returns whether any entry was actually removed.
        '''
        fname = self._getfname(fname)
        possible = [fname,fname+'.pp.gz',fname+'.npy.gz']
        for p in possible:
            try:
                os.unlink(p)
                return True
            except OSError:
                pass
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
        return file_based_lock(self.jugdir, name)

    def close(self):
        '''
        store.close()

        Has no effect on file based stores.
        '''
        pass

    @staticmethod
    def remove_store(jugdir):
        shutil.rmtree(jugdir)


class file_based_lock(object):
    '''
    file_based_lock: File-system based locks

    Functions:
    ----------

        * get(): acquire the lock
        * release(): release the lock
        * is_locked(): check lock state
    '''

    def __init__(self, jugdir, name):
        self.fullname = path.join(jugdir, 'locks', name + '.lock')

    def get(self):
        '''
        lock.get()

        Create a lock for name in an NFS compatible way.
        '''
        if exists(self.fullname): return False
        create_directories(path.dirname(self.fullname))
        try:
            fd = os.open(self.fullname,os.O_RDWR|os.O_CREAT|os.O_EXCL)
            F = os.fdopen(fd,'w')
            print >>F, 'Lock', os.getpid()
            F.close()
            return True
        except OSError:
            return False

    def release(self):
        '''
        lock.release()

        Removes lock
        '''
        try:
            os.unlink(self.fullname)
        except OSError:
            pass

    def is_locked(self):
        '''
        locked = lock.is_locked()

        Returns whether a lock exists for name. Note that the answer can
        be invalid by the time this function returns. Only by trying to
        acquire the lock can you avoid race-conditions. See the get() function.
        '''
        return path.exists(self.fullname)

# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
