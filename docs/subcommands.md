# Subcommands

Jug is organised as a series of subcommands. They are called by `jug
subcommand jugfile.py [OPTIONS]`. This is similar to applications such as
version control systems.

## Major Subcommands

### execute

The main subcommand of jug is `execute`. Execute executes all your tasks. If
multiple jug processes are running at the same time, they will synchronise so
that each will run different tasks and combine the results.

It works in the following loop:

```
while not all_done():
    t = next_task()
    if t.lock():
        t.run()
        t.unlock()
```

The actual code is much more complex, of course.

`jug execute` accepts the following options:

`--name NAME`, `--pattern PATTERN`
: Only execute the tasks that match, using the same rules as
  [invalidate](#invalidate). Dependencies are not added automatically: a
  matching task whose inputs have not been computed (by another process) just
  waits for them.

`--keep-going`
: By default, a process stops at the first task that raises an exception.
  With `--keep-going`, it logs the error and continues with the remaining
  tasks (it still exits with status 1 at the end).

`--keep-failed`
: Normally, the lock of a task that failed is released, so another process
  will try it again. With `--keep-failed`, the lock is kept and marked as
  failed: `jug status` lists the task as *Failed* and no process runs it
  again until you run `jug cleanup --failed-only` (or `--locks-only`).

`--wait-cycle-time SECONDS`, `--nr-wait-cycles N`
: When no task is ready to run (because the remaining tasks are waiting for
  results that other processes are still computing), jug sleeps for
  `--wait-cycle-time` seconds (default: 12) and checks again, up to
  `--nr-wait-cycles` times (default: 150, so that the total is 30 minutes),
  before giving up.

`--no-check-environment`
: Do not check the `JUG_*` environment variables or the
  `__jug_please_stop_running.txt` file (see [Early exit](exit.md)).

`jug-execute jugfile.py [OPTIONS]` is a shortcut for `jug execute
jugfile.py [OPTIONS]` (it is installed alongside `jug`).

### status

You can check the status of your computation at any time with status. Like
`check`, it exits with status 0 if all tasks have run, 1 otherwise.

### shell

Shell drops you into an ipython shell where your jugfile has been loaded. You
can look at the results of any Tasks that have already run. It works even if
other tasks are running in the background.

IPython needs to be installed for `shell` to work.

[More information about jug shell](shell.md)

## Minor Subcommands

### check

Check is simple: it exits with status 0 if all tasks have run, 1 otherwise.
Useful for shell scripting.

### sleep-until

This subcommand will simply wait until all tasks are finished before exiting.
It is useful for monitoring a computation (especially if your terminal has an
option to display a pop-up or bell when it detects activity). It **does not**
monitor whether errors occur!

### invalidate

You can invalidate a group of tasks (by name). It deletes all results from
those tasks and from any tasks that (directly or indirectly) depend on them.
You need to give the subcommand the name with the `--name` option (which
must match exactly, but accepts wildcards such as `'function*'`) or with the
`--pattern` option (which matches any task whose name contains the pattern,
or a regular expression written as `/regex/`).

### cleanup

Removes all elements in the store that are not used by your jugfile, as well
as all locks. The following (mutually exclusive) options change what is
removed:

`--locks-only`
: Remove all locks, but keep all results. This is useful if processes were
  killed and left behind locks for tasks that are no longer running. **Do not
  run it while other processes are executing tasks**, as their locks would be
  removed too.

`--failed-only`
: Remove only the locks of failed tasks (see `jug execute --keep-failed`),
  so that those tasks can be run again.

`--keep-locks`
: Remove unused results, but keep all locks.

### count

Prints the number of tasks of each type (i.e., the number of tasks with the
same name). Unlike `status`, it does not check which tasks have run.

### graph

Writes a diagram of the dependencies between task types to `jugfile.dot` (for
`jugfile.py`), in [Graphviz](https://graphviz.org/) format, and runs the
`dot` command to render it to `jugfile.png`. Each node is labelled with the
number of failed (F), waiting (W), ready (R), active (A) and complete (C)
tasks of that type.

`--file-format FORMAT`
: Render to another format supported by `dot` (e.g., `svg` or `pdf`)
  instead of `png`.

`--no-status`
: Leave out the task counts (which require checking the store for every
  task).

If Graphviz is not installed, the `.dot` file is still written and can be
rendered later.

### webstatus

Starts a web server showing the status of the computation in a table that is
refreshed every 3 seconds (add `?refresh=N` to the URL to change this). It
requires [bottle](https://bottlepy.org/) (`pip install bottle`).

`--port PORT`
: The port to listen on (default: 8080).

`--ip IP`
: The address to listen on (default: `localhost`). Use `0.0.0.0` to make the
  page reachable from other machines.

### pack

Combines small result files (up to 512 bytes) of a filesystem jugdir into a
single file (`packs/jugpack` inside the jugdir), which reduces the number of
files. This only works with the default filesystem backend. Run it when no
other jug processes are using the jugdir.

### demo

Creates a directory called `jug-demo/` with an example jugfile (`primes.py`)
and prints instructions on how to run it.

### test-jug

Runs jug's internal test suite (requires `pytest`). This is useful to check
whether jug works correctly on your system.

### install-skills

Copies the bundled Jug assistant skill to a target skills directory. This is
useful for Codex and Claude Code integration:

```
jug install-skills --output ~/.codex/skills
jug install-skills --output .claude/skills
```

See {doc}`ai-assistants` for the full workflow and invocation examples.

## Extending Subcommands

```{note}
This feature is still experimental
```

```{eval-rst}
.. automodule:: jug.subcommands
```

## Shell completion

Jug supports tab-completion of subcommands and options in your shell. Two
optional packages provide this; install them both with:

```
pip install jug[completion]
```

### Dynamic completion with argcomplete

[argcomplete](https://kislyuk.github.io/argcomplete/) works with bash, zsh,
fish, and others. To enable it for the current shell session:

```
eval "$(register-python-argcomplete jug)"
```

Add this line to your shell's startup file (e.g., `~/.bashrc`) to make it
permanent. Alternatively, run `activate-global-python-argcomplete` once to
enable it for all argcomplete-enabled programs.

### Static completion script with shtab

[shtab](https://github.com/iterative/shtab) generates a completion script
ahead of time (bash, zsh, and tcsh are supported). Jug can print it directly:

```
jug --print-completion bash > ~/.local/share/bash_completion/completions/jug
jug --print-completion zsh > ~/.zfunc/_jug
```

(For zsh, `~/.zfunc` must be in your `fpath`.) This is equivalent to
running shtab's own command-line tool on Jug's parser:

```
shtab --shell=bash jug.options.build_parser
```

The generated script is static, so it needs to be regenerated if you upgrade
Jug (or add user subcommands) and want completion to reflect the changes.

```{note}
`jug-execute` does not support completion, only `jug` itself.
```
