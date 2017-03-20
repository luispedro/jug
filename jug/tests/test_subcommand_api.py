# -*- coding: utf-8 -*-

import os
import tempfile
import shutil
from six import StringIO
from jug.subcommands import subcommand
from jug.options import parse

CMD = "hello-cmd"
MSG = "Hello world"
MSG_OPTIONS = "Hello world - option ated"


def hello_command(*args, **kwargs):
    "This should be visible"
    return MSG


def hello_command_opts(options, *args, **kwargs):
    "This should be visible"
    return MSG + " - " + options.hello_value


def hello_options(parser):
    parser.add_argument("--value", dest="hello_value", action="store")
    parser.add_argument("--other-value", dest="hello_other_value", action="store")

    default_values = {
        "hello_value": "option ated",
        "hello_other_value": "undefined",
    }

    return default_values


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

    subcommand._commands._load_user_commands(user_path=tmpdir)
    assert CMD in subcommand._commands, "Expected: '%s' to be in '%s'" % (CMD, subcommand._commands)

    output = subcommand.run(CMD)
    assert output == "This TEST"

    shutil.rmtree(tmpdir)


def test_options():
    clear_cmds()

    subcommand.register(CMD, hello_command_opts, hello_options)
    options = parse([CMD])
    output = subcommand.run(CMD, options=options)

    assert output == MSG_OPTIONS, "Expected: '%s' , got: '%s'" % (MSG_OPTIONS, output)


_options_file = '''
[hello]
other-value=someone
'''


def test_options_config():
    clear_cmds()

    subcommand.register(CMD, hello_command_opts, hello_options)
    options = parse([CMD], StringIO(_options_file))

    assert options.hello_other_value == "someone"
    assert options.hello_value == "option ated"


def test_usage():
    clear_cmds()

    subcommand.register(CMD, hello_command)
    output = subcommand.usage(_print=False, exit=False)

    assert "This should be visible" in output

# vim: ai sts=4 et sw=4
