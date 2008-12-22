import pickle
import os
from os import path, mkdir, fdopen
from os.path import dirname
import tempfile
import options

def create_directories(dname):
    '''
    create_directories(dname)

    Recursively create directories.
    '''
    if dname.endswith('/'): dname = dname[:-1]
    head, tail = path.split(dname)
    if head: create_directories(head)
    if not path.exists(dname): mkdir(dname)

def atomic_pickle_dump(object, outname):
    '''
    atomic_pickle_dump(outname, object)

    Performs the same as

    pickle.dump(object, file(outname,'w')

    but does it in a way that is guaranteed to be atomic even over NFS.
    '''
    # Rename is atomic in NFS, but we need to create the temporary file in
    # the same directory as the result.
    #
    # Don't mess unless you know what you are doing!
    fd, fname = tempfile.mkstemp('.pp','jugtemp',options.tempdir)
    F = fdopen(fd,'w')
    pickle.dump(object,F)
    F.close()
    create_directories(dirname(outname))
    os.rename(fname,outname)

def obj2fname(obj):
    '''
    fname = obj2fname(obj)

    Returns the filename used to save the object obj
    '''
    M = md5.md5()
    S = pickle.dumps(func,args)
    M.update(S)
    D = M.hexdigest()
    return D[0] + '/' + D[1] + '/' + D[2:] + '.pp'

