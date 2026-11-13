"""The numbers the CHANGELOG states about the mode banner and the demo-only guard are checked against
the code here, one test per number-bearing sentence. Each number is read from the code (or computed
by the code's own rule), and each sentence is found by a pattern with word boundaries, so "five
passes" is not matched inside "fifteen passes"."""

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

    # the magic numbers of the final releases (3.12: 3531, 3.14: 3627) are typed here from the
    # interpreters' own tables, and the
    # figures are worked out by the same rule as `_PYC_MAGIC_MAX`: they are "from the formula", not
    # measured on 3.14 (CI runs
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


# fail-before (real run on c7eb5c79, batch 13): it FAILS there, first failing line: AssertionError: the CHANGELOG does not list READ_ERRORS as the code has it: (the old head has only the private `_READ_ERRORS`, read below)
def test_the_changelog_names_the_exact_error_types_the_banner_reads_and_the_card_delivery_catches() -> (
    None
):
    from hadavin_sdk import app as app_mod
    from hadavin_sdk import mode_banner as mb

    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    read = ", ".join(f"`{t.__name__}`" for t in mb.READ_ERRORS)
    assert f"({read}; one tuple, defined once" in text, (
        f"the CHANGELOG does not list READ_ERRORS as the code has it: {read}"
    )
    delivery = ", ".join(f"`{t.__name__}`" for t in app_mod._DELIVERY_ERRORS)
    assert f"only for {_and_list(app_mod._DELIVERY_ERRORS)} (`_DELIVERY_ERRORS`)" in text, (
        f"the CHANGELOG does not give the full delivery list as the code has it: {delivery}"
    )
    assert "`build` does NOT fail" not in text, "the old, wider sentence is still there"


def _and_list(kinds: tuple[type, ...]) -> str:
    names = [f"`{t.__name__}`" for t in kinds]
    return ", ".join(names[:-1]) + " and " + names[-1]


# fail-before (real run on dd827d79, batch 14): it FAILS there, first failing line: AssertionError: the source has 0 `except READ_ERRORS` sites; update the CHANGELOG, the docstrings and the tests
# fail-before (real run on c7eb5c79, batch 14): it FAILS there, first failing line: AssertionError: the source has 0 `except READ_ERRORS` sites; update the CHANGELOG, the docstrings and the tests
def test_the_changelog_counts_the_read_error_sites_as_the_source_has_them() -> None:
    sites = sum(
        (ROOT / "src/hadavin_sdk" / name).read_text(encoding="utf-8").count("except READ_ERRORS")
        for name in ("app.py", "mode_banner.py")
    )
    assert sites == 6, (
        f"the source has {sites} `except READ_ERRORS` sites; update the CHANGELOG, the docstrings and the tests"
    )
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "used by all six `except READ_ERRORS` sites" in text, (
        "the CHANGELOG does not say how many sites there are"
    )


# fail-before (real run on dd827d79, batch 14): it FAILS there, first failing line: AssertionError: the log rule is not in the CHANGELOG: `banner_or_unconfirmed` logs a warning on every call
# fail-before (real run on c7eb5c79, batch 14): it FAILS there, first failing line: AssertionError: the log rule is not in the CHANGELOG: `banner_or_unconfirmed` logs a warning on every call
def test_the_changelog_states_the_log_rule_of_each_path_of_the_banner() -> None:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    for phrase in (
        "`banner_or_unconfirmed` logs a warning on every call",
        "`App.mode_banner()` calls it, so a banner that cannot be built is logged on every call, not once",
        "`_warn_once` covers only the sealing in `build`, the read of the connected parts and the read of `registry.tools`",
        "the source check logs nothing and the words of the banner log at debug level",
    ):
        assert phrase in text, f"the log rule is not in the CHANGELOG: {phrase}"


# fail-before (real run on dd827d79, batch 14): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
# fail-before (real run on c7eb5c79, batch 14): it PASSES there. A pin: it keeps a behaviour from breaking and is not proof of a fix.
def test_pin_a_banner_that_cannot_be_built_is_logged_on_every_call_by_the_app_and_by_the_function(
    tmp_path, monkeypatch, caplog
) -> None:
    import logging

    from tests.test_mode_banner import _sealed_app

    def boom(*_a, **_k):
        raise RuntimeError("unreadable")

    from hadavin_sdk import mode_banner as mb

    app = _sealed_app(tmp_path, "log1")
    monkeypatch.setattr(mb, "banner_from_config", boom)
    caplog.set_level(logging.WARNING)
    for _ in range(3):
        app.mode_banner()
    lines = [r for r in caplog.records if "could not be built" in r.getMessage()]
    assert len(lines) == 3, f"expected one warning per call, got {len(lines)}"
    assert all(
        "RuntimeError" in r.getMessage() and "unreadable" not in r.getMessage() for r in lines
    )


