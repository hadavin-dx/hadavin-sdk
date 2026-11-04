"""P2: the gold set and the exemplars against the validator and the allowlists (design A-10)."""

import json

import pytest
from askdata import derive_allowlist as derive_tool
from askdata.allowed import CAST_TARGETS, FUNCTIONS, LUMEN_VIEWS, VIEWS
from askdata.validate import Rejected, validate
from sqlglot import exp

from tests.demo_askdata.conftest import DEMO

STATEMENTS = derive_tool.gold_statements()


def test_the_lumen_catalog_is_the_dataset_contract():
    assert len(LUMEN_VIEWS) == 7 and "email" not in {
        c for cols in LUMEN_VIEWS.values() for c in cols
    }
    assert set(VIEWS) < set(LUMEN_VIEWS) and VIEWS != LUMEN_VIEWS


@pytest.mark.parametrize(("label", "sql"), STATEMENTS, ids=[s[0] for s in STATEMENTS])
def test_every_gold_query_and_exemplar_validates_on_the_lumen_catalog(label, sql):
    first = validate(sql, views=LUMEN_VIEWS)
    assert (
        validate(first.canonical_sql, views=LUMEN_VIEWS) == first
    )  # canonical text is a fixed point


def test_a_lumen_only_view_is_refused_on_the_default_catalog():
    with pytest.raises(Rejected) as caught:
        validate("SELECT count(*) FROM analytics.refunds_v")
    assert caught.value.rule == "V04"
    assert validate("SELECT count(*) FROM analytics.refunds_v", views=LUMEN_VIEWS).canonical_sql


def test_the_catalog_override_does_not_leak_between_calls():
    validate("SELECT count(*) FROM analytics.refunds_v", views=LUMEN_VIEWS)
    with pytest.raises(Rejected):
        validate("SELECT count(*) FROM analytics.refunds_v")


def test_adversarial_replies_are_refused_with_the_expected_rule_family():
    rows = []
    for name in ("adversarial.jsonl", "adversarial.dev.jsonl"):
        rows += [
            json.loads(x) for x in (DEMO / "data" / name).read_text(encoding="utf-8").splitlines()
        ]
    sql_rows = [r for r in rows if r.get("fixed_reply_sql") and r["expect_outcome"] == "refused"]
    assert sql_rows
    for r in sql_rows:
        with pytest.raises(Rejected):
            validate(r["fixed_reply_sql"], views=LUMEN_VIEWS)


def test_the_committed_allowlist_equals_the_derived_one():
    committed = json.loads(derive_tool.COMMITTED.read_text(encoding="utf-8"))
    assert committed == derive_tool.derive(), (
        "gold changed: run python -m askdata.derive_allowlist --write and review"
    )


def test_everything_the_gold_set_uses_is_allowed_and_the_rest_is_listed_as_unused():
    got = derive_tool.derive()
    assert set(got["functions"]) <= FUNCTIONS and set(got["casts"]) <= CAST_TARGETS
    unused = got["allowed_but_unused_by_gold"]
    assert set(unused["functions"]) == FUNCTIONS - set(got["functions"])
    assert set(unused["casts"]) == CAST_TARGETS - set(got["casts"])


def test_every_node_class_the_gold_set_uses_is_on_the_validators_node_list():
    from askdata.validate import _ALLOWED_NODES

    listed = {c.__name__ for c in _ALLOWED_NODES}
    for name in derive_tool.derive()["nodes"]:
        cls = getattr(exp, name)
        assert name in listed or issubclass(cls, exp.Func), (
            f"{name} is used by gold but is not an allowed node"
        )
