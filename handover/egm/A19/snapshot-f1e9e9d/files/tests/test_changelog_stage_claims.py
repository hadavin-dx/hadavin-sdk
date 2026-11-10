"""The CHANGELOG claims about ids and the redactor that code can break (stage follow-up). Its own file, not
tests/test_stage_names.py: the stage mutant runner (tests/stage_mutants.py) copies only src, tests, tools, demos and docs, so
a test that reads the root CHANGELOG.md cannot sit in the file it runs.

Only facts are checked here: the words and numbers the CHANGELOG names equal what the code does. The wording of the
CHANGELOG is not pinned (a sentence that is reworded must not fail a test)."""

import re
from pathlib import Path

import pytest

from hadavin_sdk.commonwords import SWEEP_MIN_DIGITS, SWEEP_MIN_LENGTH
from hadavin_sdk.guard.redact import redact
from hadavin_sdk.guard.runmap import redact_text
from hadavin_sdk.stages import REFUSED_ID_WORDS, check_id

ROOT = Path(__file__).resolve().parents[1]


def unreleased() -> str:
    """The Unreleased section of the CHANGELOG: released history keeps its old wording."""
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    start = text.index("## Unreleased")
    end = text.find("\n## ", start + 1)
    return text[start : end if end != -1 else len(text)]


def entry(prefix: str) -> str:
    return next(p for p in unreleased().split("\n") if p.startswith(prefix))


def test_the_changelog_lists_every_refused_word():
    """The words in the CHANGELOG are the words the code refuses, no more and no fewer.
    The stage mutant runner cannot run this file (it does not copy the root CHANGELOG, and tools/mutation_runner.py is a
    byte copy that the demo repos pin by hash); a dropped word is killed by the literal list in tests/test_tenant_ids.py."""
    text = entry("- **An id may not be a stage word")
    listed = set(re.findall(r"`([a-z]+)`", text.split("as an id,")[1].split(". They are")[0]))
    assert listed == set(REFUSED_ID_WORDS)
    assert f"refuses these {len(REFUSED_ID_WORDS)} words" in text


def test_the_changelog_limits_are_the_redactors_own_numbers():
    text = entry("- **An id the redactor cannot mask is refused.")
    assert f"at least {SWEEP_MIN_LENGTH} characters long" in text
    assert f"from {SWEEP_MIN_DIGITS} digits" in text
    assert f"fewer than {SWEEP_MIN_DIGITS} digits" in text
    assert f"id of 1 or {SWEEP_MIN_LENGTH - 1} characters" in text


def test_the_changelog_examples_of_refused_and_accepted_ids_match_check_id():
    text = entry("- **An id the redactor cannot mask is refused.")
    for refused in ("xy", "ac\x00me", "ac me", "ac.me", "Ünïcode", "аcme", "12345"):
        with pytest.raises(ValueError):
            check_id(refused)
    for word in ("a NUL", "a bell", "a space", "a dot", "an accented letter", "Cyrillic letter"):
        assert word in text, word
    for accepted in ("demos", "prod-1", "preprod"):
        assert f"`{accepted}`" in text
        assert check_id(accepted) == accepted


def test_the_redactor_behaves_as_the_changelog_says_for_pilot_and_demo():
    """What is and is not masked for a tenant named Pilot or Demo (through both `redact` and `redact_text`)."""
    for fn in (lambda t: redact(t).text, lambda t: redact_text(t, {})):
        assert "Pilot" not in fn("tenant_id=Pilot x") and "pilot" not in fn("tenant_id=pilot x")
        assert "Demo" not in fn("customer_id: Demo x")
        assert fn("Pilot and Demo again") == "Pilot and Demo again"  # standing alone: not swept
        assert (
            fn("tenant: Pilot and customer=Demo") == "tenant: Pilot and customer=Demo"
        )  # no `_id`
        assert "acmeco" not in fn("acmeco and tenant_id=acmeco")  # an ordinary id: every copy
        assert "pilot" not in fn("password=pilot and pilot again")  # a secret: every copy
