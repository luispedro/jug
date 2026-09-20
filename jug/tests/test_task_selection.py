import pytest

from jug.options import parse
from jug.utils import (prepare_matcher_from_options, prepare_name_matcher,
                       prepare_task_matcher)


def test_name_full():
    m = prepare_name_matcher('jugfile.function')
    assert m('jugfile.function')
    assert not m('jugfile.function_other')
    assert not m('jugfile.other_function')
    assert not m('xjugfile.function')


def test_name_bare():
    m = prepare_name_matcher('function')
    assert m('jugfile.function')
    assert m('pkg.mod.function')
    assert not m('jugfile.function_other')
    assert not m('jugfile.a_function')
    assert not m('function.other')


def test_name_partially_qualified():
    m = prepare_name_matcher('mod.function')
    assert m('pkg.mod.function')
    assert m('mod.function')
    assert not m('pkg.xmod.function')
    assert not m('pkg.mod.function_other')


def test_name_glob():
    m = prepare_name_matcher('function*')
    assert m('jugfile.function')
    assert m('jugfile.function_other')
    assert not m('jugfile.other_function')

    m = prepare_name_matcher('*function')
    assert m('jugfile.function')
    assert m('jugfile.other_function')
    assert not m('jugfile.function_other')

    m = prepare_name_matcher('jugfile.*')
    assert m('jugfile.function')
    assert not m('other.function')

    assert prepare_name_matcher('f?')('mod.fn')


def test_name_regex_chars_are_literal():
    # Unlike --pattern, --name does not interpret regular expressions
    m = prepare_name_matcher('/function/')
    assert not m('jugfile.function')
    m = prepare_name_matcher('func.ion')
    assert not m('jugfile.function')
    assert m('jugfile.func.ion')


def test_name_lambda():
    assert prepare_name_matcher('<lambda>')('jugfile.<lambda>')


def test_name_empty():
    assert not prepare_name_matcher('')('jugfile.function')


def test_pattern_is_loose():
    # this is the behaviour --target used to have
    m = prepare_task_matcher('jugfile.function')
    assert m('jugfile.function')
    assert m('jugfile.function_other')

    m = prepare_task_matcher('function')
    assert m('jugfile.function_other')
    assert not m('jugfile_function')

    m = prepare_task_matcher('/compute_.*/')
    assert m('jugfile.compute_x')
    assert not m('jugfile.other')

    assert not prepare_task_matcher('/function$/')('jugfile.function_other')
    assert prepare_task_matcher('/function$/')('jugfile.function')


def test_matcher_from_options():
    assert prepare_matcher_from_options() is None
    assert prepare_matcher_from_options(name='function')('mod.function')
    assert not prepare_matcher_from_options(name='function')('mod.function_other')
    assert prepare_matcher_from_options(pattern='function')('mod.function_other')

    m = prepare_matcher_from_options(name='function*', pattern='/other/')
    assert m('mod.function_other')
    assert not m('mod.function')


@pytest.mark.parametrize('cmd,name_attr,pattern_attr', [
    ('execute', 'execute_name', 'execute_pattern'),
    ('invalidate', 'invalid_name', 'invalid_pattern'),
    ])
def test_parse_name_and_pattern(cmd, name_attr, pattern_attr, capsys):
    options = parse([cmd, '--name', 'f'])
    assert getattr(options, name_attr) == 'f'
    assert getattr(options, pattern_attr) is None

    options = parse([cmd, '--pattern', 'f'])
    assert getattr(options, name_attr) is None
    assert getattr(options, pattern_attr) == 'f'
    assert capsys.readouterr().err == ''


@pytest.mark.parametrize('cmd,name_attr,pattern_attr', [
    ('execute', 'execute_name', 'execute_pattern'),
    ('invalidate', 'invalid_name', 'invalid_pattern'),
    ])
def test_parse_target_is_deprecated_name(cmd, name_attr, pattern_attr, capsys):
    options = parse([cmd, '--target', 'f'])
    assert getattr(options, name_attr) == 'f'
    assert getattr(options, pattern_attr) is None
    err = capsys.readouterr().err
    assert '--target is deprecated' in err
    assert '--name' in err and '--pattern' in err


def test_parse_invalid_is_deprecated_name(capsys):
    options = parse(['invalidate', '--invalid', 'f'])
    assert options.invalid_name == 'f'
    assert '--invalid is deprecated' in capsys.readouterr().err


@pytest.mark.parametrize('cmd', ['execute', 'invalidate'])
@pytest.mark.parametrize('other', ['--pattern', '--target'])
def test_parse_name_excludes_others(cmd, other):
    with pytest.raises(SystemExit):
        parse([cmd, '--name', 'f', other, 'g'])


def test_parse_invalidate_requires_selection():
    with pytest.raises(SystemExit):
        parse(['invalidate'])


def test_parse_execute_selection_optional():
    options = parse(['execute'])
    assert options.execute_name is None
    assert options.execute_pattern is None
