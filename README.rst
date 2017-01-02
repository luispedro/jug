===========================================
Jug: A Task-Based Parallelization Framework
===========================================

Jug allows you to write code that is broken up into
tasks and run different tasks on different processors.

It uses the filesystem to communicate between processes and
works correctly over NFS, so you can coordinate processes on
different machines.

Jug is a pure Python implementation and should work on any platform.

Python 2.6/2.7 and Python 3.3+ are supported.

*Website*: `http://luispedro.org/software/jug <http://luispedro.org/software/jug>`__

*Documentation*: `https://jug.readthedocs.org/ <https://jug.readthedocs.org/>`__

*Video*: On `vimeo <http://vimeo.com/8972696>`__ or `showmedo
<http://showmedo.com/videotutorials/video?name=9750000;fromSeriesID=975>`__

*Mailing List*: `http://groups.google.com/group/jug-users
<http://groups.google.com/group/jug-users>`__

Short Example
-------------

Here is a one minute example. Save the following to a file called ``primes.py``::

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

Of course, this is only for didactical purposes, normally you would use a
better method. Similarly, the ``sleep`` function is so that it does not run too
fast.

Now type ``jug status primes.py`` to get::

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

Travis Build Status
~~~~~~~~~~~~~~~~~~~

.. image:: https://travis-ci.org/luispedro/jug.png
       :target: https://travis-ci.org/luispedro/jug

What's New
----------

version **1.4.0** (Tue Jan 3 2017)
- Fix bug with writing very large objects to disk
- Smarter handling of --aggressive-unload (do not unload what will be
  immediately necessary)
- Work around corner case in `jug shell` command
- Add test-jug subcommand
- Add return_tuple decorator

version **1.3.0** (Tue Nov 1 2016)
- Update `shell` subcommand to IPython 5
- Use ~/.config/jugrc as configuration file
- Cleanup usage string
- Use `bottle` instead of `web.py` for webstatus subcommand
- Add `jug_execute` function
- Add timing functionality

version **1.2.2** (Sat Jun 25 2016)
- Fix bugs in shell subcommand and a few corner cases in encoding/decoding
  results


version **1.2.1** (Mon Feb 15 2016)
- Changed execution loop to ensure that all tasks are checked (issue #33 on
  github)
- Fixed bug that made 'check' or 'sleep-until' slower than necessary
- Fixed jug on Windows (which does not support fsync on directories)
- Made Tasklets use slightly less memory


version **1.2** (Thu Aug 20 2015)
- Use HIGHEST_PROTOCOL when pickle()ing
- Add compress_numpy option to file_store
- Add register_hook_once function
- Optimize case when most (or all) tasks are already run
- Add --short option to 'jug status' and 'jug execute'
- Fix bug with dictionary order in kwargs (fix by Andreas Sorge)
- Fix ipython colors (fix by Andreas Sorge)
- Sort tasks in 'jug status'

version **1.1** (Tue Mar 3 2015)
- Python 3 compatibility fixes
- fsync(directory) in file backend
- Jug hooks (still mostly undocumented, but already enabling internal code simplification)

version **1.0** (Tue May 20 2014)
- Adapt status output to terminal width (by Alex Ford)
- Add a newline at the end of lockfiles for file backend
- Add --cache-file option to specify file for ``status --cache``

version **0.9.7** (Tue Feb 18 2014)

- Fix use of numpy subclasses
- Fix redis URL parsing
- Fix ``shell`` for newer versions of IPython
- Correctly fall back on non-sqlite ``status``
- Allow user to call set_jugdir() inside jugfile

version **0.9.6** (Tue Aug 6 2013)

- Faster decoding
- Add jug-execute script
- Add describe() function
- Add write_task_out() function

version **0.9.5** (May 27 2013)

- Added debug mode
- Even better map.reduce.map using blocked access
- Python 3 support
- Documentation improvements

version **0.9.4** (Apr 15 2013)

- Add CustomHash wrapper to set __jug_hash__
- Print traceback on import error
- Exit when no progress is made even with barrier
- Use Tasklets for better jug.mapreduce.map
- Use Ipython debugger if available (patch by Alex Ford)
- Faster --aggressive-unload
- Add currymap() function

version **0.9.3** (Dec 2 2012)

- Fix parsing of ports on redis URL (patch by Alcides Viamontes)
- Make hashing robust to different orders when using randomized hashing
  (patch by Alcides Viamontes)
- Allow regex in invalidate command (patch by Alcides Viamontes)
- Add ``--cache --clear`` suboption to status
- Allow builtin functions for tasks
- Fix status --cache`` (a general bug which seems to be triggered mainly by
  ``bvalue()`` usage).
- Fix ``CompoundTask`` (broken by earlier ``__jug_hash__`` hook introduction)
- Make ``Tasklets`` more flexible by allowing slicing with ``Tasks``
  (previously, slicing with tasks was **not** allowed)

For older version see ``ChangeLog`` file.



.. image:: https://badges.gitter.im/Join%20Chat.svg
   :alt: Join the chat at https://gitter.im/luispedro/jug
   :target: https://gitter.im/luispedro/jug?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge
