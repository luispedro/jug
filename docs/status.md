# Status

## Simple Status

The `status` subcommand displays a summary of the computation status, for
example:

```
$ jug status
      Failed     Waiting       Ready    Complete      Active  Task name
-----------------------------------------------------------------------------------
           0           0           2           0           0  jugfile.compfeats
           0          10           0           0           0  jugfile.nfold
...................................................................................
           0          10           2           0           0  Total
```

Each task is in one of the following states:

- **Failed**: the task is locked and its lock is marked as failed. This
  happens when the task raised an exception while running with `jug execute
  --keep-failed` (otherwise, the lock is released and the task goes back to
  *Ready*), or, with the `file_keepalive` backend, when the process running
  it has died (see [backends](backends.md)). Failed tasks are not run again
  until you remove their locks with `jug cleanup --failed-only`.
- **Waiting**: the task cannot run yet, as some of its dependencies have not
  finished.
- **Ready**: all the dependencies of the task are available, so it can be run.
- **Complete**: the result of the task is available.
- **Active**: the task is locked, i.e., it is being run by a `jug execute`
  process (with the default filesystem backend, a task whose process was
  killed also remains *Active*, until you run `jug cleanup --locks-only`).

`jug status` exits with status 0 if all tasks are complete and 1 otherwise.

## Short Status

The same status as above, now in a `short` version:

```
$ jug status --short
12 tasks waiting to be run, 0 failed, 0 complete, (none active).
```

Once every task has finished, this becomes:

```
$ jug status --short
All tasks complete (12 tasks).
```

## Cached Status

If you have many tasks, then `jug status` can become pretty slow. One way to
speed it up is to use a cache:

```
$ jug status --cache
```

or:

```
$ jug status --cache --short
```

The first time you run it, it will be as slow as usual as it will parse the
jugfile and interrogate the store for every possible task. However, then it
will save a record which will enable it to speed up the next few times.

The cache is saved in the file `.jugstatus.sqlite3` in the current
directory. Use `--cache-file` to choose a different file (e.g., if you have
several jugfiles in the same directory):

```
$ jug status --cache --cache-file=analysis.jugstatus.sqlite3
```

To remove the cache (so that the next `jug status --cache` rebuilds it), use
`--clear`:

```
$ jug status --cache --clear
```

You should do this every time you change the jugfile.

**Note**: This is a fragile system, which should be used with care as the cache
can easily become out of sync with the jugfile used (`jugfile.py` in the
examples above). It is kept in jug as the speed gains can be quite spectacular
(from many seconds to instantaneous).

The cache can also become out of sync with the store: once a task is recorded
as finished, its result is never checked again. If results are removed (e.g.,
with `jug invalidate`, `jug cleanup`, or by deleting the jugdir), `jug status
--cache` will still report those tasks as finished. This also applies to the
exit code (0 if all tasks are finished, 1 otherwise), so do not rely on it in
scripts (e.g., `jug status --cache && ...`): use `jug status` without
`--cache` (or `jug check`) instead. Enabling the cache in a configuration file
(`cache = on` in the `[status]` section) affects every `jug status` call, so
use `jug status --cache --clear` whenever you need an accurate answer.
