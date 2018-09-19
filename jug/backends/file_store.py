# -*- coding: utf-8 -*-
# Copyright (C) 2008-2018, Luis Pedro Coelho <luis@luispedro.org>
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


import os
import sys
from os import path, mkdir
from os.path import dirname, exists
import errno
import logging
import tempfile
import shutil
from subprocess import Popen
from time import time

from .base import base_store, base_lock
from jug.backends.encode import encode_to, decode_from

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
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def fsync_dir(fname):
    import errno
    parent = dirname(fname)
    try:
        fd = os.open(parent, os.O_RDONLY)
    except:
        # It seems that, on Windows and related platforms (cygwin...), you
        # cannot open a directory to get a file descriptor, so the call above
        # raises an error.
        import sys
        if not sys.platform.startswith('linux'):
            return
        else: # On Linux, we still want to check what's wrong
            raise
    try:
        os.fsync(fd)
    except OSError as err:
        if err.errno != errno.EINVAL:
            raise
    finally:
        os.close(fd)


class file_store(base_store):
    def __init__(self, dname, compress_numpy=False):
        '''
        file_store(dname)

        Recursively create directories.
        '''
        if dname.endswith('/'): dname = dname[:-1]
        self.jugdir = dname
        self.compress_numpy = compress_numpy

    def __repr__(self):
        return 'file_store({})'.format(self.jugdir)
    __str__ = __repr__

    def create(self):
        '''
        Recursively create directories.
        '''
        create_directories(self.jugdir)
        create_directories(self.tempdir())

    def _maybe_create(self):
        '''
        Calls self.create() the first time it is called; then becomes a no-op.
        '''
        self.create()
        self._maybe_create = (lambda : None)

    def tempdir(self):
        return path.join(self.jugdir, 'tempfiles')

    def _getfname(self, name):
        import six
        if type(name) != six.text_type:
            name = six.text_type(name, 'utf-8')
        return path.join(self.jugdir, name[:2], name[2:])


    def dump(self, object, name):
        '''
        store.dump(object, name)

        Performs roughly the same as

        pickle.dump(object, open(name,'w'))

        but does it in a way that is guaranteed to be atomic even over NFS and
        using compression on the disk for faster access.
        '''
        self._maybe_create()
        name = self._getfname(name)
        create_directories(dirname(name))
        fd, fname = tempfile.mkstemp('.jugtmp', 'jugtemp', self.tempdir())
        output = os.fdopen(fd, 'wb')
        try:
            import numpy as np
            if not self.compress_numpy and type(object) == np.ndarray:
                np.lib.format.write_array(output, object)
                output.flush()
                os.fsync(output.fileno())
                output.close()
                fsync_dir(fname)
                os.rename(fname, name)
                return
        except ImportError:
            pass
        except OSError:
            pass
        except ValueError:
            pass

        encode_to(object, output)
        output.flush()
        os.fsync(output.fileno())
        output.close()

        # Rename is atomic even over NFS.
        fsync_dir(fname)
        os.rename(fname, name)

    def list(self):
        '''
        keys = store.list()

        Returns a list of all the keys in the store
        '''
        if not exists(self.jugdir):
            return []

        keys = []
        for d in os.listdir(self.jugdir):
            if len(d) == 2:
                for f in os.listdir(path.join(self.jugdir, d)):
                    keys.append((d+f).encode('ascii'))
        return keys


    def listlocks(self):
        '''
        keys = store.listlocks()

        Returns a list of all the locks in the store

        This is an unsafe function as the results may be outdated by the time
        the function returns.
        '''
        if not exists(path.join(self.jugdir, 'locks')):
            return []

        keys = []
        for k in os.listdir(path.join(self.jugdir, 'locks')):
            keys.append(k[:-len('.lock')].encode('ascii'))
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
        with open(fname, 'rb') as ifile:
            try:
                import numpy as np
                return np.lib.format.read_array(ifile)
            except ValueError:
                ifile.seek(0)
            except ImportError:
                pass
            return decode_from(ifile)

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

    def cleanup(self, active, keeplocks=False):
        '''
        nr_removed = store.cleanup(active, keeplocks)

        Implement 'cleanup' command

        Parameters
        ----------
        active : sequence
            files *not to remove*
        keeplocks : boolean
            whether to preserve or remove locks

        Returns
        -------
        nr_removed : integer
            number of removed files
        '''
        active = frozenset(self._getfname(t.hash()) for t in active)
        removed = 0
        for dir,_,fs in os.walk(self.jugdir):
            if keeplocks and dir == "locks":
                continue
            for f in fs:
                f = path.join(dir, f)
                if f not in active:
                    os.unlink(f)
                    removed += 1
        return removed

    def remove_locks(self):
        '''
        removed = store.remove_locks()

        Remove all locks

        Returns
        -------
        removed : int
            Number of locks removed
        '''

        lockdir = path.join(self.jugdir, 'locks')
        if not exists(lockdir): return 0

        removed = 0
        for f in os.listdir(lockdir):
            os.unlink(path.join(lockdir, f))
            removed += 1
        return removed

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

    def metadata(self, t):
        '''
        meta = store.metadata(t)

        Retrieves information on the state of the computation

        Parameters
        ----------
        t : Task
            A Task object

        Returns
        -------
        meta : dict
            Dictionary describing the state of the computation
        '''
        from os import stat, path
        from time import ctime
        fname = self._getfname(t.hash())
        if path.exists(fname):
            st = stat(fname)
            return {
                'computed': True,
                'completed': ctime(st.st_mtime),
            }
        return {
                'computed': False
        }


    @staticmethod
    def remove_store(jugdir):
        '''
        file_store.remove_store(jugdir)

        Removes from disk all the files associated with this jugdir.
        '''
        if path.exists(jugdir):
            shutil.rmtree(jugdir)


