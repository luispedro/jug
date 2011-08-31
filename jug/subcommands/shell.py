#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (C) 2008-2010, Luis Pedro Coelho <luis@luispedro.org>
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


from ..task import value

def load_all(jugspace, local_ns):
    '''
    load_all(jugspace, local_ns)

    Loads the result of all tasks.
    '''
    for k,v in jugspace.iteritems():
        # ignore objects name like __this__
        if k.startswith('__') and k.endswith('__'): continue
        try:
            local_ns[k] = value(v)
        except Exception, e:
            print 'Error while loading %s: %s' % (k, e)

_ipython_not_found_msg = '''\
jug: Error: could not import IPython libraries

IPython is necessary for `shell` command.
'''
_ipython_banner = '''
=========
Jug Shell
=========


Available jug functions:
    - value() : loads a specific object
    - load_all() : loads all objects

Enjoy...
'''

def shell(store, options, jugspace):
    '''
    shell(store, options, jugspace)

    Implement 'shell' command.

    Currently depends on Ipython being installed.
    '''
    try:
        from IPython.Shell import IPShellEmbed
        ipshell = IPShellEmbed(banner=_ipython_banner)
    except ImportError:
        try:
            # From ipython v0.11, the interface changed.
            # So we try the new interface too
            from IPython.frontend.terminal.embed import InteractiveShellEmbed
            ipshell = InteractiveShellEmbed(display_banner=_ipython_banner)
        except ImportError:
            import sys
            print >>sys.stderr, _ipython_not_found_msg
            sys.exit(1)

    def _load_all():
        '''
        load_all()

        Loads all task results.
        '''
        load_all(jugspace, local_ns)

    local_ns = {
        'load_all' : _load_all,
        'value' : value,
    }
    # This is necessary for some versions of Ipython. See:
    # http://groups.google.com/group/pylons-discuss/browse_thread/thread/312e3ead5967468a
    try:
        del jugspace['__builtins__']
    except KeyError:
        pass

    local_ns.update(jugspace)
    ipshell(global_ns=jugspace, local_ns=local_ns)

