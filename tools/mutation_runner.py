"""A small mutation runner: revert one guard at a time in a temp copy of a package and judge the kill by its reason.

``run_mutants(root, mutants, ...)`` takes ONE snapshot of ``root/src`` (and the listed test files and fixtures) when it starts (an edit of ``root`` during the run never leaks into a later mutant) and copies it to a temp dir for EACH mutant; the pytest child sees only the environment variables in ``CHILD_ENV`` (no DSN, token or other secret of the caller), replaces
every occurrence of ``old`` by ``new`` in one file, runs pytest with a JUnit file on the targeted tests, and judges the failing test with
``testing.mutation.judge``. A mutant counts as GOOD only if the verdict is KILLED, or CRASH when the mutant sets ``allow_crash``. The
unmutated copy must pass first (otherwise every kill is meaningless). Stdlib only; runs pytest through ``sys.executable``.

This is a developer tool, not a runtime module: it lives in ``tools/`` (NOT in the wheel, not under ``src``). A repository that wants
it copies ``tools/__init__.py`` and ``tools/mutation_runner.py`` byte for byte (the files and their sha256 values are listed in
``tests/fixtures/mutation_manifest.json``); the tool imports only ``hadavin_sdk.testing.mutation``. It runs a subprocess on caller-chosen trees, so the mutant file is found by LISTING the
tree (``_locate``: the caller's string is compared with the listed names and never joined to a path), every other path is checked to
stay inside its tree (``_inside``: a ``..`` part or an absolute path is a ``ValueError``), a path that starts with ``-`` or ``@`` is refused
everywhere (``_plain_operand``: pytest would read it as an option or as an argument file, also after ``--``; ``./name`` is the way to write it),
a relative symlink of the snapshot that points outside the tree is refused (``_refuse_links_out``), a Windows junction (a folder link that ``shutil.copytree`` follows and copies as a real folder)
in ``src`` or in a fixture folder, or one of those folders itself or a part of its path, is refused before the copy (``_refuse_junctions``; ``os.path.isjunction``, Python 3.12 and later, where it is always False off Windows), and every pytest run has a timeout, and a timeout kills the whole process tree of the run.

The limit on names: a path may not contain ':' (a Windows drive or an NTFS stream name), so a file or folder whose name holds a colon cannot be named to this tool at all, on any system.

Limits, stated plainly. The tree kill reaches the processes that stay in the run's process group (POSIX) or the parent chain
(Windows ``taskkill /T``). A test or mutant that starts a process in a NEW session (``setsid``, ``start_new_session=True``) or, on
Windows, a process whose parent has already ended, escapes it. The mutant runner does not use a Windows Job Object (one would
reach those processes). After a normal exit the group is killed once more, so a leftover background process of a finished run
does not outlive it (POSIX only; on Windows nothing is killed after a normal exit: the parent is gone, ``taskkill /T`` cannot
find the children, and its pid may already belong to an unrelated process).

A SIGTERM or SIGHUP sent to the process that runs ``run_mutants`` (POSIX, main thread; a signal that was ignored on entry stays
ignored: SIGHUP under ``nohup``, or a SIGTERM that the parent set to ignore) is turned into ``SystemExit(128 + signal number)`` for
the length of the call, so the same cleanup as for Ctrl-C runs: the pytest tree is killed and the temp folders are removed. The old
handlers are restored afterwards. While the cleanup runs (the tree kill, the removal of the temp folders) and while the child is
being started, a termination signal is remembered and raised when that step is done, and once one signal has ended the run a further
one is remembered and dropped, so a second signal cannot cut the cleanup short. What stays open: a signal in the few bytecodes
between the handler and the cleanup's first line is held only by the "one signal already ended the run" rule, and SIGKILL cannot be
caught, and then the temp folders (``mutants_*`` and ``mutant_ini_*`` in the temp directory) stay.

On POSIX the run's process group is killed while its leader has ended but is NOT yet reaped (``os.waitid`` with ``WNOWAIT``), so the
group id cannot belong to an unrelated process by then. Where ``os.waitid`` does not exist (macOS) the leader is reaped by ``wait``
first and the group kill after a normal exit has the old, tiny pid-reuse risk.

Two more limits of the "reaped by someone else" case (SIGCHLD ignored, or a stray ``wait``). (a) Where ``os.waitid`` does not exist
(macOS) the run is waited for with ``proc.wait``, which cannot tell a reaped child from one that exited with status 0, so such a child
can still read as exit code 0 there: the ``REAPED_ELSEWHERE`` result exists on platforms with ``os.waitid`` only. (b) On the reaped-leader
path the group is NOT killed (its leader's pid may belong to another process by now), so descendants the child left behind are not killed.

Packages that need a ``conftest.py`` or pytest options from a ``pyproject.toml`` / ``pytest.ini`` cannot be run by this tool: pytest
runs with ``--noconftest`` and with an empty ini file on purpose (a planted file in a parent folder is never read).

Dev-tool constants: ``MAX_JUNIT_CHARS`` (in ``testing.mutation``), ``SETUP_TRIES``, ``SETUP_WAIT``, ``WAIT_POLL``, ``TREE_KILL_TIMEOUT``,
``TIMED_OUT``, ``REAPED_ELSEWHERE``, ``CHILD_ENV``, ``CHILD_FIXED_ENV``, ``JUNIT_REFUSED`` and the default run timeout (``DEFAULT_TIMEOUT``, 900.0 seconds) are module constants here and NOT in ``defaults.py``:
the no-hardcoding rule is about product behaviour (names, regions, prices, thresholds a deployment tunes), and this is a developer tool
that ships in no wheel, has no config surface and is copied byte for byte into demos. A caller changes the timeouts by argument.
"""

