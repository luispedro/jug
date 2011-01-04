==============
Compound Tasks
==============

Compound tasks are useful in other contexts, but they appear naturally in
map/reduce settings, so we will use that as an example.

The canonical example for map/reduce is counting words in files. Here, we will
do the same with some very small files:

::

    inputs = [
            "banana apple apple banana",
            "apple pear football",
            "pear",
            "banana apple apple",
            "football banana",
            "apple pear",
            "waldorf salad",
            ]

The ``mapper`` function will output a dictionary of counts::

    def count1(str):
        from collections import defaultdict
        counts = defaultdict(int)
        for word in str.split():
            counts[word] += 1
        return counts

(We used the very useful ``collections.defaultdict``).

While the ``reducer`` adds two dictionaries together::

    def merge_dicts(rhs, lhs):
        # Note that we SHOULDN'T modify arguments, so we will create a copy
        rhs = rhs.copy()
        for k,v in lhs.iteritems():
            rhs[k] += v
        return rhs

We can now use ``jug.mapreduce.mapreduce`` to put these together::

    final_counts = jug.mapreduce.mapreduce(
                            merge_dicts,
                            count1,
                            inputs,
                            map_step=1)

Running ``jug status`` shows up the structure of our problem::

    Task name                                    Waiting       Ready    Finished     Running
    ----------------------------------------------------------------------------------------
    jug.mapreduce._jug_map_reduce                      0           6           0           0
    jug.mapreduce._jug_reduce                          1           0           0           0
    ........................................................................................
    Total:                                             1           6           0           0


If we had more than just 6 "files", the values in the table would be much
larger. Let's also assume that this is part of some much larger programme that
computes counts and then does some further processing with them.

Once that task is done, we might not care anymore about the break up into 6
units. So, we can wrap the whole thing into a **compound task**::

    final_counts = CompoundTask(jug.mapreduce.mapreduce,
                            merge_dicts,
                            count1,
                            inputs,
                            map_step=1)

At first, this does not do much. The status is the same::

    Task name                                    Waiting       Ready    Finished     Running
    ----------------------------------------------------------------------------------------
    jug.compound.compound_task_execute                 1           0           0           0
    jug.mapreduce._jug_map_reduce                      0           6           0           0
    jug.mapreduce._jug_reduce                          1           0           0           0
    ........................................................................................
    Total:                                             2           6           0           0

But if we *execute* the tasks and re-check the status::

    Task name                                    Waiting       Ready    Finished     Running
    ----------------------------------------------------------------------------------------
    jug.mapreduce.mapreduce                            0           0           1           0
    ........................................................................................
    Total:                                             0           0           1           0

Now, ``jug status`` reports a single task (the mapreduce task) and it is *Finished*.

Compound tasks not only lower the cognitive load, but they also make operations
such as ``jug status`` much faster.


Full example source code
------------------------

We left out the imports above, but other than that, it is a fully functional example::

    import jug.mapreduce
    from jug.compound import CompoundTask

    inputs = [
            "banana apple apple banana",
            "apple pear football",
            "pear",
            "banana apple apple",
            "football banana",
            "apple pear",
            "waldorf salad",
            ]


    def count1(str):
        from collections import defaultdict
        counts = defaultdict(int)
        for word in str.split():
            counts[word] += 1
        return counts


    def merge_dicts(rhs, lhs):
        # Note that we SHOULDN'T modify arguments, so we will create a copy
        rhs = rhs.copy()
        for k,v in lhs.iteritems():
            rhs[k] += v
        return rhs

    #final_counts = jug.mapreduce.mapreduce(
    #                        merge_dicts,
    #                        count1,
    #                        inputs,
    #                        map_step=1)

    final_counts = CompoundTask(jug.mapreduce.mapreduce,
                            merge_dicts,
                            count1,
                            inputs,
                            map_step=1)

