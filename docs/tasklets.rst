========
Tasklets
========
.. versionadded:: 0.8
   Tasklets were added in version 0.8, starting with the betas (named 0.7.9..)

.. versionchanged:: 2.4.0
   Since version 2.4.0, Tasklets can use a lambda function

A Tasklet is a light-weight task. It looks very similar to a Task *except that
it does not save its results to disk*. Every time you need its output, it is
recomputed. Other than that, you can pass it around, just like a Task.

They also get sometimes automatically generated.

Before Tasklets
---------------

Before Tasklets were a part of jug, often there was a need to write some
connector Tasks::


    def select_first(t):
        return t[0]

    result = Task(...)
    result0 = Task(select_first, result)

    next = Task(next_step,result0)


This obviously works, but it has two drawbacks:

1. It is not natural Python
2. It is space inefficient on disk. You are saving ``result`` and then
   ``result0``.

With Tasklets
-------------

First version::

    def select_first(t):
        return t[0]
    result = Task(...)
    result0 = Tasklet(result, select_first)
    next = Task(next_step,result0)

If you look closely, you will see that we are now using a *Tasklet*. This
jugfile will work exactly the same, but it will not save the ``result0`` to
disk. So you have a performance gain.

It is still not natural Python. However, the Task can *generate Tasklets
automatically*:

Second version::

    result = Task(...)
    next = Task(next_function, result[0])

Now, we have a version that is both idiomatic Python and efficient.

