"""Errors shared by ``config`` and ``backends``, kept here so neither has to import the other. Also the two helpers
that decide what part of a configuration file may appear in an error text (a leaf module: standard library only)."""

from __future__ import annotations

import os
import re
from collections.abc import Callable, Collection, Iterable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Any


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
    return isinstance(name, str) and bool(_WORDLIKE.fullmatch(name)) and not _LONG_RUN.search(name)


def shown_name(name: object, loaded: Collection[object] | None = None) -> str:
    """A name taken from a configuration file, safe to put in an error text. Shown only when it is word-like (see
    `_WORDLIKE`: letter first, at most 40 characters, no run of 20 or more digits or hex digits, no capital letter,
    space or look-alike character) AND it is the id of something that was loaded: a member of `loaded` (given by the
    caller) or, if none is given, of the names made active by `loaded_ids` (set by the loaders). Otherwise
    `<not shown>`. With neither, there is no loaded set to compare with and only the word-like test applies (a name
    printed before anything was loaded, or by a unit that is called alone). A pasted credential can sit where a name
    belongs: this is a filter on shape and membership, not a secret detector. Wherever the position or the field name
    is enough, say that instead of the name."""
    if not word_like(name):
        return NOT_SHOWN
    names = loaded if loaded is not None else _LOADED.get()
    if names is not None and name not in names:
        return NOT_SHOWN
    return str(name)


_DIGEST = re.compile(r"[0-9a-f]{64}")


def is_digest(value: object) -> bool:
    """True for a SHA-256 written as 64 lower-case hex digits (what `tool_module_hashes` must hold)."""
    return isinstance(value, str) and bool(_DIGEST.fullmatch(value))


def digest_prefix(value: object) -> str:
    """The first 12 characters of a digest for an error text, only when `value` really is a digest; a pasted credential
    in a pin position is `<not shown>` (its first characters are never printed)."""
    return f"{value[:12]}..." if isinstance(value, str) and is_digest(value) else NOT_SHOWN


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
    failure = None
    try:
        return call()
    except passthrough:
        raise
    except Exception as exc:  # noqa: BLE001 - THE one place that turns any library failure into its class name only
        failure = type(exc).__name__
    raise make_error(failure)


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


def error_where(error: dict[str, Any], *, field_names: bool = False) -> str:
    """The place of one pydantic problem (an entry of `ValidationError.errors()`) as a dotted path. A key that the
    model does not know (`extra_forbidden`) is the pasted text itself, so it is replaced by `<unknown key>` and the
    parent path stays; any other name taken from the file (a mapping key) is shown only when `shown_name` allows it;
    positions are numbers and stay. `field_names=True` is for a model whose own field names are code-owned text (a
    tool manifest entry): a name is then shown on the word-like test alone, without the loaded-ids membership test
    (the loaded set holds ids from the file, never the names of fields, so the test would hide every field)."""
    loc = list(error["loc"])
    parts = []
    for i, part in enumerate(loc):
        if isinstance(part, int):
            parts.append(str(part))
        elif error["type"] == "extra_forbidden" and i == len(loc) - 1:
            parts.append(UNKNOWN_KEY)
        elif field_names:
            parts.append(str(part) if word_like(part) else NOT_SHOWN)
        else:
            parts.append(shown_name(part))
    return ".".join(parts)
