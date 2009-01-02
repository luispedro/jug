# -*- coding: utf-8 -*-
# Copyright (C) 2008  Murphy Lab
# Carnegie Mellon University
# 
# Written by Luís Pedro Coelho <lpc@cmu.edu>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; either version 3 of the License,
# or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#
# For additional information visit http://murphylab.web.cmu.edu or
# send email to murphy@cmu.edu
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
    return path.join(options.lockdir,name[0],name[1],name[2:]+'.lock')

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
    os.unlink(_fullname(name))

def is_locked(name):
    '''
    locked = is_locked(name)

    Returns whether a lock exists for name. Note that the answer can
    be invalid by the time this function returns. Only by trying to
    acquire the lock can you avoid race-conditions. See the get() function.
    '''
    return path.exists(_fullname(name))

# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
