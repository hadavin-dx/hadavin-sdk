"""T-E3 / P2: the validator (control C1). Attacks are refused with the tagged rule; benign statements are accepted."""

import hashlib

import pytest
import sqlglot
from askdata import validate as validate_module
from askdata.validate import RULES, Rejected, prefilter, validate

from .attackrun import outcome
from .corpus import ATTACKS, BENIGN, NUL

CATEGORIES = {
    "parser-differential", "dollar-quoting", "nested-comments", "escape-strings", "table-functions",
    "qualified-functions", "function-case", "public-functions", "resource-abuse", "casts", "identifier-folding",
    "star-whole-row", "locking", "select-into", "data-modifying-cte", "explain", "multiple-statements", "comments",
    "unicode-lookalikes", "backslash", "cte-scoping", "reparse-identity", "joins", "placeholders",
}  # fmt: skip


@pytest.mark.parametrize("attack", ATTACKS, ids=[a.name for a in ATTACKS])
def test_attack_is_refused_with_the_tagged_rule(attack):
    assert outcome(attack) == attack.rule, attack.name


@pytest.mark.parametrize(("name", "sql"), BENIGN, ids=[b[0] for b in BENIGN])
def test_benign_statement_is_accepted_and_canonical_is_stable(name, sql):
    first = validate(sql)
    assert validate(sql) == first  # the same text hashes identically on every run
    assert validate(first.canonical_sql) == first  # the canonical text is a fixed point
    assert first.sha256 == hashlib.sha256(first.canonical_sql.encode()).hexdigest()
    _, saw_comment = prefilter(first.canonical_sql)
    assert not saw_comment  # no comment survives regeneration
    tree = sqlglot.parse_one(first.canonical_sql, read="postgres")
    # the regenerated SQL re-parses to an identical tree (and regenerates to the same text)
    assert sqlglot.parse_one(tree.sql(dialect="postgres", comments=False), read="postgres") == tree


def test_corpus_meets_the_quotas_and_covers_the_listed_categories():
    assert len(ATTACKS) >= 80 and len(BENIGN) >= 40
    assert len({a.name for a in ATTACKS}) == len(ATTACKS)
    assert {a.rule for a in ATTACKS} == set(RULES), "every rule V01..V12 needs a tagged attack"
    assert CATEGORIES <= {a.category for a in ATTACKS}
    harms = {a.harm.split(":")[0] for a in ATTACKS}
    assert harms <= {"write", "lock", "leak", "exec", "abuse", "pg-refuses", "none"}


def test_comment_markers_inside_literals_are_kept_but_real_comments_vanish():
    canonical = validate(dict(BENIGN)["literals-with-comment-markers"]).canonical_sql
    assert "'a--b'" in canonical and "'c/*d*/'" in canonical and "real comment" not in canonical


def test_nested_block_comment_is_discarded_whole():
    sql = "SELECT 1 /* a /* nested */ still comment */ FROM analytics.orders_v"
    assert validate(sql).canonical_sql == "SELECT 1 FROM analytics.orders_v"


def test_the_parser_never_sees_a_comment():
    """Comments become spaces before sqlglot parses, so two parsers cannot disagree about where one ends."""
    raw = "SELECT 1 /* a /* b */ c */ -- tail\n, 2 FROM x"
    cleaned, saw = prefilter(raw)
    assert saw and len(cleaned) == len(raw)  # same offsets, comments blanked
    assert (
        "tail" not in cleaned
        and "/*" not in cleaned
        and "--" not in cleaned
        and "c" not in cleaned.split("1")[1]
    )
    assert validate("SELECT 1 FROM analytics.orders_v GROUP /**/ BY 1").canonical_sql.endswith(
        "GROUP BY 1"
    )


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


def test_rejection_names_a_rule_from_the_registry():
    assert {a.rule for a in ATTACKS} <= set(RULES)


@pytest.mark.parametrize(
    "tail",
    ["'x'", '"x"', "SELECT 2", ";", "(", "1"],
    ids=["string", "qident", "select", "semicolon", "paren", "digit"],
)
def test_nothing_but_whitespace_or_comments_may_follow_the_first_semicolon(tail):
    with pytest.raises(Rejected) as caught:
        validate("SELECT 1; " + tail)
    assert caught.value.rule == "V01"
    assert validate("SELECT 1; -- done\n /* ok */ ").canonical_sql == "SELECT 1"


def test_mutation_cte_visibility_check_is_what_rejects_forward_references(monkeypatch):
    """Remove the position-aware visibility (every CTE visible everywhere) and the forward reference is accepted."""
    import askdata.validate as v

    sql = "WITH a AS (SELECT * FROM b), b AS (SELECT 1 AS x) SELECT * FROM a"
    with pytest.raises(Rejected) as caught:
        validate(sql)
    assert caught.value.rule == "V04"
    monkeypatch.setattr(v, "_visible_ctes", lambda node: {"a", "b"})
    assert validate(
        sql
    ).canonical_sql  # accepted without the visibility logic: the test sees the rule


def test_generator_normalisation_is_accepted_when_the_new_tree_passes_and_settles():
    """sqlglot adds a CAST inside ROUND(AVG(x), 2). The canonical text must still be a fixed point that passes every
    rule: the tree of the text that RUNS is what is checked (before P2 this benign statement was a false V11)."""
    got = validate("SELECT round(avg(total_amount), 2) FROM analytics.orders_v")
    assert (
        got.canonical_sql
        == "SELECT ROUND(CAST(AVG(total_amount) AS DECIMAL), 2) FROM analytics.orders_v"
    )
    assert validate(got.canonical_sql) == got


def test_a_generator_that_does_not_settle_is_v11_and_a_sound_one_is_fine():
    drift = next(a for a in ATTACKS if a.category == "reparse-identity")
    assert outcome(drift) == "V11"
    assert validate(drift.sql).canonical_sql == drift.sql  # the same text with the real generator


def test_an_unexpected_exception_inside_the_checks_becomes_a_refusal(monkeypatch):
    import askdata.validate as v

    def boom(*args, **kwargs):
        raise AttributeError("a malformed tree")

    monkeypatch.setattr(v, "_check_node", boom)
    with pytest.raises(Rejected) as caught:
        validate("SELECT 1")
    assert caught.value.rule == "V10"


def test_node_limit_is_2000_and_rejects_with_v10(monkeypatch):
    assert validate_module.MAX_NODES == 2000
    sql = "SELECT order_id, customer_id FROM analytics.orders_v WHERE status = 'paid'"
    assert validate(sql)
    monkeypatch.setattr(validate_module, "MAX_NODES", 5)
    with pytest.raises(Rejected) as caught:
        validate(sql)
    assert caught.value.rule == "V10" and "nodes" in caught.value.detail
