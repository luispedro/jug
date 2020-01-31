#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (C) 2008-2020, Luis Pedro Coelho <luis@luispedro.org>
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
from . import SubCommand, maybe_print_citation_info


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


class ExecuteCommand(SubCommand):
    '''Execute tasks

    execute(options)

    Implement 'execute' command
    '''
    name = "execute"

    def run(self, options, *args, **kwargs):
        from signal import signal, SIGTERM
        from ..hooks.exit_checks import exit_env_vars, exit_if_file_exists
        from ..jug import execution_loop

        signal(SIGTERM, _sigterm)
        if not options.execute_no_check_environment:
            exit_env_vars()
            exit_if_file_exists('__jug_please_stop_running.txt')

        tasks = task.alltasks
        tstats = TaskStats()
        store = None
        register_hook_once('execute.task-loadable', '_log_loadable', _log_loadable)

        nr_wait_cycles = int(options.execute_nr_wait_cycles)
        noprogress = 0
        failures = False
        while noprogress < nr_wait_cycles:
            del tasks[:]
            store, jugspace = init(options.jugfile, options.jugdir, store=store)
            if options.debug:
                for t in tasks:
                    # Trigger hash computation:
                    t.hash()

            previous = sum(tstats.executed.values())
            failures = execution_loop(tasks, options) or failures
            after = sum(tstats.executed.values())
            done = not jugspace.get('__jug__hasbarrier__', False)
            if done:
                break
            if after == previous:
                from time import sleep
                noprogress += 1
                sleep(int(options.execute_wait_cycle_time))
            else:
                noprogress = 0
        else:
            logging.info('No tasks can be run!')

        jug_hook('execute.finished_pre_status')
        maybe_print_citation_info(options)
        print_task_summary_table(options, [("Executed", tstats.executed), ("Loaded", tstats.loaded)])
        jug_hook('execute.finished_post_status')

        if failures:
            sys.exit(1)

    def parse(self, parser):
        defaults = self.parse_defaults()

        parser.add_argument('--wait-cycle-time', action='store', dest='execute_wait_cycle_time',
                            metavar='WAIT_CYCLE_TIME', type=int,
                            help=("How long to wait in each cycle (in seconds) "
                                  "(Default: {execute_wait_cycle_time})".format(**defaults)))
        parser.add_argument('--nr-wait-cycles', action='store',
                            dest='execute_nr_wait_cycles',
                            metavar='NR_WAIT_CYCLES', type=int,
                            help=("How many wait cycles to do "
                                  "(Default: {execute_nr_wait_cycles})".format(**defaults)))
        parser.add_argument('--target', action='store', dest='execute_target',
                            metavar='TARGET',
                            help="Restrict tasks to execute based on their name")
        parser.add_argument('--keep-going',
                            action='store_const', const=True,
                            dest='execute_keep_going',
                            help='Continue after errors')
        parser.add_argument('--keep-failed',
                            action='store_const', const=True,
                            dest='execute_keep_failed',
                            help='Keep failed tasks locked')
        parser.add_argument('--no-check-environment',
                            action='store_const', const=True,
                            dest='execute_no_check_environment',
                            help='Do not check environment variables JUG_* and file __jug_please_stop_running.txt')

    def parse_defaults(self):
        wait_cycle_time = 12

        default_values = {
            "execute_keep_going": False,
            "execute_keep_failed": False,
            "execute_target": None,
            "execute_wait_cycle_time": wait_cycle_time,
            "execute_nr_wait_cycles": (30 * 60) // wait_cycle_time,
            "execute_no_check_environment": False,
        }

        return default_values


execute = ExecuteCommand()
