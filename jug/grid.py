# -*- coding: utf-8 -*-

import jug.jug


def grid_jug(jug_args, jug_nworkers=4, name='gridjug', **kwargs):
    """
    A light-weight wrapper to run jug with gridmap on a Grid Engine cluster
    """

    from gridmap.job import grid_map
    
    jug_argv = ['dummy_script_name_not_parsed_by_jug', 'execute']
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
    return jug.jug.main(*args, **kwargs)
