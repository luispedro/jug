#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (C) 2008-2020, Luis Pedro Coelho <luis@luispedro.org>
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


def _get_debugger():
    '''
    Get a debugger object
    '''
    # The code below is a complex attempt to load IPython
    # debugger which works with multiple versions of IPython.
    #
    # Unfortunately, their API kept changing prior to version 1.0.
    try:
        import IPython
        try:
            import IPython.core.debugger
            try:
                from IPython.terminal.ipapp import load_default_config
                config = load_default_config()
                colors = config.TerminalInteractiveShell.colors
            except:
                import IPython.core.ipapi
                ip = IPython.core.ipapi.get()
                colors = ip.colors
            try:
                return IPython.core.debugger.Pdb(colors.get_value(initial='Linux'))
            except AttributeError:
                return IPython.core.debugger.Pdb(colors)
        except ImportError:
            #Fallback to older version of IPython API
            import IPython.ipapi
            import IPython.Debugger
            shell = IPython.Shell.IPShell(argv=[''])
            ip = IPython.ipapi.get()
            return IPython.Debugger.Pdb(ip.options.colors)
    except ImportError:
        #Fallback to standard debugger
        import pdb
        return pdb.Pdb()


def debug_exception():
    '''
    Start a debugger on the exception currently being handled
    '''
    import sys

    _,_, tb = sys.exc_info()
    debugger = _get_debugger()
    debugger.reset()
    debugger.interaction(None, tb)
