"""The shared rules for a file name or a folder path, used by the file operations listed by the package tripwire test.

Class of bug this closes: a containment check copied per caller (``config.confined``, ``signer.key_path``), so a rule added to one was
missing from the others, and most file operations had no check at all.
Rung (tool ladder): the older checks' ideas are reused; no library gives one refusal type with the Windows device rules
and containment after resolving links, so this small standard-library module is the one place.

Who controls a path: operator-typed (``operator_dir`` and ``operator_file`` check its SHAPE only), data-derived (a case
id, a file name found in a folder or manifest: every one goes through ``component`` or ``join``), fixed (a constant in
our code: no check). Threat model: the attacker is operator-typed or data-derived TEXT, not a second local process that
changes the folder while we run (a swap between check and use is NOT claimed closed). Callers use ONLY the returned path.

Rules (each has one test and one mutant): R1 empty or dot, R2 separator, R3 colon, R4 control or invisible character
(CONTROL_RANGES), R5 length (the whole path, in at most 4095 bytes, and every name in it, in at most 255; checked on the typed text and again on the
resolved path), R6 trailing dot or space, R7 Windows device name,
R8 escape, R9 absolute or drive-relative names (refused by R2 and R3), R10 cannot be resolved (any error from the
operating system), R11 wrong type, R12 a character Windows does not allow in a name, R13 a write target or temp name that
cannot be used. R6, R7 and R12 apply to names (``component``, ``join``) only. The text of a refusal names the argument
and the problem, never the value or the rule number (that is ``PathRefused.rule``). Refuse, never repair. Case-insensitive
disks, Unicode normal forms and Windows 8.3 names are not repaired. Hard links and mount points are out of scope.
The name rules apply on every system. Standard library only. The rules that read text alone live in ``pathtext``.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.pathtext import (
    CONTROL_RANGES,
    MAX_COMPONENT_BYTES,
    MAX_PATH_BYTES,
    MAX_WRITE_NAME_BYTES,
    PathRefused,
    check_name,
    check_text,
    name_bytes,
    refuse,
)


def component(name: str, *, what: str) -> str:
    """Refuse unless ``name`` is one safe path component. Returns the same string, never changed."""
    check_name(name, what)
    return name


# Errors of the system that make a typed path "cannot be resolved": any OSError (every errno), a NUL (ValueError), a value
# that is not a path (TypeError) and a path nested too deep for the interpreter (RecursionError). A symlink loop is a
# RuntimeError on 3.12 only; any other RuntimeError is not ours and propagates (``_LOOP_TEXT`` names the loop).
_SYSTEM_ERRORS = (OSError, ValueError, TypeError, RecursionError)
_LOOP_TEXT = "Symlink loop"


# The one place that asks the operating system about a typed path: those errors become one refusal with a fixed text (the
# system's own text holds the path). The refusal is raised outside the ``except`` block: no cause and no context.
def _os[T](call: Callable[[], T], what: str) -> T:
    try:
        return call()
    except _SYSTEM_ERRORS:
        refusal = refuse("R10", what, "cannot be resolved")
    except RuntimeError as exc:
        if not str(exc).startswith(_LOOP_TEXT):
            raise
        refusal = refuse("R10", what, "cannot be resolved")
    raise refusal


def _resolve(path: Path | str, what: str, *, strict: bool) -> Path:
    """The real location, measured again: a link can lead to a path longer than the text typed (R4 and R5 on the result)."""
    real = _os(lambda: Path(path).resolve(strict=strict), what)
    check_text(str(real), what)
    return real


def _within(root: Path, path: Path, what: str, must_exist: bool, kind: str | None) -> Path:
    """The one tail of ``inside`` and ``join``: resolved (strictly when ``must_exist``), inside ``root``, of ``kind``."""
    check_text(str(path), what)
    real = _resolve(path, what, strict=must_exist)
    if not real.is_relative_to(root):
        raise refuse("R8", what, "path escapes its folder")
    if kind and not _os(real.is_file if kind == "file" else real.is_dir, what):
        raise refuse("R11", what, "not a file" if kind == "file" else "not a folder")
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
    check_text(str(base), what)
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
        check_name(name, what)
    check_text(str(base), what)
    root = _resolve(base, what, strict=False)
    return _within(root, root.joinpath(*names), what, must_exist, kind)


def _operator(path: Path | str, what: str, kind: str, must_exist: bool) -> Path:
    check_text(str(path), what)
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


def has_entries(path: Path, *, what: str) -> bool:
    """True when the folder ``path`` (already checked) exists and holds something. An error of the system (no right to
    look) is a refusal with a fixed text, not an OSError that carries the path."""
    return _os(lambda: path.exists() and any(path.iterdir()), what)


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
    "has_entries",
    "inside",
    "join",
    "mapped",
    "name_bytes",
    "operator_dir",
    "operator_file",
]
