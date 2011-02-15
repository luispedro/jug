#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (C) 2008-2010, Luis Pedro Coelho <lpc@cmu.edu>
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
import logging

from . import task
from . import backends
from .backends import memoize_store
from .task import Task
from .subcommands.status import status
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

    Implement 'invalidate' command

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
    def isinvalid(t):
        h = t.hash()
        if h in cache:
            return cache[h]
        if t.name == invalid_name:
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

def execute(store, options):
    '''
    execute(store, options)

    Implement 'execute' command
    '''
    from time import sleep
    from signal import signal, SIGTERM

    tasks = task.alltasks
    task_names = set(t.name for t in tasks)
    tasks_executed = defaultdict(int)
    tasks_loaded = defaultdict(int)
    task.topological_sort(tasks)
    logging.info('Execute start (%s tasks)' % len(tasks))
    signal(SIGTERM,_sigterm)
    while tasks:
        upnext = [] # tasks that can be run
        for i in xrange(options.execute_nr_wait_cycles):
            max_cannot_run = min(len(tasks), 128)
            for i in xrange(max_cannot_run):
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
            logging.info('waiting 12 secs for an open task...')
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
            except Exception, e:
                if options.pdb:
                    import pdb, sys
                    _,_, tb = sys.exc_info()
                    pdb.post_mortem(tb)
                else:
                    import itertools
                    logging.critical('Exception while running %s: %s' % (t.name,e))
                    for other in itertools.chain(upnext, tasks):
                        for dep in other.dependencies():
                            if dep is t:
                                logging.critical('Other tasks are dependent on this one! Parallel processors will be held waiting!')
                raise
            finally:
                if locked: t.unlock()

    options.print_out('%-52s%12s%12s' %('Task name','Executed','Loaded'))
    options.print_out('-' * (52+12+12))
    for t in task_names:
        name_cut = t[:52]
        options.print_out('%-52s%12s%12s' % (name_cut,tasks_executed[t],tasks_loaded[t]))
    if not task_names:
        options.print_out('<no tasks>')


def cleanup(store):
    '''
    cleanup(store)

    Implement 'cleanup' command
    '''
    tasks = task.alltasks
    removed = store.cleanup(tasks)
    print_out('Removed %s files' % removed)


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
    _check_or_sleep_until(store, False)

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
    _check_or_sleep_until(store, True)

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
                sys.exit(1)
        else:
            for dep in recursive_dependencies(t):
                try:
                    active.remove(dep)
                except KeyError:
                    pass
    sys.exit(0)


def init(jugfile=None, jugdir=None, on_error='exit'):
    '''
    store,jugspace = init(jugfile={'jugfile'}, jugdir={'jugdata'}, on_error='exit')

    Initializes jug (create backend connection, ...).
    Imports jugfile

    Parameters
    ----------
    `jugfile` : jugfile to import (default: 'jugfile')
    `jugdir` : jugdir to use (could be a path)
    `on_error` : What to do if import fails (default: exit)

    Returns
    -------
    `store` : storage object
    `jugspace` : dictionary
    '''
    import imp
    assert on_error in ('exit', 'propagate'), 'jug.init: on_error option is not valid.'

    if jugfile is None:
        jugfile = 'jugfile'
    if jugdir is None:
        jugdir = 'jugdata'
    store = backends.select(jugdir)
    Task.store = store
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
    jugspace = jugmodule.__dict__
    sys.modules[jugmodname] = jugmodule
    try:
        execfile(jugfile, jugspace, jugspace)
    except BarrierError:
        pass
    except Exception, e:
        logging.critical("Could not import file '%s' (error: %s)", jugfile, e)
        if on_error == 'exit':
            sys.exit(1)
        else:
            raise
    return store, jugspace


def main():
    from .options import parse
    options = parse()
    if options.cmd != 'status':
        store,jugspace = init(options.jugfile, options.jugdir)

    if options.cmd == 'execute':
        execute(store, options)
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
    else:
        logging.critical('Jug: unknown command: \'%s\'' % options.cmd)
    if options.cmd != 'status':
        store.close()

if __name__ == '__main__':
    try:
        main()
    except Exception, exc:
        logging.critical('Unhandled Jug Error!')
        raise
