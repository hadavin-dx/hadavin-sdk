"""F-money-definer step 4, the grant flip. After it the runtime login holds only SELECT on `spend` and `spend_month`
(`spend_totals` reads them) and nothing on `spend_reservations`; no login holds INSERT, UPDATE or DELETE on the three
tables; every booking is a SECURITY DEFINER function the runtime may EXECUTE; the purge login holds no table right and
only EXECUTE on the purge function; the portal and reset logins hold nothing. Real PostgreSQL 16, a throwaway schema
and real non-superuser logins. Needs HADAVIN_TEST_PG_DSN."""

from __future__ import annotations

import os
from datetime import date, timedelta
from decimal import Decimal

import psycopg
import pytest
from psycopg import errors, sql

from hadavin_sdk.models import new_id, now
from tests.test_stop_state_roles import World

D = Decimal
pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)
TABLES = ("spend", "spend_month", "spend_reservations")
WRITES = ("INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER")
STATEMENTS = {
    "INSERT": {
        "spend": "INSERT INTO spend (agent_id, day, usd) VALUES ('x', '2026-01-01', 1)",
        "spend_month": "INSERT INTO spend_month (agent_id, month, usd) VALUES ('x', '2026-01-01', 1)",
        "spend_reservations": (
            "INSERT INTO spend_reservations (reservation_id, agent_id, day, reserved_usd) "
            "VALUES ('r', 'x', '2026-01-01', 1)"
        ),
    },
    "UPDATE": {
        "spend": "UPDATE spend SET usd = 0",
        "spend_month": "UPDATE spend_month SET usd = 0",
        "spend_reservations": "UPDATE spend_reservations SET reserved_usd = 0",
    },
    "DELETE": {t: f"DELETE FROM {t}" for t in TABLES},  # noqa: S608 - fixed names
}


@pytest.fixture(name="w")
def step4_world():
    world = World()
    with psycopg.connect(world.dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(world.schema)))
        for r in world.roles:
            db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(r)))
    try:
        world.migrate()
        yield world
    finally:
        for s in world.stores:
            s._db.close()
        with psycopg.connect(world.dsn, autocommit=True) as db:
            for schema in world.schemas:
                db.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
            for r in world.roles:
                db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(r)))
                db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(r)))


def _has(w, role, table, priv):
    return w.run("SELECT has_table_privilege(%s, %s, %s)", (role, table, priv))[0][0]


def _counts(w):
    return [w.run(f"SELECT count(*) FROM {t}")[0][0] for t in TABLES]  # noqa: S608 - fixed names


@pytest.mark.parametrize("verb", ["INSERT", "UPDATE", "DELETE"])
@pytest.mark.parametrize("table", TABLES)
def test_the_runtime_login_cannot_write_a_money_table(w, verb, table):
    with w.as_(w.runtime) as db, pytest.raises(errors.InsufficientPrivilege):
        db.execute(STATEMENTS[verb][table])
    assert _counts(w) == [0, 0, 0]


def test_the_runtime_login_cannot_read_the_reservations(w):
    with w.as_(w.runtime) as db, pytest.raises(errors.InsufficientPrivilege):
        db.execute("SELECT count(*) FROM spend_reservations")
    with w.as_(w.runtime) as db:
        db.execute("SELECT usd FROM spend")  # the two counters stay readable (spend_totals)
        db.execute("SELECT usd FROM spend_month")


@pytest.mark.parametrize("table", TABLES)
def test_no_role_holds_a_write_right_and_only_the_runtime_reads_the_counters(w, table):
    for role in (w.runtime, w.portal, w.purge, w.reset, "public"):
        for priv in WRITES:
            assert not _has(w, role, table, priv), (role, table, priv)
        columns = w.run(
            "SELECT count(*) FROM pg_attribute WHERE attrelid = %s::regclass AND attnum > 0 "
            "AND has_column_privilege(%s, attrelid, attnum, 'SELECT,INSERT,UPDATE')",
            (table, role),
        )[0][0]
        reads = role == w.runtime and table != "spend_reservations"
        assert _has(w, role, table, "SELECT") is reads, (role, table)
        assert (columns > 0) is reads, (role, table, columns)