from __future__ import annotations

import contextlib
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath

from hadavin_sdk.testing.mutation import MAX_JUNIT_CHARS, Verdict, first_failure_junit, judge


@dataclass(frozen=True)
class Mutant:
    name: str
    file: str  # relative to the copied root
    old: str
    new: str
    expect: str  # >= 4 characters: a distinctive fragment of the INTENDED failing assertion line (its message), never of the killer's name
    allow_crash: bool = (
        False  # the intended reaction is a crash (an exception other than an assertion)
    )
    crash_type: str = ""  # REQUIRED with allow_crash: the exception CLASS NAME that must LEAD the first ``E`` line (parsed, not a substring match), or the mutant is not good
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


def _plain_operand(arg: str) -> str:
    """``arg`` may reach the pytest command line as an operand: it must not start with ``-`` (pytest reads it as an option; the ``--``
    marker is not a safe fence, on some Python 3.12 builds argparse still takes the next word after it as an option) or with ``@``
    (pytest reads ``@name`` as a file of further arguments, also after ``--``). A caller who means such a file name writes ``./name``."""
    if arg.startswith(("-", "@")):
        raise ValueError(f"a path may not start with '-' or '@' (write ./name): {arg!r}")
    return arg


def _relative(rel: str) -> str:
    """``rel`` must be a relative path with no ``..`` part (checked as a POSIX and as a Windows path) and must not start with ``-`` or ``@``."""
    if not isinstance(rel, str) or not rel:
        raise ValueError("a path is a non-empty string")
    _plain_operand(rel)
    # a Windows drive, or an NTFS alternate data stream name (``file.py:stream``): neither is a plain relative path
    if ":" in rel:
        raise ValueError(f"a path may not contain ':': {rel!r}")
    for pure in (PurePosixPath(rel), PureWindowsPath(rel)):
        if pure.is_absolute() or pure.anchor or ".." in pure.parts:
            raise ValueError(f"path escapes its tree: {rel!r}")
    return rel


