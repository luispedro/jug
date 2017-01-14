=============
Configuration
=============

Configuration file
------------------

.. versionadded:: 1.3
    In previous versions, the configuration file was called
    ``~/.jug/configrc``. Since version 1.3, the path ``~/.config/jugrc`` is
    used (for compatibility, ``~/.jug/configrc`` is read if ``~/.config/jugrc``
    is missing).

On startup, ``jug`` reads the file ``~/.config/jugrc`` (if it exists). It
expects an *.ini* format file. It can have the following fields::

    [main]
    jugdir=%(jugfile)s.jugdata
    jugfile=jugfile.py

    [status]
    cache=off

    [execute]
    aggressive-unload=False
    pdb=False
    wait-cycle-time=12
    nr-wait-cycles=150

These have the same meaning as the analogous command line options. If both are
given, the command line takes priority.

