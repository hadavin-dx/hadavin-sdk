"""The CHANGELOG sentences about Pilot and Demo in the redactor (P0t follow-up). Its own file, not tests/test_stage_names.py:
the stage mutant runner (tests/stage_mutants.py) copies only src, tests, tools, demos and docs, so a test that reads the
root CHANGELOG.md cannot sit in the file it runs."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_the_changelog_states_what_is_and_is_not_masked_for_pilot_and_demo():
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
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
    assert "a demo database" not in text, "one word, one meaning: the stage is called demo-stage"
