"""The ONE place the tests start a program (git, node, chown, chmod, this interpreter): a fixed list of arguments, never a
shell string, with the program looked up on the PATH and run by its full path. Keeping the start in one function means the
project's subprocess rule is waived once, in `pyproject.toml`, with the reason written there, and not on every line."""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Sequence
from typing import Any


def run(argv: Sequence[str], *, check: bool, **kwargs: Any) -> subprocess.CompletedProcess[Any]:
    """`subprocess.run` for a fixed argument list. The first item is a program name or a full path; a name that is not on
    the PATH raises `FileNotFoundError` naming it (a missing tool is never read as a pass)."""
    first = str(argv[0])
    exe = first if os.path.isabs(first) else shutil.which(first)
    if exe is None:
        raise FileNotFoundError(f"{first}: not found on PATH")
    return subprocess.run([exe, *map(str, argv[1:])], check=check, **kwargs)
