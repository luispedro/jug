#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (C) 2008-2016, Luis Pedro Coelho <luis@luispedro.org>
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
    for k,v in jugspace.items():
        # ignore objects name like __this__
        if k.startswith('__') and k.endswith('__'): continue
        try:
            local_ns[k] = value(v)
        except Exception as e:
            print('Error while loading %s: %s' % (k, e))

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
        import IPython
        if IPython.version_info[0]>=1:
            from IPython.terminal.embed import InteractiveShellEmbed
            from IPython.terminal.ipapp import load_default_config
        else:
            from IPython.frontend.terminal.embed import InteractiveShellEmbed
            from IPython.frontend.terminal.ipapp import load_default_config
        config = load_default_config()
        ipshell = InteractiveShellEmbed(config=config, display_banner=_ipython_banner)
    except ImportError:
        try:
            # Fallback for older Python:
            from IPython.Shell import IPShellEmbed
            ipshell = IPShellEmbed(banner=_ipython_banner)
        except ImportError:
            import sys
            sys.stderr.write(_ipython_not_found_msg)
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

    jugspace.update(local_ns)
    local_ns['__name__'] = '__jugfile__'
    if IPython.version_info[0] >= 5:
        from sys import modules

        # This is tricky, but the following WOULD NOT work:
        #  for mod in modules.values():
        #     ..
        # Some modules use https://pypi.python.org/pypi/apipkg which triggers
        # name loading when __dict__ is accessed. This may itself import other
        # modules, thus raising an error: "RuntimeError: dictionary changed
        # size during iteration" Whether this happens depends on exactly which
        # modules the user uses/has loaded

        modules = list(modules.values())
        for mod in modules:
            if getattr(mod, '__dict__', None) is jugspace:
                break
        else:
            raise KeyError("Could not find jug module")
        ipshell(module=mod, local_ns=local_ns)
    else:
        ipshell(global_ns=jugspace, local_ns=local_ns)
