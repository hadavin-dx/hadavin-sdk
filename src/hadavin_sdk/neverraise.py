"""The record kept by the never-raise guards: how many times each one absorbed a failure.

Standard library only. A few functions must never raise into the money or redaction path (the diagnostic emitter, the
provider-facts readers, the retry classifier). Each catches ``Exception``, calls ``record`` with its own closed ``Site``, and
returns its fallback. Only the site is kept, never the exception text (it may come from a hostile provider reply or a
hostile object). ``KeyboardInterrupt`` and ``SystemExit`` are not ``Exception`` subclasses and still propagate.
"""

from __future__ import annotations

import enum
import threading
from collections import Counter
from typing import Final


class Site(enum.StrEnum):
    """Where a guard absorbed a failure (one member per guard in the three files)."""

    diag_attrs_unreadable = "diag_attrs_unreadable"
    diag_provider_class_check = "diag_provider_class_check"
    facts_safe_attr = "facts_safe_attr"
    facts_adapter_hook = "facts_adapter_hook"
    retry_class_text = "retry_class_text"
    retry_close_failed_http = "retry_close_failed_http"
    retry_classify = "retry_classify"
    retry_decision = "retry_decision"
    retry_wait = "retry_wait"


_LOCK: Final = threading.Lock()
_COUNTS: Final[Counter[Site]] = Counter()


def record(site: Site) -> None:
    """Count one absorbed failure at ``site``. Never raises."""
    with _LOCK:
        _COUNTS[site] += 1


def counts() -> dict[str, int]:
    """A copy of the counters, keyed by site name."""
    with _LOCK:
        return {str(site): n for site, n in _COUNTS.items()}


def reset() -> None:
    """Zero the counters (tests)."""
    with _LOCK:
        _COUNTS.clear()
