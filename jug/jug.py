#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (C) 2008-2012, Luis Pedro Coelho <luis@luispedro.org>
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

from __future__ import division
from collections import defaultdict
import sys
import os
import os.path
import re
import logging

from . import task
from .task import Task
from .subcommands.status import status
from .subcommands.webstatus import webstatus
from .subcommands.shell import shell
from .barrier import BarrierError

def do_print(store, options):
    '''
    do_print(store, options)

    Print a count of task names.

    Parameters
    ----------
    store : jug backend
    options : jug options
    '''
    task_counts = defaultdict(int)
    for t in task.alltasks:
        task_counts[t.name] += 1
    for tnc in task_counts.items():
        options.print_out('Task %s: %s' % tnc)

def invalidate(store, options):
    '''
    invalidate(store, options)

    Implements 'invalidate' command

    Parameters
    ----------
    store : jug.backend
    options : options object
        Most relevant option is `invalid_name`, a string  with the exact (i.e.,
        module qualified) name of function to invalidate
    '''
    invalid_name = options.invalid_name
    tasks = task.alltasks
    cache = {}
    if re.match( r'/.*?/', invalid_name):
        # Looks like a regular expression
        invalidate_re = re.compile( invalid_name.strip('/') )
    elif '.' in invalid_name:
        # Looks like a full task name
        invalidate_re = invalid_name.replace('.','\\.' )
    else:
        # A bare function name perhaps?
        invalidate_re = re.compile(r'\.' + invalid_name )
    def isinvalid(t):
        if isinstance(t, task.Tasklet):
            return isinvalid(t.base)
        h = t.hash()
        if h in cache:
            return cache[h]
        if re.search( invalidate_re, t.name ):
            cache[h] = True
            return True
        for dep in t.dependencies():
            if isinvalid(dep):
                cache[h] = True
                return True
        cache[h] = False
        return False

    invalid = filter(isinvalid, tasks)
    if not invalid:
        options.print_out('No results invalidated.')
        return
    task_counts = defaultdict(int)
    for t in invalid:
        if store.remove(t.hash()):
            task_counts[t.name] += 1
    if sum(task_counts.values()) == 0:
        options.print_out('Tasks invalidated, but no results removed')
    else:
        options.print_out('Tasks Invalidated')
        options.print_out()
        options.print_out('Task Name                                   Count')
        options.print_out('-------------------------------------------------')
        #                  0         1         2         3         4         5
        #                  012345678901234567890123456789012345678901234567890123456789
        for n_c in task_counts.items():
            options.print_out('%-40s: %7s' % n_c)


def _sigterm(_,__):
    sys.exit(1)

def execution_loop(tasks, options, tasks_executed, tasks_loaded):
    from time import sleep

    logging.info('Execute start (%s tasks)' % len(tasks))
    while tasks:
        upnext = [] # tasks that can be run
        for i in range(options.execute_nr_wait_cycles):
            max_cannot_run = min(len(tasks), 128)
            for i in range(max_cannot_run):
                # The argument for this is the following:
                # if T' is dependent on the result of T, it is better if the
                # processor that ran T, also runs T'. By having everyone else
                # push T' to the end of tasks, this is more likely to happen.
                #
                # Furthermore, this avoids always querying the same tasks.
                if tasks[0].can_run():
                    break
                tasks.append(tasks.pop(0))
            while tasks and tasks[0].can_run():
                upnext.append(tasks.pop(0))
            if upnext:
                break
            logging.info('waiting %s secs for an open task...' % options.execute_wait_cycle_time_secs)
            sleep(options.execute_wait_cycle_time_secs)
        if not upnext:
            logging.info('No tasks can be run!')
            break
        for t in upnext:
            if t.can_load():
                logging.info('Loadable %s...' % t.name)
                tasks_loaded[t.name] += 1
                continue
            locked = False
            try:
                locked = t.lock()
                if t.can_load(): # This can be true if the task ran between the check above and this one
                    logging.info('Loadable %s...' % t.name)
                    tasks_loaded[t.name] += 1
                elif locked:
                    logging.info('Executing %s...' % t.name)
                    t.run()
                    tasks_executed[t.name] += 1
                    if options.aggressive_unload:
                        t.unload_recursive()
                else:
                    logging.info('Already in execution %s...' % t.name)
            except Exception as e:
                if options.pdb:
                    import sys
                    _,_, tb = sys.exc_info()

                    try:
                        import IPython
                        try:
                            #Attempt to load IPython debugger
                            import IPython.core.ipapi
                            import IPython.core.debugger
                            ip = IPython.core.ipapi.get()
                            debugger = IPython.core.debugger.Pdb(ip.colors)
                        except ImportError:
                            #Fallback to older version of IPython API
                            import IPython.ipapi
                            import IPython.Debugger
                            shell = IPython.Shell.IPShell(argv=[''])
                            ip = IPython.ipapi.get()
                            debugger=IPythong.Debugger.Pdb(ip.options.colors)
                    except ImportError:
                        #Fallback to standard debugger
                        import pdb
                        debugger = pdb.Pdb()

                    debugger.reset()
                    debugger.interaction(None, tb)
                else:
                    import itertools
                    logging.critical('Exception while running %s: %s' % (t.name,e))
                    for other in itertools.chain(upnext, tasks):
                        for dep in other.dependencies():
                            if dep is t:
                                logging.critical('Other tasks are dependent on this one! Parallel processors will be held waiting!')
                if not options.execute_keep_going:
                    raise
            finally:
                if locked: t.unlock()
