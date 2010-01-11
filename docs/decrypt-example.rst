Worked-Out Example 0
====================
Processing text
...............

Problem: crack an encrypted file by brute force. Assume that the password is a
five-letter lower-case word and that you know that the plain text contains my
name.

This is the ultimate parallel problem: try very many keys (26**5 ~ 11M), but
there is no interaction between the different tasks.

The brute force version is very simple::

    for p in product(letters, repeat=5):
    text = decode(ciphertext, p)
    if isgood(text):
        passwd = "".join(map(chr,p))
        print '%s:%s' % (passwd, text)

However, if we have more than one processor, we'd like to be able to jug
``jug`` to use the multiple processors.

We cannot simply have each password be its own task: 11M tasks would be too
much!

So, we are going to iterate over the first letter and a task will consist of
trying every possibility *starting* with that letter::

    @TaskGenerator
    def decrypt(prefix, suffix_size):
        res = []
        for p in product(letters, repeat=suffix_size):
            text = decode(ciphertext, np.concatenate([prefix, p]))
            if isgood(text):
                passwd = "".join(map(chr,p))
                res.append((passwd, text))
        return res

    @TaskGenerator
    def join(partials):
        return list(chain(*partials))

    fullresults = join([decrypt( [let], 4) for let in letters])

Here, the ``decrypt`` function returns a list of all the good passwords it
found. To simplify things, we call the ``join`` function which concatenates all
the partial results into a single list for convenience.

In order to make sense of all of this, we write a final script, which loads the
results and prints them on stdout::

    import jug
    jug.init('jugfile', 'jugdata')
    import jugfile
    results = jug.task.value(jugfile.fullresults)
    for p,t in results:
        print "%s\n\n    Password was '%s'" % (t,p)

``jug.init`` takes the jugfile name (which happens to be ``jugfile.py``, the
extension is optional if it is ``.py``) and the data directory name.

``jug.task.value`` takes a ``jug.Task`` and loads its result. It handles more
complex cases too, such as a list of tasks (and returns a list of their
results).

