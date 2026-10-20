# Jug: A Task-Based Parallelization Framework

```{note}
If you use Jug to generate results for a scientific publication, please cite

> Coelho, L.P., (2017). Jug: Software for Parallel Reproducible Computation in
> Python. Journal of Open Research Software. 5(1), p.30.
>
> <https://doi.org/10.5334/jors.161>
```

## What is Jug?

Jug allows you to write code that is broken up into tasks and run different
tasks on different processors.

Its main backend uses the filesystem to communicate between processes and
works correctly over NFS, so you can coordinate processes on different
machines. Another is based on redis so the processes only need the capability
to connect to a common redis server. See [backends](backends.md) for all
options.

Jug also takes care of saving all the intermediate results to the backend in a
way that allows them to be retrieved later.

## Examples

### Short Example

Here is a one minute example. Save the following to a file called `primes.py`:

```{literalinclude} ../examples/primes/primes.py
```

Of course, this is only for didactic purposes, normally you would use a
better method. Similarly, the `sleep` function is so that it does not run too
fast.

Now type `jug status primes.py` to get:

```
      Failed     Waiting       Ready    Complete      Active  Task name
-------------------------------------------------------------------------------------
           0           1           0           0           0  primes.count_primes
           0           0          99           0           0  primes.is_prime
           0           1           0           0           0  primes.write_output
.....................................................................................
           0           2          99           0           0  Total
```

This tells you that you have 99 tasks called `primes.is_prime` ready to run,
while both other tasks are *waiting* (i.e., they need the `primes.is_prime`
tasks to finish). So run `jug execute primes.py &`. You can even run
multiple instances in the background (if you have multiple cores, for example).
After starting 4 instances and waiting a few seconds, you can check the status
again (with `jug status primes.py`):

```
      Failed     Waiting       Ready    Complete      Active  Task name
-------------------------------------------------------------------------------------
           0           1           0           0           0  primes.count_primes
           0           0          63          32           4  primes.is_prime
           0           1           0           0           0  primes.write_output
.....................................................................................
           0           2          63          32           4  Total
```

Now you have 32 tasks complete, 4 active (running), and 63 still ready. Eventually, they
will all finish (including `count_primes` and `write_output`) and you can
inspect the results with `jug shell primes.py`. This will give you an
`ipython` shell. The `primes100` variable is available, but it is an ugly
list of `jug.Task` objects. To get the actual value, you call the `value`
function:

```
In [1]: primes100 = value(primes100)

In [2]: primes100[:10]
Out[2]: [True, True, False, True, False, True, False, False, False, True]
```

### More Examples

There is a worked out example in the [tutorial](tutorial.md). The
[`examples/`](https://github.com/luispedro/jug/tree/main/examples) directory
contains three fully functioning examples:

- [`primes`](https://github.com/luispedro/jug/tree/main/examples/primes): the
  short example above,
- [`decrypt`](https://github.com/luispedro/jug/tree/main/examples/decrypt):
  cracking a password by brute force (see the [decryption
  example](decrypt-example.md)),
- [`text`](https://github.com/luispedro/jug/tree/main/examples/text): finding
  meaningful words in Wikipedia articles (see the [text example](text-example.md)).

## Links

- [Mailing list](https://groups.google.com/g/jug-users)
- [Github](https://github.com/luispedro/jug)
- [Documentation](https://jug.readthedocs.io/)

## How do I get Jug?

The simplest is using pip:

```
pip install jug
```

You can also get the git repository at

[https://github.com/luispedro/jug](https://github.com/luispedro/jug)

Or download the package from [PyPI](https://pypi.org/project/Jug/)

If you use [conda](https://anaconda.org/), you can install jug from
[conda-forge](https://conda-forge.org/):

```
conda config --add channels conda-forge
conda install jug
```

## What do I need to run Jug?

It is a Python only package. Jug is [continuously tested](https://github.com/luispedro/jug/actions) with Python 3.10 and up.

## How does it work?

Read the [tutorial](tutorial.md).

## What's the status of the project?

Since version 1.0, jug should be considered stable.

## Testimonials

"I've been using jug with great success to distribute the running of a
reasonably large set of parameter combinations" - Andreas Longva

## Documentation Contents

```{toctree}
:maxdepth: 2

tutorial
ai-assistants
decrypt-example
text-example
segmentation-example
subcommands
status
exit
hooks
shell
types
tasks
tasklets
invalidate
idioms
barrier
compound
utilities
mapreduce
backends
configuration
bash
faq
why
writeabackend
magic
api
history
```

## Indices and tables

- {ref}`genindex`
- {ref}`modindex`
- {ref}`search`

