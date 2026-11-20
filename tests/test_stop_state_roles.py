"""Step B, the stop state, against a real PostgreSQL through real non-superuser logins.

Written by a different agent than the builder, from the ticket (handover/core-b/tickets/B-stop-state.md), not
from the code. Every case gets a fresh schema and four LOGIN roles (runtime, portal, purge, reset) with random
names, `migrate(...)` with all four named, and drops only what it made. "Denied" means
`psycopg.errors.InsufficientPrivilege` exactly, and the relation is proven to exist first, so a missing relation
never counts as a denial. Needs HADAVIN_TEST_PG_DSN (CI: the postgres service); skipped without it."""

from __future__ import annotations

import inspect
import os
import threading
import time
import uuid

import pytest
import yaml

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg
from psycopg import errors, sql
from psycopg.conninfo import make_conninfo

from hadavin_sdk import cli
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.backends import platform_secrets
from hadavin_sdk.backends.factory import make
from hadavin_sdk.backends.table import ChainSettings, PostgresSettings
from hadavin_sdk.config import ConfigError
from hadavin_sdk.limits import Limits
from hadavin_sdk.models import KillSwitch, RunState
from hadavin_sdk.store import migrate as migrate_mod
from hadavin_sdk.store.migrate import GRANTS, migrate
from hadavin_sdk.store.protocol import Store

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)

DENIED = errors.InsufficientPrivilege
STOP_RELATIONS = ("kill_switch", "kill_switch_stops", "kill_switch_clears")
OFF = KillSwitch(on=False, by="admin:reset")
SETTINGS = {"kind": "postgres", "dsn_secret_name": "pg-dsn"}
RESET_REF = "reset-dsn"  # the NAME of a secret (config), never a value


class World:
    """One schema and four logins. Everything it creates is recorded and dropped by the fixture."""

    def __init__(self):
        sfx = uuid.uuid4().hex[:10]
        self.sfx = sfx
        self.dsn = os.environ["HADAVIN_TEST_PG_DSN"]
        self.schema = f"sb_s_{sfx}"
        self.schemas = [self.schema]
        self.runtime, self.portal, self.purge, self.reset = (
            f"sb_{n}_{sfx}" for n in ("rt", "po", "pu", "rs")
        )
        self.roles = [self.runtime, self.portal, self.purge, self.reset]
        self.scoped = self.scope(self.schema)
        self.stores = []

    def scope(self, schema):
        return make_conninfo(self.dsn, options=f"-c search_path={schema}")

    def dsn_of(self, role, scoped=None):
        return make_conninfo(scoped or self.scoped, user=role)

    def admin(self):
        return psycopg.connect(self.scoped, autocommit=True)

    def as_(self, role, autocommit=True):
        return psycopg.connect(self.dsn_of(role), autocommit=autocommit)

    def migrate(self, **kw):
        roles = {
            "runtime_role": self.runtime,
            "portal_role": self.portal,
            "purge_role": self.purge,
            "reset_role": self.reset,
        }
        return migrate(self.scoped, **{**roles, **kw})

    def store(self, role, scoped=None):
        """A store whose one connection is logged in as `role` (proven, not assumed)."""
        s = make(
            "store",
            PostgresSettings(**SETTINGS),
            FakeSecretProvider({"pg-dsn": self.dsn_of(role, scoped)}),
        )
        self.stores.append(s)
        assert s._db.execute("SELECT current_user").fetchone()[0] == role
        s._db.execute("SET statement_timeout = '30s'")  # a blocked statement fails, never hangs
        return s

    def new_role(self, part, options="LOGIN"):
        name = f"sb_{part}_{self.sfx}"
        with psycopg.connect(self.dsn, autocommit=True) as db:
            db.execute(sql.SQL("CREATE ROLE {} {}").format(sql.Identifier(name), sql.SQL(options)))
        self.roles.append(name)
        return name

    def new_schema(self, part):
        name = f"sb_{part}_{self.sfx}"
        with psycopg.connect(self.dsn, autocommit=True) as db:
            db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(name)))
        self.schemas.append(name)
        return self.scope(name)

    def run(self, statement, params=()):
        with self.admin() as db:
            return db.execute(statement, params).fetchall()

    def do(self, statement):
        with self.admin() as db:
            db.execute(statement)

    def grant(self, text, *names):
        """Owner-side GRANT or REVOKE; `{}` slots are identifiers."""
        with self.admin() as db:
            db.execute(sql.SQL(text).format(*(sql.Identifier(n) for n in names)))

    def exists(self, relation):
        return self.run("SELECT to_regclass(%s) IS NOT NULL", (f"{self.schema}.{relation}",))[0][0]

    def read(self):
        """The stop state as a NEW connection of the runtime login reads it."""
        s = self.store(self.runtime)
        try:
            return s.get_kill_switch()
        finally:
            s._db.close()

    def count(self, table):
        return self.run(sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(table)))[0][0]

    def kinds(self):
        return [r[0] for r in self.run("SELECT kind FROM audit_entries ORDER BY seq")]

    def rights(self, role):
        """{relation: set of privileges} the role effectively holds on every relation of the schema."""
        out = {}
        with self.admin() as db:
            rels = db.execute(
                "SELECT c.oid, c.relname, c.relkind FROM pg_class c JOIN pg_namespace n "
                "ON n.oid = c.relnamespace WHERE n.nspname = %s AND c.relkind IN ('r','p','v','m','S')",
                (self.schema,),
            ).fetchall()
            for oid, name, kind in rels:
                if kind == "S":
                    privs, q = ("USAGE", "SELECT", "UPDATE"), "has_sequence_privilege"
                else:
                    privs = ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES")
                    privs, q = (*privs, "TRIGGER"), "has_table_privilege"
                held = {
                    p
                    for p in privs
                    if db.execute(f"SELECT {q}(%s, %s, %s)", (role, oid, p)).fetchone()[0]
                }
                if held:
                    out[name] = held
        return out


