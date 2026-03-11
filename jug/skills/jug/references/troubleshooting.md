# Jug Troubleshooting

Operational guidance for failed tasks, stale locks, invalidation, and debugging.

## When a Task Raises an Exception

Default behavior:

- Jug logs the exception
- `jug execute` stops unless `--keep-going` was set
- the task lock is released
- a later `jug execute` retries the task

This means a normal task failure does **not** leave a persistent failed lock by
default.

Typical recovery:

```bash
jug status jugfile.py
jug execute jugfile.py
```

Use `--keep-going` if you want Jug to continue running independent tasks after
a failure:

```bash
jug execute jugfile.py --keep-going
```

## Failed Locks

Failed locks matter in two cases:

- you ran with `jug execute --keep-failed`
- you used `file_keepalive:` and a dead worker's lock aged into failed state

In those cases, clear failed locks before retrying:

```bash
jug cleanup jugfile.py --failed-only
jug execute jugfile.py
```

Use `--keep-failed` when you want failures to remain visible in `jug status`
instead of being retried automatically on the next run.

## Stale Locks After Worker Crashes

With the default file store, a killed worker can leave a stale lock behind.
If all workers are stopped and you want to unblock the graph:

```bash
jug cleanup jugfile.py --locks-only
jug execute jugfile.py
```

Only do this when you know no healthy worker is still running those tasks.

## Code Changed, but Jug Reuses Old Results

Jug hashes task names and arguments, not function bytecode. Changing task
implementation does not invalidate cached results automatically.

Invalidate by target name:

```bash
jug invalidate jugfile.py --target process
```

Invalidate by fully qualified name:

```bash
jug invalidate jugfile.py --target mymodule.process
```

Invalidate by regex:

```bash
jug invalidate jugfile.py --target /compute_.*/
```

`jug invalidate` removes matching results and all downstream dependents. Re-run
`jug execute` afterwards.

## Jug Appears Stuck Waiting

Common causes:

- a dependency failed earlier
- a stale lock is blocking a ready task
- a `barrier()` or `bvalue()` split requires another execution pass
- you restricted execution too much with `--target`

Useful checks:

```bash
jug status jugfile.py
jug status jugfile.py --short
```

If you suspect target filtering is the problem, re-run without `--target`.

If the jugfile uses `barrier()` or `bvalue()`, waiting can be normal while Jug
completes the tasks required to finish parsing the rest of the graph.

## Debugging Hash and Mutation Problems

Use debug mode when task behavior seems inconsistent or cached results do not
match expectations:

```bash
jug execute jugfile.py --debug
```

`--debug` adds extra hash checks and can catch mutable-argument mistakes.

Use `--pdb` if you want an interactive debugger on exceptions:

```bash
jug execute jugfile.py --pdb
```

`--pdb` implies `--debug`.

## Shell for Investigation

Use `jug shell` when you need to inspect tasks interactively:

```bash
jug shell jugfile.py
```

Useful helpers in the shell:

- `value(task)` loads a result
- `invalidate(task)` removes one task result and downstream dependents
- `get_tasks()` lists all tasks
- `get_filtered_tasks(loadable=True|failed=True|available=True)` filters by state

Example:

```python
failed = get_filtered_tasks(failed=True)
available = get_filtered_tasks(available=True)
```

## Cleaning Orphaned Results

If the shape of the task graph changed and old cached results are no longer
referenced:

```bash
jug cleanup jugfile.py
```

This removes orphaned objects from the current jugdir.

## Backend-Specific Notes

Filesystem store:

- default backend
- safest general-purpose choice on local disk or shared filesystems
- dead workers can leave stale locks until you clean them

`file_keepalive:` store:

- refreshes lock timestamps while a worker is alive
- can distinguish dead-worker locks from active ones after enough time passes
- useful when crash detection matters more than absolute simplicity

`dict_store`:

- useful for tests or small local experiments
- not a multi-machine coordination backend

Redis store:

- good when workers do not share a filesystem
- requires separate Redis setup and operations discipline
