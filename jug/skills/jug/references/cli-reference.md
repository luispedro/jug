# Jug CLI Reference

Full reference for every `jug` subcommand and option.

## Global Options

These apply to all subcommands:

| Option | Default | Description |
|--------|---------|-------------|
| `jugfile` (positional) | `jugfile.py` | Python script defining the task graph |
| `--jugdir DIR` | `<jugfile>.jugdata` | Directory (or URI) for storing results |
| `--short` | false | Short one-line output for status-style commands |
| `--verbose info` | quiet | Set logging level (`info` shows task details) |
| `--debug` | false | Extra hash checking; detects mutable-argument bugs |
| `--pdb` | false | Drop into PDB debugger on error (implies `--debug`) |
| `--aggressive-unload` | false | Unload results from RAM aggressively (use if you hit memory limits) |
| `--will-cite` | false | Suppress citation reminder |
| `--version` | — | Print version and exit |

The jugdir string supports Python format variables:
- `%(jugfile)s` — jugfile basename without extension
- `%(date)s` — today's date (`YYYY-MM-DD`)

Example: `--jugdir /scratch/%(jugfile)s-%(date)s.jugdata`

---

## `jug execute`

Run tasks. Typically run on every worker process/machine.

```
jug execute [jugfile] [options]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--target PATTERN` | (all tasks) | Only execute tasks whose name matches PATTERN (same syntax as `invalidate --target`) |
| `--keep-going` | false | Continue executing other tasks after a task fails, instead of stopping |
| `--keep-failed` | false | Leave failed tasks locked (do not release lock on failure) |
| `--wait-cycle-time N` | 12 | Seconds to sleep between cycles when no task is ready |
| `--nr-wait-cycles N` | 150 | Maximum number of wait cycles before exiting (default = 30 min total) |
| `--no-check-environment` | false | Skip checking `JUG_*` env vars and `__jug_please_stop_running.txt` |

**Stop signals:** Create a file named `__jug_please_stop_running.txt` in the
working directory to ask all workers to exit cleanly after finishing their
current task. Remove the file to let them resume.

Workers re-import the jugfile each cycle, so jugfiles with `barrier()` are
handled transparently across multiple cycles.

Exit code: 0 if all tasks completed successfully; 1 if any task failed.

---

## `jug status`

Show how many tasks are in each state.

```
jug status [jugfile] [options]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--short` | false | Print one-line summary instead of per-task-type table |
| `--cache` | false | Use an SQLite cache for faster repeated calls |
| `--cache-file FILE` | `.jugstatus.sqlite3` | Path to the SQLite cache file |
| `--clear` | false | Delete the cache file (use with `--cache`) |

**Status values shown:**
- **Failed** — task has a failed lock state (for example after `--keep-failed`
  or a dead keepalive lock)
- **Waiting** — dependencies not yet complete
- **Ready** — all dependencies done, no worker has claimed it
- **Active** — currently being executed by a worker
- **Complete** — result is stored in jugdir

**Tip:** `jug status --short` is safe to run frequently from scripts or
monitoring dashboards. Use `--cache` to speed up status checks on jugfiles
with thousands of tasks.

---

## `jug invalidate`

Remove cached results of tasks matching a pattern, plus all downstream tasks.

```
jug invalidate jugfile --target PATTERN
```

| Option | Required | Description |
|--------|----------|-------------|
| `--target PATTERN` | yes | Pattern to match task names (also accepts `--invalid`) |

**Pattern formats:**
- `/regex/` — regex applied to the full task name (e.g., `/compute_.*/`)
- `module.function` — fully qualified name with a dot (e.g., `jugfile.process`)
- `function` — bare name without a dot, matches `.function` in any module

After invalidating, re-run `jug execute` to recompute.

---

## `jug cleanup`

Remove stale objects from jugdir.

```
jug cleanup [jugfile] [options]
```

Without options, removes all results in jugdir that are not referenced by the
current jugfile (orphaned results from old task graph shapes).

