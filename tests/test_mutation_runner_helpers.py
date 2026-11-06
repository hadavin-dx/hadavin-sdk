"""Tests of the two helpers in ``tests/test_mutation_runner.py`` that must work on Windows as well as on Linux.

``_pid_alive_windows`` talks to the Windows system library through ``ctypes``; here that library is replaced by a fake, so the
logic (which handle is asked for, what counts as alive, that the handle is closed) is checked on any system. A real Windows run
is still needed to prove the real calls. These tests are kept out of ``tests/test_mutation_runner.py`` because the meta-test
pins that file to its listed tests plus the manifest test.

Rule for every test here and in the other two ``tests/test_mutation_runner*.py`` files: a test that fakes ``sys.platform`` or
``os.name`` also fakes EVERY operating-system call the faked branch makes (``os.kill``, ``os.symlink``, ...). The faked branch is
reached on a system where its real calls mean something else (on Windows ``os.kill(pid, 0)`` sends Ctrl-C, and a symlink needs a
privilege), so the test would run the real call under the wrong flag.
"""

import ctypes
import errno
import subprocess
import sys
import types

import pytest

from tests import test_mutation_runner as t


class _Fn:
    """A stand-in for one function of the Windows library: a callable that accepts the type attributes ctypes sets."""

    def __init__(self, impl):
        self.impl = impl
        self.restype = None
        self.argtypes = None

    def __call__(self, *args):
        return self.impl(*args)


class _FakeKernel32:
    def __init__(self, *, opens=True, exit_code=259, exit_ok=True, last_error=0):
        self.opened_with = None
        self.closed = []
        self.last_error = last_error
        self._opens, self._exit_code, self._exit_ok = opens, exit_code, exit_ok
        self.OpenProcess = _Fn(self._open)
        self.GetExitCodeProcess = _Fn(self._get_exit_code)
        self.CloseHandle = _Fn(self._close)

    def _open(self, access, inherit, pid):
        self.opened_with = (access, inherit, pid)
        return 0x1234 if self._opens else None

    def _get_exit_code(self, handle, ref):
        ref._obj.value = self._exit_code
        return 1 if self._exit_ok else 0

    def _close(self, handle):
        self.closed.append(handle)
        return 1


def _install(monkeypatch, fake):
    monkeypatch.setattr(ctypes, "WinDLL", lambda name, use_last_error=False: fake, raising=False)
    monkeypatch.setattr(ctypes, "get_last_error", lambda: fake.last_error, raising=False)


def test_windows_probe_reports_a_running_process_and_closes_the_handle(monkeypatch):
    fake = _FakeKernel32(exit_code=259)
    _install(monkeypatch, fake)
    assert t._pid_alive_windows(4242) is True
    assert fake.opened_with == (
        0x1000,
        0,
        4242,
    )  # PROCESS_QUERY_LIMITED_INFORMATION, not inheritable
    assert fake.closed == [0x1234]


def test_windows_probe_reports_an_ended_process_dead_and_closes_the_handle(monkeypatch):
    fake = _FakeKernel32(exit_code=1)
    _install(monkeypatch, fake)
    assert t._pid_alive_windows(4242) is False
    assert fake.closed == [0x1234]


def test_windows_probe_no_such_process_is_dead_and_access_denied_is_alive(monkeypatch):
    gone = _FakeKernel32(opens=False, last_error=87)  # ERROR_INVALID_PARAMETER: no such pid
    _install(monkeypatch, gone)
    assert t._pid_alive_windows(4242) is False
    assert gone.closed == []
    denied = _FakeKernel32(
        opens=False, last_error=5
    )  # ERROR_ACCESS_DENIED: it exists, it is not ours
    _install(monkeypatch, denied)
    assert t._pid_alive_windows(4242) is True


def _fake_tasklist(monkeypatch, stdout):
    seen = []

    def run(argv, **kw):
        seen.append(argv)
        return types.SimpleNamespace(stdout=stdout)

    monkeypatch.setattr(subprocess, "run", run)
    return seen


def test_windows_probe_a_failed_exit_code_read_falls_back_to_tasklist(monkeypatch, tmp_path):
    fake = _FakeKernel32(exit_ok=False, last_error=6)
    _install(monkeypatch, fake)
    monkeypatch.setenv("SystemRoot", str(tmp_path))
    seen = _fake_tasklist(monkeypatch, '"python.exe","4242","Console","1","10,000 K"\n')
    assert t._pid_alive_windows(4242) is True
    assert seen == [
        [str(tmp_path / "System32" / "tasklist.exe"), "/FI", "PID eq 4242", "/NH", "/FO", "CSV"]
    ]  # by the full System32 path, not a PATH search
    assert fake.closed == [0x1234]  # the handle is closed on the error path too
    _fake_tasklist(monkeypatch, "INFO: No tasks are running which match the specified criteria.\n")
    assert t._pid_alive_windows(4242) is False
    # a pid that only CONTAINS the number (14242) is not the process
    _fake_tasklist(monkeypatch, '"python.exe","14242","Console","1","10,000 K"\n')
    assert t._pid_alive_windows(4242) is False


