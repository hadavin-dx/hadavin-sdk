"""tools/mypy_ratchet.py: every way the mypy rollout list can be wrong is reported, and a correct list is not.

The tool runs mypy on the real repository; here its mypy run is replaced by a fixed answer (`counts`) and its
repository root by a temporary folder, so these tests need no mypy and no network. One test also feeds the tool's
own parser a canned mypy output.
"""

from __future__ import annotations

import json
import subprocess
import textwrap
from pathlib import Path

import pytest
from tools import mypy_ratchet as mr

A = "src/pkg/a.py"
B = "src/pkg/b.py"


def _project(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    listed: list[str],
    files: list[str],
    baseline: dict[str, int],
    now: dict[str, int],
) -> None:
    """A temp repository: pyproject.toml listing `listed` modules, the files under src/, a baseline, a mypy answer."""
    for rel in files:
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x = 1\n", encoding="utf-8")
    mods = ", ".join(f'"{m}"' for m in listed)
    (tmp_path / "pyproject.toml").write_text(
        textwrap.dedent(
            f"""\
            [tool.mypy]
            files = ["src"]

            [[tool.mypy.overrides]]
            ignore_errors = true
            module = [{mods}]
            """
        ),
        encoding="utf-8",
    )
    (tmp_path / "baseline.json").write_text(json.dumps(baseline), encoding="utf-8")
    monkeypatch.setattr(mr, "ROOT", tmp_path)
    monkeypatch.setattr(mr, "BASELINE", tmp_path / "baseline.json")
    monkeypatch.setattr(mr, "counts", lambda: now)


def _run(capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    rc = mr.main(["mypy_ratchet"])
    return rc, capsys.readouterr().out


def test_a_list_that_matches_the_baseline_passes(tmp_path, monkeypatch, capsys):
    _project(
        tmp_path,
        monkeypatch,
        listed=["pkg.a", "pkg.b"],
        files=[A, B],
        baseline={A: 3, B: 1},
        now={A: 3, B: 1},
    )
    rc, out = _run(capsys)
    assert rc == 0, out
    assert "2 listed, 4 findings, 0 problems" in out


def test_a_listed_module_that_is_clean_is_reported(tmp_path, monkeypatch, capsys):
    _project(
        tmp_path,
        monkeypatch,
        listed=["pkg.a", "pkg.b"],
        files=[A, B],
        baseline={A: 3, B: 1},
        now={A: 3},  # b.py has no finding any more
    )
    rc, out = _run(capsys)
    assert rc == 1
    assert f"{B}: listed but clean" in out


def test_a_listed_module_that_does_not_exist_is_reported(tmp_path, monkeypatch, capsys):
    _project(
        tmp_path,
        monkeypatch,
        listed=["pkg.a", "pkg.gone"],
        files=[A],
        baseline={A: 3},
        now={A: 3},
    )
    rc, out = _run(capsys)
    assert rc == 1
    assert "pkg.gone: no such module" in out


def test_a_listed_module_with_more_findings_is_reported_as_growth(tmp_path, monkeypatch, capsys):
    _project(tmp_path, monkeypatch, listed=["pkg.a"], files=[A], baseline={A: 3}, now={A: 4})
    rc, out = _run(capsys)
    assert rc == 1
    assert f"{A}: 4 findings, baseline 3 (it got worse)" in out


def test_a_listed_module_with_fewer_findings_must_lower_the_baseline(tmp_path, monkeypatch, capsys):
    _project(tmp_path, monkeypatch, listed=["pkg.a"], files=[A], baseline={A: 3}, now={A: 2})
    rc, out = _run(capsys)
    assert rc == 1
    assert f"{A}: 2 findings, baseline 3 (lower the baseline" in out


def test_an_unlisted_module_with_a_finding_is_reported(tmp_path, monkeypatch, capsys):
    _project(
        tmp_path,
        monkeypatch,
        listed=["pkg.a"],
        files=[A, B],
        baseline={A: 3},
        now={A: 3, B: 2},
    )
    rc, out = _run(capsys)
    assert rc == 1
    assert f"{B}: has 2 finding(s) but is not listed" in out


def test_a_listed_module_missing_from_the_baseline_is_reported(tmp_path, monkeypatch, capsys):
    _project(tmp_path, monkeypatch, listed=["pkg.a"], files=[A], baseline={}, now={A: 3})
    rc, out = _run(capsys)
    assert rc == 1
    assert f"{A}: listed but missing from the baseline" in out


def test_a_baseline_entry_that_is_not_listed_is_reported(tmp_path, monkeypatch, capsys):
    _project(
        tmp_path,
        monkeypatch,
        listed=["pkg.a"],
        files=[A, B],
        baseline={A: 3, B: 1},
        now={A: 3},
    )
    rc, out = _run(capsys)
    assert rc == 1
    assert f"{B}: in the baseline but not listed" in out


def test_a_package_module_is_found_through_its_init_file(tmp_path, monkeypatch, capsys):
    init = "src/pkg/sub/__init__.py"
    _project(
        tmp_path, monkeypatch, listed=["pkg.sub"], files=[init], baseline={init: 1}, now={init: 1}
    )
    rc, out = _run(capsys)
    assert rc == 0, out


def test_write_replaces_the_baseline_with_the_current_counts(tmp_path, monkeypatch, capsys):
    _project(tmp_path, monkeypatch, listed=["pkg.a"], files=[A], baseline={A: 9}, now={A: 2})
    assert mr.main(["mypy_ratchet", "--write"]) == 0
    assert json.loads((tmp_path / "baseline.json").read_text(encoding="utf-8")) == {A: 2}
    assert "baseline written: 1 files, 2 findings" in capsys.readouterr().out


def test_the_config_for_the_run_drops_every_override_block(tmp_path, monkeypatch):
    _project(tmp_path, monkeypatch, listed=["pkg.a"], files=[A], baseline={}, now={})
    cfg = mr.config_without_overrides()
    assert "[tool.mypy]" in cfg
    assert "overrides" not in cfg
    assert "ignore_errors" not in cfg


def test_the_counts_come_from_the_error_lines_of_mypys_output(tmp_path, monkeypatch):
    real_counts = (
        mr.counts
    )  # `_project` replaces it with a fixed answer; this test wants the real one
    _project(tmp_path, monkeypatch, listed=[], files=[], baseline={}, now={})
    out = (
        "src/pkg/a.py:3: error: Incompatible types  [assignment]\n"
        "src/pkg/a.py:9: error: Missing return  [return]\n"
        "src/pkg/a.py:9: note: a note is not an error\n"
        "src/pkg/b.py:1: error: Name x is not defined  [name-defined]\n"
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a, 1, stdout=out, stderr=""),
    )
    assert real_counts() == {"src/pkg/a.py": 2, "src/pkg/b.py": 1}