def _inside(base: Path, rel: str) -> Path:
    """``base / rel``, resolved, and proven to lie inside ``base`` (symlinks included)."""
    root = base.resolve()
    path = (root / _relative(rel)).resolve()
    if path == root or not path.is_relative_to(root):
        raise ValueError(f"path escapes its tree: {rel!r}")
    return path


_IS_WINDOWS = (
    os.name == "nt"
)  # one place to ask (tests set it to check the Windows branch of the tree kill on any system)
DEFAULT_TIMEOUT = 900.0  # seconds one pytest run may take (a 15-minute ceiling for the slowest killer); override by argument
REAPED_ELSEWHERE = -1001  # returned instead of an exit code when someone else reaped the child first (SIGCHLD ignored, a stray ``wait``): its exit status is lost and ``Popen`` would report 0, which the judge must never read as a pass or a fail
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


def _taskkill() -> str:
    """taskkill.exe by its full path under %SystemRoot%\\System32, not by a PATH search (a planted taskkill in a work folder is not run)."""
    root = os.environ.get("SystemRoot") or os.environ.get("SYSTEMROOT") or r"C:\Windows"
    return str(Path(root) / "System32" / "taskkill.exe")


WAIT_POLL = (
    0.05  # seconds between two looks at a running child (POSIX ``os.waitid`` has no timeout)
)
TREE_KILL_TIMEOUT = 60.0  # seconds ``taskkill`` may take before the child itself is killed anyway


def _leading_class(first: str) -> str:
    """The exception class name that starts a pytest ``E`` line (``E   demo.fakes.AuditWriteError: text`` gives ``AuditWriteError``;
    a name that only CONTAINS the declared one, or that appears later in the text, does not match it). The ``E`` marker is a letter
    followed by spaces: a class such as ``EOFError`` keeps its first letter, and a line with no marker (a message fallback) is read as is."""
    head = re.sub(r"^E\s+", "", first.strip()).split(":", 1)[0].strip()
    return head.rsplit(".", 1)[-1]


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


class _ReapedElsewhere(Exception):
    """The child ended but another waiter reaped it, so its exit status is unknown (``Popen`` itself would call it 0)."""


