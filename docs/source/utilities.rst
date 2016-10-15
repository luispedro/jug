=========
Utilities
=========

The module ``jug.utils`` has a few functions which are meant to be used in
writing jugfiles.

Identity
--------

This is simply implemented as::

    @TaskGenerator
    def identity(x):
        return x

This might seem like the most pointless function, but it can be helpful in
speeding things up. Consider the following case::

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

How is this processed? Every time ``process`` is called, a new ``jug.Task`` is
generated. This task has two arguments: ``inputs`` and an integer. When the hash
of the task is computed, both its arguments are analysed. ``inputs`` is a large
list of strings. Therefore, it is going to take a very long time to process all
of the hashes.

Consider the variation::

    from jug.utils import identity

    # ...
    # same as above

    inputs = identity(inputs)
    results = {}
    for p in range(1000):
        results[p] = process(inputs, p)

Now, the long list is only hashed once! It is transformed into a ``Task`` (we
reuse the name ``inputs`` to keep things clear) and each ``process`` call can
now compute its hash very fast.

jug_execute
-----------

This is a simple wrapper around ``subprocess.call()``. It adds two important
pieces of functionality:

1. it checks the exit code and raises an exception if not zero (this can be
   disabled by passing ``check_exit=False``).
2. It takes an argument called ``run_after`` which is ignored but can be used
   to declare dependencies between tasks.

.. automodule:: jug.utils
    :members:
