from nose.tools import with_setup

def simple_execute():
    from jug.jug import execution_loop
    from jug.task import alltasks
    from jug.options import default_options
    execution_loop(alltasks, default_options)

def remove_files(flist, dlist=[]):
    def teardown():
        from os import unlink
        for f in flist:
            try:
                unlink(f)
            except:
                pass
        from shutil import rmtree
        for dir in dlist:
            try:
                rmtree(dir)
            except:
                pass
    return with_setup(None, teardown)
