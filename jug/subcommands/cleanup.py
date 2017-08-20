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

from .. import task
from . import SubCommand

__all__ = [
    'cleanup'
]


class CleanupCommand(SubCommand):
    '''Cleanup: remove result files that are not used

    cleanup(store, options)

    Implement 'cleanup' command
    '''
    name = "cleanup"

    def run(self, store, options, *args, **kwargs):

        if options.cleanup_locks_only:
            removed = store.remove_locks()
        elif options.cleanup_failed_only:
            removed = 0
            for name in list(store.listlocks()):
                lock = store.getlock(name)
                if lock.is_failed():
                    lock.release()
                    removed += 1
        else:
            tasks = task.alltasks
            removed = store.cleanup(tasks, keeplocks=options.cleanup_keep_locks)

        options.print_out('Removed %s files' % removed)

    def parse(self, parser):
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--locks-only',
                           action='store_const', const=True,
                           dest='cleanup_locks_only',
                           help="Cleanup locks leaving computed results untouched")
        group.add_argument('--failed-only',
                           action='store_const', const=True,
                           dest='cleanup_failed_only',
                           help="Cleanup failed locks leaving computed results and active locks untouched")
        group.add_argument('--keep-locks',
                           action='store_const', const=True,
                           dest='cleanup_keep_locks',
                           help="Cleanup unused results leaving locks untouched")

    def parse_defaults(self):
        return {
            "cleanup_keep_locks": False,
            "cleanup_failed_only": False,
            "cleanup_locks_only": False,
        }


cleanup = CleanupCommand()
