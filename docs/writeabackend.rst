=================
Writing a Backend
=================

What is a backend
-----------------

A backend is simply a store for objects. It needs to support four operations:

1. Saving Python objects associated with a key (a key is a string)
2. Loading Python objects by their key
3. Create a lock (identified by a key)
4. Release a lock (identified by a key)

There are a few other operations, like deleting an entry, that are useful, but
not strictly necessary.

Backends are identified by a URI type string, generically called ``jugdir``.
For example, to connect to a redis backend, use ``redis:host:port/database``.
Your backend should support a similar scheme.

How to write a backend
----------------------

You can start with the file ``jug/backends/base.py`` which provides a
template with documentation. Implement the functions in there.

.. automodule:: jug.backends.base
    :members: base_store, base_lock