def execute(options):
    '''
    execute(options)

    Implement 'execute' command
    '''
    from signal import signal, SIGTERM

    signal(SIGTERM,_sigterm)
    tasks = task.alltasks
    tasks_executed = defaultdict(int)
    tasks_loaded = defaultdict(int)
    store = None
    noprogress = 0
    while noprogress < 2:
        del tasks[:]
        store,jugspace = init(options.jugfile, options.jugdir, store=store)
        previous = sum(tasks_executed.values())
        execution_loop(tasks, options, tasks_executed, tasks_loaded)
        after = sum(tasks_executed.values())
        done = not jugspace.get('__jug__hasbarrier__', False)
        if done:
            break
        if after == previous:
            from time import sleep
            noprogress += 1
            sleep(options.execute_wait_cycle_time_secs)
    else:
        logging.info('No tasks can be run!')


    options.print_out('%-52s%12s%12s' %('Task name','Executed','Loaded'))
    options.print_out('-' * (52+12+12))
    task_names = tasks_executed.keys()
    task_names.extend(tasks_loaded.keys())
    task_names = sorted(set(task_names))
    for t in task_names:
        name_cut = t[:52]
        options.print_out('%-52s%12s%12s' % (name_cut,tasks_executed[t],tasks_loaded[t]))
    if not task_names:
        options.print_out('<no tasks>')


def cleanup(store, options):
    '''
    cleanup(store, options)

    Implement 'cleanup' command
    '''
    if options.cleanup_locks_only:
        removed = store.remove_locks()
    else:
        tasks = task.alltasks
        removed = store.cleanup(tasks)
    options.print_out('Removed %s files' % removed)


def check(store, options):
    '''
    check(store, options)

    Executes check subcommand

    Parameters
    ----------
    store : jug.backend
            backend to use
    options : jug options
    '''
    sys.exit(_check_or_sleep_until(store, False))

def sleep_until(store, options):
    '''
    sleep_until(store, options)

    Execute sleep-until subcommand

    Parameters
    ----------
    store : jug.backend
            backend to use
    options : jug options
        ignored
    '''
    sys.exit(_check_or_sleep_until(store, True))

def _check_or_sleep_until(store, sleep_until):
    from .task import recursive_dependencies
    tasks = task.alltasks
    active = set(tasks)
    for t in reversed(tasks):
        if t not in active:
            continue
        while not t.can_load(store):
            if sleep_until:
                from time import sleep
                sleep(12)
            else:
                return 1
        else:
            for dep in recursive_dependencies(t):
                try:
                    active.remove(dep)
                except KeyError:
                    pass
    return 0


def init(jugfile=None, jugdir=None, on_error='exit', store=None):
    '''
    store,jugspace = init(jugfile={'jugfile'}, jugdir={'jugdata'}, on_error='exit', store=None)

    Initializes jug (create backend connection, ...).
    Imports jugfile

    Parameters
    ----------
    jugfile : str, optional
        jugfile to import (default: 'jugfile')
    jugdir : str, optional
        jugdir to use (could be a path)
    on_error : str, optional
        What to do if import fails (default: exit)
    store : storage object, optional
        If used, this is returned as ``store`` again.

    Returns
    -------
    store : storage object
    jugspace : dictionary
    '''
    import imp
    from .options import set_jugdir
    assert on_error in ('exit', 'propagate'), 'jug.init: on_error option is not valid.'

    if jugfile is None:
        jugfile = 'jugfile'
    if store is None:
        store = set_jugdir(jugdir)
    sys.path.insert(0, os.path.abspath('.'))

    # The reason for this implementation is that it is the only that seems to
    # work with both barrier and pickle()ing of functions inside the jugfile
    #
    # Just doing __import__() will not work because if there is a BarrierError
    # thrown, then functions defined inside the jugfile end up in a confusing
    # state.
    #
    # Alternatively, just execfile()ing will make any functions defined in the
    # jugfile unpickle()able which makes mapreduce not work
    #
    # Therefore, we simulate (partially) __import__ and set sys.modules *even*
    # if BarrierError is raised.
    #
    jugmodname = os.path.basename(jugfile[:-len('.py')])
    jugmodule = imp.new_module(jugmodname)
    jugmodule.__file__ = os.path.abspath(jugfile)
    jugspace = jugmodule.__dict__
    sys.modules[jugmodname] = jugmodule
    try:
        exec(compile(open(jugfile).read(), jugfile, 'exec'), jugspace, jugspace)
    except BarrierError:
        jugspace['__jug__hasbarrier__'] = True
    except Exception as e:
        logging.critical("Could not import file '%s' (error: %s)", jugfile, e)
        if on_error == 'exit':
            import traceback
            print(traceback.format_exc(e))
            sys.exit(1)
        else:
            raise
    return store, jugspace


def main():
    from .options import parse
    options = parse()
    store = None
    if options.cmd not in ('status', 'execute', 'webstatus'):
        store,jugspace = init(options.jugfile, options.jugdir)

    if options.cmd == 'execute':
        execute(options)
    elif options.cmd == 'count':
        do_print(store, options)
    elif options.cmd == 'check':
        check(store, options)
    elif options.cmd == 'sleep-until':
        sleep_until(store, options)
    elif options.cmd == 'status':
        status(options)
    elif options.cmd == 'invalidate':
        invalidate(store, options)
    elif options.cmd == 'cleanup':
        cleanup(store, options)
    elif options.cmd == 'shell':
        shell(store, options, jugspace)
    elif options.cmd == 'webstatus':
        webstatus(options)
    else:
        logging.critical('Jug: unknown command: \'%s\'' % options.cmd)
    if store is not None:
        store.close()

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        logging.critical('Unhandled Jug Error!')
        raise
