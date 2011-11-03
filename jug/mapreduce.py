# -*- coding: utf-8 -*-
# Copyright (C) 2008-2010, Luis Pedro Coelho <luis@luispedro.org>
# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
# License : MIT

'''
mapreduce: Build tasks that follow a map-reduce pattern.
'''

from __future__ import division
from jug import Task
from .utils import identity
from itertools import chain
import operator

__all__ = [
    'mapreduce',
    'map',
    'reduce',
    ]

def _jug_map_reduce(reducer, mapper, inputs):
    import __builtin__
    return __builtin__.reduce(reducer, __builtin__.map(mapper, inputs))
def _jug_reduce(reducer, inputs):
    import __builtin__
    return __builtin__.reduce(reducer, chain(inputs))

def _break_up(lst, step):
    start = 0
    next = step
    while start < len(lst):
        yield lst[start:next]
        start = next
        next += step

class _jug_map(object):
    def __init__(self, mapper):
        self.mapper = mapper
    def __call__(self, e):
        return [self.mapper(e)]

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
    if len(reducers) == 0:
        return identity([])
    elif len(reducers) == 1:
        return reducers[0]
    else:
        assert False, 'This is a bug'

def map(mapper, sequence, map_step=4):
    '''
    sequence' = map(mapper, sequence, map_step=4)

    Roughly equivalent to::

        sequence' = [Task(mapper,s) for s in sequence]

    except that the tasks are grouped in groups of `map_step`

    Parameters
    ----------
    mapper : function
        functions from A -> B
    sequence : list of A
    map_step : integer, optional
        nr of elements to process per task. This should be set so that each
        task takes the right amount of time.

    Returns
    -------
    sequence' : list of B
        sequence'[i] = mapper(sequence[i])

    See Also
    --------
    mapreduce
    '''
    return mapreduce(operator.add, _jug_map(mapper), sequence, map_step=map_step, reduce_step=(len(sequence)//map_step+1))

def reduce(reducer, inputs, reduce_step=8):
    '''
    task = reduce(reducer, inputs, reduce_step=8)

    Parameters
    ----------
    reducer : associative, commutative function
            This should map
                  Y_0,Y_1 -> Y'
    inputs : list of X
    reduce_step : integer, optional
            Number of reduce operations to do in one go.
            (default: 8)

    Returns
    -------
    task : jug.Task object

    See Also
    --------
    mapreduce
    '''
    return mapreduce(reducer, None, inputs, reduce_step=reduce_step)