@pytest.fixture(name="w")
def stop_world():
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


def _stop(w, by="ops:stop"):
    rt = w.store(w.runtime)
    rt.set_kill_switch(KillSwitch(on=True, by=by))
    return rt


def _denied(w, role, statement, relation):
    assert w.exists(relation), f"{relation} does not exist: a refusal would prove nothing"
    with w.as_(role) as db, pytest.raises(DENIED):
        db.execute(statement)


# ---- Normal ----------------------------------------------------------------------------------------------------------


def test_n1_a_stop_by_the_runtime_login_reads_on_from_a_second_connection(w):
    assert w.read().on is False
    _stop(w, "ops:first")
    ks = w.read()
    assert (ks.on, ks.by) == (True, "ops:first")
    assert w.run('SELECT "on" FROM kill_switch')[0][0] is False  # one INSERT, the flag untouched
    assert w.count("kill_switch_stops") == 1


def test_n2_a_reset_by_the_reset_login_reads_off(w):
    """Also settles the ticket's open point: the foreign-key check lets the reset login insert a clear."""
    _stop(w, "ops:a")
    _stop(w, "ops:b")
    w.store(w.reset).set_kill_switch(OFF)
    assert w.read().on is False
    assert [r[0] for r in w.run('SELECT "by" FROM kill_switch_clears')] == ["admin:reset"] * 2
    _stop(w, "ops:later")  # a stop after the reset is open again
    ks = w.read()
    assert (ks.on, ks.by) == (True, "ops:later")


def test_n2_the_reset_login_writes_the_reset_audit_row_itself(w):
    """Limits.reset on a store and a chain audit that both hold ONLY the reset login's connection."""
    _stop(w)
    rs = w.store(w.reset)
    audit = make("audit", ChainSettings(kind="chain"), store=rs, signer=None, anchor=None)
    Limits(rs, audit, None).reset("admin:r")
    assert w.kinds() == ["limits.reset"]
    assert w.read().on is False


def test_n4_migrate_twice_keeps_the_state_and_the_grants(w):
    before = {r: w.rights(r) for r in w.roles}
    _stop(w)
    assert w.migrate() == []
    assert w.read().on is True
    assert {r: w.rights(r) for r in w.roles} == before
    w.store(w.reset).set_kill_switch(OFF)
    assert w.migrate() == []
    assert w.read().on is False
    assert (w.count("kill_switch_stops"), w.count("kill_switch_clears")) == (1, 1)


def test_n5_without_a_reset_role_named_the_runtime_still_stops_and_reads(w):
    other = w.new_schema("s2")
    migrate(other, runtime_role=w.runtime)
    rt = w.store(w.runtime, other)
    assert rt.get_kill_switch().on is False
    rt.set_kill_switch(KillSwitch(on=True, by="ops"))
    assert rt.get_kill_switch().on is True
    with pytest.raises(DENIED):
        rt.set_kill_switch(OFF)
    assert rt.get_kill_switch().on is True


# ---- Invariant 6: exact rights ---------------------------------------------------------------------------------------


def test_the_reset_role_holds_exactly_the_rights_of_the_ticket(w):
    assert w.rights(w.reset) == {
        "kill_switch": {"SELECT", "UPDATE"},
        "kill_switch_stops": {"SELECT"},
        "kill_switch_clears": {"SELECT", "INSERT"},
        "audit_entries": {"SELECT", "INSERT"},
        "audit_checkpoints": {"SELECT"},
    }
    q = "SELECT has_schema_privilege(%s, %s, 'USAGE'), has_schema_privilege(%s, %s, 'CREATE')"
    assert w.run(q, (w.reset, w.schema, w.reset, w.schema))[0] == (True, False)


def test_the_other_roles_hold_exactly_their_rights_on_the_stop_relations(w):
    stop = {"kill_switch", "kill_switch_stops", "kill_switch_clears"}
    runtime = {k: v for k, v in w.rights(w.runtime).items() if k.startswith("kill_switch")}
    assert runtime == {
        "kill_switch": {"SELECT"},
        "kill_switch_stops": {"SELECT", "INSERT"},
        "kill_switch_clears": {"SELECT"},
    }
    for role in (w.portal, w.purge):
        assert not stop & set(w.rights(role)), role


def test_the_four_roles_are_not_members_of_each_other(w):
    for a in w.roles[:4]:
        for b in w.roles[:4]:
            if a != b:
                assert w.run("SELECT pg_has_role(%s, %s, 'MEMBER')", (a, b))[0][0] is False


# ---- Invariant 3: the stop id (ticket, CORRECTED 5) ------------------------------------------------------------------


