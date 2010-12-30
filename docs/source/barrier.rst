========
Barriers
========

Often part of your control structure depends on previous computations. For
example, you might load all the data, and filter some of them out based on a
long computation::

    from jug import Task
    inputs = load_data()
    keeps = [Task(keep, i) for i in inputs]

    # Now I want to throw out data
    # This will NOT work:
    inputs = [i for i,k in zip(inputs,keeps) if k]
    results = [Task(long_computation, i) for i in inputs]

This will not work: the ``keeps`` list is a list of ``Tasks`` not its results.
You can work around this in a couple of ways, but none of which is completely
satisfactory.

The solution is a ``barrier()``::

    from jug import Task, barrier, value
    inputs = load_data()
    keeps = [Task(keep, i) for i in inputs]
    
    barrier() # <-------- this will divide the jugfile in two!
    inputs = [i for i,k in zip(inputs, value(keeps)) if k]
    results = [Task(long_computation, i) for i in inputs]

This effectively divides the jugfile in two or more blocks: up to the barrier
call and after the barrier call. When a barrier call is reached, if there are
any tasks that have not run, then the jugfile is not loaded any further. This
ensures that **after the call** you can load the results of previous tasks.

Limitations
-----------

Currently, to run a file like the one above you need to call ``jug execute``
first to run all the tasks up to the barrier and then again to run it past the
barrier (or more times if you have several barrier calls).


