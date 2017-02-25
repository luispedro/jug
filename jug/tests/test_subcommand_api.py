# -*- coding: utf-8 -*-

import os
import tempfile
import shutil
from jug.subcommands import subcommand

CMD = "hello-cmd"
MSG = "Hello world"


def hello_command(*args, **kwargs):
    "This should be visible"
    return MSG


def clear_cmds():
    subcommand._commands.clear()
    assert CMD not in subcommand._commands


def test_register():
    clear_cmds()

    subcommand.register(CMD, hello_command)
    output = subcommand.run(CMD)

    assert output == MSG, "Expected: '%s' , got: '%s'" % (MSG, output)


def test_user_commands():
    clear_cmds()

    payload = """
from jug.subcommands import subcommand

def hello_command(*args, **kwargs):
    "This should be visible"
    return "This TEST"

subcommand.register("hello-cmd", hello_command)
"""
    userfile = "jug_user_commands.py"
    tmpdir = tempfile.mkdtemp(prefix="jug")
    with open(os.path.join(tmpdir, userfile), 'w') as fh:
        fh.write(payload)

    subcommand._load_user_commands(user_path=tmpdir)
    assert CMD in subcommand._commands, "Expected: '%s' to be in '%s'" % (CMD, subcommand._commands)

    output = subcommand.run(CMD)
    assert output == "This TEST"

    shutil.rmtree(tmpdir)


def test_usage():
    clear_cmds()

    subcommand.register(CMD, hello_command)
    output = subcommand.usage(_print=False, exit=False)

    assert "This should be visible" in output

# vim: ai sts=4 et sw=4
