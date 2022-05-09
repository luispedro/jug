=========
Jug Shell
=========

The ``jug shell`` subcommand opens up a shell within the environment of the
Jugfile. It can be used for debugging and exploration of the task structure.

To obtain a ``list`` of all tasks seen by jug you can run ``tasks =
get_tasks()``. As a convenience function, you can also use
``get_filtered_tasks()`` to obtain filtered versions:

    all_tasks = get_tasks()

    loadable = get_filtered_tasks(loadable=True)
    failed = get_filtered_tasks(failed=True)


This returns only tasks that fulfil the filtering criteria used


.. versionadded:: 2.3
   ``get_filtered_tasks`` was added in version 2.3. In previous versions, you
   had to filter the output of ``get_tasks()`` yourself


Inside the environment, you can use the ``value(task)`` function to load
results (if available; otherwise, an exception is thrown).

The ``invalidate(task)`` function invalidates the results of its argument and
all dependents, **recursively**, much like the ``jug invalidate`` subcommand.


You can call methods on ``Task`` objects directly as well:

- ``run()``: run the task and return the result **even if the task has run
  before**.
- ``can_run()``: whether all dependencies are available
- ``can_load()``: whether the task has already run
- ``invalidate()``: remove the result of this task (**not recursive**, unlike
  the ``invalidate`` subcommand, unlike the invalidate function).

You can access the original function with the ``.f`` attribute as well.

Note
----

Jug shell requires `IPython <https://ipython.org>`__ to be installed.
