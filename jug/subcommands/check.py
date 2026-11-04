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

import sys

from .. import task
from ..jug import init
from ..utils import (prepare_matcher_from_options, add_task_selection_options,
                     add_task_exclusion_options)
from . import SubCommand

__all__ = [
    'check',
    'sleep_until',
]


def _add_selection_options(parser, prefix, what, verb):
    add_task_selection_options(parser, f'{prefix}_name', f'{prefix}_pattern',
                               required=False, what=f'Only {what} tasks')
    add_task_exclusion_options(parser, f'{prefix}_exclude_name', f'{prefix}_exclude_pattern',
                               what=verb)


def _selection_defaults(prefix):
    return {
        f'{prefix}_name': None,
        f'{prefix}_pattern': None,
        f'{prefix}_exclude_name': [],
        f'{prefix}_exclude_pattern': [],
    }


def _matcher_from_options(options, prefix):
    return prepare_matcher_from_options(
                getattr(options, f'{prefix}_name', None),
                getattr(options, f'{prefix}_pattern', None),
                exclude_names=getattr(options, f'{prefix}_exclude_name', None),
                exclude_patterns=getattr(options, f'{prefix}_exclude_pattern', None))


def _no_match_error(command):
    sys.stderr.write(
        f'jug {command}: no task matches the given --name/--pattern/--exclude-* '
        'options.\n')
    return 1


class CheckCommand(SubCommand):
    '''Returns 0 if all tasks are finished. 1 otherwise.

    Executes check subcommand

    With ``--name``/``--pattern`` (and ``--exclude-name``/``--exclude-pattern``),
    only the matching tasks are checked. As tasks after a ``barrier()`` are not
    known, 1 is returned if loading the jugfile stopped at a barrier. If no task
    matches, 1 is returned (and an error message is printed).

    Parameters
    ----------
    store : jug.backend
            backend to use
    options : jug options
    '''
    name = "check"

    def run(self, store, options, *args, **kwargs):
        jugspace = kwargs.get('jugspace') or {}
        if jugspace.get('__jug__hasbarrier__', False):
            sys.exit(1)
        matcher = _matcher_from_options(options, 'check')
        if matcher is not None and not _select(matcher):
            sys.exit(_no_match_error(self.name))
        sys.exit(_check_or_sleep_until(store, False, matcher))

    def parse(self, parser):
        _add_selection_options(parser, 'check', 'check', 'check')

    def parse_defaults(self):
        return _selection_defaults('check')


class SleepUntilCommand(SubCommand):
    '''Wait until all tasks are done, then exit.

    Execute sleep-until subcommand

    If the jugfile contains barriers, it is re-imported (using
    ``options.jugfile`` and ``options.jugdir``) whenever all the tasks seen so
    far are done, until no barrier is hit.

    With ``--name``/``--pattern`` (and ``--exclude-name``/``--exclude-pattern``),
    only waits for the matching tasks. However, while loading the jugfile
    stops at a barrier, matching tasks may be defined after it, so all the
    tasks before the barrier are waited for (so that the barrier is passed).
    If no task matches (and no barrier was hit), it exits with 1 (and prints
    an error message).

    Parameters
    ----------
    store : jug.backend
            backend to use
    options : jug options
    '''
    name = "sleep-until"

    def run(self, options, store, jugspace, *args, **kwargs):
        matcher = _matcher_from_options(options, 'sleep_until')
        while True:
            hasbarrier = jugspace.get('__jug__hasbarrier__', False)
            if hasbarrier:
                # Wait for all the tasks (not just the matching ones) so that
                # the barrier is passed when the jugfile is re-loaded
                _check_or_sleep_until(store, True)
            else:
                if matcher is not None and not _select(matcher):
                    sys.exit(_no_match_error(self.name))
                _check_or_sleep_until(store, True, matcher)
                sys.exit(0)
            del task.alltasks[:]
            store, jugspace = init(options.jugfile, options.jugdir, store=store)

    def parse(self, parser):
        _add_selection_options(parser, 'sleep_until', 'wait for', 'wait for')

    def parse_defaults(self):
        return _selection_defaults('sleep_until')


def _select(matcher):
    '''Returns the tasks in ``task.alltasks`` whose name matches'''
    return [t for t in task.alltasks if matcher(t.name)]


def _check_or_sleep_until(store, sleep_until, matcher=None):
    '''Check (or wait) that all tasks (or those matching ``matcher``) are done

    Returns 0 if they are all done, 1 otherwise (only if ``sleep_until`` is
    false; otherwise, it waits until they are all done).
    '''
    tasks = task.alltasks if matcher is None else _select(matcher)
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
            active.discard(dep)
    return 0


check = CheckCommand()
sleep_until = SleepUntilCommand()
