#!/usr/bin/python
# Copyright (C) 2012-2026, Luis Pedro Coelho <luis@luispedro.org>
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

from html import escape

from . import status as st
from . import SubCommand


template = '''
<html>
<head>
  <meta http-equiv="refresh" content="%(refresh)s">
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
    <th>Failed</th>
    <th>Waiting</th>
    <th>Ready</th>
    <th>Complete</th>
    <th>Active</th>
</tr>
%(table)s
</table>
</body>
</html>
'''
_row_template = '''
<tr>
    <th class="task-name">{}</th>
    <td>{}</td>
    <td>{}</td>
    <td>{}</td>
    <td>{}</td>
    <td>{}</td>
</tr>'''


def _format_counts(ts):
    table = []
    names = set()
    for t in [ts.failed, ts.waiting, ts.ready, ts.running, ts.finished]:
        names.update(t)
    for n in sorted(names):
        table.append(
                _row_template.format(escape(n), ts.failed.get(n, 0), ts.waiting.get(n, 0), ts.ready.get(n, 0), ts.finished.get(n, 0), ts.running.get(n, 0)))
    table.append(_row_template.format('', '', '', '', '', ''))
    table.append(_row_template.format('Total',
                          sum(ts.failed.values()),
                          sum(ts.waiting.values()),
                          sum(ts.ready.values()),
                          sum(ts.finished.values()),
                          sum(ts.running.values())))
    return ''.join(table)


def _render_page(jugfile, refresh, ts):
    try:
        refresh = int(refresh)
    except (TypeError, ValueError):
        refresh = 3
    return template % {
        'jugfile': escape(jugfile),
        'refresh': refresh,
        'table': _format_counts(ts),
    }


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
    webstatus subcommand requires that bottle be installed (it could not be found).
    You can install it with:

        pip install bottle
    ''')
            return

        app = bottle.Bottle()
        @app.route('/')
        def status():
            ht, deps, rdeps = st.retrieve_sqlite3(connection)
            ts, dirty = st.update_status(store, ht, deps, rdeps)
            st.save_dirty3(connection, dirty)
            return _render_page(options.jugfile, request.query.refresh, ts)
        bottle.run(app, port=options.webstatus_port,
                   host=options.webstatus_ip, quiet=True)

    def parse(self, parser):
        defaults = self.parse_defaults()
        parser.add_argument('--port',
                            action='store',
                            dest='webstatus_port',
                            help=('Port for the webstatus server to listen on'
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
