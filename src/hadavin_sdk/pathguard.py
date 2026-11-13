"""One place that decides whether a file name or a folder path is safe to use.

Class of bug this closes: a containment check copied per caller (``config.confined``, ``causelist._inside``,
``signer.key_path``), so a rule added to one was missing from the others, and most file operations had no check at all.
Everything below is the shared rule set; the three old checks now call it.

Who controls a path (one word, one meaning):

* operator-typed: a folder or file the person types on the command line or in the config. The operator already owns
  that folder, so nothing can "contain" it. ``operator_dir`` and ``operator_file`` check its SHAPE only.
* data-derived: a name that comes from data (a case id, an ordinal, a file name found in a folder or a manifest).
  This is the real traversal risk. Every one goes through ``component`` or ``join``.
* fixed: a constant in our code. No check needed.

Threat model, stated plainly: the attacker is operator-typed or data-derived TEXT. It is not a second local process that
changes the operator's folder while we run, so a swap between the check and the use is NOT claimed to be closed.
Callers use ONLY the returned path afterwards, never the original text.

Rules (each has one test and one mutant): R1 empty or dot, R2 separator, R3 colon, R4 control or invisible character,
R5 length, R6 trailing dot or space, R7 Windows device name, R8 escape, R9 absolute or drive-relative names (refused by R2
and R3), R10 cannot be resolved, R11 wrong type, R12 a character Windows does not allow in a name. R6, R7 and R12 apply to
data-derived names (``component``, ``join``) only, not to ``inside`` or the operator checks. The text of a refusal names
the argument (the ``what`` words) and the problem, never the value and never the rule number; the number is in
``PathRefused.rule``. Refuse, never repair: no rule changes the text of a name. Case-insensitive disks,
Unicode normal forms (NFC and NFD) and Windows 8.3 short names are not repaired: on a disk where two spellings are one
folder they can only cause a refusal or a wrong "inside" answer. Hard links and mount points are out of scope (a hard link
inside the base to a file outside resolves inside). The name rules apply on every operating system, so an output file made
here also opens on Windows.

Standard library only (no vendor import).
"""

from __future__ import annotations

import re
from pathlib import Path

from hadavin_sdk.errors import ConfigError

MAX_COMPONENT_BYTES = 255  # one name, in UTF-8 bytes (the usual file system limit)
# ``atomic_write`` names its temp file ".<name>.<16 hex>.tmp": this many bytes more than the name. A file that will be
# written through ``atomic_write`` must therefore have a name of at most MAX_WRITE_NAME_BYTES (one constant, used by the
# writer and by every loader that turns data into a file name, so the two can never disagree).
TEMP_EXTRA_BYTES = 1 + 1 + 16 + 4
MAX_WRITE_NAME_BYTES = MAX_COMPONENT_BYTES - TEMP_EXTRA_BYTES
MAX_PATH_CHARS = 4096  # a whole path, in characters (the usual Linux limit; Windows allows less)

# COM and LPT also come with the superscript digits 1, 2 and 3 (U+00B9, U+00B2, U+00B3), written as escapes here
_DIGITS = "0123456789\u00b9\u00b2\u00b3"
_DEVICE_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$", "CLOCK$"}
    | {f"{prefix}{n}" for prefix in ("COM", "LPT") for n in _DIGITS}
)
# C0 (U+0000-U+001F), DEL, C1 (U+0080-U+009F), the Arabic letter mark (U+061C), zero-width characters and the left and
# right marks (U+200B-U+200F), line and paragraph separators (U+2028, U+2029), bidirectional embeddings (U+202A-U+202E),
# isolates (U+2066-U+2069) and the byte order mark (U+FEFF): they reorder or hide printed text. A raw string, so the
# escapes are read by the regex engine, not pasted into this file.
_CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f\u061c\u200b-\u200f\u2028-\u202e\u2066-\u2069\ufeff]")
# Characters Windows does not allow in a file name (the colon is R3). Refused on every system, as PathRefused.
_WINDOWS_INVALID = re.compile(r'[<>"|?*]')


class PathRefused(ConfigError):
    """A path or name was refused. ``rule`` is R1 to R12. The text names the argument and the problem, never the value."""

    def __init__(self, rule: str, message: str) -> None:
        super().__init__(message)
        self.rule = rule

    def __reduce__(self) -> tuple[type, tuple[str, str]]:
        return (PathRefused, (self.rule, str(self)))  # so copy and pickle keep the rule


def _refuse(rule: str, what: str, text: str) -> PathRefused:
    return PathRefused(rule, f"{what}: {text}")


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
    if len(name.encode("utf-8", errors="surrogatepass")) > MAX_COMPONENT_BYTES:
        raise _refuse("R5", what, "too long")
    if name[-1] in ". ":
        raise _refuse("R6", what, "ends with a dot or space")
    if name.split(".", 1)[0].rstrip(" ").upper() in _DEVICE_NAMES:
        raise _refuse("R7", what, "reserved device name")


