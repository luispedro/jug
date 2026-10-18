# Copyright (C) 2014-2026, Luis Pedro Coelho <luis@luispedro.org>
# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
# License: MIT

'''
Hooks: functions that ``jug execute`` calls at specific points

Register a function with ``register_hook(name, f)``. See ``register_hook`` for
the list of hooks.

The submodules ``jug.hooks.exit_checks`` and ``jug.hooks.execution`` contain
functions that use hooks (to exit early and to time tasks, respectively).
'''

from .register import jug_hook, register_hook, register_hook_once, reset_all_hooks