def test_the_stop_id_is_a_database_chosen_uuid_and_no_sequence_exists(w):
    q = (
        "SELECT data_type, column_default FROM information_schema.columns "
        "WHERE table_schema = %s AND table_name = 'kill_switch_stops' AND column_name = 'id'"
    )
    kind, default = w.run(q, (w.schema,))[0]
    assert kind == "uuid", f"the stop id is {kind}, the ticket asks for a random UUID"
    assert "gen_random_uuid" in (default or "")
    assert not w.exists("kill_switch_stops_id_seq")
    assert not [k for k in GRANTS if k.startswith("kill_switch") and GRANTS[k].kind == "sequence"]


def test_h2_the_runtime_login_cannot_make_a_later_stop_fail(w):
    """The runtime login may INSERT, so it may also choose ids. Whatever it plants, a reset and then an honest
    stop must still work and read ON (a serial id lets it plant the ids the sequence hands out next)."""
    kind = w.run(
        "SELECT data_type FROM information_schema.columns WHERE table_schema = %s "
        "AND table_name = 'kill_switch_stops' AND column_name = 'id'",
        (w.schema,),
    )[0][0]
    planted = list(range(1, 201)) if kind != "uuid" else [uuid.uuid4() for _ in range(200)]
    with w.as_(w.runtime) as db:
        for i in planted:
            db.execute('INSERT INTO kill_switch_stops (id, "by") VALUES (%s, %s)', (i, "planted"))
    w.store(w.reset).set_kill_switch(OFF)
    assert w.read().on is False
    rt = w.store(w.runtime)
    for n in range(3):
        rt.set_kill_switch(KillSwitch(on=True, by=f"ops:honest{n}"))
    ks = w.read()
    assert (ks.on, ks.by) == (True, "ops:honest0")


def test_h3_a_fake_reset_audit_row_by_the_runtime_login_clears_nothing(w):
    rt = _stop(w)
    audit = make("audit", ChainSettings(kind="chain"), store=rt, signer=None, anchor=None)
    audit.write_intent(Limits._event(False, "agent:x", "reset"))
    assert w.kinds() == ["limits.reset"]
    assert w.read().on is True and w.count("kill_switch_clears") == 0


# ---- Edge ------------------------------------------------------------------------------------------------------------


def test_e1_a_reset_with_nothing_open_is_fine(w):
    rs = w.store(w.reset)
    rs.set_kill_switch(OFF)
    rs.set_kill_switch(OFF)
    assert w.read().on is False and w.count("kill_switch_clears") == 0


def test_e2_two_resets_at_once_both_succeed(w):
    rt = _stop(w)
    for n in range(20):
        rt.set_kill_switch(KillSwitch(on=True, by=f"ops:{n}"))
    stores, gate, failed = [w.store(w.reset), w.store(w.reset)], threading.Barrier(2), []

    def reset(store):
        try:
            gate.wait(timeout=10)
            store.set_kill_switch(OFF)
        except Exception as exc:  # noqa: BLE001 - reported below
            failed.append(exc)

    threads = [threading.Thread(target=reset, args=(s,)) for s in stores]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)
    assert failed == []
    assert w.read().on is False
    assert w.count("kill_switch_clears") == w.count("kill_switch_stops") == 21


def test_e2_a_reset_that_overlaps_an_uncommitted_reset_succeeds(w):
    """Deterministic overlap: reset A has inserted its clears and not committed; reset B then waits on the same
    stop ids and, once A commits, must end without an error (ON CONFLICT DO NOTHING)."""
    _stop(w)
    a, b, failed = w.store(w.reset), w.store(w.reset), []
    pid = b._db.info.backend_pid

    def second():
        try:
            b.set_kill_switch(OFF)
        except Exception as exc:  # noqa: BLE001 - reported below
            failed.append(exc)

    t = threading.Thread(target=second)
    waited = False
    with (
        a._db.transaction()
    ):  # the store's own transaction becomes a savepoint: nothing is committed yet
        a.set_kill_switch(OFF)
        t.start()
        q = "SELECT count(*) FROM pg_stat_activity WHERE pid = %s AND wait_event_type = 'Lock'"
        for _ in range(100):
            if w.run(q, (pid,))[0][0]:
                waited = True
                break
            time.sleep(0.1)
    t.join(timeout=60)
    assert waited, "reset B never waited on reset A: the two did not overlap"
    assert failed == []
    assert w.read().on is False and w.count("kill_switch_clears") == 1


def test_e3_a_stop_committed_after_the_reset_ran_stays_on(w):
    _stop(w, "ops:before")
    with w.as_(w.runtime, autocommit=False) as a:
        a.execute('INSERT INTO kill_switch_stops ("by") VALUES (%s)', ("ops:in-flight",))
        w.store(w.reset).set_kill_switch(OFF)  # cannot see the uncommitted stop
        assert w.read().on is False
        a.commit()
    ks = w.read()
    assert (ks.on, ks.by) == (True, "ops:in-flight")
    assert (w.count("kill_switch_stops"), w.count("kill_switch_clears")) == (2, 1)


def test_e4_a_thousand_stops_then_one_reset_reads_off(w):
    rt = w.store(w.runtime)
    for n in range(1000):
        rt.set_kill_switch(KillSwitch(on=True, by=f"ops:{n}"))
    assert w.read().on is True
    w.store(w.reset).set_kill_switch(OFF)
    assert w.read().on is False
    assert w.count("kill_switch_clears") == 1000


