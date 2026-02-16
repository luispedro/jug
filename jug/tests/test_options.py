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


def test_parse_bool_from_config_false():
    parsed = jug.options.parse(
        ["execute"],
        StringIO("[main]\nwill-cite=false\n"))
    assert not parsed.will_cite


def test_parse_bool_from_config_off():
    parsed = jug.options.parse(
        ["execute"],
        StringIO("[main]\nwill-cite=off\n"))
    assert not parsed.will_cite


def test_parse_bool_from_config_zero():
    parsed = jug.options.parse(
        ["execute"],
        StringIO("[main]\nwill-cite=0\n"))
    assert not parsed.will_cite


def test_find_local_config_with_git(tmp_path, monkeypatch):
    # Create a mock git project with config files at multiple levels
    project = tmp_path / "project"
    project.mkdir()
    (project / ".git").mkdir()
    (project / ".jugrc").write_text("[main]\njugfile=root.py\n")

    sub = project / "sub"
    sub.mkdir()
    (sub / ".jugrc").write_text("[main]\njugfile=sub.py\n")

    monkeypatch.chdir(sub)
    files = jug.options.find_local_configuration_files()
    assert len(files) == 2
    assert files[0] == str(sub / ".jugrc")
    assert files[1] == str(project / ".jugrc")


def test_find_local_config_without_git(tmp_path, monkeypatch):
    # Without .git, only search cwd
    project = tmp_path / "project"
    project.mkdir()
    (project / ".jugrc").write_text("[main]\njugfile=root.py\n")

    sub = project / "sub"
    sub.mkdir()
    (sub / "jugrc").write_text("[main]\njugfile=sub.py\n")

    monkeypatch.chdir(sub)
    files = jug.options.find_local_configuration_files()
    assert len(files) == 1
    assert files[0] == str(sub / "jugrc")


def test_find_local_config_both_filenames(tmp_path, monkeypatch):
    # Both .jugrc and jugrc in the same directory
    project = tmp_path / "project"
    project.mkdir()
    (project / ".jugrc").write_text("[main]\njugfile=dot.py\n")
    (project / "jugrc").write_text("[main]\njugfile=nodot.py\n")

    monkeypatch.chdir(project)
    files = jug.options.find_local_configuration_files()
    assert len(files) == 2
    assert str(project / ".jugrc") in files
    assert str(project / "jugrc") in files


def test_find_local_config_none(tmp_path, monkeypatch):
    # No config files at all
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)
    files = jug.options.find_local_configuration_files()
    assert files == []


def test_local_config_shadows_farther(tmp_path, monkeypatch):
    # Closer config should shadow farther config via Options chaining
    project = tmp_path / "project"
    project.mkdir()
    (project / ".git").mkdir()
    (project / ".jugrc").write_text("[main]\njugfile=root.py\n")

    sub = project / "sub"
    sub.mkdir()
    (sub / ".jugrc").write_text("[main]\njugfile=sub.py\n")

    monkeypatch.chdir(sub)
    opts = jug.options.read_configuration_file(default_options=jug.options.default_options)
    assert opts.jugfile == 'sub.py'
