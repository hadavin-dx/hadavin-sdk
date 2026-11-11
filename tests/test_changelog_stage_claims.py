"""The CHANGELOG sentences about Pilot and Demo in the redactor (P0t follow-up). Its own file, not tests/test_stage_names.py:
the stage mutant runner (tests/stage_mutants.py) copies only src, tests, tools, demos and docs, so a test that reads the
root CHANGELOG.md cannot sit in the file it runs."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def unreleased() -> str:
    """The Unreleased section of the CHANGELOG: released history keeps its old wording."""
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    start = text.index("## Unreleased")
    end = text.find("\n## ", start + 1)
    return text[start : end if end != -1 else len(text)]


def test_the_changelog_states_what_is_and_is_not_masked_for_pilot_and_demo():
    text = unreleased()
    sentences = [
        (
            "a tenant or customer named `Pilot` or `Demo` is masked where an id label such as `tenant_id` or "
            "`customer_id` gives it (`tenant_id=Pilot`, `customer_id: Demo`; the lower-case `tenant_id=pilot` too), "
            "but the same word standing alone is not swept"
        ),
        (
            "a label without `_id` is not read by the tenant rule at all, so `tenant: Pilot` and `customer=Demo` are "
            "not masked anywhere"
        ),
        (
            "because the redactor sweeps every copy of a secret that is 4 characters or longer "
            "(`demo` has 4, `pilot` has 5)"
        ),
        "through both `redact` and `redact_text`",
    ]
    for sentence in sentences:
        assert sentence in text, sentence
    # Order 126 worded the repair as "demo-stage database"; order 132 added "databases of the demo repos". The split is
    # deliberate (the repair entry names both groups); the id entry says "including the databases of the demo repos".
    # Only the bare phrase that blurs the two groups is refused here, in the repair entry.
    repair = next(
        p for p in text.split("\n") if p.lstrip().startswith("- **Repair every demo-stage database")
    )
    assert not re.search(r"\b(?:a|the) demo database", repair.lower()), (
        "say demo-stage database or demo repo database"
    )


def test_the_changelog_states_the_id_rule_its_words_and_its_limit():
    text = unreleased()
    for sentence in [
        "`hadavin_sdk.stages.check_id` (and `check_tenant_id` for tenants) refuses these 29 words",
        "`hadavin_sdk/commonwords.py`, imported by both the redactor and `stages.py`",
        "`config.TenantId`, `OrgId`, `CustomerId`, `AccountId` and `UserId`",
        "including the databases of the demo repos",
        "are now stage words",
        "no id is created or stored on this branch",
        "the check guards no live path yet",
        "`model_construct` skips it",
    ]:
        assert sentence.lower() in text.lower(), sentence


def test_the_changelog_lists_every_refused_word():
    """The 29 words in the CHANGELOG are the words the code refuses, no more and no fewer.
    The stage mutant runner cannot run this file (it does not copy the root CHANGELOG, and tools/mutation_runner.py is a
    byte copy that the demo repos pin by hash); a dropped word is killed by the literal list in tests/test_tenant_ids.py."""
    from hadavin_sdk.stages import REFUSED_ID_WORDS

    text = unreleased()
    entry = next(p for p in text.split("\n") if p.startswith("- **An id may not be a stage word"))
    listed = set(re.findall(r"`([a-z]+)`", entry.split("as an id,")[1].split(". They are")[0]))
    assert listed == set(REFUSED_ID_WORDS)
    assert f"refuses these {len(REFUSED_ID_WORDS)} words" in entry


def test_the_repair_entry_names_both_groups_and_what_the_merge_commit_sentence_covers():
    text = unreleased()
    for sentence in [
        "Repair every demo-stage database and every database of the demo repos",
        "a demo-stage database, one used by the stage named `demo`",
        "a database of one of the demo repos (for example `ask-your-data`), whatever stage it runs in",
        "The merge-commit sentence covers both groups",
    ]:
        assert sentence in text, sentence


def test_the_entries_added_by_this_change_are_each_at_most_a_thousand_characters():
    """The stage and id entries are split so each can be read; other entries (released history included) are not
    measured."""
    prefixes = (
        "- **Breaking: the first stage is now called `demo`",
        "- **One question for the stage guards.",
        "- **Redactor, ",
        "- **No stage is stored yet.",
        "- **An id may not be",
        "- **Id field types.",
        "- **Why an id may not be",
        "- **Stage scan:",
        "- **Limits of the id check.",
        "- **What the id check does not refuse.",
    )
    lines = unreleased().split("\n")
    for prefix in prefixes:
        found = [ln for ln in lines if ln.startswith(prefix)]
        assert found, f"no entry starts with {prefix!r}"
        for ln in found:
            assert len(ln) <= 1000, f"{len(ln)} characters: {ln[:60]}"


def test_the_changelog_short_and_odd_ids_match_the_code():
    """The not-refused entry says a 2-character id is refused only if listed (`db`), and that a control character or a
    space inside an id is not refused. Each claim is checked against check_id."""
    import pytest

    from hadavin_sdk.stages import check_id

    entry = next(
        p
        for p in unreleased().split("\n")
        if p.startswith("- **What the id check does not refuse.")
    )
    assert "`db` is on the list and is refused" in entry
    assert "An id of 1 or 2 characters that is not on the list (`xy`;" in entry
    for text in ("category Cc", "`de\\x00mo`, `d emo`"):
        assert text in entry, text
    with pytest.raises(ValueError):
        check_id("db")
    assert check_id("xy") == "xy"
    assert check_id("de\x00mo") == "de\x00mo"
    assert check_id("d emo") == "d emo"
