===========================================
Jug: A Task-Based Parallelization Framework
===========================================

What is Jug?
------------

Jug allows you to write code that is broken up into
tasks and run different tasks on different processors.

It uses the filesystem to communicate between processes and
works correctly over NFS, so you can coordinate processes on
different machines.

Jug also takes care of saving all the intermediate results to
disk in a way that allows them to be retrieved later.

How do I get Jug?
-----------------

You can either get the git repository at

http://coupland.cbi.cmu.edu/git/jug.git

Or download the package from PyPI_.

.. _PyPI: http://pypi.python.org/pypi/Jug

How does it work?
-----------------

Read the tutorial_.

.. _tutorial: tutorial.html

What's the status of the project?
---------------------------------

Alpha (or thereabouts). This is still in heavy development and APIs are not fixed.


Contents:
---------

.. toctree::
   :maxdepth: 2

   tutorial

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

