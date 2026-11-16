"""Offline guard (contract DoD item 5) and the test-split open spy (design review 6, M9).

The spy records every file the default run opens through `open`, `io.open`, `Path.open/read_text/read_bytes`. If any of them is a test-split data file
(`test.jsonl`, `world_test.json`), the run FAILS at the end. A static scan cannot see a built path or a glob; this sees the open itself. What it does
NOT see: a subprocess, `os.open`, `mmap`, or `sqlite3`. And the default run is still COUPLED to the test split's CONTENT: `tests/test_data.py`
regenerates the split in memory from `data/gen.py` and the seeds and compares hashes, so a change to the generator changes what the default run checks.
"""

import builtins
import io
import socket
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo_only"
if DEMO.is_dir():
    sys.path.insert(0, str(DEMO))  # the demo source package (loaded only through refunds.data_source) lives there

TEST_SPLIT_NAMES = {"test.jsonl", "world_test.json"}
_opened: list[str] = io.__dict__.setdefault(
    "_hadavin_opened", []
)  # shared by name: pytest may import this file under two module names
_real_open, _real_io_open = builtins.open, io.open


def _spy(real):
    def wrapper(file, *a, **k):
        if isinstance(file, (str, Path)):
            _opened.append(Path(file).name)
        return real(file, *a, **k)

    return wrapper


def pytest_configure(config):
    builtins.open = _spy(_real_open)
    io.open = _spy(_real_io_open)


def pytest_unconfigure(config):
    builtins.open, io.open = _real_open, _real_io_open


def pytest_sessionfinish(session, exitstatus):
    touched = sorted({n for n in _opened if n in TEST_SPLIT_NAMES})
    if touched:
        session.exitstatus = 1
        print(f"\nTEST-SPLIT FILE OPENED BY THE DEFAULT RUN: {touched}")


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("network access attempted in a test")

    for name in ("connect", "connect_ex", "sendto", "send", "sendall"):
        monkeypatch.setattr(socket.socket, name, boom)
    monkeypatch.setattr(socket, "create_connection", boom)
    monkeypatch.setattr(socket, "getaddrinfo", boom)


# ---- the cut test: with the demo folder deleted, modules that need demo data are left out of collection (and listed in the header); the rest must stay green
_NEEDS_DEMO = (
    "demo_only",
    "import reference",
    "import ingest_model",
    "import wgkit",
    "import worldkit",
    "from wgkit",
    "from worldkit",
    "from reference",
)
_left_out: list[str] = []


def pytest_ignore_collect(collection_path, config):
    if DEMO.is_dir() or collection_path.suffix != ".py" or not collection_path.name.startswith("test_"):
        return None
    if any(m in collection_path.read_text(encoding="utf-8") for m in _NEEDS_DEMO):
        _left_out.append(collection_path.name)
        return True
    return None


def pytest_report_header(config):
    if not DEMO.is_dir():
        return "demo folder absent (cut test): test modules that need demo data are left out of collection; see the list in the terminal summary"
    return None


def pytest_terminal_summary(terminalreporter):
    if _left_out:
        terminalreporter.write_line("left out because the demo folder is absent: " + ", ".join(sorted(_left_out)))