class file_based_lock(base_lock):
    '''
    file_based_lock: File-system based locks

    Functions:
    ----------

    - get(): acquire the lock
    - release(): release the lock
    - is_locked(): check lock state
    '''
    # We use epoch + 1 second to mark a task as failed
    # More at https://github.com/luispedro/jug/issues/55
    _FAILED_TIMESTAMP = (1, 1)  # atime, mtime

    def __init__(self, jugdir, name):
        import six
        if type(name) != six.text_type:
            name = six.text_type(name, 'utf-8')
        self.fullname = path.join(jugdir, 'locks', '{0}.lock'.format(name))

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
            from datetime import datetime
            fd = os.open(self.fullname, os.O_RDWR|os.O_CREAT|os.O_EXCL)
            F = os.fdopen(fd, 'w')
            F.write('PID {0} on HOSTNAME {1}\n'.format(os.getpid(), socket.gethostname()))
            F.write('Lock created on {0}\n'.format(datetime.now().strftime('%Y-%m-%d (%Hh%M.%S)')))
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

    def fail(self):
        '''
        lock.fail()

        Mark a task as failed.
        Has no effect if the task isn't locked
        '''
        try:
            os.utime(self.fullname, self._FAILED_TIMESTAMP)
        except OSError:
            return False
        else:
            return True

    def is_failed(self):
        '''
        failed = lock.is_failed()

        Returns whether this task is marked as failed.

        This code is not race-condition free. It may happen that by the time
        this function returns, the failed lock has been released.
        '''
        if self.is_locked():
            try:
                t = os.stat(self.fullname)
            except OSError:
                pass
            else:
                if t.st_mtime == self._FAILED_TIMESTAMP[0]:
                    return True

        return False


class file_keepalive_store(file_store):
    def __repr__(self):
        return 'file_keepalive_store({})'.format(self.jugdir)
    __str__ = __repr__

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
        return file_keepalive_based_lock(self.jugdir, name)


class file_keepalive_based_lock(file_based_lock):
    '''
    file_keepalive_based_lock: File-system based locks

    Works much like file_based_lock but implements a mechanism to keep locks
    alive during execution, making it possible to recognize crashed/killed jobs
    as failed.

    Functions:
    ----------

    - get(): acquire the lock
    - release(): release the lock
    - is_locked(): check lock state
    '''
    def __init__(self, *args, **kwargs):
        self.monitor = None
        super(file_keepalive_based_lock, self).__init__(*args, **kwargs)

    def start_monitor(self):
        """Start side-kick process that ensures locks are refreshed while
        main process is active on this task
        """
        # No need to be gentle. Killing it straight away is safe.
        self.monitor = Popen([sys.executable, "-m", "jug.backends.file_keepalive_monitor", self.fullname])

    def stop_monitor(self):
        """Stop side-kick process that ensures locks are refreshed while
        main process is active on this lock
        """
        if self.monitor is None:
            return

        try:
            self.monitor.kill()
        except OSError as e:
            logging.warning('keepalive process failed to die with %s' % e)

        # subprocess module implements a cleanup mechanism that kicks in when
        # a Popen instance is deleted. This prevents leaking subprocesses and
        # avoids having to explicitly block and .wait() for a task to finish
        del self.monitor
        self.monitor = None

    def get(self):
        '''
        lock.get()

        Create a lock for name in an NFS compatible way.
        And start a lock monitor job

        Parameters
        ----------
        None

        Returns
        -------
        locked : bool
            Whether the lock was created
        '''
        acquired = super(file_keepalive_based_lock, self).get()

        if acquired:
            self.start_monitor()

        return acquired

    def release(self):
        '''
        lock.release()

        Removes lock
        And stops lock monitor job
        '''
        self.stop_monitor()
        return super(file_keepalive_based_lock, self).release()

    def fail(self):
        '''
        lock.fail()

        Mark a task as failed.
        Has no effect if the task isn't locked other than stopping the monitoring
        process if it exists
        '''
        self.stop_monitor()
        return super(file_keepalive_based_lock, self).fail()

    def is_failed(self):
        '''
        failed = lock.is_failed()

        Returns whether this task has a lock in failed state.

        A lock in failed state is one that exists and was last modified more
        than 30 minutes ago.

        This code is not race-condition free. It may happen that by the time
        this function returns, the failed lock has been released.
        '''
        failed_lock = time() - (30 * 60)  # 30 minutes old lock is a dead lock

        if self.is_locked():
            try:
                t = os.stat(self.fullname)
            except OSError:
                pass
            else:
                if t.st_mtime <= failed_lock:
                    return True

        return False
