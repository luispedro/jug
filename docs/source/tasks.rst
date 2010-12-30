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

