"""The one place that creates a new private (owner-only, 0600 on POSIX) text file: used by make_run_env.py. Kept as its own tiny file so the secret-scope
scan can allow the single ``os.open`` here instead of the whole of make_run_env.py."""

from __future__ import annotations

import os
from pathlib import Path


def write_new_private_text(path: Path, text: str) -> None:
    """Create ``path`` (it must not exist) and write ``text``; raises ``FileExistsError`` if it exists."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
