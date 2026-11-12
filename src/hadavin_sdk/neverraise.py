"""The one record kept by the never-raise guards: how many times each one absorbed a failure.

Standard library only, so ``guard/diagnostic.py`` (which must not import ``llm``) can use it. A few functions must never raise
into the money or redaction path (the diagnostic emitter, the provider-facts readers, the retry classifier). Each catches
``Exception``, calls ``record`` with its own closed ``Site``, and returns its fallback. Only the site is kept, never the exception
text (it may come from a hostile provider reply or a hostile object). ``KeyboardInterrupt`` and ``SystemExit`` are not
``Exception`` subclasses and still propagate.

A site counts a guard that absorbed a FAULT (a hook that crashed, a property that raised). It never counts ordinary control
flow: a provider error that is retried or refused as designed is not recorded.
"""

from __future__ import annotations

import enum
import threading
from collections import Counter
from typing import Final


class Site(enum.StrEnum):
    """Where a guard absorbed a failure (one member per guard in the three files; ``diag_*`` are the guards of
    ``guard/diagnostic.py``, named as its ``_guard_failed`` calls name them)."""

    diag_named_class = "diag_named_class"
    diag_class_name = "diag_class_name"
    diag_own_code = "diag_own_code"
    diag_provider_attrs = "diag_provider_attrs"
    diag_counted_module = "diag_counted_module"
    diag_locator = "diag_locator"
    diag_validation_text = "diag_validation_text"
    diag_group_member = "diag_group_member"
    diag_provider_class = "diag_provider_class"
    diag_diagnose = "diag_diagnose"
    diag_render = "diag_render"
    facts_safe_attr = "facts_safe_attr"
    facts_adapter_hook = "facts_adapter_hook"
    retry_class_text = "retry_class_text"
    retry_close_failed_http = "retry_close_failed_http"
    retry_decision = "retry_decision"
    retry_wait = "retry_wait"


# Reentrant: a finalizer or signal handler that runs a guard on the thread that is already inside ``record`` must not deadlock.
_LOCK: Final = threading.RLock()
_COUNTS: Final[Counter[Site]] = Counter()


def record(site: Site) -> None:
    """Count one absorbed failure at ``site``. Never raises."""
    with _LOCK:
        _COUNTS[site] += 1


def counts() -> dict[str, int]:
    """A copy of the counters, keyed by site name."""
    with _LOCK:
        return {str(site): n for site, n in _COUNTS.items()}
