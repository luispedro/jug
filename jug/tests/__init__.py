def run():
    import pytest
    from os import path
    currentdir = path.dirname(__file__)
    updir = path.join(currentdir, '..')
    pytest.main([updir])
