Worked-Out Example 0
====================
Decrypting a Password
.....................

Problem: crack an encrypted file by brute force. Assume that the password is a
five-letter lower-case word and that you know that the plain text contains my
name.

(The complete code for this example and a secret message comes with the
`jug source <https://github.com/luispedro/jug/tree/master/examples/decrypt>`__)

This is the ultimate parallel problem: try very many keys (26**5 ~ 11M), but
there is no interaction between the different tasks.

The brute force version is very simple:

.. code-block:: python

    for p in product(letters, repeat=5):
        text = decode(ciphertext, p)
        if isgood(text):
            passwd = "".join(map(chr, p))
            print('%s:%s' % (passwd, text))

However, if we have more than one processor, we'd like to be able to tell
``jug`` to use multiple processors.

We cannot simply have each password be its own task: 11M tasks would be too
much!

So, we are going to iterate over the first letter and a task will consist of
trying every possibility *starting* with that letter:

.. code-block:: python

    @TaskGenerator
    def decrypt(prefix, suffix_size):
        res = []
        for p in product(letters, repeat=suffix_size):
            text = decode(ciphertext, np.concatenate([prefix, p]))
            if isgood(text):
                passwd = "".join(map(chr, p))
                res.append((passwd, text))
        return res

    @TaskGenerator
    def join(partials):
        return list(chain(*partials))

    fullresults = join([decrypt([let], 4) for let in letters])

Here, the ``decrypt`` function returns a list of all the good passwords it
found. To simplify things, we call the ``join`` function which concatenates all
the partial results into a single list for convenience.

Now, run ``jug``:

.. code-block:: bash

    $ jug execute jugfile.py &
    $ jug execute jugfile.py &
    $ jug execute jugfile.py &
    $ jug execute jugfile.py &

You can run as many simultaneous processes as you have processors. To see what
is happening, type:

.. code-block:: bash

    $ jug status jugfile.py

And you will get an output such as::

    Task name                                    Waiting       Ready    Finished     Running
    ----------------------------------------------------------------------------------------
    jugfile.join                                       1           0           0           0
    jugfile.decrypt                                    0          14           8           4
    ........................................................................................
    Total:                                             1          14           8           4


There are two task functions: ``decrypt``, of which 8 are finished, 14 are ready
to run, and 4 are currently running; and ``join`` which has a single instance,
which is ``waiting``: it cannot run until all the ``decrypt`` tasks have
finished.

Eventually, everything will be finished and your results will be saved in
directory ``jugdata`` in files with names such as
``jugdata/5/4/a1266debc307df7c741cb7b997004f`` The name is simply a hash of the
task description (function and its arguments).

In order to make sense of all of this, we write a final script, which loads the
results and prints them on stdout:

.. code-block:: python

    import jug
    jug.init('jugfile.py', 'jugdata')
    import jugfile

    results = jug.task.value(jugfile.fullresults)
    for p, t in results:
        print("%s\n\n    Password was '%s'" % (t, p))

``jug.init`` takes the jugfile name (which happens to be ``jugfile.py``) and
the data directory name.

``jug.task.value`` takes a ``jug.Task`` and loads its result. It handles more
complex cases too, such as a list of tasks (and returns a list of their
results).

