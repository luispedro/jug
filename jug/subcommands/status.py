#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (C) 2008-2015, Luis Pedro Coelho <luis@luispedro.org>
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
from contextlib import contextmanager

import jug
from .. import task
from .. import backends
from ..task import Task
from ..backends import memoize_store
from ..io import print_task_summary_table

__all__ = [
    'status'
    ]

unknown = 'unknown'
waiting = 'waiting'
ready = 'ready'
running = 'running'
finished = 'finished'

def create_sqlite3(connection, ht, deps, rdeps):
    connection.executescript('''
    CREATE TABLE ht (
            id INTEGER PRIMARY KEY,
            name CHAR(128),
            hash CHAR(128),
            status INT);
    CREATE TABLE dep (
        source INT,
        target INT);
    ''')

    connection.executemany('INSERT INTO ht VALUES(?,?,?,?)', ht)

    for i,cdeps in deps.items():
        if len(cdeps):
            connection.executemany('''
               INSERT INTO dep(source, target) VALUES(?,?)
                ''', [(i,cd) for cd in cdeps])

def retrieve_sqlite3(connection):
    ht = connection. \
            execute('SELECT * FROM ht ORDER BY id'). \
            fetchall()
    deps = defaultdict(list)
    rdeps = defaultdict(list)
    for d0,d1 in connection.execute('SELECT * FROM dep'):
        deps[d0].append(d1)
        rdeps[d1].append(d0)
    return ht, dict(deps), dict(rdeps)

def save_dirty3(connection, dirty):
    connection.executemany('UPDATE ht SET STATUS = ? WHERE id = ?', [(nstatus,id) for id,nstatus in dirty.items()])

@contextmanager
def _open_connection(options):
    import sqlite3
    connection = sqlite3.connect(options.status_cache_file)
    yield connection
    connection.commit()
    connection.close()


def load_jugfile(options):
    store,_ = jug.init(options.jugfile, options.jugdir)
    h2idx = {}
    ht = []
    deps = {}
    for i,t in enumerate(task.alltasks):
        deps[i] = [h2idx[d.hash() if isinstance(d,Task) else d._base_hash()]
                        for d in t.dependencies()]
        hash = t.hash()
        ht.append( (i, t.name, hash, unknown) )
        h2idx[hash] = i

    rdeps = defaultdict(list)
    for k,v in deps.items():
        for rv in v:
            rdeps[rv].append(k)
    return store, ht, deps, dict(rdeps)


def update_status(store, ht, deps, rdeps):
    tasks_waiting = defaultdict(int)
    tasks_ready = defaultdict(int)
    tasks_running = defaultdict(int)
    tasks_finished = defaultdict(int)

    store = memoize_store(store, list_base=True)
    dirty = {}
    for i,name,hash,status in ht:
        nstatus = None
        if status == finished or store.can_load(hash):
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
        assert nstatus is not None, 'update_status: nstatus not assigned'
        if status != nstatus:
            dirty[i] = nstatus
    return tasks_waiting, tasks_ready, tasks_running, tasks_finished, dirty


def _print_status(options, waiting, ready, running, finished):
    if options.short:
        n_ready = sum(ready.values())
        n_running = sum(running.values())
        n_waiting = sum(waiting.values())
        n_finished = sum(finished.values())
        if not n_waiting and not n_running and not n_ready:
            options.print_out('All finished ({0} tasks).'.format(n_finished))
        elif not n_running:
            options.print_out('{0} tasks to be run, {1} finished, (none running).'.format(n_waiting + n_ready, n_finished))
        else:
            options.print_out('{0} tasks to be run, {1} finished, ({2} running).'.format(n_waiting + n_ready, n_finished, n_running))
    else:
        print_task_summary_table(options, [
                                ("Waiting", waiting),
                                ("Ready", ready),
                                ("Finished", finished),
                                ("Running", running)])


def _clear_cache(options):
    from os import unlink
    try:
        unlink(options.status_cache_file)
    except:
        pass

def _status_cached(options):
    create, update = list(range(2))
    try:
        with _open_connection(options) as connection:
            ht, deps, rdeps = retrieve_sqlite3(connection)
        store = backends.select(options.jugdir)
        mode = update
    except:
        store, ht, deps, rdeps = load_jugfile(options)
        mode = create

    tw,tre,tru,tf,dirty = update_status(store, ht, deps, rdeps)
    _print_status(options, tw, tre, tru, tf)
    if mode == update:
        with _open_connection(options) as connection:
            save_dirty3(connection, dirty)
    else:
        for k in dirty:
            _,name,hash,_ = ht[k]
            ht[k] = (k, name, hash, dirty[k])
        with _open_connection(options) as connection:
            create_sqlite3(connection, ht, deps, rdeps)
    return sum(tf.values())


def _status_nocache(options):
    store,_ = jug.init(options.jugfile, options.jugdir)
    Task.store = memoize_store(store, list_base=True)

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
    return sum(tasks_finished.values())


def status(options):
    '''
    status(options)

    Implements the status command.

    Parameters
    ----------
    options : jug options
    '''
    if options.status_mode == 'cached':
        try:
            import sqlite3
        except ImportError:
            from sys import stderr
            stderr.write('Cached status relies on sqlite3. Falling back to non-cached version')
            options.status_mode = 'no-cache'
            return status(options)
        if options.status_cache_clear:
            return _clear_cache(options)
        return _status_cached(options)
    else:
        return _status_nocache(options)
