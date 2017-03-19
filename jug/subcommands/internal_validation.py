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

from os import path
import logging
from . import SubCommand

__all__ = [
    'internal_validation',
]

# NOTE This module and function were originally called test_jug however
# after refactoring to subcommands nose would pick this module as a test and
# run it creating a test recursion.
#
# For this reason this module was renamed to internal_validation


class InternalValidationCommand(SubCommand):
    '''Run jug test suite (internal validation)
    '''
    name = "test-jug"

    def run(self, *args, **kwargs):
        try:
            import nose
        except ImportError:
            logging.critical('jug test requires nose library')
            return
        currentdir = path.dirname(__file__)
        updir = path.join(currentdir, '..')
        argv = ['', '--exe', '-w', updir]
        argv.append('--verbose')
        return nose.run('jug', argv=argv)


internal_validation = InternalValidationCommand()
