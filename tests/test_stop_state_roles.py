"""Step B, the stop state, against a real PostgreSQL through real non-superuser logins.

Written by a different agent than the builder, from the ticket (handover/core-b/tickets/B-stop-state.md), not
from the code. Every case gets a fresh schema and four LOGIN roles (runtime, portal, purge, reset) with random
names, `migrate(...)` with all four named, and drops only what it made. "Denied" means
`psycopg.errors.InsufficientPrivilege` exactly, and the relation is proven to exist first, so a missing relation
never counts as a denial. Needs HADAVIN_TEST_PG_DSN (CI: the postgres service); skipped without it."""

from __future__ import annotations

import contextlib
import inspect
import io
import logging
import os
import sys
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
from tests import pg_gate

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)

DENIED = errors.InsufficientPrivilege
# One advisory lock for the whole server (tests/pg_gate.py). Every `migrate` call of every test module holds it
# SHARED (tests/conftest.py wraps it); a case that makes a role that every other migrate would refuse (below
# PostgreSQL 16, a CREATEROLE login is listed server-wide) holds it EXCLUSIVE while the role exists, so no other
# migrate runs meanwhile, with or without pytest-xdist.
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
        settings = PostgresSettings(**SETTINGS)
        if (
            role == self.reset
        ):  # the CLI marks the reset login (E6): it is not held to the runtime's rights
            settings._login_role = "reset"
        s = make("store", settings, FakeSecretProvider({"pg-dsn": self.dsn_of(role, scoped)}))
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
        "kill_switch_resets": {"SELECT", "INSERT"},  # 0009: the reset's own record
        "kill_switch_watermark": {"SELECT", "INSERT", "UPDATE"},  # 0009
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
        "kill_switch_watermark": {
            "SELECT"
        },  # 0009: read only; no right at all on kill_switch_resets
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
        created, _ = migrate_mod._scan(files[:5])
        for name in [k for k in GRANTS if k not in created]:  # every relation a later file creates
            m.delitem(GRANTS, name)
        made = migrate_mod._functions_created(files[:5])
        for sig in [
            s for s in migrate_mod.FUNCTION_GRANTS if migrate_mod._signature_key(s) not in made
        ]:
            m.delitem(migrate_mod.FUNCTION_GRANTS, sig)
        assert migrate(old, no_roles=True)[-1].startswith("0005_")
    with psycopg.connect(old, autocommit=True) as db:
        assert db.execute("SELECT to_regclass('kill_switch_stops')").fetchone()[0] is None
        db.execute('UPDATE kill_switch SET "on" = TRUE, "by" = \'user:before\'')
    roles = {"runtime_role": w.runtime, "reset_role": w.reset, "purge_role": w.purge}
    assert migrate(
        old, **roles
    ) == [  # every file from 0006 on: a new migration never breaks this test
        p.stem for p in sorted(migrate_mod.MIGRATIONS.glob("*.sql")) if p.stem >= "0006"
    ]
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
            ConfigError,
            match="is a member of .*the owner of the hadavin_\\* functions: remove the membership",
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
    assert code == (2 if case == "nul" else 0), err[
        :300
    ]  # a NUL cannot be stored: refused, never a crash
    assert "Traceback" not in err and "failed:" not in err
    assert w.read().on is (code == 0)  # the state agrees with the exit code
    _stop(w, "ops:real")
    code = _limits(cfg, "reset", by)
    err = capsys.readouterr().err
    assert code == (2 if case == "nul" else 0), err[
        :300
    ]  # a NUL cannot be stored: refused, never a crash
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


def test_e9_a_stop_state_that_turns_unreadable_at_any_later_read_means_no_card_and_no_action(
    w, app, fake_system, monkeypatch
):
    """The loop reads the limits more than once before a card is posted (before each model call and again once
    the plan is ready). A clean run counts the reads; then, for every k after the first, a new run whose k-th and
    later reads fail must go to a person with nothing done."""
    from tests.test_cuj import _doc

    real, broken, reads, fail_from = app.store.get_kill_switch, _unreadable(w), [], [0]

    def counted():
        reads.append(1)
        return broken() if fail_from[0] and len(reads) >= fail_from[0] else real()

    monkeypatch.setattr(app.store, "get_kill_switch", counted)
    clean = app.runtime.handle("test-agent", "svc:test-agent", _doc(app, "create.txt"))
    total = len(reads)
    assert clean.state == RunState.WAITING_FOR_APPROVAL, clean.reason_code
    assert total >= 2, "the loop read the stop state once only: this case would test nothing"
    seen = {}
    for k in range(2, total + 1):
        reads.clear()
        app.runtime.llm._attempts.clear()  # the fake model replays the same recordings for the next run
        fail_from[0] = k
        run = app.runtime.handle("test-agent", "svc:test-agent", _doc(app, "create.txt"))
        assert len(reads) >= k, f"read {k} was never made"
        seen[k] = (run.state, run.reason_code)
    assert seen == dict.fromkeys(range(2, total + 1), (RunState.NEEDS_PERSON, "limits_unavailable"))
    assert fake_system.creates == 0


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


# ======================================================================================================================
# Fix round 3 (ticket: "RESOLUTION of review round 1", S1 to S12). Written from the ticket by a different agent than
# the builder. The cases above are unchanged.
# ======================================================================================================================


def _shadow(w, store, flag=True, stops=True, clears=True):
    """What a taken-over runtime session could try (S1): TEMPORARY tables with the names of the stop relations, made
    on the store's own connection. The temporary flag is off, the temporary stops are empty and the temporary
    clears hold a clear for every real stop. Each shadow is proven to be what an unqualified name finds."""
    db, real = store._db, sql.Identifier(w.schema)
    if flag:
        db.execute(
            sql.SQL("CREATE TEMPORARY TABLE kill_switch AS SELECT * FROM {}.kill_switch").format(
                real
            )
        )
        db.execute('UPDATE kill_switch SET "on" = FALSE, "by" = \'temp:off\'')
        assert db.execute('SELECT "by" FROM kill_switch').fetchall() == [("temp:off",)]
    if stops:
        db.execute(
            sql.SQL(
                "CREATE TEMPORARY TABLE kill_switch_stops (LIKE {}.kill_switch_stops INCLUDING DEFAULTS)"
            ).format(real)
        )
        assert db.execute("SELECT count(*) FROM kill_switch_stops").fetchone()[0] == 0
    if clears:
        db.execute(
            sql.SQL(
                "CREATE TEMPORARY TABLE kill_switch_clears (LIKE {}.kill_switch_clears INCLUDING DEFAULTS)"
            ).format(real)
        )
        db.execute(
            sql.SQL(
                "INSERT INTO kill_switch_clears (stop_id, \"by\") SELECT id, 'temp:clear' FROM {}.kill_switch_stops"
            ).format(real)
        )
        n = db.execute("SELECT count(*) FROM kill_switch_clears").fetchone()[0]
        assert n == w.count("kill_switch_stops")


# ---- S1 (invariant 14): a temporary table does not change what the store reads or where a stop lands -----------------


@pytest.mark.parametrize("which", ["stops", "clears", "all_three"])
def test_s1_temporary_tables_on_the_runtime_connection_do_not_hide_an_open_stop(w, which):
    _stop(w, "ops:real")
    rt = w.store(w.runtime)
    _shadow(
        w,
        rt,
        flag=which == "all_three",
        stops=which != "clears",
        clears=which != "stops",
    )
    ks = rt.get_kill_switch()
    assert ks.on is True
    assert ks.by == "ops:real"
    rt.set_kill_switch(KillSwitch(on=True, by="ops:second"))  # lands in the real table
    assert w.count("kill_switch_stops") == 2
    assert w.count("kill_switch_clears") == 0
    assert w.read().on is True


def test_s1_a_temporary_flag_table_does_not_hide_a_real_flag_that_is_on(w):
    w.do('UPDATE kill_switch SET "on" = TRUE, "by" = \'owner:flag\'')
    rt = w.store(w.runtime)
    _shadow(w, rt, stops=False, clears=False)
    ks = rt.get_kill_switch()
    assert ks.on is True
    assert ks.by == "owner:flag"


def test_s1_a_temporary_flag_table_does_not_hide_a_missing_flag_row(w):
    rt = w.store(w.runtime)
    _shadow(w, rt, stops=False, clears=False)
    w.do("DELETE FROM kill_switch")
    assert rt.get_kill_switch().on is True


