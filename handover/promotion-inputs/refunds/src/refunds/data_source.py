"""The one door to case and world data (config-selected).

`data_source` is read from the environment variable REFUNDS_DATA_SOURCE:
  * `client` (the default): the data comes from the client's own systems through a source the build supplies; this repository ships none, so asking for
    it without one raises `NoSourceConfigured`. A client build sets REFUNDS_CLIENT_SOURCE to the module that provides `source()`.
  * `demo`: the synthetic demo source. REFUNDS_DEMO_SOURCE names the module that provides `source()` and REFUNDS_PATH lists the directory to import it
    from. Nothing in the product code names that folder or opens a demo file: delete it and everything but the demo runner still works.

A source object has `world() -> dict` and `cases() -> list[dict]` (both plain JSON-shaped data).
"""

from __future__ import annotations

import importlib
import os
import sys
from typing import Protocol


class NoSourceConfigured(RuntimeError):
    pass


class Source(Protocol):
    def world(self) -> dict: ...

    def cases(self) -> list[dict]: ...


def load(kind: str | None = None) -> Source:
    kind = kind or os.environ.get("REFUNDS_DATA_SOURCE", "client")
    if kind not in ("demo", "client"):
        raise ValueError(f"data_source must be 'demo' or 'client', got {kind!r}")
    var = "REFUNDS_DEMO_SOURCE" if kind == "demo" else "REFUNDS_CLIENT_SOURCE"
    module = os.environ.get(var)
    if not module:
        raise NoSourceConfigured(f"data_source={kind}: set {var} to the module that provides source()")
    for extra in reversed([p for p in os.environ.get("REFUNDS_PATH", "").split(os.pathsep) if p]):
        if extra not in sys.path:
            sys.path.insert(0, extra)
    return importlib.import_module(module).source()
