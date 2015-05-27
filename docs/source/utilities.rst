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

.. automodule:: jug.utils
    :members:
