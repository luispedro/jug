# -*- coding: utf-8 -*-
# Copyright (C) 2008-2022, Luis Pedro Coelho <luis@luispedro.org>
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

import logging
from datetime import datetime
from .jug_version import __version__
import sys


class Options:
    def __init__(self, next, autoinit=False):
        self.next = next
        self._autoinit = autoinit

    def update(self, dict):
        for k, v in dict.items():
            setattr(self, k, v)

    def copy(self):
        from copy import deepcopy
        return deepcopy(self)

    def __getattr__(self, name):
        if name in ('__deepcopy__', '_autoinit'):
            raise AttributeError

        if self._autoinit:
            # Used to automatically load default values from subcommands when
            # first accessed and no match exists
            self._autoinit(self)
            self._autoinit = False

        if name in self.__dict__:
            return self.__dict__[name]

        if self.__dict__.get('next') is None:
            raise AttributeError
        return getattr(self.__dict__['next'], name)


def load_default_options(opt):
    opt.jugdir = '%(jugfile)s.jugdata'
    opt.jugfile = 'jugfile.py'
    opt.subcommand = None
    opt.aggressive_unload = False
    opt.invalid_name = None
    opt.argv = None
    opt.print_out = print
    opt.short = False
    opt.pdb = False
    opt.verbose = 'quiet'
    opt.debug = False
    opt.will_cite = False

    # Current hierarchy of options is the following:
    #   default_options
    #     .next => subcommands.default_options
    from .subcommands import cmdapi
    opt.next = cmdapi.default_options


default_options = Options(None, autoinit=load_default_options)


def _str_to_bool(s):
    return s.lower() not in ('', '0', 'false', 'off')


def key_to_option(s):
    return s.replace('-', '_')


def find_local_configuration_files():
    '''
    files = find_local_configuration_files()

    Walk up from the current working directory looking for `.jugrc` or `jugrc`
    files. If a `.git` directory is found, search up to (and including) that
    directory. If no `.git` is found, only search the current directory.

    Returns
    -------
    files : list of str
        Paths to configuration files, ordered closest-to-cwd first.
    '''
    from pathlib import Path
    cwd = Path.cwd()
    found = []
    git_root = None

    # Walk upward to find git root
    for d in [cwd, *cwd.parents]:
        if (d / '.git').is_dir():
            git_root = d
            break

    # Search directories from cwd upward
    search = [cwd, *cwd.parents] if git_root is not None else [cwd]
    for d in search:
        for name in ['.jugrc', 'jugrc']:
            candidate = d / name
            if candidate.is_file():
                found.append(str(candidate))
        if git_root is not None and d == git_root:
            break

    return found


def _parse_config_file(fp, next_options, default_options=None):
    '''Parse a single configuration file into an Options object.

    Parameters
    ----------
    fp : file-like object
        Open file to read.
    next_options : Options
        The next Options object in the chain.
    default_options : Options, optional
        Used to determine types for casting config values.

    Returns
    -------
    options : Options
    '''
    import configparser
    options = Options(next_options)
    config = configparser.RawConfigParser()
    config.read_file(fp)
    fp.close()

    for section in config.sections():
        for key, value in config.items(section):
            if section == "main":
                new_name = key_to_option(key)
            else:
                new_name = "{0}_{1}".format(key_to_option(section), key_to_option(key))

            if default_options is not None:
                old_value = getattr(default_options, new_name, None)
                if old_value is not None:
                    if isinstance(old_value, bool):
                        value = _str_to_bool(value)
                    else:
                        value = type(old_value)(value)

            logging.debug("Setting %s to %s", new_name, value)
            setattr(options, new_name, value)

    return options


def read_configuration_file(fp=None, default_options=None):
    '''
    options = read_configuration_file(fp='~/.config/jugrc',
                                      default_options={'':'', ...})

    Parse configuration file.

    Parameters
    ----------
    fp : inputfile, optional
        File to read. If not given, use
    default_options: dictionary, optional
        Dictionary with the default values for all command-line arguments.
        Used to convert settings in the config file to the correct object type.
    '''
    if fp is not None:
        return _parse_config_file(fp, default_options, default_options=default_options)

    # Start with global config -> defaults chain
    global_options = Options(default_options)
    from os import path
    for gfp in ['~/.config/jug/jugrc', '~/.config/jugrc', '~/.jug/configrc']:
        gfp = path.expanduser(gfp)
        if path.exists(gfp):
            try:
                f = open(gfp)
            except IOError:
                break
            global_options = _parse_config_file(f, default_options, default_options=default_options)
            break

    # Find local config files (closest-first)
    local_files = find_local_configuration_files()

    if not local_files:
        return global_options

    # Chain: closest local -> ... -> farthest local -> global -> defaults
    # Build from farthest to closest so closest ends up on top
    head = global_options
    for config_path in reversed(local_files):
        try:
            f = open(config_path)
        except IOError:
            continue
        head = _parse_config_file(f, head, default_options=default_options)

    return head


