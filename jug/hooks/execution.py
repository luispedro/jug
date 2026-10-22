#!/usr/bin/python
# Copyright (C) 2014-2026, Luis Pedro Coelho <luis@luispedro.org>
from time import time

def _mean(vs):
    return sum(vs)/float(len(vs))

class TimeTasks:
    '''
    Collects the execution time of each task (grouped by task name)

    Used by ``register_time_tasks``.
    '''
    def __init__(self):
        from collections import defaultdict
        self.times = defaultdict(list)

    def start(self, t):
        self.start_time = time()

    def stop(self, t):
        ellapsed = time() - self.start_time
        self.times[t.name].append(ellapsed)

    def print_summary(self):
        print("TIMES")
        print("-----\n")
        for k,v in self.times.items():
            print(f"{k:20} {_mean(v):.2f}s ({len(v)} tasks)")



def register_time_tasks():
    '''register_time_tasks()

    Time each task and print a summary at the end of ``jug execute``

    Call this function in your jugfile to trigger printing a timing summary at
    the end of jug execute::

        from jug.hooks.execution import register_time_tasks
        register_time_tasks()

    '''
    from . import register_hook_once
    # The jugfile may be imported several times (e.g., with barriers), so
    # only register the hooks the first time
    tt = TimeTasks()
    register_hook_once('execute.task-pre-execute', 'register_time_tasks', tt.start)
    register_hook_once('execute.task-executed1', 'register_time_tasks', tt.stop)
    register_hook_once('execute.finished_post_status', 'register_time_tasks', tt.print_summary)
