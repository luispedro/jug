from data import create_directories
import jugfileparser
import scheduler
import options

def parse_jugfile():
    jugfileparser.parse('jugfile.py')

def print_tasks():
    for i,t in enumerate(scheduler.tasks):
        print 'Task %s: %s' % (i,t.name)

def execute_tasks():
    tasks = scheduler.tasks
    while tasks:
        ready = [t for t in tasks if t.can_run()]
        if len(ready) == 0:
            print 'No tasks can be run!'
            return
        for t in ready:
            if t.can_load():
                t.load()
            else:
                t.run()
            tasks.remove(t)

def init():
    create_directories(options.datadir + '/tempfiles')

def main():
    init()
    parse_jugfile()
    print_tasks()
    execute_tasks()
    print_tasks()

if __name__ == '__main__':
    main()

