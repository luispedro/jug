# -*- coding: utf-8 -*-
# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
# Copyright (C) 2010-2023, Luis Pedro Coelho <luis@luispedro.org>
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


def _can_load_limit_recursion(tsk, alltasks):
    # This is a hack to get around Python limitations with recursion (Python doesn't like it)

    # So, if we have a recursion error, we switch methods and first compute the
    # list of dependencies with an explicit stack (`q`). Then, we iterate over
    # the list of dependencies and trigger hash computation for each of the
    # dependencies. This should ensures that the next call to `can_load()`
    # returns immediately.

    try:
        return tsk.can_load()
    except RecursionError:
        dependencies = set()
        q = [tsk]
        while q:
            top = q.pop()
            ndeps = top.dependencies()
            ndeps = [t for t in ndeps if id(t) not in dependencies]
            q.extend(ndeps)
            dependencies.update(id(t) for t in ndeps)

        for t in alltasks:
            if id(t) in dependencies:
                t.__jug_hash__()
        return tsk.can_load()


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
        if not _can_load_limit_recursion(t, alltasks):
            raise BarrierError


def bvalue(t):
    '''
    value = bvalue(t)

    Named after ``barrier``+``value``, ``value = bvalue(t)`` is similar to::

        barrier()
        value = value(t)

    except that it only checks that `t` is complete (and not all tasks) and
    thus can be much faster than a full ``barrier()`` call.

    Thus, ``bvalue`` stops interpreting the Jugfile if its argument has not run
    yet. When it has run, then it returns its value.

    Example
    -------

    A typical use case is the following:

    1. split an input file into blocks of 1,000 lines
    2. process each of these blocks independently.

    You can use the following function to split the input::

        @TaskGenerator
        def split_input_file(ifile):
            splits = []
            output = None
            with open(ifile) as ifile:
                index = 0
                for i,line in enumerate(ifile):
                    if i % 1000 == 0:
                        if output is not None:
                            output.close()
                        ofile = 'splits.{}.txt'.format(index)
                        output = open(ofile, 'wt')
                        index += 1
                        splits.append(ofile)
                    output.write(line)
            if output is not None:
                output.close()
            return splits

        blocks = split_input_file('input.txt')

    And now, use ``bvalue`` to continue processing:


        for b in bvalue(blocks):
            process(b)

    The use of a barrier-type construct (such as ``bvalue``) is necessary for
    this case because you only know how many blocks you have **after running
    part of the pipeline**.


    See Also
    --------
    barrier : Checks that **all** tasks have results available.
    '''
    from .task import value
    try:
        return value(t)
    except:
        raise BarrierError