def _pytest(cwd: Path, tests: Sequence[str], junit: Path, timeout: float) -> int:
    # an ALLOWLIST, not os.environ: a mutant run must not see a database DSN, a token or any other secret of the caller; PYTHONPATH also holds the tree root (tests may import tools.*)
    for operand in tests:  # the one place the caller's strings reach the argv: refuse here too, not only where the paths are first checked
        _plain_operand(operand)
    env = {k: os.environ[k] for k in CHILD_ENV if k in os.environ}
    env.update(CHILD_FIXED_ENV)
    env["PYTHONPATH"] = os.pathsep.join([str(cwd / "src"), str(cwd)])
    # an EMPTY ini file inside the copy is the config file and the copy is the rootdir: a planted pytest.ini, tox.ini, setup.cfg or
    # pyproject.toml in a parent folder (the shared temp folder, for one) is never picked up
    # the ini file lives in a private temp folder of its own, never in the caller's working folder
    ini_dir: Path | None = None
    proc: subprocess.Popen[bytes] | None = None
    try:
        with _signals_held():
            ini_dir = Path(tempfile.mkdtemp(prefix="mutant_ini_"))
        ini = ini_dir / "mutant_run.ini"
        ini.write_text("", encoding="utf-8")
        cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--noconftest", "-x", "-c", str(ini), f"--rootdir={cwd}", f"--junitxml={junit}", *tests]  # fmt: skip
        # own process group (POSIX session / Windows group): on a timeout the whole tree dies, not only pytest (a test may have started psql or a server)
        own = (
            {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
            if _IS_WINDOWS
            else {"start_new_session": True}
        )
        # a termination signal during the start is held until ``proc`` is known, then raised inside this ``try``: the child is killed
        with _signals_held():
            # S603 stays a listed exception: the argument list holds the caller's test paths and the junit path, so ruff cannot see it as a literal. Fixed argv (our own interpreter), no shell, caller strings only as pytest operands that ``_plain_operand`` has checked
            proc = subprocess.Popen(  # noqa: S603
                cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **own  # type: ignore[call-overload]
            )  # fmt: skip
        try:
            _wait_unreaped(proc, timeout)
        except subprocess.TimeoutExpired:
            _kill_tree(proc)
            # a mutant that loops forever is reported, never allowed to hang the run
            return TIMED_OUT
        except _ReapedElsewhere:
            return REAPED_ELSEWHERE  # ``proc`` knows it has ended (poll), so there is no group to signal and nothing to kill
        # a normal exit can leave a background process of the run behind: on POSIX it is killed too. Not on Windows: the parent is
        # gone, taskkill /T finds no children, and the pid may already belong to an unrelated process
        if not _IS_WINDOWS:
            _kill_tree(proc)
        return proc.wait()
    except BaseException:  # Ctrl-C (KeyboardInterrupt) or any other exit while waiting: never leave a spinning mutant behind
        if proc is not None and proc.returncode is None:
            _kill_tree(proc)
        raise
    finally:
        with _signals_held():
            if ini_dir is not None:
                shutil.rmtree(ini_dir, ignore_errors=True)


def _wait_unreaped(proc: subprocess.Popen[bytes], timeout: float) -> None:
    """Return when ``proc`` has ended; raise ``subprocess.TimeoutExpired`` after ``timeout`` seconds. On POSIX the ended leader is NOT
    reaped (``os.waitid`` with ``WNOWAIT``, polled), so the later group kill cannot hit a reused pid; ``_kill_tree`` reaps it. If someone
    else reaped it first (SIGCHLD ignored) its exit status is gone: ``proc`` is told it has ended, and ``_ReapedElsewhere`` is raised.
    Windows,
    and a POSIX without ``os.waitid`` (macOS): ``proc.wait``, which reaps. Tests patch this function to steer the wait."""
    if _IS_WINDOWS or not hasattr(os, "waitid"):
        proc.wait(timeout=timeout)
        return
    deadline = time.monotonic() + timeout
    while True:
        try:
            if os.waitid(os.P_PID, proc.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None:
                return
        except ChildProcessError:  # someone else reaped it already (SIGCHLD ignored): let ``proc`` learn it, or ``_kill_tree`` would signal a reaped group
            proc.poll()  # sets returncode (0, a guess) so ``_kill_tree`` will not signal a reaped group
            raise _ReapedElsewhere from None
        left = deadline - time.monotonic()
        if left <= 0:
            raise subprocess.TimeoutExpired(proc.args, timeout)
        time.sleep(min(WAIT_POLL, left))


def _kill_tree(proc: subprocess.Popen[bytes]) -> None:
    """Kill ``proc`` and everything it started (POSIX: its process group; Windows: ``taskkill /T``). A failing tree kill (no ``taskkill``
    on the PATH, its own timeout, ``PermissionError`` from ``killpg``) never skips the kill of the child itself. The group is not
    killed when the leader was already reaped (its pid may be someone else's by now), except where ``os.waitid`` is missing. A
    termination signal during the kill is held until it is done."""
    with _signals_held():
        try:
            if _IS_WINDOWS:
                # S603 stays a listed exception: the pid is our own child's, but the list is not a literal to ruff. Fixed argv, no shell
                subprocess.run(  # noqa: S603
                    [_taskkill(), "/F", "/T", "/PID", str(proc.pid)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False, timeout=TREE_KILL_TIMEOUT,
                )  # fmt: skip
            elif proc.returncode is None or not hasattr(os, "waitid"):
                os.killpg(proc.pid, signal.SIGKILL)
        # ProcessLookupError and PermissionError are OSErrors
        except (OSError, subprocess.TimeoutExpired):
            pass
        finally:
            proc.kill()  # the child itself, always
            proc.wait()


# the signals that end a run like Ctrl-C does (POSIX; SIGHUP does not exist on Windows)
_TERMINATING = ("SIGTERM", "SIGHUP")
# State of the termination handling. Only the main thread changes it (the handlers run there, and ``_signals_held`` does nothing in
# another thread): ``depth`` counts the steps that must not be cut short, ``pending`` is the first signal that arrived during one,
# ``ended`` says that a signal has already ended the run (every later one is remembered and dropped: the cleanup is under way),
# ``active`` says that a ``run_mutants`` call of this thread is under way (one at a time: the counters are shared, see ``run_mutants``).
_SIGNALS = {"depth": 0, "pending": 0, "ended": 0, "active": 0}


def _signals_active() -> bool:
    return not _IS_WINDOWS and threading.current_thread() is threading.main_thread()


@contextlib.contextmanager
def _signals_held() -> Iterator[None]:
    """POSIX main thread: a termination signal that arrives inside the block does not raise there; the first one is raised as
    ``SystemExit`` when the outermost block ends (unless a signal has already ended the run). Used around the start of the child, the
    tree kill and the removal of temp folders. Elsewhere it changes nothing."""
    if not _signals_active():
        yield
        return
    _SIGNALS["depth"] += 1
    try:
        yield
    finally:
        _SIGNALS["depth"] -= 1
        if _SIGNALS["depth"] == 0 and _SIGNALS["pending"]:
            number, _SIGNALS["pending"] = _SIGNALS["pending"], 0
            if not _SIGNALS["ended"]:
                _SIGNALS["ended"] = 1
                raise SystemExit(128 + number)


@contextlib.contextmanager
def _terminations_raise() -> Iterator[None]:
    """POSIX main thread: SIGTERM and SIGHUP raise ``SystemExit(128 + signal number)`` inside the block, so the cleanup in ``finally`` and in
    ``_pytest`` runs (a stopped runner would otherwise leave the pytest tree and the temp folders behind). The old handlers are restored;
    a signal that was ignored on entry (``nohup``) stays ignored. Elsewhere (Windows, another thread) it changes nothing."""
    if not _signals_active():
        yield
        return
    # refused BEFORE anything is changed: the counters of the outer call stay as they are
    if _SIGNALS["active"]:
        raise RuntimeError(
            "run_mutants is not re-entrant: a second call inside a running one is refused"
        )

    def stop(signum: int, _frame: object) -> None:
        if _SIGNALS["depth"] or _SIGNALS["ended"]:
            _SIGNALS["pending"] = _SIGNALS["pending"] or signum
            return
        _SIGNALS["ended"] = 1
        raise SystemExit(128 + signum)

    previous: dict[int, object] = {}
    _SIGNALS.update(depth=0, pending=0, ended=0, active=1)
    try:
        for name in _TERMINATING:
            sig = getattr(signal, name, None)
            if sig is None or signal.getsignal(sig) is signal.SIG_IGN:
                continue
            previous[sig] = signal.signal(sig, stop)
        yield
    finally:
        for sig, old in previous.items():
            signal.signal(sig, old if old is not None else signal.SIG_DFL)  # type: ignore[arg-type]
        _SIGNALS.update(depth=0, pending=0, ended=0, active=0)


def run_mutants(
    root: Path,
    mutants: Iterable[Mutant],
    tests: Sequence[str],
    *,
    extra_dirs: Sequence[str] = ("tests/fixtures",),
    extra_files: Sequence[str] = (),
    only: Sequence[str] = (),
    timeout: float = DEFAULT_TIMEOUT,
    baseline_timeout: float | None = None,
    on_result: Callable[[tuple[str, Verdict, str, bool]], None] | None = None,
    first_lines: dict[str, str] | None = None,
) -> list[tuple[str, Verdict, str, bool]]:
    """(name, verdict, failing test id, good). Raises ``RuntimeError`` if the unmutated copy fails or times out; a mutant whose temp copy cannot be built (after ``SETUP_TRIES`` tries) is ``(name, Verdict.ERROR, "SETUP FAILED: <error class>", False)``; a mutant run that exceeds
    ``timeout`` seconds is ``(name, Verdict.ERROR, "TIMEOUT", False)``. The unmutated baseline run gets ``baseline_timeout`` (default: ``timeout``; 0 is a real, immediate timeout and not "unset"),
    so a test can use a short mutant timeout without failing a slow baseline. ``on_result`` is called with each result as soon as that mutant
    finishes (stream it and a timeout of the whole run still leaves a kill list). ``extra_files`` are single files outside ``tests`` (for
    example ``CHANGELOG.md``, read by a test from the repo root) copied into the temp tree when they exist; they are never passed to pytest.
    Every ``tests``, ``extra_dirs`` and ``extra_files`` entry and every mutant file
    must name a file inside its tree (``ValueError``). ``first_lines``, if given, is emptied at the start and then filled with the first ``E`` line
    of each judged kill (mutant name -> line; diagnostics, and what ``crash_type`` is checked against): it belongs to this call, so two
    runs in two threads never share it. A SIGTERM or SIGHUP during the call ends it like Ctrl-C (see the module docstring).
    NOT re-entrant: the signal state is one module-level record, so on POSIX in the main thread a ``run_mutants`` call made while another is
    running in the same thread (from ``on_result``, say) raises ``RuntimeError`` and leaves the outer call untouched. Calls in other threads do not
    share that state, and each is handled by its own thread (the signal handling is then off, as the module docstring says)."""
    with _terminations_raise():
        return _run_mutants(
            root, mutants, tests, extra_dirs, only, timeout, baseline_timeout, on_result,
            {} if first_lines is None else first_lines, tuple(extra_files),
        )  # fmt: skip


def _refuse_links_out(base: Path) -> None:
    """Refuse a RELATIVE symlink of the snapshot whose target lies outside ``base`` (``ValueError``). The snapshot and every copy of it sit
    side by side in the shared temp folder, so such a link (``../../x`` out of ``src``) would resolve to a neighbour in that folder, not to
    what it meant in the caller's tree. An absolute link keeps its meaning in a copy and stays a link (it is the caller's explicit choice)."""
    real_base = os.path.realpath(base)
    for dirpath, dirs, files in os.walk(base):  # os.walk does not enter a linked folder
        for name in (*dirs, *files):
            link = os.path.join(dirpath, name)
            if not os.path.islink(link):
                continue
            target = os.readlink(link)
            if os.path.isabs(target):
                continue
            hop = os.path.normpath(os.path.join(os.path.realpath(dirpath), target))
            if os.path.commonpath([real_base, hop]) != real_base:
                raise ValueError(
                    f"a relative link points outside the tree: {os.path.relpath(link, base)!r}"
                )


def _refuse_junctions(root: Path, rel: str) -> None:
    """Refuse a Windows junction at ``root / rel`` (``ValueError``): the folder itself, any part of the path ``rel`` (``tests`` in
    ``tests/fixtures``) and anything below it. ``shutil.copytree(symlinks=True)`` does not see a junction as a link (Python
    3.12 ``islink`` is False for it), follows it and copies the target as a real folder, so the snapshot would hold files from outside the
    tree. Looked at in the CALLER's tree before the copy: afterwards nothing tells the copy from a real folder. ``os.path.isjunction`` exists
    from Python 3.12 (always False off Windows); where it is missing there is nothing to ask."""
    isjunction = getattr(os.path, "isjunction", None)
    if isjunction is None:
        return
    here = root
    for part in re.split(r"[\\/]", rel):
        here = here / part
        if isjunction(here):
            raise ValueError(f"a junction is not followed: {rel!r} (at {part!r})")
    for dirpath, dirs, _files in os.walk(here):
        for name in dirs:
            if isjunction(os.path.join(dirpath, name)):
                raise ValueError(
                    f"a junction is not followed: {os.path.relpath(os.path.join(dirpath, name), root)!r}"
                )


def _run_mutants(
    root: Path,
    mutants: Iterable[Mutant],
    tests: Sequence[str],
    extra_dirs: Sequence[str],
    only: Sequence[str],
    timeout: float,
    baseline_timeout: float | None,
    on_result: Callable[[tuple[str, Verdict, str, bool]], None] | None,
    first_lines: dict[str, str],
    extra_files: Sequence[str] = (),
) -> list[tuple[str, Verdict, str, bool]]:
    first_lines.clear()  # the diagnostics of an earlier run must not answer for this one
    root = Path(root)
    mutants = list(mutants)
    for t in (*tests, *extra_dirs, *extra_files):
        _relative(t)
    for m in mutants:  # before anything runs: a bad `test_file` must not surface after earlier mutants were already run
        if m.test_file and m.test_file not in tests:
            raise ValueError(
                f"mutant {m.name!r}: test_file {m.test_file!r} is not one of the copied tests"
            )
    # both folders are named from ONE mkdtemp, made inside the try below (held against a signal), so no signal can leave ``tmp`` alone behind
    made: list[Path] = []
    tmp: Path
    snap: Path

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
        for f in extra_files:
            if _inside(snap, f).is_file():
                dst = _inside(tmp, f)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(_inside(snap, f), dst)

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

    # the try starts right after the first temp folder exists: a refusal (a path through a link out of the tree, a missing ``src``)
    # or a signal at any later point leaves no temp folder behind
    try:
        with _signals_held():
            made.append(Path(tempfile.mkdtemp(prefix="mutants_")))
        tmp = made[0]
        snap = tmp.with_name(tmp.name + "_snap")
        snap.mkdir()
        # ONE snapshot of the tree at the start: every mutant copy is made from it, so an edit of ``root`` while the run is going (a
        # developer saving a file, a second tool) can never leak into a later mutant
        _refuse_junctions(root, "src")
        shutil.copytree(
            root / "src", snap / "src", symlinks=True, ignore=shutil.ignore_patterns("__pycache__")
        )  # links stay links (never followed out of the tree)
        for t in tests:
            dst = _inside(snap, t)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(_inside(root, t), dst)
        for d in extra_dirs:
            if _inside(root, d).exists():
                _refuse_junctions(root, d)
                shutil.copytree(
                    _inside(root, d), _inside(snap, d), symlinks=True, dirs_exist_ok=True
                )
        for f in extra_files:
            if _inside(root, f).is_file():
                dst = _inside(snap, f)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(_inside(root, f), dst)
        _refuse_links_out(snap)
        fresh()
        base_rc = _pytest(
            tmp, tests, tmp / "base.xml", timeout if baseline_timeout is None else baseline_timeout
        )
        if base_rc == REAPED_ELSEWHERE:
            raise RuntimeError(
                "the baseline run was reaped by someone else: its exit status is unknown"
            )
        if base_rc != 0:
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
            # the exit status is lost: an error row, never a pass or a kill
            if rc == REAPED_ELSEWHERE:
                emit((m.name, Verdict.ERROR, "REAPED ELSEWHERE", False))
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
            first_lines[m.name] = first
            declared = _leading_class(first) == m.crash_type
            crash_ok = v is Verdict.CRASH and m.allow_crash and declared
            emit((m.name, v, test_id, v is Verdict.KILLED or crash_ok))
    finally:
        with _signals_held():  # a signal is raised after the removal
            for folder in made:
                shutil.rmtree(folder, ignore_errors=True)
                shutil.rmtree(folder.with_name(folder.name + "_snap"), ignore_errors=True)
    return out
