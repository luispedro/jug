=====================================================
Invalidating Jug Task Results (invalidate subcommand)
=====================================================

When you invalidate results of a task, you are telling jug that everything that
was computed using that function should no longer be used. Thus, any
result which depended on that function needs to be recomputed.

Invalidation is manual
----------------------

To invalidate a task, you need to use the ``invalidate`` command. Jug does not
detect that you fixed a bug in your code automatically.

Invalidation is dependency aware
--------------------------------

When you invalidate a task, all results that depend on the invalid results
will also be invalidated. This is what makes the invalidate subcommand so
powerful.

Example
-------

Consider the `British parliament example <text-example.html>`__ we used
elsewhere in this guide::

    allcounts = []
    for mp in MPs:
        article = get_data(mp)
        words = count_words(mp, article)
        allcounts.append(words)

    global_counts = add_counts(allcounts) # Here all processes must sync


Its dependency graph looks like this::

    M0 -> get_data -> count_words -> C0
    M1 -> get_data -> count_words -> C1
    M2 -> get_data -> count_words -> C2
    ...
    C0 C1 C2 -> add_counts -> avgs
    C0 + avgs -> divergence
    C1 + avgs -> divergence
    C2 + avgs -> divergence
    ...

This is a typical fan-in-fan-out structure. After you have run the code, ``jug
status`` will give you this output::

    \      Waiting       Ready    Finished     Running  Task name
    ----------------------------------------------------------------------------------
               0           0           1           0  jugfile.add_counts
               0           0         656           0  jugfile.count_words
               0           0         656           0  jugfile.divergence
               0           0         656           0  jugfile.get_data
    ..................................................................................
               0           0        1969           0  Total

Now assume that ``add_counts`` has a bug. Now you must:

1. Fix the bug (well, of course)
2. Rerun everything that could have been affected by the bug.

Jug invalidation helps you with the second task.

::

    $ jug invalidate --target add_counts
    Invalidated  Task name
    -----------------------------------------------------------
               1  jugfile.add_counts
             656  jugfile.divergence
    ...........................................................
             657  Total

will remove results for all the ``add_counts`` tasks, *and all the
``divergence`` tasks* because those results depended on results from
``add_counts``. Now, ``jug status`` gives us::

    \     Waiting       Ready    Finished     Running  Task name
    ------------------------------------------------------------------------------------
               0           1           0           0  jugfile.add_counts
               0           0         656           0  jugfile.count_words
             656           0           0           0  jugfile.divergence
               0           0         656           0  jugfile.get_data
    ....................................................................................
             656           1        1312           0  Total

So, now when you run ``jug execute``, ``add_counts`` will be re-run as will
everything that could possibly have changed as well.

