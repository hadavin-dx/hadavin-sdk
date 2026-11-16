"""The demo-folder rule, checkable with or without the folder: product code never names it or opens a demo file, and the data source is config-selected
(`client` by default; `demo` only when asked, through a module the environment names)."""

import os
import re
from pathlib import Path

import pytest

from refunds import data_source

ROOT = Path(__file__).resolve().parents[1]
DEMO = "demo" + "_only"  # built from parts: this module must stay collectable when the folder is deleted
_SKIP_DIRS = {
    ".venv",
    "__pycache__",
    ".ruff_cache",
    ".pytest_cache",
    ".git",
    "dist",
    "out",
    DEMO,
    "tests",
    "tests_oneshot",
    "mutation",
}
_PRODUCT_FILES = ("pyproject.toml", "uv.lock", ".gitignore", ".gitattributes", ".gitleaksignore")
_FAKE_IDS = re.compile(r"\brefunds-[a-z]-\d{3}\b|\bmsg-\d+-\d{5}\b")


def _product_files():
    for dirpath, dirs, files in os.walk(ROOT):
        here = Path(dirpath)
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS and not d.startswith(".venv")]
        if here == ROOT:
            dirs[:] = [d for d in dirs if d in {"src", ".github"}]
            yield from (here / f for f in files if f in _PRODUCT_FILES)
        else:
            yield from (here / f for f in files if f.endswith((".py", ".yml", ".yaml", ".toml", ".json", ".txt")))


def test_product_code_and_packaging_never_name_the_demo_folder_or_a_fake_record_id():
    hits = []
    for path in _product_files():
        text = path.read_text(encoding="utf-8")
        if DEMO in text or _FAKE_IDS.search(text):
            hits.append(str(path.relative_to(ROOT)))
    assert hits == [], hits
    # documentation (the repo's markdown files) may describe the layout; the rule covers code, config and CI


def test_the_wheel_ships_only_the_package():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'packages = ["src/refunds"]' in pyproject


def test_the_data_source_is_client_by_default_and_demo_needs_a_named_module(monkeypatch):
    for var in ("REFUNDS_DATA_SOURCE", "REFUNDS_DEMO_SOURCE", "REFUNDS_CLIENT_SOURCE", "REFUNDS_PATH"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(data_source.NoSourceConfigured):
        data_source.load()
    with pytest.raises(data_source.NoSourceConfigured):
        data_source.load("demo")
    with pytest.raises(ValueError):
        data_source.load("both")
    monkeypatch.setenv("REFUNDS_DATA_SOURCE", "nonsense")
    with pytest.raises(ValueError):
        data_source.load()


def test_a_client_source_is_just_a_module_the_environment_names(monkeypatch, tmp_path):
    (tmp_path / "my_client_source.py").write_text(
        "class S:\n    def world(self): return {'w': 1}\n    def cases(self): return [{'c': 1}]\n\n\ndef source():\n    return S()\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("REFUNDS_CLIENT_SOURCE", "my_client_source")
    monkeypatch.setenv("REFUNDS_PATH", str(tmp_path))
    s = data_source.load("client")
    assert s.world() == {"w": 1} and s.cases() == [{"c": 1}]
