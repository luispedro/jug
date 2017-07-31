#!/usr/bin/python
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

import os
import sys
from .. import task
from . import SubCommand
from subprocess import check_call, CalledProcessError


__all__ = [
    'graph'
]


class GraphCommand(SubCommand):
    '''Graph: produce a diagram of task dependencies

    graph(store, options)

    Implement 'graph' command
    '''
    name = "graph"

    _label_template = (
        '"{}" [label=<'
        "<table cellpadding='0' cellborder='0' border='0'>"
        "<tr><td colspan='4'>{}</td></tr>"
        "<tr>"
        "<td><font color='#f98cb6'><b>{}</b></font></td>"
        "<td><font color='#fca985'><b>{}</b></font></td>"
        "<td><font color='#7589bf'><b>{}</b></font></td>"
        "<td><font color='#85ca5d'><b>{}</b></font></td>"
        "</tr>"
        "</table>"
        ">]\n"
    )

    def run(self, store, options, *args, **kwargs):
        jugfile = os.path.splitext(options.jugfile)[0]
        dotfile = jugfile + ".dot"

        with open(dotfile, 'w') as fh:
            fh.write("digraph {\n")

            targets = {}
            for t in task.alltasks:
                if t.name not in targets:
                    targets[t.name] = {
                        "finished": 0,
                        "running": 0,
                        "ready": 0,
                        "waiting": 0,
                        "deps": set(),
                    }

                if t.can_load():
                    targets[t.name]["finished"] += 1
                elif t.can_run():
                    if t.is_locked():
                        targets[t.name]["running"] += 1
                    else:
                        targets[t.name]["ready"] += 1
                else:
                    targets[t.name]["waiting"] += 1

                for d in t.dependencies():
                    targets[t.name]["deps"].add((d.name, t.name))

            for name in targets:
                if options.graph_no_status:
                    fh.write('"{}"\n'.format(name))
                else:
                    fh.write(self._label_template.format(
                        name, name,
                        targets[name]["waiting"],
                        targets[name]["ready"],
                        targets[name]["running"],
                        targets[name]["finished"],
                    ))

                for dep in targets[name]["deps"]:
                    fh.write('"{}" -> "{}"\n'.format(*dep))

            fh.write("}\n")

        try:
            check_call(["dot", dotfile, "-Tpng", "-o", "jugfile.png"])
        except CalledProcessError:
            sys.stderr.write("Couldn't render graph file. Is graphviz installed?\n")
            sys.stderr.write("You will have to manually render the dotfile\n")

    def parse(self, parser):
        parser.add_argument("--no-status",
                            action="store_const", const=True,
                            dest="graph_no_status",
                            help="Disable inclusion of status information")

    def parse_defaults(self):
        return {
            "graph_no_status": False,
        }


graph = GraphCommand()
