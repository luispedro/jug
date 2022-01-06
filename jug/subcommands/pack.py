#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (C) 2022, Luis Pedro Coelho <luis@luispedro.org>
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
    'pack',
]


class PackCommand(SubCommand):
    '''Returns 0 if all tasks are finished. 1 otherwise.

    pack(store, options)

    Executes pack subcommand

    Parameters
    ----------
    store : jug.backend
            backend to use
    options : jug options
    '''
    name = "pack"

    def run(self, store, options, *args, **kwargs):
        if not hasattr(store, 'update_pack'):
            from sys import stderr, exit
            stderr.write("Cannot pack this store (only basic file-based jugdata directories can be packed)")
            exit(1)
        packed = store.update_pack()
        options.print_out('Packed {packed} objects'.format(packed=packed))


pack = PackCommand()
