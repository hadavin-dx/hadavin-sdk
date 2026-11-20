"""M3 of review AB-3: the spend and reservation statements of the store name their schema, so a table of the same
name elsewhere on the search path is never read or written. The store runs in a non-default schema, with decoy
tables of the same names in `public` (on the search_path, behind the real schema) and in `pg_temp` (searched first
by an unqualified name). The decoys are proven to exist and to hold rows; after every store call they must be
unchanged, and the real tables must hold the results.

The audit chain's own statements live in audit/chain.py (outside this change) and are not covered here."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

from psycopg import sql
from psycopg.conninfo import make_conninfo

from hadavin_sdk.models import new_id
from tests.test_spend_reservations_pg import AGENT, DAY, reservation_world  # noqa: F401  (the "w" fixture)

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)

D = Decimal
TABLES = ("spend", "spend_month", "spend_reservations")
DECOY_AGENT = "decoy-agent"


def _snapshot(db, schema):
    out = {}
    for t in TABLES:
        q = sql.SQL("SELECT * FROM {}.{} ORDER BY 1, 2").format(
            sql.Identifier(schema), sql.Identifier(t)
        )
        out[t] = [tuple(r) for r in db.execute(q).fetchall()]
    return out


def _decoys(w, store):
    """Decoys in public and in pg_temp, each holding one row of DECOY_AGENT. Returns a cleanup function."""
    real = sql.Identifier(w.schema)
    made = []
    with w.admin() as db:
        for t in TABLES:
            ident = sql.Identifier(t)
            assert db.execute("SELECT to_regclass(%s)", (f"public.{t}",)).fetchone()[0] is None
            db.execute(
                sql.SQL("CREATE TABLE public.{} (LIKE {}.{} INCLUDING DEFAULTS)").format(
                    ident, real, ident
                )
            )
            made.append(t)
            for r in w.roles:
                db.execute(sql.SQL("GRANT ALL ON public.{} TO {}").format(ident, sql.Identifier(r)))
    for t in TABLES:
        ident = sql.Identifier(t)
        store._db.execute(
            sql.SQL("CREATE TEMPORARY TABLE {} (LIKE {}.{} INCLUDING DEFAULTS)").format(
                ident, real, ident
            )
        )
    for target in (sql.SQL("public."), sql.SQL("")):
        for text, args in (
            ("INSERT INTO {}spend (agent_id, day, usd) VALUES (%s, %s, 7)", (DECOY_AGENT, DAY)),
            (
                "INSERT INTO {}spend_month (agent_id, month, usd) VALUES (%s, %s, 7)",
                (DECOY_AGENT, DAY.replace(day=1)),
            ),
            (
                (
                    "INSERT INTO {}spend_reservations (reservation_id, agent_id, day, reserved_usd, status, "
                    "created_at) VALUES (%s, %s, %s, 7, 'open', now() - interval '2 days')"
                ),
                (new_id("res"), DECOY_AGENT, DAY),
            ),
        ):
            store._db.execute(sql.SQL(text).format(target), args)

    def cleanup():
        with w.admin() as db:
            for t in made:
                db.execute(sql.SQL("DROP TABLE IF EXISTS public.{}").format(sql.Identifier(t)))

    return cleanup


def test_spend_and_reservation_statements_never_touch_a_same_named_table_elsewhere(w):
    scoped = make_conninfo(w.dsn, options=f"-c search_path={w.schema},public")
    rt = w.store(w.runtime, scoped)
    pu = w.store(w.purge, scoped)
    assert rt._schema == w.schema
    cleanup = _decoys(w, rt)
    try:
        before_public = _snapshot(rt._db, "public")
        before_temp = {
            t: rt._db.execute(
                sql.SQL("SELECT * FROM pg_temp.{} ORDER BY 1, 2").format(sql.Identifier(t))
            ).fetchall()
            for t in TABLES
        }
        assert all(before_public[t] and before_temp[t] for t in TABLES), "the decoys must hold rows"

        rid = new_id("res")
        rt.reserve_spend(rid, AGENT, DAY, D("2.00"), day_cap=D("100"), month_cap=D("100"))
        rt.settle_spend(rid, D("1.50"))
        assert rt.add_spend(AGENT, DAY, D("1.00")) == (D("2.50"), D("2.50"))
        assert rt.spend_totals(AGENT, DAY) == (D("2.50"), D("2.50"))
        assert rt.spend_totals(DECOY_AGENT, DAY) == (D(0), D(0))
        rid2 = new_id("res")
        rt.reserve_spend(rid2, AGENT, DAY, D("1.00"), day_cap=D("100"), month_cap=D("100"))
        assert (
            rt.expire_spend_reservations(0) == 1
        )  # the decoys' open rows are old too, and must not count
        pu.purge_spend_reservations(datetime(2999, 1, 1, tzinfo=UTC))

        assert [r[0] for r in w.run("SELECT agent_id FROM spend")] == [AGENT]
        assert _snapshot(rt._db, "public") == before_public
        after_temp = {
            t: rt._db.execute(
                sql.SQL("SELECT * FROM pg_temp.{} ORDER BY 1, 2").format(sql.Identifier(t))
            ).fetchall()
            for t in TABLES
        }
        assert after_temp == before_temp
    finally:
        cleanup()


def test_the_money_function_calls_name_their_schema_so_a_temporary_function_never_answers(w):
    """Step 3: reserve, settle, expire, purge and add_spend are calls of `<schema>.hadavin_*`. A function of the same
    name and argument types in `pg_temp`, searched FIRST when the session says so, must never be called: each decoy
    raises, and the real functions must do the work."""
    rt = w.store(w.runtime)
    pu = w.store(w.purge)
    decoys = {
        "hadavin_reserve_spend": "(p_id text, p_agent text, p_day date, p_usd numeric, p_day_cap numeric, "
        "p_month_cap numeric, p_run_id text) RETURNS void",
        "hadavin_settle_spend": "(p_id text, p_actual numeric, p_agent text) RETURNS SETOF record",
        "hadavin_expire_spend_reservations": "(p_age_s integer) RETURNS bigint",
        "hadavin_purge_spend_reservations": "(p_before timestamptz) RETURNS bigint",
        "hadavin_add_spend": "(p_agent text, p_day date, p_usd numeric) RETURNS record",
    }
    for db in (rt._db, pu._db):
        for name, signature in decoys.items():
            db.execute(
                f"CREATE FUNCTION pg_temp.{name}{signature} LANGUAGE plpgsql AS "
                "$$ BEGIN RAISE EXCEPTION 'decoy was called'; END $$"
            )
        db.execute(sql.SQL("SET search_path = pg_temp, {}").format(sql.Identifier(w.schema)))
    rid = new_id("res")
    rt.reserve_spend(rid, AGENT, DAY, D("2.00"), day_cap=D("100"), month_cap=D("100"))
    row, applied = rt.settle_spend(rid, D("1.50"))
    assert applied and row.settled_usd == D("1.50")
    assert rt.add_spend(AGENT, DAY, D("1.00")) == (D("2.50"), D("2.50"))
    rt.reserve_spend(new_id("res"), AGENT, DAY, D("1.00"), day_cap=D("100"), month_cap=D("100"))
    assert rt.expire_spend_reservations(0) == 1
    assert pu.purge_spend_reservations(datetime(2999, 1, 1, tzinfo=UTC)) == 1
