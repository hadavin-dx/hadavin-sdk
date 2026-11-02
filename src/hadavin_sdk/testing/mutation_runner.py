"""A small mutation runner: revert one guard at a time in a temp copy of a package and judge the kill by its reason.

``run_mutants(root, mutants, ...)`` copies ``root/src`` (and the listed test files and fixtures) to a temp dir for EACH mutant, replaces
every occurrence of ``old`` by ``new`` in one file, runs pytest with a JUnit file on the targeted tests, and judges the failing test with
``testing.mutation.judge``. A mutant counts as GOOD only if the verdict is KILLED, or CRASH when the mutant sets ``allow_crash``. The
unmutated copy must pass first (otherwise every kill is meaningless). Stdlib only; runs pytest through ``sys.executable``.

This is a developer tool, not a runtime module: no ``hadavin_sdk`` module imports it and it is not re-exported. It stays in the package
(and not in a separate tools folder) because demo repositories take it from core by path and pin (``core_copies.json``), and moving
it would break that import. It runs a subprocess on caller-chosen trees, so every path it reads, copies or writes is checked to stay
inside its tree (``_inside``: a ``..`` part or an absolute path is a ``ValueError``), and every pytest run has a timeout.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath

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

    def __post_init__(self) -> None:
        _relative(self.file)
        if len(self.expect) < 4:
            raise ValueError("expect must be at least 4 characters")


def _relative(rel: str) -> str:
    """``rel`` must be a relative path with no ``..`` part (checked as a POSIX and as a Windows path)."""
    if not isinstance(rel, str) or not rel:
        raise ValueError("a path is a non-empty string")
    for pure in (PurePosixPath(rel), PureWindowsPath(rel)):
        if pure.is_absolute() or pure.anchor or pure.drive or ".." in pure.parts:
            raise ValueError(f"path escapes its tree: {rel!r}")
    return rel


def _inside(base: Path, rel: str) -> Path:
    """``base / rel``, resolved, and proven to lie inside ``base`` (symlinks included)."""
    root = base.resolve()
    path = (root / _relative(rel)).resolve()
    if path == root or not path.is_relative_to(root):
        raise ValueError(f"path escapes its tree: {rel!r}")
    return path


TIMED_OUT = -9  # returned instead of an exit code when the run exceeded its timeout


def _pytest(cwd: Path, tests: Sequence[str], junit: Path, timeout: float) -> int:
    env = dict(os.environ, PYTHONPATH=str(cwd / "src"))
    try:
        r = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--noconftest", "-x", f"--junitxml={junit}", "--", *tests],
            cwd=cwd, env=env, capture_output=True, text=True, check=False, timeout=timeout,
        )  # fmt: skip
    except subprocess.TimeoutExpired:
        return TIMED_OUT  # a mutant that loops forever is reported, never allowed to hang the run
    return r.returncode


def run_mutants(
    root: Path,
    mutants: Iterable[Mutant],
    tests: Sequence[str],
    *,
    extra_dirs: Sequence[str] = ("tests/fixtures",),
    only: Sequence[str] = (),
    timeout: float = 900.0,
) -> list[tuple[str, Verdict, str, bool]]:
    """(name, verdict, failing test id, good). Raises ``RuntimeError`` if the unmutated copy fails or times out; a mutant run that exceeds
    ``timeout`` seconds is ``(name, Verdict.ERROR, "TIMEOUT", False)``. Every ``tests`` and ``extra_dirs`` entry and every mutant file
    must stay inside its tree (``ValueError``)."""
    root = Path(root)
    for t in (*tests, *extra_dirs):
        _relative(t)
    tmp = Path(tempfile.mkdtemp(prefix="mutants_"))

    def fresh() -> None:
        shutil.rmtree(tmp, ignore_errors=True)
        (tmp / "tests").mkdir(parents=True)
        shutil.copytree(root / "src", tmp / "src", ignore=shutil.ignore_patterns("__pycache__"))
        for t in tests:
            dst = _inside(tmp, t)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(_inside(root, t), dst)
        for d in extra_dirs:
            src = _inside(root, d)
            if src.exists():
                shutil.copytree(src, _inside(tmp, d), dirs_exist_ok=True)

    out: list[tuple[str, Verdict, str, bool]] = []
    try:
        fresh()
        if _pytest(tmp, tests, tmp / "base.xml", timeout) != 0:
            raise RuntimeError("the unmutated copy does not pass its tests")
        for m in mutants:
            if only and not any(o in m.name for o in only):
                continue
            fresh()
            p = _inside(tmp, m.file)
            text = p.read_text(encoding="utf-8")
            if m.old not in text:
                out.append((m.name, Verdict.ERROR, "SNIPPET NOT FOUND", False))
                continue
            p.write_text(text.replace(m.old, m.new), encoding="utf-8", newline="\n")
            junit = tmp / "r.xml"
            rc = _pytest(tmp, tests, junit, timeout)
            if rc == TIMED_OUT:
                out.append((m.name, Verdict.ERROR, "TIMEOUT", False))
                continue
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
