# Jug Common Patterns

Recipes and utilities for common parallelization patterns in Jug.

---

## MapReduce

`jug.mapreduce` provides three functions for processing collections in parallel.

### `jug.mapreduce.map(mapper, sequence, map_step=4)`

Apply a function to every element of a list in parallel.

```python
from jug.mapreduce import map as jug_map
from jug import TaskGenerator

@TaskGenerator
def process(item):
    ...

results = jug_map(process, my_list, map_step=4)
# results[i] ≈ process(my_list[i]), but computed in parallel
```

- `map_step` controls how many list elements are grouped into a single task.
  Increase it if individual items are too fast; decrease it for slow items.
- Returns a `block_access` object that behaves like a list of task results.

### `jug.mapreduce.currymap(mapper, sequence, map_step=4)`

Like `map` but each element of `sequence` is a tuple unpacked as arguments:

```python
from jug.mapreduce import currymap

pairs = [(img, param) for img in images for param in params]
results = currymap(process_with_params, pairs)
# results[i] ≈ process_with_params(*pairs[i])
```

### `jug.mapreduce.reduce(reducer, inputs, reduce_step=8)`

Reduce a list of task results using an associative, commutative function:

```python
from jug.mapreduce import reduce as jug_reduce

total = jug_reduce(add, partial_sums)
```

The reducer must be associative and commutative because jug may apply it in
any order for parallelism.

### `jug.mapreduce.mapreduce(reducer, mapper, inputs, map_step=4, reduce_step=8)`

Map and reduce in one call:

```python
from jug.mapreduce import mapreduce

total = mapreduce(add, compute_partial, inputs)
```

---

## `identity()` — Hash Large Objects Once

When the same large object (e.g. a big array or list) is used as an argument
to many tasks, jug re-hashes it for each task. Wrap it in `identity()` to
hash it once and reference the cached result thereafter.

```python
from jug.utils import identity
from jug import Task

large_data = list(range(1_000_000))
large_data = identity(large_data)   # creates a Task; hashed only once

results = [Task(process, large_data, i) for i in range(1000)]
```

`value(identity(x)) == x` — it is the identity function, but implemented as
a cached task.

---

## `timed_path()` — Depend on an External File

By default jug hashes a filename string, not the file contents. If the file
changes, tasks depending on it won't automatically re-run. Use `timed_path`
to make the hash sensitive to the file's modification time and size.

```python
from jug.utils import timed_path
from jug import TaskGenerator

input_file = timed_path('data/input.csv')

@TaskGenerator
def load(path):
    ...

data = load(input_file)   # re-runs if input.csv is touched or changes size
```

`timed_path` returns a `CustomHash` wrapper that behaves like the string path
but hashes using `mtime + size`.

---

## `jug_execute()` — Shell Commands as Tasks

Wrap shell commands in tasks to integrate external tools into the pipeline.

```python
from jug.utils import jug_execute
from jug import Task

# Simple command:
step1 = jug_execute(['my_tool', '--input', 'data.txt', '--output', 'out.txt'])

# Ordered execution (run step2 after step1 finishes):
step2 = jug_execute(['post_process', 'out.txt'], run_after=step1)

# Use return_value to pass a filename to downstream tasks:
outfile = 'results.txt'
produced = jug_execute(['compute', '--out', outfile], return_value=outfile)
load_results = Task(load, produced)   # depends on jug_execute via filename
```

- `check_exit=True` (default) raises an error if the command returns non-zero.
- `run_after` accepts any task value; its contents are ignored — only the
  dependency is used.
- `return_value` is returned by the task and can be passed to downstream tasks.

---

## `CompoundTaskGenerator` — Hide Intermediate Tasks

By default, `jug status` shows every intermediate task. Use
`CompoundTaskGenerator` to group them into one logical unit.

```python
from jug import CompoundTaskGenerator

@CompoundTaskGenerator
def preprocess_and_align(sample):
    cleaned = clean(sample)
    aligned = align(cleaned)
    return aligned

result = preprocess_and_align(my_sample)
```

`jug status` sees `preprocess_and_align` as a single task group rather than
separate `clean` and `align` entries. The underlying tasks are still computed
individually.

---

