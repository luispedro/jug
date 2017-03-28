==========================
Frequently Asked Questions
==========================

Why the name jug?
-----------------

The cluster I was using when I first started developing jug was called
"juggernaut". That is too long and there is a Unix tradition of 3-character
programme names, so I abbreviated it to jug.

How to work with multiple computers?
------------------------------------

The typical setting is that all the computers have access to a networked
filesystem like NFS. This means that they all "see" the same files. In this
case, the default file-based backend will work nicely.

You need to start separate ``jug execute`` processes on each node.

See also the answer to the next question if you are using a batch system or the
`bash utilities page <bash.html>`__ if you are not.

Will jug work on batch cluster systems (like SGE/LFS/PBS)?
----------------------------------------------------------

Yes, it was built for it.

The simplest way to do it is to use a job array.

On LFS, it would be run like this::

  bsub -o output.txt -J "jug[1-100]" jug execute myscript.py

For SGE, you often need to write a script. For example::

  cat >>jug1.sh <<EOF
  #!/bin/bash

  exec jug execute myscript.py
  EOF

  chmod +x jug1.sh

Now, you can run a job array::

  qsub -t 1-100 ./jug1.sh


Alternatively, depending on your set up, you can pass in the script on STDIN::


    echo jug execute myscript.py | qsub -t 1-100

In any case, 100 jobs would start running with jug synchronizing their outputs.

Given that jobs can join the computation at any time and all of the
communication is through the backend (file system by default), jug is
especially suited for these environments.

The project `gridjug <http://gridjug.readthedocs.io/>`__ integrates jug with
`gridmap <https://github.com/pygridtools/gridmap>`__ to help run jug on SGE
clusters (this is an external project).

How do I clean up locks if jug processes are killed?
----------------------------------------------------

Jug will attempt to clean up when exiting, including if it receives a SIGTERM
signal on Unix. However, there is nothing it can do if it receives a SIGKILL (or
if the computer crashes).

The solution is to run ``jug cleanup`` to remove all the locks.

In some cases, you can avoid the problem in the first place by making sure that
SIGTERM is being properly delivered to the jug process.

For example, if you executing a script that only runs jug (like in the previous
question), then use ``exec`` to replace the script by the jug process.

Alternatively, in bash you can set a ``trap`` to catch and propagate the
``SIGTERM``::

    #!/bin/bash
    N_JOBS=10

    pids=""
    for i in $(seq $N_JOBS); do
        jug execute &
        pids="$! $pids"
    done
    trap "kill -TERM $pids; exit 1" TERM
    wait


It doesn't work with random input!
----------------------------------

Normally the problem boils down to the following::

    from jug import Task
    from random import random

    def f(x):
        return x*2

    result = Task(f, random())

Now, if you check ``jug status``, you will see that you have one task, an ``f``
task. If you run ``jug execute``, jug will execute your one task. But, now, if
you check ``jug status`` again, there is still one task that needs to be run!

While this may be surprising, it is actually correct. Everytime you run the
script, you build a task that consists of calling ``f`` with a different number
(because it's a randomly generated number). Given that tasks are defined as the
combination of a Python function and its arguments, every time you run jug, you
build a different task (unless you, by chance, draw twice the same number).

My solution is typically **to set the random seed at the start of the
computation explicitly**::

    from jug import Task
    from random import random, seed

    def f(x):
        return x*2

    seed(123) # <- set the random seed
    result = Task(f, random())

Now, everything will work as expected.

(As an aside: given that jug was developed in a context where it is important
to be able to reproduce your results, it is generally a good idea that if your
computation depends on pseudo-random numbers, you be explicit about the
seeds. So, *this is a feature not a bug*.)

Why does jug not check for code changes?
----------------------------------------

1) It is very hard to get this right. You can easily check Python code (with
dependencies), but checking into compiled C is harder. If the system runs any
command line programmes you need to check for them (including libraries) as
well as any configuration/datafiles they touch.

You can do this by monitoring the programmes, but it is no longer portable (I
could probably figure out how to do it on Linux, but not other operating
systems) and it is a lot of work.

It would also slow things down. Even if it checked only the Python code: it
would need to check the function code & all dependencies + global variables at
the time of task generation.

I believe `sumatra <http://pythonhosted.org/Sumatra/>`__ accomplishes this.
Consider using it if you desire all this functionality.

2) I was also afraid that this would make people wary of refactoring their
code. If improving your code even in ways which would not change the results
(refactoring) makes jug recompute 2 hours of results, then you don't do it.

3) Jug supports explicit invalidation with jug invalidate. This checks your
dependencies. It is not automatic, but often you need a person to understand
the code changes in any case.

Can jug handle non-pickle() objects?
------------------------------------

Short answer: No.

Long answer: Yes, with a little bit of special code. If you have another way to
get them from one machine to another, you could write a special backend for
that. Right now, only ``numpy`` arrays are treated as a special case (they are
not pickled, but rather saved in their native format), but you could extend
this. Ask on the `mailing list <http://groups.google.com/group/jug-users>`_ if
you want to learn more.

Is jug based on a background server?
------------------------------------

No. Jug processes do not need a server running. They need a shared *backend*.
This may be the filesystem or a *redis* database. But **jug does not need any
sort of jug server**.

Can I pass command line arguments to a Jugfile?
-----------------------------------------------

Yes. They will be available using ``sys.argv`` as usual.

If you need to pass arguments starting with a dash, you can use ``--`` (double
dash) to terminate option processing. For example, if your jugfile contains::

    import sys
    print(sys.argv)

Now you can call it as::

    # Argv[0] is the name of the script
    $ jug execute
    ['jugfile.py']

    $ jug execute jugfile.py
    ['jugfile.py']

    # Using a jug option does not change ``sys.argv``
    $ jug execute --verbose=info jugfile.py
    ['jugfile.py']

    $ jug execute --verbose=info jugfile.py argument
    ['jugfile.py', 'argument']

    # Use -- to terminate argument processing
    $ jug execute --verbose=info jugfile.py argument -- --arg --arg2=yes
    ['jugfile.py', 'argument', '--arg', '--arg2=yes']

