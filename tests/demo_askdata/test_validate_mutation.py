"""P2 mutation test: for each rule V01..V12, switch only that rule off and require that at least one named corpus
attack stops being refused with its tagged rule. A rule no corpus test can see would be a rule nobody notices
breaking (per rule id, not per check site). Mutations go through askdata.validate._OFF, the validator's own switch (empty in production)."""

import askdata.validate as v
import pytest

from tests.demo_askdata.attackrun import outcome
from tests.demo_askdata.corpus import ATTACKS

RULES = sorted(v.RULES)


@pytest.fixture(autouse=True)
def _all_rules_back_on():
    v._OFF.clear()
    yield
    v._OFF.clear()


def broken_with(rule: str) -> dict[str, str]:
    """Attack name -> what happens instead, for every attack that no longer gets its tagged refusal."""
    v._OFF.add(rule)
    try:
        outcomes = {a.name: outcome(a) for a in ATTACKS}
    finally:
        v._OFF.discard(rule)
    return {a.name: outcomes[a.name] for a in ATTACKS if outcomes[a.name] != a.rule}


def test_baseline_every_attack_is_refused_with_its_tag():
    assert {a.name: outcome(a) for a in ATTACKS if outcome(a) != a.rule} == {}


@pytest.mark.parametrize("rule", RULES)
def test_switching_off_one_rule_fails_a_corpus_attack_tagged_with_it(rule):
    broken = broken_with(rule)
    tagged = {a.name for a in ATTACKS if a.rule == rule}
    assert tagged, f"no corpus attack is tagged {rule}"
    assert tagged & set(broken), (
        f"{rule} off: no attack tagged {rule} noticed ({sorted(broken)[:5]})"
    )


# Rules whose attacks the default-deny node list refuses anyway: V02 (root type) and V03 (writes, locks, INTO) are
# backed by "this node class is not allowed" (V10) and by the root check, so switching one off re-labels the refusal.
DEFENCE_IN_DEPTH = {"V02", "V03"}


@pytest.mark.parametrize("rule", RULES)
def test_switching_off_one_rule_lets_an_attack_through_or_a_second_line_refuses_it(rule):
    """Without the rule, either an attack is ACCEPTED (the rule is a real barrier) or, for the two rules with a
    default-deny backstop, every attack is still refused, only by another rule. A crash is never acceptable."""
    broken = broken_with(rule)
    assert not [n for n, o in broken.items() if o.startswith("CRASH")], broken
    if rule in DEFENCE_IN_DEPTH:
        assert broken and all(
            o in {"V02", "V03", "V04", "V10"} - {rule} for o in broken.values()
        ), broken
    else:
        assert "ACCEPTED" in broken.values(), f"{rule} off: nothing was accepted ({broken})"


def test_the_switch_is_empty_by_default():
    assert not v._OFF
