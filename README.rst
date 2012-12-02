Jug: A Task-Based Parallelization Framework
-------------------------------------------

Jug allows you to write code that is broken up into
tasks and run different tasks on different processors.

It uses the filesystem to communicate between processes and
works correctly over NFS, so you can coordinate processes on
different machines.

Jug is a pure Python implementation and should work on any platform.

*Website*: `http://luispedro.org/software/jug <http://luispedro.org/software/jug>`_

*Documentation*: `http://packages.python.org/Jug <http://packages.python.org/Jug>`_

*Video*: On `vimeo <http://vimeo.com/8972696>`_ or `showmedo
<http://showmedo.com/videotutorials/video?name=9750000;fromSeriesID=975>`_

*Mailing List*: `http://groups.google.com/group/jug-users
<http://groups.google.com/group/jug-users>`_

Short Example
.............

Here is a one minute example. Save the following to a file called ``primes.py``::

    from jug import TaskGenerator
    from time import sleep

    @TaskGenerator
    def is_prime(n):
        sleep(1.)
        for j in xrange(2,n-1):
            if (n % j) == 0:
                return False
        return True

    primes100 = map(is_prime, xrange(2,101))

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


What's New
..........

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


version **0.9.2** (Nov 4 2012):
- More flexible mapreduce()/map() functions
- Make TaskGenerator pickle()able and hash()able
- Add invalidate() method to Task
- Add --keep-going option to execute
- Better help messsage

version **0.9.1** (Jun 11 2012):
- Add --locks-only option to cleanup subcommand
- Make cache file (for ``status`` subcommand) configurable
- Add ``webstatus`` subcommand
- Add bvalue() function
- Fix bug in ``shell`` subcommand (``value`` was not in global namespace)
- Improve identity()
- Fix bug in using Tasklets and --aggressive-unload
- Fix bug with Tasklets and sleep-until/check

version **0.9**:
- In the presence of a barrier(), rerun the jugfile. This makes barrier much
  easier to use.
- Add set_jugdir to public API
- Added CompoundTaskGenerator
- Support subclassing of Task
- Avoid creating directories in file backend unless it is necessary
- Add jug.mapreduce.reduce (which mimicks the builtin reduce)


For older version see ``ChangeLog`` file.

Roadmap
.......

Version 1.0
'''''''''''

Version 1.0 is just around the corner. After 0.8 is done, there really are not
that many features left. More flexible configuration, a bit more caching, and
we are done.

After version 1.0
'''''''''''''''''

I want to start adding bells&whistles through extensions. Things like timing,
more active monitoring, &c.

