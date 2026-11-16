"""One-shot checks of the TEST split. NOT part of the default run (pyproject testpaths = tests). Run explicitly:

    uv run --group test pytest tests_oneshot --confirm-one-shot

The first run writes eval/test_split_run.json; a second run is refused unless --allow-rerun is given (and the rerun is then recorded). The test
split is a tuned held-out split, NOT sealed: dev holds every builder and deny code, so nothing here can be debugged only on the test split."""

import json
import time
from pathlib import Path

import pytest

MARK = Path(__file__).resolve().parents[1] / "demo_only" / "eval" / "test_split_run.json"


def pytest_addoption(parser):
    parser.addoption("--confirm-one-shot", action="store_true", default=False)
    parser.addoption("--allow-rerun", action="store_true", default=False)


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--confirm-one-shot"):
        skip = pytest.mark.skip(reason="test-split checks run only with --confirm-one-shot")
        for item in items:
            item.add_marker(skip)
        return
    if MARK.exists() and not config.getoption("--allow-rerun"):
        raise pytest.UsageError(f"the test split was already run ({MARK.name}); pass --allow-rerun to run again (recorded)")
    runs = json.loads(MARK.read_text(encoding="utf-8"))["runs"] if MARK.exists() else []
    MARK.write_text(json.dumps({"runs": [*runs, {"at_epoch_s": int(time.time())}]}, indent=2) + "\n", encoding="utf-8")
