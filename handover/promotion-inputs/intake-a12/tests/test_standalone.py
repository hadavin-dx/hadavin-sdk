"""Standalone-repo guards: no internal-workspace traces in tracked files, demo data reachable only through the config-selected loader, nothing outside the
demo-data folder and the tests names it, the wheel carries none of it. Patterns are assembled from fragments so this file does not match itself."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from intake import data_source

ROOT = Path(__file__).resolve().parents[1]
BS = chr(92)
DEMO_DIR = "demo" + "_" + "only"

LEAK = re.compile(
    "|".join(
        [
            "e" + "gm" + "[" + BS + BS + "/]",
            "hand" + "off" + "[" + BS + BS + "/]",
            "bi" + "ble" + "[" + BS + BS + "/]",
            "Bho" + "vix" + " Lab",
            "bho" + "vix" + "_tools",
            "studio" + " folder",
            r"(?-i:\bR[0-9]{2,3}\b)",  # a numbered internal rule reference (the demo's own ids are R-INTAKE-nnn, which do not match)
            r"[A-Za-z]:" + BS + BS + r"(?:Users|bho" + "vix)",
            "Down" + "loads" + BS + BS,
            "users" + r"\.noreply\.github",
            "Keth" + "ari",
            "ve" + "era" + "rak" + "esh",
        ]
    ),
    re.I,
)
INVISIBLE = re.compile(
    "["
    + "".join(chr(c) for r in ((0x200B, 0x200F), (0x202A, 0x202E), (0x2060, 0x2064), (0xFEFF, 0xFEFF)) for c in range(r[0], r[1] + 1))
    + "]"
)


def _tracked() -> list[Path]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [ROOT / f for f in out.split("\0") if f]


def _text(p: Path) -> str | None:
    try:
        return p.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def test_no_internal_workspace_traces_or_invisible_characters_in_tracked_files():
    bad = []
    for p in _tracked():
        t = _text(p)
        if t is None or "core_copy" in p.parts:
            continue
        for rx in (LEAK, INVISIBLE):
            if rx.search(t):
                bad.append((p.relative_to(ROOT).as_posix(), rx.pattern[:12]))
    assert not bad, bad


# files that must name the folder to configure or exercise the cut: the build config, the attributes file, the readme, the CI workflow, the mutation tool
FOLDER_NAMING_ALLOWED = {"pyproject.toml", ".gitattributes", "README.md", ".gitignore", "tools/mutate_src.py", "tools/docfacts.py"}


def test_nothing_outside_the_demo_folder_and_tests_names_it():
    bad = []
    for p in _tracked():
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith((DEMO_DIR + "/", "tests/", ".github/")) or rel in FOLDER_NAMING_ALLOWED:
            continue
        t = _text(p)
        if t is not None and DEMO_DIR in t:
            bad.append(rel)
    assert not bad, bad


def test_product_code_never_opens_demo_data_except_through_the_loader():
    for p in (ROOT / "src" / "intake").rglob("*.py"):
        if "core_copy" in p.parts:
            continue
        t = p.read_text(encoding="utf-8")
        assert DEMO_DIR not in t, p
        if p.name != "data_source.py":
            assert "INTAKE_DEMO_DATA" not in t, p


def test_build_config_packages_only_the_product_source():
    t = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'packages = ["src/intake"]' in t
    assert DEMO_DIR not in (ROOT / "src" / "intake" / "__init__.py").read_text(encoding="utf-8")
    assert not list((ROOT / "src").rglob(DEMO_DIR))


def test_the_loader_is_config_selected_and_fails_closed(tmp_path, monkeypatch):
    monkeypatch.delenv("INTAKE_DEMO_DATA", raising=False)
    with pytest.raises(data_source.DataSourceError):
        data_source.data_root({"data_source": "demo"}, env={})
    with pytest.raises(data_source.DataSourceError):
        data_source.data_root({"data_source": "demo"}, env={"INTAKE_DEMO_DATA": str(tmp_path / "missing")})
    assert data_source.data_root({"data_source": "demo"}, env={"INTAKE_DEMO_DATA": str(tmp_path)}) == tmp_path.resolve()
    for other in ({"data_source": "client"}, {"data_source": "x"}, {}, {"data_source": None}):
        with pytest.raises(data_source.DataSourceError):
            data_source.data_root(other, env={"INTAKE_DEMO_DATA": str(tmp_path)})


def test_the_shipped_policy_selects_the_demo_source_and_no_credentials_are_tracked():
    import json

    assert json.loads((ROOT / "config" / "policy.json").read_text(encoding="utf-8"))["data_source"] == "demo"
    key = re.compile("AK" + r"IA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY")
    for p in _tracked():
        t = _text(p)
        if t is None or "core_copy" in p.parts:
            continue
        for m in key.finditer(t):
            assert m.group(0) == "AK" + "IAIOSFODNN7EXAMPLE", (p.name, "secret-shaped text")


def test_cut_marker_the_run_header_says_so_when_the_demo_folder_is_absent():
    from conftest import DEMO, NEEDS_DEMO_DATA, collect_ignore

    assert (collect_ignore == []) == DEMO.is_dir()
    assert all((ROOT / "tests" / n).exists() for n in NEEDS_DEMO_DATA)
