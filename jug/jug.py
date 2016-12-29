#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (C) 2008-2016, Luis Pedro Coelho <luis@luispedro.org>
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
import sys
import os
import os.path
import re
import logging
import itertools

from . import task
from .task import Task
from .hooks import jug_hook, register_hook, register_hook_once
from .io import print_task_summary_table
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

    print_task_summary_table(options, [("Count", task_counts)])

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

    invalid = list(filter(isinvalid, tasks))
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
        print_task_summary_table(options, [("Invalidated", task_counts)])

def _sigterm(_,__):
    sys.exit(1)

def execution_loop(tasks, options):
    from time import sleep

    logging.info('Execute start (%s tasks)' % len(tasks))

    # For the special (but common) case where most (if not all) of the tasks
    # can be loaded directly, just skip them as fast as possible:
    first_unloadable = 0
    while (first_unloadable < len(tasks)) and tasks[first_unloadable].can_load():
        t = tasks[first_unloadable]
        jug_hook('execute.task-loadable', (tasks[first_unloadable],))
        first_unloadable += 1
    del tasks[:first_unloadable]

    prevtask = None
    while tasks:
        upnext = [] # tasks that can be run
        nr_wait_cycles = int(options.execute_nr_wait_cycles)
        for i in range(nr_wait_cycles):
            max_cannot_run = min(len(tasks), 128)
            if i == nr_wait_cycles - 1:
                # in the last loop iteration, check all tasks to ensure we don't miss any
                max_cannot_run = len(tasks)
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
            for ti,t in enumerate(tasks):
                if t.can_run():
                    upnext.append(tasks.pop(ti))
                    break
            if upnext:
                break
            logging.info('waiting %s secs for an open task...' % options.execute_wait_cycle_time_secs)
            sleep(int(options.execute_wait_cycle_time_secs))
        if not upnext:
            logging.info('No tasks can be run!')
            break
        for t in upnext:
            if t.can_load():
                jug_hook('execute.task-loadable', (t,))
                continue
            locked = False
            try:
                locked = t.lock()
                if t.can_load(): # This can be true if the task ran between the check above and this one
                    jug_hook('execute.task-loadable', (t,))
                elif locked:
                    logging.info('Executing %s...' % t.name)
                    jug_hook('execute.task-pre-execute', (t,))

                    if options.aggressive_unload:
                        if prevtask is not None:
                            active = set([id(d) for d in t.dependencies()])
                            for d in itertools.chain(prevtask.dependencies(), [prevtask]):
                                if id(d) not in active:
                                    d.unload()
                        prevtask = t
                    t.run(debug_mode=options.debug)
                    jug_hook('execute.task-executed1', (t,))
                else:
                    logging.info('Already in execution %s...' % t.name)
            except SystemExit:
                raise
            except Exception as e:
                if options.pdb:
                    import sys
                    _,_, tb = sys.exc_info()

                    # The code below is a complex attempt to load IPython
                    # debugger which works with multiple versions of IPython.
                    #
                    # Unfortunately, their API kept changing prior to the 1.0.
                    try:
                        import IPython
                        try:
                            import IPython.core.debugger
                            try:
                                from IPython.terminal.ipapp import load_default_config
                                config = load_default_config()
                                colors = config.TerminalInteractiveShell.colors
                            except:
                                import IPython.core.ipapi
                                ip = IPython.core.ipapi.get()
                                colors = ip.colors
                            try:
                                debugger = IPython.core.debugger.Pdb(colors.get_value(initial='Linux'))
                            except AttributeError:
                                debugger = IPython.core.debugger.Pdb(colors)
                        except ImportError:
                            #Fallback to older version of IPython API
                            import IPython.ipapi
                            import IPython.Debugger
                            shell = IPython.Shell.IPShell(argv=[''])
                            ip = IPython.ipapi.get()
                            debugger = IPython.Debugger.Pdb(ip.options.colors)
                    except ImportError:
                        #Fallback to standard debugger
                        import pdb
                        debugger = pdb.Pdb()

                    debugger.reset()
                    debugger.interaction(None, tb)
                else:
                    logging.critical('Exception while running %s: %s' % (t.name,e))
                    for other in itertools.chain(upnext, tasks):
                        for dep in other.dependencies():
                            if dep is t:
                                logging.critical('Other tasks are dependent on this one! Parallel processors will be held waiting!')
                if not options.execute_keep_going:
                    raise
            finally:
                if locked: t.unlock()
            if options.aggressive_unload and prevtask is not None:
                prevtask.unload()

class TaskStats(object):
    def __init__(self):
        self.loaded = defaultdict(int)
        self.executed = defaultdict(int)
        register_hook('execute.task-loadable', self.loadable)
        register_hook('execute.task-executed1', self.executed1)

    def loadable(self, t):
        self.loaded[t.name] += 1
    def executed1(self, t):
        self.executed[t.name] += 1

def _log_loadable(t):
    logging.info('Loadable {0}...'.format(t.name))

def execute(options):
    '''
    execute(options)

    Implement 'execute' command
    '''
    from signal import signal, SIGTERM

    signal(SIGTERM,_sigterm)
    tasks = task.alltasks
    tstats = TaskStats()
    store = None
    register_hook_once('execute.task-loadable', '_log_loadable', _log_loadable)

    nr_wait_cycles = int(options.execute_nr_wait_cycles)
    noprogress = 0
    while noprogress < nr_wait_cycles:
        del tasks[:]
        store,jugspace = init(options.jugfile, options.jugdir, store=store)
        if options.debug:
            for t in tasks:
                # Trigger hash computation:
                t.hash()

        previous = sum(tstats.executed.values())
        execution_loop(tasks, options)
        after = sum(tstats.executed.values())
        done = not jugspace.get('__jug__hasbarrier__', False)
        if done:
            break
        if after == previous:
            from time import sleep
            noprogress += 1
            sleep(int(options.execute_wait_cycle_time_secs))
        else:
            noprogress = 0
    else:
        logging.info('No tasks can be run!')


    jug_hook('execute.finished_pre_status')
    print_task_summary_table(options, [("Executed", tstats.executed), ("Loaded", tstats.loaded)])
    jug_hook('execute.finished_post_status')

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
    jugfile_contents = open(jugfile).read()
    try:
        exec(compile(jugfile_contents, jugfile, 'exec'), jugspace, jugspace)
    except BarrierError:
        jugspace['__jug__hasbarrier__'] = True
    except Exception as e:
        logging.critical("Could not import file '%s' (error: %s)", jugfile, e)
        if on_error == 'exit':
            import traceback
            print(traceback.format_exc())
            sys.exit(1)
        else:
            raise

    # The store may have been changed by the jugfile.
    store = Task.store
    return store, jugspace


def main(argv=None):
    from .options import parse
    if argv is None:
        from sys import argv
    options = parse(argv[1:])
    store = None
    if options.cmd not in ('status', 'execute', 'webstatus', 'test-jug'):
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
    elif options.cmd == 'test-jug':
        try:
            import nose
        except ImportError:
            logging.critical('jug test requires nose library')
            return
        from os import path
        currentdir = path.dirname(__file__)
        updir = path.join(currentdir, '..')
        argv = ['', '--exe', '-w', updir]
        argv.append('--verbose')
        return nose.run('jug', argv=argv)
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
