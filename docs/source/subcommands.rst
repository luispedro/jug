===========
Subcommands
===========

Jug is organised as a series of subcommands. They are called by ``jug
subcommand jugfile.py [OPTIONS]``. This is similar to applications such as
version control systems.


Major Subcommands
-----------------

execute
~~~~~~~

The main subcommand of jug is `execute`. Execute executes all your tasks. If
multiple jug processes are running at the same time, they will synchronise so
that each will run different tasks and combine the results.

It works in the following loop::

    while not all_done():
        t = next_task()
        if t.lock():
            t.run()
            t.unlock()

The actual code is much more complex, of course.

status
~~~~~~

You can check the status of your computation at any time with status.

shell
~~~~~

Shell drops you into an ipython shell where your jugfile has been loaded. You
can look at the results of any Tasks that have already run. It works even if
other tasks are running in the background.

IPython needs to be installed for ``shell`` to work.

`More information about jug shell <shell.html>`__


Minor Subcommands
-----------------

check
~~~~~

Check is simple: it exits with status 0 if all tasks have run, 1 otherwise.
Useful for shell scripting.

sleep-until
~~~~~~~~~~~

This subcommand will simply wait until all tasks are finished before exiting.
It is useful for monitoring a computation (especially if your terminal has an
option to display a pop-up or bell when it detects activity). It **does not**
monitor whether errors occur!

invalidate
~~~~~~~~~~

You can invalidate a group of tasks (by name). It deletes all results from
those tasks and from any tasks that (directly or indirectly) depend on them.
You need to give the subcommand the name with the ``--invalid`` option.

cleanup
~~~~~~~

Removes all elements in the store that are not used by your jugfile.


Extending Subcommands
---------------------

.. note::
    This feature is still experimental

.. automodule:: jug.subcommands
