# Copyright (C) 2008-2026, Luis Pedro Coelho <luis@luispedro.org>
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
from os import path
from os.path import dirname, exists
import logging
import shutil
from contextlib import suppress
from subprocess import Popen
from time import time

from .base import base_store, base_lock
from jug.backends.encode import encode_to, decode_from

MAX_FILESIZE_IN_PACK = 512


def fsync_dir(fname):
    import errno
    parent = dirname(fname)
    try:
        fd = os.open(parent, os.O_RDONLY)
    except OSError:
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


def _write_to(value, output, compress_numpy):
    start = output.tell()
    def rewind():
        # Writing in a native format may have failed after part of the output
        # was written, which must be discarded before falling back to
        # encode_to (or the file could not be loaded)
        output.seek(start)
        output.truncate()
    try:
        import numpy as np
        if not compress_numpy and type(value) is np.ndarray and not value.dtype.hasobject:
            np.lib.format.write_array(output, value)
            return
    except ImportError:
        pass
    except (OSError, ValueError):
        rewind()
    try:
        import polars as pl
        if not compress_numpy and type(value) is pl.DataFrame:
            value.write_parquet(output)
            return
    except ImportError:
        pass
    except (OSError, ValueError):
        rewind()

    encode_to(value, output)


def _make_temp_file(tempdir):
    '''Create temporary file in tempdir

    This is better than using tempfile.mkstemp because that function creates files
    with mode 0600, which is not always the right thing to do. This function
    results in the same permissions as the regular open() function.

    Parameters
    ----------
    tempdir : str
        Directory where to create the temporary

    Returns
    -------
    fname : str
        Filename
    output : file
    '''
    import random
    import string
    # random.choices is not cryptographic, which is fine: the name only needs
    # to avoid collisions. With 52**24 possibilities, a collision is
    # practically impossible, but the exclusive-create ('x') open plus retry
    # loop guarantees we never overwrite an existing file.
    while True:
        fname = path.join(tempdir,
                    ''.join(random.choices(string.ascii_letters, k=24)))
        try:
            return fname, open(fname, 'bx')
        except FileExistsError:
            pass


