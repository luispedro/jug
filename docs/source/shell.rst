=========
Jug Shell
=========

The ``jug shell`` subcommand opens up a shell within the environment of the
Jugfile. It can be used for debugging and exploration of the task structure.

To obtain a ``list`` of all tasks seen by jug you can run ``tasks = get_tasks()``

.. versionadded:: 1.6.5
    ``get_tasks()`` was only added to the shell in version 1.6.5. Before that you
    can access tasks directly by importing ``from jug.task import alltasks as tasks``.

Inside the environment, you can use the ``value(task)`` function to load
results (if available; otherwise, an exception is thrown).

.. versionadded:: 1.5
    ``invalidate(task)`` was only added to the shell in version 1.5. Before
    that, only ``task.invalidate()`` (non-recursive) was available.

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
