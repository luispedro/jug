# -*- coding: utf-8 -*-
# Copyright (C) 2024, Luis Pedro Coelho <luis@luispedro.org>
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

__all__ = [
    'NoHash',
    ]

class NoHash:
    '''
    Class that indicates that no hashing is to be done on an object.

    This is useful when you want to indicate that the object should not be
    hashed as its value is not important.

    For example, if you are using jug_execute and one of the arguments is the
    number of CPUs:

    ::

        jug_execute(['make', '-j', NoHash(4)])

    This way, the number of CPUs is not hashed and the task will be **not** be
    rerun if the number of CPUs changes.

    Parameters
    ----------
    obj : any object
    '''
    def __init__(self, obj):
        self.obj = obj

    def __jug_value__(self):
        return self.obj

    def __jug_hash__(self):
        return b'nohash'

