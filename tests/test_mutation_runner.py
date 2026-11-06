"""Tests of the mutation runner (``tools/mutation_runner.py``) and the mutation judge (``hadavin_sdk.testing.mutation``).

Moved from the PR #50 head (21 tests, each of which targets one guard of the runner or judge; the mutants that revert those
guards are in ``tests/mutation_runner_mutants.py``, and the meta-tests that check that list are in
``tests/test_mutation_runner_meta.py``). No test here talks to a network or a model; every tree is built in ``tmp_path``
from made-up files.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from tools import mutation_runner as mr
from tools.mutation_runner import Mutant, run_mutants

from hadavin_sdk.testing import mutation as mutmod
from hadavin_sdk.testing.mutation import Verdict, first_failure, first_failure_junit, judge

FIX = Path(__file__).parent / "fixtures"


# ---- helpers of the tests below ---------------------------------------------------------------------------------------------


def _pk_tree(tmp_path, test_body):
    root = tmp_path / "pkg"
    (root / "src" / "pk").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "src" / "pk" / "__init__.py").write_text("", encoding="utf-8")
    (root / "src" / "pk" / "core.py").write_text(
        "def go(flag):\n    return flag\n", encoding="utf-8"
    )
    (root / "tests" / "test_core.py").write_text(test_body, encoding="utf-8")
    return root


def _raising_tree(tmp_path):
    return _pk_tree(
        tmp_path, "from pk.core import go\n\ndef test_a():\n    assert go(True) is True\n"
    )


def _copytree_failing(monkeypatch, fail_calls):
    """Make ``shutil.copytree`` raise ``PermissionError`` on the numbered calls (1-based) made by the runner."""
    import shutil

    from tools import mutation_runner

    real, calls = shutil.copytree, []

    def flaky(*a, **kw):
        dst = Path(
            a[1]
        )  # shutil.copytree calls itself for every sub-folder: count only the runner's own copy of src
        if (
            dst.name == "src"
            and dst.parent.name.startswith("mutants_")
            and "snap" not in dst.parent.name
        ):
            calls.append(1)
        if len(calls) in fail_calls and calls and dst.name == "src":
            raise PermissionError("file in use")
        return real(*a, **kw)

    monkeypatch.setattr(mutation_runner.shutil, "copytree", flaky)
    monkeypatch.setattr(mutation_runner, "SETUP_WAIT", 0.0)


_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
_STILL_ACTIVE = 259  # the exit code GetExitCodeProcess reports for a process that has not ended
_ERROR_ACCESS_DENIED = 5


def _pid_alive_windows(pid):
    """Windows: ``os.kill(pid, 0)`` is not a probe there (it raises WinError 87), so ask for a limited handle to the
    process and read its exit code. No handle with "access denied" means it exists and is not ours; any other
    refusal (87, invalid parameter) means there is no such process."""
    import ctypes

    try:
        return _pid_alive_ctypes(ctypes, pid)
    except (OSError, AttributeError):
        return _pid_alive_tasklist(
            pid
        )  # the system library could not be used: ask ``tasklist`` instead


def _pid_alive_ctypes(ctypes, pid):
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.restype = ctypes.c_void_p
    kernel32.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    kernel32.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = kernel32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, 0, pid)
    if not handle:
        return ctypes.get_last_error() == _ERROR_ACCESS_DENIED
    try:
        code = ctypes.c_ulong(0)
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
            raise OSError(f"GetExitCodeProcess failed, error {ctypes.get_last_error()}")
        return code.value == _STILL_ACTIVE
    finally:
        kernel32.CloseHandle(handle)


def _pid_alive_tasklist(pid):
    """Fallback on Windows: ``tasklist`` by its full path under %SystemRoot%\\System32 (not a PATH search) lists the pid if it runs."""
    import subprocess

    root = os.environ.get("SystemRoot") or os.environ.get("SYSTEMROOT") or r"C:\Windows"
    exe = str(Path(root) / "System32" / "tasklist.exe")
    done = subprocess.run(  # noqa: S603  # our own fixed argv, no shell, a pid we made
        [exe, "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    return f',"{pid}",' in done.stdout


def _force_kill(pid):
    """Cleanup of a leftover process (a test that failed halfway must not leave a sleeping process behind)."""
    import subprocess

    if sys.platform == "win32":
        subprocess.run(  # noqa: S603  # our own fixed argv, no shell
            [mr._taskkill(), "/F", "/T", "/PID", str(pid)],
            capture_output=True,
            check=False,
            timeout=60,
        )
        return
    import signal

    try:
        os.kill(pid, signal.SIGKILL)
    except OSError:
        pass


def _pid_alive(pid):
    """True while ``pid`` is a running process. A killed grandchild that nobody has waited for is a zombie
    (state ``Z`` in ``/proc/<pid>/stat``); a zombie counts as dead."""
    if sys.platform == "win32":
        return _pid_alive_windows(pid)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # it exists, it is only not ours
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    except OSError:
        return True  # no /proc here: the signal check above is all there is
    return stat.rpartition(")")[2].split()[0] != "Z"


def _symlink_or_skip(target, link, **kwargs):
    """``os.symlink``, but skip the test ONLY on Windows and only when the account lacks the privilege (error 1314). On any
    other system, or for any other error, a failure to make a link is a failure of the test."""
    try:
        os.symlink(target, link, **kwargs)
    except OSError as exc:
        if sys.platform == "win32" and getattr(exc, "winerror", None) == 1314:
            pytest.skip(f"creating a symlink needs a privilege this account lacks ({exc})")
        raise


def _dir_link(target, link):
    """A folder link out of a tree. On Windows a junction (no privilege needed); elsewhere a symlink."""
    if sys.platform == "win32":
        import _winapi

        _winapi.CreateJunction(str(target), str(link))
    else:
        _symlink_or_skip(target, link, target_is_directory=True)


def _must_refuse(label, call, *args, match="", **kwargs):
    """Call ``call``; it must raise ``ValueError``. Otherwise the test fails with ``<label>: was not refused`` as the FIRST
    assertion line, so a mutation run can tell which guard was removed."""
    try:
        call(*args, **kwargs)
    except ValueError as exc:
        assert match in str(exc), f"{label}: refused with another message: {exc}"
        return
    raise AssertionError(f"{label}: was not refused")


def _baseline_passes(root):
    """True when a run with no mutants finds the unmutated copy of ``root`` passing (``run_mutants`` raises ``RuntimeError`` if not)."""
    try:
        return run_mutants(root, [], ["tests/test_core.py"], extra_dirs=(), timeout=120) == []
    except RuntimeError:
        return False


# ---- mutation judge and runner ------------------------------------------------------------------------------------------


def test_mutation_judge_verdicts():
    a = "E   AssertionError: assert 1 == 2"
    assert judge(1, "t.py::a", a) == Verdict.KILLED and judge(0, "t.py::a", a) == Verdict.SURVIVED
    assert judge(5, "t.py::a", a) == Verdict.NO_TESTS and judge(2, "t.py::a", a) == Verdict.ERROR
    assert (
        judge(1, "t.py::test_aaaa", a, expect="test_aaaa") == Verdict.KILLED
        and judge(1, "t.py::a", a, expect="zzzz") == Verdict.WRONG_REASON
    )
    _must_refuse(
        "a one-letter expect was accepted by the judge", judge, 1, "t.py::a", a, expect="a"
    )  # a one-letter fragment matches almost anything
    assert judge(1, "t.py::a", a, pinned="t.py::b") == Verdict.OTHER_TEST
    for line in (
        "E   KeyError: 'x'",
        "E   TypeError: boom",
        "E   RuntimeError: x",
        "E   ImportError: no",
        "E   demo.fakes.AuditWriteError: audit write failed",
        "E   Failed: custom",
    ):
        assert judge(1, "t.py::a", line) == Verdict.CRASH, (
            f"an exception line counted as a kill: {line}"
        )
    assert judge(1, "t.py::a", "E   Failed: DID NOT RAISE <class 'TypeError'>") == Verdict.KILLED
    internal = "E   AssertionError: assert 'denied:internal_error' == 'queued'"
    assert judge(1, "t.py::a", internal) == Verdict.KILLED
    assert (
        judge(
            1, "t.py::a", internal, crash_markers=[re.compile(r"assert 'denied:internal_error' ==")]
        )
        == Verdict.CRASH
    ), "a crash marker was ignored"
    out = "FAILED tests/t.py::test_x[1] - assert 1\nE   AssertionError: assert 1 == 2\n"
    assert first_failure(out) == ("tests/t.py::test_x[1]", "E   AssertionError: assert 1 == 2")
    xml = (
        '<testsuite><testcase classname="tests.t" name="test_ok"/><testcase classname="tests.t" name="test_x[a - b | c]">'
        '<failure message="boom">def f():\nE   AssertionError: assert 1 == 2\n</failure></testcase></testsuite>'
    )
    assert first_failure_junit(xml) == (
        "tests/t::test_x[a - b | c]",
        "E   AssertionError: assert 1 == 2",
    )  # ids with ' - ' and ' | ' are intact


def test_the_runner_kills_a_mutant_of_a_tiny_package(tmp_path):
    (tmp_path / "src" / "pkg").mkdir(parents=True)
    (tmp_path / "src" / "pkg" / "__init__.py").write_text(
        "def guard(x):\n    if x < 0:\n        raise ValueError('negative')\n    return x\n",
        encoding="utf-8",
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_g.py").write_text(
        "import pytest\nfrom pkg import guard\n\ndef test_guard_refuses_negative():\n    with pytest.raises(ValueError):\n        guard(-1)\n",
        encoding="utf-8",
    )
    res = run_mutants(
        tmp_path,
        [Mutant("guard removed", "src/pkg/__init__.py", "if x < 0:", "if False:", "test_guard_refuses_negative"),
         Mutant("no-op mutant", "src/pkg/__init__.py", "return x", "return x  # same", "test_guard_refuses_negative"),
         Mutant("crash mutant", "src/pkg/__init__.py", "if x < 0:", "if 1 / 0:", "test_guard_refuses_negative"),
         Mutant("missing snippet", "src/pkg/__init__.py", "nope", "x", "test_guard")],
        ["tests/test_g.py"],
    )  # fmt: skip
    by = {n: (v, good) for n, v, _, good in res}
    assert (
        by["guard removed"] == (Verdict.KILLED, True)
        and by["no-op mutant"][1] is False
        and by["missing snippet"][1] is False
    ), f"a mutant of a tiny package was not killed as expected: {by}"
    assert by["crash mutant"] == (Verdict.CRASH, False)  # an exception is not an assertion kill


def test_a_mutant_path_that_is_absolute_or_names_a_drive_is_refused():
    for bad in ("/etc/passwd", "C:\\x.py", "\\\\host\\share\\x.py", ""):
        _must_refuse(
            f"an absolute, drive or empty mutant path {bad!r}",
            Mutant,
            "name",
            bad,
            "a",
            "b",
            "test_x_assertion",
        )


def test_a_mutant_path_with_a_dotdot_part_is_refused():
    for bad in ("../x.py", "a/../../x.py", "..\\x.py"):
        _must_refuse(
            f"a mutant path with a dotdot part {bad!r}",
            Mutant,
            "name",
            bad,
            "a",
            "b",
            "test_x_assertion",
        )


def test_a_mutant_path_with_a_stream_name_is_refused():
    _must_refuse(
        "a mutant path with a stream name", Mutant, "name", "a.py:stream", "a", "b", "test_x"
    )
    assert (
        Mutant("name", "src/a.py", "a", "b", "test_x").file == "src/a.py"
    )  # a plain relative path is fine


def test_a_mutant_with_a_short_expect_is_refused():
    _must_refuse("an expect of three characters", Mutant, "name", "a.py", "a", "b", "abc")


def test_inside_refuses_a_path_through_a_link_out_of_the_tree(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    _must_refuse("a plain dotdot path", mr._inside, base, "../outside.txt")
    assert mr._inside(base, "src/a.py").is_relative_to(base.resolve())
    link = base / "link"
    _dir_link(tmp_path, link)
    assert link.exists(), "the test could not create a link out of the tree"
    _must_refuse("a path through a link out of the tree", mr._inside, base, "link/outside.txt")


def test_locate_does_not_list_a_file_through_a_link_out_of_the_tree(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    (base / "ok.py").write_text("x", encoding="utf-8")
    assert mr._locate(base, "ok.py") == base / "ok.py"
    (tmp_path / "real.txt").write_text("x", encoding="utf-8")
    _dir_link(tmp_path, base / "link")
    _must_refuse("a file listed through a folder link", mr._locate, base, "link/real.txt")
    # A link to a FILE is listed (``os.walk`` lists it among the files), so only the real-path check keeps it out; the folder link
    # above never reaches that check on Linux, because ``os.walk`` does not enter it. On Windows a file link needs a privilege:
    # the test skips there, and only there, when the account lacks it.
    _symlink_or_skip(tmp_path / "real.txt", base / "file_link.txt")
    _must_refuse("a file link out of the tree was listed", mr._locate, base, "file_link.txt")


def test_the_runner_checks_a_forged_mutant_path_again(tmp_path):
    outside = tmp_path / "outside.txt"
    victim = tmp_path / "victim.txt"
    victim.write_text("before", encoding="utf-8")
    forged = Mutant("forged", "src/a.py", "before", "after", "test_x_assertion")
    object.__setattr__(
        forged, "file", str(victim)
    )  # a Mutant built around __post_init__: the runner checks again
    pkg = tmp_path / "pkg0"
    (pkg / "src").mkdir(parents=True)
    (pkg / "tests").mkdir()
    (pkg / "tests" / "test_a.py").write_text("def test_a():\n    assert True\n", encoding="utf-8")
    _must_refuse(
        "a forged mutant path (outside the tree)",
        run_mutants,
        pkg,
        [forged],
        ["tests/test_a.py"],
        extra_dirs=(),
    )
    assert victim.read_text(encoding="utf-8") == "before", "the file outside the tree was changed"
    assert not outside.exists()


def test_run_mutants_refuses_test_and_fixture_paths_that_leave_the_tree(tmp_path):
    root = tmp_path / "pkg"
    (root / "src").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "tests" / "test_a.py").write_text("def test_a():\n    assert True\n", encoding="utf-8")
    for tests, extra in (
        (["../x.py"], ()),
        (["tests/test_a.py"], ("../x",)),
        (["/abs/test.py"], ()),
    ):
        _must_refuse(f"tests {tests} extra {extra}", run_mutants, root, [], tests, extra_dirs=extra)


def test_the_runner_children_see_an_allowlisted_environment_only(tmp_path, monkeypatch):
    monkeypatch.setenv("HADAVIN_TEST_PG_DSN", "postgresql://u:p@h/db")  # the real caller's secret
    monkeypatch.setenv("SOME_API_TOKEN", "tok")
    root = _pk_tree(
        tmp_path,
        "import os\n\ndef test_no_secret_reaches_the_child():\n"
        "    assert 'HADAVIN_TEST_PG_DSN' not in os.environ\n"
        "    assert 'SOME_API_TOKEN' not in os.environ\n"
        "    assert 'PATH' in os.environ\n"
        "    assert os.environ.get('PYTHONNOUSERSITE') == '1'\n",
    )
    # the unmutated baseline must pass: it fails (RuntimeError) while the child inherits os.environ
    assert _baseline_passes(root), "a secret of the caller reached the child process"


def test_an_edit_of_the_tree_during_the_run_does_not_leak_into_a_later_mutant(tmp_path):
    root = _pk_tree(
        tmp_path,
        "from pk.core import go\n\ndef test_go_is_true():\n    assert go(True) is True\n",
    )
    m1 = Mutant("one", "src/pk/core.py", "return flag", "return False", "test_go_is_true")
    m2 = Mutant("two", "src/pk/core.py", "return flag", "return not flag", "test_go_is_true")

    def edit_root_after_first(row):  # a second tool / a save while the run is going
        (root / "src" / "pk" / "core.py").write_text(
            "def go(flag):\n    return None\n", encoding="utf-8"
        )

    out = run_mutants(
        root,
        [m1, m2],
        ["tests/test_core.py"],
        extra_dirs=(),
        timeout=120,
        on_result=edit_root_after_first,
    )
    assert [(n, v) for n, v, _t, _g in out] == [("one", Verdict.KILLED), ("two", Verdict.KILLED)], (
        f"an edit of the tree during the run leaked into a later mutant: {out}"
    )


def test_a_mutant_that_loops_forever_times_out_instead_of_hanging_the_run(tmp_path):
    root = tmp_path / "pkg"
    (root / "src" / "pk").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "src" / "pk" / "__init__.py").write_text("FLAG = False\n", encoding="utf-8")
    (root / "src" / "pk" / "core.py").write_text(
        "def go(flag):\n    return flag\n", encoding="utf-8"
    )
    (root / "tests" / "test_core.py").write_text(
        "from pk.core import go\n\ndef test_go_is_true():\n    assert go(True) is True\n",
        encoding="utf-8",
    )
    hang = Mutant(
        "hang", "src/pk/core.py", "return flag", "while True:\n        pass", "test_go_is_true"
    )
    out = run_mutants(
        root, [hang], ["tests/test_core.py"], extra_dirs=(), timeout=6, baseline_timeout=180
    )
    assert out == [("hang", Verdict.ERROR, "TIMEOUT", False)], (
        f"a timeout was not reported as one: {out}"
    )


def test_a_test_path_that_starts_with_a_dash_is_a_path_not_a_pytest_option(tmp_path):
    (tmp_path / "test_ok.py").write_text("def test_a():\n    assert True\n", encoding="utf-8")
    assert mr._pytest(tmp_path, ["test_ok.py"], tmp_path / "r2.xml", 60) == 0
    # as a bare option "-x" would collect and pass test_ok.py in the cwd; as an operand it is a missing file
    assert mr._pytest(tmp_path, ["-x"], tmp_path / "r.xml", 60) != 0, (
        "a test path with a dash was taken as a pytest option"
    )


def test_a_failing_tree_kill_still_kills_the_child(monkeypatch):
    import subprocess
    import sys

    def boom(*a, **k):
        raise PermissionError("taskkill")

    def denied(*a, **k):
        raise PermissionError("killpg")

    monkeypatch.setattr(mr.subprocess, "run", boom)
    monkeypatch.setattr(mr.os, "killpg", denied, raising=False)
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(600)"])
    try:
        mr._kill_tree(proc)
        assert proc.poll() is not None
    finally:
        proc.kill()
        proc.wait()


def test_the_baseline_run_gets_its_own_timeout(tmp_path, monkeypatch):
    root = tmp_path / "pkg"
    (root / "src" / "pk").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "src" / "pk" / "core.py").write_text(
        "def go(flag):\n    return flag\n", encoding="utf-8"
    )
    (root / "tests" / "test_core.py").write_text(
        "def test_a():\n    assert True\n", encoding="utf-8"
    )
    seen = []

    def fake(cwd, tests, junit, timeout):
        seen.append(timeout)
        return 0 if len(seen) == 1 else mr.TIMED_OUT

    monkeypatch.setattr(mr, "_pytest", fake)
    mut = Mutant("m", "src/pk/core.py", "return flag", "return not flag", "test_a_x")
    out = run_mutants(
        root, [mut], ["tests/test_core.py"], extra_dirs=(), timeout=7, baseline_timeout=111
    )
    assert seen == [111, 7] and out == [("m", Verdict.ERROR, "TIMEOUT", False)], (
        f"the baseline run did not get its own timeout: {seen}"
    )
    seen.clear()
    run_mutants(root, [mut], ["tests/test_core.py"], extra_dirs=(), timeout=9)
    assert seen == [9, 9]  # the baseline falls back to the mutant timeout


def test_a_baseline_timeout_of_zero_is_not_unset(tmp_path):
    root = _raising_tree(tmp_path)
    try:
        run_mutants(
            root, [], ["tests/test_core.py"], extra_dirs=(), timeout=120, baseline_timeout=0
        )
    except RuntimeError:
        return  # an immediate timeout of the baseline: the unmutated copy "does not pass"
    raise AssertionError("a baseline_timeout of 0 was treated as unset")


def test_the_runner_streams_each_result_and_keeps_a_sigkill_apart_from_a_timeout(
    tmp_path, monkeypatch
):
    assert mr.TIMED_OUT != -9 and mr.TIMED_OUT < -64, (
        "TIMED_OUT equals a process exit status"
    )  # no process exit status can equal it
    root = tmp_path / "pkg"
    (root / "src" / "pk").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "src" / "pk" / "core.py").write_text(
        "def go(flag):\n    return flag\n", encoding="utf-8"
    )
    (root / "tests" / "test_core.py").write_text(
        "def test_a():\n    assert True\n", encoding="utf-8"
    )
    codes = iter(
        [0, -9, mr.TIMED_OUT]
    )  # baseline, a mutant killed by SIGKILL (the OOM killer), a mutant that timed out

    monkeypatch.setattr(mr, "_pytest", lambda cwd, tests, junit, timeout: next(codes))
    muts = [
        Mutant(f"m{i}", "src/pk/core.py", "return flag", "return not flag", "test_a_x")
        for i in range(2)
    ]
    seen, finished = [], []
    mr_run = mr.run_mutants

    def on_result(row):
        seen.append(row[0])
        finished.append(len(seen))  # called once per mutant, in order, before the run returns

    out = mr_run(root, muts, ["tests/test_core.py"], extra_dirs=(), on_result=on_result)
    assert seen == ["m0", "m1"] and finished == [1, 2] and [r[0] for r in out] == seen
    assert (
        out[0][1] is Verdict.ERROR and out[0][2] != "TIMEOUT" and out[0][3] is False
    )  # SIGKILL: an error, not a timeout
    assert out[1] == ("m1", Verdict.ERROR, "TIMEOUT", False)


def _patient_wait(monkeypatch, pidfile, then):
    """Make the runner's own ``proc.wait(timeout=...)`` start only after the child has written ``pidfile`` (it is the
    timeout of the RUN that is under test, not how fast this machine starts a child); then ``then(self, real_wait)``
    decides what that wait does. A child that ends first (the baseline run) is waited for as ever."""
    real_wait = subprocess.Popen.wait

    def wait(self, timeout=None):
        if timeout is not None:
            for _ in range(1200):
                if (
                    pidfile.exists() and pidfile.read_text(encoding="utf-8").strip()
                ) or self.poll() is not None:
                    break
                time.sleep(0.1)
            if self.poll() is None:
                assert pidfile.exists(), "the child never wrote its pid file"
                return then(self, real_wait)
        return real_wait(self, timeout=timeout)

    monkeypatch.setattr(subprocess.Popen, "wait", wait)


def test_a_timeout_kills_the_whole_process_tree_not_only_pytest(tmp_path, monkeypatch):
    root = _pk_tree(
        tmp_path, "from pk.core import go\n\ndef test_go_is_true():\n    assert go(True) is True\n"
    )
    pidfile = tmp_path / "pid.txt"
    body = (
        "import subprocess, sys, time\n"
        "    c = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(600)'])\n"
        f"    open({str(pidfile)!r}, 'w').write(str(c.pid))\n"
        "    time.sleep(600)"
    )
    spawn = Mutant("spawn", "src/pk/core.py", "return flag", body, "test_go_is_true")
    _patient_wait(monkeypatch, pidfile, lambda self, real_wait: real_wait(self, timeout=1))
    pid = None
    try:
        out = run_mutants(
            root, [spawn], ["tests/test_core.py"], extra_dirs=(), timeout=30, baseline_timeout=180
        )
        assert out == [("spawn", Verdict.ERROR, "TIMEOUT", False)]
        pid = int(pidfile.read_text(encoding="utf-8"))
        for _ in range(50):
            if not _pid_alive(pid):
                break
            time.sleep(0.2)
        assert not _pid_alive(pid), "the grandchild survived the timeout"
    finally:
        if pid is None and pidfile.exists() and pidfile.read_text(encoding="utf-8").strip():
            pid = int(pidfile.read_text(encoding="utf-8"))
        if pid is not None:
            _force_kill(pid)


def _spawn_test(tmp_path, body):
    """A folder with one test file ``test_x.py`` holding ``body``; returns the folder."""
    (tmp_path / "test_x.py").write_text(
        "import subprocess, sys, time, os\n\ndef test_x():\n" + body, encoding="utf-8"
    )
    return tmp_path


def test_an_interrupt_while_waiting_kills_the_run_and_is_not_swallowed(tmp_path, monkeypatch):
    pidfile = tmp_path / "pid.txt"
    folder = _spawn_test(
        tmp_path, f"    open({str(pidfile)!r}, 'w').write(str(os.getpid()))\n    time.sleep(25)\n"
    )

    def interrupt(self, real_wait):
        raise KeyboardInterrupt

    _patient_wait(monkeypatch, pidfile, interrupt)
    killed = []
    real_kill = mr._kill_tree
    monkeypatch.setattr(mr, "_kill_tree", lambda proc: (killed.append(proc.pid), real_kill(proc)))
    try:
        with pytest.raises(KeyboardInterrupt):
            mr._pytest(folder, ["test_x.py"], folder / "r.xml", 120)
    finally:
        if pidfile.exists() and pidfile.read_text(encoding="utf-8").strip():
            _force_kill(int(pidfile.read_text(encoding="utf-8")))
    pid = int(pidfile.read_text(encoding="utf-8"))
    assert killed == [pid], "an interrupt while waiting did not kill the run before it propagated"
    assert not _pid_alive(pid)


@pytest.mark.skipif(
    sys.platform == "win32", reason="the parent has ended, so taskkill /T cannot find its children"
)
def test_a_background_process_left_by_a_finished_run_is_killed_too(tmp_path):
    pidfile = tmp_path / "pid.txt"
    folder = _spawn_test(
        tmp_path,
        "    c = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(600)'])\n"
        f"    open({str(pidfile)!r}, 'w').write(str(c.pid))\n",
    )
    pid = None
    try:
        assert mr._pytest(folder, ["test_x.py"], folder / "r.xml", 120) == 0
        pid = int(pidfile.read_text(encoding="utf-8"))
        for _ in range(50):
            if not _pid_alive(pid):
                break
            time.sleep(0.2)
        assert not _pid_alive(pid), "a background process of a finished run was left running"
    finally:
        if pid is None and pidfile.exists() and pidfile.read_text(encoding="utf-8").strip():
            pid = int(pidfile.read_text(encoding="utf-8"))
        if pid is not None:
            _force_kill(pid)


def test_a_pytest_ini_planted_in_a_parent_folder_is_not_picked_up(tmp_path, monkeypatch):
    shared = tmp_path / "shared_temp"
    shared.mkdir()
    (shared / "pytest.ini").write_text(
        "[pytest]\naddopts = -k no_such_test_name\n", encoding="utf-8"
    )
    monkeypatch.setattr(
        tempfile, "tempdir", str(shared)
    )  # the runner's copies are made below this folder
    root = _raising_tree(tmp_path)
    assert _baseline_passes(root), "a pytest.ini planted in a parent folder was picked up"


def test_a_setup_failure_for_one_mutant_is_a_result_row_and_a_blip_is_retried(
    tmp_path, monkeypatch
):
    root = _pk_tree(
        tmp_path, "from pk.core import go\n\ndef test_go_is_true():\n    assert go(True) is True\n"
    )
    a = Mutant("a", "src/pk/core.py", "return flag", "return False", "test_go_is_true")
    b = Mutant("b", "src/pk/core.py", "return flag", "return not flag", "test_go_is_true")
    # call 1 = baseline copy; calls 2..6 = every try for mutant a (SETUP_TRIES = 5)
    _copytree_failing(monkeypatch, set(range(2, 7)))
    out = run_mutants(root, [a, b], ["tests/test_core.py"], extra_dirs=(), timeout=120)
    assert [(n, v, t) for n, v, t, _g in out] == [
        ("a", Verdict.ERROR, "SETUP FAILED: PermissionError"),
        ("b", Verdict.KILLED, out[1][2]),
    ], f"the setup failure of one mutant was not a result row, or a blip was not retried: {out}"
    assert [g for *_x, g in out] == [False, True]
    # a lock that clears after two tries costs nothing: the mutant is judged as usual
    _copytree_failing(monkeypatch, {2, 3})
    again = run_mutants(root, [a], ["tests/test_core.py"], extra_dirs=(), timeout=120)
    assert [(n, v) for n, v, _t, _g in again] == [("a", Verdict.KILLED)], (
        f"a lock that clears after two tries was not retried: {again}"
    )


def test_the_runner_keeps_a_symlink_a_link(tmp_path):
    root = _pk_tree(
        tmp_path,
        "import pathlib, pk\n\ndef test_ext_is_a_link():\n"
        "    assert (pathlib.Path(pk.__file__).parent / 'ext.py').is_symlink()\n",
    )
    outside = tmp_path / "outside.py"
    outside.write_text("X = 1\n", encoding="utf-8")
    _symlink_or_skip(
        outside, root / "src" / "pk" / "ext.py"
    )  # skips only on Windows without the privilege
    assert _baseline_passes(root), "a symlink of the package was copied as a plain file"


def test_a_test_file_that_is_not_among_the_copied_tests_fails_before_any_mutant_runs(tmp_path):
    root = _pk_tree(
        tmp_path, "from pk.core import go\n\ndef test_go_is_true():\n    assert go(True) is True\n"
    )
    ok = Mutant("ok", "src/pk/core.py", "return flag", "return False", "test_go_is_true")
    bad = Mutant(
        "bad",
        "src/pk/core.py",
        "return flag",
        "return not flag",
        "test_go_is_true",
        test_file="tests/elsewhere.py",
    )
    ran = []
    _must_refuse(
        "a test_file that is not among the copied tests",
        run_mutants,
        root,
        [ok, bad],
        ["tests/test_core.py"],
        match="elsewhere",
        extra_dirs=(),
        timeout=120,
        on_result=ran.append,
    )
    assert ran == [], "the first mutant was run before the bad test_file was found"


def test_junit_with_a_doctype_or_entity_is_refused_not_parsed():
    bomb = '<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]><testsuite><testcase classname="t" name="n"/></testsuite>'
    _must_refuse(
        "a JUnit file with a DOCTYPE was parsed", first_failure_junit, bomb
    )  # FAIL-BEFORE: parsed
    ok = '<testsuite><testcase classname="tests.t" name="n"><failure message="m">E   assert 1 == 2</failure></testcase></testsuite>'
    assert first_failure_junit(ok) == ("tests/t::n", "E   assert 1 == 2")


def test_the_runner_wires_pinned_so_another_failing_test_is_other_test(tmp_path):
    body = "from pk.core import go\n\ndef test_a():\n    assert go(True) is True\n\ndef test_b():\n    assert go(True) is True\n"
    root = _pk_tree(tmp_path, body)
    base = ("m", "src/pk/core.py", "return flag", "return False", "test_")
    other = Mutant(*base, pinned="tests/test_core::test_does_not_exist")
    same = Mutant("m2", *base[1:], pinned="tests/test_core::test_a")
    res = run_mutants(root, [other, same], ["tests/test_core.py"], extra_dirs=(), timeout=120)
    verdicts = {name: v for name, v, _tid, _good in res}
    assert verdicts["m"] is Verdict.OTHER_TEST, (
        "pinned was dropped: another failing test was not OTHER_TEST"
    )  # FAIL-BEFORE: Mutant had no pinned field
    assert verdicts["m2"] is Verdict.KILLED  # the pinned test is the one that failed first


def test_a_refused_junit_marks_that_mutant_error_and_the_run_goes_on(tmp_path, monkeypatch):
    from tools import mutation_runner

    body = "from pk.core import go\n\ndef test_a():\n    assert go(True) is True\n"
    root = _pk_tree(tmp_path, body)
    real = mutation_runner.first_failure_junit
    state = {"n": 0}

    def flaky(text):
        state["n"] += 1
        if state["n"] == 1:
            raise ValueError("refused")
        return real(text)

    monkeypatch.setattr(mutation_runner, "first_failure_junit", flaky)
    m1 = Mutant("m1", "src/pk/core.py", "return flag", "return False", "test_")
    m2 = Mutant("m2", "src/pk/core.py", "return flag", "return False", "test_")
    res = run_mutants(root, [m1, m2], ["tests/test_core.py"], extra_dirs=(), timeout=120)
    got = {n: (v, tid) for n, v, tid, _ in res}
    assert got["m1"] == (
        Verdict.ERROR,
        "JUNIT REFUSED",
    )  # FAIL-BEFORE: the ValueError aborted the whole run
    assert got["m2"][0] is Verdict.KILLED


def test_a_junit_text_over_the_ceiling_is_refused():
    _must_refuse(
        "a JUnit text over the size ceiling was parsed",
        first_failure_junit,
        "<testsuite>" + " " * getattr(mutmod, "MAX_JUNIT_CHARS", 8_000_000) + "</testsuite>",
    )  # FAIL-BEFORE: no size cap


def test_a_crash_row_is_good_only_when_the_exception_class_is_the_declared_one(tmp_path):
    root = _raising_tree(tmp_path)
    base = ("src/pk/core.py", "return flag", 'raise ValueError("boom")', "test_a")
    right = Mutant("right", *base, allow_crash=True, crash_type="ValueError")
    wrong = Mutant("wrong", *base, allow_crash=True, crash_type="KeyError")
    # a class that only CONTAINS the declared name (``MyValueError``) is not the declared class
    lookalike = Mutant(
        "lookalike",
        "src/pk/core.py",
        "return flag",
        'raise type("MyValueError", (Exception,), {})("boom")',
        "test_a",
        allow_crash=True,
        crash_type="ValueError",
    )
    res = {
        n: (v, good)
        for n, v, _t, good in run_mutants(
            root, [right, wrong, lookalike], ["tests/test_core.py"], extra_dirs=(), timeout=120
        )
    }
    assert res["right"] == (Verdict.CRASH, True)
    assert res["wrong"] == (Verdict.CRASH, False), (
        "a crash row was good for another exception class"
    )  # FAIL-BEFORE: any exception counted as good
    assert res["lookalike"] == (Verdict.CRASH, False), (
        "a crash row was good for a lookalike class name"
    )
    assert "ValueError" in mr.FIRST_LINES["right"]


def test_the_leading_class_of_an_error_line_is_parsed_not_searched():
    assert (
        mr._leading_class("E   demo.fakes.AuditWriteError: audit write failed") == "AuditWriteError"
    )
    assert mr._leading_class("E   ValueError") == "ValueError"
    assert mr._leading_class("PermissionError: [Errno 1] x") == "PermissionError"
    assert mr._leading_class("E   AssertionError: assert 'ValueError' == 'x'") == "AssertionError"
    assert mr._leading_class("") == ""


def test_allow_crash_without_a_crash_type_is_refused():
    _must_refuse(
        "allow_crash without a crash_type",
        Mutant, "m", "src/pk/core.py", "a", "b", "test_a", allow_crash=True,
    )  # fmt: skip
    _must_refuse(
        "a crash_type without allow_crash",
        Mutant, "m", "src/pk/core.py", "a", "b", "test_a", crash_type="ValueError",
    )  # fmt: skip


def test_a_truncated_junit_marks_the_mutant_error_and_the_run_goes_on(tmp_path, monkeypatch):
    root = _raising_tree(tmp_path)

    def truncated(text):
        raise ET.ParseError("no element found")

    monkeypatch.setattr(mr, "first_failure_junit", truncated)
    m = Mutant("m", "src/pk/core.py", "return flag", "return False", "test_a")
    ((_name, v, tid, good),) = run_mutants(
        root, [m], ["tests/test_core.py"], extra_dirs=(), timeout=120
    )
    assert (v, tid, good) == (
        Verdict.ERROR,
        "JUNIT REFUSED",
        False,
    )  # FAIL-BEFORE: ParseError aborted the whole run


def test_taskkill_is_resolved_under_system_root(tmp_path, monkeypatch):
    path = Path(mr._taskkill())
    assert path.name.lower() == "taskkill.exe" and path.parent.name.lower() == "system32", (
        f"taskkill was not run from System32: {path}"
    )
    # and the tree kill on Windows really runs THAT file (the Windows branch, with ``subprocess.run`` faked)
    winroot = tmp_path / "winroot"
    monkeypatch.setenv("SystemRoot", str(winroot))
    monkeypatch.setattr(mr, "_IS_WINDOWS", True)
    seen = []
    monkeypatch.setattr(mr.subprocess, "run", lambda argv, **kw: seen.append(argv))
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(600)"])
    try:
        mr._kill_tree(proc)
    finally:
        proc.kill()
        proc.wait()
    expected = [str(winroot / "System32" / "taskkill.exe"), "/F", "/T", "/PID", str(proc.pid)]
    assert seen == [expected], f"taskkill was not run from System32: {seen}"


# last on purpose: a mutation of a pinned file must be judged by the test aimed at it, not by this hash pin
def test_the_manifest_pins_the_files_a_demo_copies():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((FIX / "mutation_manifest.json").read_text(encoding="utf-8"))
    for rel, sha in manifest["files"].items():
        data = (root / rel).read_bytes().replace(b"\r\n", b"\n")
        assert hashlib.sha256(data).hexdigest() == sha, (
            rel,
            "changed: re-sync the demos and update the manifest and the CHANGELOG",
        )
    assert set(manifest["files"]) == {
        "src/hadavin_sdk/testing/__init__.py",
        "src/hadavin_sdk/testing/mutation.py",
        "tools/__init__.py",
        "tools/mutation_runner.py",
    }
    log = root / "CHANGELOG.md"
    if log.exists():  # the mutation copies do not carry it
        text = log.read_text(encoding="utf-8")
        for rel, sha in manifest["files"].items():
            assert sha in text, rel  # the CHANGELOG re-copy list names every pinned hash
