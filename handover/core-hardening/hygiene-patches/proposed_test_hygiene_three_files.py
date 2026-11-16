"""PROPOSED test (copy to tests/ after the three HY patches are applied). Not collected here: file name does not start with test_.
Negative control: the scan below MUST find the old problem in text built from parts, so a scanner that went blind would fail.
Positive checks: the three files are UTF-8 and carry no entry of the BANNED list of tests/test_no_reference_material.py."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARD = (ROOT / "tests" / "test_no_reference_material.py").read_text(encoding="utf-8")
BANNED = tuple(re.findall(r'"([^"]+)"', re.search(r"BANNED = \((.*?)\n\)", GUARD, re.S).group(1)))
THREE = (
    "handover/BRIEF-PREAMBLE-studio-2026-11-06.md",
    "handover/demo/portal/portal-design-v2.md",
    "handover/reviews/P1a-idempotence-probe.txt",
)


def problems(raw: bytes):
    """Same two failure kinds as test_no_vendor_brand_string_is_tracked: not UTF-8, or a banned entry."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return ["not UTF-8"]
    return [f"banned entry {i}" for i, s in enumerate(BANNED) if s in text]


def test_scanner_still_sees_both_old_problems():
    old_brand = ("see the " + BANNED[3] + " bar").encode()  # built from the list, never typed here
    assert problems(old_brand) == ["banned entry 3"]
    assert problems(b"ik(\xd8)") == ["not UTF-8"]  # the old probe line: one cp1252 byte


def test_the_three_files_are_clean():
    found = {rel: problems((ROOT / rel).read_bytes()) for rel in THREE}
    assert not any(found.values()), found


def test_the_probe_keeps_its_meaning():
    text = (ROOT / THREE[2]).read_text(encoding="utf-8")
    assert "same_person('BØB','bob'): False" in text