def test_windows_probe_without_the_system_library_falls_back_to_tasklist(monkeypatch, tmp_path):
    def no_library(name, use_last_error=False):
        raise OSError("no kernel32")

    monkeypatch.setattr(ctypes, "WinDLL", no_library, raising=False)
    monkeypatch.setenv("SystemRoot", str(tmp_path))
    _fake_tasklist(monkeypatch, '"python.exe","4242","Console","1","10,000 K"\n')
    assert t._pid_alive_windows(4242) is True


def test_pid_alive_uses_the_windows_probe_only_on_windows(monkeypatch):
    seen, signalled = [], []

    def no_such_process(pid, sig):
        signalled.append((pid, sig))
        raise ProcessLookupError(pid)

    monkeypatch.setattr(t, "_pid_alive_windows", lambda pid: seen.append(pid) or "win")
    # the POSIX branch is run with the platform faked: the real ``os.kill(77, 0)`` must not run (on Windows signal 0 is Ctrl-C)
    monkeypatch.setattr(t.os, "kill", no_such_process)
    monkeypatch.setattr(sys, "platform", "win32")
    assert t._pid_alive(77) == "win" and seen == [77] and signalled == []
    monkeypatch.setattr(sys, "platform", "linux")
    assert t._pid_alive(77) is False and seen == [77]
    assert signalled == [(77, 0)], "the POSIX probe did not ask the (faked) system call"


@pytest.mark.skipif(sys.platform == "win32", reason="the POSIX branch uses /proc and signals")
def test_pid_alive_on_posix_sees_itself_and_a_gone_process():
    import os
    import subprocess

    assert t._pid_alive(os.getpid()) is True
    child = subprocess.Popen([sys.executable, "-c", "pass"])
    child.wait()
    assert t._pid_alive(child.pid) is False  # waited for, so gone


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="needs /proc")
def test_pid_alive_counts_a_zombie_as_dead():
    import subprocess
    import time

    child = subprocess.Popen([sys.executable, "-c", "pass"])
    try:
        for _ in range(50):  # the child has ended but nobody waits for it: a zombie
            if not t._pid_alive(child.pid):
                break
            time.sleep(0.1)
        assert t._pid_alive(child.pid) is False
    finally:
        child.wait()


def _refusing(error):
    def fail(*_a, **_k):
        raise error

    return fail


def test_symlink_helper_skips_only_on_windows_without_the_privilege(monkeypatch, tmp_path):
    winerr = OSError(errno.EINVAL, "A required privilege is not held by the client")
    winerr.winerror = 1314
    monkeypatch.setattr(t.os, "symlink", _refusing(winerr))
    monkeypatch.setattr(sys, "platform", "win32")
    with pytest.raises(pytest.skip.Exception, match="privilege"):
        t._symlink_or_skip(tmp_path, tmp_path / "l")
    # any other error on Windows is a failure ...
    other = OSError(errno.ENOSPC, "No space left on device")
    other.winerror = 112
    monkeypatch.setattr(t.os, "symlink", _refusing(other))
    with pytest.raises(OSError):
        t._symlink_or_skip(tmp_path, tmp_path / "l")
    # ... and so is EPERM, or even error 1314, anywhere else: POSIX must be able to make a link
    monkeypatch.setattr(sys, "platform", "linux")
    for error in (OSError(errno.EPERM, "Operation not permitted"), winerr):
        monkeypatch.setattr(t.os, "symlink", _refusing(error))
        with pytest.raises(OSError):
            t._symlink_or_skip(tmp_path, tmp_path / "l")


def test_dir_link_makes_a_junction_on_windows_and_a_symlink_elsewhere(monkeypatch, tmp_path):
    made = []
    fake = types.SimpleNamespace(CreateJunction=lambda src, dst: made.append((src, dst)))
    monkeypatch.setitem(sys.modules, "_winapi", fake)
    monkeypatch.setattr(sys, "platform", "win32")
    t._dir_link(tmp_path, tmp_path / "j")
    assert made == [(str(tmp_path), str(tmp_path / "j"))]  # no privilege needed, so no skip either
    # the non-Windows half with the platform faked: the link call is a recorder, so no real symlink is made (Windows needs a privilege)
    links = []
    monkeypatch.setattr(
        t.os, "symlink", lambda target, link, **kw: links.append((target, link, kw))
    )
    monkeypatch.setattr(sys, "platform", "linux")
    t._dir_link(tmp_path, tmp_path / "s")
    assert links == [(tmp_path, tmp_path / "s", {"target_is_directory": True})]
    assert len(made) == 1


def test_symlink_helper_makes_the_link_where_it_can(tmp_path):
    (tmp_path / "real.txt").write_text("x", encoding="utf-8")
    t._symlink_or_skip(tmp_path / "real.txt", tmp_path / "link.txt")
    assert (tmp_path / "link.txt").is_symlink()
