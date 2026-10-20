# Map/Reduce

## Mapping, reducing and all that Jazz

Jug is **not** a map/reduce framework. However, it is still useful to sometimes
frame problems in that framework. And applying the same function to a large
collection of elements (in a word, *mapping*) is exactly the absurdly parallel
problem that Jug excels at.

### Naïve Solution

Let's say you want to double all numbers between 0 and 1023. You could do
this:

```
from jug import TaskGenerator

@TaskGenerator
def double(x):
    return 2*x

numbers = range(1024)
result = [double(n) for n in numbers]
```

This might work well for this problem. However, if instead of 1,024 numbers,
you had 1 million and each computation was very fast, then this would actually
be very inefficient: you are generating one task per computation. As a rule of
thumb, you want your computations to last at least a few seconds, otherwise,
the overhead of maintaining the infrastructure becomes too large.

### Grouping computations

You can use `jug.mapreduce.map` to achieve a better result:

```
from jug import mapreduce

result = mapreduce.map(double, numbers, map_step=32)
```

The `map_step` argument defines how many calls to `double` will be
performed in a single Task.

You can also include a reduce step:

```
@TaskGenerator
def add(a, b):
    return a + b

final = mapreduce.mapreduce(add, double, numbers, map_step=32)
```

this is sort of equivalent to:

```
from functools import reduce
final = reduce(add, map(double, numbers))
```

except that **the reduction is not done strictly from left to right**: the
elements are reduced in blocks, and then the partial results are reduced
together. Adjacent elements are always combined in order, but the grouping is
different. Therefore, this only works well if the reduction function is
associative.

### Curried mapping

The above is fine, but sometimes you need to pass multiple arguments to the
function you want to loop over:

```
@TaskGenerator
def distance_to(x, ref):
    return abs(x - ref)

ref = 34.34
inputs = range(1024)

result = [distance_to(x, ref) for x in inputs]
```

This works, but we are back to where we were: too many small Tasks!

`currymap` to the rescue:

```
result = mapreduce.currymap(distance_to, [(x,ref) for x in inputs])
```

Arguably this function should have been called `uncurrymap` (as it is
equivalent to the Haskell expression `map . uncurry`), but that just doesn't
sound right (I also like to think it's the programming equivalent to the
Currywurst, a culinary concept which almost makes me chuckle).

## Example

The canonical example for map/reduce is counting words in files. Here, we will
do the same with some very small files:

```
inputs = [
        "banana apple apple banana",
        "apple pear football",
        "pear",
        "banana apple apple",
        "football banana",
        "apple pear",
        "waldorf salad",
        ]
```

The `mapper` function will output a dictionary of counts:

```
def count1(str):
    from collections import defaultdict
    counts = defaultdict(int)
    for word in str.split():
        counts[word] += 1
    return counts
```

(We used the very useful `collections.defaultdict`).

While the `reducer` adds two dictionaries together:

```
def merge_dicts(lhs, rhs):
    # Note that we SHOULDN'T modify arguments, so we will create a copy
    merged = lhs.copy()
    for k,v in rhs.items():
        merged[k] += v
    return merged
```

We can now use `jug.mapreduce.mapreduce` to put these together:

```
final_counts = jug.mapreduce.mapreduce(
                        merge_dicts,
                        count1,
                        inputs,
                        map_step=1)
```

Running `jug status` shows up the structure of our problem:

```
      Failed     Waiting       Ready    Complete      Active  Task name
-----------------------------------------------------------------------------------------------
           0           0           7           0           0  jug.mapreduce._jug_map_reduce
           0           1           0           0           0  jug.mapreduce._jug_reduce
...............................................................................................
           0           1           7           0           0  Total
```

If we had more than just 7 "files", the values in the table would be much
larger. Let's also assume that this is part of some much larger programme that
computes counts and then does some further processing with them.

Once that task is done, we might not care anymore about the break up into 7
units. So, we can wrap the whole thing into a **compound task**:

```
final_counts = CompoundTask(jug.mapreduce.mapreduce,
                        merge_dicts,
                        count1,
                        inputs,
                        map_step=1)
```

At first, this does not do much. The status is the same:

```
      Failed     Waiting       Ready    Complete      Active  Task name
----------------------------------------------------------------------------------------------------
           0           1           0           0           0  jug.compound.compound_task_execute
           0           0           7           0           0  jug.mapreduce._jug_map_reduce
           0           1           0           0           0  jug.mapreduce._jug_reduce
....................................................................................................
           0           2           7           0           0  Total
```

But if we *execute* the tasks and re-check the status:

```
      Failed     Waiting       Ready    Complete      Active  Task name
-----------------------------------------------------------------------------------------
           0           0           0           1           0  jug.mapreduce.mapreduce
.........................................................................................
           0           0           0           1           0  Total
```

Now, `jug status` reports a single task (the mapreduce task) and it is *Complete*.

Compound tasks not only lower the cognitive load, but they also make operations
such as `jug status` much faster.

### Full example source code

We left out the imports above, but other than that, it is a fully functional example:

```
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


def merge_dicts(lhs, rhs):
    # Note that we SHOULDN'T modify arguments, so we will create a copy
    merged = lhs.copy()
    for k,v in rhs.items():
        merged[k] += v
    return merged

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
```
