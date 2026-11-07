"""Child process body for the import-order check: it imports modules in the given order and nothing else (standard library only)."""

from __future__ import annotations

import importlib


def import_in_order(modules: tuple[str, ...]) -> None:
    """A cycle or a missing import raises here, so the child's exit code is not 0."""
    for name in modules:
        importlib.import_module(name)


def record_while_holding_the_lock() -> None:
    """A guard that runs while this thread is already inside ``neverraise.record`` (a finalizer, a signal handler) must not block."""
    from hadavin_sdk import neverraise

    with neverraise._LOCK:
        neverraise.record(neverraise.Site.facts_safe_attr)
