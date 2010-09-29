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
from jug import Task
from itertools import chain

def _jug_map_reduce(reducer, mapper, inputs):
     return reduce(reducer, map(mapper, inputs))
def _jug_reduce(reducer, inputs):
    return reduce(reducer, chain(inputs))

def _break_up(lst, step):
    start = 0
    next = step
    while start < len(lst):
        yield lst[start:next]
        start = next
        next += step

def mapreduce(reducer, mapper, inputs, map_step=4, reduce_step=8):
    '''
    task = mapreduce(reducer, mapper, inputs, map_step=4, reduce_step=8)

    Create a task that does roughly the following::

        reduce(reducer, map(mapper, inputs))

    Roughly because the order of operations might be different. In particular,
    `reducer` should be a true `reducer` functions (i.e., commutative and
    associative).

    Parameters
    ----------
    reducer : associative, commutative function
            This should map
                  Y_0,Y_1 -> Y'
    mapper : function from X -> Y
    inputs : list of X

    map_step : integer, optional
            Number of mapping operations to do in one go.
            This is what defines an inner task. (default: 4)
    reduce_step : integer, optional
            Number of reduce operations to do in one go.
            (default: 8)

    Returns
    -------
    task : jug.Task object
    '''
    reducers = [Task(_jug_map_reduce, reducer, mapper, input_i) for input_i in _break_up(inputs, map_step)]
    while len(reducers) > 1:
        reducers = [Task(_jug_reduce, reducer, reduce_i) for reduce_i in _break_up(reducers, reduce_step)]
    return reducers[0]

