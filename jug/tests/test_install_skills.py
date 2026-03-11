import filecmp
import os
from pathlib import Path

import pytest

from jug.options import parse
from jug.subcommands.install_skills import bundled_skill_path, install_skill, install_skills


def _assert_same_tree(left, right):
    comparison = filecmp.dircmp(left, right)
    assert comparison.left_only == []
    assert comparison.right_only == []
    assert comparison.diff_files == []
    for subdir in comparison.common_dirs:
        _assert_same_tree(
            os.path.join(left, subdir),
            os.path.join(right, subdir))


def test_bundled_skill_payload_exists():
    bundled = Path(bundled_skill_path()).resolve()

    assert bundled.is_dir()
    assert bundled.joinpath('SKILL.md').is_file()
    assert bundled.joinpath('agents', 'openai.yaml').is_file()
    assert bundled.joinpath('references', 'troubleshooting.md').is_file()


def test_install_skill_copies_tree(tmp_path):
    target = install_skill(str(tmp_path))
    assert Path(target).is_dir()
    assert Path(target, 'SKILL.md').is_file()
    _assert_same_tree(str(Path(bundled_skill_path())), str(Path(target)))


def test_install_skill_refuses_existing_target(tmp_path):
    install_skill(str(tmp_path))
    with pytest.raises(RuntimeError):
        install_skill(str(tmp_path))


def test_install_skill_force_overwrites_existing_target(tmp_path):
    target = Path(install_skill(str(tmp_path)))
    target.joinpath('sentinel.txt').write_text('stale')

    install_skill(str(tmp_path), force=True)

    assert not target.joinpath('sentinel.txt').exists()
    _assert_same_tree(str(Path(bundled_skill_path())), str(target))


def test_install_skills_options():
    options = parse(['install-skills', '--output', '/tmp/skills'])
    assert options.install_skills_output == '/tmp/skills'
    assert not options.install_skills_force


def test_install_skills_command(tmp_path):
    options = parse(['install-skills', '--output', str(tmp_path)])
    messages = []
    options.print_out = messages.append

    install_skills.run(options=options)

    assert messages == ['Installed Jug skill to {}'.format(tmp_path / 'jug')]
