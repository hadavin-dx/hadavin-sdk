"""The ONE place the project starts a program: the folder guard, `tools/scan_repo.py` and the tests all call
`run_fixed`.

The contract checks the SHAPE of the command, not which program runs: the arguments are a list or tuple of
texts or paths (never one string, never empty, no NUL character), the program is an absolute path or is found on
the PATH, only the keyword arguments in `ALLOWED_KEYWORDS` may be given (so `shell`, `executable`, `preexec_fn`
and `stdin` are refused), and a program that is not found stops the caller with its name. A caller must never
pass untrusted data as the arguments of an interpreter (`sh`, `python`): `["sh", "-c", text]` passes the
shape check. Because every caller goes through this one start point, the project's subprocess rule needs one
marker, on the line that starts the program; that marker is the only waiver."""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Sequence
from typing import Any

ALLOWED_KEYWORDS = frozenset(
    {"cwd", "env", "capture_output", "text", "timeout", "input", "encoding"}
)


def run_fixed(
    argv: Sequence[str | os.PathLike[str]], *, check: bool, **kwargs: Any
) -> subprocess.CompletedProcess[Any]:
    """Start `argv` once, with the contract of the module text. A broken contract raises before a start."""
    if not isinstance(argv, (list, tuple)) or not argv:
        raise TypeError("run_fixed takes a non-empty list or tuple of arguments, never a string")
    refused = sorted(set(kwargs) - ALLOWED_KEYWORDS)
    if refused:
        raise ValueError(f"run_fixed does not accept {refused}: no shell, no executable, no hooks")
    words = [os.fspath(a) for a in argv]
    if not all(isinstance(w, str) and "\0" not in w for w in words):
        raise TypeError("run_fixed takes texts or paths without a NUL character")
    exe = words[0] if os.path.isabs(words[0]) else shutil.which(words[0])
    if exe is None:
        raise SystemExit(f"{words[0]} was not found on the PATH; nothing here guesses")
    return subprocess.run([exe, *words[1:]], check=check, **kwargs)  # noqa: S603 - argv is validated above: list of text, no NUL, only allowed keywords
