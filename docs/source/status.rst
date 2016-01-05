======
Status
======

Simple Status
-------------

The ``status`` subcommand displays a summary of the computation status, for
example::

    $ jug status
         Waiting       Ready    Finished     Running  Task name              
    -------------------------------------------------------------------------
               0           2           0           0  jugfile.compfeats      
              10           0           0           0  jugfile.nfold          
    .........................................................................
              10           2           0           0  Total                  


Short Status
------------

The same status as above, now in a ``short`` version::

    $ jug status --short
    12 tasks to be run, 0 finished, (none running).


Cached Status
-------------

If you have many tasks, then ``jug status`` can become pretty slow. One way to
speed it up is to use a cache::


    $ jug status --cache

or::

    $ jug status --cache --short

The first time you run it, it will be as slow as usual as it will parse the
jugfile and interrogate the store for every possible task. However, then it
will save a record which will enable it to speed up the next few times.

**Note**: This is a fragile system, which should be used with care as the cache
can easily become out of sync with the jugfile used (``jugfile.py`` in the
examples above). It is kept in jug as the speed gains can be quite spectacular
(from many seconds to instantaneous).