class file_store(base_store):
    def __init__(self, dname, compress_numpy=False):
        '''
        file_store(dname, compress_numpy=False)

        Initialise a file-based store. Directories are not created here, but
        only when needed (see ``create()``).

        Parameters
        ----------
        dname : str
            Directory to use (the jugdir)
        compress_numpy : boolean, optional
            If true, numpy arrays and polars DataFrames are stored compressed
            (like any other object) instead of in their native formats
            (``.npy`` and parquet, respectively). Default: False
        '''
        if dname.endswith('/'): dname = dname[:-1]
        self.jugdir = dname
        self.compress_numpy = compress_numpy
        self.packed = self._read_pack()

    def _packfile(self):
        return path.join(self.jugdir, 'packs', 'jugpack')

    def _read_pack(self):
        if not path.exists(self._packfile()):
            return {}
        with open(self._packfile(), 'rb') as pfile:
            sys.path.insert(0, '.')
            try:
                return decode_from(pfile)
            finally:
                del sys.path[0]

    def __repr__(self):
        return f'file_store({self.jugdir})'
    __str__ = __repr__

    def create(self):
        '''
        Recursively create directories.
        '''
        os.makedirs(self.jugdir, exist_ok=True)
        os.makedirs(self.tempdir(), exist_ok=True)

    def _maybe_create(self):
        '''
        Calls self.create() the first time it is called; then becomes a no-op.
        '''
        self.create()
        self._maybe_create = (lambda : None)

    def tempdir(self):
        return path.join(self.jugdir, 'tempfiles')

    def _getfname(self, name):
        if not isinstance(name, str):
            name = name.decode('utf-8')
        return path.join(self.jugdir, name[:2], name[2:])

    def dump(self, value, name):
        '''
        store.dump(value, name)

        Performs roughly the same as

        pickle.dump(value, open(name,'wb'))

        but does it in a way that is guaranteed to be atomic even over NFS and
        using compression on the disk for faster access. Numpy arrays and
        polars DataFrames are stored in their native formats (``.npy`` and
        parquet), unless ``compress_numpy`` was set.
        '''
        self._remove_from_pack([name])

        self._maybe_create()
        name = self._getfname(name)
        os.makedirs(dirname(name), exist_ok=True)
        fname, output = _make_temp_file(self.tempdir())
        try:
            _write_to(value, output, self.compress_numpy)
            output.flush()
            os.fsync(output.fileno())
        except:
            output.close()
            with suppress(OSError):
                os.unlink(fname)
            raise
        output.close()

        # Rename is atomic even over NFS.
        os.rename(fname, name)
        fsync_dir(name)

    def _iter_filekeys(self):
        '''
        for f in store._iter_filekeys():
            ...

        Internal. Use `self.list()`

        '''
        if not exists(self.jugdir):
            return

        for d in sorted(os.listdir(self.jugdir)):
            if len(d) == 2:
                for f in sorted(os.listdir(path.join(self.jugdir, d))):
                    yield (d+f).encode('ascii')

    def list(self):
        '''
        keys = store.list()

        Returns a list of all the keys in the store
        '''
        return list(self.packed.keys()) + list(self._iter_filekeys())

    def update_pack(self):
        '''
        nr_packed = store.update_pack()

        Moves all result files of at most ``MAX_FILESIZE_IN_PACK`` bytes into
        the pack file (which backs ``jug pack``).

        Note that the whole pack is loaded into memory by every process that
        opens the store.

        Returns
        -------
        nr_packed : int
            Number of results that were moved into the pack
        '''
        to_pack = {}
        for k in self._iter_filekeys():
            f = self._getfname(k)
            # Another process (e.g., ``jug invalidate``) may remove the file
            # concurrently, in which case there is nothing to pack
            try:
                s = os.stat(f)
                if s.st_size <= MAX_FILESIZE_IN_PACK:
                    # Use _load_file() rather than decode_from() as the file
                    # may be in a native format (npy or parquet), and rather
                    # than load() so that a stale packed value does not
                    # overwrite the file we are about to remove
                    to_pack[k] = self._load_file(k)
            except FileNotFoundError:
                pass
        if to_pack:
            def add(packed):
                packed.update(to_pack)
                return True
            self._modify_pack(add)
        for k in to_pack:
            with suppress(FileNotFoundError):
                os.unlink(self._getfname(k))
        return len(to_pack)


    def _get_pack_lock(self):
        lock = self.getlock('pack-save')
        for i in range(10):
            if lock.get():
                return lock
            from time import sleep
            logging.warning("Waiting for lock file 'pack-save'")
            sleep(2**i)
        raise Exception('Could not obtain lock to save packed data')

    def _write_pack(self, packed):
        os.makedirs(path.join(self.jugdir, 'packs'), exist_ok=True)
        self._maybe_create()
        # Not tempfile.mkstemp (see _make_temp_file): the pack must have the
        # same permissions as the result files it replaces
        fname, output = _make_temp_file(self.tempdir())
        try:
            with output:
                encode_to(packed, output)
                output.flush()
                os.fsync(output.fileno())
            # Rename is atomic even over NFS.
            os.rename(fname, self._packfile())
            fsync_dir(self._packfile())
        except:
            with suppress(OSError):
                os.unlink(fname)
            raise

    def _modify_pack(self, modify):
        '''
        store._modify_pack(modify)

        Re-reads the pack from disk while holding the 'pack-save' lock (so
        that changes made by other processes are not lost), calls
        ``modify(packed)`` on it, and saves it if ``modify`` returns true.
        '''
        lock = self._get_pack_lock()
        try:
            packed = self._read_pack()
            if modify(packed):
                self._write_pack(packed)
            self.packed = packed
        finally:
            lock.release()

    def _remove_from_pack(self, names):
        '''
        removed = store._remove_from_pack(names)

        Removes ``names`` from the pack, only touching the pack file if any of
        them is in it.
        '''
        removed = set()
        if not any(name in self.packed for name in names):
            return removed
        def remove(packed):
            for name in names:
                if name in packed:
                    del packed[name]
                    removed.add(name)
            return bool(removed)
        self._modify_pack(remove)
        return removed

    def resave_pack(self):
        '''
        store.resave_pack()

        Writes the in-memory pack to disk (atomically, holding a lock)

        WARNING: This is not used by jug itself and is only kept for
        backwards compatibility. The in-memory pack may be stale (it is read
        when the store is opened), so this can undo changes made to the pack
        by other processes since then (e.g., bring back invalidated results).
        '''
        lock = self._get_pack_lock()
        try:
            self._write_pack(self.packed)
        finally:
            lock.release()


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
        return name in self.packed or exists(fname)


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
        if name in self.packed:
            return self.packed[name]
        return self._load_file(name)

    def _load_file(self, name):
        '''
        obj = store._load_file(name)

        Internal. Loads the result *file* for ``name``, ignoring the pack.

        Use ``self.load()`` instead, unless the file is specifically what is
        wanted: a key can be both in the pack and on disk (the pack is only
        read when the store is opened, so another process may have written a
        file for a key which this process still sees in its pack), and in
        that case the file is the newer value.
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
            if ifile.peek(4)[:4] == b'PAR1':
                try:
                    import polars as pl
                    return pl.read_parquet(ifile)
                except ImportError:
                    pass
                except Exception:
                    ifile.seek(0)
            return decode_from(ifile)


    def remove_many(self, names):
        '''
        removed = store.remove_many(names)

        Removes the objects with the given names from the store.

        Returns
        -------
        removed : set
            Names that were actually removed
        '''
        names = list(names)
        removed = self._remove_from_pack(names)
        for name in names:
            with suppress(OSError):
                os.unlink(self._getfname(name))
                removed.add(name)
        return removed

    def remove(self, name):
        '''
        was_removed = store.remove(name)

        Remove the entry associated with name.

        Returns whether any entry was actually removed.
        '''
        return bool(self.remove_many([name]))


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
            number of removed result objects (removed locks are *not*
            included in this count; see ``remove_locks()``)
        '''
        active = frozenset(t.hash() for t in active)
        active_fnames = frozenset(self._getfname(h) for h in active)
        removed = 0
        for dirpath,_,fs in os.walk(self.jugdir):
            is_lockdir = (path.basename(dirpath) == "locks")
            if keeplocks and is_lockdir:
                continue
            if path.basename(dirpath) == "packs":
                continue
            if path.basename(dirpath) == "tempfiles":
                continue
            for f in fs:
                f = path.join(dirpath, f)
                if f not in active_fnames:
                    os.unlink(f)
                    if not is_lockdir:
                        removed += 1
        if exists(self._packfile()):
            nr_unpacked = 0
            def remove_inactive(packed):
                nonlocal nr_unpacked
                inactive = frozenset(packed.keys()) - active
                for k in inactive:
                    del packed[k]
                nr_unpacked = len(inactive)
                return bool(inactive)
            self._modify_pack(remove_inactive)
            removed += nr_unpacked
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
            This is a file_based_lock object
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
        name = t.hash()
        fname = self._getfname(name)
        if path.exists(fname):
            st = stat(fname)
            return {
                'computed': True,
                'completed': ctime(st.st_mtime),
            }
        if name in self.packed:
            return {
                'computed': True,
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

    Methods:

    - get(): acquire the lock
    - release(): release the lock
    - is_locked(): check lock state
    - fail(): mark task as failed
    - is_failed(): check if task is failed
    '''
    # We use epoch + 1 second to mark a task as failed
    # More at https://github.com/luispedro/jug/issues/55
    _FAILED_TIMESTAMP = (1, 1)  # atime, mtime

    def __init__(self, jugdir, name):
        if not isinstance(name, str):
            name = str(name, 'utf-8')
        self.fullname = path.join(jugdir, 'locks', f'{name}.lock')

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
        os.makedirs(path.dirname(self.fullname), exist_ok=True)
        try:
            import socket
            from datetime import datetime
            fd = os.open(self.fullname, os.O_RDWR|os.O_CREAT|os.O_EXCL)
            F = os.fdopen(fd, 'w')
            F.write(f'PID {os.getpid()} on HOSTNAME {socket.gethostname()}\n')
            F.write(f"Lock created on {datetime.now().strftime('%Y-%m-%d (%Hh%M.%S)')}\n")
            F.close()
            return True
        except FileExistsError:
            return False

    def release(self):
        '''
        lock.release()

        Removes lock
        '''
        with suppress(OSError):
            os.unlink(self.fullname)

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
                if t.st_mtime == self._FAILED_TIMESTAMP[1]:
                    return True

        return False


class file_keepalive_store(file_store):
    def __repr__(self):
        return f'file_keepalive_store({self.jugdir})'
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
            This is a file_keepalive_based_lock object
        '''
        return file_keepalive_based_lock(self.jugdir, name)


class file_keepalive_based_lock(file_based_lock):
    '''
    file_keepalive_based_lock: File-system based locks

    Works much like file_based_lock but implements a mechanism to keep locks
    alive during execution, making it possible to recognize crashed/killed jobs
    as failed.

    Methods:

    - get(): acquire the lock
    - release(): release the lock
    - is_locked(): check lock state
    - fail(): mark task as failed
    - is_failed(): check if task is failed
    '''
    def __init__(self, *args, **kwargs):
        self.monitor = None
        super().__init__(*args, **kwargs)

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
            logging.warning(f'keepalive process failed to die with {e}')

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
        acquired = super().get()

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
        return super().release()

    def fail(self):
        '''
        lock.fail()

        Mark a task as failed.
        Has no effect if the task isn't locked other than stopping the monitoring
        process if it exists
        '''
        self.stop_monitor()
        return super().fail()

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
