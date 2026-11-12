"""Errors shared by ``config`` and ``backends``, kept here so neither has to import the other. Also the two helpers
that decide what part of a configuration file may appear in an error text (a leaf module: standard library only)."""

from __future__ import annotations

import os
import re
from collections.abc import Callable, Collection, Iterable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Self


class ConfigError(ValueError):
    """The client config is invalid; the process must not start."""


class ConfigValueError(ValueError):
    """A configuration validator's own refusal. THE marker for "Hadavin wrote this sentence": the sentence of a
    `value_error` problem is shown in a config error only when its cause is this class (any other `ValueError`, for
    example one out of `int()`, `float()`, `Decimal()`, `bytes.fromhex` or a library, may quote the value it choked on
    and gets a fixed sentence). Raise it only with a sentence that holds no text taken from the configuration."""


# A name from a file may appear in an error text only if it is (1) word-like and (2) the id of a thing that was loaded.
# (D-2322, lead decision 2026-11-11.) Word-like = a letter first, then lower case letters, digits, `_`, `-`, `.`, `:`;
# at most 40 characters; no run of 20 or more hex digits or digits (a key, a hash, a token). Not a secret detector:
# a short plain word typed as the id of a loaded thing is shown, because the id of a thing is how a person finds it.
_WORDLIKE = re.compile(r"[a-z][a-z0-9_.:-]{0,39}")
_LONG_RUN = re.compile(r"[0-9a-f]{20,}")
NOT_SHOWN = "<not shown>"
UNKNOWN_KEY = "<unknown key>"

_LOADED: ContextVar[frozenset[str] | None] = ContextVar("hadavin_loaded_ids", default=None)


@contextmanager
def loaded_ids(*groups: Iterable[object]) -> Iterator[None]:
    """While active, `shown_name` shows only the names in these groups (the ids the loader itself has read: agents,
    actions, chains, principals, tools, routes, systems, sources, tool modules, input names). Groups add to the
    names already active. Names the loader did not read (a reference that matched nothing) are shown by position."""
    names = {n for g in groups for n in g if isinstance(n, str)}
    previous = _LOADED.get()
    token = _LOADED.set(frozenset(names) if previous is None else previous | names)
    try:
        yield
    finally:
        _LOADED.reset(token)


def word_like(name: object) -> bool:
    # `type(name) is str`: a `str` subclass may define its own `__str__` or `__eq__` and answer differently from its text
    return type(name) is str and bool(_WORDLIKE.fullmatch(name)) and not _LONG_RUN.search(name)


def shown_name(name: object, loaded: Collection[object] | None = None) -> str:
    """A name taken from a configuration file, safe to put in an error text. Shown only when it is word-like (see
    `_WORDLIKE`: letter first, at most 40 characters, no run of 20 or more digits or hex digits, no capital letter,
    space or look-alike character) AND it is the id of something that was loaded: a member of `loaded` (given by the
    caller) or, if none is given, of the names made active by `loaded_ids` (set by the loaders). Otherwise
    `<not shown>`. With neither, there is no loaded set to compare with and the name is `<not shown>` too (batch 18:
    before, the word-like test alone decided, so a word-like pasted key was printed by a unit called alone). A pasted credential can sit where a name
    belongs: this is a filter on shape and membership, not a secret detector. Wherever the position or the field name
    is enough, say that instead of the name."""
    if not word_like(name):
        return NOT_SHOWN
    names = loaded if loaded is not None else _LOADED.get()
    # no loaded set to compare with: nothing is shown (batch 18; was: shown on shape alone)
    if names is None or name not in names:
        return NOT_SHOWN
    return str.__str__(name)


_DIGEST = re.compile(r"[0-9a-f]{64}")


def is_digest(value: object) -> bool:
    """True for a SHA-256 written as 64 lower-case hex digits (what `tool_module_hashes` must hold)."""
    return isinstance(value, str) and bool(_DIGEST.fullmatch(value))


def digest_prefix(value: object) -> str:
    """The first 12 characters of a digest for an error text, only when `value` really is a digest; a pasted credential
    in a pin position is `<not shown>` (its first characters are never printed)."""
    return f"{value[:12]}..." if isinstance(value, str) and is_digest(value) else NOT_SHOWN


class Failed:
    """Round 13: a block that keeps the error it raised instead of letting it out, and with no `except` handler. Use
    `with Failed() as caught: ...`; after the block, `caught.error` is the error (or None). The error leaves the
    block here, so a new error raised after the block has no cause and no context (nothing the library said can be
    reached from it). An error of a class in `passthrough` and anything that is not an `Exception` (a stop signal)
    pass through as they are."""

    def __init__(self, passthrough: tuple[type[BaseException], ...] = ()) -> None:
        self.error: Exception | None = None
        self._passthrough = passthrough

    def __enter__(self) -> Self:
        return self

    def __exit__(self, kind: object, value: BaseException | None, trace: object) -> bool:
        if not isinstance(value, Exception) or isinstance(value, self._passthrough):
            return False
        self.error = value
        return True


