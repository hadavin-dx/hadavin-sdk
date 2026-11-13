"""Atomic file write: temp file in the same folder, fsync, ``os.replace``. A crash leaves a ``*.tmp``, never a torn file.

The caller passes the FOLDER and the file NAME separately. The folder is one the caller already validated (an operator-typed
folder goes through ``pathguard.operator_dir``); the name goes through ``pathguard.join`` (rules R1 to R8 of ``pathguard``),
so a name that came from data can neither leave the folder nor be a Windows device name.

Honest limits. ``O_NOFOLLOW`` protects only the last component of the temp name and does not exist on Windows;
``os.replace`` resolves its target by name; a second local process that changes the folder while this runs is outside the
threat model (see ``pathguard``). A temp file is removed on any exception (including Ctrl-C); a hard kill (power loss,
SIGKILL) can still leave a ``.<name>.<random>.tmp`` file, which ``score`` reports as a stray file. A name that is a hard
link (a second name of a file that may lie outside the folder) is replaced by a new file: the other name keeps the old
content (one test pins this); mount points are not handled.
"""

from __future__ import annotations

import os
import secrets
from pathlib import Path

from hadavin_sdk import pathguard


def atomic_write(base: Path, name: str, text: str) -> None:
    """Write ``text`` to ``base/name`` (UTF-8, ``\\n`` line ends, unencodable characters as backslash escapes). A name that
    is already a link is refused: the link is not replaced and its target is not written through it."""
    final = pathguard.join(base, name, what="output file")
    if len(name.encode("utf-8", errors="surrogatepass")) > pathguard.MAX_WRITE_NAME_BYTES:
        raise pathguard.PathRefused("R5", "output file: too long")
    # the unresolved name: join() resolved a link to its target
    if os.path.islink(Path(base) / name):
        raise pathguard.PathRefused("R8", "output file: a link is not replaced")
    if final.is_dir():  # a folder is never replaced; the text must not hold the path
        raise pathguard.PathRefused("R13", "output file: a folder is not replaced")
    tmp = pathguard.join(final.parent, f".{name}.{secrets.token_hex(8)}.tmp", what="temp file")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    try:
        fd = os.open(tmp, flags, 0o666)  # the umask removes what the operator's setting removes
    except (
        FileExistsError
    ):  # the existing file is left alone; the OS text holds the path, so it is not passed on
        raise pathguard.PathRefused("R13", "temp file: the name is already in use") from None
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
