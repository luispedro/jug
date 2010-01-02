Backends
========

What is a Jug Backend?
----------------------

A jug backend serves two tasks: it saves intermediate results and it
synchronises the running processes when needed.

What Backends Are Available?
----------------------------

There are two backend available: one is based on the filesystem, the other is a
`redis`_ backend.

Filesystem
..........

By default, jug will save its results in a directory called ``jugdata``. This
is done in a way that works across **NFS** if you are using a cluster.

Redis
.....

Redis is a non-relational database system. I assume you have already installed
it (it is easy to install from source, but it is now a part of Ubuntu, so that
is even easier).

    1. Run a redis server (see its docs for how to control it, but simply calling
    ``redis-server`` should work).
    2. Now start your jug jobs with the ``--jugdir=redis://127.0.0.1/``.

Which Backend Should I Use?
---------------------------

If all your nodes share a filesystem and you don't want to set anything up,
just you the default filesystem backend. If your computations are non-trivial
(in general, you should avoid breaking up your algorithm so much that each
tasks takes less than a second), then this will be fast enough and very robust.

Do note that ``jug`` **works well over NFS**.

If your nodes do not share a filesystem then you are going to have to use
redis. For some cases (if you have many outputs of computations that do not
take very long), it is also faster and, if your results are small, takes up
significantly less space.

So the tradeoffs are speed and space vs. convenience. 

.. _redis: http://code.google.com/p/redis
