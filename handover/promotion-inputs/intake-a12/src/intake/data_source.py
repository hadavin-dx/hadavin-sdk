"""The only way product code reaches demo data: a loader chosen by config (`data_source` in config/policy.json: `demo` or `client`).

`demo` needs the directory named by the environment variable INTAKE_DEMO_DATA (set by the test fixtures and the run script; there is no default
path, so a client build that forgets to configure a source fails closed instead of reading demo files). `client` is refused here on purpose: a
real engagement wires its own loader (the client's systems, their secret manager) behind this same function. Nothing else in `src/` opens demo data.
"""

from __future__ import annotations

from collections.abc import Mapping
from os import environ as _environ  # private name: no `data_source.os` module is exposed
from pathlib import Path


class DataSourceError(Exception):
    pass


def data_root(policy: Mapping[str, object], env: Mapping[str, str] | None = None) -> Path:
    kind = policy.get("data_source")
    if kind == "client":
        raise DataSourceError("the client data source is wired by the engagement; no loader for it exists in this repository")
    if kind != "demo":
        raise DataSourceError(f"unknown or missing data_source: {kind!r}")
    raw = (_environ if env is None else env).get("INTAKE_DEMO_DATA", "")
    path = Path(raw).resolve() if raw else None
    if path is None or not path.is_dir():
        raise DataSourceError("data_source is demo but INTAKE_DEMO_DATA does not name an existing directory")
    return path
