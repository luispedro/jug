#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (C) 2012-2022, Luis Pedro Coelho <luis@luispedro.org>
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
from . import SubCommand


template = '''
<html>
<head>
<head>
  <meta http-equiv="refresh" content="%(refresh)s">
</head>
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

TH.task-name {
    text-align: left;
    padding-right: 2em;
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
    <th>Executing</th>
    <th>Completed</th>
</tr>
%(table)s
</table>
</body>
'''
_row_template = '''
<tr>
    <th class="task-name">{}</th>
    <td>{}</td>
    <td>{}</td>
    <td>{}</td>
    <td>{}</td>
</tr>'''


def _format_counts(ts):
    table = []
    names = set()
    for t in [ts.waiting, ts.ready, ts.running, ts.finished]:
        names.update(list(t.keys()))
    for n in names:
        table.append(
                _row_template.format(n, ts.waiting[n], ts.ready[n], ts.running[n], ts.finished[n]))
    table.append(_row_template.format('', '', '', '', ''))
    table.append(_row_template.format('Total',
                          sum(ts.waiting.values()),
                          sum(ts.ready.values()),
                          sum(ts.running.values()),
                          sum(ts.finished.values())))
    return ''.join(table)


class WebStatusCommand(SubCommand):
    '''Start a web interface which displays the status
    '''
    name = "webstatus"

    def run(self, options, *args, **kwargs):
        import sqlite3
        connection = sqlite3.connect(':memory:', check_same_thread=False)
        store, ht, deps, rdeps = st.load_jugfile(options)
        st.create_sqlite3(connection, ht, deps, rdeps)

        try:
            import bottle
            from bottle import request
        except ImportError:
            from sys import stderr
            stderr.write('''
    webstatus subcommand requires that web.py be installed (it could not be found).
    You can try one of the following commands to install it:

        pip install bottle

    or

        easy_install bottle
    ''')
            return

        app = bottle.Bottle()
        @app.route('/')
        def status():
            ht, deps, rdeps = st.retrieve_sqlite3(connection)
            ts, dirty = st.update_status(store, ht, deps, rdeps)
            st.save_dirty3(connection, dirty)
            return template % {
                'jugfile': options.jugfile,
                'refresh': request.query.refresh or "3",
                'table': _format_counts(ts),
            }
        bottle.run(app, port=options.webstatus_port,
                   host=options.webstatus_ip, quiet=True)

    def parse(self, parser):
        defaults = self.parse_defaults()
        parser.add_argument('--port',
                            action='store',
                            dest='webstatus_port',
                            help=('Port for the webstatus serve to listen on'
                                  ' (Default: 8080)')
        )
        parser.add_argument('--ip',
                            action='store',
                            dest='webstatus_ip',
                            help=('The IP address the webstatus server will listen on.'
                                  ' (Default: localhost)')
        )

    def parse_defaults(self):
        return {
            "webstatus_port": '8080',
            "webstatus_ip": 'localhost'
        }


webstatus = WebStatusCommand()
