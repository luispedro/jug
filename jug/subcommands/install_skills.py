#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import shutil
import sys

from . import SubCommand

__all__ = [
    'install_skills',
    'install_skill',
    'bundled_skill_path',
]


SKILL_NAME = 'jug'


def bundled_skill_path():
    return os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'skills',
        SKILL_NAME)


def _remove_existing(path):
    if os.path.isdir(path) and not os.path.islink(path):
        shutil.rmtree(path)
    else:
        os.unlink(path)


def install_skill(output, force=False):
    source = bundled_skill_path()
    if not os.path.isdir(source):
        raise RuntimeError('Bundled skill payload is missing: {}'.format(source))

    output = os.path.abspath(os.path.expanduser(output))
    target = os.path.join(output, SKILL_NAME)
    try:
        os.makedirs(output, exist_ok=True)
    except OSError as err:
        raise RuntimeError(
            'Could not create output directory {}: {}'.format(output, err))

    if os.path.lexists(target):
        if not force:
            raise RuntimeError(
                'Destination already exists: {} (use --force to overwrite)'.format(target))
        try:
            _remove_existing(target)
        except OSError as err:
            raise RuntimeError(
                'Could not remove existing destination {}: {}'.format(target, err))

    try:
        shutil.copytree(source, target)
    except OSError as err:
        raise RuntimeError(
            'Could not install bundled skill to {}: {}'.format(target, err))
    return target


class InstallSkillsCommand(SubCommand):
    '''Install the bundled Jug skill into a skills directory.

    The skill is copied to ``OUTPUT/jug``.
    '''
    name = "install-skills"

    def parse(self, parser):
        parser.add_argument(
            '--output',
            action='store',
            dest='install_skills_output',
            help='Directory where the bundled skill should be installed')
        parser.add_argument(
            '--force',
            action='store_const',
            const=True,
            dest='install_skills_force',
            help='Overwrite OUTPUT/jug if it already exists')

    def parse_defaults(self):
        return {
            'install_skills_output': None,
            'install_skills_force': False,
        }

    def run(self, options, *args, **kwargs):
        if not options.install_skills_output:
            sys.stderr.write('jug install-skills requires --output DIR\n')
            sys.exit(2)

        try:
            target = install_skill(
                options.install_skills_output,
                force=options.install_skills_force)
        except RuntimeError as err:
            sys.stderr.write(str(err) + '\n')
            sys.exit(1)

        options.print_out('Installed Jug skill to {}'.format(target))


install_skills = InstallSkillsCommand()
