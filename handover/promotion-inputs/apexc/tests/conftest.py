import json
import socket
import sys
from pathlib import Path

import pytest
from demo_loader import MODULES_NEEDING_DEMO_DATA, data_source_name, demo_file, demo_root

ROOT = Path(__file__).resolve().parents[1]

# Cut test: with demo_only/ deleted these modules (they read the synthetic gold set at import time) are not collected, and the header says so.
if demo_root():
    sys.path[:0] = [str(demo_root() / "data"), str(demo_root())]  # the generator (gen) and the baseline tool, for the tests that use them
collect_ignore = [] if demo_root() else list(MODULES_NEEDING_DEMO_DATA)


def pytest_report_header(config):
    root = demo_root()
    return f"demo_only: {'present' if root else 'ABSENT, skipped modules: ' + ', '.join(MODULES_NEEDING_DEMO_DATA)} (data_source={data_source_name()})"


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """A test fails if a socket opens (definition of done 5)."""

    def boom(*a, **k):
        raise AssertionError("network access attempted in a test")

    monkeypatch.setattr(socket.socket, "connect", boom)
    monkeypatch.setattr(socket, "create_connection", boom)


@pytest.fixture(scope="session")
def pol():
    return json.loads((ROOT / "config" / "policy.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def cases():
    out = []
    for name in ("dev", "test"):
        out += [json.loads(line) for line in demo_file("data", f"{name}.jsonl").read_text(encoding="utf-8").splitlines()]
    return out
