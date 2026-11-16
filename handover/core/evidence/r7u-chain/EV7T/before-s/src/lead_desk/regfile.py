"""The one way the library opens a file: a REGULAR file or a refusal. `open_regular` is for a file it only reads
(settings, key and flag files); `open_output` is for a file it writes or appends to (the lock file, the spend ledger,
the trace file, the counters file).

A pipe (FIFO), a device or a socket has no end, so a plain read of one can wait for ever. The file is opened without
waiting (O_NONBLOCK, so opening a pipe returns at once), its kind is checked on the open handle (not on the name, so
a swap between the check and the read changes nothing) and anything but a regular file is refused with an OSError,
which every reader already turns into its own fixed "cannot be read" text (never the path).

A file that is written has the same trap (opening a pipe for writing waits until somebody reads it) and one more: a
path the operator names that does not exist yet must be created. `open_output` opens it without waiting, creates it
only when it is absent, checks the kind on the open handle and refuses anything but a regular file BEFORE any byte is
cut off or written (a file is shortened only after the check). A link that points to a regular file keeps working (an
operator may link a log file); a link that points to a pipe is refused like the pipe, because the kind is read from
the open handle, not from the name."""

from __future__ import annotations

import errno
import math
import os
import stat
from collections.abc import Iterator
from typing import IO, Any

from lead_desk.constants import LIVE_KEY_MIN_CHARS, MAX_JSON_BYTES, MAX_TEXT_BYTES, NEW_FILE_MODE, SECRET_FILE_MAX_BYTES
from lead_desk.jsonread import loads_bounded
from lead_desk.scrub import scrub_error

# O_NOCTTY: opening a terminal device must not make it the controlling terminal of the process
_COMMON = (
    getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOCTTY", 0)
)
_FLAGS = os.O_RDONLY | _COMMON


class NotRegularFile(OSError):
    """The path is a pipe, a device, a socket, a folder or has a NUL character: not something to read as a file. The
    text never holds the path."""


def open_regular(path: str | os.PathLike[str]) -> IO[bytes]:
    """Open `path` for reading bytes; a missing file raises FileNotFoundError and any other kind of file than a
    regular one raises NotRegularFile (both are OSError)."""
    try:
        fd = os.open(path, _FLAGS)
    except ValueError:  # an embedded NUL character
        raise NotRegularFile("not a regular file") from None
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise NotRegularFile("not a regular file")
        return os.fdopen(fd, "rb")
    except BaseException:
        os.close(fd)
        raise


class FileRefused(ValueError):
    """The file is regular but its content cannot be used: too big, not UTF-8 text, not JSON, or nested so deeply
    that the JSON reader gave up (RecursionError). The text is fixed and never holds the path or the content."""


_ASCII_WHITESPACE = " \t\r\n"  # the only characters trimmed round a secret; every other kind of space is refused


def read_secret_line(path: str | os.PathLike[str], what: str, noun: str, *, spaced: bool = False) -> str:
    """The ONE reader of a key or password file (the live model key, the HubSpot key, the SMTP password). The file is
    a regular file of at most SECRET_FILE_MAX_BYTES, UTF-8 text (a byte-order mark is accepted; UTF-16 is refused with
    a helpful text), ONE line, at least LIVE_KEY_MIN_CHARS printable ASCII characters (a non-ASCII key is refused in
    both modes). A space or tab inside is refused, except with `spaced=True` (an app password shown in groups: the
    spaces are dropped). Raises FileRefused with a fixed text that names `what` ("the {what} file ...") and `noun`
    ("key" or "password") and holds neither the path nor the content. A caller that needs its own error class maps
    FileRefused. The refusal carries no earlier error: the OSError that caused it holds the path, and a decode error
    holds the bytes of the file (the key itself), so neither stays reachable through `__context__`."""
    try:
        return _read_secret_text(path, what, noun, spaced)
    except FileRefused as e:
        scrub_error(e)  # the choke point of every key and password file: no earlier error, no frame holds a path
        raise


