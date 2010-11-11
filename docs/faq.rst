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

And it will work fine. Jobs can join at any time too.

