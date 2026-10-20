# Writing a Backend

## What is a backend

A backend is simply a store for objects (identified by a key, which is a
string) together with a locking mechanism. A backend is a subclass of
`jug.backends.base.base_store` and must implement all of its abstract methods
(Python will refuse to instantiate it otherwise):

- `dump(object, name)`: save a Python object under a key
- `load(name)`: load a Python object by its key
- `can_load(name)`: whether an object with that key exists
- `list()`: iterate over all the keys in the store
- `remove(name)`: remove an entry
- `cleanup(active, keeplocks=False)`: remove all entries not in `active`
- `listlocks()`: iterate over the keys of all the locks
- `remove_locks()`: remove all the locks
- `getlock(name)`: return a lock object (see below)
- `close()`: release any resources held by the store

Locks returned by `getlock` are subclasses of `jug.backends.base.base_lock`
and must implement:

- `get()`: try to acquire the lock, returning whether it succeeded (this must
  be atomic across all processes using the store)
- `release()`: release the lock
- `is_locked()`: whether the lock is held (by any process)
- `fail()`: mark the lock as *failed* (the task raised an error)
- `is_failed()`: whether the lock is marked as failed

Other methods (`remove_many`, `metadata`, and the static method
`remove_store`) have default implementations which you can override if your
backend can do better.

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
