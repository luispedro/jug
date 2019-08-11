#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (C) 2008-2019, Luis Pedro Coelho <luis@luispedro.org>
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

import sys

from .. import task
from ..jug import init
from . import SubCommand

__all__ = [
    'check',
    'sleep_until',
]


class CheckCommand(SubCommand):
    '''Returns 0 if all tasks are finished. 1 otherwise.

    check(store, options)

    Executes check subcommand

    Parameters
    ----------
    store : jug.backend
            backend to use
    options : jug options
    '''
    name = "check"

    def run(self, store, options, *args, **kwargs):
        sys.exit(_check_or_sleep_until(store, False))


class SleepUntilCommand(SubCommand):
    '''Wait until all tasks are done, then exit.

    sleep_until(store, options)

    Execute sleep-until subcommand

    Parameters
    ----------
    store : jug.backend
            backend to use
    options : jug options
        ignored
    '''
    name = "sleep-until"

    def run(self, options, store, jugspace, *args, **kwargs):
        while True:
            _check_or_sleep_until(store, True)
            hasbarrier = jugspace.get('__jug__hasbarrier__', False)
            if not hasbarrier:
                sys.exit(0)
            store, jugspace = init(options.jugfile, options.jugdir, store=store)


def _check_or_sleep_until(store, sleep_until):
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
        for dep in task.recursive_dependencies(t):
            try:
                active.remove(dep)
            except KeyError:
                pass
    return 0


check = CheckCommand()
sleep_until = SleepUntilCommand()
