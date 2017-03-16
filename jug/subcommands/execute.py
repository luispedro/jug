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
import logging
import sys

from .. import task
from ..hooks import jug_hook, register_hook, register_hook_once
from ..io import print_task_summary_table
from ..jug import init
from . import subcommand


__all__ = [
    'execute'
]


def _sigterm(_, __):
    sys.exit(1)


def _log_loadable(t):
    logging.info('Loadable {0}...'.format(t.name))


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


def execute(options, *args, **kwargs):
    '''Execute tasks

    execute(options)

    Implement 'execute' command
    '''
    from signal import signal, SIGTERM
    from ..jug import execution_loop

    signal(SIGTERM, _sigterm)
    tasks = task.alltasks
    tstats = TaskStats()
    store = None
    register_hook_once('execute.task-loadable', '_log_loadable', _log_loadable)

    nr_wait_cycles = int(options.execute_nr_wait_cycles)
    noprogress = 0
    while noprogress < nr_wait_cycles:
        del tasks[:]
        store, jugspace = init(options.jugfile, options.jugdir, store=store)
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


def execute_options(parser):
    wait_cycle_time = 12

    parser.add_argument('--wait-cycle-time', action='store', dest='execute_wait_cycle_time_secs',
                        metavar='WAIT_CYCLE_TIME_SECS', default=wait_cycle_time,
                        help="How long to wait in each cycle (in seconds)")
    parser.add_argument('--nr-wait-cycles', action='store', dest='execute_nr_wait_cycles',
                        metavar='NR_WAIT_CYCLES', default=(30 * 60) // wait_cycle_time,
                        help="How many wait cycles to do")
    parser.add_argument('--target', action='store', dest='execute_target',
                        metavar='TARGET', default=None,
                        help="Restrict tasks to execute based on their name")
    parser.add_argument('--keep-going', action='store_true', dest='execute_keep_going',
                        help='Continue after errors')


subcommand.register("execute", execute, execute_options)
