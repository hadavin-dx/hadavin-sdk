"""demo_only/ rule: product code never mentions or opens demo material; a config-selected loader is the only way in. Runs with or without demo_only/."""

import os
from pathlib import Path

import pytest

from dealdesk import data_source
from dealdesk.errors import Malformed

ROOT = Path(__file__).resolve().parent.parent
MARK = "demo" + "_only"  # built from parts so this file is easy to grep for the real references
PRODUCT = [ROOT / "src", ROOT / "config", ROOT / "pyproject.toml"]
ALLOWED_TOP = {
    "tests",
    "tests_oneshot",
    MARK,
    ".github",
    "mutation",
    ".git",
    ".venv",
    "dist",
    "__pycache__",
    ".ruff_cache",
    ".pytest_cache",
}


def _files(p: Path):
    return [p] if p.is_file() else [f for f in p.rglob("*") if f.is_file() and "__pycache__" not in f.parts]


def test_product_code_and_config_never_mention_demo_only():
    hits = [
        f.relative_to(ROOT).as_posix()
        for p in PRODUCT
        for f in _files(p)
        if MARK in f.read_text(encoding="utf-8", errors="ignore")
    ]
    assert hits == []


def test_nothing_outside_the_allowed_places_mentions_it_except_markdown_docs():
    bad = []
    for f in ROOT.iterdir():
        if f.name in ALLOWED_TOP or f.suffix == ".md" or f.name in {"uv.lock", ".gitignore"}:
            continue
        for g in _files(f):
            if MARK in g.read_text(encoding="utf-8", errors="ignore"):
                bad.append(g.relative_to(ROOT).as_posix())
    assert bad == []


def test_the_data_source_is_chosen_by_config_and_unregistered_sources_fail_closed():
    assert data_source.configured_source({}) == "client"  # the default is the client, never the demo
    assert data_source.configured_source({"DEALDESK_DATA_SOURCE": "demo"}) == "demo"
    with pytest.raises(Malformed):
        data_source.configured_source({"DEALDESK_DATA_SOURCE": "typo"})
    saved = dict(data_source._SOURCES)
    try:
        data_source._SOURCES.clear()
        with pytest.raises(Malformed):
            data_source.load_world({})  # `client` has no registered source in this process
        with pytest.raises(Malformed):
            data_source.register_source("typo", lambda: None)
        data_source.register_source("client", lambda: "client-world")
        assert data_source.load_world({}) == "client-world"
    finally:
        data_source._SOURCES.clear()
        data_source._SOURCES.update(saved)


@pytest.mark.skipif(not (ROOT / MARK).exists(), reason="demo_only/ is absent (cut test)")
def test_the_demo_source_registers_itself_when_the_demo_runner_is_imported():
    import importlib
    import sys

    sys.path.insert(0, str(ROOT / MARK))
    try:
        importlib.import_module("run_demo")
    finally:
        sys.path.remove(str(ROOT / MARK))
    assert "demo" in data_source._SOURCES
    assert data_source.load_world({"DEALDESK_DATA_SOURCE": "demo"}) is not None
    assert os.environ.get("DEALDESK_DATA_SOURCE") != "demo"  # selecting it is a configuration act, never an import side effect
