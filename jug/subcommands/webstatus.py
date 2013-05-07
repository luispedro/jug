#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (C) 2012, Luis Pedro Coelho <luis@luispedro.org>
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

from . import status as st

template = '''
<html>
<head>

<title>Jug Status :: %(jugfile)s</title>
<style>
body {
    width: 80%%;
    margin: auto;
    margin-top: 2em;
    font-family: sans-serif;
}
H1 {
    color: #D95550;
}
H1 .jugfile {
    color: #647704;
}

TH {
    color: #6d2243;
}
</style>
</head>
<body>
<h1>Jug Status for <span class="jugfile">%(jugfile)s</span></h1>
<table>
<tr>
    <th>Task Name</th>
    <th>Waiting</th>
    <th>Ready</th>
    <th>Completed</th>
    <th>Executing</th>
</tr>
%(table)s
</table>
</body>
'''
_row_template = '''
<tr>
    <th>%s</th>
    <td>%s</td>
    <td>%s</td>
    <td>%s</td>
    <td>%s</td>
</tr>'''


def _format_counts(tw, tre, tru, tf):
    r = ''
    names = set()
    for t in [tw,tre,tru,tf]:
        names.update(list(t.keys()))
    for n in names:
        r += _row_template % (n, tw[n], tre[n], tru[n], tf[n])
    r += _row_template % ('', '', '', '', '')
    r += _row_template % ('Total',
                                sum(tw.values()),
                                sum(tre.values()),
                                sum(tru.values()),
                                sum(tf.values()))
    return r


def webstatus(options):
    import sqlite3
    connection = sqlite3.connect(':memory:', check_same_thread=False)
    store, ht, deps, rdeps = st.load_jugfile(options)
    st.create_sqlite3(connection, ht, deps, rdeps)

    try:
        import web
    except ImportError:
        from sys import stderr
        stderr.write('''
webstatus subcommand requires that web.py be installed (it could not be found).
You can try one of the following commands to install it:

    pip install web.py

or

    easy_install web.py
''')
        return
    urls = (
        '/(.*)', 'status'
    )
    class Status(object):
        def GET(self, name):
            ht, deps, rdeps = st.retrieve_sqlite3(connection)
            tw,tre,tru,tf,dirty = st.update_status(store, ht, deps, rdeps)
            st.save_dirty3(connection, dirty)
            return template % {
                    'jugfile' : options.jugfile,
                    'table' : _format_counts(tw, tre, tru, tf),
            }
    app = web.application(urls, {'status': Status})
    app.run()
