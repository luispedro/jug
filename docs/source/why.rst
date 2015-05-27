==============
The Why of Jug
==============

This explains the *philosophy* behind **jug** and some of its design decisions.

Why jug? A Bit of History
-------------------------

Jug was designed to solve two intertwined problems:

1. Writing parallel code.
2. Managing intermediate files.

Up until that point, I had been writing code that saved intermediate results to
files with complex filenames (e.g., ``r3_d2_p0_p3_p22_v9.pp`` for the results
of stage 3, dataset 2, with parameters (0,3,22), running version 9 of the
code). This becomes taxing on the mind that needs to keep track of things and
extremely brittle. You constantly run the risk of having results that you are
not sure how to reproduce again.

Therefore, I decided I was going to write a solution for this.

The initial idea was something like an enhanced Makefile language. This evolved
into something similiar to `scons <http://www.scons.org/>`__. Very rapidily it
became apparent that a good solution involved *Tasks* and saving results to
files based on a hash of the inputs. This is still the basis of jug's
architecture. All of this was at the paper napkin stage, written in some off
time I had before I wrote some actual code.

The motivating applications were scientific applications and some of that is
probably part of jug's DNA in ways that are most apparent to those outside of
science.

Design Criteria
---------------

Jug was meant to *run in a queuing batch system*. Therefore, it was a good idea
to have the possibility of *just adding processes* to a running process without
any explicit synchronisation. This explains why **there is no central manager**
handing out tasks. Tasks coordinate based on a central store such as the
filesystem. This also required jug to play nice with NFS and not rely on
intra-memory communication.

Another goal (not one of the original goals, but it became a feature that we
felt we needed to keep) is that, as much as possible, **code should look
normal**. Many scripts can be *jugified* by adding ``@TaskGenerator`` to a few
function declarations. Part of this involves *making it unintrusive* (not
necessarily light-weight or low on features, but the user code should not need
much work).

jug was also meant to be used in an *exploratory development environment*.
This is why we have features such as ``jug shell``, ``jug invalidate`` (a much
better alternative than attempting to selectively update "all of the affected
files" after some code change), and, to a certain extent, ``barrier()``. Much
of the optimisation work that has been put into jug has been to support
interactive work better.

As for more down to earth goals, there should **never be any known bugs** in
jug. Any bug report has a promise to fix it ASAP. Fixing bugs takes priority
over new features, always. To attempt to keep quality high, when a bug is
found, a regression test is always written.

