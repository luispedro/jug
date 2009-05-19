#!/usr/bin/python
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
from .store import create_directories

def do_print():
    '''
    do_print()

    Print a count of task names.
    '''
    task_counts = defaultdict(int)
    for t in task.alltasks:
        task_counts[t.name] += 1
    for tnc in task_counts.items():
        print 'Task %s: %s' % tnc

def invalidate():
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
        fname = t.filename()
        possible = [fname,fname+'.pp.gz',fname+'.pp']
        for p in possible:
            if os.path.exists(p):
                os.unlink(p)
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


def execute():
    '''
    execute()

    Implement 'execute' command
    '''
    task_names = set(t.name for t in task.alltasks)
    tasks = task.alltasks
    tasks_executed = defaultdict(int)
    tasks_loaded = defaultdict(int)
    if options.shuffle:
        random.shuffle(tasks)
    task.topological_sort(tasks)
    print 'Execute start'
    signal(SIGTERM,_sigterm)
    upnext = set()
    while tasks:
        if not upnext:
            if tasks[0].can_run():
                t = tasks.pop(0)
            else:
                waits = [0,4,8,16,32,64,128,128,128,128,1024,2048]
                t = None
                for w in waits:
                    if w:
                        print 'waiting...', w, 'for an open task'
                        sleep(w)
                    for i,t_ in enumerate(tasks):
                        if t_.can_run():
                            t = t_
                            del tasks[i]
                            break
                    if t is not None: break
                if t is None:
                    print 'No tasks can be run!'
                    return
        locked = False
        try:
            locked = t.lock()
            if t.can_load():
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
            print >>sys.stderr, 'Exception while running %s: %s' % (repr(t),e)
            raise
        finally:
            if locked: t.unlock()

    print '%-52s%12s%12s' %('Task name','Executed','Loaded')
    print ('-' * (40+12+12))
    for t in task_names:
        print '%-52s%12s%12s' % (t,tasks_executed[t],tasks_loaded[t])
    if not task_names:
        print '<no tasks>'

def status():
    '''
    status()

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

def init():
    '''
    init()

    Initializes jug (creates needed directories &c).
    Imports jugfile
    '''
    create_directories(options.tempdir)
    jugfile = options.jugfile
    assert jugfile.endswith('.py'), 'Jugfiles must have the .py extension!'
    jugfile = jugfile[:-len('.py')]
    __import__(jugfile)

def _sigterm(_,__):
    sys.exit(1)

def main():
    options.parse()
    init()

    if options.cmd == 'execute':
        execute()
    elif options.cmd == 'count':
        do_print()
    elif options.cmd == 'status':
        status()
    elif options.cmd == 'invalidate':
        invalidate()
    else:
        print >>sys.stderr, 'Jug: unknown command: \'%s\'' % options.cmd

if __name__ == '__main__':
    try:
        main()
    except Exception, exc:
        print >>sys.stderr, 'Jug Error!'
        raise
# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
