# -*- coding: utf-8 -*-

import os
import tempfile
import shutil
from six import StringIO
from jug.subcommands import cmdapi, SubCommand
from jug.options import parse

CMD = "hello-cmd"
MSG = "Hello world"


class HelloCommand(SubCommand):
    "This should be visible"

    name = "hello-cmd"

    def run(self, *args, **kwargs):
        return MSG

    def parse(self, parser):
        parser.add_argument("--value", dest="hello_value", action="store")
        parser.add_argument("--other-value", dest="hello_other_value", action="store")

    def parse_defaults(self):
        return {
            "hello_value": "option",
            "hello_other_value": "undefined",
        }


class HelloNoSelfRegister(HelloCommand):
    "No self register"
    def __init__(self):
        pass


def clear_default(default):
    try:
        delattr(cmdapi.default_options, default)
    except AttributeError:
        pass


class TestSubCommandAPI():
    def setup(self):
        self._old_commands = cmdapi._commands.copy()
        cmdapi._commands.clear()

    def teardown(self):
        cmdapi._commands.clear()
        cmdapi._commands.update(self._old_commands)

    def test_register(self):
        hello_command = HelloNoSelfRegister()
        assert "hello-cmd" not in cmdapi._commands

        cmdapi._register(CMD, hello_command)
        assert "hello-cmd" in cmdapi._commands

        output = cmdapi.run(CMD)
        assert output == MSG, "Expected: '%s' , got: '%s'" % (MSG, output)

    def test_user_commands(self):
        payload = """
from jug.subcommands import SubCommand

class HelloCommandPayload(SubCommand):
    "This should be visible"

    name = "hello-payload"

    def run(self, *args, **kwargs):
        return "This TEST"

hello_command = HelloCommandPayload()
"""
        userfile = "jug_user_commands.py"
        tmpdir = tempfile.mkdtemp(prefix="jug")
        with open(os.path.join(tmpdir, userfile), 'w') as fh:
            fh.write(payload)

        cmdapi._commands._load_user_commands(user_path=tmpdir)
        CMD = "hello-payload"
        assert CMD in cmdapi._commands, "Expected: '%s' to be in '%s'" % (CMD, cmdapi._commands)

        output = cmdapi.run(CMD)
        assert output == "This TEST"

        shutil.rmtree(tmpdir)

    def test_usage(self):
        HelloCommand()
        output = cmdapi.usage(_print=False, exit=False)

        assert "This should be visible" in output

    def test_options_cmdline(self):
        clear_default("hello_other_value")
        clear_default("hello_value")

        assert CMD not in cmdapi._commands

        HelloCommand()

        options = parse([CMD, "--value", "FooBar"])
        assert options.hello_value == "FooBar"
        assert options.hello_other_value == "undefined"

        output = cmdapi.run(CMD, options=options)
        assert output == "Hello world", "Got '{0}'".format(output)

    def test_options_config(self):
        "Test if settings read from config file work even for custom subcommands"

        _options_file = '''
[hello]
other-value=someone
'''

        clear_default("hello_other_value")
        clear_default("hello_value")

        cmd = HelloCommand()
        defaults = cmd.parse_defaults()
        assert defaults["hello_other_value"] == "undefined"
        assert defaults["hello_value"] == "option"

        options = parse([CMD], StringIO(_options_file))

        assert options.hello_other_value == "someone"
        assert options.hello_value == "option"

# vim: ai sts=4 et sw=4
