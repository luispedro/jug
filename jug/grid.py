# -*- coding: utf-8 -*-

from .jug import main as jug_main


def grid_jug(jug_args, jug_nworkers=4, name='gridjug', **kwargs):
    """
    A light-weight wrapper to run Jug with GridMap on a Grid Engine cluster

    From their own description, GridMap is a package that allows to easily
    create jobs on a Grid Engine powered cluster directly from Python.
    This wrapper lets GridMap simply spawn several jug-execute workers on a
    Grid Engine cluster.
    Thus we have the benefit of programmatic (reproducible) execution of Jug
    processes.
    Furthermore, GridMap adds a convenient monitoring and reporting layer.
    Under the hood, of course, Jug keeps doing the actual work.

    Parameters
    ----------

    jug_args : list
        Jug command-line arguments.
        Note that ``'execute'`` is already included.
        The command line is roughly equivalent to:

            'jug execute ' + ' '.join(jug_args)

    jug_nworkers : int, optional
        number of Grid Engine tasks to start
        (i.e. number of times 'jug execute' is run)

    name : str, optional
        base name of the Grid Engine task

    **kwargs : keyword-dict, optional
        additional options passed through to gridmap.grid_map

    See Also
    --------

    `GridMap <https://github.com/pygridtools/gridmap>`_

    `gridmap.grid_map <http://gridmap.readthedocs.org/en/latest/gridmap.html#gridmap.job.grid_map>`_
    """

    from gridmap.job import grid_map

    jug_argv = ['jug', 'execute']
    jug_argv.extend(jug_args)

    # function arguments for grid_map
    # note that there are multiple lists here
    # the innermost list is the list of arguments to jug
    # this needs to stay a list as jug.main accepts a single argument argv
    # which is a list of parameters for jug
    # https://github.com/luispedro/jug/blob/15a7043f6f859810b5e6af1638176d1a9cb70f5a/jug/jug.py#L405
    #
    # we wrap this inner list in a wrapper list [jug_argv] that gridmap
    # "expands" to its single item jug_argv upon calling the jug.main function,
    # with that very single item jug_argv as the single argument
    # https://github.com/pygridtools/gridmap/blob/master/gridmap/job.py#L225
    #
    # finally, the wrapper list [jug_arvg] is contained in the outer list
    # [[jug_argv]]. The outer list is multiplied by the number of workers to
    # create an outer list of that many items, each of which is the wrapped
    # list [jug_argv] to supplied to each of the worker jobs
    # https://github.com/pygridtools/gridmap/blob/master/gridmap/job.py#L929
    # https://github.com/pygridtools/gridmap/blob/master/gridmap/job.py#L933
    #
    args_list = jug_nworkers * [[jug_argv]]

    return grid_map(
        f=_jug_main,
        args_list=args_list,
        name=name,
        **kwargs
    )


def _jug_main(*args, **kwargs):
    """
    wrapper function for pickle
    """
    return jug_main(*args, **kwargs)
