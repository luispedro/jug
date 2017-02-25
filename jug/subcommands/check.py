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

import sys

from .. import task
from . import subcommand

__all__ = [
    'check',
    'sleep_until',
]


def check(store, options, *args, **kwargs):
    '''Returns 0 if all tasks are finished. 1 otherwise.

    check(store, options)

    Executes check subcommand

    Parameters
    ----------
    store : jug.backend
            backend to use
    options : jug options
    '''
    sys.exit(_check_or_sleep_until(store, False))


def sleep_until(store, options, *args, **kwargs):
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
    sys.exit(_check_or_sleep_until(store, True))


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


subcommand.register("check", check)
subcommand.register("sleep-until", sleep_until)
