#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (C) 2008-2009, Luís Pedro Coelho <lpc@cmu.edu>
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
from .task import Task

silent = False
def print_out(s=''):
    if not silent:
        print s

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
    for t in tasks:
        if t.name == invalid_name:
            invalid.add(t)
        else:
            for dep in task.recursive_dependencies(t):
                if type(dep) is task.Task:
                    if dep.name == invalid_name:
                        invalid.add(t)
                        break
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
        print_out('    Task Name          Count')
        print_out('----------------------------')
        for n_c in task_counts.items():
            print_out('%21s: %12s' % n_c)


def execute(store, aggressive_unload=False):
    '''
    execute(store, aggressive_unload=False)

    Implement 'execute' command
    '''
    task_names = set(t.name for t in task.alltasks)
    tasks = task.alltasks
    tasks_executed = defaultdict(int)
    tasks_loaded = defaultdict(int)
    task.topological_sort(tasks)
    logging.info('Execute start (%s tasks)' % len(tasks))
    signal(SIGTERM,_sigterm)
    waits = [0,8,16,32,64,128,128,128,128,1024,2048]
    while tasks:
        upnext = []
        for w in waits:
            if w:
                logging.info('waiting...', w, 'for an open task')
                sleep(w)
            cannot_run = 0
            max_cannot_run = max(128, min(len(tasks)//4+2, 32))
            while not tasks[0].can_run() and cannot_run < max_cannot_run:
                tasks.append(tasks.pop(0))
                cannot_run += 1
            while tasks and tasks[0].can_run():
                upnext.append(tasks.pop(0))
            if upnext:
                break
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
                logging.critical('Exception while running %s: %s' % (t.name,e))
                raise
            finally:
                if locked: t.unlock()

    print_out('%-52s%12s%12s' %('Task name','Executed','Loaded'))
    print_out('-' * (52+12+12))
    for t in task_names:
        print_out('%-52s%12s%12s' % (t,tasks_executed[t],tasks_loaded[t]))
    if not task_names:
        print_out('<no tasks>')

def status(store):
    '''
    status(store)

    Implements the status command.
    '''
    task_names = set(t.name for t in task.alltasks)
    tasks = task.alltasks
    tasks_ready = defaultdict(int)
    tasks_finished = defaultdict(int)
    tasks_running = defaultdict(int)
    tasks_waiting = defaultdict(int)
    for t in tasks:
        if t.can_load():
            tasks_finished[t.name] += 1
        elif t.can_run():
            if t.is_locked():
                tasks_running[t.name] += 1
            else:
                tasks_ready[t.name] += 1
        else:
            tasks_waiting[t.name] += 1

    print_out('%-40s%12s%12s%12s%12s' % ('Task name','Waiting','Ready','Finished','Running'))
    print_out('-' * (40+12+12+12+12))
    for t in task_names:
        print_out('%-40s%12s%12s%12s%12s' % (t[:40],tasks_waiting[t],tasks_ready[t],tasks_finished[t],tasks_running[t]))
    print_out('.' * (40+12+12+12+12))
    print_out('%-40s%12s%12s%12s%12s' % ('Total:',sum(tasks_waiting.values()),sum(tasks_ready.values()),sum(tasks_finished.values()),sum(tasks_running.values())))
    print_out()

def cleanup(store):
    '''
    cleanup(store)

    Implement 'cleanup' command
    '''
    tasks = task.alltasks
    removed = store.cleanup(tasks)
    print_out('Removed %s files' % removed)

def init(jugfile, jugdir, on_error='exit'):
    '''
    store = init(jugfile, jugdir, on_error='exit')

    Initializes jug (create backend connection, ...).
    Imports jugfile

    Parameters
    ----------
    `jugfile` : jugfile to import
    `jugdir` : jugdir to use (could be a path)
    `on_error` : What to do if import fails (default: exit)

    Returns
    -------
    `store` : storage object
    '''
    store = backends.select(jugdir)
    Task.store = store

    if jugfile.endswith('.py'):
        jugfile = jugfile[:-len('.py')]
    sys.path.insert(0, os.path.abspath('.'))
    try:
        __import__(jugfile)
    except ImportError:
        logging.critical("Could not import file '%s'" % jugfile)
        sys.exit(1)
    return store


def _sigterm(_,__):
    sys.exit(1)

def main():
    options.parse()
    store = init(options.jugfile, options.jugdir)

    if options.cmd == 'execute':
        execute(store, options.aggressive_unload)
    elif options.cmd == 'count':
        do_print(store)
    elif options.cmd == 'status':
        status(store)
    elif options.cmd == 'invalidate':
        invalidate(store, options.invalid_name)
    elif options.cmd == 'cleanup':
        cleanup(store)
    else:
        logging.critical('Jug: unknown command: \'%s\'' % options.cmd)

if __name__ == '__main__':
    try:
        main()
    except Exception, exc:
        logging.critical('Unhandled Jug Error!')
        raise
# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
