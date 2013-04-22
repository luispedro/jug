==============
Compound Tasks
==============

*This is a fairly advanced topic, which you should only tackle once you have
mastered the basics of Jug.*

A compound task is a function that builds up a potentially-complex task.
Because this function might generate many intermediate tasks which are not very
meaningful, using a compound task construct allows us to throw them away once
they have run.

For example::

    @TaskGenerator
    def poly(a,b,c):
        return a*b+c

    @TaskGenerator
    def max3(values):
        'Return the maximum 3 values'
        values.sort()
        return tuple(values[-3:])

    def buildup(numbers):
        results = []
        for n in numbers:
            results.append(poly(n, 2*n, poly(n,n,n)))
        return max3(results)

    # Work in Python2 & Python3
    numbers = list(range(192))
    intermediate = buildup(numbers)
    ...

We have a fairly complex function ``buildup``, which takes the list of ``N``
numbers and generated ``2*N+1`` Tasks. These are a lot of Tasks and may make
jug run slower. On the other hand, you may not want to simply have a single
Task do everything::


    def poly(a,b,c):
        return a*b+c

    def max3(values):
        'Return the maximum 3 values'
        values.sort()
        return tuple(values[-3:])

    @TaskGenerator
    def buildup(numbers):
        results = []
        for n in numbers:
            results.append(poly(n, 2*n, poly(n,n,n)))
        return max3(results)

Because, this way, you will have lost any ability to have the different calls
to ``poly`` be run in parallel.

A compound task behaves like the first example until all necessary tasks have
been computed::

    @TaskGenerator
    def poly(a,b,c):
        return a*b+c

    @TaskGenerator
    def max3(values):
        'Return the maximum 3 values'
        values.sort()
        return tuple(values[-3:])

    @CompoundTaskGenerator
    def buildup(numbers):
        results = []
        for n in numbers:
            results.append(poly(n, 2*n, poly(n,n,n)))
        return max3(results)

    # Work in Python2 & Python3
    numbers = list(range(192))
    intermediate = buildup(numbers)
    ...

Basically, when Jug sees the ``CompoundTask``, it asks *is the result of all of
this already available?* If yes, then it is just the current result; otherwise,
the function is called immediately (**not** at execution time, but every time
the jugfile is loaded).

See Also
--------

See also the section on `mapreduce <mapreduce.html>`__.
