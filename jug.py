from data import create_directories
import jugfileparser
import scheduler
import options

def parse_jugfile():
    jugfileparser.parse('jugfile.py')

def print_tasks():
    for i,t in enumerate(scheduler.tasks):
        print 'Task %s: %s' % (i,t.name)

def init():
    create_directories(options.datadir + '/tempfiles')

def main():
    init()
    parse_jugfile()
    print_tasks()

if __name__ == '__main__':
    main()

