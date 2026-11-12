"""Atomic file write: temp file in the same folder, fsync, ``os.replace``. A crash leaves a ``*.tmp``, never a torn file.

The caller passes the FOLDER and the file NAME separately. The folder is one the caller already validated (an operator-typed
folder goes through ``pathguard.operator_dir``); the name goes through ``pathguard.join`` (rules R1 to R8 of ``pathguard``),
so a name that came from data can neither leave the folder nor be a Windows device name.

Honest limits. ``O_NOFOLLOW`` protects only the last component of the temp name and does not exist on Windows;
``os.replace`` resolves its target by name; a second local process that changes the folder while this runs is outside the
threat model (see ``pathguard``). A temp file is removed on any exception (including Ctrl-C); a hard kill (power loss,
SIGKILL) can still leave a ``.<name>.<random>.tmp`` file, which ``score`` reports as a stray file.
"""

from __future__ import annotations

import os
import secrets
from pathlib import Path

from hadavin_sdk import pathguard

# The temp name is ".<name>.<16 hex>.tmp": this many bytes more than the name, and it must stay within one name's limit.
_TEMP_EXTRA = 1 + 1 + 16 + 4


def atomic_write(base: Path, name: str, text: str) -> None:
    """Write ``text`` to ``base/name`` (UTF-8, ``\\n`` line ends, unencodable characters as backslash escapes)."""
    final = pathguard.join(base, name, what="output file")
    if (
        len(name.encode("utf-8", errors="surrogatepass")) + _TEMP_EXTRA
        > pathguard.MAX_COMPONENT_BYTES
    ):
        raise pathguard.PathRefused("R5", "output file: too long")
    tmp = pathguard.join(final.parent, f".{name}.{secrets.token_hex(8)}.tmp", what="temp file")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    fd = os.open(tmp, flags, 0o666)  # the umask removes what the operator's setting removes
    try:
        f = os.fdopen(fd, "w", encoding="utf-8", errors="backslashreplace", newline="\n")
    except BaseException:
        os.close(fd)
        tmp.unlink(missing_ok=True)
        raise
    try:
        with f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, final)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