# fail-before: not run on the old heads (it reads the CHANGELOG text of this head only); it fails when the sentence is removed.
def test_the_changelog_says_what_the_masker_is_compared_with() -> None:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "the core redactor `hadavin_sdk.guard.redact`" in text, (
        "the CHANGELOG does not name what the masker is compared with"
    )
    assert "`tools/demo_only_guard.py` is new in this branch" in text, (
        "the CHANGELOG does not say the guard is new"
    )


# -- batch 15: the one paragraph that states the masker, claim by claim
# --------------------------------------------------- (input, what the masker gives, whether the
# core redactor changes the input at all)
MASKER_CLAIMS = [
    ("Bearer a1b2c3", "Bearer <hidden>", False),
    ("Basic abc1", "Basic <hidden>", False),
    ("Basic abc-defghijklmno", "Basic <hidden>", False),
    ("Basic abc-defghijklmn", "Basic abc-defghijklmn", False),
    ("authorization=Bearer abcdefgh", "authorization=<hidden>", True),
    ('authorization=Bearer "abc def"', "authorization=<hidden>", False),
    ('authorization=Digest username="a", response="b"', "authorization=<hidden>", True),
    ("bypass=true x", "bypass=<hidden> x", False),
    ("Authorization: Foo bar", "Authorization: <hidden>", False),
    ("bypass_key=x", "bypass_key=<hidden>", False),
    ("bypass=1", "bypass=1", True),
    ("bypass=0", "bypass=0", True),
    ("bypass=true", "bypass=true", False),
    ("Bearer abcdefghijk", "Bearer abcdefghijk", False),
    ("Basic abcdefg", "Basic abcdefg", False),
    ("password: hunter2", "password: hunter2", True),
    ('"token": "x"', '"token": "x"', True),
    ("--password x", "--password x", False),
    ('"authorization": "Bearer x"', '"authorization": "Bearer x"', False),
    (
        "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ4In0.c2ln",
        "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ4In0.c2ln",
        True,
    ),
    ("Zm9vYmFyYmF6cXV4cXV1eA", "Zm9vYmFyYmF6cXV4cXV1eA", False),
    ("Cookie: sid=abc123def456", "Cookie: sid=abc123def456", True),
]


def _masker_paragraph() -> str:
    marker = "the line masker (batch 15).**"
    (para,) = [ln for ln in CHANGELOG.split("\n") if marker in ln]
    return para


# fail-before: it cannot run on the old heads (the paragraph and the claim table are new); it fails when a claim and the code differ.
def test_every_example_of_the_masker_paragraph_gives_the_stated_result_in_the_masker_and_the_core() -> (
    None
):
    from hadavin_sdk.guard import redact

    wrong = []
    for text, masked, core_changes in MASKER_CLAIMS:
        got = g._hide_secrets(text)
        core = redact(text).text != text
        if got != masked or core != core_changes:
            wrong.append((text, got, core))
    assert not wrong, (
        f"examples whose result is not the stated one (input, masker, core changes it): {wrong}"
    )


def test_every_example_of_the_claim_table_is_written_in_the_masker_paragraph() -> None:
    para = _masker_paragraph()
    missing = [text for text, _, _ in MASKER_CLAIMS if f"`{text}`" not in para]
    assert not missing, f"examples of the table that the paragraph does not show: {missing}"


def test_the_masker_text_does_not_say_it_is_the_core_or_that_it_only_hides_more() -> None:
    banned = (
        "follows the core",
        "all on the hiding side",
        "never shows less",
        "exactly as in the core",
    )
    source = (ROOT / "tools" / "demo_only_guard.py").read_text(encoding="utf-8")
    start = source.index("# The line masker `_hide_secrets`")
    comments = source[start : source.index("_BEARER = re.compile(")]
    for where, text in (("CHANGELOG.md", CHANGELOG), ("the masker comment of the guard", comments)):
        found = [b for b in banned if b in text]
        assert not found, f"{where} says {found}"
    for where, text in (
        ("the masker paragraph", _masker_paragraph()),
        ("the masker comment", comments),
    ):
        assert not re.search(r"\bexactly\b", text), f"{where} says 'exactly'"
