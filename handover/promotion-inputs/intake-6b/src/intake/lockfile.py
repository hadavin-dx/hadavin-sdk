"""Portable single-writer lock (errata 3): ``acquire(path) -> handle`` (raises ``LockHeld`` if held),
``is_held(path) -> bool`` (never leaves the lock held), ``release(handle)``. Windows uses ``msvcrt.locking``, POSIX ``fcntl.flock``.

The lock lives as long as the handle (an open file object: keep a reference, dropping it releases the lock); the operating system drops it if the process dies. ``service.py`` (WP6) holds it for its
whole life; ``demo_ctl reset`` (WP7) calls ``is_held`` and refuses while the service runs. ``LockHeld`` is the second-``serve`` case: WP6 maps it to
exit 3 (``serve`` already running); it is not a refusal code of a request."""

from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    from os import O_NOFOLLOW as _NOFOLLOW  # refuse a symlinked lock file where the platform can
except ImportError:  # Windows
    _NOFOLLOW = 0

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl


class LockHeld(Exception):  # noqa: N818 (name fixed by the interface: "raises if held")
    """Another handle (this or another process) holds the lock."""


def _try_lock(f) -> bool:
    try:
        if sys.platform == "win32":
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def _unlock(f) -> None:
    try:
        if sys.platform == "win32":
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass


def acquire(path):
    """Take the exclusive lock on ``path`` (created if absent; its parent folder is created too). Returns the handle; raises ``LockHeld``."""
    p = Path(path)
    if p.is_dir():
        raise IsADirectoryError(p.name)
    p.parent.mkdir(parents=True, exist_ok=True)
    f = os.fdopen(os.open(p, os.O_RDWR | os.O_CREAT | _NOFOLLOW, 0o600), "a+b")  # the open file IS the handle; owner-only on POSIX
    if not _try_lock(f):
        f.close()
        raise LockHeld(p.name)
    return f


def release(handle) -> None:
    _unlock(handle)
    handle.close()


def is_held(path) -> bool:
    """True when somebody holds the lock now. A missing file means not held (and is not created). Never leaves the lock held. A directory path
    raises ``IsADirectoryError``. The answer is a snapshot: the holder may start or stop right after (a check-then-act caller must hold the lock
    itself with ``acquire``; ``demo_ctl reset`` accepts this because the service is stopped first)."""
    p = Path(path)
    if p.is_dir():
        raise IsADirectoryError(p.name)
    if not p.exists():
        return False
    try:
        h = acquire(p)
    except LockHeld:
        return True
    release(h)
    return False
