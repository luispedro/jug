Worked-Out Example 1
====================
Processing text
...............

Problem: Take a list of the British members of Parliament (MPs) in the last
decade and characterise each by a couple of *meaningful* word from their
wikipedia pages. Meaningful words are those that appear in the article for the
the particular MP but not everywhere else.

(The complete code for this example and a list of MPs [valid in 2010] with the
`jug source <https://github.com/luispedro/jug/tree/master/examples/text>`__)

The algorithm looks like this:

.. code-block:: python

    allcounts = []
    for mp in MPs:
        article = get_data(mp)
        words = count_words(mp, article)
        allcounts.append(words)

    global_counts = add_counts(allcounts) # Here all processes must sync

    for mp, mp_count in zip(MPs, counts):
        meaningful = []
        for w, c in mp_count:
            if c > global_counts[w] // 100:
                meaningful.append(w)
        meaningful.sort(key=mp_count.get)
        meaningful.reverse()
        print(mp, meaningful[:8])

Very simple. It's also *embarassingly parallel*, except for the line which
computes ``global_counts``, because it uses the results from everyone.

To use ``jug``, we write the above, including the functions, to a file (in this
case, the file is ``jugfile.py``). Now, I can call ``jug status jugfile.py`` to
see the state of the computation::

    Task name                                    Waiting       Ready    Finished     Running
    ----------------------------------------------------------------------------------------
    jugfile.get_data                                   0         657           0           0
    jugfile.count_words                              657           0           0           0
    jugfile.divergence                               657           0           0           0
    jugfile.add_counts                                 1           0           0           0
    ........................................................................................
    Total:                                          1315         657           0           0


Unsurprisingly, no task is finished and only the ``get_data`` task is ready to
run. No nodes are running. So, let's start a couple of processes [#]_:

.. code-block:: bash

    $ jug execute jugfile.py &
    $ jug execute jugfile.py &
    $ jug execute jugfile.py &
    $ jug execute jugfile.py &
    $ sleep 4
    $ jug status jugfile.py
    $ sleep 48
    $ jug status jugfile.py

This prints out first:

.. code-block:: bash

    Task name                                    Waiting       Ready    Finished     Running
    ----------------------------------------------------------------------------------------
    jugfile.get_data                                   0         653           0           4
    jugfile.count_words                              657           0           0           0
    jugfile.divergence                               657           0           0           0
    jugfile.add_counts                                 1           0           0           0
    ........................................................................................
    Total:                                          1315         653           0           4

    $ sleep 48
    $ jug status jugfile.py

    Task name                                    Waiting       Ready    Finished     Running
    ----------------------------------------------------------------------------------------
    jugfile.get_data                                   0         635          20           2
    jugfile.count_words                              637           2          16           2
    jugfile.divergence                               657           0           0           0
    jugfile.add_counts                                 1           0           0           0
    ........................................................................................
    Total:                                          1295         637          36           4


So, we can see that almost immediately after the four background processes were
started, 4 of them were working on the ``get_data`` task [#]_.

Forty-eight seconds later, some of the ``get_data`` calls are finished, which
makes some ``count_words`` tasks be callable and some have been executed. The
order in which tasks are executed is decided by ``jug`` itself.

At this point, we can add a couple more nodes to the process if we want for no
other reason than to demonstrate this capability (maybe you have a dynamic
clustering system and a whole lot more nodes have become available). The nodes
will happily chug along until we get to the following situation::

    Task name                                    Waiting       Ready    Finished     Running
    ----------------------------------------------------------------------------------------
    jugfile.get_data                                   0           0         657           0
    jugfile.count_words                                0           0         657           0
    jugfile.divergence                               657           0           0           0
    jugfile.add_counts                                 0           0           0           1
    ........................................................................................
    Total:                                           657           0        1314           1


This is the bottleneck in the programme: Notice how there is only one node
running, it is computing ``add_counts()``. Everyone else is waiting (there are no
*ready* tasks) [#]_. Fortunately, once that node finishes, everyone else can get to
work computing ``divergence``::

    Task name                                    Waiting       Ready    Finished     Running
    ----------------------------------------------------------------------------------------
    jugfile.get_data                                   0           0         657           0
    jugfile.count_words                                0           0         657           0
    jugfile.divergence                                 0         653           0           4
    jugfile.add_counts                                 0           0           1           0
    ........................................................................................
    Total:                                             0         653        1315           4

Eventually, all the nodes finish and we are done. All the results are now left
inside ``jugdata``. To access it, we can write a little script:

.. code-block:: python

    import jug
    import jug.task

    jug.init('jugfile.py', 'jugdata')
    import jugfile

    results = jug.task.value(jugfile.results)
    for mp, r in zip(file('MPs.txt'), results):
        mp = mp.strip()
        print(mp, ":    ", " ".join(r[:8]))


The ``jug.init()`` call takes the *jugfile* (which does not need to be called
*jugfile.py*) and the storage backend (at the simplest, just a directory path
like here). Internally, ``jug.init`` imports the module, but we need to import
it here too to make the names available (**it is important that you use this
interface.** For example, running the jugfile directly on the interpreter might
result in different task names and weirdness all around). ``jug.task.value``
looks up the value computed and then we can process the results into a nicer
output format.

Besides serving to demonstrate, ``jug``'s abilities, this is actually a very
convenient format for organising computations:

1.  Have a master jugfile.py that does all the computations that take a long
    time.
2.  Have a secondary outputresult.py that loads the results and does the pretty
    printing. This should run fast and not do much computation.

The reason why it's good to have the second step as a separate process is that
you often want fast iteration on the output or even interactive use (if you are
outputting a graph, for example; you want to be able to fiddle with the colours
and axes and have immediate feedback).  Otherwise, you could have had everything
in the main ``jugfile.py``, with a final function writing to an output file.

.. [#] For this tutorial, all nodes are on the same machine. In real life, they
   could be on different computers as long as they can communicate with each
   other.
.. [#] In order to make this a more realistic example, tasks all call the
   ``sleep()`` function to simulate long running processes. This example,
   without the ``sleep()`` calls, takes four seconds to run, so it wouldn't be
   worth the effort to run multiple processors. Check ``jugfile.py`` for
   details.
.. [#] There is a limit to how long the nodes will wait before giving up to
   avoid having one bad task keep every node in active-wait mode, which is very
   unfriendly if you are sharing a cluster. By default, the maximum wait time
   is set to roughly half an hour. You can set this with the
   ``--nr-wait-cycles`` (how many times jug will check for tasks) and
   ``--wait-cycle-time`` (the number of seconds to wait between each check).

