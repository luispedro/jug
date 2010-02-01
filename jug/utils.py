# -*- coding: utf-8 -*-
# Copyright (C) 2009-2010, Luis Pedro Coelho <lpc@cmu.edu>
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

from __future__ import division
import os

from .task import Task

def _return_first(one, two):
    '''
    one = _return_first(one, two)

    Used internally to implement jug.util.timed_path
    '''
    return one

def timed_path(path):
    '''
    opath = timed_path(ipath)

    Returns a Task object that simply returns `path` with the exception that it uses the
    paths mtime (modification time) in the hash. Thus, if the file contents change, this triggers
    an invalidation of the results (which propagates).

    Parameters
    ----------
    `ipath` : A filesystem path

    Returns
    -------
    `opath` : A task equivalent to (lambda: ipath) 
    '''
    mtime = os.stat_result(os.stat(path)).st_mtime
    return Task(_return_first, path, mtime)

