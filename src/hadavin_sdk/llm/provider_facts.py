"""Checked facts about a failed provider call: a number in a fixed range, a word from a fixed list, a short token of a fixed shape.

A fact is never free text. This module is neutral: it imports only the standard library, ``hadavin_sdk.codes`` and
``hadavin_sdk.neverraise`` (itself standard library only) and names no vendor. Every check lives in one ``clean_*`` function; the error classes (``llm/protocol.py``) and ``ProviderFacts`` both call
them, so no check is written twice. An invalid value is DROPPED to ``None``; nothing here raises on a bad value.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Final

from hadavin_sdk.codes import (
    FACT_BOUNDS,
    REQUEST_ID_SHAPES,
    STATUS_ERROR_TYPE,
    FactKey,
    ProviderErrorType,
)
from hadavin_sdk.neverraise import Site, record

# The longest string looked up in a closed vendor table (the longest key has 29 characters), so the bound changes no result.
TYPE_NAME_MAX: Final = 64

_SHAPES: Final = {name: re.compile(pattern) for name, pattern in REQUEST_ID_SHAPES.items()}


def _bounded(key: FactKey, value: object) -> int | None:
    lo, hi = FACT_BOUNDS[key]
    return value if type(value) is int and lo <= value <= hi else None  # type: ignore[return-value]


def clean_status(value: object) -> int | None:
    """An exact ``int`` (not a ``bool``) from 100 to 599."""
    return _bounded(FactKey.http_status, value)


def clean_count(value: object) -> int | None:
    """An exact ``int`` from 0 to 1000."""
    return _bounded(FactKey.retry_count, value)


def clean_flag(value: object) -> bool | None:
    return value if type(value) is bool else None


def clean_error_type(value: object) -> ProviderErrorType | None:
    """A member of ``ProviderErrorType`` by exact type; a plain string is refused."""
    return value if type(value) is ProviderErrorType else None  # type: ignore[return-value]


def clean_request_id(value: object, shape: str | None = None) -> str | None:
    """A plain ``str`` that ``fullmatch``es one closed shape (or only ``shape``, a key of ``REQUEST_ID_SHAPES``)."""
    if type(value) is not str:
        return None
    patterns = _SHAPES.values() if shape is None else [_SHAPES[shape]] if shape in _SHAPES else []
    for pattern in patterns:
        if pattern.fullmatch(value) is not None:
            return str.__str__(value)
    return None


@dataclass(frozen=True)
class ProviderFacts:
    """What an adapter learned from one failed call. Direct construction never raises: an invalid field is dropped."""

    status: int | None
    error_type: ProviderErrorType | None
    request_id: str | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", clean_status(self.status))
        object.__setattr__(self, "error_type", clean_error_type(self.error_type))
        object.__setattr__(self, "request_id", clean_request_id(self.request_id))


NO_FACTS: Final = ProviderFacts(None, None, None)


def safe_attr(obj: object, name: str) -> object | None:
    """``getattr`` that gives ``None`` when the lookup raises an ``Exception`` (a hostile property)."""
    try:
        return getattr(obj, name, None)
    except Exception:  # noqa: BLE001 - never-raise guard: a property that raises is "no value", never a raise into the adapter
        record(Site.facts_safe_attr)
        return None


def status_error_type(status: object) -> ProviderErrorType | None:
    """The error type a checked status implies, or ``None``."""
    valid = clean_status(status)
    return None if valid is None else STATUS_ERROR_TYPE.get(valid)


def safe_facts(hook: Callable[[BaseException], ProviderFacts], exc: BaseException) -> ProviderFacts:
    """``hook(exc)`` if it returns exactly a ``ProviderFacts``; ``NO_FACTS`` if it raises an ``Exception`` or returns anything else.

    A ``BaseException`` that is not an ``Exception`` (``KeyboardInterrupt``, ``SystemExit``) propagates."""
    try:
        got = hook(exc)
    except Exception:  # noqa: BLE001 - never-raise guard: an adapter failure must not replace the real provider error
        record(Site.facts_adapter_hook)
        return NO_FACTS
    return got if type(got) is ProviderFacts else NO_FACTS
