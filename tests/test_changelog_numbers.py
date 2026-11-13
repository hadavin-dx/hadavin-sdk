"""The numbers the CHANGELOG states about the mode banner and the demo-only guard are checked against the code here, one
test per number-bearing sentence. Each number is read from the code (or computed by the code's own rule), and each sentence
is found by a pattern with word boundaries, so "five passes" is not matched inside "fifteen passes"."""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

from tools import demo_only_guard as g

from tests.test_demo_only_guard import LISTING_FILES, SUPERSET_FILE

ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

WORD = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven"}


def count_of(phrase_after: str) -> list[int]:
    """The counts written as words (one ... seven) before `phrase_after` anywhere in the CHANGELOG."""
    inverse = {v: k for k, v in WORD.items()}
    found = re.findall(rf"\b({'|'.join(inverse)})\s+{phrase_after}", CHANGELOG, flags=re.IGNORECASE)
    return [inverse[w.lower()] for w in found]


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: the CHANGELOG does not state a number of masker passes
def test_the_changelog_says_the_masker_has_as_many_passes_as_the_code_lists() -> None:
    said = count_of(r"passes\b")
    assert said, "the CHANGELOG does not state a number of masker passes"
    assert set(said) == {len(g._MASK_PASSES)}, (
        f"the CHANGELOG says {sorted(set(said))} passes, the code lists {len(g._MASK_PASSES)}"
    )


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: assert None
def test_the_changelog_limits_of_the_bearer_and_basic_rules_are_the_numbers_of_their_patterns() -> (
    None
):
    bearer = int(re.search(r"\{(\d+),\}", g._BEARER.pattern).group(1))
    basic = int(re.search(r"\{(\d+),", g._BASIC.pattern).group(1))
    assert (bearer, basic) == (12, 8)
    assert re.search(rf"\bbearer needs {bearer} characters, basic {basic}\b", CHANGELOG)
    assert re.search(
        rf"\ba token of {bearer - 1} characters or fewer after a bearer word stays visible\b",
        CHANGELOG,
    )
    # and the code agrees with the sentence: 11 stays visible, 12 is hidden
    token = "a" * (bearer - 1)
    assert token in g._hide_secrets(f"x Bearer {token}"), (
        "a token one short of the limit was hidden"
    )
    assert token + "a" not in g._hide_secrets(f"x Bearer {token}a")


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: the CHANGELOG does not say 'Three listings of the tracked files'
def test_the_three_equal_listings_and_the_one_superset_are_the_files_the_changelog_names() -> None:
    # the number is the length of the table that the listing test compares, not a literal typed here
    count = WORD[len(LISTING_FILES)].capitalize()
    assert re.search(rf"\b{count} listings of the tracked files\b", CHANGELOG), (
        f"the CHANGELOG does not say '{count} listings of the tracked files'"
    )
    assert re.search(r"\bthe fourth place\b", CHANGELOG) and len(LISTING_FILES) + 1 == 4
    for name in LISTING_FILES:
        assert (ROOT / name).is_file(), f"{name} is named as one of the listings and is not a file"
        assert name in CHANGELOG, f"{name} is not named in the CHANGELOG"
    assert (ROOT / SUPERSET_FILE).is_file()
    assert SUPERSET_FILE in CHANGELOG
    # the decision text of the listing test is in the CHANGELOG too
    assert "core has no shared helper" in CHANGELOG, "the decision text is not in the CHANGELOG"
    assert "is only checked to hold every tracked file" in CHANGELOG


# fail-before (real run on dd827d79, batch 12): it FAILS there, first failing line: assert None
def test_the_changelog_pyc_range_is_the_rule_of_the_code_with_the_numbers_of_its_two_interpreters() -> (
    None
):
    def top(magic: int) -> int:
        return min(8191, max(3999, magic + 1000))

    # the magic numbers of the final releases (3.12: 3531, 3.14: 3627) are typed here from the interpreters' own tables, and the
    # figures are worked out by the same rule as `_PYC_MAGIC_MAX`: they are "from the formula", not measured on 3.14 (CI runs
    # 3.12 and 3.13; only the interpreter running this test is checked against the code, below)
    assert (top(3531), top(3627)) == (4531, 4627)
    assert re.search(
        r"\b4531 on Python 3\.12, 4627 on Python 3\.14 \(from the formula; CI runs 3\.12 and 3\.13\)",
        CHANGELOG,
    )
    assert re.search(r"\bat least 3999, never above 8191\b", CHANGELOG)
    assert re.search(r"\bfrom 3000 up to a limit\b", CHANGELOG)
    running = int.from_bytes(importlib.util.MAGIC_NUMBER[:2], "little")
    assert g._PYC_MAGIC_MAX == top(running), (
        "the limit of the code is not the rule the CHANGELOG states"
    )
    table = {(3, 12): 4531, (3, 14): 4627}
    if sys.version_info[:2] in table:
        assert g._PYC_MAGIC_MAX == table[sys.version_info[:2]]


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_the_changelog_size_cap_and_head_length_are_the_numbers_of_the_code() -> None:
    assert g.MAX_FILE_BYTES == 8 * 1024 * 1024
    assert re.search(r"\b8 MiB\b", CHANGELOG)
    toml = (ROOT / "tools/demo_only_guard.toml").read_text(encoding="utf-8")
    assert re.search(rf"\bmax_file_bytes = {g.MAX_FILE_BYTES}\b", toml)
    assert re.search(r"\bThe first 512 bytes decide\b", CHANGELOG)
    # a mark after the first 512 bytes is not looked at
    assert g._magic_kind(b"\x00" * 512 + b"PK\x03\x04") == ""


# fail-before (real run on dd827d79, batch 12): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_the_changelog_names_four_product_folders_and_the_settings_list_them() -> None:
    assert re.search(
        r"\bover four product folders \(`src`, `templates`, `tools`, `demos`\)", CHANGELOG
    )
    toml = (ROOT / "tools/demo_only_guard.toml").read_text(encoding="utf-8")
    assert re.search(
        r'product_roots\s*=\s*\[\s*"src",\s*"templates",\s*"tools",\s*"demos"\s*\]', toml
    )
