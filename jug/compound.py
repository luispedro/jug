# -*- coding: utf-8 -*-
# Copyright (C) 2008-2010, Luis Pedro Coelho <lpc@cmu.edu>
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
from .task import Task, alltasks

def compound_task_execute(x, h):
    '''
    compound_task_execute

    This is an internal function. Do **not** use directly.
    '''
    Task.store.dump(x, h)
    return x

def CompoundTask(f, *args, **kwargs):
    '''
    task = CompoundTask(f, *args, **kwargs)

    `f` should be such that it returns a `Task`, which can be as complex as it
    wants.

    If `f` cannot been loaded, then this becomes equivalent to
        f(*args, **kwargs)
    However, if it can, then we get a pseudo-task which returns the same value
    without `f` ever being executed.

    Parameters
    ----------
      f : A function returning a `Task`
    Returns
    -------
      task : A `Task`
    '''
    task = Task(f, *args, **kwargs)
    if task.can_load():
        return task
    h = task.hash()
    inner = f(*args, **kwargs)
    del alltasks[alltasks.index(task)]
    del task
    return Task(compound_task_execute, inner, h)

