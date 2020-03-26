===========================================
Jug: A Task-Based Parallelization Framework
===========================================

.. note::

    If you use Jug to generate results for a scientific publication, please cite

        Coelho, L.P., (2017). Jug: Software for Parallel Reproducible Computation in
        Python. Journal of Open Research Software. 5(1), p.30.

        http://doi.org/10.5334/jors.161

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



Examples
--------

Short Example
~~~~~~~~~~~~~

Here is a one minute example. Save the following to a file called ``primes.py``:

.. literalinclude:: ../../examples/primes/primes.py

Of course, this is only for didactical purposes, normally you would use a
better method. Similarly, the ``sleep`` function is so that it does not run too
fast.

Now type ``jug status primes.py`` to get::


     Waiting       Ready    Finished     Running  Task name                    
    ---------------------------------------------------------------------------
           1           0           0           0  primes.count_primes          
           0          99           0           0  primes.is_prime              
           1           0           0           0  primes.write_output          
    ...........................................................................
           2          99           0           0  Total                        




This tells you that you have 99 tasks called ``primes.is_prime`` ready to run,
while both other tasks are _waiting_ (i.e., they need the ``primes.is_prime``
tasks to finish).  So run ``jug execute primes.py &``. You can even run
multiple instances in the background (if you have multiple cores, for example).
After starting 4 instances and waiting a few seconds, you can check the status
again (with ``jug status primes.py``)::


     Waiting       Ready    Finished     Running  Task name                    
    ---------------------------------------------------------------------------
           1           0           0           0  primes.count_primes          
           0          63          32           4  primes.is_prime              
           1           0           0           0  primes.write_output          
    ...........................................................................
           2          99           0           0  Total                        


Now you have 32 tasks finished, 4 running, and 63 still ready. Eventually, they
will all finish (including ``count_primes`` and ``write_output`) and you can
inspect the results with ``jug shell primes.py``.  This will give you an
``ipython`` shell. The `primes100` variable is available, but it is an ugly
list of `jug.Task` objects. To get the actual value, you call the `value`
function::

    In [1]: primes100 = value(primes100)

    In [2]: primes100[:10]
    Out[2]: [True, True, False, True, False, True, False, False, False, True]

More Examples
~~~~~~~~~~~~~

There is a worked out example in the `tutorial`_, and another, fully functioning in
the `examples/` directory.

Links
-----

- `Mailing list <http://groups.google.com/group/jug-users>`__
- `Github <http://github.com/luispedro/jug>`__
- `Freshmeat <http://freshmeat.net/projects/jug>`__
- `Documentation <http://packages.python.org/Jug/>`__
- `Homepage <http://luispedro.org/software/jug>`__

How do I get Jug?
-----------------

The simplest is using pip::

pip install jug


You can either get the git repository at

`http://github.com/luispedro/jug <http://github.com/luispedro/jug>`__

Or download the package from `PyPI <http://pypi.python.org/pypi/Jug>`__


Testimonials
------------

"I've been using jug with great success to distribute the running of a
reasonably large set of parameter combinations" - Andreas Longva



Documentation Contents
----------------------

.. toctree::
    :maxdepth: 2

    tutorial.rst
    decrypt-example.rst
    text-example.rst
    segmentation-example.rst
    subcommands.rst
    status.rst
    exit.md
    shell.rst
    types.rst
    tasks.rst
    tasklets.rst
    invalidate.rst
    idioms.rst
    barrier.rst
    compound.rst
    utilities.rst
    mapreduce.rst
    backends.rst
    configuration.rst
    bash.rst
    faq.rst
    why.rst
    writeabackend.rst
    magic.rst
    api.rst
    history.rst

What do I need to run Jug?
---------------------------

It is a Python only package. Jug is `continuously tested
<https://travis-ci.com/luispedro/jug>`__ with Python 2.6 and up (including
Python 3.3 and up).

How does it work?
-----------------

Read the tutorial_.

.. _tutorial: tutorial.html

What's the status of the project?
---------------------------------

Since version 1.0, jug should be considered stable.

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
