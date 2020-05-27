# Early exit

_This functionality is available since 1.7, but needed to be explicitly
activated until version 2.0_

Note that, in all cases, _the process will only exit after finishing a task_.
If you set a time limit and that time is reach while a task is running, then
the task will keep going.

## Maximum running time

The following variables specify the maximum running time:

- `JUG_MAX_HOURS`
- `JUG_MAX_MINUTES`
- `JUG_MAX_SECONDS`

The names should be self-explanatory, but note that they are **additive**, so
that `JUG_MAX_HOURS=1 JUG_MAX_MINUTES=30` means that the process will run for 1
hour **and** 30 minutes.

```python
from jug.hooks.exit_checks import exit_after_time
exit_after_time(hours=..., minutes=..., seconds=...)
```

## Exiting if a file exists

This can be specified by the environmental variable `JUG_EXIT_IF_FILE_EXISTS`,
but the filename `__jug_please_stop_running.txt` is always added as well.

To achieve the same with code, run:

```python
from jug.hooks.exit_checks import exit_if_file_exists
exit_if_file_exists('__jug_please_stop_running.txt')
```

## Exiting after a specified number of tasks

Use the variable `JUG_MAX_TASKS` or run the following code:


```python
from jug.hooks.exit_checks import exit_after_n_tasks
exit_after_n_tasks(int(environ['JUG_MAX_TASKS']))
```