def test_s1_temporary_tables_made_before_any_stop_do_not_swallow_the_stop(w):
    rt = w.store(w.runtime)
    _shadow(w, rt)
    assert rt.get_kill_switch().on is False
    rt.set_kill_switch(KillSwitch(on=True, by="ops:after-temp"))
    stops = w.count("kill_switch_stops")
    assert stops == 1, "the stop went into the temporary table, not the real one"
    assert rt._db.execute("SELECT count(*) FROM kill_switch_stops").fetchone()[0] == 0
    assert rt.get_kill_switch().on is True
    ks = w.read()
    assert (ks.on, ks.by) == (True, "ops:after-temp")


def test_s1_the_runtime_login_cannot_reset_through_its_temporary_tables(w):
    """With unqualified names the reset would 'succeed' on the session's own tables and the store would read OFF."""
    _stop(w, "ops:kept")
    rt = w.store(w.runtime)
    _shadow(w, rt)
    with pytest.raises(DENIED):
        rt.set_kill_switch(OFF)
    assert rt.get_kill_switch().on is True
    assert w.read().on is True and w.count("kill_switch_clears") == 0


def test_s1_a_reset_by_the_reset_login_with_temporary_tables_clears_the_real_stop(w):
    _stop(w)
    rs = w.store(w.reset)
    _shadow(w, rs, flag=False, clears=False)  # the reset session "sees" no stop by the bare name
    rs.set_kill_switch(OFF)
    assert w.count("kill_switch_clears") == 1
    assert w.read().on is False


def test_s1_a_search_path_that_names_no_schema_is_refused_at_connect(w):
    with pytest.raises(ConfigError, match="search_path names no schema"):
        make(
            "store",
            PostgresSettings(**SETTINGS),
            FakeSecretProvider({"pg-dsn": w.dsn_of(w.runtime, w.scope(f"sb_none_{w.sfx}"))}),
        )


# ---- S2 (invariant 7): who else can clear ----------------------------------------------------------------------------


_STOP_REFUSAL = "roles other than the reset role could clear a stop"
_MONEY_REFUSAL = "roles not named in this command can run the money functions"


def _refused_naming(w, role, call=None, reset=None):
    """`migrate` raises the who-else ConfigError naming `role`, and its transaction rolled back: a marker right the
    owner gave the runtime role by hand (a migrate that committed would have revoked it) is still there.

    Two true refusals can apply and the money one runs first: a role that inherits the execute right of a named role,
    or any role when a role of an earlier call is left unnamed, is refused as an unnamed money executor. Then `role`
    must still be what the stop check lists (`_who(..., reset)`), and the return is None (no stop-check names)."""
    w.grant("GRANT DELETE ON kill_switch_stops TO {}", w.runtime)
    before = {r: w.rights(r) for r in w.roles[:4]}
    assert "DELETE" in before[w.runtime]["kill_switch_stops"]
    with pytest.raises(ConfigError, match=f"{_STOP_REFUSAL}|{_MONEY_REFUSAL}") as e:
        (call or w.migrate)()
    text = str(e.value)
    assert {r: w.rights(r) for r in w.roles[:4]} == before
    if _STOP_REFUSAL in text:
        names = text.split("could clear a stop", 1)[1].split(". Name the runtime")[0]
        assert role in names, f"{role} is not named in: {e.value}"
        return names
    assert role in text or role in _who(w.scoped, reset), f"{role} is not named in: {e.value}"
    return None


S2_STRAY = {
    "update_on_the_flag": "GRANT UPDATE ON kill_switch TO {}",
    "insert_on_the_clears": "GRANT INSERT ON kill_switch_clears TO {}",
    "column_update_of_on": 'GRANT UPDATE ("on") ON kill_switch TO {}',
    "column_insert_of_stop_id": "GRANT INSERT (stop_id) ON kill_switch_clears TO {}",
    "delete_on_the_flag": "GRANT DELETE ON kill_switch TO {}",
    "truncate_on_the_flag": "GRANT TRUNCATE ON kill_switch TO {}",
    "trigger_on_the_flag": "GRANT TRIGGER ON kill_switch TO {}",
    "trigger_on_the_stops": "GRANT TRIGGER ON kill_switch_stops TO {}",
    "trigger_on_the_clears": "GRANT TRIGGER ON kill_switch_clears TO {}",
}


@pytest.mark.parametrize("case", sorted(S2_STRAY))
def test_s2_migrate_refuses_a_third_role_that_holds_a_right_to_clear(w, case):
    third = w.new_role("x3", "NOLOGIN")
    w.grant(S2_STRAY[case], third)
    names = _refused_naming(w, third)
    assert w.reset not in names and w.runtime not in names
    w.grant("REVOKE ALL ON kill_switch, kill_switch_stops, kill_switch_clears FROM {}", third)
    assert w.migrate() == []  # the right gone: the same command passes


@pytest.mark.parametrize("options", ["LOGIN NOINHERIT", "LOGIN"])
def test_s2_migrate_refuses_a_member_of_the_reset_role(w, options):
    member = w.new_role("mb", options)
    w.grant("GRANT {} TO {}", w.reset, member)
    _refused_naming(w, member)
    w.grant("REVOKE {} FROM {}", w.reset, member)
    assert w.migrate() == []


def test_s2_migrate_refuses_a_member_of_a_member_of_the_reset_role(w):
    middle, far = w.new_role("m1", "NOLOGIN NOINHERIT"), w.new_role("m2", "LOGIN NOINHERIT")
    w.grant("GRANT {} TO {}", w.reset, middle)
    w.grant("GRANT {} TO {}", middle, far)
    names = _refused_naming(w, far)
    assert middle in names


def test_s2_migrate_refuses_the_runtime_role_as_a_noinherit_member_of_a_group_that_can_clear(w):
    """The runtime role holds no right itself (NOINHERIT), so the per-role check sees nothing; it can SET ROLE."""
    group = w.new_role("gr", "NOLOGIN")
    w.grant("GRANT UPDATE ON kill_switch TO {}", group)
    w.grant("GRANT USAGE ON SCHEMA {} TO {}", w.schema, group)
    w.grant("ALTER ROLE {} NOINHERIT", w.runtime)
    w.grant("GRANT {} TO {}", group, w.runtime)
    assert "UPDATE" not in w.rights(w.runtime)["kill_switch"]
    with w.as_(w.runtime) as db:  # the path is real: the runtime login turns the flag by SET ROLE
        db.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(group)))
        db.execute('UPDATE kill_switch SET "on" = FALSE')
    names = _refused_naming(w, w.runtime)
    assert group in names


def _who(scoped, reset, accepted=()):
    with pg_gate.shared(), psycopg.connect(scoped, autocommit=True) as db:
        return migrate_mod.who_else_can_clear(db, reset, accepted)


def test_s2_roles_of_the_server_with_no_grant_on_these_relations_are_not_listed(w):
    """The check reads this schema's grants only. A role with nothing here, a member of the (superuser) owner and
    a member of a predefined role that can write every table are outside the guarantee and never refuse a migrate.
    (Before 2026-11-20 the member of pg_write_all_data and the member of the owner were refused by the stop check; the
    member of pg_write_all_data is now refused by the money-table writer check, not by this one.)"""
    owner = w.run("SELECT current_user")[0][0]
    w.new_role("st")
    of_owner, writer = w.new_role("mw", "LOGIN NOINHERIT"), w.new_role("wa")
    # A member of pg_write_all_data writes every table of the SERVER: another worker's migrate with named roles would
    # refuse it as a writer of the money tables. The exclusive gate (cross-process) keeps those migrates out while the
    # membership exists; it is revoked before the gate is released.
    with pg_gate.exclusive():
        w.grant("GRANT {} TO {}", owner, of_owner)
        w.grant("GRANT pg_write_all_data TO {}", writer)
        try:
            assert _who(w.scoped, w.reset) == []
            # a member of pg_write_all_data can write the money tables: refused as such (step 4), not by the stop
            # check; a member of the owner is outside the guarantee
            with pytest.raises(ConfigError, match=f"can write a money table.*{writer}"):
                w.migrate()
            w.grant("REVOKE pg_write_all_data FROM {}", writer)
            assert w.migrate() == []
        finally:
            w.grant("REVOKE {} FROM {}", owner, of_owner)
            w.grant("REVOKE pg_write_all_data FROM {}", writer)


