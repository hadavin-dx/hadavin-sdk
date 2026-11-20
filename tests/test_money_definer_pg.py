"""The five SECURITY DEFINER money functions of 0011, tested by a different agent than the builders (ticket
F-money-definer, step 5, test writer C). Real PostgreSQL 16, a throwaway schema and logins with unique names, dropped
after. Needs HADAVIN_TEST_PG_DSN.

THE RUNTIME LOGIN HERE IS WHAT `migrate` MAKES (step 4 shipped): SELECT on `spend` and `spend_month`, nothing on
`spend_reservations`, nothing else on the money tables, EXECUTE on the four runtime functions. The world no longer
strips any right by hand: the tests prove what migrate produces.

The attacks H1, H2 (insert), H2 (inflate) of tickets/migrations-0009-0010-review-1.md, and the shared-owner login of
L2, are run against that login below (`test_attack_*`, `test_L2_*`) and are REFUSED. They REPLACE the four
`xfail(strict)` pins in `tests/test_migrations_0009_0010_round2.py` at step 4 (that file is not touched here: the
pins flip to XPASS(strict) = failure the day the grants change, and are then deleted there).

The checks that the mutant harness (`tests/test_money_definer_mutants.py`) re-uses are the plain functions of
`BATTERY` (`check_*(w)`): each takes a world, resets the money state, and raises when the property is broken. Each
runs here once as a test against the real SQL, and there against every mutant.

Reference semantics: `MemoryStore` (the in-repo Python store, the contract suite's other kind) is run through the same
random sequences as the functions and must agree on every outcome and every counter (`test_parity_*`).
Known, documented differences (builder A's report): the Python exponent window of a cap is a property of the Decimal
form, not of the value, and is not applied in SQL (`max_exponent` is seeded and not read)."""

from __future__ import annotations

import os
import random
import threading
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg
from psycopg import sql

from hadavin_sdk.store import migrate as mig
from hadavin_sdk.store.memory import MemoryStore
from hadavin_sdk.store.protocol import NotFound, SpendCapExceeded, StaleState
from tests.test_stop_state_roles import World

D = Decimal
pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)

MONEY_TABLES = ("spend", "spend_month", "spend_reservations")
RESERVE, SETTLE, EXPIRE, PURGE, ADD = mig.MONEY_FUNCTIONS[:5]  # the five booking functions
NAMES = {
    "reserve": "hadavin_reserve_spend",
    "settle": "hadavin_settle_spend",
    "expire": "hadavin_expire_spend_reservations",
    "purge": "hadavin_purge_spend_reservations",
    "add": "hadavin_add_spend",
}
TYPES = {
    "reserve": ("text", "text", "date", "numeric", "numeric", "numeric", "text"),
    "settle": ("text", "numeric", "text"),
    "expire": ("integer",),
    "purge": ("timestamptz",),
    "add": ("text", "date", "numeric"),
}
RUNTIME_FUNCS = ("reserve", "settle", "expire", "add")
DAY = date(2026, 11, 10)
DAY2 = date(2026, 11, 11)
BIG = D(10**12)
LIMITS = {"max_amount": 10**9, "max_decimals": 12, "max_id_chars": 200, "max_expiry_age": 10**7}


# --- the world: the final design's grants -----------------------------------------------------------------------


def build_world() -> World:
    """A migrated scratch schema, the runtime login as the final design has it (see the module docstring)."""
    w = World()
    with psycopg.connect(w.dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(w.schema)))
        for r in w.roles:
            db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(r)))
    w.release = w.new_role("rl")
    return w


def teardown_world(w: World) -> None:
    for s in w.stores:
        s._db.close()
    with psycopg.connect(w.dsn, autocommit=True) as db:
        for schema in w.schemas:
            db.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema)))
        for r in w.roles:
            db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(r)))
            db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(r)))


@pytest.fixture(scope="module", name="w")
def world():
    w = build_world()
    try:
        w.migrate(release_role=w.release)
        yield w
    finally:
        teardown_world(w)


def reset(w: World) -> None:
    """Empty money state and the limits as the constants give them (a check may have changed them)."""
    with w.admin() as db:
        db.execute("TRUNCATE spend, spend_month, spend_reservations, runs CASCADE")
        db.execute("DELETE FROM hadavin_limits")
        for name, value in mig.money_limits().items():
            db.execute("INSERT INTO hadavin_limits VALUES (%s, %s)", (name, value))


@pytest.fixture(autouse=True)
def _clean(request):
    if "w" in request.fixturenames:
        reset(request.getfixturevalue("w"))
    yield


# --- calling the functions as the runtime login ---------------------------------------------------------------------


def rt_conn(w: World, role: str | None = None):
    return w.as_(role or w.runtime)


def _call_sql(w: World, key: str) -> sql.Composed:
    casts = [sql.SQL("%s::" + t) for t in TYPES[key]]
    return sql.SQL("SELECT * FROM {}.{}({})").format(
        sql.Identifier(w.schema), sql.Identifier(NAMES[key]), sql.SQL(", ").join(casts)
    )


def call(w: World, key: str, *args, db=None):
    """Rows of one call (a void function gives one empty row). Raises the psycopg error."""
    own = db is None
    db = db or rt_conn(w)
    try:
        return db.execute(_call_sql(w, key), args).fetchall()
    finally:
        if own:
            db.close()


def refused(w: World, key: str, *args, db=None):
    """(sqlstate, message) of the error of one call; fails when the call went through."""
    try:
        call(w, key, *args, db=db)
    except psycopg.Error as exc:
        return exc.sqlstate, str(exc.diag.message_primary)
    raise AssertionError(f"{key}{args!r} was not refused")


def reserve(w, rid, agent="ag", day=DAY, usd="1", day_cap=BIG, month_cap=BIG, run_id=None, db=None):
    return call(w, "reserve", rid, agent, day, D(usd), D(day_cap), D(month_cap), run_id, db=db)


def settle(w, rid, actual, agent="ag", db=None):
    rows = call(w, "settle", rid, D(actual), agent, db=db)
    return rows[0] if rows else None


