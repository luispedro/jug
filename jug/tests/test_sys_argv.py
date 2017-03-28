# -*- coding: utf-8 -*-

import sys
import tempfile
from .task_reset import task_reset
from jug.jug import init
from jug.options import parse
from jug.subcommands.execute import execute
import json
from six import StringIO


class catch_stdout:
    def __enter__(self):
        sys.stdout = StringIO()
        return sys.stdout

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout.seek(0)
        sys.stdout = sys.__stdout__


@task_reset
def test_sys_argv():
    payload = """
import json, sys
sys.stdout.write(json.dumps(sys.argv) + '\\n')
"""
    jugfile = tempfile.NamedTemporaryFile(suffix=".py")
    jugfile.write(payload.encode("utf8"))
    jugfile.flush()

    options = parse(["execute", jugfile.name, '--', '--noarg', 'here'])
    assert sys.argv[0] == jugfile.name

    store, space = init(jugfile.name, 'dict_store')

    with catch_stdout() as stdout:
        execute.run(options=options, store=store, jugspace=space)

    output = stdout.readline()
    args = json.loads(output)
    expected = [jugfile.name, "--noarg", "here"]
    assert args == expected, "Saw {}, expected {}".format(args, expected)
