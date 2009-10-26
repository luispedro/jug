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

from . import options
from . import task
from . import file_based_store
from . import redis_store
from .task import Task

def do_print(store):
    '''
    do_print(store)

    Print a count of task names.
    '''
    task_counts = defaultdict(int)
    for t in task.alltasks:
        task_counts[t.name] += 1
    for tnc in task_counts.items():
        print 'Task %s: %s' % tnc

def invalidate(store):
    '''
    invalidate()

    Implement 'invalidate' command
    '''
    invalid_name = options.invalid_name
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
        print 'No results invalidated.'
        return
    task_counts = defaultdict(int)
    for t in invalid:
        if store.remove(t.hash()):
            task_counts[t.name] += 1
    if sum(task_counts.values()) == 0:
        print 'Tasks invalidated, but no results removed'
    else:
        print 'Tasks Invalidated'
        print
        print '    Task Name          Count'
        print '----------------------------'
        for n_c in task_counts.items():
            print '%21s: %12s' % n_c


def execute(store):
    '''
    execute(store)

    Implement 'execute' command
    '''
    task_names = set(t.name for t in task.alltasks)
    tasks = task.alltasks
    tasks_executed = defaultdict(int)
    tasks_loaded = defaultdict(int)
    task.topological_sort(tasks)
    print 'Execute start (%s tasks)' % len(tasks)
    signal(SIGTERM,_sigterm)
    waits = [0,4,8,16,32,64,128,128,128,128,1024,2048]
    upnext = []
    while tasks or upnext:
        if not upnext:
            for w in waits:
                if w:
                    print 'waiting...', w, 'for an open task'
                    sleep(w)
                upnext = []
                i = 0
                while i < len(tasks):
                    if tasks[i].can_run():
                        upnext.append(tasks[i])
                        del tasks[i]
                        if len(upnext) > 10:
                            break
                    else:
                        i += 1
                if upnext:
                    break
            if not upnext:
                print 'No tasks can be run!'
                return
        t = upnext.pop(0)
        if t.can_load():
            print 'Loadable %s...' % t.name
            tasks_loaded[t.name] += 1
            continue
        locked = False
        try:
            locked = t.lock()
            if t.can_load(): # This can be true if the task run between the check above and this one
                print 'Loadable %s...' % t.name
                tasks_loaded[t.name] += 1
            elif locked:
                print 'Executing %s...' % t.name
                t.run()
                tasks_executed[t.name] += 1
                if options.aggressive_unload:
                    t.unload_recursive()
            else:
                print 'Already in execution %s...' % t.name
        except Exception, e:
            print >>sys.stderr, 'Exception while running %s: %s' % (t.name,e)
            raise
        finally:
            if locked: t.unlock()

    print '%-52s%12s%12s' %('Task name','Executed','Loaded')
    print ('-' * (52+12+12))
    for t in task_names:
        print '%-52s%12s%12s' % (t,tasks_executed[t],tasks_loaded[t])
    if not task_names:
        print '<no tasks>'

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

    print '%-40s%12s%12s%12s%12s' %('Task name','Waiting','Ready','Finished','Running')
    print ('-' * (40+12+12+12+12))
    for t in task_names:
        print '%-40s%12s%12s%12s%12s' % (t[:40],tasks_waiting[t],tasks_ready[t],tasks_finished[t],tasks_running[t])
    print ('.' * (40+12+12+12+12))
    print '%-40s%12s%12s%12s%12s' % ('Total:',sum(tasks_waiting.values()),sum(tasks_ready.values()),sum(tasks_finished.values()),sum(tasks_running.values()))
    print

def cleanup(store):
    '''
    cleanup(store)

    Implement 'cleanup' command
    '''
    tasks = task.alltasks
    removed = store.cleanup(tasks)
    print 'Removed %s files' % removed

def init():
    '''
    init()

    Initializes jug (creates needed directories &c).
    Imports jugfile
    '''
    jugfile = options.jugfile
    if jugfile.endswith('.py'):
        jugfile = jugfile[:-len('.py')]
    try:
        __import__(jugfile)
    except ImportError:
        print >>sys.stderr, "Could not import file '%s'" % jugfile
        sys.exit(1)
    jugdir = options.jugdir
    if jugdir.startswith('redis:'):
        store = redis_store.redis_store(options.jugdir)
    else:
        store = file_based_store.file_store(options.jugdir)
    Task.store = store
    return store


def _sigterm(_,__):
    sys.exit(1)

def main():
    options.parse()
    store = init()

    if options.cmd == 'execute':
        execute(store)
    elif options.cmd == 'count':
        do_print(store)
    elif options.cmd == 'status':
        status(store)
    elif options.cmd == 'invalidate':
        invalidate(store)
    elif options.cmd == 'cleanup':
        cleanup(store)
    else:
        print >>sys.stderr, 'Jug: unknown command: \'%s\'' % options.cmd

if __name__ == '__main__':
    try:
        main()
    except Exception, exc:
        print >>sys.stderr, 'Jug Error!'
        raise
# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
