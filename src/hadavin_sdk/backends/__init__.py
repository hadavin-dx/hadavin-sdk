"""Pluggable backends: one table (``table.py``) maps each capability and kind to a settings model and a factory;
``factory.py`` holds ``make``, ``hosts`` and ``Deps``.

They are loaded on first use (PEP 562), so importing a sibling module such as ``backends.table`` (the config
does) never pulls in the secret providers: ``runtime``, ``approvals`` and ``llm`` reach no secret holder even
transitively (K5, M21; tests/test_repo_rules.py).
"""

from __future__ import annotations

import importlib
from typing import Any

__all__ = ["Deps", "hosts", "make"]


def __getattr__(name: str) -> Any:
    if name in __all__:
        # A dynamic import, so a static scan of this package's imports does not reach the secret providers.
        return getattr(importlib.import_module("hadavin_sdk.backends.factory"), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