def counters(w, agent="ag", day=DAY):
    d = w.run("SELECT usd FROM spend WHERE agent_id = %s AND day = %s", (agent, day))
    m = w.run(
        "SELECT usd FROM spend_month WHERE agent_id = %s AND month = date_trunc('month', %s::date)",
        (agent, day),
    )
    return (d[0][0] if d else None), (m[0][0] if m else None)


def row_counts(w):
    return tuple(w.count(t) for t in MONEY_TABLES)


def snapshot(w):
    return (
        w.run("SELECT * FROM spend ORDER BY 1, 2"),
        w.run("SELECT * FROM spend_month ORDER BY 1, 2"),
        w.run("SELECT reservation_id, status, settled_usd FROM spend_reservations ORDER BY 1"),
    )


# --- the checks (each one also runs against every mutant) ---------------------------------------------------------


def check_execute_map(w):
    """EXECUTE: the runtime holds the four runtime functions, not the purge; PUBLIC, portal, reset, release hold none
    of the five; a fresh login of no role gets 'permission denied'."""
    for key, sig in zip(NAMES, mig.MONEY_FUNCTIONS[:5], strict=True):
        runtime = key in RUNTIME_FUNCS
        want = {
            w.runtime: runtime,
            w.purge: key == "purge",
            w.portal: False,
            w.reset: False,
            w.release: False,
            "public": False,
        }
        for role, expected in want.items():
            got = w.run("SELECT has_function_privilege(%s, %s, 'EXECUTE')", (role, sig))[0][0]
            assert got is expected, (key, role)
    nobody = w.new_role("nobody")
    with rt_conn(w, nobody) as db:
        for key in NAMES:
            assert refused(w, key, *_ok_args(key), db=db)[0] == "42501", key
    assert refused(w, "purge", datetime.now(UTC))[0] == "42501"


def _ok_args(key):
    return {
        "reserve": ("a1", "ag", DAY, D(1), BIG, BIG, None),
        "settle": ("a1", D(1), "ag"),
        "expire": (0,),
        "purge": (datetime.now(UTC),),
        "add": ("ag", DAY, D(1)),
    }[key]


def check_no_table_rights(w):
    """The runtime login writes no money table, whatever the statement; it reads no reservation and no limit."""
    seed(w)
    before = snapshot(w)
    attacks = [
        (
            "INSERT INTO spend_reservations (reservation_id, agent_id, day, reserved_usd, settled_usd, "
            "status, closed_at) VALUES ('forged', 'ag', '2026-11-10', 90, 0, 'settled', now())"
        ),
        "INSERT INTO spend_reservations (reservation_id, agent_id, day, reserved_usd) VALUES ('x', 'ag', '2026-11-10', 1)",
        "INSERT INTO spend (agent_id, day, usd) VALUES ('z', '2026-11-10', 0)",
        "INSERT INTO spend_month (agent_id, month, usd) VALUES ('z', '2026-11-01', 0)",
        "UPDATE spend SET usd = 0",
        "UPDATE spend SET usd = usd - 10 WHERE agent_id = 'ag'",
        "UPDATE spend_month SET usd = 0",
        "UPDATE spend_reservations SET status = 'settled', settled_usd = 0 WHERE reservation_id = 'h1'",
        "UPDATE spend_reservations SET reserved_usd = 1000 WHERE reservation_id = 'h1'",
        "DELETE FROM spend_reservations",
        "DELETE FROM spend",
        "DELETE FROM spend_month",
        "TRUNCATE spend",
        "TRUNCATE spend_month, spend_reservations",
        "ALTER TABLE spend DISABLE TRIGGER ALL",
        "ALTER TABLE spend_reservations DISABLE TRIGGER USER",
        "CREATE TRIGGER t BEFORE UPDATE ON spend FOR EACH ROW EXECUTE FUNCTION hadavin_money_guard()",
        "CREATE RULE r AS ON UPDATE TO spend DO INSTEAD NOTHING",
        "COPY spend FROM STDIN",
        "SELECT * FROM spend_reservations",
        "SELECT * FROM hadavin_limits",
        "UPDATE hadavin_limits SET value = 1e30",
        "INSERT INTO hadavin_limits VALUES ('max_amount', 1e30)",
        "SET session_replication_role = replica",
        "SET ROLE postgres",
        "SET SESSION AUTHORIZATION postgres",
    ]
    with rt_conn(w) as db:
        for stmt in attacks:
            with pytest.raises(psycopg.Error) as exc:
                if stmt.startswith("COPY"):
                    with db.cursor() as cur, cur.copy(stmt) as cp:
                        cp.write(b"z\t2026-11-10\t0\n")
                else:
                    db.execute(stmt)
            assert exc.value.sqlstate in ("42501", "42704", "0LP01", "22023"), (stmt, exc.value)
    assert snapshot(w) == before, "a refused attack changed a money table"
    for t in MONEY_TABLES:
        for p in ("INSERT", "UPDATE", "DELETE", "TRUNCATE", "TRIGGER"):
            assert w.run("SELECT has_table_privilege(%s, %s, %s)", (w.runtime, t, p)) == [(False,)]
        for p in ("INSERT", "UPDATE", "REFERENCES"):
            assert w.run("SELECT has_any_column_privilege(%s, %s, %s)", (w.runtime, t, p)) == [
                (False,)
            ]
    assert w.run(
        "SELECT has_table_privilege(%s, 'spend_reservations', 'SELECT')", (w.runtime,)
    ) == [(False,)]
    assert w.run(
        "SELECT has_any_column_privilege(%s, 'hadavin_limits', 'SELECT')", (w.runtime,)
    ) == [(False,)]
    # nor can it make a function of its own that writes (the schema is not its)
    with rt_conn(w) as db, pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute(f"CREATE FUNCTION {w.schema}.hadavin_x() RETURNS int LANGUAGE sql AS 'SELECT 1'")


def seed(w):
    """Counter 100 for ag on DAY: a plain charge of 90 and an open hold h1 of 10 (made through the functions)."""
    call(w, "add", "ag", DAY, D(90))
    reserve(w, "h1", usd="10")
    assert counters(w) == (100, 100)


