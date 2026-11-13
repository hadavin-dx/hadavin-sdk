"""The ONE place the project starts a program: the folder guard, `tools/scan_repo.py` and the tests all call `run_fixed`.

The arguments are a fixed list (never a shell string, and `shell=True` is refused), the program is looked up on the PATH and
run by its full path (this interpreter is already one), and a program that is not found stops the caller with its name. A
single start point means the project's subprocess rule needs no waiver anywhere else."""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Sequence
from typing import Any


def run_fixed(
    argv: Sequence[str | os.PathLike[str]], *, check: bool, **kwargs: Any
) -> subprocess.CompletedProcess[Any]:
    """The ONE place the guard, `tools/scan_repo.py` and the tests start a program: a fixed list of arguments (never a shell
    string; `shell=True` is refused), the program found on the PATH and run by its full path (this interpreter is already
    one). A missing program stops the caller with its name."""
    if isinstance(argv, (str, bytes)) or not argv:
        raise TypeError("run_fixed takes a list of arguments, never a shell string")
    if kwargs.get("shell"):
        raise ValueError("run_fixed never starts a shell")
    first = os.fspath(argv[0])
    exe = first if os.path.isabs(first) else shutil.which(first)
    if exe is None:
        raise SystemExit(f"{first} was not found on the PATH; nothing here guesses")
    return subprocess.run([exe, *argv[1:]], check=check, **kwargs)
