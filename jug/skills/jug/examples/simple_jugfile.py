"""
Simple annotated Jug example.

Task graph:
  process(item_0) \
  process(item_1)  --> aggregate([result_0, result_1, ...])
  ...

Run with:
  jug execute simple_jugfile.py        # in one or more terminals / machines
  jug status simple_jugfile.py         # check progress
  jug status simple_jugfile.py --short # one-line summary
"""

from jug import TaskGenerator

# ---------------------------------------------------------------------------
# Step 1: define task functions with @TaskGenerator
#
# Calling process(item) now returns a Task object — it does NOT run the
# function immediately. The real call happens inside `jug execute`.
# ---------------------------------------------------------------------------

@TaskGenerator
def process(item):
    """Simulate an expensive computation for one item."""
    import time, math
    time.sleep(2)                   # pretend this takes a while
    return math.sqrt(item)


@TaskGenerator
def aggregate(results):
    """Combine per-item results into a final summary."""
    return sum(results)


# ---------------------------------------------------------------------------
# Step 2: build the task graph
#
# This runs at import time and is fast — no actual computation happens here.
# Each process(i) call creates a Task and records it in jug's task registry.
# ---------------------------------------------------------------------------

items = list(range(20))

# List of Task objects (not results!)
partial_results = [process(item) for item in items]

# Task whose argument is a list of other tasks — jug resolves them at run time
total = aggregate(partial_results)

# ---------------------------------------------------------------------------
# How jug uses this file:
#
#   1. `jug execute` imports this module, collecting all Task objects.
#   2. It scans for tasks whose dependencies are satisfied (no deps for
#      `process` tasks; all `process` tasks must finish before `aggregate`).
#   3. It locks a ready task and calls the underlying function with resolved
#      argument values.
#   4. The result is pickled and saved in the jugdir.
#   5. Next time the jugfile is imported, already-finished tasks are skipped.
# ---------------------------------------------------------------------------
