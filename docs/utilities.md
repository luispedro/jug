# Utilities

The module `jug.utils` has a few functions which are meant to be used in
writing jugfiles (a few more are in `jug.task` and `jug.io`, see the end of
this page).

## Identity

This is simply implemented as:

```
@TaskGenerator
def identity(x):
    return x
```

This might seem like the most pointless function, but it can be helpful in
speeding things up. Consider the following case:

```
from glob import glob

def load(fname):
   return open(fname).readlines()

@TaskGenerator
def process(inputs, parameter):
    ...

inputs = []
for f in glob('*.data'):
    inputs.extend(load(f))
# inputs is a large list

results = {}
for p in range(1000):
    results[p] = process(inputs, p)
```

How is this processed? Every time `process` is called, a new `jug.Task` is
generated. This task has two arguments: `inputs` and an integer. When the hash
of the task is computed, both its arguments are analysed. `inputs` is a large
list of strings. Therefore, it is going to take a very long time to process all
of the hashes.

Consider the variation:

```
from jug.utils import identity

# ...
# same as above

inputs = identity(inputs)
results = {}
for p in range(1000):
    results[p] = process(inputs, p)
```

Now, the long list is only hashed once! It is transformed into a `Task` (we
reuse the name `inputs` to keep things clear) and each `process` call can
now compute its hash very fast.

### Using `identity` to induce dependencies

`identity` can also be used to introduce dependencies. One can define a
helper function:

```
def value_after(val, token):
    from jug.utils import identity
    return identity( [val, token] )[0]
```

Now, this function, will always return its first argument, but will only run
once its second argument is available. Here is a typical use case:

1. Function `process` takes an output file name
2. Function `postprocess` takes as input the output filename of `process`

Now, you want to run `process` and **then** `postprocess`, but since
communication is done with files, Jug does not see that these functions depend
on each other. `value_after` is the solution:

```
token = process(input, ofile='output.txt')
postprocess(value_after('output.txt', token))
```

This works independently of whatever `process` returns (even if it is
`None`).

## jug_execute

This is a simple wrapper around `subprocess.call()`. It adds two important
pieces of functionality:

1. it checks the exit code and raises an exception if not zero (this can be
   disabled by passing `check_exit=False`).

2. It takes an argument called `run_after` which is ignored but can be used
   to declare dependencies between tasks. Thus, it can be used to ensure that a
   specific process only runs after something else has run:

   ```
   from jug.utils import jug_execute
   from jug import TaskGenerator

   @TaskGenerator
   def my_computation(input, output_filename):
       ...

   token = my_computation(input, 'output.txt')
   # We want to run gzip, but **only after** `my_computation` has run:
   jug_execute(['gzip', 'output.txt'], run_after=token)
   ```

3. It takes an argument called `return_value`, which is returned (unchanged)
   once the command has run. This is often a cleaner way to chain steps that
   communicate through files, as the name of the output file becomes the
   result of the task, which can then be passed on to the next step:

   ```
   from jug.utils import jug_execute

   sorted_file = jug_execute(['sort', '-o', 'sorted.txt', 'input.txt'],
                             return_value='sorted.txt')
   # `sorted_file` is a Task whose value is 'sorted.txt', so this
   # automatically depends on the previous step:
   jug_execute(['gzip', sorted_file])
   ```

## cached_glob

`cached_glob` is a simple utility to perform the following common operation:

```
from glob import glob
from jug import CachedFunction
files = CachedFunction(glob, pattern)
files.sort()
```

where `pattern` is a glob pattern, can be simply written as:

```
from jug.utils import cached_glob
files = cached_glob(pattern)
```

Note that the glob is run while the jugfile is being loaded (the first time)
and its result is saved in the store, as a `jug.utils.glob_sort` task (which
shows up in `jug status`). Afterwards, the saved result is used, so files
which are created later are **not** picked up. To have the glob run again,
invalidate it:

```
$ jug invalidate --name glob_sort
```

As `cached_glob` returns a plain list (not a task), tasks which use it are not
invalidated by this, but tasks which receive a different list of files have a
different hash, so they will be run (while results for the files which were
already there are reused).

## NoHash

This is imported from the `jug.unsafe` module as it bypasses the hashing
mechanism and can lead to incorrect results if used incorrectly.

This marks certain arguments to Tasks as not being part of the hash that
defines the results. It can be useful for arguments that do not change the
results, but nonetheless need to be passed to functions.

Example usage:

```
from jug.unsafe import NoHash
from jug.utils import jug_execute

jug_execute(['SemiBin2', 'single_easy_bin',
                '--cpus', NoHash('8'),
                '-i', 'input/contigs.fna.gz',
                '--bam', 'input/mapped.bam',
                '--output', 'output'
                ])
```

## Inspecting tasks

`jug.task.describe(t)` returns a description of how the result of task `t`
is computed, as nested dictionaries and lists with the name of each task and
its arguments (recursively including the tasks it depends on).

`jug.task.recursive_dependencies(t, max_level=-1)` iterates over all the
tasks that `t` depends on, directly or indirectly (use `max_level` to limit
the depth).

## Writing results to files

`jug.io.write_task_out(t, 'output.pkl')` creates a task that writes the
result of task `t` to a file: numpy arrays are saved in `.npy` format (load
them with `numpy.load`), and everything else is pickled. If you also pass
`metadata_fname`, the output of `describe(t)` is written to that file, in
YAML (the default, which requires [PyYAML](https://pyyaml.org/)) or JSON
(`metadata_format='json'`). `jug.io.write_metadata` writes only the
metadata.

```{eval-rst}
.. automodule:: jug.utils
    :no-index:
    :members:
```
