from os import system
import sys

def startjob(cmd):
    system(cmd + "&")
    
if __name__ == '__main__':
    if len(sys.argv) == 1:
        print '''
python %s NR

Start NR instances of jug.py execute
'''  % sys.argv[0]
        sys.exit(0)
    N=int(sys.argv[1])
    for n in xrange(N):
        startjob('python jug.py execute --shuffle=%s' % n)

