"""lockfile: acquire raises while held, is_held never leaves the lock held, release frees it, and a second PROCESS sees the lock (single-writer)."""

from __future__ import annotations

import os
import subprocess
import sys
import time

import pytest

from conftest import ROOT
from intake import lockfile

ENV = dict(os.environ, PYTHONPATH=str(ROOT / "src"))


def test_acquire_release_cycle(tmp_path):
    p = tmp_path / "sub" / "serve.lock"
    assert lockfile.is_held(p) is False and not p.exists()  # a missing file is not held and is not created by is_held
    h = lockfile.acquire(p)
    assert lockfile.is_held(p) is True
    with pytest.raises(lockfile.LockHeld):
        lockfile.acquire(p)
    lockfile.release(h)
    assert lockfile.is_held(p) is False
    lockfile.release(lockfile.acquire(p))  # free again


def test_is_held_does_not_keep_the_lock(tmp_path):
    p = tmp_path / "serve.lock"
    lockfile.release(lockfile.acquire(p))
    for _ in range(3):
        assert lockfile.is_held(p) is False
    h = lockfile.acquire(p)  # still acquirable after the probes
    lockfile.release(h)


def test_a_second_process_sees_and_cannot_take_the_lock(tmp_path):
    p = tmp_path / "serve.lock"
    code = (
        "import sys; from intake import lockfile\n"
        "p = sys.argv[1]\n"
        "print(lockfile.is_held(p))\n"
        "try:\n    lockfile.acquire(p); print('took')\nexcept lockfile.LockHeld:\n    print('refused')\n"
    )
    h = lockfile.acquire(p)
    try:
        r = subprocess.run([sys.executable, "-c", code, str(p)], capture_output=True, text=True, cwd=ROOT, env=ENV, timeout=60)
        assert r.stdout.split() == ["True", "refused"], r.stderr
    finally:
        lockfile.release(h)
    r = subprocess.run([sys.executable, "-c", code, str(p)], capture_output=True, text=True, cwd=ROOT, env=ENV, timeout=60)
    assert r.stdout.split() == ["False", "took"], r.stderr


def test_a_killed_holder_frees_the_lock(tmp_path):
    p = tmp_path / "serve.lock"
    code = "import sys, time; from intake import lockfile\nholder = lockfile.acquire(sys.argv[1]); print('ready', flush=True); time.sleep(60)\n"
    proc = subprocess.Popen([sys.executable, "-c", code, str(p)], stdout=subprocess.PIPE, text=True, cwd=ROOT, env=ENV)
    try:
        assert proc.stdout.readline().strip() == "ready"
        assert lockfile.is_held(p) is True
    finally:
        proc.kill()
        proc.wait(timeout=30)
    for _ in range(50):  # the operating system releases the lock when the process dies
        if not lockfile.is_held(p):
            break
        time.sleep(0.1)
    assert lockfile.is_held(p) is False