def test_e5_a_flag_set_on_by_the_owner_reads_on_and_a_reset_turns_it_off(w):
    w.do('UPDATE kill_switch SET "on" = TRUE, "by" = \'owner:flag\'')
    ks = w.read()
    assert (ks.on, ks.by) == (True, "owner:flag")
    w.store(w.reset).set_kill_switch(OFF)
    assert w.read().on is False
    assert w.run('SELECT "on" FROM kill_switch')[0][0] is False


def test_e6_a_deleted_flag_row_reads_on_and_a_reset_fails_loudly_and_stays_on(w):
    """Ticket S7: a reset that finds no flag row raises, clears nothing and is audited as reset_failed."""
    _stop(w)
    w.do("DELETE FROM kill_switch")
    assert w.read().on is True
    rs = w.store(w.reset)
    with pytest.raises(ConfigError, match="kill_switch row missing"):
        rs.set_kill_switch(OFF)
    audit = make("audit", ChainSettings(kind="chain"), store=rs, signer=None, anchor=None)
    with pytest.raises(ConfigError):
        Limits(rs, audit, None).reset("admin:r")
    assert w.kinds() == ["limits.reset", "limits.reset_failed"]
    assert cli.kill_switch(Limits(rs, audit, None), "reset", "admin:r") == 2
    ks = w.read()
    assert (ks.on, ks.by) == (True, "system:kill_switch_row_missing")
    assert w.count("kill_switch_clears") == 0


def test_e7_a_flag_on_before_0006_stays_on_after_the_upgrade(w, monkeypatch):
    old = w.new_schema("up")
    files = migrate_mod._migration_files()
    with (
        monkeypatch.context() as m
    ):  # the release before step B: five files and no stop rows in the map
        m.setattr(migrate_mod, "_migration_files", lambda: files[:5])
        for name in [
            k for k in GRANTS if k.startswith("kill_switch_") or k == "spend_reservations"
        ]:
            m.delitem(GRANTS, name)
        assert migrate(old)[-1].startswith("0005_")
    with psycopg.connect(old, autocommit=True) as db:
        assert db.execute("SELECT to_regclass('kill_switch_stops')").fetchone()[0] is None
        db.execute('UPDATE kill_switch SET "on" = TRUE, "by" = \'user:before\'')
    roles = {"runtime_role": w.runtime, "reset_role": w.reset, "purge_role": w.purge}
    assert migrate(old, **roles) == ["0006_stop_state", "0007_spend_reservations"]
    rt = w.store(w.runtime, old)
    ks = rt.get_kill_switch()
    assert (ks.on, ks.by) == (True, "user:before")
    with pytest.raises(DENIED):
        rt.set_kill_switch(OFF)
    assert rt.get_kill_switch().on is True
    w.store(w.reset, old).set_kill_switch(OFF)
    assert rt.get_kill_switch().on is False


def test_e8_a_refused_clear_leaves_the_flag_on(w):
    """The flag update and the clears are one transaction: when the second statement fails, the first is undone."""
    _stop(w)
    w.do('UPDATE kill_switch SET "on" = TRUE')
    w.grant("REVOKE INSERT ON kill_switch_clears FROM {}", w.reset)
    with pytest.raises(DENIED):
        w.store(w.reset).set_kill_switch(OFF)
    assert w.run('SELECT "on" FROM kill_switch')[0][0] is True
    assert w.read().on is True


# ---- Per-role negatives ----------------------------------------------------------------------------------------------

RUNTIME_DENIED = [
    ("kill_switch_clears", 'INSERT INTO kill_switch_clears (stop_id, "by") SELECT id, \'x\' FROM kill_switch_stops'),
    ("kill_switch_clears", "UPDATE kill_switch_clears SET \"by\" = 'x'"),
    ("kill_switch_clears", "DELETE FROM kill_switch_clears"),
    ("kill_switch_clears", "TRUNCATE kill_switch_clears"),
    ("kill_switch_stops", 'UPDATE kill_switch_stops SET "by" = NULL'),
    ("kill_switch_stops", "DELETE FROM kill_switch_stops"),
    ("kill_switch_stops", "TRUNCATE kill_switch_stops CASCADE"),
    ("kill_switch", 'UPDATE kill_switch SET "on" = FALSE'),
    ("kill_switch", "UPDATE kill_switch SET \"by\" = 'x' WHERE id = 1"),
    ("kill_switch", "INSERT INTO kill_switch (id, schema_version, \"on\", ts) VALUES (1, 1, FALSE, now())"),
    ("kill_switch", 'INSERT INTO kill_switch (id, schema_version, "on", ts) VALUES (1, 1, FALSE, now()) ON CONFLICT (id) DO UPDATE SET "on" = FALSE'),
    ("kill_switch", "DELETE FROM kill_switch"),
    ("kill_switch", "TRUNCATE kill_switch"),
]  # fmt: skip


@pytest.mark.parametrize(
    "relation,statement", RUNTIME_DENIED, ids=[s[:34] for _, s in RUNTIME_DENIED]
)
def test_runtime_login_is_denied_and_the_switch_stays_on(w, relation, statement):
    _stop(w)
    _denied(w, w.runtime, statement, relation)
    assert w.read().on is True
    assert (w.count("kill_switch_stops"), w.count("kill_switch_clears")) == (1, 0)


