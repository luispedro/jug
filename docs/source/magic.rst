=================
Magic Jug Methods
=================

This is an advanced use of jug and you can shoot yourself in the foot doing
this. If you cannot figure out why this functionality could be useful, then you
probably should not be using it.

Custom hash functions
---------------------

Sometimes, you may want to give your objects a special hash function, either to
add functionality or for efficiency. There are two ways to do it: (1) use a
``CustomHash`` object for simple cases or (2) add a ``__jug_hash__`` method for
more complex ones.

Using the CustomHash wrapper
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For example, here is how ``timed_path`` is implemented (minus the comments in
the real code)::

        def hash_with_mtime_size(path):
            from .hash import hash_one
            st = os.stat_result(os.stat(path))
            mtime = st.st_mtime
            size = st.st_size
            return hash_one((path, mtime, size))

        def timed_path(path):
            return CustomHash(path, hash_with_mtime_size)

The return value from ``timed_path`` is an object which behaves exactly like
``path`` (i.e., as a file path), but when jug needs to hash it, it calls the
function ``hash_with_mtime_size``.

Implementing a __jug_hash__ method
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When jug wants to hash an object, first it checks whether the object has a
``__jug_hash__`` method. If so, that method should return ``bytes`` (or a
bytes-like object that can be used by a `hashlib
<https://docs.python.org/3.6/library/hashlib.html>`__ object. If there is no
``__jug_hash__`` method, jug checks whether the object is one of its known
types (dict, list, tuple, numpy array, ...). If so, it will use optimized code.
Otherwise; it resorts to calling pickle on the object and then hashing the
pickled representation.

This fallback can be very inefficient. For example, let's say you have an
object which is basically just a numpy array loaded from disk, which remembers
its initial location. The standard pickling method would be very inefficient
compared to the optimized numpy code.

The way to solve this is to define a ``__jug_hash__`` method. Inside it, we can
rely on the jug hashing machinery to access the optimized version!

Here is how we'd do it::

    import numpy as np
    class NamedNumpy:
        def __init__(self, ifile):
            self.data = np.load(ifile)
            self.name = ifile

        def transform(self, x):
            self.data *= x

        def __jug_hash__(self):
            from jug.hash import hash_one

            return hash_one({
                'type': 'NumpyPair',
                'data': self.data,
                'name': self.name,
                })


The function ``hash_one`` takes one object and hashes it using the jug
machinery. Because we are passing it a dictionary, it recursively build a hash
for it. Thus, our ``NamedNumpy`` object now has a very fast hash function.

In fact, the ``CustomHash`` object we saw above, just defined its
``__jug_hash__`` function to call whatever you pass it in.

Overriding the ``value`` function
---------------------------------

Similarly to overriding the hashing, we can override the ``value`` call which
jug used internally to load objects.

Again, ``value(x)`` works in the following way:

1. Does the ``x.__jug_value__`` member exist? If so, call it.
2. Is ``x`` one of the composite types it knows about (dict, list,...). If so, use
   special code to recursively get all the sub objects. For a list
   ``value([x,y]) == [value(x), value(y)]``.
3. Is it a ``Task`` or a ``Tasklet``? If so, load it from the store.
4. Otherwise, ``value(x) == x``.

What if you have your own sequence object? Then you can set a ``__jug_value__``
method, which will be called whenever ``value(self)`` is needed. This is a
pretty advanced use case: if you cannot figure out why this may be useful, then
you probably don't need to use it.

