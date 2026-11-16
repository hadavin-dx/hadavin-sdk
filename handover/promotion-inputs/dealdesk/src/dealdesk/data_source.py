"""Config-selected data source. `data_source` is configuration (environment variable DEALDESK_DATA_SOURCE, default `client`), never code: product code asks
for a source BY NAME and never imports or opens demo material. A client build registers its own `client` source (its CRM and billing readers, behind the
read-only ports); the demo runner registers `demo` (synthetic data) when it is run. An unregistered or unknown name is refused (fail closed), so demo data
cannot reach a client's outputs by default."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping

from dealdesk.errors import Malformed

KNOWN = ("demo", "client")
_SOURCES: dict[str, Callable[[], object]] = {}


def register_source(name: str, factory: Callable[[], object]) -> None:
    if name not in KNOWN:
        raise Malformed(f"unknown data source {name!r}")
    _SOURCES[name] = factory


def configured_source(env: Mapping[str, str] | None = None) -> str:
    name = (os.environ if env is None else env).get("DEALDESK_DATA_SOURCE", "client")
    if name not in KNOWN:
        raise Malformed(f"DEALDESK_DATA_SOURCE must be one of {KNOWN}")
    return name


def load_world(env: Mapping[str, str] | None = None) -> object:
    """Build the world (ports data) from the configured source; raises if that source is not registered."""
    name = configured_source(env)
    factory = _SOURCES.get(name)
    if factory is None:
        raise Malformed(f"data source {name!r} is not registered in this process")
    return factory()
