#-*- coding: utf-8 -*-
# Copyright (C) 2009-2022, Luis Pedro Coelho <luis@luispedro.org>
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
dict_store: an in-memory dictionary.

Does not support multiple processes!
'''

import pickle
from collections import defaultdict

from .base import base_store, base_lock

def _gen_key(key, name):
    if type(name) != str:
        name = name.decode('utf-8')
    return '{0}:{1}'.format(key, name).encode('utf-8')

def _resultname(name):
    return _gen_key('result', name)

def _lockname(name):
    return _gen_key('lock', name)



class dict_store(base_store):
    def __init__(self, backend=None):
        '''
        dict_store(backend=None)

        Parameters
        ----------
        backend : str, optional
                  filename to load/save to
        '''
        if backend is not None:
            try:
                self.store = pickle.load(open(backend))
            except IOError:
                self.store = {}
        else:
            self.store = {}
        self.backend = backend
        self.counts = defaultdict(int)

    def dump(self, object, name):
        '''
        self.dump(object, name)
        '''
        self.store[_resultname(name)] = pickle.dumps(object)
        self.counts[_gen_key('dump:',name)] += 1


    def can_load(self, name):
        '''
        can = can_load(name)
        '''
        self.counts[_gen_key('exists', name)] += 1
        return _resultname(name) in self.store


    def load(self, name):
        '''
        obj = load(name)

        Loads the objects. Equivalent to pickle.load(), but a bit smarter at times.
        '''
        self.counts[_gen_key('load',name)] += 1
        return pickle.loads(self.store[_resultname(name)])


    def remove(self, name):
        '''
        was_removed = remove(name)

        Remove the entry associated with name.

        Returns whether any entry was actually removed.
        '''
        self.counts[_gen_key('del',name)] += 1
        if self.can_load(name):
            self.counts[_gen_key('true-del',name)] += 1
            del self.store[_resultname(name)]


    def cleanup(self, active, keeplocks=False):
        '''
        cleanup()

        Implement 'cleanup' command
        '''
        existing = set(self.store.keys())
        for act in active:
            try:
                existing.remove(_resultname(act.hash()))
            except KeyError:
                pass

        if keeplocks:
            for lock in self.listlocks():
                try:
                    existing.remove(_lockname(lock))
                except ValueError:
                    pass

        cleaned = len(existing)
        for superflous in existing:
            del self.store[superflous]

        return cleaned

    def remove_locks(self):
        '''
        removed = store.remove_locks()

        Remove all locks

        Returns
        -------
        removed : int
            Number of locks removed
        '''
        removed = 0
                # we need a copy of the keys because we change it inside
                # iteration:
        for k in list(self.store.keys()):
            if k.startswith(b'lock:'):
                del self.store[k]
                removed += 1
        return removed

    def list(self):
        '''
        for key in store.list():
            ...

        Iterates over all the keys in the store
        '''
        for k in self.store.keys():
            if k.startswith(b'result:'):
                yield k[len('result:'):]

    def listlocks(self):
        '''
        for key in store.listlocks():
            ...

        Iterates over all the keys in the store
        '''
        for k in self.store.keys():
            if k.startswith(b'lock:'):
                yield k[len('lock:'):]


    def getlock(self, name):
        return dict_lock(self.store, self.counts, name)

    def close(self):
        if self.backend is not None:
            pickle.dump(self.store, open(self.backend, 'w'))
            self.backend = None
    __del__ = close


_NOT_LOCKED, _LOCKED, _FAILED = 0,1,2
class dict_lock(base_lock):
    '''
    dict_lock

    Functions:
    ----------

    get()
        acquire the lock
    release()
        release the lock
    is_locked()
        check lock state
    '''

    def __init__(self, store, counts, name):
        self.name = _lockname(name)
        self.store = store
        self.counts = counts

    def get(self):
        '''
        lock.get()
        '''

        self.counts[_lockname(self.name)] += 1

        previous = self.store.get(self.name, _NOT_LOCKED)
        self.store[self.name] = _LOCKED

        if previous == _FAILED:
            self.store[self.name] = _FAILED

        return previous == _NOT_LOCKED

    def release(self):
        '''
        lock.release()

        Removes lock
        '''
        self.counts[_gen_key('unlock', self.name)] += 1
        del self.store[self.name]

    def is_locked(self):
        '''
        locked = lock.is_locked()
        '''
        self.counts[_gen_key('islock', self.name)] += 1
        return (self.store.get(self.name, _NOT_LOCKED) in (_LOCKED, _FAILED))

    def fail(self):
        '''
        lock.fail()

        Mark a task as failed.
        Has no effect if the task isn't locked
        '''
        self.counts[_gen_key('fail', self.name)] += 1

        if self.store.get(self.name, _NOT_LOCKED) == _LOCKED:
            self.store[self.name] = _FAILED

        return self.store[self.name] == _FAILED

    def is_failed(self):
        '''
        failed = lock.is_failed()

        Returns whether this task is marked as failed.
        '''
        self.counts[_gen_key('isfail', self.name)] += 1
        return (self.store.get(self.name, _NOT_LOCKED) == _FAILED)

# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
