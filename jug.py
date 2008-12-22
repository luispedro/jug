from collections import defaultdict
from time import sleep
from store import create_directories
import sys
import random
import options
import task
import jugfile

def print_tasks():
    task_counts = defaultdict(int)
    for t in task.alltasks:
        task_counts[t.name] += 1
    for tnc in task_counts.items():
        print 'Task %s: %s' % tnc

task_names = set(t.name for t in task.alltasks)
tasks_executed = defaultdict(int)
tasks_loaded = defaultdict(int)
def execute_tasks():
    '''
    execute_tasks()

    Implement 'execute' command
    '''
    tasks = task.alltasks
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

def print_fstats():
    print '%-20s%12s%12s' %('Task name','Executed','Loaded')
    print ('-' * (20+12+12))
    for t in task_names:
        print '%-20s%12s%12s' % (t,tasks_executed[t],tasks_loaded[t])

def init():
    create_directories(options.tempdir)

def main():
    options.parse()
    init()
    if options.cmd == 'execute':
        execute_tasks()
    else:
        print >>sys.stderr, 'Unknown command: \'%s\'' % options.cmd
    print_fstats()

if __name__ == '__main__':
    main()

