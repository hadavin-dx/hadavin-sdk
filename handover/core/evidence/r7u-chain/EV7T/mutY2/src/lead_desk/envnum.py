"""The one helper for every number read from setting text (DESK_* environment names, config-file lines).

A bad value is a plain SettingRefused (a ValueError) that names the SETTING and never echoes the value or Python's own
message. Every numeric parse of settings text in src/, scripts/, load_tools/, tools/ and the demo folder goes through
`env_number`, never a bare int(), float() or Decimal() on text that came from the environment."""

from __future__ import annotations

import math
import re
import unicodedata
from collections.abc import Callable, Mapping
from decimal import Decimal
from typing import Any
from urllib.parse import SplitResult, urlsplit

from lead_desk.constants import PORT_MAX

_MISSING: Any = object()
_WHOLE = re.compile(r"[+-]?[0-9]+")  # ASCII digits only: no other-script digits, underscores, spaces or exponent
_DECIMAL = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")


def read_number(text: str, cast: Callable[[str], Any]) -> Any:
    """The ONE reader of a number written as text (a setting, a command-line option, a scenario word, a price). Plain
    ASCII only: a sign, ASCII digits, one point and an exponent. `1_0`, other-script digits, a space inside or around
    the text, `nan` and `inf` are refused (Python's own int(), float() and Decimal() accept all of them, so a typed
    `1_0` would be read as 10 and Arabic-Indic digits as a number). `cast` is int (whole numbers only), float or
    Decimal. Raises ValueError; the message is fixed and holds no typed text. Callers that allow spaces around a value
    strip them first (`env_number` does)."""
    pattern = _WHOLE if cast is int else _DECIMAL
    if not (isinstance(text, str) and text.isascii() and pattern.fullmatch(text)):
        raise ValueError("not a number")
    try:
        value = cast(text)
    except (ValueError, ArithmeticError):  # a whole number of more than 4300 digits, an exponent that overflows
        raise ValueError("not a number") from None
    if isinstance(value, Decimal):
        finite = value.is_finite()
    elif isinstance(value, float):
        finite = math.isfinite(value)
    else:
        finite = True
    if not finite:
        raise ValueError("not a number")
    return value


class SettingRefused(ValueError):
    """A setting holds a value the desk refuses. The message names the setting (its DESK_* or REAL_* name) and never
    the value. `server.main` turns exactly this error into the clean exit 4; any other ValueError is a real bug."""


def env_number(
    env: Mapping[str, str],
    name: str,
    cast: Callable[[str], Any],
    default: Any = _MISSING,
    *,
    low: Any = None,
    high: Any = None,
) -> Any:
    """`cast(env[name])` (or `cast(default)` when the name is absent and a default is given). SettingRefused messages:
    "NAME is not a number" (junk text; after ASCII spaces, tabs and line ends are stripped from both ends, text that is
    not plain ASCII digits, a sign, a point and an exponent; a float or Decimal that is not finite; a whole number that
    is too long) and, when `low` or `high` is given, "NAME must be
    between LOW and HIGH" (or "at least LOW" / "at most HIGH")."""
    raw = default if (default is not _MISSING and name not in env) else env[name]
    if isinstance(raw, str):
        raw = raw.strip(" \t\r\n")  # spaces around a value are harmless (`set X=8765 ` in cmd.exe, env files)
        try:
            read_number(raw, cast)  # the shared ASCII-only reader: the same refusals everywhere
        except ValueError:
            raise SettingRefused(f"{name} is not a number") from None
    try:
        value = cast(raw)
    except (ValueError, ArithmeticError, TypeError):
        raise SettingRefused(f"{name} is not a number") from None
    if isinstance(value, Decimal):
        finite = value.is_finite()
    elif isinstance(value, float):
        finite = math.isfinite(value)
    else:
        finite = True
    if not finite:
        raise SettingRefused(f"{name} is not a number")
    if (low is not None and value < low) or (high is not None and value > high):
        if low is not None and high is not None:
            raise SettingRefused(f"{name} must be between {low} and {high}")
        raise SettingRefused(f"{name} must be at least {low}" if low is not None else f"{name} must be at most {high}")
    return value


def check_url_port(name: str, parts: SplitResult) -> None:
    """A SettingRefused naming `name` when the address has a port that is not a number from 1 to 65535 (`:0` is "any
    port" to a listener and no place to send to; `:99999` and `:abc` cannot be used). No port at all is fine. Why:
    `urlsplit` reads the port lazily, so a bad one passed the settings check and failed later, after a cost line."""
    try:
        port = parts.port
    except ValueError:
        raise SettingRefused(f"{name} has a port that is not a number from 1 to {PORT_MAX}") from None
    if port is not None and not 1 <= port <= PORT_MAX:
        raise SettingRefused(f"{name} has a port that is not a number from 1 to {PORT_MAX}")


def split_url(name: str, text: str) -> SplitResult:
    """`urlsplit(text)` for the value of setting `name`: text that cannot be split (an unclosed bracket such as
    `http://[/`) is a SettingRefused naming the setting, never a bare ValueError. Text with a control character, a
    line break or a space is refused too: urlsplit silently drops tabs and line ends, so such a value would pass the
    checks and still be a different text from the one that is later used. Text that is not plain ASCII is refused as
    well: `urlsplit(...).hostname` lower-cases the host, and a non-ASCII letter such as the Kelvin sign (U+212A) becomes
    an ASCII `k`, so the host that is checked would not be the host that is later dialled."""
    if not text.isascii() or any(unicodedata.category(c) in ("Cc", "Zs", "Zl", "Zp") for c in text):
        raise SettingRefused(f"{name} is not a valid address")
    try:
        return urlsplit(text)
    except ValueError:
        raise SettingRefused(f"{name} is not a valid address") from None
