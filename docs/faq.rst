==========================
Frequently Asked Questions
==========================

Why the name jug?
-----------------

The cluster I was using when I first started developing jug was called
"juggernaut". That is too long and there is a Unix tradition of 3-character
programme names, so I abbreviated it to jug.

Will jug work on batch cluster systems (like SGE or PBS)?
---------------------------------------------------------

Yes, it was built for it. Submit jobs that look like::

    jug execute my_jug_script.py --jugdir=my_jug_dir

And it will work fine. Jobs can join at any time too, which makes jug
especially suited for these environments.

Can jug handle non-pickle() objects?
------------------------------------

Short answer: No.

Long answer: Yes, with a little bit of special code. If you have another way to
get them from one machine to another, you could write a special backend for
that. Right now, only ``numpy`` arrays are treated as a special case (they are
not pickled, but rather saved in their native format), but you could extend
this. Ask on the `mailing list <http://groups.google.com/group/jug-users>`_ if
you want to learn more.

