"""The one door from tests to demo_only/ (synthetic data, generators, recorded replies). Product code under src/ never reaches demo_only/.

`data_source` is chosen by the environment variable APEXC_DATA_SOURCE (default `demo`):
  demo    use the synthetic data under demo_only/ when the folder exists; tests that need it skip with a clear reason when it is absent
  client  a client deployment: demo_only/ must not be used at all; tests that need demo data skip, and nothing here loads client data
          (the client's own loader, written for that client, does that outside this repo's tests)
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULES_NEEDING_DEMO_DATA = ("test_data.py", "test_rules.py")  # read the gold set at import time


def data_source_name() -> str:
    name = os.environ.get("APEXC_DATA_SOURCE", "demo")
    if name not in ("demo", "client"):
        raise ValueError("APEXC_DATA_SOURCE must be demo or client")
    return name


def demo_root() -> Path | None:
    """The demo_only folder, or None when the source is `client` or the folder was cut away."""
    root = ROOT / "demo_only"
    return root if data_source_name() == "demo" and root.is_dir() else None


def demo_file(*parts: str) -> Path:
    """A file under demo_only/, or skip the calling test with a clear reason."""
    root = demo_root()
    if root is None or not root.joinpath(*parts).exists():
        pytest.skip("needs demo_only/ (synthetic demo data), which is absent or not selected by data_source")
    return root.joinpath(*parts)


def demo_files(*parts: str) -> list[Path]:
    """Like demo_file for scans: the file in a list, or an empty list when demo_only/ is absent."""
    root = demo_root()
    return [root.joinpath(*parts)] if root is not None and root.joinpath(*parts).exists() else []
