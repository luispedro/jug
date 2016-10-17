#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (C) 2014, Luis Pedro Coelho <luis@luispedro.org>
from time import time

def _mean(vs):
    return sum(vs)/float(len(vs))

class TimeTasks(object):
    def __init__(self):
        from collections import defaultdict
        self.times = defaultdict(list)

    def start(self, t):
        self.start = time()

    def stop(self, t):
        ellapsed = time() - self.start
        self.times[t.name].append(ellapsed)

    def print_summary(self):
        print("TIMES")
        print("-----\n")
        for k,v in self.times.items():
            print("{:20} {:.2}s ({} tasks)".format(k, _mean(v), len(v)))



def register_time_tasks():
    '''register_time_tasks()

    Call this function in your jugfile to trigger printing a timing summary at
    the end of jug execute::


        from jug.hooks.execution import register_time_tasks
        register_time_tasks()

    '''
    from . import register_hook
    tt = TimeTasks()
    register_hook('execute.task-pre-execute', tt.start)
    register_hook('execute.task-executed1', tt.stop)
    register_hook('execute.finished_post_status', tt.print_summary)
 
