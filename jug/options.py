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
Options

Options
-------
- jugdir: main jug directory.
- jugfile: filesystem name for the Jugfile
- cmd: command to run.
- aggressive_unload: --aggressive-unload
- invalid_name: --invalid
- argv: Arguments not captured by jug (for script use)
- print_out: Print function to be used for output (behaves like Python3's print)
'''
from __future__ import division
import logging
from datetime import datetime
import string
import sys

from .p3 import nprint

class Options(object):
    def __init__(self, next):
        self.next = next

    def copy(self):
        from copy import deepcopy
        return deepcopy(self)

    def __getattr__(self, name):
        if name == '__deepcopy__':
            raise AttributeError
        if name in self.__dict__:
            return self.__dict__[name]
        if self.__dict__['next'] is None:
            raise KeyError('jug.options: Cannot find option value for `%s`' % name)
        return getattr(self.__dict__['next'], name)

default_options = Options(None)

default_options.jugdir = '%(jugfile)s.jugdata'
default_options.jugfile = 'jugfile.py'
default_options.cmd = None
default_options.aggressive_unload = False
default_options.invalid_name = None
default_options.argv = None
default_options.print_out = nprint
default_options.status_mode = 'no-cached'
default_options.pdb = False
default_options.verbose = 'quiet'

default_options.execute_wait_cycle_time_secs = 12
default_options.execute_nr_wait_cycles = (30*60) // default_options.execute_wait_cycle_time_secs

_Commands = (
    'execute',
    'status',
    'check',
    'sleep-until',
    'stats',
    'cleanup',
    'count',
    'invalidate',
    'shell',
    )
_usage_string = \
'''jug SUBCOMMAND JUGFILE OPTIONS...

Subcommands
-----------
   execute:      Execute tasks
   status:       Print status
   check:        Returns 0 if all tasks are finished. 1 otherwise.
   sleep-until:  Wait until all tasks are done, then exit.
   counts:       Simply count tasks
   cleanup:      Cleanup: remove result files that are not used.
   invalidate:   Invalidate the results of a task
   shell:        Run a shell after initialization

General Options
---------------
--jugdir=JUGDIR
    Directory in which to save intermediate files
    You can use Python format syntax, the following variables are available:
        - date
        - jugfile (without extension)
    By default, the value of `jugdir` is "%(jugfile)s.jugdata"
--verbose=LEVEL
    Verbosity level ('DEBUG', 'INFO', 'QUIET')

execute OPTIONS
---------------
--aggressive-unload
    Aggressively unload data from memory. This causes many more reloading of
    information, but is necessary if keeping too much in memory is leading to
    memory errors.
--pdb
    Call python debugger on errors

invalidate OPTIONS
------------------
--invalid=TASK-NAME
    Task name to invalidate


Examples
--------

  jug status script.py
  jug execute script.py &
  jug execute script.py &
  jug status script.py
'''

_usage_simple = 'jug SUBCOMMAND [JUGFILE] [OPTIONS...]'

def usage():
    '''
    usage()

    Print an usage string and exit.
    '''
    import sys
    print _usage_string
    sys.exit(1)

def _str_to_bool(s):
    return s in ('', '0', 'False', 'off')

def read_configuration_file(fp=None):
    '''
    options = read_configuration_file(fp='~/.jug/configrc')

    Parse configuration file.

    Parameters
    ----------
    fp : inputfile, optional
        File to read. If not given, use
    '''
    if fp is None:
        from os import path
        fp = path.expanduser('~/.jug/configrc')
        try:
            fp = open(fp)
        except IOError:
            return Options(None)
    import ConfigParser
    config = ConfigParser.RawConfigParser()
    config.readfp(fp)
    infile = Options(None)

    def attempt(section, entry, new_name, conv=None):
        try:
            value = config.get(section, entry)
            if conv is not None:
                value = conv(value)
            setattr(infile, new_name, value)
        except ConfigParser.NoOptionError:
            pass
        except ConfigParser.NoSectionError:
            pass
    attempt('main', 'jugdir', 'jugdir')
    attempt('main', 'jugfile', 'jugfile')
    attempt('status', 'cache', 'status_mode')
    attempt('execute', 'aggressive-unload', 'aggressive_unload', _str_to_bool)
    attempt('execute', 'pbd', 'pdb', bool)
    attempt('execute', 'nr-wait-cycles', 'execute_nr_wait_cycles', int)
    attempt('execute', 'wait-cycle-time', 'execute_wait_cycle_time_secs', int)
    return infile


def parse(cmdlist=None, optionsfile=None):
    '''
    options.parse(cmdlist={sys.argv[1:]}, optionsfile=None)

    Parse the command line options and set the option variables.
    '''
    import optparse
    from .jug_version import __version__

    if cmdlist is None:
        cmdlist = sys.argv[1:]
    infile = read_configuration_file(optionsfile)
    infile.next = default_options
    cmdline = Options(infile)

    parser = optparse.OptionParser(usage=_usage_simple, version=__version__)
    parser.add_option('--aggressive-unload',action='store_true',dest='aggressive_unload')
    parser.add_option('--invalid',action='store',dest='invalid_name')
    parser.add_option('--jugdir',action='store',dest='jugdir')
    parser.add_option('--verbose',action='store',dest='verbose')
    parser.add_option('--cache', action='store_true', dest='cache')
    parser.add_option('--pdb', action='store_true', dest='pdb')
    parser.add_option('--nr-wait-cycles', action='store', dest='execute_nr_wait_cycles')
    parser.add_option('--wait-cycle-time', action='store', dest='execute_wait_cycle_time_secs')
    options,args = parser.parse_args(cmdlist)
    if not args:
        usage()
        return

    cmdline.cmd = args.pop(0)
    if args:
        cmdline.jugfile = args.pop(0)

    if cmdline.cmd not in _Commands:
        usage()
        return
    if options.invalid_name and cmdline.cmd != 'invalidate':
        usage()
        return
    if cmdline.cmd == 'invalidate' and not options.invalid_name:
        usage()
        return

    cmdline.argv = args
    sys.argv = [cmdline.jugfile] + args
    if options.cache is not None:
        cmdline.status_mode = ('cached' if options.cache else 'no-cached')
    def _maybe_set(name):
        if getattr(options, name) is not None:
            setattr(cmdline, name, getattr(options, name))

    _maybe_set('jugdir')

    _maybe_set('verbose')
    _maybe_set('aggressive_unload')
    _maybe_set('invalid_name')
    _maybe_set('pdb')
    _maybe_set('execute_nr_wait_cycles')
    _maybe_set('execute_wait_cycle_time_secs')

    cmdline.jugdir = cmdline.jugdir % {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'jugfile': cmdline.jugfile[:-3],
                }
    try:
        nlevel = {
            'DEBUG' : logging.DEBUG,
            'INFO' : logging.INFO,
        }[string.upper(cmdline.verbose)]
        root = logging.getLogger()
        root.level = nlevel
    except KeyError:
        pass
    return cmdline


def set_jugdir(jugdir):
    '''
    store = set_jugdir(jugdir)

    Sets the jugdir. This is the programmatic equivalent of passing
    ``--jugdir=...`` on the command line.

    Parameters
    ----------
    jugdir : str

    Returns
    -------
    store : a jug backend
    '''
    from .task import Task
    import backends
    if jugdir is None:
        jugdir = 'jugdata'
    store = backends.select(jugdir)
    Task.store = store
    return store

