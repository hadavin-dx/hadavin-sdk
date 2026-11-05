"""The only CSV writer (spec 9); only ``exporter`` imports it. ``regenerate`` rewrites the whole file from rows: every cell goes through the cell guard,
the rows are written to a unique temporary file in the same folder (``tempfile.mkstemp``: created exclusively, mode 0600), flushed and fsynced, then ``os.replace``
swaps it in, so a kill leaves the old or the new file whole. Nothing is appended. Python ``csv``, QUOTE_ALL, ``\n``, UTF-8 without a BOM. ``out/`` is created 0700.
The temporary file is removed on ANY exception. ``SinkLocked`` = the file is held by another program (Windows sharing/access error, EBUSY, ETXTBSY);
every other ``OSError`` (disk full, EACCES, ...) is ``SinkError``. Limits, said plainly: no fsync of the DIRECTORY after ``os.replace`` (a power cut can
lose the swap; the receipts are intact and the next export regenerates); only the process holding ``serve.lock`` may call this (the exporter documents it)."""

from __future__ import annotations

import csv
import errno
import os
import stat
import tempfile
from collections.abc import Iterable
from pathlib import Path

from .sink_guard import COLUMNS, guard_row

_LOCKED_WINERRORS = (5, 32, 33)  # access denied, sharing violation, lock violation


class SinkLocked(Exception):  # noqa: N818 (the file is open in another program; the receipts are intact)
    pass


class SinkError(Exception):  # noqa: N818 (disk full, permission or another OS error; the receipts are intact)
    pass


def _locked(e: OSError) -> bool:
    return getattr(e, "winerror", None) in _LOCKED_WINERRORS or e.errno in (errno.EBUSY, errno.ETXTBSY)


def regenerate(path: Path, rows: Iterable[dict]) -> int:
    """Write header + every row; returns the number of data rows. A bad row raises ``sink_guard.BadCell`` BEFORE the file is touched."""
    guarded = [guard_row(r) for r in rows]
    tmp: Path | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd, name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
        tmp = Path(name)
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator="\n")
            w.writerow(COLUMNS)
            for r in guarded:
                w.writerow([r[c] for c in COLUMNS])
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException as e:
        if tmp is not None:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
        if isinstance(e, OSError):
            raise (SinkLocked if _locked(e) else SinkError)(type(e).__name__) from None
        raise
    return len(guarded)


def mode_state(path: Path) -> str:
    """For ``intake check``: ``ok`` (file 0600 and folder 0700 or absent), ``warn <what>`` (a warning, never a failure: a folder made by another tool may be looser), or ``n/a`` where mode bits mean nothing (Windows)."""
    if os.name == "nt":
        return "n/a (windows)"
    bad = []
    for p, want in ((path.parent, 0o077), (path, 0o177)):
        if p.exists() and stat.S_IMODE(p.stat().st_mode) & want & 0o077:
            bad.append(p.name)
    return "ok" if not bad else "warn " + " ".join(bad)
