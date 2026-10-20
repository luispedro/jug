# Barriers

Often part of your control structure depends on previous computations. For
example, you might load all the data, and filter some of them out based on a
long computation:

```
from jug import Task
inputs = load_data()

def keep(datum):
    # A long running computation which decides whether datum should be kept
    ...

keeps = [Task(keep, i) for i in inputs]

# Now I want to throw out data
# This will NOT work:
inputs = [i for i,k in zip(inputs,keeps) if k]
results = [Task(long_computation, i) for i in inputs]
```

This will not work: the `keeps` list is a list of `Tasks` not its results.

The solution is to use a `barrier()`:

```
from jug import Task, barrier, value
inputs = load_data()

def keep(datum):
    # A long running computation which decides whether datum should be kept
    ...

keeps = [Task(keep, i) for i in inputs]

barrier() # <-------- this will divide the jugfile in two!
inputs = [i for i,k in zip(inputs, value(keeps)) if k]
results = [Task(long_computation, i) for i in inputs]
```

This effectively divides the jugfile in two or more blocks: up to the barrier
call and after the barrier call. When a barrier call is reached, if there are
any tasks that have not run, then the jugfile is not loaded any further. This
ensures that **after the call** you can load the results of previous tasks.

## What happens during `jug execute`

When `jug execute` reaches a barrier, it runs all the tasks defined up to that
point (as long as their dependencies are available) and then imports the
jugfile again. If all the tasks before the barrier have finished, the import
now continues past it, and the newly defined tasks are run. This repeats for
every barrier in the jugfile. Note that this means that the code before the
barrier is run several times (so it should not have side effects).

If several processes are running, a process may reach a barrier while tasks
before it are still being run by other processes. In this case, it waits
(`--wait-cycle-time` seconds, 12 by default) and imports the jugfile again. If
no progress is made for `--nr-wait-cycles` consecutive attempts (150 by
default, so 30 minutes in total), it gives up and exits. Thus, if a task
before the barrier cannot be completed (e.g., it failed, or it is locked by a
process that died), the processes waiting at the barrier exit after this
time.

`barrier()` is also useful when there are dependencies that Jug cannot see
(e.g., one task which writes a file which later tasks rely on). An alternative
solution (not always applicable) is to [add these dependencies through unused
parameters](utilities.md#identity).

## bvalue

```{versionadded} 0.10
bvalue() was added in version 0.10. Before this version, you needed to call barrier() & value() separately.
```

`bvalue` is a more targeted version of `barrier`, which combines the effect
of `value()` as well. The above example could also be written as:

```
from jug import Task, bvalue
inputs = load_data()

def keep(datum):
    # A long running computation which decides whether datum should be kept
    ...

keeps = [Task(keep, i) for i in inputs]

inputs = [i for i,k in zip(inputs, bvalue(keeps)) if k]
results = [Task(long_computation, i) for i in inputs]
```

Note, however, that if there are additional tasks which are not loaded by the
`bvalue()` call, processing can continue with them.
