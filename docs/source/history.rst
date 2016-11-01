=======
History
=======

version **1.3.0** (Tue Nov 1 2016)
- Update `shell` subcommand to IPython 5
- Use ~/.config/jugrc as configuration file
- Cleanup usage string
- Use `bottle` instead of `web.py` for webstatus subcommand
- Add `jug_execute` function
- Add timing functionality

version **1.2.2** (Sat Jun 25 2016)
- Fix bugs in shell subcommand and a few corner cases in encoding/decoding
  results

version **1.2.1** (Mon Feb 15 2016)
- Changed execution loop to ensure that all tasks are checked (issue #33 on
  github)
- Fixed bug that made 'check' or 'sleep-until' slower than necessary
- Fixed jug on Windows (which does not support fsync on directories)
- Made Tasklets use slightly less memory

version **1.2** (Thu Aug 20 2015)
- Use HIGHEST_PROTOCOL when pickle()ing
- Add compress_numpy option to file_store
- Add register_hook_once function
- Optimize case when most (or all) tasks are already run
- Add --short option to 'jug status' and 'jug execute'
- Fix bug with dictionary order in kwargs (fix by Andreas Sorge)
- Fix ipython colors (fix by Andreas Sorge)
- Sort tasks in 'jug status'

version **1.1** (Tue Mar 3 2015)
- Python 3 compatibility fixes
- fsync(directory) in file backend
- Jug hooks (still mostly undocumented, but already enabling internal code simplification)


version **1.0** (Tue May 20 2014)
- Adapt status output to terminal width (by Alex Ford)
- Add a newline at the end of lockfiles for file backend
- Add --cache-file option to specify file for ``status --cache``


version **0.9.7** (Tue Feb 18 2014)

- Fix use of numpy subclasses
- Fix redis URL parsing
- Fix ``shell`` for newer versions of IPython
- Correctly fall back on non-sqlite ``status``
- Allow user to call set_jugdir() inside jugfile

version **0.9.6** (Tue Aug 6 2013)

- Faster decoding
- Add jug-execute script
- Add describe() function
- Add write_task_out() function

version **0.9.5** (May 27 2013)

- Added debug mode
- Even better map.reduce.map using blocked access
- Python 3 support
- Documentation improvements

version **0.9.4** (Apr 15 2013)

- Add CustomHash wrapper to set __jug_hash__
- Print traceback on import error
- Exit when no progress is made even with barrier
- Use Tasklets for better jug.mapreduce.map
- Use Ipython debugger if available (patch by Alex Ford)
- Faster --aggressive-unload
- Add currymap() function

version **0.9.3** (Dec 2 2012)

- Fix parsing of ports on redis URL (patch by Alcides Viamontes)
- Make hashing robust to different orders when using randomized hashing
  (patch by Alcides Viamontes)
- Allow regex in invalidate command (patch by Alcides Viamontes)
- Add ``--cache --clear`` suboption to status
- Allow builtin functions for tasks
- Fix status --cache`` (a general bug which seems to be triggered mainly by
  ``bvalue()`` usage).
- Fix ``CompoundTask`` (broken by earlier ``__jug_hash__`` hook introduction)
- Make ``Tasklets`` more flexible by allowing slicing with ``Tasks``
  (previously, slicing with tasks was **not** allowed)


version **0.9.2** (Nov 4 2012):

- More flexible mapreduce()/map() functions
- Make TaskGenerator pickle()able and hash()able
- Add invalidate() method to Task
- Add --keep-going option to execute
- Better help messsage

version **0.9.1** (Jun 11 2012):

- Add --locks-only option to cleanup subcommand
- Make cache file (for ``status`` subcommand) configurable
- Add ``webstatus`` subcommand
- Add bvalue() function
- Fix bug in ``shell`` subcommand (``value`` was not in global namespace)
- Improve identity()
- Fix bug in using Tasklets and --aggressive-unload
- Fix bug with Tasklets and sleep-until/check

version **0.9**:

- In the presence of a barrier(), rerun the jugfile. This makes barrier much
  easier to use.
- Add set_jugdir to public API
- Added CompoundTaskGenerator
- Support subclassing of Task
- Avoid creating directories in file backend unless it is necessary
- Add jug.mapreduce.reduce (which mimicks the builtin reduce)

For older version see ``ChangeLog`` file.
