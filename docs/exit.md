# Early exit

`jug execute` can be told to exit early (i.e., before all tasks are done),
either with environment variables or with code in the jugfile (which uses
[hooks](hooks.md)). Afterwards, you can start new processes to continue the
computation.

Note that, in all cases, _the process will only exit after finishing a task_.
If you set a time limit and that time is reached while a task is running, then
the task will keep going.

## Maximum running time

The following variables specify the maximum running time:

- `JUG_MAX_HOURS`
- `JUG_MAX_MINUTES`
- `JUG_MAX_SECONDS`

The names should be self-explanatory, but note that they are **additive**, so
that `JUG_MAX_HOURS=1 JUG_MAX_MINUTES=30` means that the process will run for 1
hour **and** 30 minutes. The values must be integers (e.g., `JUG_MAX_HOURS=1.5`
is an error; use `JUG_MAX_MINUTES=90` instead). The time is checked after each
task finishes.

```python
from jug.hooks.exit_checks import exit_after_time
exit_after_time(hours=..., minutes=..., seconds=...)
```

## Exiting if a file exists

This can be specified by the environmental variable `JUG_EXIT_IF_FILE_EXISTS`,
but the filename `__jug_please_stop_running.txt` is always added as well.
Relative paths (including `__jug_please_stop_running.txt`) are relative to the
current working directory of the `jug execute` process (not to the jugfile or
the jugdir). The check is performed *before* each task is executed, so creating
the file will not interrupt a task that is already running.

To achieve the same with code, run:

```python
from jug.hooks.exit_checks import exit_if_file_exists
exit_if_file_exists('__jug_please_stop_running.txt')
```

## Exiting after a specified number of tasks

Use the variable `JUG_MAX_TASKS` (which must be an integer) or run the
following code:


```python
from os import environ
from jug.hooks.exit_checks import exit_after_n_tasks
exit_after_n_tasks(int(environ['JUG_MAX_TASKS']))
```


## Disabling the checks

`jug execute --no-check-environment` ignores the `JUG_*` environment variables
listed above as well as the `__jug_please_stop_running.txt` file (and the file
given by `JUG_EXIT_IF_FILE_EXISTS`). Checks set up in code in the jugfile are
not affected.
