=============
Configuration
=============

Configuration file
------------------

On startup, ``jug`` reads the file ``~/.jug/configrc`` (if it exists). It
expects an *.ini* format file. It can have the following fields::

    [main]
    jugdir=%(jugfile).jugdata
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

