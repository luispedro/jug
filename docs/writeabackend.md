# Writing a Backend

## What is a backend

A backend is simply a store for objects. It needs to support four operations:

1. Saving Python objects associated with a key (a key is a string)
2. Loading Python objects by their key
3. Create a lock (identified by a key)
4. Release a lock (identified by a key)

There are a few other operations, like deleting an entry, that are useful, but
not strictly necessary.

The built-in backends are identified by a URI type string, generically called
`jugdir`. For example, to connect to a redis backend, use
`redis://host:port/`. The mapping from these strings to backends is fixed
(see `jug.backends.select`), so a new backend cannot be selected with
`--jugdir` on the command line.

## How to use your own backend

Wherever jug accepts a jugdir, you can pass a store *object* instead of a
string and it will be used directly. To load results in a script (or a
notebook), pass it to `jug.init`:

```
import jug
from mystore import my_store

store, jugspace = jug.init('jugfile.py', store=my_store(...))
results = jug.value(jugspace['results'])
```

(Alternatively, `jug.set_jugdir(my_store(...))` sets the store without
loading a jugfile.)

To *run* the tasks (i.e., the equivalent of `jug execute`), use a small
script which sets the jugdir option to your store and calls the subcommand:

```
from jug import options
from jug.subcommands import cmdapi
from mystore import my_store

opts = options.parse(['execute', 'jugfile.py'])
opts.jugdir = my_store(...)
cmdapi.run('execute', options=opts)
```

Run this script (instead of `jug execute`) as many times in parallel as you
wish.

## How to write a backend

You can start with the file `jug/backends/base.py` which provides a
template with documentation. Implement the functions in there.

`jug status` wraps the store in `jug.backends.memoize_store`, which caches
the answers of `can_load` and of the lock status checks. If the backend
implements `list()` and `listlocks()`, `memoize_store` calls them once at
the start, instead of checking every task (and every lock) separately, which
makes `jug status` much faster for backends where each check is slow.

```{eval-rst}
.. automodule:: jug.backends.base
    :members: base_store, base_lock
```
