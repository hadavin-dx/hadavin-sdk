"""A small mutation runner: revert one guard at a time in a temp copy of a package and judge the kill by its reason.

``run_mutants(root, mutants, ...)`` takes ONE snapshot of ``root/src`` (and the listed test files and fixtures) when it starts (an edit of ``root`` during the run never leaks into a later mutant) and copies it to a temp dir for EACH mutant; the pytest child sees only the environment variables in ``CHILD_ENV`` (no DSN, token or other secret of the caller), replaces
every occurrence of ``old`` by ``new`` in one file, runs pytest with a JUnit file on the targeted tests, and judges the failing test with
``testing.mutation.judge``. A mutant counts as GOOD only if the verdict is KILLED, or CRASH when the mutant sets ``allow_crash``. The
unmutated copy must pass first (otherwise every kill is meaningless). Stdlib only; runs pytest through ``sys.executable``.

This is a developer tool, not a runtime module: it lives in ``tools/`` (NOT in the wheel, not under ``src``). A demo that wants it
copies ``tools/mutation_runner.py`` from core like any other core file (a ``core_copies.json`` row, ``import_rewrite`` of nothing: it
imports only ``hadavin_sdk.testing.mutation``). It runs a subprocess on caller-chosen trees, so the mutant file is found by LISTING the
tree (``_locate``: the caller's string is compared with the listed names and never joined to a path), every other path is checked to
stay inside its tree (``_inside``: a ``..`` part or an absolute path is a ``ValueError``), and every pytest run has a timeout, and a timeout kills the whole process tree of the run.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath

from hadavin_sdk.testing.mutation import MAX_JUNIT_CHARS, Verdict, first_failure_junit, judge


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
    crash_type: str = ""  # REQUIRED with allow_crash: the exception CLASS NAME that must appear in the first ``E`` line, or the mutant is not good
    crash_markers: tuple[
        str, ...
    ] = ()  # passed to ``judge``: a first line holding one of these is a CRASH even if it is an assertion
    test_file: str = ""  # one of the `tests` files: run ONLY this file for the mutant (its killer is not in the first file)
    pinned: str = ""  # the test id (as ``first_failure_junit`` writes it, ``tests/test_x::test_y``) that must be the one failing; another failing test is OTHER_TEST
    only_test: str = ""  # a test function name: run ONLY that test (of the first test file, or of `test_file`), so the killer never depends on test order or a fuzz seed

    def __post_init__(self) -> None:
        _relative(self.file)
        if len(self.expect) < 4:
            raise ValueError("expect must be at least 4 characters")
        if self.allow_crash and not self.crash_type.isidentifier():
            raise ValueError(
                "allow_crash needs crash_type: the exception class name the kill must show"
            )
        if self.crash_type and not self.allow_crash:
            raise ValueError("crash_type without allow_crash")
        if self.only_test and not self.only_test.isidentifier():
            raise ValueError("only_test must be a test function name")
        if self.test_file:
            _relative(self.test_file)


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


TIMED_OUT = -1000  # returned instead of an exit code when the run exceeded its timeout; no process exit status is this low (POSIX -9 is a SIGKILL, for example the OOM killer, and is judged as an error)
CHILD_ENV = (
    "PATH", "PATHEXT", "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC", "TEMP", "TMP", "TMPDIR", "HOME", "USERPROFILE",
    "LANG", "LC_ALL", "PYTHONHASHSEED", "PYTHONUTF8", "PYTHONIOENCODING",
)  # fmt: skip  # the only variables a mutant run inherits
CHILD_FIXED_ENV = {
    "PYTHONNOUSERSITE": "1"
}  # set, not inherited: the child never imports from the caller's user site-packages
SETUP_TRIES = 5  # attempts to clear and rebuild the temp copy (a Windows file lock may hold a file for a moment)
SETUP_WAIT = 0.5  # seconds between those attempts
# a refused JUnit file (DOCTYPE, ENTITY, too large) or a truncated one (ET.ParseError is a SyntaxError) is THIS mutant's ERROR, not the end of the run
JUNIT_REFUSED = (ValueError, SyntaxError)
FIRST_LINES: dict[
    str, str
] = {}  # mutant name -> the first ``E`` line of its kill (diagnostics, and what ``crash_type`` is checked against)


def _taskkill() -> str:
    """taskkill.exe by its full path under %SystemRoot%\\System32, not by a PATH search (a planted taskkill in a work folder is not run)."""
    root = os.environ.get("SystemRoot") or os.environ.get("SYSTEMROOT") or r"C:\\Windows"
    return str(Path(root) / "System32" / "taskkill.exe")


TREE_KILL_TIMEOUT = 60.0  # seconds ``taskkill`` may take before the child itself is killed anyway


def _locate(base: Path, rel: str) -> Path:
    """The file ``rel`` names inside ``base``, found by listing the tree (``os.walk``; a match is accepted only if its real path stays inside the tree): the caller's string is only
    COMPARED as data with the listed relative names and is never joined to a path, so it cannot steer a read or a write out of the tree."""
    want = _relative(rel).replace("\\", "/")
    for dirpath, _dirs, files in os.walk(base):
        for name in files:
            full = os.path.join(dirpath, name)
            if os.path.relpath(full, base).replace(os.sep, "/") != want:
                continue
            real_base, real_full = os.path.realpath(base), os.path.realpath(full)
            # a link (or junction) out of the tree does not count
            if os.path.commonpath([real_base, real_full]) == real_base:
                return Path(full)
    raise ValueError(f"no such file inside the tree: {rel!r}")


def _pytest(cwd: Path, tests: Sequence[str], junit: Path, timeout: float) -> int:
    # an ALLOWLIST, not os.environ: a mutant run must not see a database DSN, a token or any other secret of the caller; PYTHONPATH also holds the tree root (tests may import tools.*)
    env = {k: os.environ[k] for k in CHILD_ENV if k in os.environ}
    env.update(CHILD_FIXED_ENV)
    env["PYTHONPATH"] = os.pathsep.join([str(cwd / "src"), str(cwd)])
    cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--noconftest", "-x", f"--junitxml={junit}", "--", *tests]  # fmt: skip
    # own process group (POSIX session / Windows group): on a timeout the whole tree dies, not only pytest (a test may have started psql or a server)
    own = (
        {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
        if os.name == "nt"
        else {"start_new_session": True}
    )
    # S603 stays a listed exception: the argument list holds the caller's test paths and the junit path, so ruff cannot see it as a literal. Fixed argv (our own interpreter), no shell, caller strings only as pytest operands after --
    with subprocess.Popen(  # noqa: S603
        cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **own  # type: ignore[call-overload]
    ) as proc:  # fmt: skip
        try:
            return proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            _kill_tree(proc)
            # a mutant that loops forever is reported, never allowed to hang the run
            return TIMED_OUT


def _kill_tree(proc: subprocess.Popen[bytes]) -> None:
    """Kill ``proc`` and everything it started (POSIX: its process group; Windows: ``taskkill /T``). A failing tree kill (no ``taskkill``
    on the PATH, its own timeout, ``PermissionError`` from ``killpg``) never skips the kill of the child itself."""
    try:
        if os.name == "nt":
            # S603 stays a listed exception: the pid is our own child's, but the list is not a literal to ruff. Fixed argv, no shell
            subprocess.run(  # noqa: S603
                [_taskkill(), "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False, timeout=TREE_KILL_TIMEOUT,
            )  # fmt: skip
        else:
            import signal

            os.killpg(proc.pid, signal.SIGKILL)
    # ProcessLookupError and PermissionError are OSErrors
    except (OSError, subprocess.TimeoutExpired):
        pass
    finally:
        proc.kill()  # the child itself, always
        proc.wait()


def run_mutants(
    root: Path,
    mutants: Iterable[Mutant],
    tests: Sequence[str],
    *,
    extra_dirs: Sequence[str] = ("tests/fixtures",),
    only: Sequence[str] = (),
    timeout: float = 900.0,
    baseline_timeout: float | None = None,
    on_result: Callable[[tuple[str, Verdict, str, bool]], None] | None = None,
) -> list[tuple[str, Verdict, str, bool]]:
    """(name, verdict, failing test id, good). Raises ``RuntimeError`` if the unmutated copy fails or times out; a mutant whose temp copy cannot be built (after ``SETUP_TRIES`` tries) is ``(name, Verdict.ERROR, "SETUP FAILED: <error class>", False)``; a mutant run that exceeds
    ``timeout`` seconds is ``(name, Verdict.ERROR, "TIMEOUT", False)``. The unmutated baseline run gets ``baseline_timeout`` (default: ``timeout``),
    so a test can use a short mutant timeout without failing a slow baseline. ``on_result`` is called with each result as soon as that mutant
    finishes (stream it and a timeout of the whole run still leaves a kill list). Every ``tests`` and ``extra_dirs`` entry and every mutant file
    must name a file inside its tree (``ValueError``)."""
    root = Path(root)
    mutants = list(mutants)
    for t in (*tests, *extra_dirs):
        _relative(t)
    for m in mutants:  # before anything runs: a bad `test_file` must not surface after earlier mutants were already run
        if m.test_file and m.test_file not in tests:
            raise ValueError(
                f"mutant {m.name!r}: test_file {m.test_file!r} is not one of the copied tests"
            )
    tmp = Path(tempfile.mkdtemp(prefix="mutants_"))
    # ONE snapshot of the tree at the start: every mutant copy is made from it, so an edit of ``root`` while the run is going (a developer
    # saving a file, a second tool) can never leak into a later mutant
    snap = Path(tempfile.mkdtemp(prefix="mutants_snap_"))
    shutil.copytree(
        root / "src", snap / "src", symlinks=True, ignore=shutil.ignore_patterns("__pycache__")
    )  # links stay links (never followed out of the tree)
    for t in tests:
        dst = _inside(snap, t)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(_inside(root, t), dst)
    for d in extra_dirs:
        if _inside(root, d).exists():
            shutil.copytree(_inside(root, d), _inside(snap, d), symlinks=True, dirs_exist_ok=True)

    def build() -> None:
        shutil.rmtree(tmp, ignore_errors=True)
        (tmp / "tests").mkdir(parents=True)
        shutil.copytree(snap / "src", tmp / "src", symlinks=True)
        for t in tests:
            dst = _inside(tmp, t)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(_inside(snap, t), dst)
        for d in extra_dirs:
            if _inside(snap, d).exists():
                shutil.copytree(
                    _inside(snap, d), _inside(tmp, d), symlinks=True, dirs_exist_ok=True
                )

    def fresh() -> None:
        """Rebuild the temp copy: retried ``SETUP_TRIES`` times, then the last ``OSError`` is raised (never swallowed)."""
        for attempt in range(SETUP_TRIES):
            try:
                return build()
            except OSError:
                if attempt == SETUP_TRIES - 1:
                    raise
                time.sleep(SETUP_WAIT)

    out: list[tuple[str, Verdict, str, bool]] = []

    def emit(row: tuple[str, Verdict, str, bool]) -> None:
        out.append(row)
        if on_result is not None:
            on_result(row)

    try:
        fresh()
        if _pytest(tmp, tests, tmp / "base.xml", baseline_timeout or timeout) != 0:
            raise RuntimeError("the unmutated copy does not pass its tests")
        for m in mutants:
            if only and not any(o in m.name for o in only):
                continue
            try:
                fresh()
            except OSError as exc:  # a setup failure is a RESULT ROW for this mutant, never a crash of the run and never silent
                emit((m.name, Verdict.ERROR, f"SETUP FAILED: {type(exc).__name__}", False))
                continue
            p = _locate(tmp, m.file)
            text = p.read_text(encoding="utf-8")
            if m.old not in text:
                emit((m.name, Verdict.ERROR, "SNIPPET NOT FOUND", False))
                continue
            p.write_text(text.replace(m.old, m.new), encoding="utf-8", newline="\n")
            junit = tmp / "r.xml"
            if m.test_file:
                operands = [f"{m.test_file}::{m.only_test}" if m.only_test else m.test_file]
            else:
                operands = [f"{tests[0]}::{m.only_test}", *tests[1:]] if m.only_test else tests
            rc = _pytest(tmp, operands, junit, timeout)
            if rc == TIMED_OUT:
                emit((m.name, Verdict.ERROR, "TIMEOUT", False))
                continue
            try:
                too_big = (
                    junit.exists() and junit.stat().st_size > MAX_JUNIT_CHARS
                )  # looked at BEFORE the file is read
                if too_big:
                    raise ValueError("junit file over the ceiling")
                test_id, first = (
                    first_failure_junit(junit.read_text(encoding="utf-8"))
                    if junit.exists()
                    else ("", "")
                )
            except JUNIT_REFUSED:
                emit((m.name, Verdict.ERROR, "JUNIT REFUSED", False))
                continue
            v = judge(
                rc,
                test_id,
                first,
                expect=m.expect,
                pinned=m.pinned or None,
                crash_markers=m.crash_markers,
            )
            FIRST_LINES[m.name] = first
            crash_ok = v is Verdict.CRASH and m.allow_crash and m.crash_type in first
            emit((m.name, v, test_id, v is Verdict.KILLED or crash_ok))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(snap, ignore_errors=True)
    return out