## `NoHash` — Exclude Non-Deterministic Arguments

Sometimes a task has an argument that should not affect the cache key — e.g.
a `--threads` count or a log level. Wrap it in `NoHash` to exclude it from
the hash while still passing it to the function.

```python
from jug import TaskGenerator
from jug.unsafe import NoHash

@TaskGenerator
def compute(data, threads):
    ...

result = compute(data, NoHash(8))   # changing threads won't invalidate cache
```

**Warning:** Only use `NoHash` when the argument truly doesn't affect the
output. Misuse leads to stale results silently served from cache.

---

## `value_after()` Helper — Ordering Tasks with File Side-Effects

If two tasks both write to (or read from) the same file path without
a data dependency, jug cannot infer ordering. Define a small helper and use it
to impose the dependency explicitly.

```python
from jug import Task
from jug.utils import identity

def value_after(val, token):
    return identity([val, token])[0]

write_task = Task(write_file, 'output.txt', data)
read_task  = Task(read_file, value_after('output.txt', write_task))
```

This helper returns `val`, but only after `token` has completed, making
`read_task` depend on `write_task`.

---

## `iteratetask` — Fixed-Length Iterator over Task Results

When a task returns a sequence of known length, `iteratetask` unpacks it into
indexed tasklets without running the task:

```python
from jug import iteratetask
from jug import Task

result_task = Task(return_pair, ...)
a, b = iteratetask(result_task, 2)   # a = result_task[0], b = result_task[1]
```

No error is raised if the actual length differs — that only surfaces at
`value()` time. For unknown-length results use `bvalue`.

---

## `return_tuple` — Unpack Tuple Results

Decorator that makes a `@TaskGenerator` return a tuple of tasklets directly:

```python
from jug import TaskGenerator
from jug.task import return_tuple

@return_tuple(2)
@TaskGenerator
def compute_pair(x):
    return x, x + 1

a, b = compute_pair(10)   # a and b are Tasklets
```

The size `n` is checked at runtime when the task result is loaded.

---

## `CustomHash` — Custom Hash Function

When you need control over how an argument is hashed:

```python
from jug.utils import CustomHash
from jug import Task

def my_hash(obj):
    from jug.hash import hash_one
    return hash_one(obj.canonical_form())

arg = CustomHash(my_object, my_hash)
Task(process, arg)
```

Alternatively, add a `__jug_hash__` method to your class that returns `bytes`.

---

## `cached_glob` — Glob as a Cached Task

Useful when the list of input files may change between runs and you want the
glob result to be stable across the computation:

```python
from jug.utils import cached_glob
from jug import Task

files = cached_glob('data/*.csv')   # result is sorted and cached
results = [Task(process, f) for f in files]
```

`cached_glob` is implemented using a cached task around a sorted glob. It
computes eagerly during jugfile import if no cached result exists.

---

## Pattern: Two-Stage Pipeline with `bvalue`

When stage 2 task count depends on a stage 1 result:

```python
from jug import TaskGenerator, bvalue

@TaskGenerator
def find_regions(image_path):
    # returns a list of region coordinates
    ...

@TaskGenerator
def analyze_region(image_path, region):
    ...

@TaskGenerator
def summarize(analyses):
    ...

image = 'sample.tif'
regions_task = find_regions(image)

# Stop here until find_regions is done:
regions = bvalue(regions_task)

analyses = [analyze_region(image, r) for r in regions]
result = summarize(analyses)
```

---

## Pattern: Parameter Grid Search

```python
from jug import TaskGenerator
import itertools

@TaskGenerator
def train(data, lr, depth):
    ...

@TaskGenerator
def pick_best(scores):
    return max(scores, key=lambda s: s['val_acc'])

data = load_data()
params = list(itertools.product([1e-3, 1e-4], [3, 5, 10]))
scores = [train(data, lr, depth) for lr, depth in params]
best = pick_best(scores)
```

---

## Pattern: NFS-Safe File Store

The default file store uses atomic rename, making it safe on NFS. No special
configuration is required. For extra resilience on slow NFS:

```ini
[execute]
wait-cycle-time = 30
```

Increase the wait cycle time if workers frequently see apparent lock collisions
due to NFS attribute caching delays.
