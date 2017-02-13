=========
Jug Shell
=========

The ``jug shell`` subcommand opens up a shell within the environment of the
Jugfile. It can be used for debugging and exploration of the task structure.

Inside the environment, you can use the ``value()`` function to load results
(if available; otherwise, an exception is thrown).

You can call methods on task objects directly as well:

- ``run()``: run the task and return the result **even if the task has run
  before**.
- ``can_run()``: whether all dependencies are available
- ``can_load()``: whether the task has already run
- ``invalidate()``: remove the result of this task (**not recursive**, unlike
  the ``invalidate`` subcommand).

You can access the original function with the ``.f`` attribute as well.

Note
----

Jug shell requires `IPython <https://ipython.org>`__ to be installed.
