import options
import os
from os import path
from os.path import exists
from store import create_directories
import tempfile

def _fullname(name):
    return path.join(options.lockdir,name[0],name[1],name[2:]+'.lock')

def get(name):
    '''
    get(name)

    Create a lock for name in an NFS compatible way.
    '''
    fullname = _fullname(name)
    if exists(fullname): return False
    create_directories(path.dirname(fullname))
    fd, fname = tempfile.mkstemp('.lock','juglock',options.lockdir)
    F = os.fdopen(fd,'w')
    print >>F, 'Lock', os.getpid()
    F.close()
    if exists(fullname):
        os.unlink(fname)
    else:
        os.rename(fname, fullname)
    return True

def release(name):
    '''
    release(name)

    Removes lock
    '''
    os.unlink(_fullname(name))

