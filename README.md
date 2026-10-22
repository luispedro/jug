# Jug: A Task-Based Parallelization Framework

Jug allows you to write code that is broken up into tasks and run
different tasks on different processors.

[![image](https://github.com/luispedro/jug/actions/workflows/python-package.yml/badge.svg)](https://github.com/luispedro/jug/actions/workflows/python-package.yml)
[![image](https://anaconda.org/conda-forge/jug/badges/downloads.svg)](https://anaconda.org/conda-forge/jug)
[![image](https://static.pepy.tech/personalized-badge/jug?period=total&units=international_system&left_color=black&right_color=blue&left_text=Downloads)](https://pepy.tech/project/jug)
[![Downloads](https://static.pepy.tech/badge/jug/month)](https://pepy.tech/project/jug)
[![image](https://img.shields.io/badge/CITATION-doi.org%2F10.5334%2Fjors.161-green.svg)](https://doi.org/10.5334/jors.161)

Its main backend uses the filesystem to communicate between processes
and works correctly over NFS, so you can coordinate processes on
different machines. Another is based on [Redis](https://redis.io/), so
the processes only need to be able to connect to a common Redis server.
See the [backends documentation](https://jug.readthedocs.io/en/latest/backends.html)
for all options.

Jug is a pure Python implementation and should work on any platform.

Python versions 3.10 and above are supported (will almost certainly work
on earlier versions as well, but they are not part of the [CI
suite](<https://github.com/luispedro/jug/actions>)).

*Documentation*: <https://jug.readthedocs.io/>

*Video*: On [vimeo](https://vimeo.com/8972696)

*Mailing List*: <https://groups.google.com/g/jug-users>

## Testimonials

"I've been using jug with great success to distribute the running of a
reasonably large set of parameter combinations" - Andreas Longva

## Install

You can install Jug with pip:

    pip install Jug

If you want to use `jug shell`, install IPython as well:

    pip install Jug ipython

Or, if you use [conda](https://anaconda.org/), you can install
jug from [conda-forge](https://conda-forge.org/) using the
following commands:

    conda config --add channels conda-forge
    conda install jug

## Citation

If you use Jug to generate results for a scientific publication, please
cite

> Coelho, L.P., (2017). Jug: Software for Parallel Reproducible
> Computation in Python. Journal of Open Research Software. 5(1), p.30.
>
> <https://doi.org/10.5334/jors.161>

## Short Example

Here is a one minute example. Save the following to a file called
`primes.py` (if you have installed jug, you can also obtain this example
by running `jug demo` on the command line):

    from jug import TaskGenerator

    @TaskGenerator
    def is_prime(n):
        from time import sleep

        # Sleep for 1 second, this runs too fast and is not a good demo
        sleep(1.)
        for j in range(2, n - 1):
            if (n % j) == 0:
                return False
        return True

    @TaskGenerator
    def count_primes(ps):
        return sum(ps)

    @TaskGenerator
    def write_output(n):
        with open('output.txt', 'wt') as output:
            output.write(f"Found {n} primes <= 100.\n")

    primes100 = []
    for n in range(2, 101):
        primes100.append(is_prime(n))

    n_primes = count_primes(primes100)
    write_output(n_primes)

This is a brute-force way to find all the prime numbers up to 100. Of
course, this is only for didactic purposes, normally you would use a
better method. Similarly, the `sleep` function is so that it does not
run too fast. Still, it illustrates the basic functionality of Jug for
embarrassingly parallel problems.

Type `jug status primes.py` to get:

          Failed     Waiting       Ready    Complete      Active  Task name
    -------------------------------------------------------------------------------------
               0           1           0           0           0  primes.count_primes
               0           0          99           0           0  primes.is_prime
               0           1           0           0           0  primes.write_output
    .....................................................................................
               0           2          99           0           0  Total

This tells you that you have 99 tasks called `primes.is_prime` ready to
run, while both other tasks are *waiting* (i.e., they need the
`primes.is_prime` tasks to finish). So run `jug execute primes.py &`.
You can even run multiple instances in the background (if you have
multiple cores, for example). After starting 4 instances and waiting a
few seconds, you can check the status again (with `jug status primes.py`):

          Failed     Waiting       Ready    Complete      Active  Task name
    -------------------------------------------------------------------------------------
               0           1           0           0           0  primes.count_primes
               0           0          63          32           4  primes.is_prime
               0           1           0           0           0  primes.write_output
    .....................................................................................
               0           2          63          32           4  Total

Now you have 32 tasks complete, 4 active (running), and 63 still ready.
Eventually, they will all finish (including `count_primes` and
`write_output`) and you can inspect the results with `jug shell
primes.py`. This requires `ipython` to be installed and will give you an
`ipython` shell. The `primes100` variable is available, but it is an
ugly list of `jug.Task` objects. To get the actual value, you call the
`value` function:

    In [1]: primes100 = value(primes100)

    In [2]: primes100[:10]
    Out[2]: [True, True, False, True, False, True, False, False, False, True]

## What's New

### Version 2.7.0

*Released 23 October 2026*

#### Compatibility notes

- Python 3.9 is no longer supported (it reached end-of-life in October 2025):
  jug now requires Python 3.10 or later.
- `jug execute` and `jug invalidate` select tasks by name using `--name`
  (strict) or `--pattern` (loose). The old `--target` option (and `--invalid`,
  for `jug invalidate`) is now a deprecated synonym of `--name` and prints a
  warning. This makes it **stricter** than before: `--target function` used to
  match any task whose name contained `function`
  ([GH #63](https://github.com/luispedro/jug/issues/63)), but now matches only
  tasks called `function`. For loose matching, use `--pattern function`, which
  matches a plain substring anywhere in the task name. Programmatic users:
  `execute_target` is replaced by `execute_name` and `execute_pattern`, and
  `invalidate` has a new `invalid_pattern` option alongside `invalid_name`.
- The hashes of tasks with `frozenset` arguments have changed, so their cached
  results will be recomputed the first time you run them with this version.
- `jug status` now exits with status 0 if all tasks are complete and 1
  otherwise, like `jug check` (before, the exit code was the number of
  finished tasks). With `--cache`, the exit code is only as accurate as the
  cache, so do not rely on it in scripts.
- `NoHash` (from `jug.unsafe`) now passes the *value* of a wrapped Task to the
  function (before, the function received the Task object itself).
- The `redis` backend requires redis-py 3.5 or later.
- `TimeTasks` (from `jug.hooks.execution`) stores the start time of the
  current task in `start_time` (before, it overwrote its own `start` method).
- Passing a Task inside a subclass of `list` or `tuple` (e.g., a
  `namedtuple`) now raises a `TypeError`. This was never supported. Use a
  plain `list`, `tuple` or `dict` instead.

#### Security fix

- `jug webstatus` now escapes the jugfile and task names and only accepts an
  integer for `?refresh=`. Before, these values were inserted into the page
  unescaped, which allowed injecting HTML/JavaScript into it.

#### User-visible improvements

- New `--name` and `--pattern` options for `jug execute` and `jug invalidate`
  (see above). An empty pattern is an error, as it would match every task.
- Shell completion: [argcomplete](https://pypi.org/project/argcomplete/) is
  supported and `jug --print-completion {bash,zsh,tcsh}` generates a
  completion script using [shtab](https://pypi.org/project/shtab/). Both are
  optional dependencies (`pip install 'jug[completion]'`).
- Python 3.15 is now supported.
- `return_tuple` can be imported directly from `jug`.
- A Task's function can be a `functools.partial` object.
- `jug webstatus` uses the same columns as `jug status`, shows failed tasks,
  and sorts the tasks by name.
- `jug execute --wait-cycle-time` accepts fractional values, and
  `jug execute` is faster at selecting the next task to run when there are
  many tasks.
- `jug execute` and `jug invalidate` warn if both a name and a pattern are set
  (which can only happen through configuration files).
- `jug.utils.jug_execute` includes the command and its exit code in the error
  message when the command fails.
- Summary tables respect the `COLUMNS` environment variable.
- The documentation is now written in Markdown, all examples were updated to
  match current behaviour, and previously undocumented subcommands, options,
  backends and hooks are now documented.

#### Internal improvements

- New functions `jug.utils.prepare_name_matcher` and
  `jug.options.build_parser()`.
- `CompoundTask` removes its temporary task in constant time.

#### Bugfixes

This release fixes many bugs. The most important are listed below (see the
[full history](https://jug.readthedocs.io/en/latest/history.html) for the
rest):

- `jug execute` on a jugfile with a barrier: waiting is bounded by
  `--nr-wait-cycles` overall (it could previously wait for up to about 75
  hours), and with `--keep-going`, failed tasks are not re-run on every
  re-load of the jugfile.
- Tasks wrapped in `CustomHash`, `NoHash` or a slice of `mapreduce.map`
  results are tracked as dependencies.
- `jug check` no longer takes exponential time on diamond-shaped task graphs.
- Hashes of frozensets and of numpy object arrays are now stable across
  processes (before, such tasks were never seen as finished).
- Several fixes to `jug pack` and the `file_store` pack: no lost or undone
  results, correct handling of numpy arrays and polars DataFrames, correct
  permissions of the pack file, no crash on concurrently removed files.
- `bvalue()` only treats a value as unavailable when a task it needs has not
  run yet, instead of swallowing any error.
- `jug.init(..., store=obj)` installs `obj` as the store.
- `--pdb` implies `--debug` and no longer opens a second debugger on exit;
  boolean flags can be set in configuration files, and `no`/`n` are read as
  false.
- `jug status --cache` fails with a clear message if the cache is invalid or
  cannot be opened or written.
- Fix a quadratic slowdown when loading large results.
- Fix `exit_when_true()`, `jug graph --file-format`, slicing of `map()`
  results with a step, `map`/`currymap` with `map_step=1` and a
  `TaskGenerator`, and reading UTF-8 jugfiles under a non-UTF-8 locale.

### Version 2.6.0

*Released 20 September 2026*

#### Compatibility notes

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

#### User-visible improvements

- Better error message when loading results fails (patch by Justin R.
  Porter, [GH #92](https://github.com/luispedro/jug/pull/92))
- Configuration files are now read as UTF-8 regardless of locale
- `jug cleanup` now reports the number of removed objects and of removed
  locks separately

#### Internal improvements

- Use `@property` and `@abstractmethod` instead of the deprecated
  `abstractproperty`
- Modernize Python idioms and update documentation

#### Bugfixes

- Fix `write_task_out` for numpy arrays, which are now written in `.npy`
  format (they were silently pickled instead)
- Fall back to pickle for numpy arrays of object dtype, which cannot be
  saved in numpy's native format
- `file_store.cleanup()` no longer deletes the temporary files of workers
  that are still running
- Fix the `tput` fallback in `get_terminal_size`
- Fix wrong exception type in `dict_store.cleanup()`
- Fix saving to/loading from a file backend in `jug.backends.dict_store`
  on Python 3 (pickle files must be opened in binary mode)
- Fix help text of `jug status --cache-file`

### Version 2.5.0

*Released 12 March 2026*

#### User-visible improvements

- Special case saving `polars` DataFrames in `file_store` for speed.
- More flexible parsing of booleans in `jug.options`.
- Support project-local configuration files (`.jugrc` or `jugrc`). Jug
  now walks up the directory tree from the current working directory (up
  to the git project root) looking for local configuration files. See
  [configuration](https://jug.readthedocs.io/en/latest/configuration.html)
  for details.
- Ship the Jug assistant skill in the Python package and add
  `jug install-skills --output DIR` to install it into Codex or Claude
  Code skills directories. See
  [ai-assistants](https://jug.readthedocs.io/en/latest/ai-assistants.html) for usage
  details.

#### Bugfixes

- Fix `_get_terminal_size_linux` for Python 3.14, which changed how
  `fcntl.ioctl` handles string arguments. Use `os.get_terminal_size()`
  instead (patch by justinrporter, [GH
  #90](https://github.com/luispedro/jug/issues/90)).
- Fix `jug.backends.dict_store` for Python 3.
- Fix `describe` in `jug.task` for Python 3.

### Version 2.4.0

*Released 8 May 2025*

#### User-visible improvements

- Adds support for lambda functions in `Tasklets`
- Adds `NoHash` class to disable hashing for some arguments. This is in
  `jug.unsafe` as it can be used to "fool" Jug, but it can be useful
  when there are nuisance arguments that are not relevant for the task
  (e.g., number of threads)
- jug.file_store: create files with better permissions

#### Internal improvements

- Convert to `pyproject.toml` for building

#### Bugfixes

- Better error detection for permission problems
- Bugfix when using local imports and `jug pack`

Drops support for versions of Python older than 3.7. Technically, it
should still work, but they are too old to test in Github CI, so we will
not support them.

### Version 2.3.1

*Released 5 November 2023*

- Update for Python 3.12

### Version 2.3.0

*Released 25 June 2023*

- jug shell: Add `get_filtered_tasks()`
- jug: Fix `jug --version` (which had been broken in the refactoring to
  use subcommands)
- jug shell: Fix message in jug shell when there are no dependencies (it
  would repeatedly print the message stating *this will only be run
  once*)
- jug pack: Make it much faster to invalidate elements
- file_store: ensure that the temporary directory exists
- Drops support for Python 3.4

For older version see `ChangeLog` file or the [full
history](https://jug.readthedocs.io/en/latest/history.html).
