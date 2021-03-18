import jug.options

from io import StringIO
from pytest import raises

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

    with raises(AttributeError):
        first.two

    with raises(AttributeError):
        second.three

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
    assert parsed.execute_wait_cycle_time == 23
    assert not parsed.aggressive_unload

def test_copy():
    parsed = jug.options.parse(
        ["execute", "--pdb"],
        StringIO(_options_file))
    copy = parsed.copy()
    assert parsed.pdb
    assert not parsed.aggressive_unload

def test_sys_argv():
    from sys import argv
    parsed = jug.options.parse(
        ["execute", "--pdb"])
    assert argv == ['jugfile.py']

    parsed = jug.options.parse(
        ["execute", 'jugfile.py'])
    assert argv == ['jugfile.py']

    parsed = jug.options.parse(
        ["execute", 'jugfile.py', '--', 'arg'])
    assert argv == ['jugfile.py', 'arg']

    parsed = jug.options.parse(
        ["execute", 'jugfile.py', 'arg'])
    assert argv == ['jugfile.py', 'arg']

    parsed = jug.options.parse(
        ["execute", 'jugfile.py', 'arg', '--', '--hello'])
    assert argv == ['jugfile.py', 'arg', '--hello']

def test_bool():
    from jug.options import _str_to_bool
    assert not _str_to_bool("")
    assert not _str_to_bool("0")
    assert not _str_to_bool("false")
    assert not _str_to_bool("FALSE")
    assert not _str_to_bool("off")
    assert _str_to_bool("on")
    assert _str_to_bool("true")
    assert _str_to_bool("1")
