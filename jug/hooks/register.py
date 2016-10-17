# Copyright (C) 2014-2015, Luis Pedro Coelho <luis@luispedro.org>
# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
# License: MIT

_hooks = {}

_known_hooks = frozenset([
        'execute.task-loadable',
        'execute.task-executed1',
        'execute.task-pre-execute',
        'execute.finished_pre_status',
        'execute.finished_post_status',
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

_registered = set([])
def register_hook_once(name, code, f):
    '''Register a hook only once

    Parameters
    ----------
    name : str
        Name of hook
    code : str
        An identifier for this registration. The second time this function is
        called with the same (name, code) pair, no action will be taken.
    f : function
        Function to call
        Note that this must be a function, you cannot use it as a decorator

    See Also
    --------
    register_hook
    '''
    if (name,code) not in _registered:
        _registered.add( (name, code) )
        return register_hook(name, f=f)
    elif f is None:
        raise NotImplementedError("jug.register_hook_once: function argument must be used")


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

def reset_all_hooks():
    '''Reset all hooks

    This is a destructive actions, which cannot be undone'''
    _registered.clear()
    _hooks.clear()