def _read_secret_text(path: str | os.PathLike[str], what: str, noun: str, spaced: bool) -> str:
    try:
        with open_regular(path) as f:
            raw = f.read(SECRET_FILE_MAX_BYTES + 1)  # bounded: a huge file is never read whole
    except OSError:
        raise FileRefused(f"the {what} file cannot be read") from None  # the OS error holds the path
    if len(raw) > SECRET_FILE_MAX_BYTES:
        raise FileRefused(f"the {what} file is too large: it must hold only the {noun}")
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        raise FileRefused(f"the {what} file is UTF-16 text: save it as plain UTF-8 text")
    try:
        text = raw.decode("utf-8-sig").strip(
            _ASCII_WHITESPACE
        )  # ASCII only: a no-break space etc. stays and is refused
    except UnicodeError:
        raise FileRefused(f"the {what} file is not UTF-8 text: save it as plain UTF-8 text") from None
    if "\n" in text or "\r" in text:
        raise FileRefused(f"the {what} file has more than one line: it must hold only the {noun}")
    secret = text.replace(" ", "").replace("\t", "") if spaced else text  # only space and tab are dropped
    if not secret_text_ok(secret):
        raise FileRefused(f"the {what} file holds no {noun}")
    return secret


def secret_text_ok(secret: str) -> bool:
    """The ONE check of a key or password text, for a file line and for an environment value alike: at least
    LIVE_KEY_MIN_CHARS characters, plain printable ASCII, no space, tab, control character or non-ASCII letter (a key
    with a non-ASCII character cannot be sent in an HTTP header or an SMTP login: it must be refused before any money
    is reserved or any connection is made)."""
    return (
        LIVE_KEY_MIN_CHARS <= len(secret) <= SECRET_FILE_MAX_BYTES
        and secret.isascii()
        and secret.isprintable()
        and not any(c.isspace() for c in secret)
    )


def read_regular_bytes(path: str | os.PathLike[str], max_bytes: int) -> bytes:
    """The whole content of a regular file of at most `max_bytes` bytes. A pipe, a device, a folder or a missing file
    raises OSError (open_regular); a bigger file raises FileRefused (at most max_bytes + 1 bytes are ever read)."""
    with open_regular(path) as f:
        data = f.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise FileRefused("the file is too big")
    return data


def iter_regular_lines(
    path: str | os.PathLike[str], max_bytes: int, max_line_bytes: int, max_rows: int | None = None
) -> Iterator[str]:
    """The lines of a regular UTF-8 file one at a time (a line ends at a line feed; the line feed is kept), never the
    whole file in memory. Refuses with FileRefused when one line is longer than `max_line_bytes`, the file longer than
    `max_bytes` or it has more than `max_rows` rows; a pipe, a device or a missing file raises OSError (open_regular);
    bytes that are not UTF-8 raise FileRefused. At most max_line_bytes + 1 bytes are read for one line."""
    total = 0
    rows = 0
    with open_regular(path) as f:
        while True:
            raw = f.readline(max_line_bytes + 1)
            if not raw:
                return
            total += len(raw)
            rows += 1
            if len(raw) > max_line_bytes or total > max_bytes or (max_rows is not None and rows > max_rows):
                raise FileRefused("the file is too big")
            try:
                yield raw.decode("utf-8")
            except UnicodeError:
                raise FileRefused("the file is not UTF-8 text") from None


def read_regular_text(path: str | os.PathLike[str], max_bytes: int = MAX_TEXT_BYTES) -> str:
    """read_regular_bytes decoded as UTF-8; bytes that are not UTF-8 text raise FileRefused (never decoded with a
    replacement character). ONE leading byte-order mark (what some Windows editors add) is dropped, as the key and
    password reader and the invariant checker already do, so a flag file, a config file and a JSON file saved with a
    mark read as the same text as one saved without it; a mark anywhere else is kept and is not JSON."""
    try:
        return read_regular_bytes(path, max_bytes).decode("utf-8-sig")
    except UnicodeError:
        raise FileRefused("the file is not UTF-8 text") from None


def load_json_file(path: str | os.PathLike[str], max_bytes: int = MAX_JSON_BYTES) -> Any:
    """The JSON value in a regular file. Every way the content can be wrong (too big, not UTF-8, not JSON, nested too
    deeply, a number that is not finite: NaN, Infinity, -Infinity or 1e999) is one FileRefused; a file that cannot be
    opened as a regular file is an OSError."""
    text = read_regular_text(path, max_bytes)
    try:
        value = loads_bounded(text, parse_constant=_refuse_constant)
    except (ValueError, RecursionError):  # JSONDecodeError is a ValueError; 100000 nested brackets: RecursionError
        raise FileRefused("the file is not JSON that can be read") from None
    if _has_non_finite(value):  # 1e999 is read as infinity without a word
        raise FileRefused("the file is not JSON that can be read")
    return value


