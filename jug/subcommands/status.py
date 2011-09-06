#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (C) 2008-2010, Luis Pedro Coelho <luis@luispedro.org>
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

from collections import defaultdict
import sqlite3

import jug
from ..task import recursive_dependencies
from .. import task
from .. import backends
from ..task import Task
from ..backends import memoize_store

unknown,waiting,ready,running,finished = range(5)
_jugstatus_file = '.jugstatus.sqlite3'

def _create_sqlite3(ht, deps, rdeps):
    connection = sqlite3.connect(_jugstatus_file)
    connection.execute('''
    CREATE TABLE ht (
            id INTEGER PRIMARY KEY,
            name CHAR(128),
            hash CHAR(128),
            status INT );
    ''')
    connection.execute('''
    CREATE TABLE dep (
        source INT,
        target INT);
    ''')

    for h in ht:
        connection.execute('''
       INSERT INTO ht(name, hash, status) VALUES(?,?,?)
    ''', (h[1], h[2], h[3]))

    for i,cdeps in deps.iteritems():
        for cd in cdeps:
            connection.execute('''
           INSERT INTO dep(source, target) VALUES(?,?)
            ''', (i,cd))
    connection.commit()
    connection.close()

def _retrieve_sqlite3():
    connection = sqlite3.connect(_jugstatus_file)
    cursor = connection.execute('''SELECT * FROM ht''')
    ht = cursor.fetchall()
    cursor = connection.execute('''SELECT * FROM dep''')
    deps = defaultdict(list)
    rdeps = defaultdict(list)
    for d0,d1 in cursor:
        deps[d0].append(d1)
        rdeps[d1].append(d0)
    return ht, deps, rdeps

def _save_dirty3(dirty):
    connection = sqlite3.connect(_jugstatus_file)
    for id,status in dirty:
        connection.execute('''UPDATE ht SET STATUS = ? WHERE id = ?''', (status, id))
    connection.commit()


def _load_jugfile(options):
    store,_ = jug.init(options.jugfile, options.jugdir)
    h2idx = {}
    ht = []
    deps = {}
    rdeps = {}
    for i,t in enumerate(task.alltasks):
        hash = t.hash()
        curdeps = []
        for dep in t.dependencies():
            if type(dep) is Task:
                h = dep.hash()
            else:
                h = dep._base_hash()
            curdeps.append(h2idx[h])
        if curdeps:
            deps[i] = curdeps
        h = [i, t.name, hash, unknown]
        ht.append(h)
        h2idx[hash] = i

    for k,v in deps.iteritems():
        for rv in v:
            if rv not in rdeps:
                rdeps[rv] = [k]
            else:
                rdeps[rv].append(k)
    return store, ht, deps, rdeps


def _update_status(store, ht, deps, rdeps):
    tasks_waiting = defaultdict(int)
    tasks_ready = defaultdict(int)
    tasks_running = defaultdict(int)
    tasks_finished = defaultdict(int)

    store = memoize_store(store, list_base=True)
    dirty = []
    active = []
    for h in ht:
        _,name,hash,status = h
        if status == finished:
            tasks_finished[name] += 1
        else:
            active.append(h)

    for i,name,hash,status in active:
        nstatus = None
        if store.can_load(hash):
            tasks_finished[name] += 1
            nstatus = finished
        else:
            can_run = True
            if status != ready:
                for dep in deps.get(i, []):
                    _,_,dhash,dstatus = ht[dep]
                    if dstatus != finished and not store.can_load(dhash):
                        can_run = False
                        break
            if can_run:
                lock = store.getlock(hash)
                if lock.is_locked():
                    tasks_running[name] += 1
                    nstatus = running
                else:
                    tasks_ready[name] += 1
                    nstatus = ready
            else:
                tasks_waiting[name] += 1
                nstatus = waiting
        assert nstatus is not None, '_update_status: nstatus not assigned'
        if status != nstatus:
            dirty.append((i,nstatus))
    return tasks_waiting, tasks_ready, tasks_running, tasks_finished, dirty


def _print_status(options, waiting, ready, running, finished):
    names = set(waiting.keys())
    names.update(ready.keys())
    names.update(running.keys())
    names.update(finished.keys())
    format      = '%-40s%12s%12s%12s%12s'
    format_size =    40 +12 +12 +12 +12
    options.print_out(format % ('Task name','Waiting','Ready','Finished','Running'))
    options.print_out('-' * format_size)

    for n in sorted(names):
        n_cut = n[:40]
        options.print_out(format % (n_cut,waiting[n],ready[n],finished[n],running[n]))
    options.print_out('.' * format_size)
    options.print_out(format % ('Total:',sum(waiting.values()),sum(ready.values()),sum(finished.values()),sum(running.values())))
    options.print_out()


def _status_cached(options):
    create, update = range(2)
    try:
        ht, deps, rdeps = _retrieve_sqlite3()
        store = backends.select(options.jugdir)
        mode = update
    except:
        store, ht, deps, rdeps = _load_jugfile(options)
        mode = create

    tw,tre,tru,tf,dirty = _update_status(store, ht, deps, rdeps)
    _print_status(options, tw, tre, tru, tf)
    if mode == update:
        _save_dirty3(dirty)
    else:
        for i,nstatus in dirty:
            _,name,hash,_ = ht[i]
            ht[i] = (i, name, hash, nstatus)
        _create_sqlite3(ht, deps, rdeps)


def _status_nocache(options):
    store,_ = jug.init(options.jugfile, options.jugdir)
    Task.store = memoize_store(store, list_base=True)

    task_names = set(t.name for t in task.alltasks)
    tasks_waiting = defaultdict(int)
    tasks_ready = defaultdict(int)
    tasks_running = defaultdict(int)
    tasks_finished = defaultdict(int)
    for t in task.alltasks:
        if t.can_load():
            tasks_finished[t.name] += 1
        elif t.can_run():
            if t.is_locked():
                tasks_running[t.name] += 1
            else:
                tasks_ready[t.name] += 1
        else:
            tasks_waiting[t.name] += 1
    _print_status(options, tasks_waiting, tasks_ready, tasks_running, tasks_finished)


def status(options):
    '''
    status(options)

    Implements the status command.

    Parameters
    ----------
    options : jug options
    '''
    if options.status_mode == 'cached':
        _status_cached(options)
    else:
        _status_nocache(options)