def test_f1_set_kill_switch_off_by_the_runtime_login_raises_and_the_switch_stays_on(w):
    rt = _stop(w, "ops:f1")
    with pytest.raises(DENIED):
        rt.set_kill_switch(OFF)
    assert (
        rt.get_kill_switch().on is True
    )  # the same connection still works (no poisoned transaction)
    ks = w.read()
    assert (ks.on, ks.by) == (True, "ops:f1")
    assert w.count("kill_switch_clears") == 0


def test_f1_the_runtime_login_cannot_turn_an_on_flag_off_either(w):
    w.do('UPDATE kill_switch SET "on" = TRUE')
    with pytest.raises(DENIED):
        w.store(w.runtime).set_kill_switch(OFF)
    assert w.read().on is True
    assert w.run('SELECT "on" FROM kill_switch')[0][0] is True


RESET_DENIED = [
    ("kill_switch_stops", "INSERT INTO kill_switch_stops (\"by\") VALUES ('x')"),
    ("kill_switch_stops", "INSERT INTO kill_switch_stops DEFAULT VALUES"),
    ("kill_switch_stops", 'UPDATE kill_switch_stops SET "by" = NULL'),
    ("kill_switch_stops", "DELETE FROM kill_switch_stops"),
    ("kill_switch_stops", "TRUNCATE kill_switch_stops CASCADE"),
    ("kill_switch_clears", 'UPDATE kill_switch_clears SET "by" = NULL'),
    ("kill_switch_clears", "DELETE FROM kill_switch_clears"),
    ("kill_switch_clears", "TRUNCATE kill_switch_clears"),
    ("kill_switch", "DELETE FROM kill_switch"),
    ("kill_switch", "INSERT INTO kill_switch (id, schema_version, \"on\", ts) VALUES (1, 1, FALSE, now())"),
    ("runs", "SELECT 1 FROM runs"),
    ("plans", "SELECT 1 FROM plans"),
    ("tool_calls", "SELECT 1 FROM tool_calls"),
    ("redaction_maps", "SELECT 1 FROM redaction_maps"),
    ("spend", "SELECT 1 FROM spend"),
    ("audit_outbox", "INSERT INTO audit_outbox (event_id, body) VALUES ('x', '{}')"),
    ("audit_outbox", "SELECT 1 FROM audit_outbox"),
    ("audit_checkpoints", "INSERT INTO audit_checkpoints DEFAULT VALUES"),
    ("audit_entries", "UPDATE audit_entries SET body = '{}'"),
    ("audit_entries", "DELETE FROM audit_entries"),
]  # fmt: skip


@pytest.mark.parametrize("relation,statement", RESET_DENIED, ids=[s[:34] for _, s in RESET_DENIED])
def test_reset_login_is_denied(w, relation, statement):
    _stop(w)
    _denied(w, w.reset, statement, relation)
    assert w.read().on is True  # the reset login did not stop, clear or change anything by the way


def test_the_reset_login_cannot_stop(w):
    with pytest.raises(DENIED):
        w.store(w.reset).set_kill_switch(KillSwitch(on=True, by="admin"))
    assert w.count("kill_switch_stops") == 0


@pytest.mark.parametrize("who", ["purge", "portal"])
@pytest.mark.parametrize("relation", STOP_RELATIONS)
def test_purge_and_portal_logins_hold_no_right_on_the_stop_relations(w, who, relation):
    role = getattr(w, who)
    _stop(w)
    w.store(w.reset).set_kill_switch(OFF)
    _stop(w)
    table = sql.Identifier(relation)
    for statement in (
        "SELECT 1 FROM {}",
        "INSERT INTO {} DEFAULT VALUES",
        'UPDATE {} SET "by" = NULL',
        "DELETE FROM {}",
        "TRUNCATE {} CASCADE",
    ):
        _denied(w, role, sql.SQL(statement).format(table), relation)
    assert w.read().on is True


# ---- Owner: the trigger ----------------------------------------------------------------------------------------------


@pytest.mark.parametrize("table", STOP_RELATIONS[1:])
@pytest.mark.parametrize(
    "statement", ['UPDATE {} SET "by" = NULL', "DELETE FROM {}", "TRUNCATE {} CASCADE"]
)
def test_the_owner_is_refused_by_the_append_only_trigger(w, table, statement):
    _stop(w)
    w.store(w.reset).set_kill_switch(OFF)
    _stop(w)
    with w.admin() as db, pytest.raises(errors.RaiseException, match="append-only"):
        db.execute(sql.SQL(statement).format(sql.Identifier(table)))
    assert (w.count("kill_switch_stops"), w.count("kill_switch_clears")) == (2, 1)
    assert w.read().on is True


# ---- migrate refusals ------------------------------------------------------------------------------------------------


def test_migrate_refuses_a_reset_role_that_is_the_runtime_role(w):
    with pytest.raises(ConfigError, match="different roles"):
        migrate(w.scoped, runtime_role=w.runtime, reset_role=w.runtime)
    with pytest.raises(ConfigError, match="different roles"):
        w.migrate(reset_role=w.purge)


@pytest.mark.parametrize("member,group", [("reset", "runtime"), ("runtime", "reset")])
def test_migrate_refuses_reset_and_runtime_as_members_of_each_other(w, member, group):
    w.grant("GRANT {} TO {}", getattr(w, group), getattr(w, member))
    with pytest.raises(ConfigError, match="members of each other"):
        w.migrate()


