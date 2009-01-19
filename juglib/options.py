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
Options

Variables
---------

    * jugdir: main jug directory.
    * tempdir: directory for temporary files.
    * lockdir: directory for lock files.
    * jugfile: filesystem name for the Jugfile
    * cmd: command to run.
    * shuffle: --shuffle argument (None if not set)
    * aggressive_unload: --aggressive-unload
    * invalid_name: --invalid
'''
from __future__ import division

jugdir = 'jugdata'
tempdir = jugdir + '/tempfiles/'
lockdir = jugdir + '/locks/'
jugfile = 'jugfile.py'
cmd = None
shuffle = None
aggressive_unload = False
invalid_name = None

_Commands = ('execute','status','stats','cleanup','count','invalidate')
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
* invalidate
    Invalidate the results of a task

Options:
--shuffle[=N]
    Shuffle the task order using N as the seed (default: 0)
--jugfile=JUGFILE
    Name of the jugfile to use (if not given, use jugfile.py)
--aggressive-unload
    Aggressively unload data from memory
--invalid=TASK-NAME
    Task name to invalidate (for invalidate command only)
'''

def usage():
    '''
    usage()

    Print an usage string and exit.
    '''
    import sys
    print _Usage_string % sys.argv[0]
    sys.exit(1)

def find_jugfile(options):
    '''
    jugfile = find_jugfile(options)

    Returns the filename of the Jugfile or None if it is not found.
    '''
    if options.jugfile:
        return options.jugfile
    return 'jugfile.py'

def parse():
    '''
    options.parse()

    Parse the command line options and set the option variables.
    '''
    import optparse
    global cmd, shuffle, jugfile, aggressive_unload, invalid_name
    parser = optparse.OptionParser()
    parser.add_option('--shuffle',action='store',type='int',dest='shuffle',default=False)
    parser.add_option('--jugfile',action='store',type='string',dest='jugfile',default=None)
    parser.add_option('--aggressive-unload',action='store_true',dest='aggressive_unload',default=False)
    parser.add_option('--invalid',action='store',dest='invalid_name',default=None)
    options,args = parser.parse_args()
    if not args:
        usage()
        return
    cmd = args[0]
    if cmd not in _Commands:
        usage()
        return
    if options.invalid_name and cmd != 'invalidate':
        usage()
        return
    if cmd == 'invalidate' and not options.invalid_name:
        usage()
        return

    if options.shuffle is not False:
        import random
        random.seed(options.shuffle)
        shuffle = options.shuffle

    aggressive_unload = options.aggressive_unload
    jugfile = find_jugfile(options)
    invalid_name = options.invalid_name

# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
