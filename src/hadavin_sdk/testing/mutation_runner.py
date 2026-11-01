"""A small mutation runner: revert one guard at a time in a temp copy of a package and judge the kill by its reason.

``run_mutants(root, mutants, ...)`` copies ``root/src`` (and the listed test files and fixtures) to a temp dir for EACH mutant, replaces
every occurrence of ``old`` by ``new`` in one file, runs pytest with a JUnit file on the targeted tests, and judges the failing test with
``testing.mutation.judge``. A mutant counts as GOOD only if the verdict is KILLED, or CRASH when the mutant sets ``allow_crash``. The
unmutated copy must pass first (otherwise every kill is meaningless). Stdlib only; runs pytest through ``sys.executable``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from hadavin_sdk.testing.mutation import Verdict, first_failure_junit, judge


@dataclass(frozen=True)
class Mutant:
    name: str
    file: str  # relative to the copied root
    old: str
    new: str
    expect: str  # >= 4 characters: a fragment of the failing test id or of its assertion line
    allow_crash: bool = (
        False  # the intended reaction is a crash (an exception other than an assertion)
    )


def _pytest(cwd: Path, tests: Sequence[str], junit: Path) -> int:
    env = dict(os.environ, PYTHONPATH=str(cwd / "src"))
    r = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--noconftest", f"--junitxml={junit}", *tests],
        cwd=cwd, env=env, capture_output=True, text=True, check=False,
    )  # fmt: skip
    return r.returncode


def run_mutants(
    root: Path,
    mutants: Iterable[Mutant],
    tests: Sequence[str],
    *,
    extra_dirs: Sequence[str] = ("tests/fixtures",),
    only: Sequence[str] = (),
) -> list[tuple[str, Verdict, str, bool]]:
    """(name, verdict, failing test id, good). Raises ``RuntimeError`` if the unmutated copy fails."""
    tmp = Path(tempfile.mkdtemp(prefix="mutants_"))

    def fresh() -> None:
        shutil.rmtree(tmp, ignore_errors=True)
        (tmp / "tests").mkdir(parents=True)
        shutil.copytree(root / "src", tmp / "src", ignore=shutil.ignore_patterns("__pycache__"))
        for t in tests:
            (tmp / t).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(root / t, tmp / t)
        for d in extra_dirs:
            if (root / d).exists():
                shutil.copytree(root / d, tmp / d, dirs_exist_ok=True)

    out: list[tuple[str, Verdict, str, bool]] = []
    try:
        fresh()
        if _pytest(tmp, tests, tmp / "base.xml") != 0:
            raise RuntimeError("the unmutated copy does not pass its tests")
        for m in mutants:
            if only and not any(o in m.name for o in only):
                continue
            fresh()
            p = tmp / m.file
            text = p.read_text(encoding="utf-8")
            if m.old not in text:
                out.append((m.name, Verdict.ERROR, "SNIPPET NOT FOUND", False))
                continue
            p.write_text(text.replace(m.old, m.new), encoding="utf-8", newline="\n")
            junit = tmp / "r.xml"
            rc = _pytest(tmp, tests, junit)
            test_id, first = (
                first_failure_junit(junit.read_text(encoding="utf-8"))
                if junit.exists()
                else ("", "")
            )
            v = judge(rc, test_id, first, expect=m.expect)
            out.append(
                (m.name, v, test_id, v is Verdict.KILLED or (v is Verdict.CRASH and m.allow_crash))
            )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out
