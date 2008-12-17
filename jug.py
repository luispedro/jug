from store import create_directories
import options
import task

def parse_jugfile():
    import jugfile

def print_tasks():
    for i,t in enumerate(task.alltasks):
        print 'Task %s: %s' % (i,t.name)

def execute_tasks():
    tasks = task.alltasks
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

