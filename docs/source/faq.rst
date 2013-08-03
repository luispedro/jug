==========================
Frequently Asked Questions
==========================

Why the name jug?
-----------------

The cluster I was using when I first started developing jug was called
"juggernaut". That is too long and there is a Unix tradition of 3-character
programme names, so I abbreviated it to jug.

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
a Python function and its arguments, every time you run jug, you build a
different task (unless you, by chance, draw twice the same number).

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
to be able to reproduce your results, it is a good idea, in general, if your
computation dependends of pseudo-random numbers, to be explicit about the
seeds. So, *this is a feature not a bug*.)

Will jug work on batch cluster systems (like SGE or PBS)?
---------------------------------------------------------

Yes, it was built for it.

There is no interaction with the batch system, but if you submit jobs that look
like::

    jug execute my_jug_script.py --jugdir=my_jug_dir

And it will work fine. Given that jobs can join the computation at any time and
all of the communication is through the backend (file system by default), jug
especially suited for these environments.

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