def _second_schema(w):
    """A second application on the same server: its own schema, owned by a login that is NOT a superuser, with its
    own stop-state tables, runtime role and reset role."""
    owner, rt2, rs2 = w.new_role("ow"), w.new_role("r2"), w.new_role("s2")
    name = f"sb_two_{w.sfx}"
    with psycopg.connect(w.dsn, autocommit=True) as db:
        db.execute(
            sql.SQL("CREATE SCHEMA {} AUTHORIZATION {}").format(
                sql.Identifier(name), sql.Identifier(owner)
            )
        )
    w.schemas.append(name)
    scoped = w.dsn_of(owner, w.scope(name))
    assert "0006_stop_state" in migrate(scoped, runtime_role=rt2, reset_role=rs2)
    return scoped, owner, rt2, rs2


def test_s2_a_second_schema_with_its_own_stop_tables_and_roles_does_not_change_this_schemas_answer(
    w,
):
    two, _owner, rt2, rs2 = _second_schema(w)
    stray, member = w.new_role("x5", "NOLOGIN"), w.new_role("y5")
    with psycopg.connect(two, autocommit=True) as db:
        db.execute(sql.SQL("GRANT UPDATE ON kill_switch TO {}").format(sql.Identifier(stray)))
    w.grant("GRANT {} TO {}", rs2, member)
    assert _who(two, rs2) == sorted([stray, member])
    assert _who(w.scoped, w.reset) == []  # the other schema's roles are not this schema's business
    assert w.migrate() == []
    with pytest.raises(
        ConfigError, match=f"{_STOP_REFUSAL}|{_MONEY_REFUSAL}"
    ):  # the member inherits rs2's rights
        migrate(two, runtime_role=rt2, reset_role=rs2)
    here = w.new_role("x6", "NOLOGIN")
    w.grant("GRANT INSERT ON kill_switch_clears TO {}", here)
    assert _who(w.scoped, w.reset) == [here]
    assert _who(two, rs2) == sorted([stray, member])  # and the reverse


def test_s2_a_member_of_an_owner_that_is_not_a_superuser_is_not_listed(w):
    two, owner, rt2, rs2 = _second_schema(w)
    of_owner = w.new_role("mo2", "LOGIN NOINHERIT")
    w.grant("GRANT {} TO {}", owner, of_owner)
    assert _who(two, rs2) == []
    assert _who(two, None) == [rs2]  # the owner is never listed, the unnamed reset role is
    assert migrate(two, runtime_role=rt2, reset_role=rs2) == []


def test_s2_a_grant_to_public_is_listed_as_public(w):
    w.do("GRANT INSERT ON kill_switch_clears TO PUBLIC")
    assert _who(w.scoped, w.reset) == ["PUBLIC"]
    names = _refused_naming(
        w, "PUBLIC", lambda: migrate(w.scoped, reset_role=w.reset), reset=w.reset
    )
    if names is not None:  # (the unnamed runtime role is refused first as a money executor)
        assert w.runtime not in names  # one name, not every role of the server
    w.do("REVOKE INSERT ON kill_switch_clears FROM PUBLIC")
    w.do('GRANT UPDATE ("on") ON kill_switch TO PUBLIC')
    assert _who(w.scoped, w.reset) == ["PUBLIC"]


def test_s2_a_member_of_a_role_that_holds_the_right_is_listed_with_it(w):
    group, member, far = w.new_role("g7", "NOLOGIN"), w.new_role("m7"), w.new_role("f7")
    w.grant("GRANT INSERT ON kill_switch_clears TO {}", group)
    w.grant("GRANT {} TO {}", group, member)
    w.grant("GRANT {} TO {}", member, far)
    assert _who(w.scoped, w.reset) == sorted([group, member, far])


def _membership(w, role, member):
    return w.run(
        "SELECT admin_option, inherit_option, set_option FROM pg_auth_members "
        "WHERE roleid = %s::regrole AND member = %s::regrole",
        (role, member),
    )


def test_s2_the_creator_of_the_reset_role_with_the_admin_option_only_is_listed(w):
    """PostgreSQL 16 and later: a CREATEROLE login that is not a superuser is made a member, WITH ADMIN OPTION
    only, of every role it creates. It cannot use the role's rights today, but it can grant itself SET or INHERIT
    at any time, so it is listed (review B-WE-M1; until 2026-11-20 this case was NOT listed). Revoking the ADMIN
    option makes the check pass."""
    if w.run("SELECT current_setting('server_version_num')::int < 160000")[0][0]:
        pytest.skip(
            "pg_auth_members has no admin_option, inherit_option and set_option before PostgreSQL 16"
        )
    creator = w.new_role("cr", "LOGIN CREATEROLE")
    made = f"sb_s8_{w.sfx}"
    with psycopg.connect(w.dsn_of(creator, w.dsn), autocommit=True) as db:
        db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(made)))
    w.roles.insert(4, made)  # dropped before its creator
    assert _membership(w, made, creator) == [(True, False, False)]
    with (
        psycopg.connect(w.dsn_of(creator, w.dsn), autocommit=True) as db,
        pytest.raises(DENIED),
    ):
        db.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(made)))
    fresh = w.new_schema("cr")
    assert "0006_stop_state" in migrate(
        fresh, no_roles=True
    )  # a --no-roles migrate runs no check (and a refusal rolls back)
    with pytest.raises(
        ConfigError, match="roles other than the reset role could clear a stop"
    ) as e:
        migrate(fresh, runtime_role=w.runtime, reset_role=made)
    assert creator in str(e.value)
    assert _who(fresh, made) == [creator]
    w.grant("REVOKE ADMIN OPTION FOR {} FROM {}", made, creator)
    assert _who(fresh, made) == []
    assert migrate(fresh, runtime_role=w.runtime, reset_role=made) == []


def test_s2_a_member_of_a_role_that_holds_a_right_with_the_admin_option_only_is_listed(w):
    """PostgreSQL 16 and later: ADMIN on a role that holds the right (not only on the reset role) counts."""
    if w.run("SELECT current_setting('server_version_num')::int < 160000")[0][0]:
        pytest.skip("no admin_option before PostgreSQL 16")
    group, admin = w.new_role("ga", "NOLOGIN"), w.new_role("ad", "LOGIN")
    w.grant("GRANT INSERT ON kill_switch_clears TO {}", group)
    w.grant("GRANT {} TO {} WITH ADMIN TRUE, INHERIT FALSE, SET FALSE", group, admin)
    assert _who(w.scoped, w.reset) == sorted([group, admin])


def _below_16(w):
    return w.run("SELECT current_setting('server_version_num')::int < 160000")[0][0]


@contextlib.contextmanager
def _server_wide_createrole(w, count=1):
    """`count` LOGIN CREATEROLE roles for as long as the block runs, under the EXCLUSIVE server gate (below 16 they
    are listed server-wide: see tests/pg_gate.py); NOCREATEROLE again before the gate is released."""
    made = []
    with pg_gate.exclusive():
        try:
            for _ in range(count):
                made.append(w.new_role(f"cq{len(made)}", "LOGIN CREATEROLE"))
            yield made
        finally:
            for creator in made:
                w.grant("ALTER ROLE {} NOCREATEROLE", creator)


def test_s2_below_16_a_createrole_login_that_is_not_a_superuser_is_listed(w):
    """Before PostgreSQL 16 a CREATEROLE login can GRANT the reset role to itself, and holds nothing now."""
    if not _below_16(w):
        pytest.skip(
            "from PostgreSQL 16 CREATEROLE alone cannot grant a role it has no ADMIN option on"
        )
    with _server_wide_createrole(w) as (creator,):
        assert _who(w.scoped, w.reset) == [creator]
        with pytest.raises(
            ConfigError, match="roles other than the reset role could clear a stop"
        ) as e:
            w.migrate()
        assert "accepted_admin_roles" in str(e.value) and "--accept-admin-role" in str(e.value)
        w.grant("ALTER ROLE {} NOCREATEROLE", creator)
        assert w.migrate() == []


