# Copyright (C) 2014, Luis Pedro Coelho <luis@luispedro.org>
# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
# License: MIT

_hooks = {}

_known_hooks = set([
        'execute.task-loadable',
        'execute.task-executed1',
        'execute.task-pre-execute',
        ])

def jug_hook(name, args=(), kwargs={}):
    '''Call hook

    Calls ``f(*args, **kwargs)`` for all functions registered with name ``name``.

    Parameters
    ----------
    name : str
        Name
    args, kwargs
        passed to functions

    Returns
    -------
    res : list
        A list with the result of all the functions
    '''
    return [f(*args, **kwargs) for f in _hooks.get(name, [])]

def register_hook(name, f=None):
    '''Register a hook

    Known hooks

    execute.task-executed1(Task)
        A single task has been executed. This hook can call ``sys.exit`` to
        exit the jug process (technically, it needs to raise SystemExit).
        Return values are ignored.

    Parameters
    ----------
    name : str
        Identify the hook name
    f : function
        Function to call
    '''
    if name not in _known_hooks:
        raise ValueError('jug.register_hook: {} is not a known hook name (Known are {}.)'.format(name, list(_known_hooks)))
    if f is None:
        from functools import partial
        return partial(register_hook, name)
    _hooks.setdefault(name, []).append(f)
