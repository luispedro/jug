#!/usr/bin/python
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

from collections import defaultdict

from ..utils import prepare_matcher_from_options, add_task_selection_options
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
        Most relevant options are `invalid_name`, a string with the name of
        the function to invalidate (either module qualified or not; may
        contain wildcards), and `invalid_pattern`, a looser match (substring
        or /regex/). At least one must be given.
    '''
    name = "invalidate"

    def run(self, store, options, *args, **kwargs):
        task_matcher = prepare_matcher_from_options(options.invalid_name, options.invalid_pattern)
        if task_matcher is None:
            raise ValueError('jug invalidate: one of invalid_name or invalid_pattern must be given')
        tasks = task.alltasks
        cache = {}

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
        removed = store.remove_many(t.hash() for t in invalid)
        for t in invalid:
            if t.hash() in removed:
                task_counts[t.name] += 1
        if sum(task_counts.values()) == 0:
            options.print_out('Tasks invalidated, but no results removed')
        else:
            print_task_summary_table(options, [("Invalidated", task_counts)])

    def parse(self, parser):
        add_task_selection_options(parser, 'invalid_name', 'invalid_pattern',
                                   required=True, what='Invalidate tasks')


invalidate = InvalidateCommand()
