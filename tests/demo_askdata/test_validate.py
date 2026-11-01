"""T-E3: the validator (control C1). Attacks are rejected with the tagged rule; benign statements are accepted."""

import hashlib

import pytest
import sqlglot
from askdata.validate import Rejected, prefilter, validate

from .corpus import ATTACKS, BENIGN, NUL


@pytest.mark.parametrize(("name", "sql", "rule"), ATTACKS, ids=[a[0] for a in ATTACKS])
def test_attack_is_rejected_with_the_tagged_rule(name, sql, rule):
    with pytest.raises(Rejected) as caught:
        validate(sql)
    assert caught.value.rule == rule, f"{name}: {caught.value}"


@pytest.mark.parametrize(("name", "sql"), BENIGN, ids=[b[0] for b in BENIGN])
def test_benign_statement_is_accepted_and_canonical_is_stable(name, sql):
    first = validate(sql)
    assert validate(sql) == first  # the same text hashes identically on every run
    assert validate(first.canonical_sql) == first  # the canonical text is a fixed point (identity)
    assert first.sha256 == hashlib.sha256(first.canonical_sql.encode()).hexdigest()
    _, saw_comment = prefilter(first.canonical_sql)
    assert not saw_comment  # no comment survives regeneration
    assert sqlglot.parse_one(first.canonical_sql, read="postgres") == sqlglot.parse_one(
        sql, read="postgres"
    )


def test_comment_markers_inside_literals_are_kept_but_real_comments_vanish():
    canonical = validate(dict(BENIGN)["literals-with-comment-markers"]).canonical_sql
    assert "'a--b'" in canonical and "'c/*d*/'" in canonical and "real comment" not in canonical


def test_nested_block_comment_is_discarded_whole():
    sql = "SELECT 1 /* a /* nested */ still comment */ FROM analytics.orders_v"
    assert validate(sql).canonical_sql == "SELECT 1 FROM analytics.orders_v"


def test_hazards_are_rejected_before_the_parser_sees_them(monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("the parser must not run for raw-text hazards")

    monkeypatch.setattr(sqlglot, "parse", boom)
    for sql in (
        "SELECT 1 AS " + NUL,
        "SELECT 'a" + chr(92) + "'",
        "SELECT $$x$$",
        "SELECT 1 " + chr(0x202E),
    ):
        with pytest.raises(Rejected) as caught:
            validate(sql)
        assert caught.value.rule == "V09"


def test_one_trailing_semicolon_is_fine_two_statements_are_not():
    assert validate("SELECT 1;").canonical_sql == "SELECT 1"
    with pytest.raises(Rejected) as caught:
        validate("SELECT 1;;")
    assert caught.value.rule == "V01"


def test_empty_and_oversized_text_are_rejected():
    for sql, rule in (
        ("", "V01"),
        ("   -- only a comment", "V01"),
        ("SELECT '" + "x" * 5000 + "'", "V09"),
    ):
        with pytest.raises(Rejected) as caught:
            validate(sql)
        assert caught.value.rule == rule


def test_long_string_literal_is_a_size_violation():
    with pytest.raises(Rejected) as caught:
        validate("SELECT '" + "x" * 300 + "' FROM analytics.orders_v")
    assert caught.value.rule == "V10"


def test_rejection_names_a_rule_from_the_registry():
    from askdata.validate import RULES

    assert {a[2] for a in ATTACKS} <= set(RULES)
    assert len(ATTACKS) >= 20 and len(BENIGN) >= 10