def check_behaviour(w):
    """The ordinary path as the runtime login: book, refuse at cap, settle once, expire, purge, add."""
    reserve(w, "r1", usd="2.5", run_id="run-1", day_cap="10", month_cap="20")
    assert counters(w) == (D("2.5"), D("2.5"))
    assert w.run("SELECT status, reserved_usd, run_id FROM spend_reservations") == [
        ("open", D("2.5"), "run-1")
    ]
    assert refused(w, "reserve", "r2", "ag", DAY, D(8), D(10), D(20), None) == ("HD001", "day")
    assert counters(w) == (D("2.5"), D("2.5"))  # nothing left behind
    assert w.count("spend_reservations") == 1
    row = settle(w, "r1", "1")
    assert (row[0], row[5], row[6], row[9]) == ("r1", D(1), "settled", True)
    assert counters(w) == (D(1), D(1))
    again = settle(w, "r1", "9")
    assert (again[5], again[9]) == (D(1), False) and counters(w) == (D(1), D(1))
    assert call(w, "add", "ag", DAY, D(4)) == [(D(5), D(5))]
    assert call(w, "expire", 0) == [(0,)]
    reserve(w, "r3", usd="1")
    assert call(w, "expire", 0) == [(1,)] and counters(w) == (D(6), D(6))
    assert call(w, "expire", 0) == [(0,)]


def check_hostile_arguments(w):
    """Every bad argument is 22023, the message names the parameter and never the value, nothing changes."""
    rows = [
        (
            "reserve",
            ("r", "ag", DAY, D(1), BIG, BIG, None),
            "p_id",
            [
                (0, None),
                (0, ""),
                (0, "a" * 201),
                (0, "a b"),
                (0, "a\nb"),
                (0, "x'); DROP TABLE spend; --"),
                (0, "' OR '1'='1"),
                (0, "%s %I"),
                (0, "é"),
                (0, "a/b"),
            ],
        ),
        (
            "reserve",
            ("r", "ag", DAY, D(1), BIG, BIG, None),
            "p_agent",
            [
                (1, None),
                (1, ""),
                (1, "a" * 201),
                (1, "a\nb"),
                (1, "a\x01b"),
                (1, "a\x7fb"),
                (1, "a\x85b"),
            ],
        ),
        (
            "reserve",
            ("r", "ag", DAY, D(1), BIG, BIG, None),
            "p_day",
            [(2, None), (2, "infinity"), (2, "-infinity")],
        ),
        (
            "reserve",
            ("r", "ag", DAY, D(1), BIG, BIG, None),
            "p_usd",
            [
                (3, None),
                (3, D(-1)),
                (3, D("NaN")),
                (3, D("Infinity")),
                (3, D("-Infinity")),
                (3, D("0.0000000000001")),
                (3, D(10**9)),
                (3, D("1e30")),
                (3, D("-0.000000000001")),
            ],
        ),
        (
            "reserve",
            ("r", "ag", DAY, D(1), BIG, BIG, None),
            "p_day_cap",
            [(4, None), (4, D(-1)), (4, D("NaN")), (4, D("Infinity")), (4, D("0.0000000000001"))],
        ),
        (
            "reserve",
            ("r", "ag", DAY, D(1), BIG, BIG, None),
            "p_month_cap",
            [(5, None), (5, D(-1)), (5, D("NaN")), (5, D("Infinity")), (5, D("0.0000000000001"))],
        ),
        (
            "reserve",
            ("r", "ag", DAY, D(1), BIG, BIG, None),
            "p_run_id",
            [(6, ""), (6, "a" * 201), (6, "a\nb"), (6, "a\x01")],
        ),
        (
            "settle",
            ("r", D(1), "ag"),
            "p_id",
            [(0, None), (0, ""), (0, "a" * 201), (0, "a\nb"), (0, "x'); DROP TABLE spend; --")],
        ),
        (
            "settle",
            ("r", D(1), "ag"),
            "p_actual",
            [
                (1, None),
                (1, D(-1)),
                (1, D("NaN")),
                (1, D("Infinity")),
                (1, D("0.0000000000001")),
                (1, D(10**9)),
            ],
        ),
        ("settle", ("r", D(1), "ag"), "p_agent", [(2, ""), (2, "a" * 201), (2, "a\nb")]),
        ("expire", (0,), "p_age_s", [(0, None), (0, -1), (0, 10**7 + 1), (0, 2**31 - 1)]),
        (
            "purge",
            (datetime.now(UTC),),
            "p_before",
            [(0, None), (0, "infinity"), (0, "-infinity")],
        ),
        (
            "add",
            ("ag", DAY, D(1)),
            "p_agent",
            [(0, None), (0, ""), (0, "a" * 201), (0, "a\nb"), (0, "a\x7f")],
        ),
        ("add", ("ag", DAY, D(1)), "p_day", [(1, None), (1, "infinity"), (1, "-infinity")]),
        (
            "add",
            ("ag", DAY, D(1)),
            "p_usd",
            [
                (2, None),
                (2, D(-1)),
                (2, D("NaN")),
                (2, D("Infinity")),
                (2, D("0.0000000000001")),
                (2, D(10**9)),
                (2, D("1e30")),
            ],
        ),
    ]
    seed(w)
    before = snapshot(w)
    with rt_conn(w) as db, rt_conn(w, w.purge) as pdb:
        for key, base, param, variants in rows:
            for index, value in variants:
                args = list(base)
                args[index] = value
                state, message = refused(w, key, *args, db=pdb if key == "purge" else db)
                assert state == "22023", (key, param, value, state, message)
                assert param in message, (key, param, value, message)
                if isinstance(value, str) and len(value) > 3:
                    assert value not in message, "the message must not echo the value"
    assert snapshot(w) == before, "a refused call changed a money table"
    assert w.run("SELECT to_regclass('spend') IS NOT NULL") == [(True,)]


