# Jug Shell

The `jug shell` subcommand opens up a shell within the environment of the
Jugfile. It can be used for debugging and exploration of the task structure.

To obtain a `list` of all tasks seen by jug you can run `tasks =
get_tasks()`. As a convenience function, you can also use
`get_filtered_tasks()` to obtain filtered versions:

```
all_tasks = get_tasks()

loadable = get_filtered_tasks(loadable=True)
failed = get_filtered_tasks(failed=True)
```

This returns only tasks that fulfil the filtering criteria used.

```{versionadded} 2.3
`get_filtered_tasks` was added in version 2.3. In previous versions, you had to filter the output of `get_tasks()` yourself
```

Inside the environment, you can use the `value(task)` function to load
results (if available; otherwise, an exception is thrown).

To load everything at once, call `load_all()`. This replaces every variable
defined in the jugfile by its value: for example, if the jugfile contains
`results = [compute(i) for i in range(10)]`, then, after `load_all()`,
`results` is a list with the 10 results instead of a list of tasks. Variables
whose value cannot be loaded (e.g., because some of their tasks have not run
yet) are left unchanged and an error message is printed for each of them.

The `invalidate(task)` function invalidates the results of its argument and
all dependents, **recursively**, much like the `jug invalidate` subcommand.

You can call methods on `Task` objects directly as well:

- `run()`: run the task and return the result **even if the task has run
  before**.
- `can_run()`: whether all dependencies are available
- `can_load()`: whether the task has already run
- `invalidate()`: remove the result of this task (**not recursive**, unlike
  both the `invalidate` subcommand and the `invalidate()` shell function).

You can access the original function with the `.f` attribute as well.

## Note

Jug shell requires [IPython](https://ipython.org) to be installed.
