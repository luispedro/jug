=====================================================
Invalidating Jug Task Results (invalidate subcommand)
=====================================================

When you invalidate results of a task, you are telling jug that everything that
was computed using that function needs should no longer be used. Thus, any
result which depended on that function needs to be recomputed.

Invalidation is manual
----------------------

To invalidate a task, you need to use the ``invalidate`` command. Jug does not
detect that you fixed a bug in your code automatically.

Invalidation is dependency aware
--------------------------------

When you do invalidate a task, all results that depend on the invalid results
will also be invalidated. This is what makes the invalidate subcommand so
powerful.

Example
-------

Consider the MP example we useed elsewhere in this guide:

Its dependency graph looks like this::

    M0 -> getdata -> countwords -> C0
    M1 -> getdata -> countwords -> C1
    M2 -> getdata -> countwords -> C2
    ...
    C0 C1 C2 -> addcounts -> avgs
    C0 + avgs -> divergence
    C1 + avgs -> divergence
    C2 + avgs -> divergence
    ...

This is a typical fan-in-fan-out structure. After you have run the code, ``jug
status`` will give you this output::


Now assume that ``addcounts`` has a bug. Now you must:

1. Fix the bug (well, of course)
2. Rerun everything that could have been affected by the bug.

Jug invalidation helps you with the second task.::

    jug invalidate addcounts

will remove results for all the ``addcounts`` tasks, *and all the divergence
tasks* because those results depended on results from ``addcounts``. Now, ``jug
status`` gives us::


So, now when you run ``jug execute``, ``addcounts`` will be re-run as will
everything that could possibly have changed as well.

