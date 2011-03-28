def run():
    import nose
    from os import path
    currentdir = path.dirname(__file__)
    updir = path.join(currentdir, '..')
    nose.run('jug', argv=['', '--exe', '-w', updir])
