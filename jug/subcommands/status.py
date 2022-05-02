#!/usr/bin/python
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

from collections import defaultdict, namedtuple
from contextlib import contextmanager

import jug
from .. import task
from .. import backends
from ..task import Task
from ..backends import memoize_store
from ..io import print_task_summary_table
from . import SubCommand

__all__ = [
    'status'
]


unknown = 'unknown'
waiting = 'waiting'
ready = 'ready'
running = 'running'
failed = 'failed'
finished = 'finished'


def create_sqlite3(connection, ht, deps, rdeps):
    connection.executescript('''
    CREATE TABLE ht (
            id INTEGER PRIMARY KEY,
            name CHAR(128),
            hash CHAR(128),
            status CHAR(32));
    CREATE TABLE dep (
        source INT,
        target INT);
    ''')

    connection.executemany('INSERT INTO ht VALUES(?,?,?,?)', ht)

    for i, cdeps in deps.items():
        if len(cdeps):
            connection.executemany('''
               INSERT INTO dep(source, target) VALUES(?,?)
                ''', [(i, cd) for cd in cdeps])


def retrieve_sqlite3(connection):
    '''
    Retrieves status from an SQLite3 DB

    Parameters
    ----------

    connection: DB connection

    Returns
    -------
    ht : status list. See Table ht
    dep : dict
        dependencies
    rdep : dict
        reverse dependencies
    '''
    ht = connection. \
            execute('SELECT * FROM ht ORDER BY id'). \
            fetchall()
    deps = defaultdict(list)
    rdeps = defaultdict(list)
    for d0, d1 in connection.execute('SELECT * FROM dep'):
        deps[d0].append(d1)
        rdeps[d1].append(d0)
    return ht, dict(deps), dict(rdeps)


def save_dirty3(connection, dirty):
    connection.executemany('UPDATE ht SET STATUS = ? WHERE id = ?', [(nstatus, id) for id, nstatus in dirty.items()])


@contextmanager
def _open_connection(options):
    '''Opens sqlite3 connection as a context manager
    '''
    import sqlite3
    connection = sqlite3.connect(options.status_cache_file)
    yield connection
    connection.commit()
    connection.close()


def load_jugfile(options):
    store, _ = jug.init(options.jugfile, options.jugdir)
    h2idx = {}
    ht = []
    deps = {}
    try:
        for i, t in enumerate(task.alltasks):
            deps[i] = [h2idx[d.hash() if isinstance(d, Task) else d._base_hash()]
                       for d in t.dependencies()]
            hash = t.hash()
            ht.append((i, t.name, hash, unknown))
            h2idx[hash] = i
    except KeyError:
        import sys
        sys.stderr.write("Could not build dependency graph!\n")
        sys.stderr.write("This normally indicates a bug in your code!\n")
        sys.stderr.write("\n")
        sys.stderr.write("A common error is to build a Task with a mutable argument and subsequently modifying.\n")
        sys.stderr.write("\n")
        sys.stderr.write("For help, you can use the jug-users mailing-list: https://groups.google.com/g/jug-users\n")
        sys.stderr.write("\n")

        sys.exit(1)

    rdeps = defaultdict(list)
    for k, v in deps.items():
        for rv in v:
            rdeps[rv].append(k)
    return store, ht, deps, dict(rdeps)


class TaskStatus:
    def __init__(self):
        self.failed=defaultdict(int)
        self.waiting=defaultdict(int)
        self.ready=defaultdict(int)
        self.running=defaultdict(int)
        self.finished=defaultdict(int)