def component(name: str, *, what: str) -> str:
    """Refuse unless ``name`` is one safe path component. Returns the same string, never changed."""
    _check_name(name, what)
    return name


# missing or unreadable (OSError), a symlink loop (RuntimeError on 3.12), a NUL in the text (ValueError)
_RESOLVE_ERRORS = (OSError, RuntimeError, ValueError)


def _resolve(path: Path, what: str, *, strict: bool) -> Path:
    try:
        return path.resolve(strict=strict)
    except _RESOLVE_ERRORS:
        raise _refuse(
            "R10", what, "cannot be resolved"
        ) from None  # the OSError text could hold the path


def _check_kind(path: Path, kind: str | None, what: str) -> None:
    if kind == "file" and not path.is_file():
        raise _refuse("R11", what, "not a file")
    if kind == "dir" and not path.is_dir():
        raise _refuse("R11", what, "not a folder")


def _check_length(text: str, what: str) -> None:
    if len(text) > MAX_PATH_CHARS:
        raise _refuse("R5", what, "too long")


def _check_text(text: str, what: str) -> None:
    """R4 for a whole path text (the same character set as for a name), then R5. Explicit: a NUL must not depend on
    ``Path.resolve`` raising."""
    if _CONTROL.search(text):
        raise _refuse("R4", what, "contains a control character")
    _check_length(text, what)


def inside(
    base: Path | str,
    path: Path | str,
    *,
    what: str,
    must_exist: bool = False,
    kind: str | None = None,
) -> Path:
    """The real location of ``path`` (already joined, absolute or relative to the current folder), refused unless it
    lies inside the real location of ``base``. A symlink or junction that leaves the base is refused because resolving
    follows it. Returns the resolved path."""
    _check_text(str(base), what)
    _check_text(str(path), what)
    root = _resolve(Path(base), what, strict=False)
    real = _resolve(Path(path), what, strict=must_exist)
    if not real.is_relative_to(root):
        raise _refuse("R8", what, "path escapes its folder")
    _check_kind(real, kind, what)
    return real


def join(
    base: Path | str,
    *names: str,
    what: str,
    must_exist: bool = False,
    kind: str | None = None,
) -> Path:
    """``base`` plus data-derived names. Each name goes through ``component``; the result is resolved (strictly when
    ``must_exist``) and must lie inside the resolved base. With no names the resolved base is returned (``""`` and
    ``"."`` are not names: R1 refuses them). ``kind`` is ``"file"`` or ``"dir"``."""
    for name in names:
        _check_name(name, what)
    _check_text(str(base), what)
    root = _resolve(Path(base), what, strict=False)
    candidate = root.joinpath(*names)
    _check_text(str(candidate), what)
    real = _resolve(candidate, what, strict=must_exist)
    if not real.is_relative_to(root):
        raise _refuse("R8", what, "path escapes its folder")
    _check_kind(real, kind, what)
    return real


def _operator(path: Path | str, what: str, kind: str, must_exist: bool) -> Path:
    text = str(path)
    _check_text(text, what)
    real = _resolve(Path(path), what, strict=must_exist)
    if must_exist or real.exists():
        _check_kind(real, kind, what)
    return real


def operator_text(path: Path | str, *, what: str) -> None:
    """Shape check only for an operator-typed path that the caller resolves itself (no control characters, not too
    long). Returns nothing: the caller still uses its own resolved path."""
    _check_text(str(path), what)


def operator_dir(path: Path | str, *, what: str, must_exist: bool = True) -> Path:
    """A folder the operator typed: shape checked (no control characters, not too long, resolves, is a folder). There
    is no outer base, so nothing "contains" it. ``must_exist=False`` is for a folder the command will create: a path
    that does not exist yet is accepted, one that exists must still be a folder. Returns the resolved path."""
    return _operator(path, what, "dir", must_exist)


def operator_file(path: Path | str, *, what: str, must_exist: bool = True) -> Path:
    """A file the operator typed: shape checked as for ``operator_dir``, and it must exist and be a file. Returns the
    resolved path. ``must_exist=False`` is for a caller that reads the file next and reports a missing one in its own
    words: only the shape is checked (and the type, when the path exists)."""
    return _operator(path, what, "file", must_exist)


__all__ = [
    "MAX_COMPONENT_BYTES",
    "MAX_PATH_CHARS",
    "MAX_WRITE_NAME_BYTES",
    "TEMP_EXTRA_BYTES",
    "PathRefused",
    "component",
    "inside",
    "join",
    "operator_dir",
    "operator_file",
    "operator_text",
]