def test_s2_below_16_an_accepted_createrole_role_is_not_listed_and_another_one_still_is(w, caplog):
    if not _below_16(w):
        pytest.skip("below PostgreSQL 16 only: from 16 the CREATEROLE listing does not exist")
    with _server_wide_createrole(w, 2) as (vouched, other):
        assert _who(w.scoped, w.reset) == sorted([vouched, other])
        assert _who(w.scoped, w.reset, (vouched,)) == [other]
        with pytest.raises(
            ConfigError, match="roles other than the reset role could clear a stop"
        ) as e:
            w.migrate(accepted_admin_roles=(vouched,))
        names = str(e.value).split("could clear a stop", 1)[1].split(". Name the runtime")[0]
        assert other in names and vouched not in names
        w.grant("ALTER ROLE {} NOCREATEROLE", other)
        with caplog.at_level(logging.WARNING, logger="hadavin_sdk.store"):
            assert w.migrate(accepted_admin_roles=(vouched,)) == []
        assert vouched in caplog.text and "not checked" in caplog.text


def test_s2_below_16_a_member_of_an_accepted_createrole_role_is_listed_and_the_role_alone_is_not(w):
    if not _below_16(w):
        pytest.skip("below PostgreSQL 16 only: from 16 the accepted list has no effect")
    with _server_wide_createrole(w) as (vouched,):
        member = w.new_role("mv", "LOGIN")
        w.grant("GRANT {} TO {}", vouched, member)
        assert _who(w.scoped, w.reset, (vouched,)) == [member]
        names = _refused_naming(w, member, lambda: w.migrate(accepted_admin_roles=(vouched,)))
        assert vouched not in names
        w.grant("REVOKE {} FROM {}", vouched, member)
        assert _who(w.scoped, w.reset, (vouched,)) == []


def test_s2_an_accepted_role_that_holds_a_grant_or_a_membership_here_is_still_listed(w):
    """The allow-list is for the CREATEROLE listing only, never for a grant on the stop tables or a membership."""
    with _server_wide_createrole(w) as (creator,):
        w.grant("GRANT UPDATE ON kill_switch TO {}", creator)
        assert _who(w.scoped, w.reset, (creator,)) == [creator]
        _refused_naming(w, creator, lambda: w.migrate(accepted_admin_roles=(creator,)))
        w.grant("REVOKE UPDATE ON kill_switch FROM {}", creator)
        w.grant("GRANT {} TO {}", w.reset, creator)
        assert _who(w.scoped, w.reset, (creator,)) == [creator]
        w.grant("REVOKE {} FROM {}", w.reset, creator)
        w.grant("GRANT TRIGGER ON kill_switch_stops TO {}", creator)
        assert _who(w.scoped, w.reset, (creator,)) == [creator]
        w.grant("REVOKE TRIGGER ON kill_switch_stops FROM {}", creator)
        assert _who(w.scoped, w.reset, (creator,)) == []


_BAD_ACCEPTED = "accepted_admin_roles must be database role names"
FORMAT_BAD = {  # id: name (the id is what a mutant pins)
    "length64": "a" * 64,
    "trailing_space": "admin ",
    "leading_space": " admin",
    "empty": "",
    "bel": "ad" + chr(7) + "min",
    "newline": "ad" + chr(10) + "min",
    "del": "ad" + chr(127) + "min",
    "lone_surrogate": chr(0xD800),
    "nel": "ad" + chr(0x85) + "min",
    "line_separator": "ad" + chr(0x2028) + "min",
    "paragraph_separator": "ad" + chr(0x2029) + "min",
    "zero_width_space": "ad" + chr(0x200B) + "min",
    "bidi_override": "ad" + chr(0x202E) + "min",
    "bidi_isolate": "ad" + chr(0x2066) + "min",
}
FORBIDDEN = {
    "public_lower": "public",
    "public_upper": "PUBLIC",
    "public_title": "Public",
    "none_lower": "none",
    "none_upper": "NONE",
    "session_user_lower": "session_user",
    "session_user_upper": "SESSION_USER",
    "current_user_mixed": "Current_User",
    "star": "*",
    "percent": "%",
}


@pytest.mark.parametrize("bad", list(FORMAT_BAD.values()), ids=list(FORMAT_BAD))
def test_s2_an_accepted_role_name_of_the_wrong_format_is_refused_before_any_connection(bad):
    with pytest.raises(ConfigError, match=_BAD_ACCEPTED):
        migrate("postgresql://unused.invalid/none", reset_role="sb_x", accepted_admin_roles=(bad,))


@pytest.mark.parametrize("bad", list(FORBIDDEN.values()), ids=list(FORBIDDEN))
def test_s2_a_forbidden_accepted_role_name_is_refused_before_any_connection(bad):
    with pytest.raises(ConfigError, match=_BAD_ACCEPTED):
        migrate("postgresql://unused.invalid/none", reset_role="sb_x", accepted_admin_roles=(bad,))


@pytest.mark.parametrize(
    "name",
    [
        "Admin",
        "my-admin",
        "user@server",
        "a" * 63,
        "a b",
        "x'; DROP TABLE kill_switch; --",
        "caf" + chr(0xE9),
        chr(0x4E2D) + chr(0x6587),
    ],
)
def test_s2_an_accepted_role_name_of_a_managed_service_is_taken_as_exact_text(w, name):
    assert w.migrate(accepted_admin_roles=(name,)) == []
    assert w.exists("kill_switch")  # the name is a bound parameter, never SQL
    assert _who(w.scoped, w.reset, (name,)) == []


def test_s2_below_16_a_non_ascii_accepted_name_is_matched_as_exact_text_against_a_real_role(w):
    if not _below_16(w):
        pytest.skip("below PostgreSQL 16 only: from 16 the CREATEROLE listing does not exist")
    with pg_gate.exclusive():
        name = f"sb_{chr(0xE9)}{chr(0x4E2D)}_{w.sfx}"
        w.new_role(f"{chr(0xE9)}{chr(0x4E2D)}", "LOGIN CREATEROLE")
        try:
            assert _who(w.scoped, w.reset) == [name]
            assert _who(w.scoped, w.reset, (name,)) == []
            assert _who(w.scoped, w.reset, (name + "x",)) == [name]
            assert w.migrate(accepted_admin_roles=(name,)) == []
        finally:
            w.grant("ALTER ROLE {} NOCREATEROLE", name)


def test_s2_below_16_the_refusal_names_the_accepted_roles(w):
    if not _below_16(w):
        pytest.skip("below PostgreSQL 16 only")
    with _server_wide_createrole(w, 2) as (vouched, other):
        with pytest.raises(ConfigError, match="could clear a stop") as e:
            w.migrate(accepted_admin_roles=(vouched,))
        tail = str(e.value).split("see docs/stop-state-runbook.md)", 1)[1]
        assert tail.startswith(". accepted administrator roles") and vouched in tail
        assert other in str(e.value)


def test_s2_below_16_a_vouched_role_is_not_listed_for_being_a_member_of_another_vouched_role(w):
    if not _below_16(w):
        pytest.skip("below PostgreSQL 16 only: from 16 the accepted list has no effect")
    with _server_wide_createrole(w, 2) as (a, b):
        w.grant("GRANT {} TO {}", a, b)
        assert _who(w.scoped, w.reset, (a, b)) == []
        c = w.new_role("mc", "LOGIN")
        w.grant("GRANT {} TO {}", b, c)
        assert _who(w.scoped, w.reset, (a, b)) == [c]


def test_s2_a_vouched_role_that_is_a_member_of_a_listed_role_is_listed(w):
    """Vouching covers the CREATEROLE listing only: a vouched role that is a member of a role that holds a right
    (case 1), or of a CREATEROLE role that is not accepted (case 2, below 16), is listed for the membership."""
    with _server_wide_createrole(w, 2) as (b, p2):
        below = _below_16(w)
        p = w.new_role("pq", "NOLOGIN")
        w.grant("GRANT UPDATE ON kill_switch TO {}", p)
        w.grant("GRANT {} TO {}", p, b)
        assert _who(w.scoped, w.reset, (b,)) == sorted([b, p] + ([p2] if below else []))
        w.grant("REVOKE {} FROM {}", p, b)
        w.grant("REVOKE UPDATE ON kill_switch FROM {}", p)
        if below:
            w.grant("GRANT {} TO {}", p2, b)
            assert _who(w.scoped, w.reset, (b,)) == sorted([b, p2])


