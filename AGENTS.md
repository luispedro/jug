# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Commands

**Run all tests:**
```bash
pytest jug/tests/
```

**Run a single test file:**
```bash
pytest jug/tests/test_tasks.py
```

**Run a single test:**
```bash
pytest jug/tests/test_tasks.py::test_function_name
```

**Install in development mode (with dev dependencies):**
```bash
pip install -e ".[dev]"
```

**Build the package:**
```bash
python -m build
```

## Architecture

Jug is a task-based parallelization framework where a **jugfile** (a Python script) defines tasks, and multiple `jug execute` processes run those tasks concurrently using a shared backend store for coordination and result caching.

### Core concepts

**Task** (`jug/task.py`): The central abstraction. A `Task` wraps a function call with its arguments. Tasks are identified by a content hash of their function + arguments. `task.alltasks` is a module-level list that accumulates all tasks as the jugfile is imported. Tasks are typically created via the `@TaskGenerator` decorator.

**Backends** (`jug/backends/`): Storage and locking layer. `base_store` (abstract) defines the interface: `dump`, `load`, `can_load`, `list`, `lock`, etc. Implementations:
- `file_store` — filesystem-based (default, NFS-safe). Results stored as files named by task hash.
- `dict_store` — in-memory (useful for testing).
- `redis_store` — Redis-based.

Backends also implement **locking** to prevent duplicate execution across workers. `file_store` uses lock files; `redis_store` uses Redis locks.

**Hashing** (`jug/hash.py`): Task identity is determined by hashing the function (by name/module) and all arguments recursively. Objects can implement `__jug_hash__()` for custom hashing. numpy arrays and polars DataFrames have special handling in `file_store` (stored in native format for efficiency).

**Subcommands** (`jug/subcommands/`): Each `jug <cmd>` maps to a subcommand module: `execute`, `status`, `invalidate`, `cleanup`, `count`, `check`, `graph`, `shell`, `webstatus`, `pack`, `demo`. The `execute` subcommand runs the core execution loop.

**Barrier** (`jug/barrier.py`): `barrier()` raises `BarrierError` if any previously defined task isn't complete yet. This stops jugfile parsing at that point, allowing dynamic task graphs where the number of tasks depends on prior results. `bvalue(t)` is a scoped version that only checks one task.

**CompoundTask** (`jug/compound.py`): A task whose function itself returns a Task. Used to create dynamic sub-graphs that are only instantiated after the compound task runs.

**Hooks** (`jug/hooks/`): Event system for extending jug behavior (e.g., logging task execution events). Register with `register_hook(event_name, callback)`.

**Options** (`jug/options.py`): A chained options object where attributes fall through to the next layer. Configuration can come from CLI args, local config files, or defaults.

### Execution flow

1. `jug execute jugfile.py --jugdir jugdata/` is called
2. `jug.init()` sets up the backend store and imports the jugfile, populating `task.alltasks`
3. If a `barrier()` is hit before all prior tasks are done, a `BarrierError` is raised and jugfile import stops at that point (the execution loop re-imports once more tasks complete)
4. The execution loop picks tasks that are ready (all dependencies loadable), acquires a lock, executes, stores result, releases lock
5. Multiple workers run in parallel — coordination is entirely through the backend store

### Test infrastructure

Tests live in `jug/tests/`. The `tmp_file_store` pytest fixture (in `jug/tests/utils.py`) provides a temporary `file_store` and handles cleanup of `task.Task.store`. Test jugfiles (used as fixtures for integration tests) are in `jug/tests/jugfiles/`.
