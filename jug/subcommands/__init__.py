#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (C) 2008-2019, Luis Pedro Coelho <luis@luispedro.org>
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

One way to achieve this is to add the following code to ``~/.config/jug/jug_user_commands.py``::

    from jug.subcommands import SubCommand

    class FancyReport(SubCommand):
        "Produces a fancy report of my results"

        name = "my-fancy-report"

        def run(self, *args, **kwargs):
            ...

    fancy_report = FancyReport()

The first line of the class docstring is important as it will be shown in jug's
usage help page. The name attribute is also required and should be the name of
your subcommand on the command-line.

The body of the method ``run()`` defines what should happen when you
call the subcommand ``jug my-fancy-report``.

The ``run`` function will receive the following objects::

* ``options``  - object representing command-line and user options
* ``store``    - backend object reponsible for handling jobs
* ``jugspace`` - a namespace of jug internal variables (better not touch)

additional objects may be introduced in the future so make sure your function
uses ``*args, **kwargs`` to maintain compatibility.

Finally, in order to register the subcommand, you must instanciate the subcommand.


If your subcommand needs configurable options you can expose them via command-line
by defining two additional methods::

    class FancyReport(SubCommand):
        ...

        def parse(self, parser):
            parser.add_argument('--tofile', action='store',
                                dest='report_tofile',
                                help='Name of file to use for report')

        def parse_defaults(self):
            return {
                "report_tofile": "report.txt",
            }

    fancy_report = FancyReport()

The first method configures argparse arguments that will be available as
``jug my-fancy-report --tofile myreport.txt``. These will also be avaiable to
the ``run()`` method as part of the ``options`` object.

The second defines default values in case of omission. The ``key`` should match
the ``dest=`` attribute of ``add_argument()`` and the ``value`` should be any object
to be used by your ``run()`` method. Note that the value received in the command-line
will be automatically converted to the same type as this default (i.e. if your default
is ``True`` any ``--tofile john`` would result in ``bool("john") -> True``).

For more information on parser configuration refer to ``argparse``'s documentation.

NOTE: A few words of caution, we cannot rely on ``argparse``'s ``default=`` option since
it doesn't allow distinguishing between user supplied and built-in (default) values.
For the same reason, don't use ``action=`` with ``store_true`` or ``store_false``
instead use ``store_const`` and ``const=`` with ``True`` or ``False``.
Failing to do so will cause any matching setting on ``jugrc`` to not have any effect.
"""

__all__ = [
    'cmdapi',
    'SubCommand',
    'SubCommandError',
    'NoSuchCommandError',
]

import importlib
import logging
import os
import pkgutil
import sys
import traceback
from ..options import Options
from ..jug_version import CITATION
from abc import ABCMeta, abstractmethod, abstractproperty
from six import add_metaclass


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


@add_metaclass(ABCMeta)
class SubCommand:
    """Define a subcommand and its command-line options
    """

    def __init__(self):
        cmdapi._register(self.name, self)
        cmdapi.update_defaults(self.name)

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    @abstractproperty
    def name(self):
        pass

    def parse(self, parser):
        """Define command line options using parser.add_argument()

        The parser object is an argparser subparser group.
        Anything returned by this method is ignored
        """
        pass

    def parse_defaults(self):
        """Define default values for parser options

        Should return a dictionary mapping ``dest=`` targets to their default.
        """
        pass

    @abstractmethod
    def run(self, *args, **kwargs):
        """Re-define to specify what your subcommand is supposed to do

        This code will receive the following arguments:
        * ``options``  - object representing command-line and user options
        * ``store``    - backend object reponsible for handling jobs
        * ``jugspace`` - a namespace of jug internal variables (better not touch)

        Anything returned by this method is ignored
        """
        pass


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
        self.default_options = Options(None)

    def _register(self, name, cmd_instance):
        if name in self._commands and self._commands[name] != cmd_instance:
            logging.warning("Jug: command: '%s' will be overriden with code from '%s'",
                            name, cmd_instance.__class__.__name__)

        self._commands[name] = cmd_instance

    def update_defaults(self, name):
        cmd = self.get(name)
        opts = cmd.parse_defaults()
        if opts is not None:
            self.default_options.update(opts)

    def get(self, command):
        try:
            return self._commands[command]
        except KeyError:
            raise NoSuchCommandError("Unknown subcommand '%s'" % (command,))

    def run(self, command, *args, **kwargs):
        """Execute subcommand
        """
        try:
            cmd = self.get(command)
        except NoSuchCommandError as e:
            self.usage(error=e)

        try:
            return cmd(*args, **kwargs)
        except TypeError as e:
            if "unexpected keyword" in str(e):
                _invalid_module(command, e)

            traceback.print_exc(file=sys.stderr)

            self.usage(error=e)

    def usage(self, error='', exit=True, _print=True, *args, **kwargs):
        "Shows help/usage information"

        usage_text = ['''\
jug SUBCOMMAND [JUGFILE] [OPTIONS...]

Docs: https://jug.readthedocs.io/
Copyright: 2008-2019, Luis Pedro Coelho
Citation: http://doi.org/10.5334/jors.161

If you use Jug for generating results for a peer-reviewed publication, please
cite:

    Coelho, L.P., (2017). Jug: Software for Parallel Reproducible Computation in
    Python. Journal of Open Research Software. 5(1), p.30.

    http://doi.org/10.5334/jors.161


Subcommands
-----------
''']
        self._commands.load_commands()

        for name, cmd in sorted(self._commands.items()):
            usage_text.append("   %-15s %s" % (name + ":", _get_helptext(cmd)))

        usage_text.append("\nhelp:")
        usage_text.append("  Use 'jug <subcommand> --help' for subcommand specific options")

        if error:
            usage_text.append("")
            usage_text.append(str(error))

        message = "\n".join(usage_text) + "\n \n"

        if _print:
            sys.stdout.write(message)

        if exit:
            sys.exit(1)

        return message

    def get_subcommand_parsers(self, subparsers):
        self._commands.load_commands()

        parsers = []

        for name, cmd in sorted(self._commands.items()):
            parser = subparsers.add_parser(
                name,
                # This is necessary to have all the same output on all subparsers
                usage=self.usage(_print=False, exit=False),
            )
            parsers.append(parser)

            group = parser.add_argument_group(name)
            cmd.parse(group)

        return parsers

def maybe_print_citation_info(options):
    '''Unless options.will_cite, prints citation information'''
    if not options.will_cite:
        print("If you use Jug in a published research paper please cite")
        print(CITATION)
        print('')
        print('Use the --will-cite option to suppress this message')
        print('(Or set will_cite = True in the Jug configuration file)')
        print('')

cmdapi = SubCommandManager()
