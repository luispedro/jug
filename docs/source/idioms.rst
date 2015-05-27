======
Idioms
======


There are certain types of computation that show up again and again in parallel
computation. This section shows how to perform them with jug.

Map/Reduce
----------

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

The `compound task <compound.html>`__ section has a worked out example of using
map/reduce.

Parameter Sweep
---------------

This is a standard problem in many fields, for example, in machine learning.
You have an algorithm that takes a few parameters (let's call them ``p0`` and
``p1``) and a function which takes your input data (``data``) and the
parameters and outputs the score of this parameter combination.

In pure Python, we'd write something like::

    best = None
    best_val = float("-Inf")
    for p0 in range(100):
        for p1 in range(-20, 20):
            cur = score(data, p0, p1)
            if cur > best_val:
                best = p0,p1
                best_val = cur
    print('Best parameter pair', best)

This is, obviously, an **embarassingly parallel** problem and we want *jug* to
handle it.

First note: we can, of course, perform this with a *map/reduce*::

    def mapper(data, p0, p1):
        return (p0, p1, score(data, p0, p1))

    def reducer(a, b):
        _, _, av = a
        _, _, bv = b
        if av > bv: return a
        return b
    
    best = jug.mapreduce.mapreduce(
                    reducer,
                    mapper,
                    [(p0, p1)
                            for p0 in range(101)
                            for p1 in range(-20, 21)])

However, if you want to look at the whole parameter space instead of just the
best score, this will not work. Instead, you can do::

    from jug import TaskGenerator

    score = TaskGenerator(score)
    results = {}
    for p0 in range(100):
        for p1 in range(-20, 20):
            result[p0,p1] = value(data, p0, p1)

Now, *after you've run ``jug execute``*, you can use ``jug shell`` and load the
result dictionary to look at all the results.


::
    
    result = value(result)
    print(result[0, -2])
    # Look for the maximum score
    print(max(result.values()))
    # Look at maximum score *and* the parameters that generated it:
    print(max((v, k) for k, v in result.iteritems()))

