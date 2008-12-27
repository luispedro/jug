from collections import defaultdict
from time import sleep
from store import create_directories
import sys
import random
import options
import task
import jugfile

def do_print():
    task_counts = defaultdict(int)
    for t in task.alltasks:
        task_counts[t.name] += 1
    for tnc in task_counts.items():
        print 'Task %s: %s' % tnc

task_names = set(t.name for t in task.alltasks)
tasks = task.alltasks
def execute():
    '''
    execute_tasks()

    Implement 'execute' command
    '''
    tasks_executed = defaultdict(int)
    tasks_loaded = defaultdict(int)
    if options.shuffle:
        random.shuffle(tasks)
    while tasks:
        ready = [t for t in tasks if t.can_run()]
        any_run = False
        if len(ready) == 0:
            print 'No tasks can be run!'
            return
        for t in ready:
            if t.can_load():
                t.load()
                tasks_loaded[t.name] += 1
            else:
                if not t.lock(): continue
                try:
                    any_run = True
                    t.run()
                    tasks_executed[t.name] += 1
                finally:
                    t.unlock()
            tasks.remove(t)
        if not any_run:
            sleep(4)

    print '%-20s%12s%12s' %('Task name','Executed','Loaded')
    print ('-' * (20+12+12))
    for t in task_names:
        print '%-20s%12s%12s' % (t,tasks_executed[t],tasks_loaded[t])

def status():
    tasks_ready = defaultdict(int)
    tasks_finished = defaultdict(int)
    tasks_running = defaultdict(int)
    tasks_waiting = defaultdict(int)
    changed = True
    while changed:
        changed = False
        for t in tasks:
            if not t.finished and t.can_load():
                tasks_finished[t.name] += 1
                t.load()
                changed = True
    for t in tasks:
        if not t.finished:
            if t.can_run():
                if t.is_locked():
                    tasks_running[t.name] += 1
                else:
                    tasks_ready[t.name] += 1
            else:
                tasks_waiting[t.name] += 1

    print '%-20s%12s%12s%12s%12s' %('Task name','Waiting','Ready','Finished','Running')
    print ('-' * (20+12+12+12+12))
    for t in task_names:
        print '%-20s%12s%12s%12s%12s' % (t,tasks_waiting[t],tasks_ready[t],tasks_finished[t],tasks_running[t])
    print

def init():
    create_directories(options.tempdir)

def main():
    options.parse()
    init()
    if options.cmd == 'execute':
        execute()
    elif options.cmd == 'count':
        do_print()
    elif options.cmd == 'status':
        status()
    else:
        print >>sys.stderr, 'Unknown command: \'%s\'' % options.cmd

if __name__ == '__main__':
    main()