def test_migrate_refuses_a_superuser_reset_role(w):
    boss = w.new_role("su", "NOLOGIN SUPERUSER")
    with pytest.raises(
        ConfigError, match="members of each other|holds more than the grant map.*superuser"
    ):
        w.migrate(reset_role=boss)


def test_migrate_refuses_a_reset_role_that_owns_a_relation(w):
    w.do("CREATE TABLE stray (x INT)")
    w.grant("ALTER TABLE stray OWNER TO {}", w.reset)
    with pytest.raises(ConfigError, match="reset role holds more than the grant map.*owns stray"):
        w.migrate()


def test_migrate_refuses_a_reset_role_that_is_a_member_of_the_owner(w):
    owner = w.run("SELECT current_user")[0][0]
    member = w.new_role("mo", "NOLOGIN NOINHERIT")
    w.grant("GRANT {} TO {}", owner, member)
    try:
        with pytest.raises(
            ConfigError, match="reset role holds more than the grant map.*member of"
        ):
            w.migrate(reset_role=member)
    finally:
        w.grant("REVOKE {} FROM {}", owner, member)


def test_migrate_refuses_a_public_right_to_clear_when_a_runtime_role_is_named(w):
    w.do("GRANT INSERT ON kill_switch_clears TO PUBLIC")
    with pytest.raises(
        ConfigError, match="runtime role holds more than the grant map.*kill_switch_clears"
    ):
        w.migrate()


def test_migrate_refuses_a_public_right_the_reset_role_would_inherit(w):
    w.do("GRANT SELECT ON runs TO PUBLIC")
    with pytest.raises(ConfigError, match="reset role holds more than the grant map.*runs"):
        migrate(w.scoped, reset_role=w.reset)


def test_a_direct_excess_grant_to_the_reset_role_is_gone_after_migrate(w):
    w.grant("GRANT DELETE ON kill_switch_clears TO {}", w.reset)
    w.grant("GRANT INSERT ON kill_switch_stops TO {}", w.reset)
    assert "DELETE" in w.rights(w.reset)["kill_switch_clears"]
    assert w.migrate() == []
    assert w.rights(w.reset)["kill_switch_clears"] == {"SELECT", "INSERT"}
    assert w.rights(w.reset)["kill_switch_stops"] == {"SELECT"}


def test_migrate_with_a_reset_role_that_does_not_exist_applies_nothing(
    w, cfg_dir, monkeypatch, capsys
):
    fresh, ghost = w.new_schema("gh"), f"sb_ghost_{w.sfx}"
    with pytest.raises(errors.UndefinedObject):
        migrate(fresh, reset_role=ghost)
    with psycopg.connect(fresh, autocommit=True) as db:
        assert db.execute("SELECT to_regclass('kill_switch_stops')").fetchone()[0] is None
    _demo(cfg_dir)
    monkeypatch.setenv("HADAVIN_MIGRATE_DSN", fresh)
    assert cli.main(["--config", str(cfg_dir), "migrate", "--reset-role", ghost]) == 3
    assert "Traceback" not in capsys.readouterr().err
    with psycopg.connect(fresh, autocommit=True) as db:
        assert db.execute("SELECT to_regclass('kill_switch_stops')").fetchone()[0] is None


@pytest.mark.parametrize(
    "name",
    ["x; DROP TABLE runs", 'r" WITH SUPERUSER', "a b", "Reset", "", "public", "none", "session_user", "current_user"],
)  # fmt: skip
def test_h4_a_role_name_that_is_not_one_plain_role_is_refused_before_any_connection(name):
    with pytest.raises(ConfigError, match="not a plain database role name"):
        migrate(
            "postgresql://unused.invalid/none", reset_role=name
        )  # never connected: the name check is first


def test_cli_migrate_passes_the_reset_role_and_the_reset_login_can_then_reset(
    w, cfg_dir, monkeypatch
):
    fresh = w.new_schema("cm")
    _demo(cfg_dir)
    monkeypatch.setenv("HADAVIN_MIGRATE_DSN", fresh)
    argv = [
        "--config",
        str(cfg_dir),
        "migrate",
        "--runtime-role",
        w.runtime,
        "--reset-role",
        w.reset,
    ]
    assert cli.main(argv) == 0
    rt = w.store(w.runtime, fresh)
    rt.set_kill_switch(KillSwitch(on=True, by="ops"))
    w.store(w.reset, fresh).set_kill_switch(OFF)
    assert rt.get_kill_switch().on is False


# ---- CLI: limits stop / reset ----------------------------------------------------------------------------------------


def _edit(cfg, fn):
    path = cfg / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    fn(data)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def _demo(cfg_dir, ref=None):
    """The demo fixture config on a postgres store and a chain audit; `ref` sets reset_credential_ref."""

    def change(data):
        data["backends"]["store"] = dict(SETTINGS) | ({"reset_credential_ref": ref} if ref else {})
        data["backends"]["audit"] = {"kind": "chain"}

    _edit(cfg_dir, change)
    return cfg_dir


