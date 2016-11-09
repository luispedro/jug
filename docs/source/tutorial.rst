============
Jug Tutorial
============

What is jug?
------------

Jug is a simple way to write easily parallelisable programs in Python. It also
handles intermediate results for you.

Example
-------

This is a simple worked-through example which illustrates what jug does.

Problem
~~~~~~~

Assume that I want to do the following to a collection of images:

1. for each image, compute some features
2. cluster these features using k-means. In order to find out the number of
   clusters, I try several values and pick the best result. For each value of
   k, because of the random initialisation, I run the clustering 10 times.

I could write the following simple code::

    imgs = glob('*.png')
    features = [computefeatures(img,parameter=2) for img in imgs]
    clusters = []
    bics = []
    for k in range(2, 200):
        for repeat in range(10):
            clusters.append(kmeans(features,k=k,random_seed=repeat))
            bics.append(compute_bic(clusters[-1]))
    Nr_clusters = argmin(bics) // 10

Very simple and solves the problem. However, if I want to take advantage of the
obvious parallelisation of the problem, then I need to write much more
complicated code. My traditional approach is to break this down into smaller
scripts. I'd have one to compute features for some images, I'd have another to
merge all the results together and do some of the clustering, and, finally, one
to merge all the results of the different clusterings. These would need to be
called with different parameters to explore different areas of the parameter
space, so I'd have a couple of scripts just for calling the main computation
scripts. Intermediate results would be saved and loaded by the different
processes.

This has several problems. The biggest are

1. The need to manage intermediate files. These are normally files with long
   names like *features_for_img_0_with_parameter_P.pp*.
2. The code gets much more complex.

There are minor issues with having to issue several jobs (and having the
cluster be idle in the meanwhile), or deciding on how to partition the jobs so
that they take roughly the same amount of time, but the two above are the main
ones.

Jug solves all these problems!

Tasks
~~~~~

The main unit of jug is a Task. Any function can be used to generate a Task. A
Task can depend on the results of other Tasks.

The original idea for jug was a Makefile-like environment for declaring Tasks.
I have moved beyond that, but it might help you think about what Tasks are.

You create a Task by giving it a function which performs the work and its
arguments. The arguments can be either literal values or other tasks (in which
case, the function will be called with the *result* of those tasks!). Jug also
understands lists of tasks and dictionaries with tasks. For example, the
following code declares the necessary tasks for our problem::

    imgs = glob('*.png')
    feature_tasks = [Task(computefeatures,img,parameter=2) for img in imgs]
    cluster_tasks = []
    bic_tasks = []
    for k in range(2, 200):
        for repeat in range(10):
            cluster_tasks.append(Task(kmeans,feature_tasks,k=k,random_seed=repeat))
            bic_tasks.append(Task(compute_bic,cluster_tasks[-1]))
    Nr_clusters = Task(argmin,bic_tasks)

Task Generators
~~~~~~~~~~~~~~~

In the code above, there is a lot of code of the form *Task(function,args)*, so
maybe it should read *function(args)*.  A simple helper function aids this
process::

    from jug import TaskGenerator

    computefeatures = TaskGenerator(computefeatures)
    kmeans = TaskGenerator(kmeans)
    compute_bic = TaskGenerator(compute_bic)

    @TaskGenerator
    def Nr_Clusters(bics):
        return argmin(bics) // 10

    imgs = glob('*.png')
    features = [computefeatures(img,parameter=2) for img in imgs]
    clusters = []
    bics = []
    for k in range(2, 200):
        for repeat in range(10):
            clusters.append(kmeans(features,k=k,random_seed=repeat))
            bics.append(compute_bic(clusters[-1]))
    Nr_clusters(bics)

You can see that this code is almost identical to our original sequential code,
except for the decorators at the top and the fact that *Nr_clusters* is now a
function (actually a TaskGenerator, look at the use of a decorators).

This file is called the jugfile (you should name it *jugfile.py* on the
filesystem) and specifies your problem.

Jug
~~~

So far, we have achieved seemingly little. We have turned a simple piece of
sequential code into something that generates Task objects, but does not
actually perform any work. The final piece is jug. Jug takes these Task objects
and runs them. Its main loop is basically

::

    while len(tasks) > 0:
        for t in tasks:
            if can_run(t): # ensures that all dependencies have been run
                if need_to_run(t) and not is_running(t):
                    t.run()
                tasks.remove(t)

If you run jug on the script above, you will simply have reproduced the
original code with the added benefit of having all the intermediate results
saved.

The interesting is what happens when you run several instances of jug at the
same time. They will start running Tasks, but each instance will run its own
tasks. This allows you to take advantage of multiple processors in a way that
keeps the processors all occupied as long as there is work to be done, handles
the implicit dependencies, and passes functions the right values. Note also
that, unlike more traditional parallel processing frameworks (like MPI), jug
has no problems with the number of participating processors varying throughout
the job.

Behind the scenes, jug is using the filesystem to both save intermediate
results (which get passed around) and to lock running tasks so that each task
is only run once (the actual main loop is thus a bit more complex than shown
above).

Intermediate and Final Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can obtain the final results of your computation by setting up a task that
saves them to disk and loading them from there. If the results of your
computation are simple enough, this might be the simplest way.

Another way, which is also the way to access the intermediate results if you
want them, is to run the jug script and then access the *result* property of
the Task object. For example,

::

    img = glob('*.png')
    features = [computefeatures(img,parameter=2) for img in imgs]
    ...
    
    feature_values = [feat.result for feat in features]

If the values are not accessible, this raises an exception.

Advantages
----------

jug is an attempt to get something that works in the setting that I have found
myself in: code that is *embarrassingly parallel* with a couple of points where
all the results of previous processing are merged, often in a simple way.  It
is also a way for me to manage either the explosion of temporary files that
plagued my code and the brittleness of making sure that all results from
separate processors are merged correctly in my *ad hoc* scripts.

Limitations
-----------

This is not an attempt to replace libraries such as MPI in any way. For code
that has many more merge points (i.e., code locations which all threads must
reach at the same time), this won't do. It also won't do if the individual
tasks are so small that the over-head of managing them swamps out the
performance gains of parallelisation. In my code, most of the times, each task
takes 20 seconds to a few minutes. Just enough to make the managing time
irrelevant, but fast enough that the main job can be broken into thousands of
tiny pieces. As a rule of thumb, tasks that last less than 5 seconds should
probably be merged together.

The system makes it too easy to save all intermediate results and run out of
disk space.

This is still Python, not a true parallel programming language. The abstraction
will sometimes leak through, for example, if you try to pass a Task to a
function which expects a real value. Recall how we had to re-write the line
*Nr_clusters = argmin(bics) // 10* above.

