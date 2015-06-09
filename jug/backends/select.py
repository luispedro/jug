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


from . import redis_store
from . import file_store
from .dict_store import dict_store

def select(jugdir):
    '''
    store = select(jugdir)

    Returns a store object appropriate for `jugdir`

    Parameters
    ----------
    jugdir : str
            representation of jugdir, as a pseudo-URI.
            If something other than a string is passed, then the function just
            returns its argument.

    Returns
    -------
      store : A jug data store
    '''
    if type(jugdir) != str:
        return jugdir
    if jugdir.startswith('redis:'):
       return redis_store.redis_store(jugdir)
    if jugdir == 'dict_store':
        return dict_store()
    if jugdir.startswith('dict_store:'):
        return dict_store(jugdir[len('dict_store:'):])
    return file_store.file_store(jugdir)

