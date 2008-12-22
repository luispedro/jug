import options
from os import path

def _fullname(name):
    return path.join(options.jugdir,name[0],name[1],name[2:])

def get(name):
    '''
    get(name)

    Create a lock for name in an NFS compatible way.
    '''
    fullname = _fullname(name)
    if exists(fullname): return False
    create_directories(fullname)
    fd, fname = tempfile.mkstemp('.lock','juglock',options.lockdir)
    F = fdopen(fd,'w')
    print >>F, 'Lock', os.getpid()
    F.close()
    os.rename(fname, fullname)
    return True

def release(name):
    '''
    release(name)

    Removes lock
    '''
    os.unlink(_fullname(name))

