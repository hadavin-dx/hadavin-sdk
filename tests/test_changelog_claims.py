"""The Unreleased pathguard entry in CHANGELOG.md makes claims about the code. Each claim below is checked against the code,
so the text cannot drift from what runs."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from hadavin_sdk import pathguard
from hadavin_sdk.config import confined
from hadavin_sdk.errors import ConfigError

ROOT = Path(__file__).resolve().parent.parent
TEXT = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
ENTRY = next(line for line in TEXT.splitlines() if line.startswith("- **One place decides whether"))


def test_the_rule_list_in_the_entry_matches_the_rules():  # R1 to R12
    for rule in (f"R{n}" for n in range(1, 13)):
        assert rule in ENTRY
    assert "(R12)" in ENTRY and "(R10)" in ENTRY and "(R11)" in ENTRY


def test_the_numbers_in_the_entry_are_the_numbers_in_the_code():
    assert f"at most {pathguard.MAX_COMPONENT_BYTES} bytes" in ENTRY
    assert f"at most {pathguard.MAX_PATH_CHARS} characters" in ENTRY
    assert f"{pathguard.MAX_WRITE_NAME_BYTES} bytes" in ENTRY


@pytest.mark.parametrize("name", ["con", "aux", "com1"])
def test_device_names_named_in_the_entry_are_refused(name):
    assert f"`{name}`" in ENTRY
    with pytest.raises(pathguard.PathRefused):
        pathguard.component(name, what="n")


def test_no_nosonar_comment_in_src():
    hits = [p for p in (ROOT / "src").rglob("*.py") if "NOSONAR" in p.read_text(encoding="utf-8")]
    assert hits == []


def test_confined_keeps_its_text_and_a_nul_is_a_config_error(tmp_path):
    assert "path escapes its folder" in ENTRY
    with pytest.raises(ConfigError, match="path escapes its folder"):
        confined(tmp_path, "../x")
    with pytest.raises(ConfigError):
        confined(tmp_path, "a\x00b")


def test_the_entry_does_not_claim_a_scanner_finding_is_cleared():
    assert "does not claim that any SonarCloud finding is cleared" in ENTRY
    assert not re.search(r"(?<!not )\b(clears|fixes) the SonarCloud", ENTRY)


def test_the_exception_list_the_entry_names_exists_and_every_row_has_a_reason():
    path = ROOT / "tests" / "fixtures" / "pathguard_exceptions.txt"
    assert "tests/fixtures/pathguard_exceptions.txt" in ENTRY
    rows = [
        r
        for r in path.read_text(encoding="utf-8").splitlines()
        if r.strip() and not r.startswith("#")
    ]
    assert rows and all("|" in r or "#" in r or len(r.split()) > 2 for r in rows)