def test_s2_below_16_a_member_of_an_accepted_owner_is_not_listed(w):
    """The owner of the stop tables is outside the guarantee: vouching for it (it holds CREATEROLE here) seeds
    nothing, and its members are not followed, exactly as without the vouching."""
    if not _below_16(w):
        pytest.skip("below PostgreSQL 16 only: from 16 the accepted list has no effect")
    with pg_gate.exclusive():
        two, owner, _rt2, rs2 = _second_schema(w)
        member = w.new_role("mw", "LOGIN")
        w.grant("GRANT {} TO {}", owner, member)
        w.grant("ALTER ROLE {} CREATEROLE", owner)
        try:
            assert _who(two, rs2) == []
            assert _who(two, rs2, (owner,)) == []
        finally:
            w.grant("ALTER ROLE {} NOCREATEROLE", owner)


def test_s2_below_16_a_member_of_an_accepted_superuser_is_not_listed(w):
    if not _below_16(w):
        pytest.skip("below PostgreSQL 16 only: from 16 the accepted list has no effect")
    su, member = w.new_role("sv", "LOGIN SUPERUSER CREATEROLE"), w.new_role("sm", "LOGIN")
    w.grant("GRANT {} TO {}", su, member)
    assert _who(w.scoped, w.reset, (su,)) == []


def test_s2_accepted_roles_given_as_one_string_are_refused():
    with pytest.raises(ConfigError, match=_BAD_ACCEPTED):
        migrate("postgresql://unused.invalid/none", reset_role="sb_x", accepted_admin_roles="sb_y")


def test_s2_accepted_roles_without_named_roles_are_refused():
    with pytest.raises(ConfigError, match="only read when roles are named"):
        migrate("postgresql://unused.invalid/none", accepted_admin_roles=("sb_y",))


def test_s2_an_accepted_role_that_is_also_a_named_role_is_refused():
    with pytest.raises(ConfigError, match="must not name a role this command grants: sb_x"):
        migrate(
            "postgresql://unused.invalid/none", reset_role="sb_x", accepted_admin_roles=("sb_x",)
        )


def test_cli_migrate_prints_and_logs_every_accepted_admin_role(
    w, cfg_dir, monkeypatch, capsys, caplog
):
    fresh = w.new_schema("ac")
    _demo(cfg_dir)
    monkeypatch.setenv("HADAVIN_MIGRATE_DSN", fresh)
    one, two = f"sb_ac1_{w.sfx}", f"sb_ac2_{w.sfx}"
    base = [
        "--config",
        str(cfg_dir),
        "migrate",
        "--runtime-role",
        w.runtime,
        "--reset-role",
        w.reset,
    ]
    assert cli.main(base) == 0
    assert "accepted" not in capsys.readouterr().out
    argv = [*base, "--accept-admin-role", one, "--accept-admin-role", two]
    with caplog.at_level(logging.WARNING, logger="hadavin_sdk.store"):
        assert cli.main(argv) == 0
    # below 16 the line says who is vouched for; from 16 it says the option has no effect (one line either way)
    start = "accepted administrator roles" if _below_16(w) else "accepted_admin_roles has no effect"
    line = [x for x in capsys.readouterr().out.splitlines() if x.startswith(start)]
    assert len(line) == 1 and one in line[0] and two in line[0]
    assert one in caplog.text and two in caplog.text


def test_cli_migrate_notes_never_fail_on_a_stdout_that_cannot_encode_the_name(
    w, cfg_dir, monkeypatch
):
    fresh = w.new_schema("en")
    _demo(cfg_dir)
    monkeypatch.setenv("HADAVIN_MIGRATE_DSN", fresh)
    raw = io.BytesIO()
    out = io.TextIOWrapper(raw, encoding="cp1252", errors="strict", write_through=True)
    monkeypatch.setattr(sys, "stdout", out)
    cjk = chr(0x4E2D) + chr(0x6587)
    argv = [
        "--config",
        str(cfg_dir),
        "migrate",
        "--runtime-role",
        w.runtime,
        "--reset-role",
        w.reset,
    ]
    assert cli.main([*argv, "--accept-admin-role", cjk]) == 0
    assert chr(92) + "u4e2d" in raw.getvalue().decode("cp1252")


def test_cli_migrate_refuses_a_lone_surrogate_in_an_accepted_role_with_exit_2(
    w, cfg_dir, monkeypatch
):
    _demo(cfg_dir)
    monkeypatch.setenv("HADAVIN_MIGRATE_DSN", w.scoped)
    argv = [
        "--config",
        str(cfg_dir),
        "migrate",
        "--runtime-role",
        w.runtime,
        "--reset-role",
        w.reset,
    ]
    assert cli.main([*argv, "--accept-admin-role", chr(0xD800)]) == 2


class _BrokenOut(io.StringIO):
    """A stdout whose every write and flush fails, as a broken pipe does."""

    def write(self, text):
        raise OSError("broken pipe")

    def flush(self):
        raise OSError("broken pipe")


def _closed_out():
    out = io.StringIO()
    out.close()  # a write then raises ValueError, not OSError
    return out


@pytest.mark.parametrize("kind", ["oserror", "closed"])
def test_cli_migrate_a_fully_broken_stdout_never_changes_the_exit_code(
    w, cfg_dir, monkeypatch, capsys, kind
):
    """EVERY stdout write fails (the accepted-roles note and the "applied" line). A success still exits 0, a refusal
    still exits 2, and the refusal text still reaches stderr."""
    _demo(cfg_dir)
    vouched = f"sb_ac4_{w.sfx}"
    argv = [
        "--config",
        str(cfg_dir),
        "migrate",
        "--runtime-role",
        w.runtime,
        "--reset-role",
        w.reset,
        "--purge-role",
        w.purge,
        "--portal-role",
        w.portal,
        "--accept-admin-role",
        vouched,
    ]
    monkeypatch.setattr(sys, "stdout", _BrokenOut() if kind == "oserror" else _closed_out())
    monkeypatch.setenv("HADAVIN_MIGRATE_DSN", w.new_schema("bo"))
    assert cli.main(argv) == 0
    third = w.new_role("x4", "NOLOGIN")
    w.grant("GRANT UPDATE ON kill_switch TO {}", third)
    monkeypatch.setenv("HADAVIN_MIGRATE_DSN", w.scoped)
    assert cli.main(argv) == 2
    err = capsys.readouterr().err
    assert "refused:" in err and third in err


def test_cli_migrate_prints_the_accepted_admin_roles_when_it_refuses_too(
    w, cfg_dir, monkeypatch, capsys
):
    _demo(cfg_dir)
    monkeypatch.setenv("HADAVIN_MIGRATE_DSN", w.scoped)
    third, vouched = w.new_role("x3", "NOLOGIN"), f"sb_ac3_{w.sfx}"
    w.grant("GRANT UPDATE ON kill_switch TO {}", third)
    argv = [
        "--config",
        str(cfg_dir),
        "migrate",
        "--runtime-role",
        w.runtime,
        "--reset-role",
        w.reset,
        "--purge-role",
        w.purge,
        "--portal-role",
        w.portal,
    ]
    assert cli.main([*argv, "--accept-admin-role", vouched]) == 2
    captured = capsys.readouterr()
    assert vouched in captured.out and third in captured.err


def test_the_server_gate_holds_every_migrate_while_another_session_holds_it_exclusively():
    """tests/conftest.py wraps `migrate` for every module: with the gate held exclusively by another session, a
    migrate call (here the name this module imported) waits; it runs when the gate is released."""
    done = []

    def call():
        try:
            migrate("postgresql://unused.invalid/none", reset_role="Not A Role")
        except ConfigError as e:
            done.append(e)

    with psycopg.connect(os.environ["HADAVIN_TEST_PG_DSN"], autocommit=True) as holder:
        holder.execute("SELECT pg_advisory_lock(%s)", (pg_gate.GATE,))
        t = threading.Thread(target=call)
        t.start()
        t.join(1.5)
        waiting = t.is_alive() and not done
        holder.execute("SELECT pg_advisory_unlock(%s)", (pg_gate.GATE,))
        t.join(30)
    assert waiting, "migrate ran while another session held the server gate exclusively"
    assert len(done) == 1 and not t.is_alive()


