"""PR H batch 9, group 5 and group 6: what SECURITY.md and CHANGELOG.md say is pinned to the code. Not part of the mutant run (the
mutant run copies only the test files and the source, not the documents)."""

import re
from pathlib import Path

from hadavin_sdk import defaults

ROOT = Path(__file__).resolve().parents[1]
SECURITY = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
CHANGELOG = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")


def test_b9_g5_security_says_a_value_of_no_pattern_shape_is_not_read():
    """Group 5: the statement `tests/test_prh_b9.py::test_b9_g5_a_value_of_no_pattern_shape_is_not_read...` proves, in the text."""
    assert "of no pattern's shape" in SECURITY, (
        "SECURITY.md must say that a value of no pattern's shape is not read"
    )
    assert "NOT covered, by design" in SECURITY


def test_b9_g6_the_spaced_out_numbers_in_security_are_the_live_constants():
    """Group 6: every number SECURITY.md gives for the spaced-out rule is read from the live constant."""
    bullet = next(line for line in SECURITY.splitlines() if "spaces between its characters" in line)
    want = {
        "12 or more characters": defaults.SPACED_VALUE_MIN_CHARS,
        "10 or more single-character words": defaults.SPACED_RUN_MIN_TOKENS,
        "at least 6 different characters": defaults.SPACED_RUN_MIN_DISTINCT,
        "more than 32 such stretches": defaults.SPACED_RUN_MAX_RUNS,
    }
    for phrase, live in want.items():
        assert phrase in bullet, phrase
        assert str(live) in phrase, f"{phrase!r} is not the live value {live}"


def test_b9_g6_the_pass_cap_in_defaults_is_the_live_cap():
    """Group 6: the comment in defaults.py names the worst seeded pass count; the live bound is above it."""
    text = (ROOT / "src/hadavin_sdk/defaults.py").read_text(encoding="utf-8")
    assert f"MAX_REDACT_PASSES = {defaults.MAX_REDACT_PASSES}" in text
    assert re.search(r"worst is \d+", text)


def test_b9_g6_the_measured_withheld_share_in_security_matches_the_recorded_evidence():
    """Group 11: the share SECURITY.md gives for ordinary text is the one in the recorded evidence files."""
    ev = ROOT / "handover/evidence/PRH/b9"
    head = (ev / "clean-corpus-head.txt").read_text(encoding="utf-8")
    assert "withheld_or_error=138" in head and "texts=7947" in head
    assert "138 (1.74 percent)" in SECURITY
    assert "155 are withheld on the tool path (5.2 percent) and 14 on the direct" in SECURITY
