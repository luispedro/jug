# -*- coding: utf-8 -*-
# Copyright (C) 2008-2011, Luis Pedro Coelho <luis@luispedro.org>
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
memoize_store: a wrapper that never repeats a lookup.
'''


class memoize_store(object):
    def __init__(self, base, list_base=False):
        '''
        '''
        self.base = base
        self.cache = {}
        self.keys = None
        self.locks = None
        if list_base and hasattr(base, 'list'):
            self.keys = set(base.list())
        if list_base and hasattr(base, 'listlocks'):
            self.locks = set(base.listlocks())

    def dump(self, object, outname):
        '''
        dump(outname, object)
        '''
        raise NotImplementedError


    def can_load(self, name):
        '''
        can = can_load(name)
        '''
        if self.keys is not None:
            return name in self.keys
        if ('can-load', name) not in self.cache:
            self.cache['can-load', name] = self.base.can_load(name)
        return self.cache['can-load',name]


    def load(self, name):
        '''
        obj = load(name)

        Loads the objects. Equivalent to pickle.load(), but a bit smarter at times.
        '''
        raise NotImplementedError


    def remove(self, name):
        '''
        was_removed = remove(name)

        Remove the entry associated with name.

        Returns whether any entry was actually removed.
        '''
        raise NotImplementedError


    def cleanup(self, active):
        '''
        cleanup()

        Implement 'cleanup' command
        '''
        raise NotImplementedError


    def getlock(self, name):
        return cache_lock(self.base, name, self.locks)


    def close(self):
        pass


_UNKNOWN, _NOT_LOCKED, _LOCKED = -1,False,True
class cache_lock(object):
    '''
    cache_lock

    Functions:
    ----------
    get(): acquire the lock
    release(): release the lock
    is_locked(): check lock state
    '''

    def __init__(self, base, name, locks):
        self.base = base.getlock(name)
        self.status = _UNKNOWN
        if locks is not None:
            self.status = (_LOCKED if (name in locks) else _NOT_LOCKED)

    def get(self):
        '''
        lock.get()
        '''
        raise NotImplementedError


    def release(self):
        '''
        lock.release()

        Removes lock
        '''
        raise NotImplementedError

    def is_locked(self):
        '''
        locked = lock.is_locked()
        '''
        if self.status == _UNKNOWN:
            self.status = (_LOCKED if self.base.is_locked() else _NOT_LOCKED)
        return self.status