def call_class_only[T](
    call: Callable[[], T],
    make_error: Callable[[str], BaseException],
    *,
    passthrough: tuple[type[BaseException], ...] = (),
) -> T:
    """Round 12, Issue 3 of Q8a-1: run `call`; if it fails, raise `make_error(<class name of the failure>)`. The new
    error is raised AFTER the `except` block, so it has no cause and no context: nothing the library said (it can
    quote a key id, an ARN, a path or a host that the configuration named) can be reached from it, not by its text,
    its repr, its traceback or a debugger. (`raise ... from None` inside the block hides the old error from the
    printed traceback but leaves it in `__context__`.) An error of a class in `passthrough` is raised as it is."""
    with Failed(passthrough) as caught:
        return call()
    raise make_error(type(caught.error).__name__)


def status_text(status: object) -> str:
    """An HTTP status for a message: the number if it is an `int`, else `?`. (`int(x)` would raise a `ValueError` that
    quotes a text; a status that a custom provider returns as a text must not reach a message either.)"""
    # `int.__repr__`, not `str`: an `int` subclass may define its own `__str__` and print any text
    return int.__repr__(status) if isinstance(status, int) and not isinstance(status, bool) else "?"


# The ids the code makes (`new_id(prefix)`): ONLY these prefixes, then a dash and 32 hex digits; for a tool call a colon and a
# counter (`<run id>:<n>`). A test reads every `new_id(...)` call of the package and fails if its prefix is not in this list,
# so a new kind of id is added here on purpose. Any other id (a legacy key, a caller's text, `key-` and 32 hex digits) is `?`.
ID_PREFIXES = ("run", "pln", "apr", "evt", "k1b")
_ID_SHAPE = re.compile(rf"(?:{'|'.join(ID_PREFIXES)})-[0-9a-f]{{32}}(?::[0-9]{{1,6}})?")


def shown_id(value: object) -> str:
    """An id for a message: the id itself if it has the shape of an id this code makes, else `?`. A caller can hand the
    store any text as an id (an argument of the command line, a field of a signed answer); that text must never reach a
    message, so only the shape the code itself makes is shown."""
    return str.__str__(value) if type(value) is str and _ID_SHAPE.fullmatch(value) else "?"


def unreadable(what: str, exc: BaseException) -> ConfigError:
    """The one refusal for a file that exists but cannot be read: a fixed sentence, the place (`what`, a fixed label
    written in code) and the error TYPE only (the error's own text holds the path or the bytes). Raise it `from None`."""
    return ConfigError(f"{what}: cannot be read ({type(exc).__name__})")


def read_configured(
    path: object, what: str, *, binary: bool = False, missing_ok: bool = False
) -> Any:
    """THE one way to read a file whose path comes from the configuration. A missing file gives None when
    `missing_ok`, else the same refusal as any other unreadable file. A folder, a missing permission, a loop of links,
    a name that is too long, a null byte, text that is not UTF-8: `ConfigError(<what> cannot be read (<type>))`, with
    no text from the path or the file."""
    try:
        p = Path(path)  # type: ignore[arg-type]
        return p.read_bytes() if binary else p.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        if missing_ok:
            return None
        raise unreadable(what, exc) from None
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        raise unreadable(what, exc) from None


def list_configured(path: object, what: str, suffix: str) -> list[Path]:
    """The files of a configuration folder with this suffix, sorted; a folder that does not exist is empty, a folder
    that exists but cannot be listed is `ConfigError` (reading it as empty would drop whatever it held)."""
    try:
        names = sorted(os.listdir(Path(path)))  # type: ignore[arg-type]
    except FileNotFoundError:
        return []
    except (OSError, ValueError, TypeError) as exc:
        raise unreadable(what, exc) from None
    return [Path(path) / n for n in names if n.endswith(suffix)]  # type: ignore[arg-type]


def error_where(error: dict[str, Any], *, field_names: bool = False, cleaned: bool = False) -> str:
    """The place of one pydantic problem (an entry of `ValidationError.errors()`) as a dotted path. A key that the
    model does not know (`extra_forbidden`) is the pasted text itself, so it is replaced by `<unknown key>` and the
    parent path stays; any other name taken from the file (a mapping key) is shown only when `shown_name` allows it;
    positions are numbers and stay. `field_names=True` is for a model whose own field names are code-owned text (a
    tool manifest entry): a name is then shown on the word-like test alone, without the loaded-ids membership test
    (the loaded set holds ids from the file, never the names of fields, so the test would hide every field).
    `cleaned=True` is for the problems of a `HiddenInputModel` (every model of this package): `hidden_input.without_input` has
    already replaced each name that is not written in code, so a word-like name that is left is a field name or a loaded id, and
    it is shown (batch 18: `shown_name` alone would hide a field name, because no loaded set holds it)."""
    loc = list(error["loc"])
    parts = []
    for i, part in enumerate(loc):
        if isinstance(part, int):
            parts.append(str(part))
        elif error["type"] == "extra_forbidden" and i == len(loc) - 1:
            parts.append(UNKNOWN_KEY)
        elif field_names or cleaned:
            parts.append(str(part) if word_like(part) else NOT_SHOWN)
        else:
            parts.append(shown_name(part))
    return ".".join(parts)