def test_a_full_reserve_settle_expire_cycle_with_execute_only(w):
    store = w.store(w.runtime)
    day = now().date()
    rid, rid2 = new_id("res"), new_id("res")
    store.reserve_spend(rid, "agent-a", day, D("1.5"), day_cap=D("10"), month_cap=D("100"))
    store.reserve_spend(rid2, "agent-a", day, D("2"), day_cap=D("10"), month_cap=D("100"))
    assert store.spend_totals("agent-a", day) == (D("3.5"), D("3.5"))
    row, claimed = store.settle_spend(rid, D("1"), agent_id="agent-a")
    assert claimed and row.status == "settled"
    assert store.spend_totals("agent-a", day) == (D("3"), D("3"))
    store.add_spend("agent-a", day, D("0.25"))
    assert store.spend_totals("agent-a", day) == (D("3.25"), D("3.25"))
    with w.admin() as db:
        db.execute(
            "UPDATE spend_reservations SET created_at = %s WHERE reservation_id = %s",
            (now() - timedelta(hours=5), rid2),
        )
    assert store.expire_spend_reservations(3600) == 1
    assert w.run("SELECT status FROM spend_reservations WHERE reservation_id = %s", (rid2,)) == [
        ("expired",)
    ]
    # and the runtime, holding no table right, still cannot do it by hand
    with w.as_(w.runtime) as db, pytest.raises(errors.InsufficientPrivilege):
        db.execute("UPDATE spend SET usd = 0")


def test_the_purge_login_cannot_delete_directly_but_the_purge_function_works(w):
    store = w.store(w.runtime)
    day = now().date()
    rid = new_id("res")
    store.reserve_spend(rid, "agent-a", day, D("1"), day_cap=D("10"), month_cap=D("100"))
    store.settle_spend(rid, D("1"), agent_id="agent-a")
    with w.as_(w.purge) as db:
        for stmt in (
            "DELETE FROM spend_reservations",
            "SELECT status, closed_at FROM spend_reservations",
            "DELETE FROM spend",
            "UPDATE spend_month SET usd = 0",
        ):
            with pytest.raises(errors.InsufficientPrivilege):
                db.execute(stmt)
    assert _counts(w)[2] == 1
    purger = w.store(w.purge)
    assert purger.purge_spend_reservations(now() + timedelta(hours=1)) == 1
    assert _counts(w)[2] == 0


@pytest.mark.parametrize("who", ["portal", "reset"])
@pytest.mark.parametrize("table", TABLES)
def test_the_portal_and_reset_logins_have_nothing_on_the_money_tables(w, who, table):
    role = getattr(w, who)
    with w.as_(role) as db:
        for stmt in (
            f"SELECT * FROM {table}",  # noqa: S608 - fixed names
            STATEMENTS["INSERT"][table],
            STATEMENTS["UPDATE"][table],
            STATEMENTS["DELETE"][table],
        ):
            with pytest.raises(errors.InsufficientPrivilege):
                db.execute(stmt)


def test_the_release_login_still_holds_nothing_on_the_money_tables_and_its_function(w):
    release = w.new_role("rl")
    w.migrate(release_role=release)
    for table in TABLES:
        for priv in ("SELECT", *WRITES):
            assert not _has(w, release, table, priv), (table, priv)
    day = date(2026, 1, 1)
    with w.as_(release) as db:
        db.execute("SELECT * FROM hadavin_release_expired_spend(%s, %s)", ("agent-a", day))


def test_a_hand_grant_of_a_write_right_is_repaired_by_the_next_migrate(w):
    for table in TABLES:
        w.grant(f"GRANT UPDATE, INSERT, SELECT ON {table} TO {{}}", w.runtime)
    w.grant("GRANT DELETE ON spend_reservations TO {}", w.purge)
    w.migrate()
    for table in TABLES:
        assert not _has(w, w.runtime, table, "UPDATE"), table
        assert not _has(w, w.runtime, table, "INSERT"), table
    assert not _has(w, w.runtime, "spend_reservations", "SELECT")
    assert not _has(w, w.purge, "spend_reservations", "DELETE")


# --- what `migrate --runtime-role` alone produces (no hand-stripping anywhere) -----------------------------------------


def _fresh(w, **roles):
    """A second schema migrated with only the named roles."""
    scoped = w.new_schema("fr")  # creates the schema and records it for the fixture's DROP
    schema = w.schemas[-1]
    from hadavin_sdk.store.migrate import migrate

    migrate(scoped, **roles)
    return schema, scoped


def test_migrate_with_only_the_runtime_role_gives_it_select_on_the_counters_and_no_write(w):
    from hadavin_sdk.store import migrate as mig

    _schema, scoped = _fresh(w, runtime_role=w.runtime)
    with psycopg.connect(scoped, autocommit=True) as db:
        for table in TABLES:
            for priv in ("INSERT", "UPDATE", "DELETE"):
                q = "SELECT has_table_privilege(%s, %s, %s)"
                assert db.execute(q, (w.runtime, table, priv)).fetchone()[0] is False, (table, priv)
        for table in ("spend", "spend_month"):
            assert db.execute(q, (w.runtime, table, "SELECT")).fetchone()[0] is True
        assert db.execute(q, (w.runtime, "spend_reservations", "SELECT")).fetchone()[0] is False
    assert mig.GRANTS["spend_reservations"].purge == ""
    assert mig.GRANTS["spend_reservations"].runtime == ""
    assert mig.GRANTS["spend"].runtime == "SELECT" == mig.GRANTS["spend_month"].runtime


