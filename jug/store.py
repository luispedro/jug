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
Store: handle the file-system based backstore.
'''
from __future__ import division

import pickle
import os
from os import path, mkdir, fdopen
from os.path import dirname
import tempfile
import options

def create_directories(dname):
    '''
    create_directories(dname)

    Recursively create directories.
    '''
    if dname.endswith('/'): dname = dname[:-1]
    head, tail = path.split(dname)
    if head: create_directories(head)
    try:
        mkdir(dname)
    except OSError:
        pass

def atomic_pickle_dump(object, outname):
    '''
    atomic_pickle_dump(outname, object)

    Performs the same as

    pickle.dump(object, file(outname,'w')

    but does it in a way that is guaranteed to be atomic even over NFS.
    '''
    # Rename is atomic in NFS, but we need to create the temporary file in
    # the same directory as the result.
    #
    # Don't mess unless you know what you are doing!
    fd, fname = tempfile.mkstemp('.pp','jugtemp',options.tempdir)
    F = fdopen(fd,'w')
    pickle.dump(object,F)
    F.close()
    create_directories(dirname(outname))
    os.rename(fname,outname)

def obj2fname(obj):
    '''
    fname = obj2fname(obj)

    Returns the filename used to save the object obj
    '''
    M = md5.md5()
    S = pickle.dumps(func,args)
    M.update(S)
    D = M.hexdigest()
    return D[0] + '/' + D[1] + '/' + D[2:] + '.pp'

# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
