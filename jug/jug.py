#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (C) 2008-2017, Luis Pedro Coelho <luis@luispedro.org>
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


import itertools
import logging
import os
import sys


from . import task
from .barrier import BarrierError
from .utils import prepare_task_matcher
from .hooks import jug_hook


_is_jug_running = False
def is_jug_running():
    '''
    Returns True if this script is being executed by jug instead of regular
    Python
    '''
    return _is_jug_running


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
    store = task.Task.store
    return store, jugspace


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

    if options.debug:
        start_task_set = set([id(t) for t in task.alltasks])

    # If we are running with a target, exclude non-matching tasks
    if options.execute_target:
        task_matcher = prepare_task_matcher(options.execute_target)
        tasks = [t for t in tasks if task_matcher(t.name)]
        logging.info('Non-matching tasks discarded. Remaining (%s tasks)' % len(tasks))

    failures = False
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
            logging.info('waiting %s secs for an open task...' % options.execute_wait_cycle_time)
            sleep(int(options.execute_wait_cycle_time))
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
                    if options.debug:
                        for nt in task.alltasks:
                            if id(nt) not in start_task_set:
                                raise RuntimeError('Creating tasks while executing another task is not supported.\n'
                                            'Error detected while running task `{0}`'.format(t.name))
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
                else:
                    failures = True
            finally:
                if locked:
                    t.unlock()
            if options.aggressive_unload and prevtask is not None:
                prevtask.unload()

    return failures


def main(argv=None):
    global _is_jug_running
    _is_jug_running = True
    from .options import parse
    if argv is None:
        from sys import argv
    options = parse()
    jugspace = None
    store = None

    if options.subcommand not in ('demo', 'status', 'execute', 'webstatus', 'test-jug'):
        store, jugspace = init(options.jugfile, options.jugdir)

    from .subcommands import cmdapi
    cmdapi.run(options.subcommand, options=options, store=store, jugspace=jugspace)

    if store is not None:
        store.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        logging.critical('Unhandled Jug Error!')
        raise
