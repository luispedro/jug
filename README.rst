===========================================
Jug: A Task-Based Parallelization Framework
===========================================

Jug allows you to write code that is broken up into
tasks and run different tasks on different processors.

.. image:: https://github.com/luispedro/jug/actions/workflows/python-package.yml/badge.svg
       :target: https://github.com/luispedro/jug/actions/workflows/python-package.yml

.. image:: https://zenodo.org/badge/205237.svg
   :target: https://zenodo.org/badge/latestdoi/205237

.. image:: https://img.shields.io/badge/install%20with-conda-brightgreen.svg?style=flat
    :target: https://anaconda.org/conda-forge/jug

.. image:: https://static.pepy.tech/personalized-badge/jug?period=total&units=international_system&left_color=black&right_color=blue&left_text=Downloads
   :target: https://pepy.tech/project/jug

.. image:: https://img.shields.io/badge/CITATION-doi.org%2F10.5334%2Fjors.161-green.svg
   :target: https://doi.org/10.5334/jors.161


It uses the filesystem to communicate between processes and
works correctly over NFS, so you can coordinate processes on
different machines.

Jug is a pure Python implementation and should work on any platform.

Python versions 3.5 and above are supported.

*Website*: `http://luispedro.org/software/jug <http://luispedro.org/software/jug>`__

*Documentation*: `https://jug.readthedocs.org/ <https://jug.readthedocs.org/>`__

*Video*: On `vimeo <http://vimeo.com/8972696>`__ or `showmedo
<http://showmedo.com/videotutorials/video?name=9750000;fromSeriesID=975>`__

*Mailing List*: `https://groups.google.com/group/jug-users
<https://groups.google.com/group/jug-users>`__

Testimonials
------------

"I've been using jug with great success to distribute the running of a
reasonably large set of parameter combinations" - Andreas Longva


Install
-------

You can install Jug with pip::

    pip install Jug

or use, if you are using `conda <https://anaconda.org/>`__, you can install jug
from `conda-forge <https://conda-forge.github.io/>`__ using the following
commands::

    conda config --add channels conda-forge
    conda install jug

Citation
--------

If you use Jug to generate results for a scientific publication, please cite

    Coelho, L.P., (2017). Jug: Software for Parallel Reproducible Computation in
    Python. Journal of Open Research Software. 5(1), p.30.

    https://doi.org/10.5334/jors.161


Short Example
-------------

Here is a one minute example. Save the following to a file called ``primes.py``
(if you have installed jug, you can obtain a slightly longer version of this
example by running ``jug demo`` on the command line)::

    from jug import TaskGenerator
    from time import sleep

    @TaskGenerator
    def is_prime(n):
        sleep(1.)
        for j in range(2,n-1):
            if (n % j) == 0:
                return False
        return True

    primes100 = [is_prime(n) for n in range(2,101)]

This is a brute-force way to find all the prime numbers up to 100. Of course,
this is only for didactical purposes, normally you would use a better method.
Similarly, the ``sleep`` function is so that it does not run too fast. Still,
it illustrates the basic functionality of Jug for embarassingly parallel
problems.

Type ``jug status primes.py`` to get::

    Task name                  Waiting       Ready    Finished     Running
    ----------------------------------------------------------------------
    primes.is_prime                  0          99           0           0
    ......................................................................
    Total:                           0          99           0           0


This tells you that you have 99 tasks called ``primes.is_prime`` ready to run.
So run ``jug execute primes.py &``. You can even run multiple instances in the
background (if you have multiple cores, for example). After starting 4
instances and waiting a few seconds, you can check the status again (with ``jug
status primes.py``)::

    Task name                  Waiting       Ready    Finished     Running
    ----------------------------------------------------------------------
    primes.is_prime                  0          63          32           4
    ......................................................................
    Total:                           0          63          32           4


Now you have 32 tasks finished, 4 running, and 63 still ready. Eventually, they
will all finish and you can inspect the results with ``jug shell primes.py``.
This will give you an ``ipython`` shell. The `primes100` variable is available,
but it is an ugly list of `jug.Task` objects. To get the actual value, you call
the `value` function::

    In [1]: primes100 = value(primes100)

    In [2]: primes100[:10]
    Out[2]: [True, True, False, True, False, True, False, False, False, True]

What's New
----------

Version 2.3.1 (*5 November 2023*)

- Update for Python 3.12

Version 2.3.0 (*25 June 2023*)

- jug shell: Add ``get_filtered_tasks()``
- jug: Fix ``jug --version`` (which had been broken in the refactoring to use subcommands)
- jug shell: Fix message in jug shell when there are no dependencies (it would repeatedly print the message stating *this will only be run once*)
- jug pack: Make it much faster to invalidate elements
- file_store: ensure that the temporary directory exists

Version 2.2.3 (*26 May 2023*)
- Fix ``jug shell`` for newer versions of IPython

Version 2.2.2 (*19 July 2022*)
- Fix ``jug cleanup`` when packs are used (``jug pack``)

Version 2.2.1 (*19 May 2022*)
- Fix bug with ``jug cleanup`` and the redis backend (`#86 <https://github.com/luispedro/jug/issues/86>`__)

Version 2.2.0 (*3 May 2022*)

- Add ``jug pack`` subcommand
- Make ``get_tasks()`` return a copy of the tasks inside ``jug shell``
- Remove ``six`` dependency

Version 2.1.1 (*18 March 2021*)

- Include requirements files in distribution

Version 2.1.0 (*18 March 2021*)

- Improvements to webstatus (by Robert Denham)
- Removed Python 2.7 support
- Fix output encoding for Python 3.8
- Fix bug mixing ``mapreduce()`` & ``status --cache``
- Make block_access (used in ``mapreduce()``) much faster (20x)
- Fix important redis bug
- More precise output in ``cleanup`` command

Version 2.0.2 (Thu Jun 11 2020)

- Fix command line argument parsing

Version 2.0.1 (Thu Jun 11 2020)

- Fix handling of ``JUG_EXIT_IF_FILE_EXISTS`` environmental variable
- Fix passing an argument to ``jug.main()`` function
- Extend ``--pdb`` to exceptions raised while importing the jugfile (issue #79)

version **2.0.0** (Fri Feb 21 2020)

- jug.backend.base_store has 1 new method 'listlocks'
- jug.backend.base_lock has 2 new methods 'fail' and 'is_failed'
- Add 'jug execute --keep-failed' to preserve locks on failing tasks.
- Add 'jug cleanup --failed-only' to remove locks from failed tasks
- 'jug status' and 'jug graph' now display failed tasks
- Check environmental exit variables by default (suggested by Renato Alves, issue #66)
- Fix 'jug sleep-until' in the presence of barrier() (issue #71)

For older version see ``ChangeLog`` file or the `full history
<https://jug.readthedocs.io/en/latest/history.html>`__.