def check_injection_agent_ids_are_stored_verbatim(w):
    """SQL-injection and format-specifier text is a legal AGENT id (no control character): stored verbatim, nothing
    is executed. As a reservation id the same text is refused (the Python id rule, `check_reservation_id`)."""
    hostile = [
        "x'); DROP TABLE spend; --",
        "' OR '1'='1",
        "%s %I %L %1$s",
        "\\'; --",
        '"quoted"',
        "é" * 100,
        "a" * 200,
    ]
    for i, agent in enumerate(hostile):
        reserve(w, f"inj{i}", agent=agent, usd="1")
        call(w, "add", agent, DAY, D(1))
        row = settle(w, f"inj{i}", "0.5", agent=agent)
        assert row[1] == agent and row[6] == "settled"
        assert counters(w, agent) == (D("1.5"), D("1.5")), agent
        stored = w.run(
            "SELECT agent_id FROM spend_reservations WHERE reservation_id = %s", (f"inj{i}",)
        )
        assert stored == [(agent,)]
    assert w.count("spend") == len(hostile)
    assert w.run("SELECT to_regclass('spend') IS NOT NULL") == [(True,)]
    for bad in ("x'); DROP TABLE spend; --", "' OR '1'='1", "%s %I"):
        assert refused(w, "reserve", bad, "ag", DAY, D(1), BIG, BIG, None)[0] == "22023"


def check_attack_h1_repeated_lowering(w):
    """H1: one allowed settle, then repeated lowering of the counter. The runtime has no UPDATE right: every
    statement is refused, the counter keeps the plain charge."""
    seed(w)
    lower = "UPDATE spend SET usd = usd - 10 WHERE agent_id = 'ag'"
    settle_sql = (
        "UPDATE spend_reservations SET status = 'settled', settled_usd = 0, closed_at = clock_timestamp() "
        "WHERE reservation_id = 'h1'"
    )
    with rt_conn(w) as db:
        for stmt in (settle_sql, lower, lower, lower):
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                db.execute(stmt)
    assert counters(w) == (100, 100)
    assert w.run("SELECT status FROM spend_reservations") == [("open",)]
    # the one thing it may do: settle the hold it can name, once, by at most the reserved amount
    assert settle(w, "h1", "0")[9] is True and counters(w) == (90, 90)
    with rt_conn(w) as db, pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute(lower)
    assert settle(w, "h1", "0")[9] is False and counters(w) == (90, 90)


def check_attack_h2_forged_settled_hold(w):
    """H2 (insert): a forged settled hold, then lowering the counter: refused by the missing INSERT/UPDATE."""
    seed(w)
    fake = (
        "INSERT INTO spend_reservations (reservation_id, agent_id, day, reserved_usd, settled_usd, status, "
        "closed_at) VALUES ('fake', 'ag', '2026-11-10', 90, 0, 'settled', now())"
    )
    with rt_conn(w) as db:
        for stmt in (fake, "UPDATE spend SET usd = 10 WHERE agent_id = 'ag'"):
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                db.execute(stmt)
    assert counters(w) == (100, 100) and w.count("spend_reservations") == 1


def check_attack_h2_inflate_reserved(w):
    """H2 (inflate): settle, inflate reserved_usd of the settled row, zero the counter: each step refused."""
    seed(w)
    with rt_conn(w) as db:
        for stmt in (
            "UPDATE spend_reservations SET reserved_usd = 1000 WHERE reservation_id = 'h1'",
            "UPDATE spend SET usd = 0 WHERE agent_id = 'ag'",
        ):
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                db.execute(stmt)
    settle(w, "h1", "0")
    with rt_conn(w) as db:
        for stmt in (
            "UPDATE spend_reservations SET reserved_usd = 1000 WHERE reservation_id = 'h1'",
            "UPDATE spend SET usd = 0 WHERE agent_id = 'ag'",
            "UPDATE spend_month SET usd = 0 WHERE agent_id = 'ag'",
        ):
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                db.execute(stmt)
    assert counters(w) == (90, 90)
    assert w.run("SELECT reserved_usd, settled_usd FROM spend_reservations") == [(D(10), D(0))]


TEMP_SHADOWS = {
    "spend": "agent_id text, day date, usd numeric",
    "spend_month": "agent_id text, month date, usd numeric",
    "spend_reservations": "reservation_id text, agent_id text, day date, run_id text, reserved_usd numeric, "
    "settled_usd numeric, status text, created_at timestamptz DEFAULT now(), closed_at timestamptz",
    "runs": "run_id text, cost_usd numeric",
    "hadavin_limits": "name text, value numeric",
}


def check_temp_shadow(w):
    """A caller's TEMP tables, functions and operator, and its own search_path, change nothing: the functions run
    pinned `pg_catalog, <schema>, pg_temp`. The temp tables stay empty, the real rows move."""
    with rt_conn(w) as db:
        for t, cols in TEMP_SHADOWS.items():
            db.execute(f"CREATE TEMP TABLE {t} ({cols})")
        # a hostile limit table: if it were read, an amount of 1e30 would pass
        db.execute(
            "INSERT INTO pg_temp.hadavin_limits VALUES ('max_amount', 1e40), ('max_decimals', 40), ('max_id_chars', 9999)"
        )
        for fn, args, ret in (
            ("scale", "numeric", "integer"),
            ("isfinite", "date", "boolean"),
            ("char_length", "text", "integer"),
            ("clock_timestamp", "", "timestamptz"),
            ("date_trunc", "text, date", "timestamptz"),
            ("greatest", "numeric, numeric", "numeric"),
        ):
            body = {
                "integer": "0",
                "boolean": "true",
                "timestamptz": "'2999-01-01'::timestamptz",
                "numeric": "0",
            }[ret]
            try:
                db.execute(
                    f"CREATE FUNCTION pg_temp.{fn}({args}) RETURNS {ret} LANGUAGE sql AS 'SELECT {body}'"
                )
            except psycopg.Error:
                pass
        for stmt in (
            "CREATE FUNCTION pg_temp.numeric_le(numeric, numeric) RETURNS boolean LANGUAGE sql AS 'SELECT true'",
            "CREATE OPERATOR pg_temp.<= (LEFTARG = numeric, RIGHTARG = numeric, FUNCTION = pg_temp.numeric_le)",
        ):
            try:
                db.execute(stmt)
            except psycopg.Error:
                pass
        db.execute("SET search_path = pg_temp, public")
        reserve(w, "t1", usd="3", day_cap="5", month_cap="5", db=db)
        assert refused(w, "reserve", "t2", "ag", DAY, D(3), D(5), D(5), None, db=db) == (
            "HD001",
            "day",
        )
        assert (
            refused(w, "reserve", "t3", "ag", DAY, D("1e30"), BIG, BIG, None, db=db)[0] == "22023"
        )
        assert (
            refused(w, "reserve", "a" * 150, "ag" * 101, DAY, D(1), BIG, BIG, None, db=db)[0]
            == "22023"
        )
        assert settle(w, "t1", "1", db=db)[9] is True
        call(w, "add", "ag", DAY, D(1), db=db)
        assert call(w, "expire", 0, db=db) == [(0,)]
        for t in (*MONEY_TABLES, "runs"):
            assert db.execute(
                sql.SQL("SELECT count(*) FROM pg_temp.{}").format(sql.Identifier(t))
            ).fetchone() == (0,), t
    assert counters(w) == (D(2), D(2))
    assert w.run("SELECT status FROM spend_reservations") == [("settled",)]