def _pilot(tmp_path, ref=RESET_REF, env="pilot"):
    from tests.test_k3_pilot_env import pilot_cfg

    cfg = pilot_cfg(tmp_path, env=env)

    def change(data):
        if ref:
            data["backends"]["store"]["reset_credential_ref"] = ref
        if (
            env == "prod"
        ):  # what prod asks for at load: a key from the secrets kind and an agreed anchor
            data["backends"]["signer"] = {
                "kind": "ed25519_local",
                "private_key_secret_name": "audit-key",
            }
            data["backends"]["anchor"] = {
                "kind": "s3_object_lock",
                "bucket": "sb-" + "anchor",
                "region": "eu-central-1",
                "retention_ack": True,
            }

    _edit(cfg, change)
    return cfg


def _provide(w, monkeypatch, held):
    """The secrets kind of the CLI answers from `held` (a dict the test may change between calls). Every store
    the CLI builds is recorded, so the fixture closes its connection."""
    real = cli.make

    def fake(capability, settings, *a, **k):
        if capability == "secrets":
            return FakeSecretProvider(dict(held))
        made = real(capability, settings, *a, **k)
        if capability == "store":
            w.stores.append(made)
        return made

    monkeypatch.setattr(cli, "make", fake)


def _limits(cfg, action, by="user:op"):
    return cli.main(["--config", str(cfg), "limits", action, "--by", by])


def _runtime_secrets(w):
    return {"pg-dsn": w.dsn_of(w.runtime), "pg-purge": w.dsn_of(w.purge)}


def test_n3_cli_round_trip_in_pilot_with_only_the_reset_dsn_for_the_reset(
    w, tmp_path, monkeypatch, capsys
):
    cfg, held = _pilot(tmp_path), _runtime_secrets(w)
    _provide(w, monkeypatch, held)
    assert _limits(cfg, "stop", "user:stopper") == 0
    ks = w.read()
    assert (ks.on, ks.by) == (True, "user:stopper")
    held.clear()
    held[RESET_REF] = w.dsn_of(w.reset)  # the operator's machine: the reset login and nothing else
    assert _limits(cfg, "reset", "user:resetter") == 0
    assert w.read().on is False
    assert w.kinds() == ["limits.stop", "limits.reset"]
    assert w.run('SELECT "by" FROM kill_switch_clears') == [("user:resetter",)]
    assert w.count("audit_checkpoints") == 0  # the reset login signs nothing
    held.clear()
    held.update(_runtime_secrets(w))
    capsys.readouterr()
    assert cli.main(["--config", str(cfg), "audit", "verify"]) == 0
    assert "intact" in capsys.readouterr().out


def test_cli_round_trip_in_demo_with_the_ref_set(w, cfg_dir, monkeypatch):
    cfg = _demo(cfg_dir, RESET_REF)
    _provide(w, monkeypatch, {"pg-dsn": w.dsn_of(w.runtime), RESET_REF: w.dsn_of(w.reset)})
    assert _limits(cfg, "reset") == 0  # nothing open
    assert _limits(cfg, "stop") == 0
    assert w.read().on is True
    assert _limits(cfg, "reset") == 0
    assert w.read().on is False
    assert w.kinds() == ["limits.reset", "limits.stop", "limits.reset"]


@pytest.mark.parametrize("env", ["pilot", "prod"])
def test_e10_reset_without_the_ref_is_refused_before_any_connection(
    w, tmp_path, monkeypatch, capsys, env
):
    cfg = _pilot(tmp_path, ref=None, env=env)
    _stop(w)

    def never(capability, *a, **k):
        raise AssertionError(f"make({capability!r}) was called: the refusal must come first")

    monkeypatch.setattr(cli, "make", never)
    assert _limits(cfg, "reset") == 2
    err = capsys.readouterr().err
    assert err.startswith(f"refused: limits reset in {env} needs the reset role's login")
    assert "migrate --reset-role" in err and "backends.store.reset_credential_ref" in err
    assert w.kinds() == [] and w.count("kill_switch_clears") == 0
    assert w.read().on is True


def test_e10_reset_in_demo_without_the_ref_uses_the_configured_login(w, cfg_dir, monkeypatch):
    """Demo keeps today's path: the one configured DSN. Here that DSN is the reset login's, so it works."""
    cfg = _demo(cfg_dir)
    _stop(w)
    _provide(w, monkeypatch, {"pg-dsn": w.dsn_of(w.reset)})
    assert _limits(cfg, "reset") == 0
    assert w.read().on is False


@pytest.mark.parametrize("how", ["demo_no_ref", "pilot_ref_names_the_runtime_dsn"])
def test_cli_reset_on_the_runtime_dsn_exits_2_stays_on_and_audits_reset_failed(
    w, cfg_dir, tmp_path, monkeypatch, capsys, how
):
    _stop(w, "ops:kept")
    if how == "demo_no_ref":
        cfg, held = _demo(cfg_dir), {"pg-dsn": w.dsn_of(w.runtime)}
    else:
        cfg, held = _pilot(tmp_path), {RESET_REF: w.dsn_of(w.runtime)}
    _provide(w, monkeypatch, held)
    assert _limits(cfg, "reset", "agent:hostile") == 2
    err = capsys.readouterr().err
    assert "NOT reset" in err and "Nothing was changed" in err and "InsufficientPrivilege" in err
    assert "reset_credential_ref" in err and "Traceback" not in err
    assert w.kinds() == ["limits.reset", "limits.reset_failed"]
    ks = w.read()
    assert (ks.on, ks.by) == (True, "ops:kept")
    assert w.count("kill_switch_clears") == 0


