#-*- coding: utf-8 -*-
# Copyright (C) 2009-2010, Luis Pedro Coelho <lpc@cmu.edu>
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
from __future__ import division
import cPickle as pickle
from collections import defaultdict

def _resultname(name):
    return 'result:' + name

def _lockname(name):
    return 'lock:' + name


class dict_store(object):
    def __init__(self):
        '''
        '''
        self.store = {}
        self.counts = defaultdict(int)

    def dump(self, object, name):
        '''
        self.dump(object, name)
        '''
        self.store[_resultname(name)] = pickle.dumps(object)
        self.counts['dump:' + name] += 1


    def can_load(self, name):
        '''
        can = can_load(name)
        '''
        self.counts['exists:' + name] += 1
        return _resultname(name) in self.store


    def load(self, name):
        '''
        obj = load(name)

        Loads the objects. Equivalent to pickle.load(), but a bit smarter at times.
        '''
        self.counts['load:' + name] += 1
        return pickle.loads(self.store[_resultname(name)])


    def remove(self, name):
        '''
        was_removed = remove(name)

        Remove the entry associated with name.

        Returns whether any entry was actually removed.
        '''
        self.counts['del:' + name] += 1
        if self.can_load(name):
            self.counts['true-del:' + name] += 1
            del self.store[_resultname(name)]


    def cleanup(self, active):
        '''
        cleanup()

        Implement 'cleanup' command
        '''
        existing = self.store.keys()
        for act in active:
            try:
                existing.remove(_resultname(act))
            except KeyError:
                pass
        for superflous in existing:
            del self.store[_resultname(superflous)]


    def getlock(self, name):
        return dict_lock(self.store, self.counts, name)


    def close(self):
        pass


_NOT_LOCKED, _LOCKED = 0,1
class dict_lock(object):
    '''
    dict_lock

    Functions:
    ----------

        * get(): acquire the lock
        * release(): release the lock
        * is_locked(): check lock state
    '''

    def __init__(self, store, counts, name):
        self.name = _lockname(name)
        self.store = store
        self.counts = counts

    def get(self):
        '''
        lock.get()
        '''

        self.counts['lock:' + self.name] += 1

        previous = self.store.get(self.name, _NOT_LOCKED)
        self.store[self.name] = _LOCKED
        return previous == _NOT_LOCKED


    def release(self):
        '''
        lock.release()

        Removes lock
        '''
        self.counts['unlock:' + self.name] += 1
        del self.store[self.name]

    def is_locked(self):
        '''
        locked = lock.is_locked()
        '''
        self.counts['islock:' + self.name] += 1
        return (self.store.get(self.name, _NOT_LOCKED) == _LOCKED)

# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
