# Backends

## What is a Jug Backend?

A jug backend serves two tasks: it saves intermediate results and it
synchronises the running processes when needed.

## What Backends Are Available?

There are four backends available: the default one is based on the
filesystem, a variation of it (`file_keepalive`) can detect processes that
died, the third is a [redis](https://redis.io/) backend, and the last is a
simple in-memory backend which does not allow sharing across processes.

### Filesystem

By default, jug will save its results in a directory named after the jugfile
(e.g., `jugfile.jugdata` for `jugfile.py`). This
is done in a way that works across **NFS** if you are using a cluster.

Results are compressed pickles, except that numpy arrays are saved in numpy's
`.npy` format and [polars](https://pola.rs/) DataFrames as parquet files.

### Filesystem with keepalive

If a jug process is killed (e.g., by the cluster's job scheduler) while it is
running a task, the lock for that task is left behind and no other process
will run it (until you run `jug cleanup --locks-only`). The `file_keepalive`
backend avoids this problem. Use it with `--jugdir=file_keepalive:path`
(e.g., `--jugdir=file_keepalive:jugfile.jugdata`). It stores results exactly
as the default filesystem backend (so you can switch between them), but, while
a task runs, a helper process refreshes the timestamp of its lock every 5
minutes. A lock that has not been refreshed for 30 minutes is considered
*failed*: `jug status` lists the task as Failed, and `jug cleanup
--failed-only` removes those locks so that the tasks can be run again.

### Redis

Redis is a non-relational database system. I assume you have already installed
it (it is easy to install from source, but it is now a part of Ubuntu, so that
is even easier).

This backend also requires the [redis](https://pypi.org/project/redis/)
Python package, which is not installed together with jug (install it with
`pip install redis`).

1. Run a redis server (see its docs for how to control it, but simply calling
   `redis-server` should work).
2. Now start your jug jobs with the `--jugdir=redis://127.0.0.1/`.

The jugdir must have the form `redis://host/` or `redis://host:port/` (the
default port is 6379). A database number cannot be given: anything after the
port is ignored and the default database is used. If the jugdir starts with
`redis:` but is not in this form (e.g., just `--jugdir=redis:`), jug
connects to the default port on `localhost`.

## In Memory Store

If you just want an in-memory store, use `--jugdir=dict_store:filename` and
the results will be loaded and saved into `filename` (use just
`--jugdir=dict_store` to get a run where results are *not* saved to file).

This is only appropriate for small projects, but has the lowest maintenance of
any system.

## Which Backend Should I Use?

If all your nodes share a filesystem and you don't want to set anything up,
just use the default filesystem backend. If your computations are non-trivial
(in general, you should avoid breaking up your algorithm so much that each
task takes less than a second), then this will be fast enough and very robust.

Do note that `jug` **works well over NFS**.

If your nodes do not share a filesystem then you are going to have to use
redis. For some cases (if you have many outputs of computations that do not
take very long), it is also faster and, if your results are small, takes up
significantly less space.

The tradeoffs are speed and space vs. convenience.
