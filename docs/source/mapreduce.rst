===================
Map/Reduce With Jug
===================

Currently, the dominant paradigm for large scale distributed computing is the
map/reduce paradigm. Originally made prominent by Google's proprietary
implementation, it is now available in many implementations, including
open-source ones such as Hadoop.

Jug is not a direct competitor to Hadoop as it focuses on medium sized
problems. Jug does not implement a distributed file system of any sort, but
assumes that all compute nodes have access to a central repository of
information (such as a shared filesystem or a redis server).

On the other hand, jug supports much more complex computations than map-reduce.
If, however, your problem is naturally described as a map/reduce computation,
then *jug* has some helper functions.

``jug.mapreduce.mapreduce``
---------------------------

The ``jug.mapreduce.mapreduce`` function implements mapreduce::

    jug.mapreduce(reducer, mapper, inputs)

is roughly equivalent to::

    Task{ reduce(reducer, map(mapper, inputs)) }

If the syntax of Python supported such a thing.

An issue that might come up is that your *map* function can be **too fast**. A
good task should take at least a few seconds (otherwise, the overhead of
scheduling and loading the data overwhelms the performance advantages of
parallelism. Analogously for the *reduce* function.

Therefore, ``jug`` groups your inputs so that a mapping task actually consists
of mapping and reducing more than one input. How many is controlled by the
``map_step`` parameter. By default, it is set to 4. Similarly, the
``reduce_step`` parameter controls how many reduction steps to perform in a
single task (by default, 8; reflecting the fact that reduce operations tend to
be lighter than map operations).


