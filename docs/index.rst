===========================================
Jug: A Task-Based Parallelization Framework
===========================================

What is Jug?
------------

Jug allows you to write code that is broken up into tasks and run different
tasks on different processors.

It currently has two backends. The first uses the filesystem to communicate
between processes and works correctly over NFS, so you can coordinate processes
on different machines. The second is based on redis so the processes only need
the capability to connect to a common redis server.

Jug also takes care of saving all the intermediate results to the backend in a
way that allows them to be retrieved later.

Contents:
---------

.. toctree::
    :maxdepth: 2

    tutorial.rst
    decrypt-example.rst
    text-example.rst
    backends.rst

Examples
--------

There is a worked out example in the `tutorial`_, and another, fully functioning in
the `examples/` directory.

How do I get Jug?
-----------------

You can either get the git repository at

git://github.com/luispedro/jug

Or download the package from PyPI_. You can use `easy_instal jug` or `pip
install jug` if you'd like.

.. _PyPI: http://pypi.python.org/pypi/Jug

What do I need to run Jug?
---------------------------

It is a Python only package. I have tested it with Python 2.5 and 2.6.
I do not expect Python 2.4 or earlier to work (this is not a priority).
Python 3.0 will not work either (this is expected to change in the 
future---patches are welcome).

How does it work?
-----------------

Read the tutorial_.

.. _tutorial: tutorial.html

What's the status of the project?
---------------------------------

Beta (or thereabouts).

This is still in development and APIs are not fixed, but are in less flux than
they were earlier in the project.

It is usable, though. I have used it for my academic projects for the past year
and wouldn't now start any other project without using jug. It's become a major
part of the way I handle projects with a large number of computations and
cluster usage.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