def check_limits_are_read_not_hardcoded(w):
    """The limits come from hadavin_limits, not from a literal: change a row (as the owner) and the function follows."""

    def put(name, value):
        w.run("UPDATE hadavin_limits SET value = %s WHERE name = %s RETURNING 1", (value, name))

    put("max_amount", 100)
    reserve(w, "l1", usd="99.5")
    assert refused(w, "reserve", "l2", "ag", DAY, D(100), BIG, BIG, None)[0] == "22023"
    assert refused(w, "add", "ag", DAY, D(100))[0] == "22023"
    assert refused(w, "settle", "l1", D(100), "ag")[0] == "22023"
    put("max_amount", 10**9)
    put("max_decimals", 2)
    assert refused(w, "add", "ag", DAY, D("0.001"))[0] == "22023"
    assert refused(w, "reserve", "l3", "ag", DAY, D(1), D("5.001"), BIG, None)[0] == "22023"
    assert call(w, "add", "ag", DAY, D("0.01"))
    put("max_decimals", 12)
    put("max_id_chars", 5)
    assert refused(w, "reserve", "abcdef", "ag", DAY, D(1), BIG, BIG, None)[0] == "22023"
    assert refused(w, "reserve", "abcde", "agentx", DAY, D(1), BIG, BIG, None)[0] == "22023"
    assert refused(w, "add", "agentx", DAY, D(1))[0] == "22023"
    assert refused(w, "settle", "abcdef", D(1), "ag")[0] == "22023"
    assert refused(w, "settle", "abcde", D(1), "agentx")[0] == "22023"
    put("max_id_chars", 200)
    put("max_expiry_age", 5)
    assert refused(w, "expire", 6)[0] == "22023"
    assert call(w, "expire", 5) == [(0,)]
    put("max_expiry_age", 10**7)
    assert call(w, "expire", 10**7) == [(0,)]


def check_owner(w):
    """One owner for the five functions, the money tables and the limits; the runtime is none of them nor a member."""
    owners = {
        o
        for (o,) in w.run(
            "SELECT pg_get_userbyid(p.proowner) FROM pg_proc p WHERE p.pronamespace = to_regnamespace(%s) "
            "AND p.proname LIKE 'hadavin\\_%%'",
            (w.schema,),
        )
    }
    tables = {
        o
        for (o,) in w.run(
            "SELECT pg_get_userbyid(relowner) FROM pg_class WHERE relnamespace = to_regnamespace(%s) "
            "AND relname = ANY(%s)",
            (w.schema, [*MONEY_TABLES, "runs", "hadavin_limits"]),
        )
    }
    assert len(owners) == 1 and owners == tables, (owners, tables)
    (owner,) = owners
    assert owner != w.runtime
    assert w.run("SELECT pg_has_role(%s, %s, 'MEMBER')", (w.runtime, owner)) == [(False,)]
    assert w.run(
        "SELECT rolsuper OR rolcreaterole FROM pg_roles WHERE rolname = %s", (w.runtime,)
    ) == [(False,)]


def check_definer_and_pins(w):
    """Every hadavin_* money function: SECURITY DEFINER, VOLATILE, not STRICT, pinned `pg_catalog, <schema>, pg_temp`."""
    rows = w.run(
        "SELECT p.oid::regprocedure::text, p.prosecdef, p.provolatile, p.proisstrict, p.proconfig "
        "FROM pg_proc p WHERE p.pronamespace = to_regnamespace(%s) AND p.proname = ANY(%s)",
        (w.schema, list(NAMES.values())),
    )
    assert len(rows) == 5
    for sig, secdef, vol, strict, config in rows:
        assert secdef is True, sig
        assert vol == "v", sig
        assert strict is False, sig
        assert config == [f"search_path=pg_catalog, {w.schema}, pg_temp"], (sig, config)


def check_release_function_not_callable(w):
    """The runtime login cannot run the release function of 0008 (only the release role)."""
    with rt_conn(w) as db, pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute(
            sql.SQL("SELECT {}.hadavin_release_expired_spend(%s, %s)").format(
                sql.Identifier(w.schema)
            ),
            ("ag", DAY),
        )


def check_settle_never_lowers_an_expired_hold(w):
    """M-j: after expiry the booked amount never goes down: settle of an expired hold below the reservation keeps it
    booked, above it raises the counter by the difference only."""
    reserve(w, "e1", usd="10")
    reserve(w, "e2", usd="10")
    assert call(w, "expire", 0) == [(2,)]
    assert counters(w) == (20, 20)
    row = settle(w, "e1", "3")
    assert (row[5], row[6], row[9]) == (D(10), "settled", True) and counters(w) == (20, 20)
    row = settle(w, "e2", "15")
    assert (row[5], row[9]) == (D(15), True) and counters(w) == (25, 25)


