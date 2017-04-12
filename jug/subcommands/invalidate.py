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

from ..utils import prepare_task_matcher
from .. import task
from ..io import print_task_summary_table
from . import SubCommand

__all__ = [
    'invalidate'
]


class InvalidateCommand(SubCommand):
    '''Invalidate the results of a task

    invalidate(store, options)

    Implements 'invalidate' command

    Parameters
    ----------
    store : jug.backend
    options : options object
        Most relevant option is `invalid_name`, a string  with the exact (i.e.,
        module qualified) name of function to invalidate
    '''
    name = "invalidate"

    def run(self, store, options, *args, **kwargs):
        invalid_name = options.invalid_name
        tasks = task.alltasks
        cache = {}

        task_matcher = prepare_task_matcher(invalid_name)

        def isinvalid(t):
            if isinstance(t, task.Tasklet):
                return isinvalid(t.base)
            h = t.hash()
            if h in cache:
                return cache[h]
            if task_matcher(t.name):
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

    def parse(self, parser):
        parser.add_argument('--target', '--invalid', required=True, action='store',
                            dest='invalid_name',
                            help='Task name to invalidate')


invalidate = InvalidateCommand()
