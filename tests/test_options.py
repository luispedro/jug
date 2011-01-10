import jug.options
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