def test_s2_a_view_with_a_stop_table_name_is_refused_not_passed(w):
    fresh = w.new_schema("vw")
    migrate(fresh, runtime_role=w.runtime, reset_role=w.reset)
    with psycopg.connect(fresh, autocommit=True) as db:
        db.execute("DROP TABLE kill_switch_clears")
        db.execute("CREATE VIEW kill_switch_clears AS SELECT 1 AS stop_id")
    _refuses_to_read(fresh, w.reset, "kill_switch_clears", "missing")


def test_s2_from_16_a_createrole_login_with_no_membership_is_not_listed(w):
    """From PostgreSQL 16 a CREATEROLE login can only grant roles it has the ADMIN option on."""
    if w.run("SELECT current_setting('server_version_num')::int < 160000")[0][0]:
        pytest.skip("below PostgreSQL 16 a CREATEROLE login is listed")
    w.new_role("cq", "LOGIN CREATEROLE")
    assert _who(w.scoped, w.reset) == []
    assert w.migrate() == []


def test_s2_a_superuser_with_a_right_or_a_membership_is_not_listed(w):
    """A superuser is outside the guarantee (it can do anything), so it is never listed, however it got the right."""
    su = w.new_role("su", "LOGIN SUPERUSER")
    w.grant("GRANT UPDATE ON kill_switch TO {}", su)
    w.grant("GRANT {} TO {}", w.reset, su)
    assert _who(w.scoped, w.reset) == []
    assert w.migrate() == []


def test_s2_a_dropped_column_keeps_no_grant(w):
    """A dropped column holds no right, even where the server (PostgreSQL 15) leaves its ACL in pg_attribute: the
    `NOT attisdropped` filter keeps the role out of the list."""
    third = w.new_role("dc", "NOLOGIN")
    w.do("ALTER TABLE kill_switch ADD COLUMN zz int")
    w.grant("GRANT UPDATE (zz) ON kill_switch TO {}", third)
    assert _who(w.scoped, w.reset) == [third]
    w.do("ALTER TABLE kill_switch DROP COLUMN zz")
    assert _who(w.scoped, w.reset) == []
    assert w.migrate() == []


def _refuses_to_read(conninfo, reset, *must_name):
    with psycopg.connect(conninfo, autocommit=True) as db, pytest.raises(ConfigError) as e:
        migrate_mod.who_else_can_clear(db, reset)
    text = str(e.value)
    assert "cannot check who could clear a stop" in text
    for part in must_name:
        assert part in text, f"{part!r} is not named in: {text}"
    return text


def test_s2_an_empty_search_path_is_refused_not_passed(w):
    _refuses_to_read(make_conninfo(w.dsn, options="-c search_path="), w.reset, "schema None")


def test_s2_a_search_path_whose_first_schema_has_no_stop_tables_is_refused_not_passed(w):
    # A schema that exists and holds nothing is first; the real tables (a leftover copy, from this check's point
    # of view) are one schema further on.
    w.new_schema("em")
    name = f"sb_em_{w.sfx}"
    path = f"{name},{w.schema}"  # the real tables are one schema further on
    text = _refuses_to_read(
        make_conninfo(w.dsn, options=f"-c search_path={path}"),
        w.reset,
        name,
        path,
        "kill_switch_clears",
    )
    assert "missing" in text


def test_s2_one_missing_stop_table_is_refused_not_passed(w):
    fresh = w.new_schema("pt")
    migrate(fresh, runtime_role=w.runtime, reset_role=w.reset)
    with psycopg.connect(fresh, autocommit=True) as db:
        db.execute("DROP TABLE kill_switch_clears")
    _refuses_to_read(fresh, w.reset, "kill_switch_clears")


def test_s2_a_temporary_table_with_a_stop_table_name_is_refused_not_passed(w):
    with psycopg.connect(w.scoped, autocommit=True) as db:
        db.execute("CREATE TEMP TABLE kill_switch_clears (stop_id uuid)")
        with pytest.raises(ConfigError) as e:
            migrate_mod.who_else_can_clear(db, w.reset)
    assert "resolve to another relation" in str(e.value)
    assert "kill_switch_clears" in str(e.value)


def test_s2_a_noinherit_member_of_the_reset_role_that_can_set_role_is_listed(w):
    member = w.new_role("n9", "LOGIN NOINHERIT")
    w.grant("GRANT {} TO {}", w.reset, member)
    # It can see the tables and holds no right of its own.
    w.grant("GRANT USAGE ON SCHEMA {} TO {}", w.schema, member)
    _stop(w)
    with w.as_(member) as db:  # no right of its own, and the path is real
        with pytest.raises(DENIED):
            db.execute('UPDATE kill_switch SET "on" = FALSE')
        db.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(w.reset)))
        db.execute("INSERT INTO kill_switch_clears (stop_id) SELECT id FROM kill_switch_stops")
    assert _who(w.scoped, w.reset) == [member]
    _refused_naming(w, member)


def test_s2_a_reset_role_that_is_not_named_in_the_run_is_listed_with_its_members(w):
    member = w.new_role("n0")
    w.grant("GRANT {} TO {}", w.reset, member)
    assert _who(w.scoped, None) == sorted([member, w.reset])
    assert _who(w.scoped, w.reset) == [member]
    w.grant("REVOKE {} FROM {}", w.reset, member)
    assert _who(w.scoped, None) == [w.reset]
    assert _who(w.scoped, w.reset) == []  # the reset role alone: nobody else


def test_s2_members_of_the_reset_role_are_listed_even_when_it_holds_no_right_yet(w):
    """The reset role is a base row of the check, not only a grantee: before its grants exist (or after someone
    revoked them) a member of it is still listed, because the role is the one that is given the right."""
    member = w.new_role("n8")
    w.grant("GRANT {} TO {}", w.reset, member)
    w.grant("REVOKE ALL ON kill_switch, kill_switch_stops, kill_switch_clears FROM {}", w.reset)
    assert _who(w.scoped, w.reset) == [member]


def test_s2_migrate_naming_only_the_runtime_role_refuses_the_reset_role_of_an_earlier_call(w):
    for role in (
        w.reset,
        w.portal,
        w.purge,
    ):  # else the money check (an unnamed executor) refuses first
        w.grant("REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA {} FROM {}", w.schema, role)
    names = _refused_naming(w, w.reset, lambda: migrate(w.scoped, runtime_role=w.runtime))
    assert names is not None, "the stop check itself must be the refusal"
    assert w.runtime not in names
    assert w.rights(w.reset)["kill_switch_clears"] == {"SELECT", "INSERT"}


@pytest.mark.parametrize("only", ["portal_role", "purge_role"])
def test_s2_migrate_naming_one_other_role_runs_the_same_check(w, only):
    third = w.new_role("x4", "NOLOGIN")
    w.grant("GRANT UPDATE ON kill_switch TO {}", third)
    role = {"portal_role": w.portal, "purge_role": w.purge}[only]
    names = _refused_naming(w, third, lambda: migrate(w.scoped, **{only: role}))
    assert w.reset in (
        names or _who(w.scoped, None)
    )  # no reset role named: nobody but the owner is excluded


def test_s2_the_four_roles_named_in_one_command_with_no_stray_right_pass(w):
    fresh = w.new_schema("ok")
    applied = migrate(
        fresh, runtime_role=w.runtime, portal_role=w.portal, purge_role=w.purge, reset_role=w.reset
    )
    assert "0006_stop_state" in applied
    with psycopg.connect(fresh, autocommit=True) as db:
        assert migrate_mod.who_else_can_clear(db, w.reset) == []
        assert migrate_mod.who_else_can_clear(db, None) == [w.reset]
    assert w.migrate() == []  # and again on the schema of the fixture
    rt = w.store(w.runtime, fresh)
    rt.set_kill_switch(KillSwitch(on=True, by="ops"))
    w.store(w.reset, fresh).set_kill_switch(OFF)
    assert rt.get_kill_switch().on is False


# ---- S7 and B-2 through the command line: the reset reports the state the store reads --------------------------------


def _reset_cli(w, tmp_path, monkeypatch):
    """A pilot config whose secrets hold only the reset login's DSN (the operator's machine)."""
    cfg = _pilot(tmp_path)
    _provide(w, monkeypatch, {RESET_REF: w.dsn_of(w.reset)})
    return cfg


def _waits_on_a_lock(w, role):
    q = "SELECT count(*) FROM pg_stat_activity WHERE usename = %s AND wait_event_type = 'Lock'"
    for _ in range(200):
        if w.run(q, (role,))[0][0]:
            return True
        time.sleep(0.05)
    return False


