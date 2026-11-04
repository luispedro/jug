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
    assert m('jugfile.other_function')
    assert not m('jugfile.other')

    m = prepare_task_matcher('/compute_.*/')
    assert m('jugfile.compute_x')
    assert not m('jugfile.other')

    assert not prepare_task_matcher('/function$/')('jugfile.function_other')
    assert prepare_task_matcher('/function$/')('jugfile.function')


def test_pattern_is_substring():
    assert prepare_task_matcher('prime')('primes.is_prime')
    assert prepare_task_matcher('identity')('identity')
    assert prepare_task_matcher('s.is_p')('primes.is_prime')
    # outside /.../, regular expression characters are literal
    assert not prepare_task_matcher('compute_.*')('jugfile.compute_x')
    assert prepare_task_matcher('f+')('jugfile.f+g')
    assert not prepare_task_matcher('f+')('jugfile.ff')
    # '/a/b' is not a regular expression
    assert not prepare_task_matcher('/a/b')('jugfile.a')
    assert prepare_task_matcher('/a/b')('x/a/b')


def test_matcher_from_options(capsys):
    assert prepare_matcher_from_options() is None
    assert prepare_matcher_from_options(name='function')('mod.function')
    assert not prepare_matcher_from_options(name='function')('mod.function_other')
    assert prepare_matcher_from_options(pattern='function')('mod.function_other')
    assert capsys.readouterr().err == ''

    m = prepare_matcher_from_options(name='function*', pattern='/other/')
    assert m('mod.function_other')
    assert not m('mod.function')
    err = capsys.readouterr().err
    assert 'warning' in err
    assert 'both a name and a pattern' in err


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


@pytest.mark.parametrize('pattern', ['', '//'])
def test_pattern_empty_is_rejected(pattern):
    # an empty pattern would match every task (e.g., `--pattern "$TASK"` with
    # an unset variable would invalidate everything)
    with pytest.raises(ValueError):
        prepare_task_matcher(pattern)
    with pytest.raises(ValueError):
        prepare_matcher_from_options(pattern=pattern)


def test_pattern_slash_is_literal():
    m = prepare_task_matcher('/')
    assert m('x/y')
    assert not m('jugfile.function')


@pytest.mark.parametrize('cmd', ['execute', 'invalidate'])
@pytest.mark.parametrize('pattern', ['', '//'])
def test_parse_pattern_empty_is_rejected(cmd, pattern, capsys):
    with pytest.raises(SystemExit) as e:
        parse([cmd, '--pattern', pattern])
    assert e.value.code == 2
    assert 'empty pattern' in capsys.readouterr().err


def test_exclude_only():
    m = prepare_matcher_from_options(exclude_names=['function'])
    assert not m('mod.function')
    assert m('mod.function_other')
    assert m('mod.other')

    m = prepare_matcher_from_options(exclude_patterns=['function'])
    assert not m('mod.function')
    assert not m('mod.function_other')
    assert m('mod.other')


def test_exclude_name_is_strict():
    # same rules as --name
    m = prepare_matcher_from_options(exclude_names=['func'])
    assert not m('mod.func')
    assert not m('pkg.mod.func')
    assert m('mod.func_other')
    assert m('mod.a_func')

    m = prepare_matcher_from_options(exclude_names=['func*'])
    assert not m('mod.func_other')
    assert m('mod.a_func')


def test_exclude_pattern_is_loose():
    # same rules as --pattern
    m = prepare_matcher_from_options(exclude_patterns=['func'])
    assert not m('mod.func_other')
    assert not m('mod.a_func')
    m = prepare_matcher_from_options(exclude_patterns=['/func$/'])
    assert not m('mod.a_func')
    assert m('mod.func_other')


def test_include_and_exclude(capsys):
    m = prepare_matcher_from_options(name='align_*', exclude_names=['align_fast'])
    assert m('mod.align_slow')
    assert not m('mod.align_fast')
    assert not m('mod.other')

    m = prepare_matcher_from_options(pattern='/^mod\\./', exclude_patterns=['slow'])
    assert m('mod.align_fast')
    assert not m('mod.align_slow')
    assert not m('other.align_fast')
    # exclusions do not trigger the name+pattern warning
    assert capsys.readouterr().err == ''


def test_several_exclusions():
    m = prepare_matcher_from_options(exclude_names=['a', 'mod.b'],
                                     exclude_patterns=['/^x\\./', 'cc'])
    assert not m('mod.a')
    assert not m('mod.b')
    assert m('other.b_')
    assert not m('x.anything')
    assert not m('mod.acc')
    assert m('mod.d')


def test_exclude_single_string():
    # A bare string is one exclusion (not one per character)
    m = prepare_matcher_from_options(exclude_names='abc', exclude_patterns='xyz')
    assert not m('mod.abc')
    assert not m('mod.wxyz')
    assert m('mod.a')


@pytest.mark.parametrize('pattern', ['', '//'])
def test_exclude_pattern_empty_is_rejected(pattern):
    with pytest.raises(ValueError):
        prepare_matcher_from_options(exclude_patterns=[pattern])
    with pytest.raises(ValueError):
        prepare_matcher_from_options(exclude_patterns=['ok', pattern])


@pytest.mark.parametrize('pattern', ['', '//'])
def test_parse_exclude_pattern_empty_is_rejected(pattern, capsys):
    with pytest.raises(SystemExit) as e:
        parse(['execute', '--exclude-pattern', pattern])
    assert e.value.code == 2
    assert 'empty pattern' in capsys.readouterr().err


def test_parse_exclusions_default():
    options = parse(['execute'])
    assert options.execute_exclude_name == []
    assert options.execute_exclude_pattern == []


def test_parse_exclusions_repeatable():
    options = parse(['execute',
                     '--exclude-name', 'a',
                     '--exclude-pattern', 'b',
                     '--exclude-name', 'c',
                     '--exclude-pattern', '/d/'])
    assert options.execute_exclude_name == ['a', 'c']
    assert options.execute_exclude_pattern == ['b', '/d/']
    assert options.execute_name is None
    assert options.execute_pattern is None


@pytest.mark.parametrize('include', ['--name', '--pattern'])
def test_parse_exclusions_combine_with_include(include):
    # Not part of the mutually exclusive --name/--pattern group
    options = parse(['execute', include, 'align_*',
                     '--exclude-name', 'align_fast',
                     '--exclude-pattern', 'slow'])
    assert options.execute_exclude_name == ['align_fast']
    assert options.execute_exclude_pattern == ['slow']


def test_parse_invalidate_has_no_exclusions():
    with pytest.raises(SystemExit):
        parse(['invalidate', '--name', 'f', '--exclude-name', 'g'])


def test_exclusions_from_configuration_file():
    from io import StringIO
    config = '''
[execute]
exclude-name = align_*
    sort
exclude-pattern = /^x\\./
'''
    options = parse(['execute'], optionsfile=StringIO(config))
    assert options.execute_exclude_name == ['align_*', 'sort']
    assert options.execute_exclude_pattern == ['/^x\\./']

    # The command line replaces the configuration file
    options = parse(['execute', '--exclude-name', 'other'], optionsfile=StringIO(config))
    assert options.execute_exclude_name == ['other']
    assert options.execute_exclude_pattern == ['/^x\\./']