def check_cap_comparison(w):
    """Cap rule `booked < cap AND booked + amount <= cap`: an exact fill passes, one cent over refuses, and a counter
    AT its cap refuses even a zero amount (day first, then month); a zero cap refuses a zero amount."""
    reserve(w, "c1", usd="5", day_cap="5", month_cap="5")
    assert refused(w, "reserve", "c2", "ag", DAY, D("0.01"), D(5), D(5), None) == ("HD001", "day")
    # the day counter is at its cap: a zero amount is refused too (`<`, not `<=`)
    assert refused(w, "reserve", "c3", "ag", DAY, D(0), D(5), D(100), None) == ("HD001", "day")
    # another day of the month: the day is free, the MONTH counter is at its cap
    assert refused(w, "reserve", "c6", "ag", DAY2, D(0), D(100), D(5), None) == ("HD001", "month")
    assert refused(w, "reserve", "c4", "ag", DAY2, D(0), D(0), D(5), None) == ("HD001", "day")
    assert refused(w, "reserve", "c5", "ag", DAY2, D(1), D(5), D(5), None) == ("HD001", "month")
    assert counters(w) == (5, 5)
    assert counters(w, "ag", DAY2)[1] == 5
    assert w.count("spend_reservations") == 1


def check_concurrent_settle(w):
    """10 connections settle one hold at once, three rounds: exactly one claims it, the counter moves once."""
    call(w, "add", "ag", DAY, D(90))
    for rnd in range(3):
        rid = f"one{rnd}"
        reserve(w, rid, usd="10")
        n = 10
        start = threading.Barrier(n)
        claimed: list[bool] = []

        def worker(rid=rid, start=start, claimed=claimed):
            with rt_conn(w) as db:
                db.execute("SET statement_timeout = '60s'")
                start.wait()
                try:
                    claimed.append(settle(w, rid, "1", db=db)[9])
                except (
                    psycopg.Error
                ) as exc:  # a broken claim shows as a wrong count below, not a dead thread
                    claimed.append(exc.sqlstate)

        threads = [threading.Thread(target=worker) for _ in range(n)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert claimed.count(True) == 1 and claimed.count(False) == n - 1, claimed
        assert counters(w) == (D(91 + rnd), D(91 + rnd)), "the counter must move once per hold"


BATTERY = {
    name.removeprefix("check_"): fn
    for name, fn in sorted(globals().items())
    if name.startswith("check_")
}


def run_battery(w) -> dict[str, str]:
    """{check name: failure text} for every check that fails on this world (any exception is a failure)."""
    failed = {}
    for name, fn in BATTERY.items():
        reset(w)
        try:
            fn(w)
        except BaseException as exc:  # noqa: BLE001 - a mutant may break a check in any way
            failed[name] = f"{type(exc).__name__}: {str(exc)[:200]}"
    reset(w)
    return failed


@pytest.mark.parametrize("name", list(BATTERY))
def test_battery_check_passes_on_the_real_sql(w, name):
    BATTERY[name](w)


# --- specified behaviour, in detail --------------------------------------------------------------------------------


def test_reserve_books_day_and_month_across_days_of_one_month(w):
    reserve(w, "a", day=DAY, usd="1")
    reserve(w, "b", day=DAY2, usd="2")
    reserve(w, "c", day=date(2026, 12, 1), usd="4")
    assert counters(w, day=DAY) == (1, 3)
    assert counters(w, day=DAY2) == (2, 3)
    assert counters(w, day=date(2026, 12, 1)) == (4, 4)


def test_month_cap_refuses_and_rolls_the_day_back(w):
    reserve(w, "a", day=DAY, usd="6", day_cap="100", month_cap="10")
    assert refused(w, "reserve", "b", "ag", DAY2, D(6), D(100), D(10), None) == ("HD001", "month")
    assert counters(w, day=DAY2) == (None, 6)  # no day row seeded, month untouched
    assert w.count("spend_reservations") == 1


def test_duplicate_reservation_id_is_23505_and_books_nothing_twice(w):
    reserve(w, "dup", usd="1")
    assert refused(w, "reserve", "dup", "ag", DAY, D(1), BIG, BIG, None)[0] == "23505"
    assert refused(w, "reserve", "dup", "other", DAY, D(1), BIG, BIG, None)[0] == "23505"
    assert counters(w) == (1, 1) and w.count("spend_reservations") == 1


def test_a_cap_of_ten_to_the_twelfth_and_a_twelve_decimal_amount_work(w):
    reserve(w, "big", usd="0.000000000001", day_cap=10**12, month_cap=10**12)
    assert counters(w)[0] == D("0.000000000001")
    assert call(w, "add", "ag", DAY, D("999999999.999999999999"))


def test_settle_below_equal_above_and_the_run_cost(w):
    now = datetime.now(UTC)
    w.run(
        "INSERT INTO runs (run_id, schema_version, agent_id, principal_id, trigger_kind, trigger_ref, state, "
        "cost_usd, created_at, updated_at) VALUES ('run-1', 1, 'ag', 'p', 'user', 'r', 'WORKING', 1, %s, %s) RETURNING 1",
        (now, now),
    )
    reserve(w, "s1", usd="4", run_id="run-1")
    reserve(w, "s2", usd="4")
    reserve(w, "s3", usd="4")
    assert settle(w, "s1", "1.5")[5] == D("1.5") and counters(w) == (D("9.5"), D("9.5"))
    assert settle(w, "s2", "4")[5] == D(4) and counters(w) == (D("9.5"), D("9.5"))
    assert settle(w, "s3", "6")[5] == D(6) and counters(w) == (D("11.5"), D("11.5"))
    assert w.run("SELECT cost_usd FROM runs") == [(D("2.5"),)]  # 1 + the actual amount 1.5
    reserve(w, "s4", usd="1", run_id="no-such-run")  # a missing run row is ignored
    assert settle(w, "s4", "1")[9] is True


def test_settle_by_another_agent_and_by_an_unknown_id_is_the_same_hd002(w):
    reserve(w, "own", agent="ag", usd="1")
    foreign = refused(w, "settle", "own", D(1), "someone-else")
    unknown = refused(w, "settle", "nope", D(1), "ag")
    assert foreign == unknown == ("HD002", "reservation not found")
    assert counters(w) == (1, 1)
    assert w.run("SELECT status FROM spend_reservations") == [("open",)]


def test_settle_with_a_null_agent_settles_any_agents_hold_the_documented_residual(w):
    """HONEST RESIDUAL named in 0011's header: p_agent NULL means any agent. Do not 'fix' this silently."""
    reserve(w, "o1", agent="victim", usd="5")
    row = call(w, "settle", "o1", D(0), None)[0]
    assert (row[1], row[9]) == ("victim", True) and counters(w, "victim") == (0, 0)


def test_the_runtime_can_lower_only_by_settling_a_named_open_hold_once(w):
    reserve(w, "h", usd="10")
    call(w, "add", "ag", DAY, D(90))
    settle(w, "h", "0")
    assert counters(w) == (90, 90)
    for _ in range(3):
        assert settle(w, "h", "0")[9] is False
    assert counters(w) == (90, 90)
    assert refused(w, "settle", "unknown-guess", D(0), None)[0] == "HD002"


def test_missing_counter_row_is_hd003_and_the_claim_rolls_back(w):
    reserve(w, "m1", usd="2")
    w.run("DELETE FROM spend RETURNING 1")
    assert refused(w, "settle", "m1", D(1), "ag")[0] == "HD003"
    assert w.run("SELECT status FROM spend_reservations") == [("open",)]
    w.run("INSERT INTO spend VALUES ('ag', %s, 2) RETURNING 1", (DAY,))
    w.run("DELETE FROM spend_month RETURNING 1")
    assert refused(w, "settle", "m1", D(1), "ag")[0] == "HD003"
    assert w.run("SELECT status FROM spend_reservations") == [("open",)]
    assert w.run("SELECT usd FROM spend") == [(D(2),)]  # the day counter rolled back too


@pytest.mark.parametrize(
    ("limit", "key", "args"),
    [
        ("max_amount", "reserve", ("r", "ag", DAY, D(1), BIG, BIG, None)),
        ("max_decimals", "reserve", ("r", "ag", DAY, D(1), BIG, BIG, None)),
        ("max_id_chars", "reserve", ("r", "ag", DAY, D(1), BIG, BIG, None)),
        ("max_amount", "settle", ("r", D(1), "ag")),
        ("max_decimals", "settle", ("r", D(1), "ag")),
        ("max_id_chars", "settle", ("r", D(1), "ag")),
        ("max_amount", "add", ("ag", DAY, D(1))),
        ("max_decimals", "add", ("ag", DAY, D(1))),
        ("max_id_chars", "add", ("ag", DAY, D(1))),
        ("max_expiry_age", "expire", (0,)),
    ],
)
def test_a_missing_limit_row_fails_closed_with_hd004(w, limit, key, args):
    w.run("DELETE FROM hadavin_limits WHERE name = %s RETURNING 1", (limit,))
    assert refused(w, key, *args)[0] == "HD004"
    assert row_counts(w) == (0, 0, 0)


def test_the_unread_max_exponent_row_is_not_needed(w):
    w.run("DELETE FROM hadavin_limits WHERE name = 'max_exponent' RETURNING 1")
    reserve(w, "x", usd="1")


def test_expire_leaves_counters_and_young_holds_alone(w):
    reserve(w, "y", usd="3")
    assert call(w, "expire", 3600) == [(0,)]
    assert call(w, "expire", 10**7) == [(0,)]
    assert w.run("SELECT status FROM spend_reservations") == [("open",)]
    w.run("UPDATE spend_reservations SET created_at = created_at - interval '2 hours' RETURNING 1")
    assert call(w, "expire", 3600) == [(1,)]
    assert counters(w) == (3, 3)
    assert w.run("SELECT status, settled_usd FROM spend_reservations") == [("expired", D(3))]


def test_purge_deletes_settled_only_and_keeps_expired_and_open(w):
    for rid in ("p1", "p2", "p3", "p4"):
        reserve(w, rid, usd="1")
    settle(w, "p1", "1")
    settle(w, "p2", "0")
    call(w, "expire", 0)  # p3 and p4 expire
    reserve(w, "p5", usd="1")
    future = datetime.now(UTC) + timedelta(days=1)
    with w.as_(w.purge) as db:
        assert call(w, "purge", datetime.now(UTC) - timedelta(days=1), db=db) == [(0,)]
        assert call(w, "purge", future, db=db) == [(2,)]
    assert sorted(r[0] for r in w.run("SELECT reservation_id FROM spend_reservations")) == [
        "p3",
        "p4",
        "p5",
    ]
    assert counters(w)[0] == 4  # purge never moves a counter


def test_add_spend_returns_both_totals_and_rolls_over_the_month(w):
    assert call(w, "add", "ag", DAY, D("1.5")) == [(D("1.5"), D("1.5"))]
    assert call(w, "add", "ag", DAY2, D("2")) == [(D(2), D("3.5"))]
    assert call(w, "add", "ag", date(2026, 12, 1), D(1)) == [(D(1), D(1))]
    assert call(w, "add", "ag", DAY, D(0)) == [(D("1.5"), D("3.5"))]


def test_a_runtime_login_that_calls_unqualified_under_a_hostile_path_finds_no_function(w):
    with rt_conn(w) as db:
        db.execute("SET search_path = pg_temp, public")
        with pytest.raises(psycopg.errors.UndefinedFunction):
            db.execute("SELECT hadavin_add_spend('ag', '2026-11-10', 1)")


# --- the three reproduced bypasses and L2 (replace the xfail pins of test_migrations_0009_0010_round2.py) -------------


def test_attack_H1_repeated_lowering_is_refused(w):
    check_attack_h1_repeated_lowering(w)


def test_attack_H2_forged_settled_hold_by_insert_is_refused(w):
    check_attack_h2_forged_settled_hold(w)


def test_attack_H2_inflating_reserved_usd_is_refused(w):
    check_attack_h2_inflate_reserved(w)


def test_L2_a_runtime_login_that_is_the_owner_a_member_of_it_or_a_superuser_is_refused_by_migrate(
    w,
):
    """L2: the owner passes the trigger by design, so migrate refuses to hand the runtime role to the owner."""
    owner = w.run("SELECT current_user")[0][0]
    from hadavin_sdk.errors import ConfigError

    with pytest.raises(ConfigError):
        w.migrate(release_role=w.release, runtime_role=owner)
    member = w.new_role("member")
    w.grant("GRANT {} TO {}", owner, member)
    with pytest.raises(ConfigError):
        w.migrate(release_role=w.release, runtime_role=member)
    w.grant("REVOKE {} FROM {}", owner, member)
    w.do(f"ALTER ROLE {member} SUPERUSER")
    try:
        with pytest.raises(ConfigError):
            w.migrate(release_role=w.release, runtime_role=member)
    finally:
        w.do(f"ALTER ROLE {member} NOSUPERUSER")
    assert w.run("SELECT has_table_privilege(%s, 'spend', 'UPDATE')", (member,)) == [(False,)]


# --- parity with the in-repo Python store --------------------------------------------------------------------------

SEEDS = (3, 7, 19, 42, 101, 211, 313, 777)
AGENTS = ("a1", "a2")
DAYS = (date(2026, 11, 3), date(2026, 11, 20), date(2026, 12, 2))
AMOUNTS = ("0", "0.5", "1", "2.25", "4", "7")
CAPS = ("0", "3", "6", "20", "1000")
IDS = tuple(f"id{i}" for i in range(7))


def _script(seed, n):
    rnd = random.Random(seed)  # noqa: S311 - a reproducible test script, not a secret
    ops = []
    for _ in range(n):
        kind = rnd.choices(["reserve", "settle", "add", "expire", "purge"], [10, 8, 3, 2, 1])[0]
        if kind == "reserve":
            ops.append(
                (
                    "reserve",
                    rnd.choice(IDS),
                    rnd.choice(AGENTS),
                    rnd.choice(DAYS),
                    D(rnd.choice(AMOUNTS)),
                    D(rnd.choice(CAPS)),
                    D(rnd.choice(CAPS)),
                )
            )
        elif kind == "settle":
            ops.append(
                ("settle", rnd.choice(IDS), D(rnd.choice(AMOUNTS)), rnd.choice((*AGENTS, None)))
            )
        elif kind == "add":
            ops.append(("add", rnd.choice(AGENTS), rnd.choice(DAYS), D(rnd.choice(AMOUNTS))))
        else:
            ops.append((kind,))
    return ops


def _outcome_memory(store, op):
    try:
        if op[0] == "reserve":
            _, rid, agent, day, usd, dc, mc = op
            store.reserve_spend(rid, agent, day, usd, day_cap=dc, month_cap=mc)
            return ("ok",)
        if op[0] == "settle":
            row, claimed = store.settle_spend(op[1], op[2], agent_id=op[3])
            return ("ok", row.settled_usd, row.status, claimed)
        if op[0] == "add":
            return ("ok", *store.add_spend(op[1], op[2], op[3]))
        if op[0] == "expire":
            return ("ok", store.expire_spend_reservations(0))
        return (
            "ok",
            store.purge_spend_reservations(datetime.now(UTC) + timedelta(days=1)),
        )
    except SpendCapExceeded as exc:
        return ("HD001", exc.which)
    except StaleState:
        return ("23505",)
    except NotFound:
        return ("HD002",)


def _outcome_pg(w, db, op):
    try:
        if op[0] == "reserve":
            call(w, "reserve", op[1], op[2], op[3], op[4], op[5], op[6], None, db=db)
            return ("ok",)
        if op[0] == "settle":
            r = call(w, "settle", op[1], op[2], op[3], db=db)[0]
            return ("ok", r[5], r[6], r[9])
        if op[0] == "add":
            return ("ok", *call(w, "add", op[1], op[2], op[3], db=db)[0])
        if op[0] == "expire":
            return ("ok", call(w, "expire", 0, db=db)[0][0])
        with w.as_(w.purge) as pdb:
            return (
                "ok",
                call(w, "purge", datetime.now(UTC) + timedelta(days=1), db=pdb)[0][0],
            )
    except psycopg.Error as exc:
        state = exc.sqlstate
        if state == "HD001":
            return ("HD001", str(exc.diag.message_primary))
        return (state,)


@pytest.mark.parametrize("seed", SEEDS)
def test_parity_random_sequences_with_the_memory_store(w, seed):
    mem = MemoryStore()
    with rt_conn(w) as db:
        for i, op in enumerate(_script(seed, 60)):
            expected = _outcome_memory(mem, op)
            got = _outcome_pg(w, db, op)
            assert got == expected, f"seed={seed} op#{i}={op}: pg {got} != memory {expected}"
            for agent in AGENTS:
                for day in DAYS:
                    pg_day, pg_month = counters(w, agent, day)
                    mem_day, mem_month = mem.spend_totals(agent, day)
                    assert (pg_day or D(0)) == mem_day, f"seed={seed} op#{i} day {agent} {day}"
                    assert (pg_month or D(0)) == mem_month, (
                        f"seed={seed} op#{i} month {agent} {day}"
                    )
    states = {
        r[0]: (r[1], r[2])
        for r in w.run("SELECT reservation_id, status, settled_usd FROM spend_reservations")
    }
    with mem._lock:
        want = {k: (v.status, v.settled_usd) for k, v in mem._reservations.items()}
    assert states == want


# --- concurrency -----------------------------------------------------------------------------------------------------


def test_fifty_one_connections_reserving_under_a_cap_give_exactly_cap_winners(w):
    cap, n = 20, 51
    start = threading.Barrier(n)
    results: list[object] = []

    def worker(i):
        with rt_conn(w) as db:
            db.execute("SET statement_timeout = '60s'")
            start.wait()
            try:
                reserve(w, f"c{i}", usd="1", day_cap=cap, month_cap=cap, db=db)
                results.append("won")
            except psycopg.Error as exc:
                results.append(exc.sqlstate)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert results.count("won") == cap and results.count("HD001") == n - cap, results
    assert counters(w) == (cap, cap) and w.count("spend_reservations") == cap