def _reset_in_a_thread(cfg, by="user:op"):
    codes = []
    t = threading.Thread(target=lambda: codes.append(_limits(cfg, "reset", by)))
    t.start()
    return t, codes


def test_s7_cli_reset_with_the_flag_row_missing_exits_2_audits_reset_failed_and_stays_on(
    w, tmp_path, monkeypatch, capsys
):
    cfg = _reset_cli(w, tmp_path, monkeypatch)
    _stop(w, "ops:kept")
    w.do("DELETE FROM kill_switch")
    assert _limits(cfg, "reset") == 2
    out, err = capsys.readouterr()
    assert "kill switch NOT reset" in err and "ConfigError" in err and "Traceback" not in err
    assert "kill switch OFF" not in out + err
    assert w.kinds() == ["limits.reset", "limits.reset_failed"]
    assert w.count("kill_switch_clears") == 0  # nothing was cleared
    assert w.read().on is True
    assert _limits(cfg, "reset") == 2  # and again: the same answer, never a quiet success
    assert w.read().on is True and w.count("kill_switch_clears") == 0


def test_s7_a_reset_with_the_flag_row_missing_clears_nothing_so_the_stop_survives_the_repair(w):
    """Had the reset cleared the stop before it noticed the missing row, putting the row back would read OFF."""
    _stop(w, "ops:kept")
    w.do("DELETE FROM kill_switch")
    with pytest.raises(ConfigError, match="kill_switch row missing"):
        w.store(w.reset).set_kill_switch(OFF)
    w.do('INSERT INTO kill_switch (id, schema_version, "on", ts) VALUES (1, 1, FALSE, now())')
    ks = w.read()
    assert (ks.on, ks.by) == (True, "ops:kept")


def test_b2_cli_reset_says_still_on_when_a_stop_commits_after_its_clear_statement_began(
    w, tmp_path, monkeypatch, capsys
):
    """Deterministic: the owner holds an uncommitted clear of the one open stop, so the reset's clear statement
    (its snapshot already taken) waits on that row. A stop committed during the wait is not in the snapshot."""
    cfg = _reset_cli(w, tmp_path, monkeypatch)
    rt = _stop(w, "ops:before")
    stop_id = w.run("SELECT id FROM kill_switch_stops")[0][0]
    with psycopg.connect(w.scoped) as owner:
        owner.execute(
            'INSERT INTO kill_switch_clears (stop_id, "by") VALUES (%s, %s)',
            (stop_id, "owner:hand"),
        )
        t, codes = _reset_in_a_thread(cfg)
        try:
            waited = _waits_on_a_lock(w, w.reset)
            rt.set_kill_switch(KillSwitch(on=True, by="ops:during"))
        finally:
            owner.commit()
            t.join(timeout=60)
    assert waited, "the reset never waited on the owner's clear: nothing overlapped"
    out, err = capsys.readouterr()
    assert codes == [2], err
    assert "kill switch still ON (set by 'ops:during' at " in err
    assert "reset again" not in err and "Check the stop reason" in err
    assert "kill switch OFF" not in out + err
    assert w.kinds() == ["limits.reset"]  # written, not failed
    ks = w.read()
    assert (ks.on, ks.by) == (True, "ops:during")
    assert _limits(cfg, "reset", "user:again") == 0
    assert "kill switch OFF (by user:again; cleared 1 stop(s))" in capsys.readouterr().out
    assert w.read().on is False


def test_s5_a_stop_committed_between_the_audit_intent_and_the_clear_statement_stays_on(
    w, tmp_path, monkeypatch, capsys
):
    """The owner locks the flag row, so the reset waits at its first statement, after its audit intent.
    E6 changed the expectation (this test pinned the old unconditional clear, which erased a stop the operator was
    never shown): the reset clears exactly the stops it read before the intent, so the stop set meanwhile stays ON,
    is named, and the exit code is 2."""
    cfg = _reset_cli(w, tmp_path, monkeypatch)
    rt = _stop(w, "ops:before")
    with psycopg.connect(w.scoped) as owner:
        owner.execute("SELECT 1 FROM kill_switch WHERE id = 1 FOR UPDATE")
        t, codes = _reset_in_a_thread(cfg)
        try:
            waited = _waits_on_a_lock(w, w.reset)
            kinds, clears = w.kinds(), w.count("kill_switch_clears")
            rt.set_kill_switch(KillSwitch(on=True, by="ops:between"))
        finally:
            owner.commit()
            t.join(timeout=60)
    assert waited, "the reset never waited on the flag row"
    assert (kinds, clears) == (
        ["limits.reset"],
        0,
    )  # the intent was written before anything was cleared
    out, err = capsys.readouterr()
    assert codes == [2], err
    assert "kill switch still ON" in err and "ops:between" in err
    assert "kill switch OFF" not in out + err
    assert w.count("kill_switch_clears") == 1  # only the stop the operator was shown
    ks = w.read()
    assert (ks.on, ks.by) == (True, "ops:between")


def test_b2_cli_normal_reset_prints_off_and_exits_0(w, tmp_path, monkeypatch, capsys):
    cfg = _reset_cli(w, tmp_path, monkeypatch)
    _stop(w)
    w.do('UPDATE kill_switch SET "on" = TRUE')
    assert _limits(cfg, "reset", "user:resetter") == 0
    out, err = capsys.readouterr()
    assert out.strip().splitlines()[-1] == "kill switch OFF (by user:resetter; cleared 1 stop(s))"
    assert "still ON" not in err
    assert w.read().on is False


# ---- B-4: the reset ref must not name the runtime's own secret -------------------------------------------------------


@pytest.mark.parametrize("env", ["demo", "pilot", "prod"])
def test_b4_a_reset_ref_equal_to_the_runtime_secret_name_is_refused_before_any_connection(
    w, cfg_dir, tmp_path, monkeypatch, capsys, env
):
    same = SETTINGS["dsn_secret_name"]
    cfg = _demo(cfg_dir, same) if env == "demo" else _pilot(tmp_path, ref=same, env=env)
    _stop(w)

    def never(capability, *a, **k):
        raise ConfigError(f"make({capability!r}) was called: the refusal must come first")

    monkeypatch.setattr(cli, "make", never)
    code = _limits(cfg, "reset")
    err = capsys.readouterr().err
    assert "was called" not in err, err
    assert code == 2
    assert err.startswith(
        "refused: backends.store.reset_credential_ref names the same secret as "
        "backends.store.dsn_secret_name"
    )
    assert w.kinds() == [] and w.count("kill_switch_clears") == 0
    assert w.read().on is True


# ---- S12: the ts of a stop -------------------------------------------------------------------------------------------


def _schema_through_0006(w, monkeypatch):
    """A fresh schema with the migrations up to 0006 only (the release before 0009 added the ts range CHECK), made as
    the owner. Migration 0009's range CHECK refuses an infinite ts as well, so on the full schema it masks the 0006
    `isfinite` CHECK: only this schema shows that one."""
    schema = w.new_schema("t6")
    files = migrate_mod._migration_files()
    upto = [f for f in files if f.stem <= "0006_stop_state"]
    assert upto[-1].stem == "0006_stop_state"
    with monkeypatch.context() as m:
        m.setattr(migrate_mod, "_migration_files", lambda: upto)
        created, _ = migrate_mod._scan(upto)
        for name in [k for k in GRANTS if k not in created]:
            m.delitem(GRANTS, name)
        made = migrate_mod._functions_created(upto)
        for sig in [
            f for f in migrate_mod.FUNCTION_GRANTS if migrate_mod._signature_key(f) not in made
        ]:
            m.delitem(migrate_mod.FUNCTION_GRANTS, sig)
        assert migrate(schema, no_roles=True)[-1] == "0006_stop_state"
    return schema


