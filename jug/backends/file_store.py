# -*- coding: utf-8 -*-
# Copyright (C) 2008-2011, Luis Pedro Coelho <lpc@cmu.edu>
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

def create_directories(dname):
    '''
    create_directories(dname)

    Recursively create directories.
    '''
    if dname.endswith('/'): dname = dname[:-1]
    head, tail = path.split(dname)
    if path.exists(dname): return
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
        create_directories(self.jugdir)
        create_directories(self.tempdir())

    def tempdir(self):
        return path.join(self.jugdir, 'tempfiles')

    def _getfname(self, name):
        return path.join(self.jugdir, name[:2], name[2:])


    def dump(self, object, name):
        '''
        store.dump(object, name)

        Performs the same as

        pickle.dump(object, file(name,'w'))

        but does it in a way that is guaranteed to be atomic even over NFS.
        '''
        name = self._getfname(name)
        create_directories(dirname(name))
        fd, fname = tempfile.mkstemp('.jugtmp', 'jugtemp', self.tempdir())
        output = os.fdopen(fd, 'w')
        try:
            import numpy as np
            if type(object) == np.ndarray:
                np.lib.format.write_array(output, object)
                output.close()
                os.rename(fname, name)
                return
        except ImportError:
            pass
        except OSError:
            pass
        except ValueError:
            pass

        s = encode(object)
        if not s:
            file(name,'w').close()
            return

        output.write(s)
        output.close()

        # Rename is atomic even over NFS.
        os.rename(fname, name)

    def list(self):
        '''
        keys = store.list()

        Returns a list of all the keys in the store
        '''
        keys = []
        for d in os.listdir(self.jugdir):
            if len(d) == 2:
                for f in os.listdir(d):
                    keys.append(d+f)
        return keys


    def can_load(self, name):
        '''
        can = store.can_load(name)
        '''
        fname = self._getfname(name)
        return exists(fname)

    def load(self, name):
        '''
        obj = store.load(name)

        Loads the objects. Equivalent to pickle.load(), but a bit smarter at
        times.

        Parameters
        ----------
        name : str
            Key to use

        Returns
        -------
        obj : any
            The object that was saved under ``name``
        '''
        fname = self._getfname(name)
        input = file(fname)
        try:
            import numpy as np
            return np.load(input, mmap_mode='r')
        except ValueError:
            input.seek(0)
        except ImportError:
            pass
        s = input.read()
        input.close()
        return decode(s)

    def remove(self, name):
        '''
        was_removed = store.remove(name)

        Remove the entry associated with name.

        Returns whether any entry was actually removed.
        '''
        try:
            fname = self._getfname(name)
            os.unlink(fname)
            return True
        except OSError:
            return False

    def cleanup(self, active):
        '''
        nr_removed = store.cleanup(active)

        Implement 'cleanup' command

        Parameters
        ----------
        active : sequence
            files *not to remove*

        Returns
        -------
        nr_removed : integer
            number of removed files
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
        '''
        lock = store.getlock(name)

        Retrieve a lock object associated with ``name``.

        Parameters
        ----------
        name : str
            Key

        Returns
        -------
        lock : Lock object
            This is a file_lock object
        '''
        return file_based_lock(self.jugdir, name)

    def close(self):
        '''
        store.close()

        Has no effect on file based stores.
        '''
        pass

    @staticmethod
    def remove_store(jugdir):
        '''
        file_store.remove_store(jugdir)

        Removes from disk all the files associated with this jugdir.
        '''
        shutil.rmtree(jugdir)


class file_based_lock(object):
    '''
    file_based_lock: File-system based locks

    Functions:
    ----------

    - get(): acquire the lock
    - release(): release the lock
    - is_locked(): check lock state
    '''

    def __init__(self, jugdir, name):
        self.fullname = path.join(jugdir, 'locks', name + '.lock')

    def get(self):
        '''
        lock.get()

        Create a lock for name in an NFS compatible way.

        Parameters
        ----------
        None

        Returns
        -------
        locked : bool
            Whether the lock was created
        '''
        if exists(self.fullname): return False
        create_directories(path.dirname(self.fullname))
        try:
            import socket
            fd = os.open(self.fullname,os.O_RDWR|os.O_CREAT|os.O_EXCL)
            F = os.fdopen(fd,'w')
            print >>F, '%s on %s' % (os.getpid(), socket.gethostname())
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

