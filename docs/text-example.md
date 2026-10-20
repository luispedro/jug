# Worked-Out Example 1

## Processing text

Problem: Take a list of the British members of Parliament (MPs) in the last
decade and characterise each by a couple of *meaningful* words from their
wikipedia pages. Meaningful words are those that appear in the article for the
particular MP but not everywhere else.

(The complete code for this example and a list of MPs [valid in 2010] with the
[jug source](https://github.com/luispedro/jug/tree/main/examples/text))

To run it, you need the [requests](https://pypi.org/project/requests/)
package (`pip install requests`) and network access, as the articles are
downloaded from Wikipedia.

The algorithm looks like this:

```python
allcounts = []
for mp in MPs:
    article = get_data(mp)
    words = count_words(mp, article)
    allcounts.append(words)

global_counts = add_counts(allcounts) # Here all processes must sync

for mp, mp_count in zip(MPs, allcounts):
    meaningful = []
    for w, c in mp_count.items():
        if c > global_counts[w] // 100:
            meaningful.append(w)
    meaningful.sort(key=mp_count.get)
    meaningful.reverse()
    print(mp, meaningful[:8])
```

Very simple. It's also *embarrassingly parallel*, except for the line which
computes `global_counts`, because it uses the results from everyone.

To use `jug`, we write the above, including the functions, to a file (in this
case, the file is `jugfile.py`). Now, I can call `jug status jugfile.py` to
see the state of the computation:

```
      Failed     Waiting       Ready    Complete      Active  Task name
-------------------------------------------------------------------------------------
           0           1           0           0           0  jugfile.add_counts
           0         656           0           0           0  jugfile.count_words
           0         656           0           0           0  jugfile.divergence
           0           0         656           0           0  jugfile.get_data
.....................................................................................
           0        1313         656           0           0  Total
```

Unsurprisingly, no task is complete and only the `get_data` task is ready to
run. No nodes are running. So, let's start a couple of processes [^footnote-1]:

```bash
$ jug execute jugfile.py &
$ jug execute jugfile.py &
$ jug execute jugfile.py &
$ jug execute jugfile.py &
$ sleep 4
$ jug status jugfile.py
$ sleep 48
$ jug status jugfile.py
```

This prints out first:

```
      Failed     Waiting       Ready    Complete      Active  Task name
-------------------------------------------------------------------------------------
           0           1           0           0           0  jugfile.add_counts
           0         656           0           0           0  jugfile.count_words
           0         656           0           0           0  jugfile.divergence
           0           0         652           0           4  jugfile.get_data
.....................................................................................
           0        1313         652           0           4  Total

$ sleep 48
$ jug status jugfile.py

      Failed     Waiting       Ready    Complete      Active  Task name
-------------------------------------------------------------------------------------
           0           1           0           0           0  jugfile.add_counts
           0         636           2          16           2  jugfile.count_words
           0         656           0           0           0  jugfile.divergence
           0           0         634          20           2  jugfile.get_data
.....................................................................................
           0        1293         636          36           4  Total
```

So, we can see that almost immediately after the four background processes were
started, 4 of them were working on the `get_data` task [^footnote-2].

Forty-eight seconds later, some of the `get_data` calls are finished, which
makes some `count_words` tasks be callable and some have been executed. The
order in which tasks are executed is decided by `jug` itself.

At this point, we can add a couple more nodes to the process if we want for no
other reason than to demonstrate this capability (maybe you have a dynamic
clustering system and a whole lot more nodes have become available). The nodes
will happily chug along until we get to the following situation:

```
      Failed     Waiting       Ready    Complete      Active  Task name
-------------------------------------------------------------------------------------
           0           0           0           0           1  jugfile.add_counts
           0           0           0         656           0  jugfile.count_words
           0         656           0           0           0  jugfile.divergence
           0           0           0         656           0  jugfile.get_data
.....................................................................................
           0         656           0        1312           1  Total
```

This is the bottleneck in the programme: Notice how there is only one node
running, it is computing `add_counts()`. Everyone else is waiting (there are no
*ready* tasks) [^footnote-3]. Fortunately, once that node finishes, everyone else can get to
work computing `divergence`:

```
      Failed     Waiting       Ready    Complete      Active  Task name
-------------------------------------------------------------------------------------
           0           0           0           1           0  jugfile.add_counts
           0           0           0         656           0  jugfile.count_words
           0           0         652           0           4  jugfile.divergence
           0           0           0         656           0  jugfile.get_data
.....................................................................................
           0           0         652        1313           4  Total
```

Eventually, all the nodes finish and we are done. All the results are now left
inside `jugfile.jugdata` (by default, the jugdir is named after the jugfile). To access it, we can write a little script:

```python
import jug
import jug.task

jug.init('jugfile.py', 'jugfile.jugdata')
import jugfile

results = jug.task.value(jugfile.results)
for mp, r in zip(open('MPs.txt', encoding='utf-8'), results):
    mp = mp.strip()
    print(mp, ":    ", " ".join(r[:8]))
```

The `jug.init()` call takes the *jugfile* (which does not need to be called
*jugfile.py*) and the storage backend (at the simplest, just a directory path
like here). Internally, `jug.init` imports the module, but we need to import
it here too to make the names available (**it is important that you use this
interface.** For example, running the jugfile directly on the interpreter might
result in different task names and weirdness all around). `jug.task.value`
looks up the value computed and then we can process the results into a nicer
output format.

Besides serving to demonstrate `jug`'s abilities, this is actually a very
convenient format for organising computations:

1. Have a master jugfile.py that does all the computations that take a long
   time.
2. Have a secondary outputresult.py that loads the results and does the pretty
   printing. This should run fast and not do much computation.

The reason why it's good to have the second step as a separate process is that
you often want fast iteration on the output or even interactive use (if you are
outputting a graph, for example; you want to be able to fiddle with the colours
and axes and have immediate feedback). Otherwise, you could have had everything
in the main `jugfile.py`, with a final function writing to an output file.

[^footnote-1]: For this tutorial, all nodes are on the same machine. In real life, they
    could be on different computers as long as they can communicate with each
    other.

[^footnote-2]: In order to make this a more realistic example, tasks all call the
    `sleep()` function to simulate long running processes. This example,
    without the `sleep()` calls, takes four seconds to run, so it wouldn't be
    worth the effort to run multiple processors. Check `jugfile.py` for
    details.

[^footnote-3]: There is a limit to how long the nodes will wait before giving up to
    avoid having one bad task keep every node in active-wait mode, which is very
    unfriendly if you are sharing a cluster. By default, the maximum wait time
    is set to roughly half an hour. You can set this with the
    `--nr-wait-cycles` (how many times jug will check for tasks) and
    `--wait-cycle-time` (the number of seconds to wait between each check).
    See [execute](https://jug.readthedocs.io/en/latest/subcommands.html#execute) for all the options.
