Problem: Take a list of the British members of Parliament (MPs) in the last
decade and characterise each by a couple of *meaningful* word from their
wikipedia pages. Meaningful words are those that appear in the article for the
the particular MP but not everywhere else.

So the algorithm looks like this:

::

    allcounts = []
    for mp in MPs:
        article = get_data(mp)
        words = count_words(article)
        allcounts.append(words)

    global_counts = add_counts(allcounts) # Here all processes must sync

    for mp,mp_count in zip(MPs,counts):
        meaningfull = []
        for w,c in mp_count:
            if c > global_counts[w]//100: meaningful.append(w)
        meaningful.sort(key=mp_count.get)
        meaningful.reverse()
        print mp, meaningful[:8]

Very simple. It's also *embarassingly parallel*, except for the line where
``global_counts`` is computed, because it uses the results from everyone.

To use ``jug``, we write the above, including the functions, to a file (in this
case, the file is ``jugfile.py``). Now, I can call ``jug status jugfile.py`` to
see the state of the computation:

::
    
    Task name                                    Waiting       Ready    Finished     Running
    ----------------------------------------------------------------------------------------
    jugfile.getdata                                    0         657           0           0
    jugfile.countwords                               657           0           0           0
    jugfile.divergence                               657           0           0           0
    jugfile.addcounts                                  1           0           0           0
    ........................................................................................
    Total:                                          1315         657           0           0


Unsurprisingly, no task is finished and only the ``getdata`` task is ready to
run. No nodes are running. So, let's start a couple of processes `[#]`_:

::

    jug execute jugfile.py &
    jug execute jugfile.py &
    jug execute jugfile.py &
    jug execute jugfile.py &
    sleep 4
    jug status jugfile.py
    sleep 48
    jug status jugfile.py

This prints out first:

:: 
    Task name                                    Waiting       Ready    Finished     Running
    ----------------------------------------------------------------------------------------
    jugfile.getdata                                    0         653           0           4
    jugfile.countwords                               657           0           0           0
    jugfile.divergence                               657           0           0           0
    jugfile.addcounts                                  1           0           0           0
    ........................................................................................
    Total:                                          1315         653           0           4

    luispedro@oakeshott:/home/luispedro/work/jug/examples/text §sleep 48
    luispedro@oakeshott:/home/luispedro/work/jug/examples/text §jug status jugfile.py

    Task name                                    Waiting       Ready    Finished     Running
    ----------------------------------------------------------------------------------------
    jugfile.getdata                                    0         635          20           2
    jugfile.countwords                               637           2          16           2
    jugfile.divergence                               657           0           0           0
    jugfile.addcounts                                  1           0           0           0
    ........................................................................................
    Total:                                          1295         637          36           4


So, we can see that almost immediately after the four background processes were
started, 4 of them were working on the ``getdata`` task`[#]`_.

Forty-eight seconds later, some of the ``getdata`` calls are finished, which
makes some ``countwords`` tasks be callable and some have been executed. The
order in which tasks are executed is decided by ``jug`` itself.

At this point, we can add a couple more nodes to the process if we want for no
other reason than to demonstrate this capability (maybe you have a dynamic
clustering system and a whole lot more nodes have become available). The nodes
will happily chug along until we get to the following situation:

::

    Task name                                    Waiting       Ready    Finished     Running
    ----------------------------------------------------------------------------------------
    jugfile.getdata                                    0           0         657           0
    jugfile.countwords                                 0           0         657           0
    jugfile.divergence                               657           0           0           0
    jugfile.addcounts                                  0           0           0           1
    ........................................................................................
    Total:                                           657           0        1314           1


This is the bottleneck in the programme: Notice how there is only one node
running, it is computing ``addcounts()``. Everyone else is waiting (there are no
*ready* tasks) `[#]`_. Fortunately, once that node finishes, everyone else can get to
work computing ``divergence``:

::

    Task name                                    Waiting       Ready    Finished     Running
    ----------------------------------------------------------------------------------------
    jugfile.getdata                                    0           0         657           0
    jugfile.countwords                                 0           0         657           0
    jugfile.divergence                                 0         653           0           4
    jugfile.addcounts                                  0           0           1           0
    ........................................................................................
    Total:                                             0         653        1315           4

Eventually, all the nodes finish and we are done. All the results are now left
inside ``jugdata``. To access it, we can write a little script:

::

    import jug
    import jug.task

    jug.init('jugfile', 'jugdata')
    import jugfile

    results = jug.task.value(jugfile.results)
    for mp,r in zip(file('MPs.txt'), results):
        mp = mp.strip()
        print mp, ":    ", " ".join(r[:8])


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

    1. Have a master jugfile.py that does all the computations that take a long
    time.
    2. Have a secondary outputresult.py that loads the results and does the
    pretty printing. This should run fast and not do much computation.

The reason why it's good to have the second step as a separate process is that
you often want fast iteration on the output or even interactive use (if tyou are
outputing a graph, for example; you want to be able to fiddle with the colours
and axes and have immediate feedback).  Otherwise, you could have had everything
in the main ``jugfile.py``, with a final function writing to an output file.

.. [#] For this tutorial, all nodes are on the same machine. In real life, they
   could be in different computers as long as they can communicate with each
   other.
.. [#] In order to make this a more realistic example, tasks all call the
   ``sleep()`` function to simulate long running processes. This example,
   without the ``sleep()`` calls, takes four seconds to run, so it wouldn't be
   much worth the effort to run multiple processors. Check ``jugfile.py`` for
   details.
.. [#] There is a limit to how much the nodes will wait before giving up to
   avoid having one bad task keep every node in active-wait mode, which is very
   unfriendly if you are sharing a cluster. Right now, the maximum wait time is
   set to roughly half an hour. Eventually, this will be configurable.
