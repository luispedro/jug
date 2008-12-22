jugdir = 'jugdata'
tempdir = jugdir + '/tempfiles/'
lockdir = jugdir + '/locks/'
jugfile = 'jugfile.py'
cmd = None
shuffle = False

def parse():
    '''
    options.parse()

    Parse the command line options and set the option variables.
    '''
    import optparse
    parser = optparse.OptionParser()
    parser.add_option('--shuffle',action='store',type='int',dest='shuffle',default=False)
    options,args = parser.parse_args()
    if not args:
        import sys
        print '''
python %s COMMAND OPTIONS...

Possible commands:
    * execute
        Execute tasks
    * stats:
        Print stats

Options
    --shuffle[=N]
        Shuffle the task order using N as the seed (default: 0)
''' % sys.argv[0]
        sys.exit(1)
    global cmd, shuffle
    cmd = args[0]
    if options.shuffle is not False:
        import random
        random.seed(options.shuffle)
        shuffle = True



