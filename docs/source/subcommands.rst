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
You need to give the subcommand the name with the ``--name`` option (which
must match exactly, but accepts wildcards such as ``'function*'``) or with the
``--pattern`` option (which matches any task whose name contains the pattern,
or a regular expression written as ``/regex/``).

cleanup
~~~~~~~

Removes all elements in the store that are not used by your jugfile.

install-skills
~~~~~~~~~~~~~~

Copies the bundled Jug assistant skill to a target skills directory. This is
useful for Codex and Claude Code integration::

    jug install-skills --output ~/.codex/skills
    jug install-skills --output .claude/skills

See :doc:`ai-assistants` for the full workflow and invocation examples.


Extending Subcommands
---------------------

.. note::
    This feature is still experimental

.. automodule:: jug.subcommands

Shell completion
----------------

Jug supports tab-completion of subcommands and options in your shell. Two
optional packages provide this; install them both with::

    pip install jug[completion]

Dynamic completion with argcomplete
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`argcomplete <https://kislyuk.github.io/argcomplete/>`__ works with bash, zsh,
fish, and others. To enable it for the current shell session::

    eval "$(register-python-argcomplete jug)"

Add this line to your shell's startup file (e.g., ``~/.bashrc``) to make it
permanent. Alternatively, run ``activate-global-python-argcomplete`` once to
enable it for all argcomplete-enabled programs.

Static completion script with shtab
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`shtab <https://github.com/iterative/shtab>`__ generates a completion script
ahead of time (bash, zsh, and tcsh are supported). Jug can print it directly::

    jug --print-completion bash > ~/.local/share/bash_completion/completions/jug
    jug --print-completion zsh > ~/.zfunc/_jug

(For zsh, ``~/.zfunc`` must be in your ``fpath``.) This is equivalent to
running shtab's own command-line tool on Jug's parser::

    shtab --shell=bash jug.options.build_parser

The generated script is static, so it needs to be regenerated if you upgrade
Jug (or add user subcommands) and want completion to reflect the changes.

.. note::

    ``jug-execute`` does not support completion, only ``jug`` itself.
