---
name: jug
description: >
  This skill should be used when the user wants to parallelize Python tasks
  with Jug, write a jugfile, run jug execute/status/invalidate/cleanup/shell,
  understand task dependencies, use barriers or bvalue, apply mapreduce
  patterns, debug failed tasks, invalidate stale results, or choose a jugdir
  backend (filesystem, Redis, dict_store, file_keepalive).
---

# Jug: Task-Based Parallelization for Python

Jug lets you write plain Python that runs transparently across many processes
or machines. You write a **jugfile** describing your computation as tasks; one
or more `jug execute` workers pick up and run those tasks, caching results in
a **jugdir**. Workers coordinate through locking — no message-passing code
required.

## 1. Jug's Execution Model

1. **Jugfile is imported** to collect tasks. Every call to a `@TaskGenerator`
   function appends a `Task` object to a global registry; no computation
   happens yet.
2. **Workers run `jug execute`**, which imports the jugfile, walks the task
   graph, and runs any task whose dependencies are already done.
3. **Results are stored in jugdir** (a directory of files by default). Each
   task's result file is named after the task's hash (function name + arguments).
4. **Multiple workers cooperate** by atomically locking a task's result slot
   before running it. With the default file store, a killed worker can leave a
   stale lock that blocks the task until you run `jug cleanup --locks-only`.
   The `file_keepalive:` backend can detect dead workers and mark old locks as
   failed instead.
5. **Jugfiles with `barrier()` / `bvalue()`** require multiple passes. After
   a barrier, jug re-imports the jugfile so downstream tasks can be constructed
   from upstream results.

## 2. Writing a Jugfile

```python
from jug import TaskGenerator

@TaskGenerator
def process(filename):
    # do expensive work, return a picklable result
    ...

@TaskGenerator
def aggregate(results):
    ...

# Build the task graph — this runs at import time, instantly
results = [process(f) for f in filenames]
summary = aggregate(results)
```

Key rules:

- **Decorate with `@TaskGenerator`**: calling `process(f)` now returns a
  `Task` object, not the result. Jug calls the real function later.
- **Pass tasks as arguments**: `aggregate(results)` receives the *result* of
  each `process` task when it runs.
- **No lambdas**: tasks must be importable top-level functions.
- **Good task granularity**: each task should take at least a few seconds.
  Too many tiny tasks creates overhead; too few large tasks wastes parallelism.
- **Tasks must be pure** (or at least idempotent): jug may run them multiple
  times in edge cases, and their result is identified purely by their hash.

### Using `Task` directly

You can also build tasks without the decorator:

```python
from jug import Task
t = Task(my_function, arg0, arg1, keyword=value)
```

### Subscripting task results (`Tasklet`)

```python
t = some_task(...)
first_element = t[0]   # a Tasklet — not stored separately
```

A `Tasklet` is a lightweight view on a task's result. It is not cached
independently in the jugdir.

## 3. Task Dependencies

Dependencies are declared implicitly by passing tasks as arguments:

```python
features = compute_features(image)     # Task A
cluster  = run_kmeans(features, k=5)   # Task B, depends on A
score    = compute_score(cluster)      # Task C, depends on B
```

Jug traverses lists, tuples, and dicts of tasks automatically.

### `barrier()` — wait for all preceding tasks

```python
from jug import barrier, value

stage1_results = [step1(x) for x in inputs]
barrier()                          # stops here until all stage1 tasks finish
counts = value(stage1_results[0])  # now safe to call value()
stage2_results = [step2(c) for c in range(counts)]
```

`barrier()` causes the jugfile to stop being parsed at that line until every
previously declared task is complete. This is required when the *number* of
downstream tasks depends on an upstream result.

### `bvalue()` — wait for a single task

```python
from jug import bvalue

splits = split_file(input_path)    # returns list of filenames
for block in bvalue(splits):       # stops here until `splits` is done
    process_block(block)
```

`bvalue(t)` is equivalent to `barrier()` + `value(t)` but only blocks on `t`,
making it faster when only one result is needed before continuing. Use
`bvalue` in preference to `barrier()` whenever possible.

## 4. Running and Monitoring

### Start workers

```bash
# On each machine / in each terminal:
jug execute jugfile.py

# Restrict to a subset of tasks:
jug execute jugfile.py --target process

# Continue after task failures:
jug execute jugfile.py --keep-going
```