def add_common_options(parser):
    group = parser.add_argument_group("common")
    group.add_argument('jugfile', action='store', nargs='?',
                       help="Python script to use. (Default: %(default)s)" % {"default": default_options.jugfile})
    group.add_argument('--aggressive-unload',
                       action='store_true',
                       dest='aggressive_unload',
                       help='''\
Aggressively unload data from memory. This causes many more reloading of
information, but is necessary if keeping too much in memory is leading to
memory errors.''')
    group.add_argument('--jugdir',
                       action='store',
                       dest='jugdir',
                       help='''\
Directory in which to save intermediate files
You can use Python format syntax, the following variables are available:
    - date
    - jugfile (without extension)

    By default, the value of `jugdir` is "%(jugfile)s.jugdata"''' % {"jugfile": default_options.jugfile})
    group.add_argument('--verbose',
                       action='store',
                       dest='verbose',
                       help='Verbosity level [use "info" to see details of processing]')
    group.add_argument('--short',
                       action='store_true',
                       dest='short',
                       help='Short output')
    group.add_argument('--pdb',
                       action='store_true',
                       dest='pdb',
                       help='Drop to a PDB (debug) console on error')
    group.add_argument('--debug',
                       action='store_true',
                       dest='debug',
                       help='''\
Debug mode. This adds a little more error checking, thus it can be slower.
However, it detects certain types of errors and prints an error message. If
--pdb is passed, --debug is automatically implied, but the opposite is not
true: you can use --debug mode without --pdb.''')
    group.add_argument('--will-cite',
                       # We **cannot** use store_true because that will set it
                       # to False if the argument is not passsed.
                       # In this case, this is undesired behaviour as then the
                       # value in the configuration file will not be used.
                       action='store_const',
                       const=True,
                       dest='will_cite',
                       help='Suppresses request for citation')


def parse(args=None, optionsfile=None):
    '''
    options.parse(cmdlist={sys.argv[1:]}, optionsfile=None)

    Parse the command line options and set the option variables.
    '''
    import argparse
    from .subcommands import cmdapi
    import sys

    if args is None:
        # If reading from sys.argv, argparse discards the first argument
        # Since we filter sys.argv manually, we do the same here
        args = sys.argv[1:]
    if not args:
        cmdapi.usage()

    parser = argparse.ArgumentParser(
        description=cmdapi.usage(_print=False, exit=False),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument('--version', action="version", version=__version__)

    sub = parser.add_subparsers(dest="subcommand", help=argparse.SUPPRESS)
    sub.required = True
    subparsers = cmdapi.get_subcommand_parsers(sub)

    # NOTE The parents=[parent] feature of argparse is severely broken
    # causing dependency loops in required arguments.
    # To workaround we re-define all global options in all subparsers
    for sub in subparsers:
        add_common_options(sub)
        sub.add_argument('user_args', nargs='*', default=[])

    argopts = parser.parse_args(args)

    inifile = read_configuration_file(optionsfile, default_options=default_options)
    # Priority is: user-supplied command line, config file, default options
    cmdline = Options(inifile)

    # Set cmdline options only if they aren't None
    for key, val in vars(argopts).items():
        if val is not None:
            setattr(cmdline, key, val)
    try:
        nlevel = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
        }[cmdline.verbose.upper()]
        root = logging.getLogger()
        root.level = nlevel
    except KeyError:
        pass

    cmdline.jugdir = cmdline.jugdir % {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'jugfile': cmdline.jugfile[:-3],
    }

    logging.debug("command-line args: %s", argopts)
    logging.debug("jugrc args: %s", inifile.__dict__)
    logging.debug("default args: %s", default_options.__dict__)
    logging.debug("default subcommand args: %s", default_options.next.__dict__)
    logging.debug("continuing with: %s", cmdline.__dict__)

    # jugscripts can rely on having the jugfile as first argument and the remaining
    # arguments thereafter
    sys.argv[:] = [cmdline.jugfile] + argopts.user_args

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
    from . import backends
    if jugdir is None:
        jugdir = 'jugdata'
    store = backends.select(jugdir)
    Task.store = store
    return store
