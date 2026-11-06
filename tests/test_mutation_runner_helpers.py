"""Tests of the two helpers in ``tests/test_mutation_runner.py`` that must work on Windows as well as on Linux.

``_pid_alive_windows`` talks to the Windows system library through ``ctypes``; here that library is replaced by a fake, so the
logic (which handle is asked for, what counts as alive, that the handle is closed) is checked on any system. A real Windows run
is still needed to prove the real calls. These tests are kept out of ``tests/test_mutation_runner.py`` because the meta-test
pins that file to the 21 moved tests plus the manifest test.
"""

import ctypes
import errno
import sys

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


def test_windows_probe_a_failed_exit_code_read_is_an_error_not_an_answer(monkeypatch):
    fake = _FakeKernel32(exit_ok=False, last_error=6)
    _install(monkeypatch, fake)
    with pytest.raises(OSError, match="GetExitCodeProcess"):
        t._pid_alive_windows(4242)
    assert fake.closed == [0x1234]  # the handle is closed on the error path too


def test_pid_alive_uses_the_windows_probe_only_on_windows(monkeypatch):
    seen = []
    monkeypatch.setattr(t, "_pid_alive_windows", lambda pid: seen.append(pid) or "win")
    monkeypatch.setattr(sys, "platform", "win32")
    assert t._pid_alive(77) == "win" and seen == [77]
    monkeypatch.setattr(sys, "platform", "linux")
    assert t._pid_alive(77) != "win" and seen == [77]


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


def test_symlink_helper_skips_only_for_a_missing_privilege(monkeypatch, tmp_path):
    def refuse(code):
        def fail(*_a, **_k):
            raise code

        return fail

    winerr = OSError(errno.EINVAL, "A required privilege is not held by the client")
    winerr.winerror = 1314
    monkeypatch.setattr(t.os, "symlink", refuse(winerr))
    with pytest.raises(pytest.skip.Exception, match="privilege"):
        t._symlink_or_skip(tmp_path, tmp_path / "l")
    monkeypatch.setattr(t.os, "symlink", refuse(OSError(errno.EPERM, "Operation not permitted")))
    with pytest.raises(pytest.skip.Exception, match="privilege"):
        t._symlink_or_skip(tmp_path, tmp_path / "l")
    # any other failure is a failure, not a skip
    monkeypatch.setattr(t.os, "symlink", refuse(OSError(errno.ENOSPC, "No space left on device")))
    with pytest.raises(OSError) as info:
        t._symlink_or_skip(tmp_path, tmp_path / "l")
    assert info.value.errno == errno.ENOSPC


def test_symlink_helper_makes_the_link_where_it_can(tmp_path):
    (tmp_path / "real.txt").write_text("x", encoding="utf-8")
    t._symlink_or_skip(tmp_path / "real.txt", tmp_path / "link.txt")
    assert (tmp_path / "link.txt").is_symlink()
