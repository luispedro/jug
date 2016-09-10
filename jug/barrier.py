# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
# Copyright (C) 2010-2012, Luis Pedro Coelho <luis@luispedro.org>
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

'''
See more complete documentation at

https://jug.readthedocs.io/en/latest/barrier.html
'''

class BarrierError(Exception):
    '''
    Used to represent a barrier() violation
    '''
    pass

def barrier():
    '''
    barrier()

    In a jug file, it assures that all tasks defined up to now have been
    completed. If not, parsing will (temporarily) stop at that point.

    This ensures that, after calling ``barrier()`` you are free to call
    ``value()`` to get any needed results.

    See Also
    --------
    bvalue : function
        Restricted version of this function. Often faster
    '''
    # The reason to import here instead of at module level is that if some
    # other code does
    # jug.task.alltasks = []
    # we would still be referring to the old version
    from .task import alltasks
    for t in reversed(alltasks):
        if not t.can_load():
            raise BarrierError


def bvalue(t):
    '''
    value = bvalue(t)

    Named after ``barrier``+``value``, this function Works similarly to::

        barrier()
        value = value(t)

    except that it only checks that `t` is complete (and not all tasks) and
    thus can be much faster than a full ``barrier()`` call.

    See Also
    --------
    barrier : Checks that **all** tasks have results available.
    '''
    from .task import value
    try:
        return value(t)
    except:
        raise BarrierError

