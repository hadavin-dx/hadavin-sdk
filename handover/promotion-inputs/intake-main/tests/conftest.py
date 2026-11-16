"""Demo-data gate. The synthetic cases, generators and recorded replies live in the demo-data folder at the repo root; a client repository has that folder
deleted (the cut test). Test modules that need it are not collected when it is absent, and the run header says so; every other test still runs."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo_only"
NEEDS_DEMO_DATA = [
    "test_contract.py",
    "test_data.py",
    "test_faults.py",
    "test_inbound_isolation.py",
    "test_port_no_write.py",
    "test_review4.py",
    "test_review5.py",
    "test_rules.py",
    "test_segregation_purpose.py",
]
collect_ignore = [] if DEMO.is_dir() else list(NEEDS_DEMO_DATA)


def pytest_report_header(config):
    if collect_ignore:
        return f"demo-data folder absent (cut test): {len(collect_ignore)} test modules that need demo data are NOT collected"
    return None


@pytest.fixture(autouse=True)
def _demo_data_env(monkeypatch):
    if DEMO.is_dir():
        monkeypatch.setenv("INTAKE_DEMO_DATA", str(DEMO))
