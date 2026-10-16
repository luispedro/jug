# AGENTS.md

This file provides guidance to agents (including Claude Code, via the `CLAUDE.md` symlink) when working with code in this repository.

## Commands

**Set up the environment (as CI does, using `uv.lock`):**
```bash
uv sync --locked --all-extras --dev
```
(or `pip install -e ".[dev]"`)

**Run all tests:**
```bash
pytest jug/tests/
```

**Run a single test file / test:**
```bash
pytest jug/tests/test_tasks.py
pytest jug/tests/test_tasks.py::test_function_name
```

**Redis tests** in `test_store.py` only run when `TEST_REDIS=1` is set and a Redis server is running locally.

**Self-test, as run by CI** (from an empty directory): `TEST_REDIS=1 jug test-jug`

**Build the package:**
```bash
python -m build
```

## Architecture

Jug is a task-based parallelization framework where a **jugfile** (a Python script) defines tasks, and multiple `jug execute` processes run those tasks concurrently using a shared backend store for coordination and result caching. Jug has **no required runtime dependencies**: numpy, polars, redis, argcomplete and shtab are all imported lazily and are optional.

### Core concepts

**Task** (`jug/task.py`): The central abstraction. A `Task` wraps a function call with its arguments. Tasks are identified by a content hash of their function + arguments. `task.alltasks` is a module-level list that accumulates all tasks as the jugfile is imported. Tasks are typically created via the `@TaskGenerator` decorator. `Tasklet`s are lightweight views on a task's result (e.g. `t[0]`, or a lambda applied to it); they are never stored.

**Backends** (`jug/backends/`): Storage and locking layer. `base_store` (abstract) defines the interface: `dump`, `load`, `can_load`, `list`, `lock`, etc. `backends/select.py` maps the `--jugdir` pseudo-URI to a store: `redis:...` → `redis_store`, `dict_store[:file]` → `dict_store`, `file_keepalive:...` → `file_keepalive_store`, anything else → `file_store`. Implementations:
- `file_store` — filesystem-based (default, NFS-safe). Results stored as files named by task hash.
- `dict_store` — in-memory (useful for testing).
- `redis_store` — Redis-based.
- `memoize_store` — caching wrapper around another store.

Backends also implement **locking** to prevent duplicate execution across workers. `file_store` uses lock files; `redis_store` uses Redis locks. Serialization lives in `backends/encode.py` (compressed pickle, with numpy special-casing); `file_store` additionally stores numpy arrays and polars DataFrames in their native formats.

**Hashing** (`jug/hash.py`): Task identity is determined by hashing the function (by name/module) and all arguments recursively. Objects can implement `__jug_hash__()` for custom hashing. **Any change that alters the hash of existing tasks forces every user to recompute their cached results**, so it must be deliberate and called out in the ChangeLog as a compatibility break (e.g. the pickle protocol used for hashing is pinned to 4 so that hashes are stable across Python versions).

**Subcommands** (`jug/subcommands/`): Each `jug <cmd>` maps to a `SubCommand` subclass. Modules in this package are auto-discovered via `pkgutil`, and a subcommand registers itself by being **instantiated at module level** (e.g. `execute = ExecuteCommand()`). CLI options are added in `parse(parser)` and their defaults in `parse_defaults()`. Users can add their own commands in `~/.config/jug/jug_user_commands.py`. The `execute` subcommand runs the core execution loop.

**Barrier** (`jug/barrier.py`): `barrier()` raises `BarrierError` if any previously defined task isn't complete yet. This stops jugfile parsing at that point, allowing dynamic task graphs where the number of tasks depends on prior results. `bvalue(t)` is a scoped version that only checks one task.

**CompoundTask** (`jug/compound.py`): A task whose function itself returns a Task. Used to create dynamic sub-graphs that are only instantiated after the compound task runs.

**mapreduce** (`jug/mapreduce.py`): `mapreduce`, `map`, `currymap` and `reduce` helpers that batch many small calls into fewer tasks.

**Hooks** (`jug/hooks/`): Event system for extending jug behavior (e.g., logging task execution events). Register with `register_hook(event_name, callback)`.

**Options** (`jug/options.py`): A chained options object where attributes fall through to the next layer. Configuration can come from CLI args, local config files, or defaults.

**Agent skill** (`jug/skills/jug/`): A bundled skill describing how to *use* jug, installed by `jug install-skills`. It ships as package data, so new files there must match the globs in `[tool.setuptools.package-data]` in `pyproject.toml`.

### Execution flow

1. `jug execute jugfile.py --jugdir jugdata/` is called
2. `jug.init()` sets up the backend store and imports the jugfile, populating `task.alltasks`
3. If a `barrier()` is hit before all prior tasks are done, a `BarrierError` is raised and jugfile import stops at that point (the execution loop re-imports once more tasks complete)
4. The execution loop picks tasks that are ready (all dependencies loadable), acquires a lock, executes, stores result, releases lock
5. Multiple workers run in parallel — coordination is entirely through the backend store

### Test infrastructure

Tests live in `jug/tests/`. Because `task.alltasks`, `Task.store` and hooks are global state, tests must reset them:
- the `@task_reset` decorator (`jug/tests/task_reset.py`) gives a test a fresh `dict_store` and clears `alltasks` and hooks afterwards;
- the `tmp_file_store` fixture (`jug/tests/utils.py`) provides a temporary `file_store` and handles cleanup of `Task.store`.

Test jugfiles (used as fixtures for integration tests) are in `jug/tests/jugfiles/`; locate them with `find_test_jugfile()` from `jug/tests/utils.py`.

## Conventions

- Commit messages start with a tag: `ENH` (feature), `BUG` (fix), `MIN` (minor), `TST`, `DOC`, `BLD`, `RLS`.
- User-visible changes get an entry under `Unreleased` at the top of `ChangeLog`.
- Python >= 3.9 is supported (CI tests 3.9–3.15), so don't use syntax or stdlib features newer than 3.9.
