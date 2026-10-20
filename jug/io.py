# Copyright (C) 2013-2026, Luis Pedro Coelho <luis@luispedro.org>
# vim: set ts=4 sts=4 sw=4 expandtab smartindent:
# LICENSE: MIT
'''
Jug.IO module

- write_task_out: write out results, possibly with metadata.
- write_metadata: write out metadata on a computation.
- NoLoad: pass a Task (rather than its result) to another Task.
- print_task_summary_table: print a table of task counts (used by subcommands).
'''

from .task import TaskGenerator, Tasklet
__all__ = [
        'NoLoad',
        'write_task_out',
        'write_metadata',
        'print_task_summary_table',
        ]

class NoLoad(Tasklet):
    '''
    NoLoad can be used to decorate a Task result such that when it is passed to
    another Task, then it is passed directly (instead of passing the result).

    This is **for advanced usage**.
    '''

    def __init__(self, base):
        Tasklet.__init__(self, base, 'NoLoad')

    @property
    def t(self):
        import warnings
        warnings.warn("Using NoLoad.t is deprecated. Use the `base` accessor", DeprecationWarning)
        return self.base

    def __getitem__(self, _):
        raise NotImplementedError("You cannot slice a NoLoad object")

    def __jug_value__(self):
        return self

@TaskGenerator
def _do_write_task_out(result_value, result, oname, metadata_fname=None, metadata_format='yaml'):
    from .task import describe
    if metadata_fname is not None:
        description = describe(result.base)
        with open(metadata_fname, 'w') as output:
            if metadata_format.lower() == 'yaml':
                import yaml
                yaml.dump(description, output)
            elif metadata_format.lower() == 'json':
                import json
                json.dump(description, output)
            else:
                raise ValueError(f'jug.io.write_task_out: Unknown metadata format "{metadata_format}" [supported are "yaml" and "json"]')
    if oname is None:
        return
    try:
        import numpy as np
    except ImportError:
        np = None
    with open(oname, 'wb') as output:
        if np is not None and isinstance(result_value, np.ndarray):
            # Passing the file object (not the name) prevents numpy from
            # appending '.npy' to the output filename
            np.save(output, result_value)
        else:
            import pickle
            pickle.dump(result_value, output)

def write_task_out(result, oname, metadata_fname=None, metadata_format='yaml'):
    '''
    write_task_out(result, oname, metadata_fname=None, metadata_format='yaml')

    Write out the results of a Task to file, possibly including metadata.

    The result is written in ``.npy`` format if it is a numpy array (use
    ``numpy.load`` to read it), and pickled otherwise.

    If ``metadata_fname`` is not None, it should be the name of a file to which
    to write metadata on the computation (see ``jug.task.describe``).

    This function returns a Task (which does the writing), so it must be
    called from the jugfile (like any other task) and the output is only
    written when that task is executed.

    Parameters
    ----------
    result : a Task object
    oname : str
        The target output filename
    metadata_fname : str, optional
        If not None, metadata will be written to this file.
    metadata_format : str, optional
        What format to write data in. Currently, 'yaml' (which requires
        PyYAML) & 'json' are supported.

    Returns
    -------
    task : Task
        The task that writes the output
    '''

    return _do_write_task_out(result, NoLoad(result), oname, metadata_fname, metadata_format)

def write_metadata(result, metadata_fname, metadata_format='yaml'):
    '''
    write_metadata(result, metadata_fname, metadata_format='yaml')

    Write out the metadata on a Task out.

    This function returns a Task (which does the writing), so it must be
    called from the jugfile (like any other task) and the output is only
    written when that task is executed.

    Parameters
    ----------
    result : a Task object
    metadata_fname : str
        metadata will be written to this file.
    metadata_format : str, optional
        What format to write data in. Currently, 'yaml' (which requires
        PyYAML) & 'json' are supported.

    Returns
    -------
    task : Task
        The task that writes the metadata
    '''

    return _do_write_task_out(result, NoLoad(result), None, metadata_fname, metadata_format)

# Console status table output

def print_task_summary_table(options, groups):
    """Print task summary table given tasks groups.

    groups - [(group_title, {task_name: count})] grouped summary of tasks.
    """
    if options.short:
        for name,gv in groups:
            options.print_out(f"{name}:  {sum(gv.values())} tasks")
        n = sum(sum(gv.values()) for _, gv in groups)
        options.print_out(f"** Total: {n} tasks.")
        return

    import textwrap
    num_groups = len(groups)

    names = set()
    for _, group_data in groups:
        names.update(group_data.keys())

    termsize, termheight = get_terminal_size()
    name_width = termsize - (num_groups * 12) - 2
    if name_width <= 8: # too short. Output will look ugly in any case
        name_width = 12

    def format_line(cells, name):
        return ''.join(f'{c!s:>12}' for c in cells) + f'  {name!s:<{name_width}}'

    format_size = (12 * num_groups) + 2 + name_width

    options.print_out(format_line([g for g, _ in groups], "Task name"))
    options.print_out('-' * format_size)

    for n in sorted(names):
        name_lines = textwrap.wrap(n, width=name_width - 4)
        options.print_out(format_line([g[n] for _, g in groups], name_lines[0] if name_lines else ''))

        for name_extension in name_lines[1:]:
            options.print_out(format_line([""] * num_groups, (" " * 4) + name_extension))

    options.print_out('.' * format_size)
    options.print_out(format_line([sum(g.values()) for _, g in groups], "Total"))
    options.print_out()

def get_terminal_size():
    """ get_terminal_size()
     - get width and height of console, as a tuple ``(columns, lines)``
     - uses ``shutil.get_terminal_size()``, so the ``COLUMNS`` and ``LINES``
       environment variables take precedence
     - returns ``(80, 25)`` if the size cannot be determined
    """
    import shutil
    columns, lines = shutil.get_terminal_size((80, 25))
    return columns, lines