By default jug waits up to 30 minutes (150 cycles × 12 s) for new tasks to
appear (useful for jugfiles with barriers). Tune with `--wait-cycle-time` and
`--nr-wait-cycles`.

### Check progress

```bash
jug status jugfile.py           # full table: Failed/Waiting/Ready/Complete/Active
jug status jugfile.py --short   # one-line summary
jug status jugfile.py --cache   # faster repeated calls (uses SQLite cache)
```

### Test whether everything finished

```bash
jug check jugfile.py   # exits 0 if all tasks complete, 1 otherwise
```

Use in scripts: `jug check && post_process.sh`

### Interactive exploration

```bash
jug shell jugfile.py
```

Inside the shell you get a Python prompt with:
- `value(task)` — load a task result
- `invalidate(task)` — remove a task's cached result
- `get_tasks()` — list all tasks
- `get_filtered_tasks(loadable=True|failed=True|available=True)` — filter tasks

## 5. Fixing Problems

When something goes wrong, first check `jug status` and then use the relevant
recovery command:

- Retry a normal task failure: re-run `jug execute`
- Clear failed locks from `--keep-failed` or `file_keepalive:`: `jug cleanup --failed-only`
- Clear stale crash locks: `jug cleanup --locks-only`
- Remove stale cached results after code changes: `jug invalidate --target ...`
- Remove orphaned results from an old graph shape: `jug cleanup`

For exact workflows and failure semantics, see
[Troubleshooting](references/troubleshooting.md).

## 6. Choosing a Backend

Set the jugdir on the command line with `--jugdir`, or in the config file.

| Backend | When to use | How to select |
|---------|-------------|---------------|
| **file store** (default) | Local disk or NFS. NFS-safe — uses atomic rename. | `--jugdir path/to/dir` |
| **Redis store** | No shared filesystem; fast. | `--jugdir redis://host:port/dbname` |
| **dict store** | Unit testing or small local runs. In-memory, optionally persisted to one file. | `--jugdir dict_store` or `--jugdir dict_store:path/to/file` |
| **file keepalive store** | Shared filesystem with dead-worker detection. | `--jugdir file_keepalive:path/to/dir` |

Default jugdir name: `<jugfile_basename>.jugdata`

## 7. Config Files

Jug reads configuration from (in order of increasing priority):

1. `~/.config/jug/jugrc` (global)
2. `.jugrc` or `jugrc` in the project directory (local, searched up to git root)

Config format (INI):

```ini
[main]
jugdir = /fast/scratch/myjob.jugdata

[execute]
wait-cycle-time = 30
nr-wait-cycles = 60
keep-going = true
```

Option names match CLI flags with `-` replaced by `_` (or kept as-is in the
config). Section `[main]` holds global options; `[execute]`, `[status]`, etc.
hold subcommand options.

## 8. Key Pitfalls

**Random numbers** — If your task uses `random`, it will produce the same
sequence every run (same input → same hash → same cache key). Seed explicitly
with a task argument, e.g. `compute(data, seed=42)`.

**Code changes invalidate nothing automatically** — Jug hashes on function
name + arguments, not on function bytecode. If you change the implementation
of a task, you must manually `jug invalidate` its results.

**Task granularity** — Aim for tasks taking several seconds to minutes. Very
short tasks (< 1 s) cause excessive overhead from locking and storage I/O.

**File side-effects** — Avoid having tasks write to output files whose names
don't depend on their arguments. Two workers might overwrite each other. If
you need file-based outputs, use `jug_execute` and, when needed, a local
`value_after()` helper as shown in [Common Patterns](references/common-patterns.md).

**Mutable arguments** — Never mutate a task's arguments; jug caches hashes
and mutation will silently corrupt them. Use `--debug` to detect this.

**Lambda functions** — `Task(lambda x: x, ...)` raises `ValueError`. Use
named functions decorated with `@TaskGenerator`.

## Further Reading

- [CLI Reference](references/cli-reference.md) — every subcommand and option
- [Common Patterns](references/common-patterns.md) — MapReduce, identity,
  timed_path, CompoundTaskGenerator, NoHash, and more
- [Troubleshooting](references/troubleshooting.md) — failures, stale locks,
  invalidation, and common debugging workflows
- [Simple example](examples/simple_jugfile.py) — minimal annotated jugfile
- [Pipeline example](examples/pipeline_jugfile.py) — two-stage pipeline with `bvalue`
- [Official docs](https://jug.readthedocs.io)
