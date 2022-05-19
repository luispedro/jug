#-*- coding: utf-8 -*-
# Copyright (C) 2009-2022, Luis Pedro Coelho <luis@luispedro.org>
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
redis_store: store based on a redis backend
'''


import re
import logging
from base64 import b64encode, b64decode
from jug.backends.encode import encode, decode
from .base import base_store, base_lock


try:
    import redis
    redis_functional = True
except ImportError:
    redis_functional = False

def _resultname(name):
    if type(name) == str:
        name = name.encode('utf-8')
    return b'result:' + name

def _lockname(name):
    if type(name) == str:
        name = name.encode('utf-8')
    return b'lock:' + name

_LOCKED = b'L'
_FAILED = b'F'

_redis_urlpat = re.compile(r'redis://(?P<host>[A-Za-z0-9\.\-]+)(\:(?P<port>[0-9]+))?/?')


class redis_store(base_store):
    def __init__(self, url):
        '''
        '''
        if not redis_functional:
            raise IOError('jug.redis_store: redis module is not found!')
        redis_params = {}
        match = _redis_urlpat.match(url)
        if match:
            redis_params = match.groupdict()
            if redis_params['port'] == None:
                del redis_params['port']
            else:
                redis_params['port'] = int( redis_params['port'] )
        logging.info('connecting to %s' % redis_params)

        self.redis = redis.Redis(**redis_params)


    def dump(self, object, name):
        '''
        dump(object, name)
        '''
        s = encode(object)
        if s:
            s = b64encode(s)
        self.redis.set(_resultname(name), s)


    def can_load(self, name):
        '''
        can = can_load(name)
        '''
        return self.redis.exists(_resultname(name))


    def load(self, name):
        '''
        obj = load(name)

        Loads the object identified by `name`.
        '''
        s = self.redis.get(_resultname(name))
        if s:
            s = b64decode(s)
        return decode(s)


    def remove(self, name):
        '''
        was_removed = remove(name)

        Remove the entry associated with name.

        Returns whether any entry was actually removed.
        '''
        return self.redis.delete(_resultname(name))


    def cleanup(self, active, keeplocks=False):
        '''
        cleanup()

        Implement 'cleanup' command
        '''


        existing = set(self.list())
        existing -= set(act.hash() for act in active)

        cleaned = len(existing)
        for superflous in existing:
            self.redis.delete(_resultname(superflous))

        if not keeplocks:
            cleaned += self.remove_locks()

        return cleaned

    def remove_locks(self):
        locks = self.redis.keys('lock:*')
        for lk in locks:
            self.redis.delete(lk)
        return len(locks)

    def list(self):
        existing = self.redis.keys('result:*')
        for ex in existing:
            yield ex[len('result:'):]

    def listlocks(self):
        locks = self.redis.keys('lock:*')
        for lk in locks:
            yield lk[len('lock:'):]


    def getlock(self, name):
        return redis_lock(self.redis, name)


    def close(self):
        # It seems some versions of the protocol are implemented differently
        # and do not have the ``disconnect`` method
        try:
            self.redis.disconnect()
        except:
            pass



class redis_lock(base_lock):
    '''
    redis_lock

    Functions:
    ----------

    - get(): acquire the lock
    - release(): release the lock
    - is_locked(): check lock state
    '''

    def __init__(self, redis, name):
        self.name = _lockname(name)
        self.redis = redis


    def get(self):
        '''
        lock.get()
        '''
        # We need getset to be race-free
        previous = self.redis.getset(self.name, _LOCKED)

        if previous == _FAILED:
            self.redis.set(self.name, previous)

        return (previous is None)


    def release(self):
        '''
        lock.release()

        Removes lock
        '''
        self.redis.delete(self.name)


    def is_locked(self):
        '''
        locked = lock.is_locked()
        '''
        status = self.redis.get(self.name)
        return status is not None and status in (_LOCKED, _FAILED)


    def fail(self):
        '''
        lock.fail()

        Mark a task as failed.
        Has no effect if the task isn't locked

        Since we have to check the state of the lock before failing this
        call is not atomic nor race-free.
        '''
        status = self.redis.get(self.name)
        if status == _LOCKED:
            self.redis.set(self.name, _FAILED)
            return True
        elif status == _FAILED:
            return True
        else:
            return False


    def is_failed(self):
        '''
        failed = lock.is_failed()

        Returns whether this task is marked as failed.
        '''
        status = self.redis.get(self.name)
        return status is not None and status == _FAILED
