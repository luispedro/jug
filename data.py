import pickle
from os import path
from os import mkdir
import tempfile

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
    fname = tempfile.mkstemp('.pp','jugtemp',options.datadir + '/tempfiles/')
    F = file(fname, 'w')
    pickle.dump(F,object)
    F.close()
    create_directory(dirname(outname))
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

