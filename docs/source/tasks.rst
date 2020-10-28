======================
Structuring Your Tasks
======================
Tips & Tricks
-------------

These are some general guidelines for programming with jug.

What can be a task?
-------------------

Almost any named function can be a task.

What should be a task?
----------------------

The trade-off is between tasks that are too small (you have too many of them
and the overhead of ``jug`` will overwhelm your process) or too big (and then
you have too few tasks per processor.

As a rule of thumb, each task should take at least a few seconds, but you
should have enough tasks that your processors are not idle.

Task size control
-----------------

Certain mechanisms in jug, for example, ``jug.mapreduce.map`` and
``jug.mapreduce.mapreduce`` allow the user to tweak the task breakup with a
couple of parameters

In ``map`` for example, ``jug`` does, by default, issue a task for each element
in the sequence. It rather issues one for each 4 elements. This expects tasks
to not take that long so that grouping them gives you a better trade-off
between the throughput and latency. You might quibble with the default, but the
principle is sound and it is only a default: the setting is there to give you
more control.

Identifying tasks
-----------------

In the module ``jug.hash``, jug attempts to construct a unique identifier, called
a hash, for each of your tasks. For doing that, the name of the function involved
invoked in the task together with  the parameters that it receives are used. This
makes jug easy to use but has some drawbacks:

- If your functions take long/big arguments, the hash process will potentially be
  costly. That's a common situation when you are processing arrays for example, or
  if you are using sets/dictionaries, in which case the default handling needs
  to get a sorted list from the elements of the set/dictionary.

- Jug might not know how to handle the types of your arguments,

- Arguments might be equivalent, and thus the tasks should be identified in the
  same way, without jug knowing. As a very contrived example, suppose that a task uses
  an argument which is an angle and for the purpose of your program all the values
  are equivalent modulo 2*pi.

If you control the types of your arguments, you can add a ``__jug_hash__``
method to your type directly. This method should return a string::

    class MySpecialThing:
        def __jug_hash__(self):
            return some_string

Alternatively, you can use ``jug.utils.CustomHash`` in the case where you
cannot (or rather, would not) change the types::

    from jug.utils import CustomHash
    def my_hash_function(x):
        return some_string_based_on_x
    
    complex = ...
    value = CustomHash(complex, my_hash_function) 

Now, ``value`` behaves exactly like ``complex``, but its hash is computed by
calling ``my_hash_function``.

