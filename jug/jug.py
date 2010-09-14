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
from signal import signal, SIGTERM
from time import sleep
import sys
import os
import os.path
import random
import logging

from . import options
from . import task
from . import backends
from .backends import memoize_store
from .task import Task
from .subcommands.status import status
from .subcommands.shell import shell
from .options import print_out

def do_print(store):
    '''
    do_print(store)

    Print a count of task names.
    '''
    task_counts = defaultdict(int)
    for t in task.alltasks:
        task_counts[t.name] += 1
    for tnc in task_counts.items():
        print_out('Task %s: %s' % tnc)

def invalidate(store, invalid_name):
    '''
    invalidate()

    Implement 'invalidate' command
    '''
    invalid = set()
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
        print_out('No results invalidated.')
        return
    task_counts = defaultdict(int)
    for t in invalid:
        if store.remove(t.hash()):
            task_counts[t.name] += 1
    if sum(task_counts.values()) == 0:
        print_out('Tasks invalidated, but no results removed')
    else:
        print_out('Tasks Invalidated')
        print_out()
        print_out('Task Name                                   Count')
        print_out('-------------------------------------------------')
        #          0         1         2         3         4         5
        #          012345678901234567890123456789012345678901234567890123456789
        for n_c in task_counts.items():
            print_out('%-40s: %7s' % n_c)


def execute(store, aggressive_unload=False):
    '''
    execute(store, aggressive_unload=False)

    Implement 'execute' command
    '''

    tasks = task.alltasks
    task_names = set(t.name for t in tasks)
    tasks_executed = defaultdict(int)
    tasks_loaded = defaultdict(int)
    task.topological_sort(tasks)
    logging.info('Execute start (%s tasks)' % len(tasks))
    signal(SIGTERM,_sigterm)
    while tasks:
        upnext = []
        for i in xrange(30*60//12): #This is at most half-an-hour
            cannot_run = 0
            max_cannot_run = min(len(tasks), 128)
            while not tasks[0].can_run() and cannot_run < max_cannot_run:
                tasks.append(tasks.pop(0))
                cannot_run += 1
            while tasks and tasks[0].can_run():
                upnext.append(tasks.pop(0))
            if upnext:
                break
            logging.info('waiting 12 secs for an open task...')
            sleep(12)
        if not upnext:
            logging.info('No tasks can be run!')
            return
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
                    if aggressive_unload:
                        t.unload_recursive()
                else:
                    logging.info('Already in execution %s...' % t.name)
            except Exception, e:
                import itertools
                logging.critical('Exception while running %s: %s' % (t.name,e))
                for other in itertools.chain(upnext, tasks):
                    for dep in other.dependencies():
                        if dep is t:
                            logging.critical('Other tasks are dependent on this one! Parallel processors will be held waiting!')
                raise
            finally:
                if locked: t.unlock()

    print_out('%-52s%12s%12s' %('Task name','Executed','Loaded'))
    print_out('-' * (52+12+12))
    for t in task_names:
        name_cut = t[:52]
        print_out('%-52s%12s%12s' % (name_cut,tasks_executed[t],tasks_loaded[t]))
    if not task_names:
        print_out('<no tasks>')


def cleanup(store):
    '''
    cleanup(store)

    Implement 'cleanup' command
    '''
    tasks = task.alltasks
    removed = store.cleanup(tasks)
    print_out('Removed %s files' % removed)


def check(store):
    '''
    check(store)

    Executes check subcommand
    '''
    from .task import recursive_dependencies
    tasks = task.alltasks
    active = set(tasks)
    for t in reversed(tasks):
        if t not in active:
            continue
        if not t.can_load(store):
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
    store = init(jugfile={'jugfile'}, jugdir={'jugdata'}, on_error='exit')

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
    '''
    assert on_error in ('exit', 'propagate'), 'jug.init: on_error option is not valid.'
    if jugfile is None:
        jugfile = 'jugfile'
    if jugdir is None:
        jugdir = 'jugdata'
    store = backends.select(jugdir)
    Task.store = store

    if jugfile.endswith('.py'):
        jugfile = jugfile[:-len('.py')]
    sys.path.insert(0, os.path.abspath('.'))
    try:
        jugmodule = __import__(jugfile)
    except ImportError, e:
        logging.critical("Could not import file '%s' (error: %s)", jugfile, e)
        if on_error == 'exit':
            sys.exit(1)
        else:
            raise
    return store, jugmodule


def _sigterm(_,__):
    sys.exit(1)

def main():
    options.parse()
    if options.cmd != 'status':
        store,jugmodule = init(options.jugfile, options.jugdir)

    if options.cmd == 'execute':
        execute(store, options.aggressive_unload)
    elif options.cmd == 'count':
        do_print(store)
    elif options.cmd == 'check':
        check(store)
    elif options.cmd == 'status':
        status()
    elif options.cmd == 'invalidate':
        invalidate(store, options.invalid_name)
    elif options.cmd == 'cleanup':
        cleanup(store)
    elif options.cmd == 'shell':
        shell(store, jugmodule)
    else:
        logging.critical('Jug: unknown command: \'%s\'' % options.cmd)

if __name__ == '__main__':
    try:
        main()
    except Exception, exc:
        logging.critical('Unhandled Jug Error!')
        raise
