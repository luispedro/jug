# -*- coding: utf-8 -*-
# Copyright (C) 2013, Luis Pedro Coelho <luis@luispedro.org>
# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
# LICENSE: MIT
'''
Jug.IO module

- write_task_out: write out results, possibly with metadata.
'''

from .task import TaskGenerator, Task

class NoLoad(object):
    def __init__(self, t):
        self.t = t

    def __jug_hash__(self):
        from .hash import hash_one
        return hash_one(['NoLoad', self.t.hash()])

    def __jug_value__(self):
        return self

@TaskGenerator
def _do_write_task_out(result_value, result, oname, metadata_fname=None, metadata_format='yaml'):
    from .task import describe
    if metadata_fname is not None:
        description = describe(result.t)
        if metadata_format.lower() == 'yaml':
            import yaml
            yaml.dump(description, open(metadata_fname, 'w'))
        elif metadata_format.lower() == 'json':
            import json
            json.dump(description, open(metadata_fname, 'w'))
        else:
            raise ValueError('jug.io.write_task_out: Unknown metadata format "{}" [supported are "yaml" and "json"]'.format(metadata_format))
    try:
        import numpy as np
        if isinstance(result_value, np.ndarray):
            np.save(result, oname)
            return
    except:
        pass
    if oname is not None:
        import pickle
        pickle.dump(result_value, open(oname, 'wb'))

def write_task_out(result, oname, metadata_fname=None, metadata_format='yaml'):
    '''
    write_task_out(result, oname, metadata_fname=None, metadata_format='yaml')

    Write out the results of a Task to file, possibly including metadata.

    If ``metadata_fname`` is not None, it should be the name of a file to which
    to write metadata on the computation.

    Parameters
    ----------
    result: a Task object
    oname : str
        The target output filename
    metadata_fname : str, optional
        If not None, metadata will be written to this file.
    metadata_format : str, optional
        What format to write data in. Currently, 'yaml' & 'json' are supported.
    '''

    return _do_write_task_out(result, NoLoad(result), oname, metadata_fname, metadata_format)

def write_metadata(result, metadata_fname, metadata_format='yaml'):
    '''
    write_metadata(result, metadata_fname, metadata_format='yaml')

    Write out the metadata on a Task out.


    Parameters
    ----------
    result: a Task object
    metadata_fname : str
        metadata will be written to this file.
    metadata_format : str, optional
        What format to write data in. Currently, 'yaml' & 'json' are supported.
    '''

    return _do_write_task_out(result, NoLoad(result), None, metadata_fname, metadata_format)

