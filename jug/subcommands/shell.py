#!/usr/bin/python
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


import sys
from ..task import value

def load_all(jugfile):
    '''
    load_all(jugfile)

    Loads the result of all tasks.
    '''
    for elem in dir(jugfile):
        try:
            v = value(getattr(jugfile, elem))
            setattr(jugfile, elem, v)
        except Exception, e:
            print 'Error while loading %s: %s' % (elem, e)


def shell(store, jugmodule):
    '''
    shell(store, jugmodule)

    Implement 'shell' command.

    Currently depends on Ipython being installed.
    '''
    try:
        from IPython.Shell import IPShellEmbed
    except ImportError:
        print >>sys.stderr, '''\
jug: Error: could not import IPython libraries

IPython is necessary for `shell` command.
'''
        sys.exit(1)

    def _load_all():
        '''
        load_all()

        Loads all task results.
        '''
        load_all(jugmodule)

    if jugmodule is None:
        print >>sys.stderr, '''\
jug shell only works correctly only all the barriers have passed.'''
        jugfilename = '<jugfile>'
        msg = 'The jugfile is UNAVAILABLE.'
    else:
        jugfilename = jugmodule.__name__
        if jugfilename == 'jugfile':
            msg = 'The jugfile is available as `jugfile`.'
        else:
            msg = 'The jugfile is available as `jugfile` and as `%s`.' % jugfilename


    ipshell = IPShellEmbed(banner='''
=========
Jug Shell
=========

%s

Available jug functions:
    - value() : loads a specific object
    - load_all() : loads all objects

Enjoy...
''' % msg)

    local_ns = {
        'jugfile' : jugmodule,
        jugfilename : jugmodule,
        'load_all' : _load_all,
        'value' : value,
    }
    ipshell(local_ns=local_ns)