def update_status(store, ht, deps, rdeps):
    ts = TaskStatus()

    store = memoize_store(store, list_base=True)
    dirty = {}
    for i, name, hash, status in ht:
        nstatus = None
        if status == finished or store.can_load(hash):
            ts.finished[name] += 1
            nstatus = finished
        else:
            can_run = True
            if status != ready:
                for dep in deps.get(i, []):
                    _, _, dhash, dstatus = ht[dep]
                    if dstatus != finished and not store.can_load(dhash):
                        can_run = False
                        break
            if can_run:
                lock = store.getlock(hash)
                if lock.is_locked():
                    if lock.is_failed():
                        ts.failed[name] += 1
                        nstatus = failed
                    else:
                        ts.running[name] += 1
                        nstatus = running
                else:
                    ts.ready[name] += 1
                    nstatus = ready
            else:
                ts.waiting[name] += 1
                nstatus = waiting
        assert nstatus is not None, 'update_status: nstatus not assigned'
        if status != nstatus:
            dirty[i] = nstatus
    return ts, dirty


def _print_status(options, ts):
    if options.short:
        n_ready = sum(ts.ready.values())
        n_running = sum(ts.running.values())
        n_failed = sum(ts.failed.values())
        n_waiting = sum(ts.waiting.values())
        n_finished = sum(ts.finished.values())
        if not n_waiting and not n_running and not n_failed and not n_ready:
            options.print_out('All tasks complete ({0} tasks).'.format(n_finished))
        elif not n_running:
            options.print_out('{0} tasks waiting to be run, {1} failed, {2} complete, (none active).'.format(n_waiting + n_ready, n_failed, n_finished))
        else:
            options.print_out('{0} tasks waiting to be run, {1} failed, {2} complete, ({3} active).'.format(n_waiting + n_ready, n_failed, n_finished, n_running))
    else:
        print_task_summary_table(options, [
                                ("Failed", ts.failed),
                                ("Waiting", ts.waiting),
                                ("Ready", ts.ready),
                                ("Complete", ts.finished),
                                ("Active", ts.running)])


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

    ts, dirty = update_status(store, ht, deps, rdeps)
    _print_status(options, ts)
    if mode == update:
        with _open_connection(options) as connection:
            save_dirty3(connection, dirty)
    else:
        for k in dirty:
            _, name, hash, _ = ht[k]
            ht[k] = (k, name, hash, dirty[k])
        with _open_connection(options) as connection:
            create_sqlite3(connection, ht, deps, rdeps)
    return sum(ts.finished.values())


def _status_nocache(options):
    store, _ = jug.init(options.jugfile, options.jugdir)
    Task.store = memoize_store(store, list_base=True)

    ts = TaskStatus()

    for t in task.alltasks:
        if t.can_load():
            ts.finished[t.name] += 1
        elif t.can_run():
            if t.is_locked():
                if t.is_failed():
                    ts.failed[t.name] += 1
                else:
                    ts.running[t.name] += 1
            else:
                ts.ready[t.name] += 1
        else:
            ts.waiting[t.name] += 1
    _print_status(options, ts)
    return sum(ts.finished.values())


class StatusCommand(SubCommand):
    '''Print status

    status(options)

    Implements the status command.

    Parameters
    ----------
    options : jug options
    '''
    name = "status"

    def run(self, options, *args, **kwargs):
        if options.status_cache:
            try:
                import sqlite3
            except ImportError:
                from sys import stderr
                stderr.write('Cached status relies on sqlite3. Falling back to non-cached version')
                options.status_cache = False
                return status(options)
            if options.status_cache_clear:
                return _clear_cache(options)
            return _status_cached(options)
        else:
            return _status_nocache(options)

    def parse(self, parser):
        defaults = self.parse_defaults()

        parser.add_argument('--cache',
                            action='store_const', const=True,
                            dest='status_cache',
                            help='Use a cache for faster status [does not update after jugfile changes, though]')

        parser.add_argument('--cache-file',
                            action='store', metavar="CACHE_FILE",
                            dest='status_cache_file',
                            help=('Name of file to use for status cache. Use with status --cache. '
                                  '(Default: {status_cache_file}'.format(**defaults)))
        parser.add_argument('--clear',
                            action='store_const', const=True,
                            dest='status_cache_clear',
                            help='Use with status --cache. Removes the cache file')

    def parse_defaults(self):
        return {
            "status_cache": False,
            "status_cache_clear": False,
            "status_cache_file": ".jugstatus.sqlite3",
        }


status = StatusCommand()
