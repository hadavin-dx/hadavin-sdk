"""Execute every gold SQL (both formulations) on two stand-in Lumen Goods databases and require agreement.

The stand-in (`lumen_standin.py`) is NOT the real seed A/B of phase P1. When those exist, run
`goldcheck.check_execution` against them through `PgSource` and commit the result hashes beside the data; until then
this test is the evidence that the SQL is executable, deterministic and free of the NULL-ordering and tie hazards.
"""

from __future__ import annotations

import secrets
from collections.abc import Iterator
from functools import partial

import psycopg
import pytest

from tests.demo_askdata.gold_runner import dsn_for, load_goldcheck, load_standin, make_runner

gc = load_goldcheck()


def _scalar(conn: psycopg.Connection, sql: str):
    return conn.execute(sql).fetchone()[0]


@pytest.fixture(scope="module")
def dbs(admin_dsn: str) -> Iterator[tuple[psycopg.Connection, psycopg.Connection]]:
    tag = "askdata_gold_" + secrets.token_hex(4)
    maint = psycopg.connect(dsn_for(admin_dsn, "postgres"), autocommit=True)
    conns = []
    try:
        for side, seed in (("a", 20261101), ("b", 20261102)):
            maint.execute(f'CREATE DATABASE "{tag}_{side}"')  # generated name, not input
            conn = psycopg.connect(dsn_for(admin_dsn, f"{tag}_{side}"), autocommit=True)
            conns.append(conn)
            load_standin(conn, seed)
        yield conns[0], conns[1]
    finally:
        for c in conns:
            c.close()
        for side in "ab":
            maint.execute(f'DROP DATABASE IF EXISTS "{tag}_{side}" WITH (FORCE)')
        maint.close()


def test_the_standin_has_the_traps_the_gold_depends_on(dbs):
    for conn in dbs:
        one = partial(_scalar, conn)
        assert (
            one(
                "SELECT COUNT(DISTINCT shipping_country) FROM shop.orders WHERE shipping_country IN ('UK', 'GB')"
            )
            == 2
        )
        assert one("SELECT COUNT(*) FROM shop.support_tickets WHERE csat_score IS NULL") > 0
        assert one("SELECT COUNT(*) FROM shop.support_tickets WHERE closed_at IS NULL") > 0
        assert (
            one(
                "SELECT COUNT(*) FROM shop.customers c WHERE NOT EXISTS (SELECT 1 FROM shop.orders o WHERE o.customer_id = c.customer_id)"
            )
            > 0
        )
        assert (
            one(
                "SELECT COUNT(*) FROM shop.products p WHERE NOT EXISTS (SELECT 1 FROM shop.order_items i WHERE i.product_id = p.product_id)"
            )
            > 0
        )
        assert (
            one(
                "SELECT COUNT(*) FROM shop.order_items i JOIN shop.products p USING (product_id) WHERE i.unit_price < p.list_price"
            )
            > 0
        )
        assert one("SELECT COUNT(DISTINCT fl_cd) FROM shop.orders") == 3


def test_every_gold_query_has_two_formulations_that_agree_on_both_databases(dbs):
    gold = gc.read_jsonl(gc.DATA / "gold.jsonl")
    out = gc.check_execution(gold, make_runner(dbs[0]), make_runner(dbs[1]))
    assert out["problems"] == []
    # 52 answerable x 2 formulations x 2 databases, plus interpretations, plus tie probes
    assert out["executed"] >= 280
    assert len(out["hashes"]) == sum(g["kind"] == "answerable" for g in gold) + sum(
        len(g["accepted_interpretations"]) for g in gold if g["kind"] == "ambiguous"
    )


def test_the_two_databases_differ_so_agreement_is_not_a_coincidence(dbs):
    gold = [g for g in gc.read_jsonl(gc.DATA / "gold.jsonl") if g["id"] in ("D20", "T11", "T19")]
    out = gc.check_execution(gold, make_runner(dbs[0]), make_runner(dbs[1]))
    assert all(h["a"] != h["b"] for h in out["hashes"].values())


def test_the_standin_is_reproducible_for_one_seed():
    from tests.demo_askdata.lumen_standin import build

    first, second = build(20261101), build(20261101)
    assert first == second