def _refuse_constant(_name: str) -> Any:
    """`loads_bounded(parse_constant=...)`: NaN, Infinity and -Infinity are not JSON; the parser would accept them."""
    raise ValueError("not JSON")


def _has_non_finite(value: Any) -> bool:
    """True when a float anywhere inside `value` is infinite or NaN (a loop over a stack: no recursion limit)."""
    stack = [value]
    while stack:
        item = stack.pop()
        if isinstance(item, float):
            if not math.isfinite(item):
                return True
        elif isinstance(item, dict):
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
    return False


def plain_reason(error: BaseException) -> str:
    """Why a file could not be used, in plain words for a refusal line (never an exception class name, never the path
    or the content). Every text is fixed."""
    if isinstance(error, NotRegularFile):
        return "not a regular file"
    if isinstance(error, FileRefused):
        return str(error)  # its texts are fixed: too big, not UTF-8 text, not JSON that can be read
    if isinstance(error, FileNotFoundError):
        return "no such file"
    if isinstance(error, PermissionError):
        return "no permission"
    if isinstance(error, OSError):
        return "the system refused to open it"
    return "the content cannot be used"


_OUTPUT_MODES = ("a", "a+b", "w")


def open_output(
    path: str | os.PathLike[str], mode: str = "a+b", encoding: str | None = None, newline: str | None = None
) -> IO[Any]:
    """Open `path` for writing and return the file object, or raise NotRegularFile (an OSError) for a pipe, a device,
    a socket, a folder or a NUL character in the name. `mode` is "a" (text append; give `encoding`), "a+b" (binary
    append and read) or "w" (text write; give `encoding`; the file is emptied only once it is known to be a regular
    file). `newline` is the one of `open()` (give "" to write line ends exactly as they are). A missing file is
    created (the folder must exist). Any other OSError (no permission, a missing folder, a full disk) is raised as
    it is."""
    if mode not in _OUTPUT_MODES:
        raise ValueError("mode must be one of " + ", ".join(_OUTPUT_MODES))
    flags = _COMMON | os.O_CREAT | (os.O_RDWR if "+" in mode else os.O_WRONLY) | (os.O_APPEND if "a" in mode else 0)
    try:
        fd = os.open(path, flags, NEW_FILE_MODE)
    except ValueError:  # an embedded NUL character
        raise NotRegularFile("not a regular file") from None
    except IsADirectoryError:
        raise NotRegularFile("not a regular file") from None
    except OSError as e:
        if e.errno == errno.ENXIO:  # a pipe that nobody reads: opening it for writing without waiting says so
            raise NotRegularFile("not a regular file") from None
        raise
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise NotRegularFile("not a regular file")
        if mode == "w":
            os.ftruncate(fd, 0)
        return os.fdopen(fd, mode, encoding=encoding, newline=newline)
    except BaseException:
        os.close(fd)
        raise


def refuse_replacing_special(path: str | os.PathLike[str]) -> None:
    """Raise NotRegularFile (an OSError) when `path` already exists (a link is followed) and is not a regular file: a
    device, a pipe, a socket or a folder. Call it BEFORE `os.replace(tmp, path)`: a replace swaps the name itself, so
    it would turn a device into a plain file instead of failing. A missing path is fine (the replace creates it)."""
    try:
        mode = os.stat(path).st_mode
    except FileNotFoundError:
        return
    except ValueError:  # an embedded NUL character
        raise NotRegularFile("not a regular file") from None
    if not stat.S_ISREG(mode):
        raise NotRegularFile("not a regular file")


def write_regular_text(path: str | os.PathLike[str], text: str, newline: str | None = None) -> None:
    """Write `text` (UTF-8) as the whole content of `path`: a new file is created, an old regular file is emptied first.
    A pipe, a device, a folder or a NUL character in the name is refused (NotRegularFile, an OSError) BEFORE any byte
    is written; any other OSError (no permission, a missing folder, a full disk) is raised as it is."""
    with open_output(path, "w", encoding="utf-8", newline=newline) as f:
        f.write(text)