@pytest.mark.parametrize("table", TABLES)
@pytest.mark.parametrize("priv", ["INSERT", "UPDATE", "DELETE", "TRUNCATE"])
def test_migrate_refuses_an_unnamed_role_that_can_write_a_money_table(w, table, priv):
    from hadavin_sdk.errors import ConfigError

    stranger = w.new_role("st", "NOLOGIN")
    w.grant("GRANT USAGE ON SCHEMA {} TO {}", w.schema, stranger)
    w.grant(f"GRANT {priv} ON {table} TO {{}}", stranger)
    with pytest.raises(ConfigError, match=rf"{stranger} can {priv} {table}"):
        w.migrate()


def test_migrate_refuses_public_write_and_a_membership_that_carries_it(w):
    from hadavin_sdk.errors import ConfigError

    w.do("GRANT UPDATE ON spend TO PUBLIC")
    with pytest.raises(ConfigError, match="PUBLIC can write spend|can UPDATE spend"):
        w.migrate()
    w.do("REVOKE UPDATE ON spend FROM PUBLIC")
    heir = w.new_role("hr", "NOLOGIN")
    carrier = w.new_role("cr", "NOLOGIN")
    w.grant("GRANT DELETE ON spend_month TO {}", carrier)
    w.grant("GRANT {} TO {}", carrier, heir)
    with pytest.raises(ConfigError, match=f"{heir} can DELETE spend_month"):
        w.migrate()
    w.grant("REVOKE {} FROM {}", carrier, heir)
    w.grant("REVOKE DELETE ON spend_month FROM {}", carrier)
    assert w.migrate() == []


# --- mutants: each weakens one part of the change and must be seen ---------------------------------------------------


def _grant_mutant(table, **fields):
    from dataclasses import replace

    from hadavin_sdk.store import migrate as mig

    def apply(m):
        m.setitem(mig.GRANTS, table, replace(mig.GRANTS[table], **fields))

    return apply


def _writer_check_off(m):
    from hadavin_sdk.store import migrate as mig

    m.setattr(mig, "_money_table_writers", lambda db: [])


GRANT_MUTANTS = {
    "runtime_rw_on_reservations": _grant_mutant(
        "spend_reservations", runtime="SELECT, INSERT, UPDATE"
    ),
    "runtime_select_on_reservations": _grant_mutant("spend_reservations", runtime="SELECT"),
    "runtime_rw_on_spend": _grant_mutant("spend", runtime="SELECT, INSERT, UPDATE"),
    "runtime_update_on_spend_month": _grant_mutant("spend_month", runtime="SELECT, UPDATE"),
    "runtime_no_select_on_spend": _grant_mutant("spend", runtime=""),
    "purge_delete_on_reservations": _grant_mutant("spend_reservations", purge="DELETE"),
}


@pytest.mark.parametrize("name", ["control", *GRANT_MUTANTS])
def test_the_grant_mutants_are_seen(w, name):
    from hadavin_sdk.errors import ConfigError

    with pytest.MonkeyPatch.context() as m:
        if name != "control":
            GRANT_MUTANTS[name](m)
        try:
            _schema, scoped = _fresh(w, runtime_role=w.runtime, purge_role=w.purge)
        except ConfigError:
            # seen: the writer check refuses the weakened map before the grants stand (a mutant that leaves a
            # write right is refused by migrate itself; one that only drops a SELECT is caught by the list below)
            assert name != "control"
            return
        with psycopg.connect(scoped, autocommit=True) as db:
            q = "SELECT has_table_privilege(%s, %s, %s)"
            found = []
            for who, role in (("runtime", w.runtime), ("purge", w.purge)):
                for t in TABLES:
                    for p in ("SELECT", "INSERT", "UPDATE", "DELETE"):
                        held = db.execute(q, (role, t, p)).fetchone()[0]
                        want = who == "runtime" and p == "SELECT" and t != "spend_reservations"
                        if held != want:
                            found.append(f"{who} {p} {t} held={held}")
    assert (found == []) is (name == "control"), (name, found)


def test_the_writer_check_mutant_is_seen(w):
    from hadavin_sdk.errors import ConfigError

    stranger = w.new_role("st", "NOLOGIN")
    w.grant("GRANT USAGE ON SCHEMA {} TO {}", w.schema, stranger)
    w.grant("GRANT UPDATE ON spend TO {}", stranger)
    with pytest.raises(ConfigError, match="can UPDATE spend"):
        w.migrate()
    with pytest.MonkeyPatch.context() as m:
        _writer_check_off(m)
        w.migrate()  # the mutant lets the stranger through: the test above would fail on it
    assert _has(w, stranger, "spend", "UPDATE")
