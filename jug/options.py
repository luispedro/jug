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
Options

Variables
---------

    * jugdir: main jug directory.
    * tempdir: directory for temporary files.
    * lockdir: directory for lock files.
    * jugfile: filesystem name for the Jugfile
    * cmd: command to run.
    * shuffle: --shuffle argument (None if not set)
'''

from __future__ import division

jugdir = 'jugdata'
tempdir = jugdir + '/tempfiles/'
lockdir = jugdir + '/locks/'
jugfile = 'jugfile.py'
cmd = None
shuffle = None

_Commands = ('execute','status','stats','cleanup','count')
_Usage_string = \
'''python %s COMMAND OPTIONS...

Possible commands:
* execute
    Execute tasks
* status:
    Print status
* counts:
    Simply count tasks
* cleanup:
    Cleanup [Not implemented]
* stats
    Print statistics [Not implemented]

Options
--shuffle[=N]
    Shuffle the task order using N as the seed (default: 0)
'''

def usage():
    '''
    usage()

    Print an usage string and exit.
    '''
    import sys
    print _Usage_string % sys.argv[0]
    sys.exit(1)

def parse():
    '''
    options.parse()

    Parse the command line options and set the option variables.
    '''
    import optparse
    global cmd, shuffle
    parser = optparse.OptionParser()
    parser.add_option('--shuffle',action='store',type='int',dest='shuffle',default=False)
    options,args = parser.parse_args()
    if not args:
        usage()
        return
    cmd = args[0]
    if cmd not in _Commands:
        usage()
        return

    if options.shuffle is not False:
        import random
        random.seed(options.shuffle)
        shuffle = options.shuffle



# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
