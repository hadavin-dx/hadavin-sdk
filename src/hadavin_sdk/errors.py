"""Errors shared by ``config`` and ``backends``, kept here so neither has to import the other. Also the two helpers
that decide what part of a configuration file may appear in an error text (a leaf module: standard library only)."""

from __future__ import annotations

import re
from typing import Any


class ConfigError(ValueError):
    """The client config is invalid; the process must not start."""


class ConfigValueError(ValueError):
    """A configuration validator's own refusal. THE marker for "Hadavin wrote this sentence": the sentence of a
    `value_error` problem is shown in a config error only when its cause is this class (any other `ValueError`, for
    example one out of `int()`, `float()`, `Decimal()`, `bytes.fromhex` or a library, may quote the value it choked on
    and gets a fixed sentence). Raise it only with a sentence that holds no text taken from the configuration."""


_SHOWABLE = re.compile(r"[a-z0-9_.-]{1,64}")
NOT_SHOWN = "<not shown>"
UNKNOWN_KEY = "<unknown key>"


def shown_name(name: object) -> str:
    """A name taken from a configuration file, safe to put in an error text: shown only when it is a plain identifier
    (`a-z`, `0-9`, `_`, `-`, `.`, 1 to 64 characters, so no capital letter, space, look-alike character or long token),
    otherwise `<not shown>`. A pasted credential can sit where a name belongs, and a credential that happens to look
    like a plain identifier (all lower case letters, digits, `-`, `_` and `.`) would still pass: this is a filter on
    shape, not a secret detector. Wherever the position or the field name is enough, say that instead of the name."""
    if isinstance(name, str) and _SHOWABLE.fullmatch(name):
        return name
    return NOT_SHOWN


def error_where(error: dict[str, Any]) -> str:
    """The place of one pydantic problem (an entry of `ValidationError.errors()`) as a dotted path. A key that the
    model does not know (`extra_forbidden`) is the pasted text itself, so it is replaced by `<unknown key>` and the
    parent path stays; any other name taken from the file (a mapping key) is shown only when `shown_name` allows it;
    positions are numbers and stay."""
    loc = list(error["loc"])
    parts = []
    for i, part in enumerate(loc):
        if isinstance(part, int):
            parts.append(str(part))
        elif error["type"] == "extra_forbidden" and i == len(loc) - 1:
            parts.append(UNKNOWN_KEY)
        else:
            parts.append(shown_name(part))
    return ".".join(parts)
