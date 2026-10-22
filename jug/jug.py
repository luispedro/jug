#!/usr/bin/python
# PYTHON_ARGCOMPLETE_OK
# Copyright (C) 2008-2026, Luis Pedro Coelho <luis@luispedro.org>
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
from .utils import prepare_matcher_from_options
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
    store, jugspace = init(jugfile=None, jugdir=None, on_error='exit', store=None)

    Initializes jug (create backend connection, ...).
    Imports jugfile

    The jugfile is registered in ``sys.modules`` under its module name (the
    filename without ``.py``), so that a subsequent ``import jugfile``
    returns the same module (even if a barrier was hit while loading it).

    Parameters
    ----------
    jugfile : str, optional
        jugfile to import (default: 'jugfile.py')
    jugdir : str, optional
        jugdir to use (could be a path). If not given, 'jugdata' is used (see
        ``set_jugdir``). Ignored if ``store`` is given.
    on_error : str, optional
        What to do if import fails: 'exit' (default) prints the error and exits
        the process, while 'propagate' re-raises the exception.
    store : storage object, optional
        If used, it is installed as the store for the tasks (``Task.store``)
        and returned as ``store`` again.

    Returns
    -------
    store : storage object
    jugspace : dictionary
    '''
    import types
    from .options import set_jugdir
    assert on_error in ('exit', 'propagate'), 'jug.init: on_error option is not valid.'

    if jugfile is None:
        jugfile = 'jugfile.py'
    # set_jugdir installs the store as Task.store (a store object is used as is)
    store = set_jugdir(jugdir if store is None else store)

    curdir = os.path.abspath('.')
    if curdir not in sys.path or curdir != sys.path[0]:
        sys.path.insert(0, curdir)

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
    jugmodule = types.ModuleType(jugmodname)
    jugmodule.__file__ = os.path.abspath(jugfile)
    jugspace = jugmodule.__dict__
    sys.modules[jugmodname] = jugmodule
    try:
        # Read bytes: compile() then decodes as Python source (UTF-8 by default,
        # honouring PEP 263 cookies) independently of the locale.
        with open(jugfile, 'rb') as jfile:
            exec(compile(jfile.read(), jugfile, 'exec'), jugspace, jugspace)
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


class ExecutionState:
    '''State kept across calls to ``execution_loop``

    ``jug execute`` calls ``execution_loop`` repeatedly when the jugfile has a
    barrier (re-loading the jugfile each time), and this state ensures that
    the waiting time is bounded overall and failed tasks are not retried.

    Attributes
    ----------
    nr_waits : int
        Number of wait cycles since the last progress (i.e., since a task was
        run or a dependency became available while waiting)
    failed : set of str
        Hashes of tasks that failed (they are not run again)
    '''
    def __init__(self):
        self.nr_waits = 0
        self.failed = set()


def execution_loop(tasks, options, state=None):
    '''Run the tasks in ``tasks`` (the core of ``jug execute``)

    Repeatedly picks tasks whose dependencies are available, locks them, runs
    them, and stores their results. If no task can be run, waits
    ``options.execute_wait_cycle_time`` seconds (up to
    ``options.execute_nr_wait_cycles`` times since the last progress) for
    other processes to finish dependencies before giving up.

    Parameters
    ----------
    tasks : list of Task
        Tasks to run (this list is modified)
    options : jug options
    state : ExecutionState, optional
        State shared with previous calls (by default, a new state is used)

    Returns
    -------
    failures : bool
        Whether any task raised an exception (only possible to return if
        ``options.execute_keep_going`` is set, otherwise the exception is
        propagated)
    '''
    from time import sleep

    logging.info(f'Execute start ({len(tasks)} tasks)')

    # If we are running with --name/--pattern, exclude non-matching tasks
    task_matcher = prepare_matcher_from_options(options.execute_name, options.execute_pattern)
    if task_matcher is not None:
        tasks = [t for t in tasks if task_matcher(t.name)]
        logging.info(f'Non-matching tasks discarded. Remaining ({len(tasks)} tasks)')

    # For the special (but common) case where most (if not all) of the tasks
    # can be loaded directly, just skip them as fast as possible:
    first_unloadable = 0
    while (first_unloadable < len(tasks)) and tasks[first_unloadable].can_load():
        jug_hook('execute.task-loadable', (tasks[first_unloadable],))
        first_unloadable += 1
    del tasks[:first_unloadable]

    if options.debug:
        start_task_set = {id(t) for t in task.alltasks}


    if state is None:
        state = ExecutionState()
    nr_wait_cycles = int(options.execute_nr_wait_cycles)
    failures = False
    prevtask = None
    while tasks:
        upnext = [] # tasks that can be run
        waited = False
        while True:
            first_runnable = next((ti for ti,t in enumerate(tasks) if t.can_run()), None)
            if first_runnable is not None:
                if waited:
                    # A dependency became available while waiting
                    state.nr_waits = 0
                # Move the tasks that cannot run to the end of the list.
                #
                # The argument for this is the following:
                # if T' is dependent on the result of T, it is better if the
                # processor that ran T, also runs T'. By having everyone else
                # push T' to the end of tasks, this is more likely to happen.
                #
                # Furthermore, this avoids always querying the same tasks.
                if first_runnable:
                    tasks[:] = tasks[first_runnable:] + tasks[:first_runnable]
                nr_runnable = 1
                while nr_runnable < len(tasks) and tasks[nr_runnable].can_run():
                    nr_runnable += 1
                upnext = tasks[:nr_runnable]
                del tasks[:nr_runnable]
                break
            if state.nr_waits >= nr_wait_cycles:
                break
            logging.info(f'waiting {options.execute_wait_cycle_time} secs for an open task...')
            sleep(float(options.execute_wait_cycle_time))
            state.nr_waits += 1
            waited = True
        if not upnext:
            logging.info('No tasks can be run!')
            break
        for t in upnext:
            if t.hash() in state.failed:
                # Failed in a previous call (before the jugfile was re-loaded)
                continue
            if t.can_load():
                jug_hook('execute.task-loadable', (t,))
                continue
            locked = False
            task_failed = False
            try:
                locked = t.lock()
                if t.can_load(): # This can be true if the task ran between the check above and this one
                    jug_hook('execute.task-loadable', (t,))
                elif locked:
                    logging.info(f'Executing {t.name}...')
                    jug_hook('execute.task-pre-execute', (t,))

                    if options.aggressive_unload:
                        if prevtask is not None:
                            active = {id(d) for d in t.dependencies()}
                            for d in itertools.chain(prevtask.dependencies(), [prevtask]):
                                if id(d) not in active:
                                    d.unload()
                        prevtask = t
                    state.nr_waits = 0
                    t.run(debug_mode=options.debug)
                    jug_hook('execute.task-executed1', (t,))
                    if options.debug:
                        for nt in task.alltasks:
                            if id(nt) not in start_task_set:
                                raise RuntimeError('Creating tasks while executing another task is not supported.\n'
                                            f'Error detected while running task `{t.name}`')
                else:
                    logging.info(f'Already in execution {t.name}...')
            except SystemExit:
                raise
            except Exception as e:
                failures = task_failed = True
                if locked:
                    # Only blacklist the task if we held its lock, i.e., if it
                    # was ours to run and it really failed. If acquiring the
                    # lock itself raised, the task never ran (and the lock may
                    # belong to another worker), so it must stay runnable for
                    # the next re-load of the jugfile.
                    state.failed.add(t.hash())

                if options.pdb:
                    from .internal.debugger import debug_exception
                    debug_exception()
                else:
                    logging.critical(f'Exception while running {t.name}: {e}')
                    for other in itertools.chain(upnext, tasks):
                        for dep in other.dependencies():
                            if dep is t:
                                logging.critical('Other tasks are dependent on this one! Parallel processors will be held waiting!')

                if options.execute_keep_failed and locked:
                    t.fail()

                if not options.execute_keep_going:
                    raise

            finally:
                if locked:
                    # We only keep the lock if task failed and keep_failed is enabled.
                    if not (task_failed and options.execute_keep_failed):
                        t.unlock()

            if options.aggressive_unload and prevtask is not None:
                prevtask.unload()

    return failures


def main(argv=None):
    '''Entry point for the ``jug`` command line script

    Parses the arguments, loads the jugfile (for subcommands which need it),
    runs the subcommand, and exits with its return value.

    Parameters
    ----------
    argv : list of str, optional
        Command line (including the program name). Defaults to ``sys.argv``
    '''
    global _is_jug_running
    _is_jug_running = True
    from .options import parse
    if argv is None:
        from sys import argv
    # The interface to `parse` requires us to skip the first element:
    options = parse(argv[1:])
    jugspace = None
    store = None


    try:
        if options.subcommand not in ('demo', 'install-skills', 'status', 'execute', 'webstatus', 'test-jug'):
            on_error = ('propagate' if options.pdb else 'exit')
            store, jugspace = init(options.jugfile, options.jugdir, on_error=on_error)
        from .subcommands import cmdapi
        retval = cmdapi.run(options.subcommand, options=options, store=store, jugspace=jugspace)
    except Exception:
        if options.pdb:
            from .internal.debugger import debug_exception
            debug_exception()
            retval = 1
        else:
            raise
    finally:
        if store is not None:
            store.close()
    sys.exit(retval)


def main_execute():
    '''Entry point for the ``jug-execute`` script (same as ``jug execute``)'''
    import sys
    args = sys.argv[:]
    args.insert(1, 'execute')
    return main(args)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        logging.critical('Unhandled Jug Error!')
        raise
