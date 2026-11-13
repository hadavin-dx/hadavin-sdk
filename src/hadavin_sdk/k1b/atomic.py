"""Atomic file write: temp file in the same folder, fsync, ``os.replace``. A crash leaves a ``*.tmp``, never a torn file."""

from __future__ import annotations

import os
from pathlib import Path

from hadavin_sdk import pathguard


def atomic_write(path: Path, text: str) -> None:
    path = Path(path)
    final = pathguard.join(path.parent, path.name, what="output file")
    tmp = pathguard.join(final.parent, path.name + ".tmp", what="temp file")
    with open(tmp, "w", encoding="utf-8", errors="backslashreplace", newline="\n") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, final)
