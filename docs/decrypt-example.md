# Worked-Out Example 0

## Decrypting a Password

Problem: crack an encrypted file by brute force. Assume that the password is a
five-letter lower-case word and that you know that the plain text contains my
name.

(The complete code for this example and a secret message comes with the
[jug source](https://github.com/luispedro/jug/tree/master/examples/decrypt))

This is the ultimate parallel problem: try very many keys (26\*\*5 ~ 11M), but
there is no interaction between the different tasks.

The brute force version is very simple:

```python
for p in product(letters, repeat=5):
    text = decode(ciphertext, p)
    if isgood(text):
        passwd = "".join(map(chr, p))
        print('%s:%s' % (passwd, text))
```

However, if we have more than one processor, we'd like to be able to tell
`jug` to use multiple processors.

We cannot simply have each password be its own task: 11M tasks would be too
much!

So, we are going to iterate over the first letter and a task will consist of
trying every possibility *starting* with that letter:

```python
@TaskGenerator
def decrypt(prefix):
    res = []
    for suffix in product(letters, repeat=5 - len(prefix)):
        passwd = np.concatenate([prefix, suffix])
        text = decode(ciphertext, passwd)
        if isgood(text):
            passwd = "".join(map(chr, passwd))
            res.append((passwd, text))
    return res

@TaskGenerator
def join(partials):
    return list(chain(*partials))

fullresults = join([decrypt([let]) for let in letters])
```

Here, the `decrypt` function returns a list of all the good passwords it
found. To simplify things, we call the `join` function which concatenates all
the partial results into a single list for convenience.

Now, run `jug`:

```bash
$ jug execute jugfile.py &
$ jug execute jugfile.py &
$ jug execute jugfile.py &
$ jug execute jugfile.py &
```

You can run as many simultaneous processes as you have processors. To see what
is happening, type:

```bash
$ jug status jugfile.py
```

And you will get an output such as:

```
      Failed     Waiting       Ready    Complete      Active  Task name
---------------------------------------------------------------------------------
           0           0          14           8           4  jugfile.decrypt
           0           1           0           0           0  jugfile.join
.................................................................................
           0           1          14           8           4  Total
```

There are two task functions: `decrypt`, of which 8 are complete, 14 are ready
to run, and 4 are currently active (running); and `join` which has a single instance,
which is `waiting`: it cannot run until all the `decrypt` tasks have
finished.

Eventually, everything will be finished and your results will be saved in
directory `jugfile.jugdata` (by default, the jugdir is named after the
jugfile) in files with names such as
`jugfile.jugdata/04/545bde0f665d9364005e10bb83b7ccf3e11b05`. The name is simply
a hash of the task description (function and its arguments).

In order to make sense of all of this, we write a final script, which loads the
results and prints them on stdout:

```python
import jug
jug.init('jugfile.py', 'jugfile.jugdata')
import jugfile

results = jug.task.value(jugfile.fullresults)
for p, t in results:
    print(f"{t}\n\n    Password was '{p}'")
```

`jug.init` takes the jugfile name (which happens to be `jugfile.py`) and
the data directory name.

`jug.task.value` takes a `jug.Task` and loads its result. It handles more
complex cases too, such as a list of tasks (and returns a list of their
results).
