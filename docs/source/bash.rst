Bash Shell Helpers
==================

Who is this document for?
-------------------------

This is for someone using Jug on a compute cluster where there is a dedicated
head node. These scripts help launch, monitor, and terminate jug on all of the
compute nodes. They should be used with caution, as they are not heavily tested
and may need to be modified for your setup.

Terms used in this document
---------------------------

head node
  Computer that does not perform heavy computation locally. Instead it is in
  charge of managing and monitoring jug on other computers
compute node/client
  Interchangable terms for this doc. Computers that are connected to the head
  node (typically via an SSH connection) and will be performing computation.
jug instance
  A single jug process, typically running on a compute node

What scripts are available?
---------------------------

jug
  The normal jug executable
jugrun
  Starts jug executables on non-head machines. The number of executables
  started on each client machine should be configured to match the hardware of
  each client machine e.g. for 12 hardware threads, it may be reasonable to run
  10 instances of jug
jugstatus
  Monitors jug execution by occasionally calling 'jug status'
jughalt
  Stops all jug executors on all compute node computers
juglog
  Outputs a log of jug run/halt/stop commands
jugoutput
  If your jug tasks print to stdout or stderr, this collects all of that
  content from each remote machine and prints it out.  Note that this command
  will likely need to be configured for your computer

Installing these scripts
------------------------

You need to

1. create an alias for all of the jug* commands in your ``.bash_profile``
2. create a ``workers.iplist`` file
3. create a ``.waitonjug`` executable
4. create a `run_workers.sh`` script.

All of these are covered here. Also note, these scripts require ``pssh``

**Creating command aliases**

.. code-block:: bash

  local ~$ ssh myserver
  myserver ~$ nano .bash_profile
  # Nano opens a text editor and I paste the following at
  # the top (minus the hash signs)
  #
  #alias pssh='pssh -i -h workers.iplist '
  #alias jugstatus='watch -n 10 -d jug status --cache benchmark_jug.py'
  #alias jugrun='echo "`date`: Start" >> .juglog; screen -d -m -S jugwatcher sh ~/.waitonjug; pssh screen -d -S jug -m sh run_workers.sh'
  #alias jugoutput='pssh cat /mnt/localhd/.jug*'
  #alias jughalt='echo "`date`: Halt ">> .juglog; screen -S jugwatcher -X quit;  pssh pkill jug;'
  #alias juglog='cat ~/.juglog'
  #
  # Now we need to tell the server to 'reload' .bash_profile 
  myserver ~$ source .bash_profile
  # Now type 'jug' and hit tab a few times to see the following
  myserver ~$ jug
  jug    jughalt    juglog     jugoutput  jugrun     jugstatus  

**Creating workers.iplist**

This is pretty simple, just create a file called workers.iplist and insert
something like this to identify all of your compute nodes::

  10.0.2.2
  10.0.2.4
  10.0.2.5
  10.0.2.6
  10.0.2.7


**Creating .waitonjug executable**
Create a new file called .waitonjug and insert the following

.. code-block:: bash

 #!/bin/sh

 echo "Waiting..."
 jug sleep-until benchmark_jug.py
 echo "`date`: Completed" >> ~/.juglog
 echo "Complete, returning"

Then save the file and make it executable by typing ``chmod a+x .waitonjug``.

**Creating run_workers.sh**

Create a new file called ``run_workers.sh`` and paste the following, but *be
sure to modify the script!* There are a few things to modify: the number of
workers, the name of your jug python code, and where to send the output. 

Number of Workers: This script assumes that all compute nodes can run the same
number of jug processes without being overloaded. I would generally recommend
setting the number of jug processes to be slightly lower than the total number
of hardware threads your compute node can support. For example, each of my
compute nodes has 12 hardware threads (6 cores, 2 threads each), so I've set to
run 10 jug processes per compute node.

Name of script: Below, the name of my jug script is benchmark_jug.py.  Yours is
likely different, so please update

Output redirection: I'm outputing stdout and stderr to ``/mnt/localhd``. If your
jug tasks do not use stdout or stderr, then perhaps just do ``jug execute
<my_jug>.py &> /dev/null &`` to redirect everything to /dev/null. If you
actually want output, make sure that the directory you're using for output (in
my case /mnt/localhd) is NOT shared by NFS, or your workers on different
machines will be overwriting the same file. Or be a boss and upgrade this
script to read in the hostname ;-)

.. code-block:: bash

    #!/bin/sh

    JUG_PROCESSES_PER_WORKER=10

    rm /mnt/localhd/.jug*
    for i in {1..${JUG_PROCESSES_PER_WORKER}}
    do
        jug execute benchmark_jug.py > /mnt/localhd/.jug$i.out 2> /mnt/localhd/.jug$i.err &
    done
    wait

After creating run_workers.sh, don't forget to make it executable using ``chmod
a+x run_workers.sh``

Understanding the scripts
-------------------------

**pssh**
Pssh is required for all of these scripts. It allows me to broadcast one
command to multiple computers and receive the reply. It makes an ssh connection
to each computer, executes the command, and aggregates the replies. Pssh is
what reads in the ``workers.iplist``

**jugstatus**
This uses the watch command to call 'jug status' every ten seconds

**jugrun**
*This will likely need minor modifications for your use. See the
'installation' section above.*
This first posts log entry, then sets up what I call a 'watcher',
which is a tiny executable that runs in the background on the host
computer (actually, it runs inside of a detached screen session)
and waits on jug to complete the 'jugrun' command. If you peek
inside the ``.waitonjug`` code you will see that this 'wait on jug' logic is
nothing more than 1) use jug's sleep-until 2) create log message indicating
that the job is complete.

The actual business logic of jugrun is to use pssh to tell each compute node to
execute the ``run_workers.sh`` script. The run_workers script runs on each
compute node, and launches all the instances of jug. It also waits on them to
be terminated (e.g. killed by either jug completing or a call to jughalt). It
waits because if the script terminates before the child processes
(e.g. the instances of jug) then bad things will happen

**jughalt**
Creates a log message about halting, terminates the .waitonjug detached screen
so that we don't have anyone waiting for the job to complete, and then uses
pssh to issue a command to all compute node to kill all jug processes. The
pkill command is used to automatically find and kill and processes names *jug*.
Once the jug processes die then the run_worker.sh scripts will automatically
terminate

**juglog**
Outputs the contents of the log file from the run/halt/complete.  Simple file,
can be used with other options e.g. ``tail -f ~/.juglog``

**jugoutput**
*This will likely need to be modified for your use.* In my setup, all files
under /home/myuser/ are shared via NFS. This means that any output files placed
in my home directory can have problems as multiple jug processes are writing to
the same file and NFS is trying to share that file across multiple machines. My
solution was to output jug-process-specific files into a directory that is not
shared by NFS, specifically /mnt/localhd on each computer. The jugoutput
command uses pssh to collect all of these log files and print them to me on the
head node. Useful for monitoring progress of individual jug tasks e.g. a
particularly long running method call.
