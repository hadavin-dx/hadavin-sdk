"""The shared rules for a file name or a folder path, used by the file operations listed by the package tripwire test.

Class of bug this closes: a containment check copied per caller (``config.confined``, ``causelist._inside``,
``signer.key_path``), so a rule added to one was missing from the others, and most file operations had no check at all.
Rung (tool ladder): the older checks' ideas are reused; no library gives one refusal type with the Windows device rules
and containment after resolving links, so this small standard-library module is the one place.

Who controls a path: operator-typed (``operator_dir`` and ``operator_file`` check its SHAPE only), data-derived (a case
id, a file name found in a folder or manifest: every one goes through ``component`` or ``join``), fixed (a constant in
our code: no check). Threat model: the attacker is operator-typed or data-derived TEXT, not a second local process that
changes the folder while we run (a swap between check and use is NOT claimed closed). Callers use ONLY the returned path.

Rules (each has one test and one mutant): R1 empty or dot, R2 separator, R3 colon, R4 control or invisible character
(CONTROL_RANGES), R5 length (the whole path, and every name in it), R6 trailing dot or space, R7 Windows device name,
R8 escape, R9 absolute or drive-relative names (refused by R2 and R3), R10 cannot be resolved (any error from the
operating system), R11 wrong type, R12 a character Windows does not allow in a name, R13 a write target or temp name that
cannot be used. R6, R7 and R12 apply to names (``component``, ``join``) only. The text of a refusal names the argument
and the problem, never the value or the rule number (that is ``PathRefused.rule``). Refuse, never repair. Case-insensitive
disks, Unicode normal forms and Windows 8.3 names are not repaired. Hard links and mount points are out of scope.
The name rules apply on every system. Standard library only.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

from hadavin_sdk.errors import ConfigError

MAX_COMPONENT_BYTES = 255  # one name, in UTF-8 bytes (the usual file system limit)
# ``atomic_write`` adds 22 bytes (".<name>.<16 hex>.tmp"): the longest name it can write
MAX_WRITE_NAME_BYTES = MAX_COMPONENT_BYTES - 22
MAX_PATH_BYTES = 4096  # a whole path, in UTF-8 bytes (the usual Linux limit; Windows allows less)

# COM and LPT also come with the superscript digits 1, 2, 3 (escapes)
_DIGITS = "0123456789\u00b9\u00b2\u00b3"
_DEVICE_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$", "CLOCK$"}
    | {f"{prefix}{n}" for prefix in ("COM", "LPT") for n in _DIGITS}
)
# Characters that hide or reorder printed text: one named range per line, built with ``chr()``. A test and a mutant each.
CONTROL_RANGES = (
    ("C0 controls and NUL", 0x0000, 0x001F),
    ("DEL and C1 controls", 0x007F, 0x009F),
    ("soft hyphen", 0x00AD, 0x00AD),
    ("combining grapheme joiner", 0x034F, 0x034F),
    ("Arabic letter mark", 0x061C, 0x061C),
    ("Hangul fillers", 0x115F, 0x1160),
    ("Khmer inherent vowels", 0x17B4, 0x17B5),
    ("Mongolian vowel separator", 0x180E, 0x180E),
    ("zero-width and direction marks", 0x200B, 0x200F),
    ("line and paragraph separators and bidirectional embeddings", 0x2028, 0x202E),
    ("word joiner, invisible operators, isolates and deprecated format characters", 0x2060, 0x206F),
    ("braille blank", 0x2800, 0x2800),
    ("Hangul filler", 0x3164, 0x3164),
    ("variation selectors", 0xFE00, 0xFE0F),
    ("byte order mark", 0xFEFF, 0xFEFF),
    ("halfwidth Hangul filler", 0xFFA0, 0xFFA0),
    ("interlinear annotation", 0xFFF9, 0xFFFB),
    ("musical symbol format characters", 0x1D173, 0x1D17A),
    ("tag characters", 0xE0000, 0xE007F),
    ("variation selectors supplement", 0xE0100, 0xE01EF),
)
_CONTROL = re.compile(
    "["
    + "".join(f"{re.escape(chr(lo))}-{re.escape(chr(hi))}" for _, lo, hi in CONTROL_RANGES)
    + "]"
)
# Characters Windows does not allow in a file name (the colon is R3). Refused on every system, as PathRefused.
_WINDOWS_INVALID = re.compile(r'[<>"|?*]')


class PathRefused(ConfigError):
    """A path or name was refused. ``rule`` is R1 to R13. The text names the argument and the problem, never the value."""

    def __init__(self, rule: str, message: str) -> None:
        super().__init__(message)
        self.rule = rule

    def __reduce__(self) -> tuple[type, tuple[str, str]]:
        return (PathRefused, (self.rule, str(self)))  # so copy and pickle keep the rule


def _refuse(rule: str, what: str, text: str) -> PathRefused:
    return PathRefused(rule, f"{what}: {text}")


def _size(text: str) -> int:
    return len(text.encode("utf-8", errors="surrogatepass"))


def _check_name(name: str, what: str) -> None:
    """Rules R1 to R7 for one name (a single path component)."""
    if not isinstance(name, str):
        raise _refuse("R1", what, "not a plain name")
    if name in ("", ".", ".."):
        raise _refuse("R1", what, "not a plain name")
    if _CONTROL.search(name):
        raise _refuse("R4", what, "contains a control character")
    if "/" in name or "\\" in name:
        raise _refuse("R2", what, "contains a separator")
    if ":" in name:
        raise _refuse("R3", what, "contains a colon")
    if _WINDOWS_INVALID.search(name):
        raise _refuse("R12", what, "contains a character Windows does not allow")
    if _size(name) > MAX_COMPONENT_BYTES:
        raise _refuse("R5", what, "too long")
    if name[-1] in ". ":
        raise _refuse("R6", what, "ends with a dot or space")
    if name.split(".", 1)[0].rstrip(" ").upper() in _DEVICE_NAMES:
        raise _refuse("R7", what, "reserved device name")


def component(name: str, *, what: str) -> str:
    """Refuse unless ``name`` is one safe path component. Returns the same string, never changed."""
    _check_name(name, what)
    return name


# The one place that asks the operating system about a typed path: any OSError (every errno), a symlink loop (RuntimeError
# on 3.12), a NUL (ValueError) and a value that is not a path (TypeError) become one refusal with a fixed text (the system's
# own text holds the path). The refusal is raised outside the ``except`` block, so it has no cause and no context.
def _os[T](call: Callable[[], T], what: str) -> T:
    try:
        return call()
    except (OSError, RuntimeError, ValueError, TypeError):
        refusal = _refuse("R10", what, "cannot be resolved")
    raise refusal


def _resolve(path: Path | str, what: str, *, strict: bool) -> Path:
    return _os(lambda: Path(path).resolve(strict=strict), what)


def _check_text(text: str, what: str) -> None:
    """R4 for a whole path text, then R5 in bytes: the whole text and each name in it (the system stops at 255 bytes per
    name, so a longer name in any position would make a later ``is_file`` raise). A NUL must not depend on ``resolve``."""
    if _CONTROL.search(text):
        raise _refuse("R4", what, "contains a control character")
    parts = _os(lambda: Path(text).parts, what)
    if _size(text) > MAX_PATH_BYTES or any(_size(p) > MAX_COMPONENT_BYTES for p in parts):
        raise _refuse("R5", what, "too long")


def _within(root: Path, path: Path, what: str, must_exist: bool, kind: str | None) -> Path:
    """The one tail of ``inside`` and ``join``: resolved (strictly when ``must_exist``), inside ``root``, of ``kind``."""
    _check_text(str(path), what)
    real = _resolve(path, what, strict=must_exist)
    if not real.is_relative_to(root):
        raise _refuse("R8", what, "path escapes its folder")
    if kind and not _os(real.is_file if kind == "file" else real.is_dir, what):
        raise _refuse("R11", what, "not a file" if kind == "file" else "not a folder")
    return real


def inside(
    base: Path | str,
    path: Path | str,
    *,
    what: str,
    must_exist: bool = False,
    kind: str | None = None,
) -> Path:
    """The real location of ``path`` (already joined), refused unless it lies inside the real location of ``base`` (a link
    that leaves the base is refused: resolving follows it). No name rule applies (R6, R7, R12 are for ``join``)."""
    _check_text(str(base), what)
    return _within(
        _resolve(base, what, strict=False), _os(lambda: Path(path), what), what, must_exist, kind
    )


def join(
    base: Path | str,
    *names: str,
    what: str,
    must_exist: bool = False,
    kind: str | None = None,
) -> Path:
    """``base`` plus data-derived names, each through ``component``; the result is resolved (strictly when ``must_exist``)
    and must lie inside the resolved base. With no names the resolved base is returned. ``kind``: ``"file"`` or ``"dir"``."""
    for name in names:
        _check_name(name, what)
    _check_text(str(base), what)
    root = _resolve(base, what, strict=False)
    return _within(root, root.joinpath(*names), what, must_exist, kind)


def _operator(path: Path | str, what: str, kind: str, must_exist: bool) -> Path:
    _check_text(str(path), what)
    real = _resolve(path, what, strict=must_exist)
    if must_exist or _os(real.exists, what):
        _within(real, real, what, True, kind)
    return real


def operator_dir(
    path: Path | str, *, what: str, must_exist: bool = True, create_mode: int | None = None
) -> Path:
    """A folder the operator typed: shape checked (no control characters, not too long, resolves, is a folder; no outer
    base). ``must_exist=False`` accepts a folder the command will create; one that exists must still be a folder.
    ``create_mode`` makes it (with its parents) after the check and returns its real location; an error is a refusal."""
    real = _operator(path, what, "dir", must_exist)
    if create_mode is None:
        return real
    _os(lambda: real.mkdir(mode=create_mode, parents=True, exist_ok=True), what)
    return _resolve(real, what, strict=True)


def operator_file(path: Path | str, *, what: str, must_exist: bool = True) -> Path:
    """A file the operator typed: shape checked as for ``operator_dir``; it must exist and be a file unless
    ``must_exist=False`` (then a missing path is accepted and an existing one must be a file)."""
    return _operator(path, what, "file", must_exist)


def mapped(exc: PathRefused, **words: str) -> ConfigError:
    """Turn a refusal into a caller's own plain message: ``words`` maps a rule (``R10``) to the text to raise instead; a
    rule with no entry is returned unchanged. The caller raises the result ``from None``."""
    return ConfigError(words[exc.rule]) if exc.rule in words else exc


__all__ = [
    "CONTROL_RANGES",
    "MAX_COMPONENT_BYTES",
    "MAX_PATH_BYTES",
    "MAX_WRITE_NAME_BYTES",
    "PathRefused",
    "component",
    "inside",
    "join",
    "mapped",
    "operator_dir",
    "operator_file",
]