| Option | Description |
|--------|-------------|
| `--locks-only` | Remove all lock files, leaving computed results intact. Use after killing workers. |
| `--failed-only` | Remove only failure locks (not normal active locks and not results). |
| `--keep-locks` | Remove orphaned results but preserve all lock files. |

`--locks-only`, `--failed-only`, and `--keep-locks` are mutually exclusive.

**Common workflows:**

```bash
# Workers crashed — remove stale locks so tasks can be retried:
jug cleanup jugfile.py --locks-only

# Only clear failed tasks so they can be retried
# (relevant for --keep-failed or keepalive failed locks):
jug cleanup jugfile.py --failed-only

# Jugfile changed shape — clean up orphaned results:
jug cleanup jugfile.py
```

---

## `jug check`

Exit with status 0 if all tasks are complete, 1 otherwise. Produces no output.

```
jug check [jugfile]
```

Useful in shell scripts:

```bash
jug check jugfile.py && echo "Done, running post-processing" && ./post.sh
```

---

## `jug sleep-until`

Like `jug check`, but keeps sleeping until all tasks are complete.

```
jug sleep-until [jugfile]
```

Polls every 12 seconds. Exits 0 when all tasks are finished.

---

## `jug shell`

Open an interactive Python shell with the jugfile loaded.

Requires IPython to be installed.

```
jug shell [jugfile]
```

The shell provides these helper functions:

| Function | Description |
|----------|-------------|
| `value(task)` | Load and return the result of a task |
| `invalidate(task)` | Remove a task's result from jugdir |
| `get_tasks()` | Return all tasks seen in the jugfile |
| `get_filtered_tasks(loadable=True, failed=True, available=True)` | Filter tasks by state |

Example session:

```python
# In jug shell:
ready = get_filtered_tasks(available=True)
print(len(ready))               # how many runnable tasks?
r = value(ready[0])             # load first result
invalidate(ready[0])            # force re-run of ready[0]
```

---

## `jug graph`

Generate a task dependency graph as a DOT file (requires Graphviz).

```
jug graph [jugfile] [options]
```

| Option | Description |
|--------|-------------|
| `--file-format` | Currently just enables PNG rendering; the parser does not accept a format argument |
| `--no-status` | Don't annotate nodes with task counts |

The DOT file is written to `<jugfile>.dot`. Jug also attempts to render
`<jugfile>.png` via `dot` because the current implementation defaults the
rendered format to PNG.

Node labels show counts per status: **F**ailed, **W**aiting, **R**eady,
**A**ctive, **C**omplete.

---

## `jug webstatus`

Serve a simple web dashboard showing task status.

```
jug webstatus [jugfile] [options]
```

Requires the `bottle` package (`pip install bottle`).

| Option | Default | Description |
|--------|---------|-------------|
| `--port PORT` | 8080 | TCP port to listen on |
| `--ip IP` | `localhost` | IP address to bind to |

---

## `jug pack`

Consolidate a file-store jugdir by rewriting fragmented result objects.

```
jug pack [jugfile]
```

Reduces inode count and can improve performance on filesystems with inode
limits. Safe to run while workers are idle.

---

## `jug count`

Print counts grouped by task name in the jugfile.

```
jug count [jugfile]
```

---

## Config File Reference

Config files use INI format. Sections correspond to subcommands.

**Search order (highest priority first):**
1. Command-line flags
2. Local `.jugrc` / `jugrc` (in project dir or any parent up to git root, closest wins)
3. `~/.config/jug/jugrc` (or `~/.config/jugrc`, `~/.jug/configrc`)

**Example `~/.config/jug/jugrc`:**

```ini
[main]
jugdir = /scratch/%(jugfile)s.jugdata
will-cite = true

[execute]
wait-cycle-time = 30
nr-wait-cycles = 60
keep-going = true

[status]
short = true
```

Option keys match CLI long-option names. Dashes and underscores are
interchangeable. Boolean values: `true`/`false`, `1`/`0`, `on`/`off`.

Subcommand options use the prefix `<subcommand>-<option>` in code but are
placed under the `[<subcommand>]` section in the config file.
