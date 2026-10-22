# History

## Unreleased

### Compatibility notes

Python 3.9 is no longer supported (it reached end-of-life in October 2025):
jug now requires Python 3.10 or later.

`jug execute` and `jug invalidate` select tasks by name using `--name`
(strict) or `--pattern` (loose). The old `--target` option (and
`--invalid`, for `jug invalidate`) is now a deprecated synonym of
`--name` and prints a warning. This makes it **stricter** than before:

- `--target function` used to match any task whose name contained
  `function`, so `jug invalidate --target function` would also invalidate
  `function_other` ([GH #63](https://github.com/luispedro/jug/issues/63)).
  It now matches only tasks called `function`. For loose matching, use
  `--pattern function`.
- `--pattern` matches a plain substring anywhere in the task name, so it
  matches more tasks than the old `--target` did: a pattern without a dot used
  to match only names (or dotted parts of names) that *started* with it (so
  `--target prime` did not match `primes.is_prime`), and regular expression
  characters were interpreted even outside `/.../`.
- If you use jug's options programmatically, `execute_target` is replaced by
  `execute_name` and `execute_pattern`, and `invalidate` has a new
  `invalid_pattern` option alongside `invalid_name` (which is now strict).

The hashes of tasks with `frozenset` arguments have changed (see the bugfix
below), so their cached results will be recomputed the first time you run them
with this version. This also applies to frozensets whose hash was stable
before (e.g., frozensets of numbers).

`jug status` now exits with status 0 if all tasks are complete and 1
otherwise, like `jug check` (before, the exit code was the number of finished
tasks, so `jug status && ...` failed when work had been done).

`NoHash` (from `jug.unsafe`) now passes the *value* of a wrapped Task to the
function. Before, the function received the Task object itself.

Passing a Task inside a subclass of `list` or `tuple` (e.g., a `namedtuple`)
now raises a `TypeError`. This was never supported: the function received the
Task object instead of its value, and hashing could fail with an obscure
error. Use a plain `list`, `tuple` or `dict` instead.

### Security fix

`jug webstatus` now escapes the jugfile and task names and only accepts an
integer for `?refresh=`. Before, these values were inserted into the page
unescaped, which allowed injecting HTML/JavaScript into it.

### User-visible improvements

- New `--name` option for `jug execute` and `jug invalidate`: selects
  tasks by their exact name, either fully qualified (`jugfile.function`) or
  just the function name (`function`). Wildcards are supported, so
  `--name 'function*'` matches both `function` and `function_other`.
- New `--pattern` option for `jug execute` and `jug invalidate`: matches a
  plain substring anywhere in the task name (or a regular expression, if
  written between slashes: `--pattern '/compute_.*/'`). This is a looser
  version of what `--target` used to do (see above). An empty pattern (`''`
  or `'//'`) is an error, as it would match every task (so that, e.g.,
  `jug invalidate --pattern "$TASK"` with an unset variable does not
  invalidate everything).
- `--target` and `--invalid` are deprecated (see above).
- Shell completion: [argcomplete](https://pypi.org/project/argcomplete/) is
  supported (`eval "$(register-python-argcomplete jug)"`) and
  `jug --print-completion {bash,zsh,tcsh}` generates a completion script using
  [shtab](https://pypi.org/project/shtab/). Both are optional dependencies
  (`pip install 'jug[completion]'`). See {doc}`subcommands`.
- Python 3.15 is now supported (and tested on CI).
- `return_tuple` can be imported directly from `jug` (`from jug import
  return_tuple`).
- `jug.utils.jug_execute`: the error raised when the command fails now
  includes the command and its exit code.
- `jug webstatus` uses the same column names and order as `jug status`
  (Failed, Waiting, Ready, Complete, Active), and shows failed tasks.
- A Task's function can be a `functools.partial` object. The partial is
  unwrapped, so `Task(partial(f, a), b)` is the same task as `Task(f, a, b)`.
- `jug execute --wait-cycle-time` (and `wait-cycle-time` in configuration
  files) accepts fractional values.
- `jug execute` is faster at selecting the next task to run when there are
  many tasks.
- Summary tables use `shutil.get_terminal_size()` to get the terminal width,
  so the `COLUMNS` environment variable is respected and the width is detected
  on all platforms (e.g., FreeBSD).
- `register_time_tasks()` prints mean times with two decimal places (e.g.,
  `123.46s`) instead of two significant digits (`1.2e+02s`).
- Documentation: all examples were updated to match current behaviour, and
  the subcommands, options, backends, and hooks that were missing are now
  documented. The documentation is now written in Markdown.

### Internal improvements

- New function `jug.utils.prepare_name_matcher`. `prepare_task_matcher` now
  matches a plain substring (or a `/regex/`) anywhere in the task name.
- `CompoundTask` removes its temporary task in constant time (instead of
  searching the list of all tasks, which was quadratic in the number of
  compound tasks).
- New function `jug.options.build_parser()`, which builds the full argument
  parser (split from `parse()`, so that it can be used by shell completion
  tools).

### Bugfixes

- `jug pack` creates the pack file with the same permissions as the result
  files (following the umask). Before, it was created with mode 0600, so, on
  a jugdir shared with a group, packed results became unreadable to the other
  users.
- `jug execute` and `jug invalidate` print a warning if both a name and a
  pattern are set. This can only happen when one of them comes from a
  configuration file (on the command line, `--name` and `--pattern` are
  mutually exclusive); only tasks matching both are selected. Before, this
  happened silently.
- `jug execute` on a jugfile with a barrier: the waiting time is bounded by
  `--nr-wait-cycles` overall. Before, each re-load of the jugfile waited the
  full time again, so a stuck task (e.g., failed with `--keep-failed`) could
  keep `jug execute` waiting for up to about 75 hours with the default
  settings. With `--keep-going`, a failed task is also no longer re-run every
  time the jugfile is re-loaded.
- Tasks wrapped in `CustomHash`, `NoHash` or a slice of the result of
  `mapreduce.map` are tracked as dependencies. Before, a task using them could
  be started before the tasks it depends on had run (and then fail).
- `recursive_dependencies` lists each dependency only once. Before, a task
  reachable by several paths was listed once per path, so that `jug check`
  took exponential time on diamond-shaped task graphs.
- `jug execute --keep-failed`: do not mark a task as failed when acquiring its
  lock raised an error (the lock is not held, and may belong to another
  worker).
- `jug execute --keep-going`: a task whose lock could not be acquired because
  of an error is no longer treated as failed for the rest of the run. It never
  ran, so it is retried when the jugfile is re-loaded (before, a transient
  error, e.g. from NFS or redis, skipped the task permanently).
- `jug.init(..., store=obj)` installs `obj` as the store of the tasks (before,
  it was ignored, and the previous store, `None` in a new process, was
  returned instead).
- `--pdb` implies `--debug`, as documented (before, it did not).
- `--pdb`: do not open a second debugger on jug's own exit. `jug execute`
  exits with status 1 when a task failed, and that `SystemExit` was caught and
  debugged as if it were an error.
- The global flags `--aggressive-unload`, `--short`, `--pdb` and `--debug` can
  be set in configuration files (before, the setting was ignored).
- `mapreduce.map` and `mapreduce.currymap` with `map_step=1` accept a
  `TaskGenerator` (before, they failed with `AttributeError: __name__`).
- `jug status --cache`: exit with a clear error message if the cache file is
  not a valid cache (before, it crashed with a traceback). Interrupting the
  cache lookup no longer falls back to loading the jugfile.
- `CompoundTask`: save the result once, instead of twice.
- `TaskGenerator`: raise the intended error message when pickling a function
  whose module cannot be found (instead of a `KeyError`).
- `dict_store`: `release()` and `fail()` on a lock which is not held have no
  effect (as for the other backends), instead of raising `KeyError`.
- `file_store`: sync the destination directory after renaming a file (instead
  of the source directory before), so that the rename is durable.
- `redis_store`: fix `close()`, which silently did nothing.
- `jug webstatus`: fix the duplicate `<head>` in the page.
- Jugfiles are read as Python source (UTF-8 by default, or as declared by a
  PEP 263 coding comment) independently of the locale. Before, a UTF-8
  jugfile failed with `UnicodeDecodeError` under, e.g., `LC_ALL=C`.
- Fix task hashes of frozensets and of numpy arrays with `dtype=object` (or
  structured dtypes with object fields), which could be different in every
  process, so these tasks were never seen as finished and parallel workers
  ran them repeatedly.
- `bvalue()` only treats the value as unavailable when a task it needs has not
  run yet. Before, any error (e.g., an `IndexError` in a Tasklet) was silently
  treated as an unsatisfied barrier and `jug execute` waited and then exited
  with status 0.
- Fix `exit_when_true()`, which always failed with a `TypeError` (unless
  `function_takes_Task=True` was passed).
- `jug graph`: fix `--file-format`, which did not accept an argument.
- `jug pack`: fix crash (`zlib.error`) when the jugdir contains small numpy
  arrays or polars DataFrames.
- `file_store`: fix concurrent changes to packed results (from `jug pack`)
  being lost or undone (e.g., invalidated results coming back). Removing
  results no longer rewrites the pack when nothing in it changed, and a
  failure to save the pack no longer leaves its lock held.
- `jug pack`: do not lose a result which is both in the pack and on disk
  (which can happen if another process packed it while this one had the store
  open). The packed value was re-packed and the newer file deleted.
- `file_store`: fix numpy structured arrays with object fields, which could
  be saved but not loaded.
- `file_store`: remove the temporary file when saving a result fails (e.g.,
  because it cannot be pickled); before, partial files accumulated.
- Fix quadratic slowdown when loading large results that are not numpy arrays
  (e.g., a 64 MiB bytes object took over 90 seconds to load; it now takes a
  fraction of a second).
- Fix `decompress_stream.seek()` with a negative offset.
- `jug.mapreduce`: fix slicing the result of `map()` with a step (e.g.,
  `m[::2]` or `m[::-1]` raised `IndexError`) and support negative indices.
- `jug.task.describe()` now recurses into tuples.
- `jug.init()`: fix calling it without a jugfile argument (it now defaults to
  `jugfile.py`, as documented).
- `jug --help`: fix the description of `jug pack` and of the `--jugdir`
  default.
- Configuration files: `no` and `n` are read as false for boolean options
  (before, e.g., `keep-going = no` turned the option on).
- Configuration files: find the project root (to search for `.jugrc` in
  parent directories) in git worktrees and submodules, where `.git` is a file.
- `jug test-jug`: exit with a non-zero status when pytest is not available.
- `register_time_tasks()`: print the timing summary only once with a jugfile
  that has barriers (before, once per re-load of the jugfile).
- `jug sleep-until`: do not accumulate duplicate tasks when re-loading a
  jugfile with barriers.
- `file_store`: report packed results (after `jug pack`) as computed in
  `metadata()` (used by `describe()` and `write_metadata()`).
- `Task.unlock()` and `Task.fail()` work when called before `Task.lock()`
  (before, they raised `AttributeError`).
- `redis_store.remove()` returns a `bool`, as documented.
- `examples/decrypt/brute.py`: fix reading the message (it was opened in text
  mode).

## Version 2.6.0

*Released 20 September 2026*

### Compatibility notes

Two changes alter task hashes, so cached results for the affected tasks will
be recomputed the first time you run them with this version:

- The pickle protocol used for hashing is now pinned to protocol 4. This only
  affects users of Python 3.14 and 3.15 (where pickle's default is protocol 5);
  Python 3.13 and earlier already used protocol 4. From now on, task hashes are
  stable across Python versions.
- Tasklets built from `lambda` functions are now hashed using the lambda's
  constants, referenced names, closure and default arguments (previously only
  its bytecode was used, so lambdas that differed only in those hashed
  identically).

### User-visible improvements

- Better error message when loading results fails (patch by Justin R. Porter,
  [GH #92](https://github.com/luispedro/jug/pull/92))
- Configuration files are now read as UTF-8 regardless of locale
- `jug cleanup` now reports the number of removed objects and of removed
  locks separately

### Internal improvements

- Use `@property` and `@abstractmethod` instead of the deprecated
  `abstractproperty`
- Modernize Python idioms and update documentation

### Bugfixes

- Fix `write_task_out` for numpy arrays, which are now written in `.npy`
  format (they were silently pickled instead)
- Fall back to pickle for numpy arrays of object dtype, which cannot be saved
  in numpy's native format
- `file_store.cleanup()` no longer deletes the temporary files of workers
  that are still running
- Fix the `tput` fallback in `get_terminal_size`
- Fix wrong exception type in `dict_store.cleanup()`
- Fix saving to/loading from a file backend in `jug.backends.dict_store` on
  Python 3 (pickle files must be opened in binary mode)
- Fix help text of `jug status --cache-file`

## Version 2.5.0

*Released 12 March 2026*

### User-visible improvements

- Special case saving `polars` DataFrames in `file_store` for speed.
- More flexible parsing of booleans in `jug.options`.
- Support project-local configuration files (`.jugrc` or `jugrc`). Jug now
  walks up the directory tree from the current working directory (up to the git
  project root) looking for local configuration files. See
  {doc}`configuration` for details.
- Ship the Jug assistant skill in the Python package and add
  `jug install-skills --output DIR` to install it into Codex or Claude Code
  skills directories. See {doc}`ai-assistants` for usage details.

### Bugfixes

- Fix `_get_terminal_size_linux` for Python 3.14, which changed how
  `fcntl.ioctl` handles string arguments. Use `os.get_terminal_size()`
  instead (patch by justinrporter, [GH #90](https://github.com/luispedro/jug/issues/90)).
- Fix `jug.backends.dict_store` for Python 3.
- Fix `describe` in `jug.task` for Python 3.

## Version 2.4.0

*Released 8 May 2025*

### User-visible improvements

- Adds support for lambda functions in `Tasklets`
- Adds `NoHash` class to disable hashing for some arguments. This is in
  `jug.unsafe` as it can be used to "fool" Jug, but it can be useful when
  there are nuisance arguments that are not relevant for the task (e.g., number
  of threads)
- jug.file_store: create files with better permissions

### Internal improvements

- Convert to `pyproject.toml` for building

### Bugfixes

- Better error detection for permission problems
- Bugfix when using local imports and `jug pack`

Drops support for versions of Python older than 3.7. Technically, it should
still work, but they are too old to test in Github CI, so we will not support
them.

## Version 2.3.1

*Released 5 November 2023*

- Update for Python 3.12

## Version 2.3.0

*Released 25 June 2023*

- jug shell: Add `get_filtered_tasks()`
- jug: Fix `jug --version` (which had been broken in the refactoring to use subcommands)
- jug shell: Fix message in jug shell when there are no dependencies (it would repeatedly print the message stating *this will only be run once*)
- jug pack: Make it much faster to invalidate elements
- file_store: ensure that the temporary directory exists
- Drops support for Python 3.4

## Version 2.2.3

*Released 26 May 2023*

- Fix `jug shell` for newer versions of IPython

## Version 2.2.2

*Released 19 July 2022*

- Fix `jug cleanup` when packs are used (`jug pack`)

## Version 2.2.0

*Released 4 May 2022*

- Add `jug pack` subcommand
- Make `get_tasks()` return a copy of the tasks instead of the internal list.
  Technically, it is possible that this is a breaking change for some
  workflows, but returning the internal version was arguably a bug
- Removed dependency on the `six` library as we no longer support Python 2.7.

## Version 2.1.1

*Released 18 March 2021*

- Include requirements files in distribution

## Version 2.1.0

*Released 18 March 2021*

- Improvements to webstatus (by Robert Denham)
- Removed Python 2.7 support
- Fix output encoding for Python 3.8
- Fix bug mixing `mapreduce()` & `status --cache`
- Make block_access (used in `mapreduce()`) much faster (20x)
- Fix important redis bug
- More precise output in `cleanup` command

## Version 2.0.2

*Released Thu Jun 11 2020*

### Bugfixes

- Fix command line argument parsing

## Version 2.0.1

*Released Thu Jun 11 2020*

### Bugfixes

- Fix handling of `JUG_EXIT_IF_FILE_EXISTS` environmental variable
- Fix passing an argument to `jug.main()` function
- Extend `--pdb` to exceptions raised while importing the jugfile (issue #79)

## Version 2.0.0

*Released Fri Feb 21 2020*

### User-visible improvements

1. Jug can now keep track of failed tasks.

Use `jug execute --keep-failed` to preserve locks on failing tasks and `jug
cleanup --failed-only` to remove locks from failed tasks. Similarly, `jug
status` and `jug graph` now display failed tasks

This avoids the situation where a failing task (for whatever reason) blocks the
rest of the process. It improves on `jug execute --keep-going` (which does the same)
as with `--keep-going`, each new process will attempt to run the task. If the
task reproducibly fails after a long period, this results in wasted
computation.

2. The [exit environmental variables](exit.md) are now checked by default.
   Create a file called `__jug_please_stop_running.txt` in the current
   working directory and `Jug` will stop after it finishes the current task.

### Bugfixes

- Fix `jug sleep-until` in the presence of barrier() (issue #71)

### Internal improvements

- jug.backends.base_store has 1 new method `listlocks`
- jug.backends.base_lock has 2 new methods `fail` and `is_failed`

## Version 1.6.9

*Released Tue Aug 6 2019*

- Fix saving on newer version of numpy

## Version 1.6.8

*Released Wed July 10 2019*

- Add `cached_glob()` function
- Fix NoLoad (issue #73)
- Fix `jug shell`'s invalidate function with Tasklets (issue #77)

## Version 1.6.7

*Released Fri Apr 13 2018*

- Fix issue with deeply recursive dependency structures and barrier()
- Allow mapreduce.map() results to be used as dependencies

## Version 1.6.6

*Released Sat Apr 7 2018*

- Fix bug in shell's invalidate() function
- Fix wrong dependency handling with mapreduce.map()

## Version 1.6.5

*Released Mon Mar 12 2018*

- Add get_tasks() to 'jug shell' and document 'from jug.task import
  alltasks' (patch by Renato Alves)

## Version 1.6.4

*Released Thu Nov 2 2017*

- Fix exit_after_n_tasks. It would previously execute one task too many

## Version 1.6.3

*Released Wed Nov 1 2017*

- Add citation request

## Version 1.6.2

*Released Thu Oct 26 2017*

- Add return_value argument to jug_execute
- Add exit_env_vars

## Version 1.6.1

*Released Thu Aug 29 2017*

- Fix bug with `invalidate()` in the shell

## Version 1.6.0

*Released Thu Aug 24 2017*

- Add 'graph' subcommand - Generates a graph of tasks
- 'jug execute --keep-going' now ends with non-zero exit code in case of failures
- Fix bug with cleanup in dict_store not providing the number of removed records
- Add 'jug cleanup --keep-locks' to remove obsolete results without affecting locks

## Version 1.5.0

*Released Sun Jul 16 2017*

- Add 'demo' subcommand
- Add is_jug_running() function
- Fix bug in finding config files
- Improved --debug mode: check for unsupported recursive task creation
- Add invalidate() to shell environment
- Use ~/.config/jug/jugrc as configuration file
- Add experimental support for extensible commands, use `~/.config/jug/jug_user_commands.py`
- jugrc: execute_wait_cycle_time_secs is now execute_wait_cycle_time
- Expose sync_move in jug.utils

## Version 1.4.0

*Released Tue Jan 3 2017*

- Fix bug with writing very large objects to disk
- Smarter handling of --aggressive-unload (do not unload what will be immediately necessary)
- Work around corner case in `jug shell` command
- Add test-jug subcommand
- Add return_tuple decorator

## Version 1.3.0

*Released Tue Nov 1 2016*

- Update `shell` subcommand to IPython 5
- Use ~/.config/jugrc as configuration file
- Cleanup usage string
- Use `bottle` instead of `web.py` for webstatus subcommand
- Add `jug_execute` function
- Add timing functionality

## Version 1.2.2

*Released Sat Jun 25 2016*

- Fix bugs in shell subcommand and a few corner cases in encoding/decoding results

## Version 1.2.1

*Released Mon Feb 15 2016*

- Changed execution loop to ensure that all tasks are checked (issue #33 on github)
- Fixed bug that made 'check' or 'sleep-until' slower than necessary
- Fixed jug on Windows (which does not support fsync on directories)
- Made Tasklets use slightly less memory

## Version 1.2

*Released Thu Aug 20 2015*

- Use HIGHEST_PROTOCOL when pickle()ing
- Add compress_numpy option to file_store
- Add register_hook_once function
- Optimize case when most (or all) tasks are already run
- Add --short option to 'jug status' and 'jug execute'
- Fix bug with dictionary order in kwargs (fix by Andreas Sorge)

- Fix ipython colors (fix by Andreas Sorge)
- Sort tasks in 'jug status'

## Version 1.1

*Released Tue Mar 3 2015*

- Python 3 compatibility fixes
- fsync(directory) in file backend
- Jug hooks (still mostly undocumented, but already enabling internal code simplification)

## Version 1.0

*Released Tue May 20 2014*

- Adapt status output to terminal width (by Alex Ford)
- Add a newline at the end of lockfiles for file backend
- Add --cache-file option to specify file for `status --cache`

## Version 0.9.7

*Released Tue Feb 18 2014*

- Fix use of numpy subclasses
- Fix redis URL parsing
- Fix `shell` for newer versions of IPython
- Correctly fall back on non-sqlite `status`
- Allow user to call set_jugdir() inside jugfile

## Version 0.9.6

*Released Tue Aug 6 2013*

- Faster decoding
- Add jug-execute script
- Add describe() function
- Add write_task_out() function

## Version 0.9.5

*Released May 27 2013*

- Added debug mode
- Even better map.reduce.map using blocked access
- Python 3 support
- Documentation improvements

## Version 0.9.4

*Released Apr 15 2013*

- Add CustomHash wrapper to set `__jug_hash__`
- Print traceback on import error
- Exit when no progress is made even with barrier
- Use Tasklets for better jug.mapreduce.map
- Use IPython debugger if available (patch by Alex Ford)
- Faster --aggressive-unload
- Add currymap() function

## Version 0.9.3

*Released Dec 2 2012*

- Fix parsing of ports on redis URL (patch by Alcides Viamontes)
- Make hashing robust to different orders when using randomized hashing
  (patch by Alcides Viamontes)
- Allow regex in invalidate command (patch by Alcides Viamontes)
- Add `--cache --clear` suboption to status
- Allow builtin functions for tasks
- Fix `status --cache` (a general bug which seems to be triggered mainly by
  `bvalue()` usage).
- Fix `CompoundTask` (broken by earlier `__jug_hash__` hook introduction)
- Make `Tasklets` more flexible by allowing slicing with `Tasks`
  (previously, slicing with tasks was **not** allowed)

## Version 0.9.2

*Released Nov 4 2012*

- More flexible mapreduce()/map() functions
- Make TaskGenerator pickle()able and hash()able
- Add invalidate() method to Task
- Add --keep-going option to execute
- Better help message

## Version 0.9.1

*Released Jun 11 2012*

- Add --locks-only option to cleanup subcommand
- Make cache file (for `status` subcommand) configurable
- Add `webstatus` subcommand
- Add bvalue() function
- Fix bug in `shell` subcommand (`value` was not in global namespace)
- Improve identity()
- Fix bug in using Tasklets and --aggressive-unload
- Fix bug with Tasklets and sleep-until/check

## Version 0.9

- In the presence of a barrier(), rerun the jugfile. This makes barrier much
  easier to use.
- Add set_jugdir to public API
- Added CompoundTaskGenerator
- Support subclassing of Task
- Avoid creating directories in file backend unless it is necessary
- Add jug.mapreduce.reduce (which mimics the builtin reduce)

For older versions, see the
[`ChangeLog` file](https://github.com/luispedro/jug/blob/main/ChangeLog).
