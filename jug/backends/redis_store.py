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
redis_store: store based on a redis backend
'''
from __future__ import division

import re
import cPickle as pickle
import logging
from zlib import compress, decompress
from base64 import b64encode, b64decode

try:
    import redis
except ImportError:
    try:
        from ..thirdparty import redis
    except ImportError:
        redis = None

def _resultname(name):
    return 'result:' + name

def _lockname(name):
    return 'lock:' + name

_LOCKED = 1

_redis_urlpat = re.compile('redis://(?P<host>[A-Za-z0-9\.]+)(?P<port>\:[0-9]+)?/')


class redis_store(object):
    def __init__(self, url):
        '''
        '''
        if redis is None:
            raise IOError, 'jug.redis_store: redis module is not found!'
        redis_params = {}
        match = _redis_urlpat.match(url)
        if match:
            redis_params = match.groupdict()
        logging.info('connecting to %s' % redis_params)
        self.redis = redis.Redis(**redis_params)


    def dump(self, object, name):
        '''
        dump(object, name)
        '''
        if object is None:
            s = ''
        else:
            s = pickle.dumps(object)
            s = compress(s)
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

        Loads the objects. Equivalent to pickle.load(), but a bit smarter at times.
        '''
        s = self.redis.get(_resultname(name))
        if s:
            s = str(s)
            s = b64decode(s)
            s = decompress(s)
            return pickle.loads(s)
        else:
            return None


    def remove(self, name):
        '''
        was_removed = remove(name)

        Remove the entry associated with name.

        Returns whether any entry was actually removed.
        '''
        return self.redis.delete(_resultname(name))


    def cleanup(self, active):
        '''
        cleanup()

        Implement 'cleanup' command
        '''
        existing = self.redis.keys('result:*')
        for act in active:
            try:
                existing.remove(_resultname(act))
            except KeyError:
                pass
        for superflous in existing:
            self.redis.delete(_resultname(superflous))


    def getlock(self, name):
        return redis_lock(self.redis, name)


    def close(self):
        self.redis.disconnect()



class redis_lock(object):
    '''
    redis_lock

    Functions:
    ----------

        * get(): acquire the lock
        * release(): release the lock
        * is_locked(): check lock state
    '''

    def __init__(self, redis, name):
        self.name = _lockname(name)
        self.redis = redis

    def get(self):
        '''
        lock.get()
        '''
        previous = self.redis.getset(self.name, _LOCKED)
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
        return status is not None and status == _LOCKED

# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
