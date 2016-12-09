# -*- coding: utf-8 -*-
# Copyright (C) 2013, Luis Pedro Coelho <luis@luispedro.org>
# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
# LICENSE: MIT
'''
Jug.IO module

- write_task_out: write out results, possibly with metadata.
'''

from .task import TaskGenerator

class NoLoad(object):
    def __init__(self, t):
        self.t = t

    def __jug_hash__(self):
        from .hash import hash_one
        return hash_one(['NoLoad', self.t.hash()])

    def __jug_value__(self):
        return self

@TaskGenerator
def _do_write_task_out(result_value, result, oname, metadata_fname=None, metadata_format='yaml'):
    from .task import describe
    if metadata_fname is not None:
        description = describe(result.t)
        if metadata_format.lower() == 'yaml':
            import yaml
            yaml.dump(description, open(metadata_fname, 'w'))
        elif metadata_format.lower() == 'json':
            import json
            json.dump(description, open(metadata_fname, 'w'))
        else:
            raise ValueError('jug.io.write_task_out: Unknown metadata format "{}" [supported are "yaml" and "json"]'.format(metadata_format))
    try:
        import numpy as np
        if isinstance(result_value, np.ndarray):
            np.save(result, oname)
            return
    except:
        pass
    if oname is not None:
        import pickle
        pickle.dump(result_value, open(oname, 'wb'))

def write_task_out(result, oname, metadata_fname=None, metadata_format='yaml'):
    '''
    write_task_out(result, oname, metadata_fname=None, metadata_format='yaml')

    Write out the results of a Task to file, possibly including metadata.

    If ``metadata_fname`` is not None, it should be the name of a file to which
    to write metadata on the computation.

    Parameters
    ----------
    result: a Task object
    oname : str
        The target output filename
    metadata_fname : str, optional
        If not None, metadata will be written to this file.
    metadata_format : str, optional
        What format to write data in. Currently, 'yaml' & 'json' are supported.
    '''

    return _do_write_task_out(result, NoLoad(result), oname, metadata_fname, metadata_format)

def write_metadata(result, metadata_fname, metadata_format='yaml'):
    '''
    write_metadata(result, metadata_fname, metadata_format='yaml')

    Write out the metadata on a Task out.


    Parameters
    ----------
    result: a Task object
    metadata_fname : str
        metadata will be written to this file.
    metadata_format : str, optional
        What format to write data in. Currently, 'yaml' & 'json' are supported.
    '''

    return _do_write_task_out(result, NoLoad(result), None, metadata_fname, metadata_format)

# Console status table output

def print_task_summary_table(options, groups):
    """Print task summary table given tasks groups.

    groups - [(group_title, {(task_name, count)})] grouped summary of tasks.
    """
    if options.short:
        for name,gv in groups:
            options.print_out("{0}:  {1} tasks".format(name, sum(gv.values())))
        n = sum([sum(gv.values()) for _,gv in groups])
        options.print_out("** Total: {0} tasks.".format(n))
        return

    import textwrap
    num_groups = len(groups)

    names = set()
    for _, group_data in groups:
        names.update(group_data.keys())

    termsize, termheight = get_terminal_size()
    name_width = termsize - (num_groups * 12) - 2
    if name_width <= 8: # too short. Output will look ugly in any case
        name_width = 12

    line_format = ("%12s" * num_groups) + '  ' + '%-' + str(name_width) + 's'
    format_size = (12 * num_groups) + 2 + name_width

    options.print_out(line_format % tuple([g for g, _ in groups] + ["Task name"]))
    options.print_out('-' * format_size)

    for n in sorted(names):
        name_lines = textwrap.wrap(n, width=name_width - 4)
        options.print_out(line_format % tuple([g[n] for _, g in groups] + name_lines[:1]))

        for name_extension in name_lines[1:]:
            options.print_out(line_format % tuple( ([""] * num_groups) + [(" " * 4) + name_extension]))

    options.print_out('.' * format_size)
    options.print_out(line_format % tuple([sum(g.values()) for _,g in groups] + ["Total"]))
    options.print_out()

# Terminal size calculation

import os
import shlex
import struct
import platform
import subprocess

def get_terminal_size():
    """ get_terminal_size()
     - get width and height of console
     - works on linux,os x,windows,cygwin(windows)
     originally retrieved from:
     http://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python
    """
    current_os = platform.system()
    tuple_xy = None
    if current_os == 'Windows':
        tuple_xy = _get_terminal_size_windows()
        if tuple_xy is None:
            tuple_xy = _get_terminal_size_tput()
            # needed for window's python in cygwin's xterm!
    if current_os in ['Linux', 'Darwin'] or current_os.startswith('CYGWIN'):
        tuple_xy = _get_terminal_size_linux()
    if tuple_xy is None:
        tuple_xy = (80, 25)      # default value
    return tuple_xy

def _get_terminal_size_windows():
    try:
        from ctypes import windll, create_string_buffer
        # stdin handle is -10
        # stdout handle is -11
        # stderr handle is -12
        h = windll.kernel32.GetStdHandle(-12)
        csbi = create_string_buffer(22)
        res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
        if res:
            (bufx, bufy, curx, cury, wattr,
             left, top, right, bottom,
             maxx, maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
            sizex = right - left + 1
            sizey = bottom - top + 1
            return sizex, sizey
    except:
        pass

def _get_terminal_size_tput():
    # get terminal width
    # src: http://stackoverflow.com/questions/263890/how-do-i-find-the-width-height-of-a-terminal-window
    try:
        cols = int(subprocess.check_call(shlex.split('tput cols')))
        rows = int(subprocess.check_call(shlex.split('tput lines')))
        return (cols, rows)
    except:
        pass

def _get_terminal_size_linux():
    def ioctl_GWINSZ(fd):
        try:
            import fcntl
            import termios
            cr = struct.unpack('hh',
                               fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
            return cr
        except:
            pass
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        try:
            cr = (os.environ['LINES'], os.environ['COLUMNS'])
        except:
            return None
    return int(cr[1]), int(cr[0])
