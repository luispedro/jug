import jug.options

from StringIO import StringIO
from nose.tools import raises

def test_chaining():
    first = jug.options.Options(None)
    second = jug.options.Options(first)
    third = jug.options.Options(second)

    first.one = 'one'
    second.two = 'two'
    third.three = 'three'

    assert third.one == 'one'
    first.one = 1
    assert third.one == 1
    assert second.one == 1
    assert second.two == 'two'
    assert third.three == 'three'
    @raises(KeyError)
    def not_present_key(obj, key):
        return obj.key

    yield not_present_key, first, 'two'
    yield not_present_key, second, 'three'

_options_file = '''
[main]
jugfile=myjugfile.py

[execute]
wait-cycle-time=23
'''

def test_parse():
    parsed = jug.options.parse(
        ["execute", "--pdb"],
        StringIO(_options_file))

    assert parsed.jugfile == 'myjugfile.py'
    assert parsed.pdb
    assert parsed.execute_wait_cycle_time_secs == 23
    assert not parsed.aggressive_unload

