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

'''
file_store : file-system based data store & locks.
'''
from __future__ import division

import os
from os import path, mkdir, fdopen
from os.path import dirname, exists
import errno
import tempfile
import shutil

from jug.backends.encode import encode, decode

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

        pickle.dump(object, file(name,'w'))

        but does it in a way that is guaranteed to be atomic even over NFS.
        '''
        name = self._getfname(name)
        create_directories(dirname(name))
        s = encode(object)
        if not s:
            file(name,'w').close()
            return

        fd, fname = tempfile.mkstemp('.jugtmp', 'jugtemp', self.tempdir())
        output = os.fdopen(fd, 'w')
        output.write(s)
        output.close()

        # Rename is atomic even over NFS.
        os.rename(fname, name)


    def can_load(self, fname):
        '''
        can = can_load(fname)
        '''
        fname = self._getfname(fname)
        return exists(fname)

    def load(self, fname):
        '''
        obj = load(fname)

        Loads the objects. Equivalent to pickle.load(), but a bit smarter at times.
        '''
        fname = self._getfname(fname)
        input = file(fname)
        s = input.read()
        input.close()
        return decode(s)

    def remove(self, fname):
        '''
        was_removed = remove(fname)

        Remove the entry associated with fname.

        Returns whether any entry was actually removed.
        '''
        try:
            fname = self._getfname(fname)
            os.unlink(fname)
            return True
        except OSError:
            return False

    def cleanup(self, active):
        '''
        cleanup()

        Implement 'cleanup' command
        '''
        files = set()
        for dir,_,fs in os.walk(self.jugdir):
            for f in fs:
                files.add(path.join(dir,f))
        for t in active:
            fname = self._getfname(t.hash())
            if fname in files:
                files.remove(fname)
        for f in files:
            os.unlink(f)
        return len(files)

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

