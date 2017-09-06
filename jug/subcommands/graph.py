#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (C) 2017, Renato Alves and Luis Pedro Coelho <luis@luispedro.org>
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
from sys import stderr
from .. import task
from . import SubCommand
from subprocess import check_call, CalledProcessError


__all__ = [
    'graph'
]


def handle_tasklet(tlet):
    '''Find the first non-Tasklet dependency and return its name'''
    dep = next(tlet.dependencies())

    if isinstance(dep, task.Tasklet):
        return handle_tasklet(dep)
    else:
        return dep.name


class GraphCommand(SubCommand):
    '''Graph: produce a diagram of task dependencies

    graph(store, options)

    Implement 'graph' command
    '''
    name = "graph"

    _label_template = (
        '"{name}" [label=<'
        "<table cellpadding='0' cellborder='0' border='0'>"
        "<tr><td colspan='5'>{name}</td></tr>"
        "<tr>"
        "<td><font color='#ff4080'><b>{failed}F</b></font></td>"
        "<td><font color='#f98cb6'><b>{waiting}W</b></font></td>"
        "<td><font color='#fca985'><b>{ready}R</b></font></td>"
        "<td><font color='#7589bf'><b>{active}A</b></font></td>"
        "<td><font color='#85ca5d'><b>{complete}C</b></font></td>"
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
                        "name": t.name,
                        "complete": 0,
                        "failed": 0,
                        "active": 0,
                        "ready": 0,
                        "waiting": 0,
                        "deps": set(),
                    }

                if t.can_load():
                    targets[t.name]["complete"] += 1
                elif t.can_run():
                    if t.is_locked():
                        if t.is_failed():
                            targets[t.name]["failed"] += 1
                        else:
                            targets[t.name]["active"] += 1
                    else:
                        targets[t.name]["ready"] += 1
                else:
                    targets[t.name]["waiting"] += 1

                for d in t.dependencies():
                    if isinstance(d, task.Tasklet):
                        # Tasklets don't have a name so we need to get one
                        # from higher in the dependency chain
                        dep_name = handle_tasklet(d)
                    else:
                        dep_name = d.name

                    targets[t.name]["deps"].add((dep_name, t.name))

            for name in targets:
                if options.graph_no_status:
                    fh.write('"{name}"\n'.format(**targets[name]))
                else:
                    fh.write(self._label_template.format(**targets[name]))

                for dep in targets[name]["deps"]:
                    fh.write('"{}" -> "{}"\n'.format(*dep))

            fh.write("}\n")

        error_msg = '''\
Couldn't render graph file. Is graphviz installed?
You will have to manually render the dotfile: {}
'''.format(dotfile)
        try:
            check_call(["dot", dotfile, "-T" + options.graph_format, "-o", jugfile + "." + options.graph_format])
        except FileNotFoundError:
            stderr.write(error_msg)
        except CalledProcessError:
            stderr.write(error_msg)

    def parse(self, parser):
        parser.add_argument("--no-status",
                            action="store_const", const=True,
                            dest="graph_no_status",
                            help="Disable inclusion of status information")
        parser.add_argument("--file-format",
                            action="store_const", const="png",
                            dest="graph_format",
                            help="Set format of graph output file (supported formats are the ones supported by the `dot` command)")

    def parse_defaults(self):
        return {
            "graph_no_status": False,
            "graph_format": "png",
        }


graph = GraphCommand()