@pytest.mark.parametrize("ts", ["infinity", "-infinity"])
def test_s12_a_stop_row_cannot_carry_an_infinite_ts_even_by_hand(w, monkeypatch, ts):
    assert w.exists("kill_switch_stops")
    with w.as_(w.runtime) as db, pytest.raises(errors.CheckViolation):
        db.execute('INSERT INTO kill_switch_stops ("by", ts) VALUES (%s, %s)', ("agent:x", ts))
    assert w.count("kill_switch_stops") == 0
    # the 0006 isfinite CHECK on its own (0009's range CHECK would refuse it on the full schema too)
    old = _schema_through_0006(w, monkeypatch)
    with psycopg.connect(old, autocommit=True) as db:
        with pytest.raises(errors.CheckViolation) as e:
            db.execute('INSERT INTO kill_switch_stops ("by", ts) VALUES (%s, %s)', ("agent:x", ts))
        assert e.value.diag.constraint_name == "kill_switch_stops_ts_check"
        assert db.execute("SELECT count(*) FROM kill_switch_stops").fetchone()[0] == 0


@pytest.mark.parametrize("ts", ["infinity", "-infinity"])
def test_s12_a_clear_row_cannot_carry_an_infinite_ts_even_by_hand(w, monkeypatch, ts):
    _stop(w)
    with w.as_(w.reset) as db, pytest.raises(errors.CheckViolation):
        db.execute(
            'INSERT INTO kill_switch_clears (stop_id, "by", ts) SELECT id, %s, %s FROM kill_switch_stops',
            ("admin:x", ts),
        )
    assert w.count("kill_switch_clears") == 0 and w.read().on is True
    old = _schema_through_0006(w, monkeypatch)
    with psycopg.connect(old, autocommit=True) as db:
        db.execute('INSERT INTO kill_switch_stops ("by") VALUES (%s)', ("agent:x",))
        with pytest.raises(errors.CheckViolation) as e:
            db.execute(
                'INSERT INTO kill_switch_clears (stop_id, "by", ts) SELECT id, %s, %s FROM kill_switch_stops',
                ("admin:x", ts),
            )
        assert e.value.diag.constraint_name == "kill_switch_clears_ts_check"
        assert db.execute("SELECT count(*) FROM kill_switch_clears").fetchone()[0] == 0


# 0009 refuses a planted year outside 2000..2100 (the ts CHECK): the in-range edges are the dates a runtime can still plant
@pytest.mark.parametrize("ts", ["2000-01-01T00:00:00Z", "2099-12-31T00:00:00Z"])
def test_s12_a_hand_inserted_stop_with_another_date_is_an_open_stop_and_a_reset_clears_it(w, ts):
    with w.as_(w.runtime) as db:
        db.execute('INSERT INTO kill_switch_stops ("by", ts) VALUES (%s, %s)', ("ops:dated", ts))
    ks = w.read()
    assert (ks.on, ks.by) == (True, "ops:dated")
    w.store(w.reset).set_kill_switch(OFF)
    assert w.read().on is False
    _stop(w, "ops:now")  # and an honest stop after it is open, whatever dates lie in the table
    ks = w.read()
    assert (ks.on, ks.by) == (True, "ops:now")


@pytest.mark.parametrize(
    "ts",
    [
        "1970-01-01T00:00:00Z",
        "0100-01-01T00:00:00Z",
        "2999-01-01T00:00:00Z",
        "20000-01-01T00:00:00Z",
    ],
)
def test_s12_a_planted_year_outside_the_range_is_refused_at_insert(w, ts):
    """Migration 0009 (E12 Low 6): a stop dated outside 2000..2100 is refused by the CHECK, so it cannot make every read raise."""
    import psycopg

    with pytest.raises(psycopg.errors.CheckViolation), w.as_(w.runtime) as db:
        db.execute('INSERT INTO kill_switch_stops ("by", ts) VALUES (%s, %s)', ("ops:planted", ts))
    assert w.count("kill_switch_stops") == 0


def test_s12_the_stores_own_stop_does_not_send_ts(w):
    """The caller's clock is not trusted: a KillSwitch dated in another century is stored with the database's now."""
    from datetime import UTC, datetime

    old = datetime(2001, 1, 1, tzinfo=UTC)
    w.store(w.runtime).set_kill_switch(KillSwitch(on=True, by="ops:clock", ts=old))
    fresh = w.run("SELECT ts > now() - interval '1 hour' AND ts <= now() FROM kill_switch_stops")
    assert fresh == [(True,)]
    assert w.read().ts != old


# ---- S6: the two mutants that needed their own test ------------------------------------------------------------------


def test_s6_two_resets_while_the_flag_row_is_missing_both_fail_loudly_and_clear_nothing(w):
    """Since S7 a reset stops at the missing row, before its clear statement: two at once both raise the same
    error (never a UniqueViolation, never a quiet success) and no stop is cleared."""
    rt = _stop(w)
    for n in range(5):
        rt.set_kill_switch(KillSwitch(on=True, by=f"ops:{n}"))
    w.do("DELETE FROM kill_switch")
    stores, gate, seen = [w.store(w.reset), w.store(w.reset)], threading.Barrier(2), []

    def reset(store):
        try:
            gate.wait(timeout=10)
            store.set_kill_switch(OFF)
            seen.append("no error")
        except Exception as exc:  # noqa: BLE001 - compared below
            seen.append(f"{type(exc).__name__}: {exc}"[:36])

    threads = [threading.Thread(target=reset, args=(s,)) for s in stores]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)
    assert seen == ["ConfigError: kill_switch row missing"] * 2
    assert w.count("kill_switch_clears") == 0
    assert w.read().on is True


def test_s6_a_reset_that_meets_an_uncommitted_clear_of_the_same_stop_succeeds(w):
    """The ON CONFLICT path. Two store resets never meet there (the flag row's lock puts them in a line), but a
    clear written by hand does: the owner inserts a clear and has not committed; the reset's clear statement
    waits on that key and, once the owner commits, must end without an error."""
    _stop(w, "ops:a")
    stop_id = w.run("SELECT id FROM kill_switch_stops")[0][0]
    rs, failed = w.store(w.reset), []

    def reset():
        try:
            rs.set_kill_switch(OFF)
        except Exception as exc:  # noqa: BLE001 - reported below
            failed.append(f"{type(exc).__name__}: {exc}")

    t = threading.Thread(target=reset)
    with psycopg.connect(w.scoped) as owner:
        owner.execute(
            'INSERT INTO kill_switch_clears (stop_id, "by") VALUES (%s, %s)',
            (stop_id, "owner:hand"),
        )
        t.start()
        try:
            waited = _waits_on_a_lock(w, w.reset)
        finally:
            owner.commit()
            t.join(timeout=60)
    assert waited, "the reset never waited on the owner's clear: nothing overlapped"
    assert failed == []
    assert w.run('SELECT "by" FROM kill_switch_clears') == [("owner:hand",)]
    assert w.read().on is False


def test_s6_cli_reset_whose_clear_insert_is_refused_leaves_the_flag_on(
    w, tmp_path, monkeypatch, capsys
):
    """The flag update and the clears are one transaction: the owner took INSERT on kill_switch_clears from the
    reset role, so the second statement fails and the first (the flag off) must be undone."""
    cfg = _reset_cli(w, tmp_path, monkeypatch)
    _stop(w, "ops:kept")
    w.do('UPDATE kill_switch SET "on" = TRUE, "by" = \'owner:flag\'')
    w.grant("REVOKE INSERT ON kill_switch_clears FROM {}", w.reset)
    assert _limits(cfg, "reset") == 2
    err = capsys.readouterr().err
    assert "kill switch NOT reset" in err and "InsufficientPrivilege" in err
    assert w.run('SELECT "on", "by" FROM kill_switch') == [(True, "owner:flag")]
    assert w.kinds() == ["limits.reset", "limits.reset_failed"]
    assert w.count("kill_switch_clears") == 0
    assert w.read().on is True


# ---- S9: the migrate warning, on a real database ---------------------------------------------------------------------


def test_cli_migrate_warns_on_stderr_when_a_runtime_role_is_named_without_a_reset_role(
    w, cfg_dir, monkeypatch, capsys
):
    fresh = w.new_schema("wn")
    _demo(cfg_dir)
    monkeypatch.setenv("HADAVIN_MIGRATE_DSN", fresh)
    base = ["--config", str(cfg_dir), "migrate", "--runtime-role", w.runtime]
    assert cli.main(base) == 0
    out, err = capsys.readouterr()
    assert "warning: no reset role was named" in err and "--reset-role" in err
    assert "no reset role" not in out
    assert cli.main([*base, "--reset-role", w.reset]) == 0
    assert "no reset role" not in capsys.readouterr().err
