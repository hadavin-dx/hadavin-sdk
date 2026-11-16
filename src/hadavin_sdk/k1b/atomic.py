"""Atomic file write: temp file in the same folder, fsync, ``os.replace``. A crash leaves a ``*.tmp``, never a torn file."""

from __future__ import annotations

import os
from pathlib import Path


def atomic_write(path: Path, text: str) -> None:
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8", errors="backslashreplace", newline="\n") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
