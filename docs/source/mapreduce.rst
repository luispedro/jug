==========
Map/Reduce
==========

Mapping, reducing and all that Jazz
-----------------------------------

Jug is **not** a map/reduce framework. However, it is still useful to sometimes
frame problems in that framework. And applying the same function to a large
collection of elements (in a word, *mapping*) is exactly the absurdly parallel
problem that Jug excels at.

Naïve Solution
~~~~~~~~~~~~~~

Let's say you want to double all numbers between 0 and 1023. You could do
this::

    from jug import TaskGenerator

    @TaskGenerator
    def double(x):
        return 2*x

    numbers = range(1024)
    result = map(double, numbers)

This might work well for this problem. However, if instead of 1,024 numbers,
you had 1 million and each computation was very fast, then this would actually
be very inefficient: you are generating one task per computation. As a rule of
thumb, you want your computations to last at least a few seconds, otherwise,
the overhead of maintaining the infrastructure becomes too large.

Grouping computations
~~~~~~~~~~~~~~~~~~~~~

You can use ``jug.mapreduce.map`` to achieve a better result::


    from jug import mapreduce

    result = mapreduce.map(double, numbers, map_step=32)

The ``map_step`` argument defines how many calls to ``double`` will be
performed in a single Task.

You can also include a reduce step::

    @TaskGenerator
    def add(a, b):
        return a + b

    final = mapreduce.map(add, double, numbers, map_step=32)


this is sort of equivalent to::

    final = reduce(add, map(double, numbers))

except that **the order in which the reduction is done is not from left to
right**! In fact, this only works well if the reduction function is
associative.

Curried mapping
~~~~~~~~~~~~~~~

The above is fine, but sometimes you need to pass multiple arguments to the
function you want to loop over::

    @TaskGenerator
    def distance_to(x, ref):
        return abs(x - ref)

    ref = 34.34
    inputs = range(1024)

    result = [distance_to(x, ref) for x in inputs]

This works, but we are back to where we were: too many small Tasks!

``currymap`` to the rescue::

    result = mapreduce.currymap(distance_to, [(x,ref) for x in inputs])

Arguably this function should have been called ``uncurrymap`` (as it is
equivalent to the Haskell expression ``map . uncurry``), but that just doesn't
sound right (I also like to think it's the programming equivalent to the
Currywurst, a culinary concept which almost makes me chuckle).


