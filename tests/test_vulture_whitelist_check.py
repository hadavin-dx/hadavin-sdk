"""tools/vulture_whitelist_check.py: each way a whitelist entry can go stale is reported, and a good file passes.

The tool reads `vulture_whitelist.py` and the files it names from a repository root; here the root is a temporary
folder, so the real whitelist is not touched.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from tools import vulture_whitelist_check as vw

SOURCE = '''\
"""A docstring that mentions ghost_name and also_ghost."""

# a comment that mentions commented_name

class Model:
    field_a: int = 0

    def method_b(self, arg_c):
        self.attr_d = arg_c


def func_e():
    return 1
'''


def _repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, whitelist: str) -> None:
    pkg = tmp_path / "src" / "hadavin_sdk"
    pkg.mkdir(parents=True)
    (pkg / "mod.py").write_text(SOURCE, encoding="utf-8")
    (tmp_path / "vulture_whitelist.py").write_text(whitelist, encoding="utf-8")
    monkeypatch.setattr(vw, "ROOT", tmp_path)


def _run(capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    rc = vw.main()
    return rc, capsys.readouterr().out


def test_a_whitelist_whose_names_are_all_defined_passes(tmp_path, monkeypatch, capsys):
    _repo(
        tmp_path,
        monkeypatch,
        "# a header comment\n\n"
        "field_a  # variable in mod.py\n"
        "_.attr_d  # attribute in mod.py\n"
        "method_b  # method in mod.py\n"
        "func_e  # function in mod.py\n"
        "Model  # class in mod.py\n",
    )
    rc, out = _run(capsys)
    assert rc == 0, out
    assert "5 entries, 0 problems" in out


def test_a_name_the_file_no_longer_defines_is_reported(tmp_path, monkeypatch, capsys):
    _repo(tmp_path, monkeypatch, "removed_name  # function in mod.py\n")
    rc, out = _run(capsys)
    assert rc == 1
    assert "line 1: removed_name: mod.py no longer defines it" in out


def test_a_name_that_only_appears_in_a_comment_or_a_docstring_is_reported(
    tmp_path, monkeypatch, capsys
):
    _repo(
        tmp_path,
        monkeypatch,
        "commented_name  # variable in mod.py\nghost_name  # variable in mod.py\n",
    )
    rc, out = _run(capsys)
    assert rc == 1
    assert "line 1: commented_name: mod.py no longer defines it" in out
    assert "line 2: ghost_name: mod.py no longer defines it" in out


def test_a_name_listed_twice_is_reported(tmp_path, monkeypatch, capsys):
    _repo(
        tmp_path,
        monkeypatch,
        "field_a  # variable in mod.py\nfield_a  # variable in mod.py\n",
    )
    rc, out = _run(capsys)
    assert rc == 1
    assert "line 2: field_a is listed twice" in out


def test_a_file_that_is_gone_is_reported(tmp_path, monkeypatch, capsys):
    _repo(tmp_path, monkeypatch, "field_a  # variable in mod.py, deleted.py\n")
    rc, out = _run(capsys)
    assert rc == 1
    assert "line 1: field_a: deleted.py does not exist" in out
    assert "mod.py no longer defines" not in out  # the file that does exist still counts


def test_one_file_of_several_losing_the_name_is_reported(tmp_path, monkeypatch, capsys):
    _repo(tmp_path, monkeypatch, "field_a  # variable in mod.py, other.py\n")
    (tmp_path / "src" / "hadavin_sdk" / "other.py").write_text("y = 2\n", encoding="utf-8")
    rc, out = _run(capsys)
    assert rc == 1
    assert "line 1: field_a: other.py no longer defines it" in out


@pytest.mark.parametrize(
    "line",
    [
        "field_a",  # no comment at all
        "field_a  # mod.py",  # no kind
        "field_a  # thing in mod.py",  # an unknown kind
        "field_a # variable in mod.py",  # one space before the hash
        "field_a  # variable in mod.txt",  # not a python file
    ],
)
def test_an_entry_in_the_wrong_form_is_reported(tmp_path, monkeypatch, capsys, line):
    _repo(tmp_path, monkeypatch, line + "\n")
    rc, out = _run(capsys)
    assert rc == 1
    assert "line 1: not in the form `name  # kind in path.py`" in out