def test_e8_cli_reset_with_the_audit_down_exits_3_and_clears_nothing(
    w, tmp_path, monkeypatch, capsys
):
    cfg = _pilot(tmp_path)
    _stop(w)
    w.do('UPDATE kill_switch SET "on" = TRUE')
    w.grant("REVOKE INSERT ON audit_entries FROM {}", w.reset)  # the intent row cannot be written
    _provide(w, monkeypatch, {RESET_REF: w.dsn_of(w.reset)})
    assert _limits(cfg, "reset") == 3
    assert "The kill switch stays ON" in capsys.readouterr().err
    assert w.kinds() == [] and w.count("kill_switch_clears") == 0
    assert w.run('SELECT "on" FROM kill_switch')[0][0] is True
    assert w.read().on is True


HOSTILE_BY = {
    "empty": "",
    "newline": "user:a\nkill switch OFF (by root)",
    "ten_thousand": "x" * 10_000,
    "nul": "user:a\x00b",
}


@pytest.mark.parametrize("case", sorted(HOSTILE_BY))
def test_h1_a_hostile_by_ends_with_a_clean_exit_code(w, cfg_dir, monkeypatch, capsys, case):
    by = HOSTILE_BY[case]
    cfg = _demo(cfg_dir, RESET_REF)
    _provide(w, monkeypatch, {"pg-dsn": w.dsn_of(w.runtime), RESET_REF: w.dsn_of(w.reset)})
    code = _limits(cfg, "stop", by)
    err = capsys.readouterr().err
    assert code in (0, 2), err[:300]
    assert "Traceback" not in err and "failed:" not in err
    assert w.read().on is (code == 0)  # the state agrees with the exit code
    _stop(w, "ops:real")
    code = _limits(cfg, "reset", by)
    err = capsys.readouterr().err
    assert code in (0, 2), err[:300]
    assert "Traceback" not in err and "failed:" not in err
    assert w.read().on is (code != 0)


# ---- Invariant 10: the loop ------------------------------------------------------------------------------------------


@pytest.fixture(name="app")
def loop_app(live_cfg_dir, fake_system):
    from tests.test_review_pr3_round2 import app as pr3_app

    return pr3_app.__wrapped__(live_cfg_dir, fake_system)


def _unreadable(w):
    """E9: a login `migrate` never granted (the schema is visible, the stop relations are not readable)."""
    nobody = w.new_role("ng")
    w.grant("GRANT USAGE ON SCHEMA {} TO {}", w.schema, nobody)
    store = w.store(nobody)
    with pytest.raises(DENIED):
        store.get_kill_switch()
    return store.get_kill_switch


def test_e9_an_unreadable_stop_state_at_the_first_check_means_no_model_call(
    w, app, fake_system, monkeypatch
):
    from tests.test_cuj import _doc

    monkeypatch.setattr(app.store, "get_kill_switch", _unreadable(w))
    run = app.runtime.handle("test-agent", "svc:test-agent", _doc(app, "create.txt"))
    assert (run.state, run.reason_code) == (RunState.NEEDS_PERSON, "limits_unavailable")
    assert app.runtime.llm.calls == [] and fake_system.creates == 0


def test_e9_an_unreadable_stop_state_at_the_recheck_means_no_action(
    w, app, fake_system, monkeypatch
):
    from tests.test_cuj import _approve, _doc, _pending

    run = app.runtime.handle("test-agent", "svc:test-agent", _doc(app, "create.txt"))
    monkeypatch.setattr(app.store, "get_kill_switch", _unreadable(w))
    _approve(app, _pending(app, run.run_id))
    final = app.store.get_run(run.run_id)
    assert (final.state, final.reason_code) == (RunState.NEEDS_PERSON, "recheck.limits_unavailable")
    assert fake_system.creates == 0


# ---- Invariants 9 and 11 (no database needed; kept here so one file covers the ticket's role story) ------------------


def test_the_runtime_start_up_probe_never_resolves_the_reset_dsn():
    settings = PostgresSettings(
        **SETTINGS,
        purge_dsn_secret_name="pg-purge",  # noqa: S106 - a name
        reset_credential_ref=RESET_REF,
    )
    assert platform_secrets.secret_names(settings) == {"pg-dsn", "pg-purge"}
    with pytest.raises(ConfigError, match="may read only the secrets named"):
        platform_secrets.bound(FakeSecretProvider({RESET_REF: "x"}), settings, "store")(RESET_REF)
    assert not [
        f for f in PostgresSettings.model_fields if "reset" in f and f.endswith("_secret_name")
    ]


def test_the_python_signatures_are_unchanged():
    from hadavin_sdk.store.postgres import PostgresStore

    for owner in (Store, PostgresStore):
        assert list(inspect.signature(owner.get_kill_switch).parameters) == ["self"]
        assert list(inspect.signature(owner.set_kill_switch).parameters) == ["self", "ks"]
    for method in (Limits.stop, Limits.reset):
        assert list(inspect.signature(method).parameters) == ["self", "by"]
    names = list(inspect.signature(migrate).parameters)
    assert names[:5] == ["dsn", "runtime_role", "portal_role", "purge_role", "reset_role"]
