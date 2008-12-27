jugdir = 'jugdata'
tempdir = jugdir + '/tempfiles/'
lockdir = jugdir + '/locks/'
jugfile = 'jugfile.py'
cmd = None
shuffle = False

_Commands = ('execute','status','stats','cleanup','count')

def usage():
    import sys
    print '''
python %s COMMAND OPTIONS...

Possible commands:
* execute
    Execute tasks
* status:
    Print status
* counts:
    Simply count tasks
* cleanup:
    Cleanup [Not implemented]
* stats
    Print statistics [Not implemented]

Options
--shuffle[=N]
    Shuffle the task order using N as the seed (default: 0)
''' % sys.argv[0]
    sys.exit(1)
def parse():
    '''
    options.parse()

    Parse the command line options and set the option variables.
    '''
    import optparse
    global cmd, shuffle
    parser = optparse.OptionParser()
    parser.add_option('--shuffle',action='store',type='int',dest='shuffle',default=False)
    options,args = parser.parse_args()
    if not args:
        usage()
        return
    cmd = args[0]
    if cmd not in _Commands:
        usage()
        return

    if options.shuffle is not False:
        import random
        random.seed(options.shuffle)
        shuffle = True



