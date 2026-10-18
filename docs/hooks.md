# Hooks

Hooks are functions that `jug execute` calls at specific points, for example,
after each task. You can register them in your jugfile to extend jug's
behaviour (e.g., to log progress or to exit early):

```python
from jug.hooks import register_hook

def report(t):
    print(f'Finished {t.name}')

register_hook('execute.task-executed1', report)
```

The known hooks are:

`execute.task-loadable(Task)`
: A task was skipped because its result is already available.

`execute.task-pre-execute(Task)`
: A task is about to be executed (its lock has been acquired).

`execute.task-executed1(Task)`
: A task has been executed successfully (it is not called if the task raised
  an exception). A function registered here can call `sys.exit()` to make the
  jug process exit.

`execute.finished_pre_status()`
: `jug execute` has finished running tasks, and the summary table is about to
  be printed.

`execute.finished_post_status()`
: The summary table has been printed.

Return values of hook functions are ignored.

If your jugfile uses [barriers](barrier.md), `jug execute` imports it more
than once, and each import registers the hooks again. To avoid this, use
`register_hook_once`, which takes an extra identifier and ignores later calls
with the same name and identifier:

```python
from jug.hooks import register_hook_once

register_hook_once('execute.task-executed1', 'report', report)
```

## Built-in uses of hooks

- The functions in `jug.hooks.exit_checks` use the
  `execute.task-executed1` hook to exit early (see [Early exit](exit.md)).
- `jug.hooks.execution.register_time_tasks()` records how long each task
  takes and prints the average time per task type at the end of `jug
  execute`:

  ```python
  from jug.hooks.execution import register_time_tasks
  register_time_tasks()
  ```

```{eval-rst}
.. automodule:: jug.hooks
    :no-index:
    :members: register_hook, register_hook_once

.. automodule:: jug.hooks.execution
    :no-index:
    :members: register_time_tasks
```
