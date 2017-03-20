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

"""Subcommands are now implemented using a modular design that allows extending
jug with additional commands.
This API is currently in experimental stage and may change in the future.

The following serves as an example of how to extend jug's commands.

Lets assume you wanted to create a custom report and have it available as::

    $ jug my-fancy-report

First you will need to implement a function with the following signature::

    def fancyreport_func(*args, **kwargs):
        "Produces a fancy report of my results"
        ...

The first line of the docstring is important as it will be shown as part of the
jug usage help page.

Then add your fancyreport extra commands to ``~/.config/jug/jug_user_commands.py``
registering your commands via::

    from jug.subcommands import subcommand
    #                  <command-name>  <function to call>
    subcommand.register("my-fancy-report", fancyreport_func)

Finally you should know that your function will receive the following objects:

* ``options``  - object representing command-line and user options
* ``store``    - backend object reponsible for handling jobs
* ``jugspace`` - a namespace of jug internal variables (better not touch)

additional objects may be introduced in the future so make sure your function
uses ``*args, **kwargs`` to maintain compatibility.


If your subcommand has configurable options you can expose them via command-line
by defining arguments to be available in the command-line by using::

    def fancyreport_options(parser):
        parser.add_argument('--tofile', action='store',
                            dest='report_tofile',
                            help='Name of file to use for report')

and instead of the above, register your subcommand with::

    #                    <command-name>   <function to call> <cmd-line options>
    subcommand.register("my-fancy-report", fancyreport_func, fancyreport_options)

If a user sets these options they will be available through the ``options`` object
mentioned above. Jug uses ``argparse`` for command-line parsing.
For more information refer to ``argparse``'s documentation.

NOTE: A word of caution, don't use ``action=`` with ``store_true`` or ``store_false``
instead use ``store_const`` and ``const=`` with ``True`` or ``False``.
Failing to do so will cause any matching setting on ``jugrc`` to not have any effect.

"""

__all__ = [
    'SubCommand',
    'SubCommandManager',
    'SubCommandError',
    'NoSuchCommandError',
]

import importlib
import logging
import os
import pkgutil
import sys
import traceback


class SubCommandError(Exception):
    "Exception raised when a subcommand doesn't respect the API"


class NoSuchCommandError(Exception):
    "Exception raised when a subcommand doesn't respect the API"


def _get_helptext(command):
    "First line of the docstring is to be shown on the help/usage text"
    try:
        return command.__doc__.splitlines()[0]
    except AttributeError:
        raise SubCommandError("Command '%s' is missing a documentation string" % (command,))


def _invalid_module(module, e):
    raise SubCommandError(
        """Invalid subcommand structure.
Please make sure that the subcommand(s) '%s' conform(s) to the API.

    help(jug.subcommands) for more information

Original error was:
%s
""" % (module, e))


class SubCommandDict(dict):
    def __getitem__(self, command):
        if command not in self:
            self.load_commands(command)

        return super(SubCommandDict, self).__getitem__(command)

    def load_commands(self, stop_on_command=None):
        """Load all modules in jug's subcommands and user's jug folder

        If stop_on_command is given the function will return True as soon as
        a matching command is found
        """
        for _, name, _ in pkgutil.iter_modules(__path__):
            module = __name__ + '.' + name

            self._try_import(module)

            if stop_on_command in self:
                return True

        self._load_user_commands()

    def _try_import(self, module):
        try:
            importlib.import_module(module)
        except Exception as e:
            logging.warning("Couldn't load subcommand '%s' with error '%s'", module, e)

    def _load_user_commands(self, user_path="~/.config/jug/"):
        user_path = os.path.expanduser(user_path)
        logging.debug("Loading user commands from '%s'", user_path)
        if os.path.isdir(user_path):
            if user_path not in sys.path:
                logging.debug("Adding path '%s' to PYTHONPATH", user_path)
                sys.path.insert(0, user_path)

            user_commands = os.path.join(user_path, "jug_user_commands.py")
            if os.path.isfile(user_commands):
                self._try_import("jug_user_commands")


class SubCommandManager:
    def __init__(self):
        self._commands = SubCommandDict()
        self.default_options = {}

    def register(self, name, cmd_callback, opt_callback=None):
        callbacks = (cmd_callback, opt_callback)

        if name in self._commands and self._commands[name] != callbacks:
            if opt_callback is None:
                logging.warning("Jug: command: '%s' will be overriden with code from '%s'",
                                name, cmd_callback.__name__)
            else:
                logging.warning("Jug: command: '%s' will be overriden with code from '%s' and '%s'",
                                name, cmd_callback.__name__, opt_callback.__name__)

        self._commands[name] = callbacks

    def get(self, command):
        try:
            return self._commands[command]
        except KeyError:
            raise NoSuchCommandError("Unknown subcommand '%s'" % (command,))

    def run(self, command, *args, **kwargs):
        """Execute subcommand
        """
        try:
            cmd, opt = subcommand.get(command)
        except NoSuchCommandError as e:
            subcommand.usage(error=e)

        try:
            return cmd(*args, **kwargs)
        except TypeError as e:
            if "unexpected keyword" in str(e):
                _invalid_module(command, e)

            traceback.print_exc(file=sys.stderr)

            subcommand.usage(error=e)

    def usage(self, error='', exit=True, _print=True, *args, **kwargs):
        "Shows help/usage information"

        usage_text = ['''\
jug SUBCOMMAND [JUGFILE] [OPTIONS...]

Docs: https://jug.readthedocs.io/
Copyright: 2008-2017, Luis Pedro Coelho

Subcommands
-----------
''']
        self._commands.load_commands()

        for name, command in sorted(self._commands.items()):
            cmd, opt = command
            usage_text.append("   %-15s %s" % (name + ":", _get_helptext(cmd)))

        usage_text.append("\nhelp:")
        usage_text.append("  Use 'jug <subcommand> --help' for subcommand specific options")

        if error:
            usage_text.append("")
            usage_text.append(str(error))

        message = "\n".join(usage_text) + "\n "

        if _print:
            sys.stdout.write(message)

        if exit:
            sys.exit(1)

        return message

    def get_subcommand_parsers(self, subparsers):
        self._commands.load_commands()

        parsers = []

        for name, command in sorted(self._commands.items()):
            cmd, opt = command
            parser = subparsers.add_parser(
                name,
                # This is necessary to have all the same output on all subparsers
                usage=subcommand.usage(_print=False, exit=False),
            )
            parsers.append(parser)

            if opt is not None:
                group = parser.add_argument_group(name)
                defaults = opt(group)

                if defaults is not None:
                    self.default_options.update(defaults)

        return parsers


subcommand = SubCommandManager()
