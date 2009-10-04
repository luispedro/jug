# -*- coding: utf-8 -*-
# Copyright (C) 2008, Luís Pedro Coelho <lpc@cmu.edu>
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
Lock: File-system based locks

Functions:
----------

    * get(): acquire the lock
    * release(): release the lock
    * is_locked(): check lock state
'''

from __future__ import division
import options
import os
from os import path
from os.path import exists
from store import create_directories
import tempfile

def _fullname(name):
    return path.join(options.lockdir,name+'.lock')

def get(name):
    '''
    get(name)

    Create a lock for name in an NFS compatible way.
    '''
    fullname = _fullname(name)
    if exists(fullname): return False
    create_directories(path.dirname(fullname))
    try:
        fd = os.open(fullname,os.O_RDWR|os.O_CREAT|os.O_EXCL)
        F = os.fdopen(fd,'w')
        print >>F, 'Lock', os.getpid()
        F.close()
        return True
    except OSError:
        return False

def release(name):
    '''
    release(name)

    Removes lock
    '''
    try:
        os.unlink(_fullname(name))
    except OSError:
        pass

def is_locked(name):
    '''
    locked = is_locked(name)

    Returns whether a lock exists for name. Note that the answer can
    be invalid by the time this function returns. Only by trying to
    acquire the lock can you avoid race-conditions. See the get() function.
    '''
    return path.exists(_fullname(name))
# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
