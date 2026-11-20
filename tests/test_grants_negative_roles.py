"""Negative tests for the grant map: what each database identity must NOT be able to do.

Written by a test-writer that did not build the code under test (plan v4 step B, session core-c). Two layers:

(a) Pure Python, no database. The whole role x table x privilege matrix is computed from `migrate.GRANTS` and
    compared with a second, hand-written list of every write privilege (`WRITES` below). A grant that is added
    or widened in `GRANTS` fails here until this file is changed on purpose, by someone who is not the builder.
    Security facts are then asserted by name (the stop table, the audit log, TRUNCATE, wildcards).
(b) PostgreSQL. A migrated schema and one fresh login role per identity; each role connects as itself and
    runs one statement per cell of the matrix: a cell `GRANTS` does not give must be refused by the database
    with "permission denied", a cell it gives must not be. Needs HADAVIN_TEST_PG_DSN (CI: the postgres
    service) and is skipped without it, like the other database tests (`pg_schema`).

Not repeated here (they exist): `has_table_privilege` over the runtime and the portal map
(tests/test_k2_migrations.py), the purge role's column reads (tests/test_k5_round10_postgres.py), stop with the
audit store down (tests/test_review_fixes.py::test_stop_works_when_audit_is_down).

STEP B (a separate reset identity for the stop state) is not built. Two tests below are marked
`xfail(strict=True)`: they say what must hold after step B using only names that exist today, and they turn
red (XPASS) the day it holds, so the marker is removed then. Everything that needs a name step B has not
chosen yet is listed here and is NOT code:

Cases to enable when step B lands
  1. The reset identity is its own `migrate()` role keyword. Add it to `HOLDS` and `WRITES`; the two pin tests
     (`test_the_identities_are_the_ones_this_file_knows`, `test_every_write_privilege_is_on_the_reviewed_list`)
     fail until that is done. It must be refused when it is the same role as, or a member of, the runtime,
     portal or purge role (as `migrate()` does for the three roles today).
  2. Matrix row of the reset identity, by statement, in `test_pg_each_role_is_refused_what_the_map_does_not_give`:
     it holds what switching the stop OFF needs and what appending the audit intent needs, and every other
     cell of every other table is refused (no read of evidence or redaction maps, no write of runs, plans,
     spend, approvals, tick state; no DELETE, no TRUNCATE anywhere).
  3. The runtime identity cannot switch the stop OFF: remove the xfail marker of
     `test_step_b_the_grant_map_gives_the_runtime_role_no_way_to_switch_the_stop_off` and of
     `test_pg_step_b_the_runtime_role_cannot_switch_the_stop_off` (update the statements if the stop state
     moves to another relation).
  4. The reset identity CAN switch the stop OFF, connected as itself, and the runtime identity can still
     switch it ON (`test_pg_the_runtime_role_can_switch_the_stop_on` stays green).
  5. The reset identity can append the audit intent and cannot UPDATE, DELETE or TRUNCATE an audit row.
  6. The portal and the purge identity hold nothing on the relation(s) of the stop state after the migration.
  7. `limits reset` run with the runtime DSN (the reset DSN missing or equal to the runtime one) ends with a
     clear error and the stop still ON; with the reset DSN it works (cli.py:184-209 uses one store today).
  8. Reset under the reset identity with the audit intent failing: the stop stays ON (database level; the
     in-memory order is `test_reset_writes_the_audit_intent_before_it_touches_the_switch`).
  9. Stop under the runtime identity with the audit tables refusing writes: the stop is ON all the same.
 10. The new migration and its `GRANTS` rows arrive together: `check_grants(real files) == []`
     (tests/test_k2_migrations.py:31) and the manifest pins are bumped
     (tests/test_migration_numbers_guards.py:363, tests/test_p2_postgres.py:290).
 11. `migrate()` run again takes back anything granted by hand to the reset identity, and refuses a reset
     role that is a superuser, owns a relation or can CREATE in the schema (`effective_problems`).
 12. A missing stop row still reads as ON (postgres.py:444-451) in the new shape.
"""

from __future__ import annotations

import inspect
import re
import uuid
from dataclasses import fields

import pytest

from hadavin_sdk.audit.protocol import AuditUnavailable
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.limits import Limits
from hadavin_sdk.store import migrate as mig
from tests.contracts.kinds.store_postgres import pg_schema

PRIVILEGES = ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE")
STOP_TABLE = "kill_switch"
AUDIT_LOG = ("audit_entries", "audit_checkpoints")


def _split(privileges: str) -> set[str]:
    return {p.strip() for p in privileges.split(",") if p.strip()}


# How `migrate()` turns one Grant into the table-level privileges of each identity (migrate.py:347-359).
HOLDS = {
    "runtime": lambda g: _split(g.runtime),
    "portal": lambda g: {"SELECT"} if g.portal else set(),
    "purge": lambda g: _split(g.purge),
}
ROLES = tuple(HOLDS)

# The reviewed list of EVERY write privilege (anything but SELECT), written by hand from main on 2026-11-20.
# It is a second copy on purpose: `GRANTS` must match it, so no grant gets wider without a change here.
WRITES: dict[str, dict[str, set[str]]] = {
    "runtime": {
        "runs": {"INSERT", "UPDATE"},
        "plans": {"INSERT", "UPDATE"},
        "gate_decisions": {"INSERT"},
        "approval_requests": {"INSERT", "UPDATE"},
        "approval_decisions": {"INSERT"},
        "dead_letters": {"INSERT"},
        "spend": {"INSERT", "UPDATE"},
        "spend_month": {"INSERT", "UPDATE"},
        "spend_reservations": {"INSERT", "UPDATE"},
        "kill_switch": {"INSERT", "UPDATE"},
        "tick_state": {"INSERT", "UPDATE"},
        "audit_entries": {"INSERT"},
        "audit_checkpoints": {"INSERT"},
        "audit_outbox": {"INSERT", "DELETE"},
        "tool_calls": {"INSERT"},
        "redaction_maps": {"INSERT", "UPDATE"},
    },
    "portal": {},
    # spend_reservations: migration 0007 (F-store) lets the purge role delete CLOSED reservations only (purge_cols)
    "purge": {
        "tool_calls": {"DELETE"},
        "redaction_maps": {"DELETE"},
        "spend_reservations": {"DELETE"},
    },
}


def _tables() -> list[str]:
    return [name for name, grant in mig.GRANTS.items() if grant.kind != "sequence"]


def _matrix() -> dict[tuple[str, str, str], bool]:
    """(role, table, privilege) -> granted, for every table and view in `GRANTS`."""
    return {
        (role, table, privilege): privilege in HOLDS[role](mig.GRANTS[table])
        for role in ROLES
        for table in _tables()
        for privilege in PRIVILEGES
    }


def _holders(table: str, *privileges: str) -> set[str]:
    return {r for (r, t, p), yes in _matrix().items() if yes and t == table and p in privileges}


# --- (a) pure Python ---------------------------------------------------------------------------------


def test_the_identities_are_the_ones_this_file_knows():
    """A new role keyword or Grant field is a new identity: its denials must be written here first."""
    keywords = {p for p in inspect.signature(mig.migrate).parameters if p.endswith("_role")}
    assert keywords == {f"{role}_role" for role in ROLES}
    assert {f.name for f in fields(mig.Grant)} == {
        "kind",
        "runtime",
        "portal",
        "purge",
        "purge_cols",
    }


def test_the_matrix_covers_every_role_table_and_privilege():
    matrix = _matrix()
    assert len(matrix) == len(ROLES) * len(_tables()) * len(PRIVILEGES)
    assert (
        len(_tables()) >= 15
    )  # main has 15 tables; a shrinking map would make the tests below vacuous
    assert sum(matrix.values()) > 0
    assert sum(not held for held in matrix.values()) > sum(matrix.values())  # mostly refusals


def test_every_write_privilege_is_on_the_reviewed_list():
    actual = {role: {} for role in ROLES}
    for (role, table, privilege), held in _matrix().items():
        if held and privilege != "SELECT":
            actual[role].setdefault(table, set()).add(privilege)
    assert actual == WRITES


@pytest.mark.parametrize("role", ROLES)
def test_no_role_may_truncate_any_table(role):
    assert [
        t
        for t in _tables()
        if (role, t, "TRUNCATE") in _matrix() and _matrix()[role, t, "TRUNCATE"]
    ] == []


def test_no_grant_uses_a_wildcard_or_a_privilege_outside_the_plain_ones():
    name = re.compile(r"[a-z_][a-z0-9_]*")
    for relation, grant in mig.GRANTS.items():
        assert name.fullmatch(relation), relation
        allowed = {"USAGE", "SELECT"} if grant.kind == "sequence" else set(PRIVILEGES[:4])
        for text in (grant.runtime, grant.purge):
            tokens = [p.strip() for p in text.split(",")] if text else []
            assert all(tokens), (relation, text)  # no empty item
            assert len(tokens) == len(set(tokens)), (relation, text)
            assert set(tokens) <= allowed, (
                relation,
                text,
            )  # so no ALL, no *, no TRUNCATE, no TRIGGER
        assert all(name.fullmatch(col) for col in grant.purge_cols), relation
    assert (
        mig._TABLE_PRIVS[:5] == PRIVILEGES
    )  # the migrate-time check looks at the same five and more


def test_only_the_runtime_role_holds_anything_on_the_stop_table():
    held = {role: {p for p in PRIVILEGES if _matrix()[role, STOP_TABLE, p]} for role in ROLES}
    assert held == {"runtime": {"SELECT", "INSERT", "UPDATE"}, "portal": set(), "purge": set()}
    assert _holders(STOP_TABLE, "DELETE", "TRUNCATE") == set()  # nobody can remove the row


@pytest.mark.parametrize("table", AUDIT_LOG)
def test_nobody_may_change_or_remove_an_audit_row(table):
    assert _holders(table, "UPDATE", "DELETE", "TRUNCATE") == set()
    assert _holders(table, "INSERT") == {"runtime"}
    assert _holders(table, "SELECT") == {"runtime", "portal"}


def test_delete_is_held_only_on_the_outbox_and_the_purged_evidence():
    deletes = {(r, t) for (r, t, p), held in _matrix().items() if held and p == "DELETE"}
    assert deletes == {
        ("runtime", "audit_outbox"),
        ("purge", "tool_calls"),
        ("purge", "redaction_maps"),
        ("purge", "spend_reservations"),
    }


def test_the_portal_role_writes_nothing_and_reads_no_secret_or_control_table():
    assert all(HOLDS["portal"](g) <= {"SELECT"} for g in mig.GRANTS.values())
    never = {STOP_TABLE, "redaction_maps", "tool_calls", "audit_outbox", "tick_state", "spend"}
    assert never <= set(_tables())
    assert {t for t in never if _holders(t, *PRIVILEGES) & {"portal"}} == set()


def test_the_purge_role_holds_delete_only_and_no_whole_table_read():
    for table in _tables():
        assert HOLDS["purge"](mig.GRANTS[table]) <= {"DELETE"}, table
    # column reads exist only to find the rows to delete or the run they belong to, never on other tables
    assert {t for t in _tables() if mig.GRANTS[t].purge_cols} == {
        "runs",
        "tool_calls",
        "redaction_maps",
        "spend_reservations",
    }


def test_no_role_but_the_runtime_role_may_use_a_sequence():
    for relation, grant in mig.GRANTS.items():
        if grant.kind == "sequence":
            assert _split(grant.runtime) == {"USAGE"}, relation  # nextval only: no setval (UPDATE)
            assert not grant.portal and not grant.purge and not grant.purge_cols, relation


def test_a_grant_row_without_its_migration_stops_migrate_before_it_connects(monkeypatch):
    monkeypatch.setitem(mig.GRANTS, "relation_no_migration_creates", mig.Grant("table", "SELECT"))

    def never(*args, **kwargs):
        raise AssertionError("migrate() connected although the grant map is inconsistent")

    monkeypatch.setattr(mig, "connect", never)
    assert any(
        "relation_no_migration_creates, which no migration creates" in problem
        for problem in mig.check_grants(mig._migration_files())
    )
    with pytest.raises(ConfigError, match="which no migration creates"):
        mig.migrate("host=unused.invalid")


def test_a_migration_without_its_grant_row_stops_migrate_before_it_connects(monkeypatch):
    monkeypatch.delitem(mig.GRANTS, STOP_TABLE)

    def never(*args, **kwargs):
        raise AssertionError("migrate() connected although the grant map is inconsistent")

    monkeypatch.setattr(mig, "connect", never)
    with pytest.raises(ConfigError, match=f"{STOP_TABLE} .table. is created by a migration"):
        mig.migrate("host=unused.invalid")


# --- stop and reset order (no database; true today, must stay true through step B) -----------------


class _Recorder:
    """A store and an audit sink in one: records the order of the calls `Limits` makes."""

    def __init__(self, fail: str | None = None):
        self.calls: list[str] = []
        self._fail = fail

    def _note(self, call: str) -> None:
        self.calls.append(call)
        if self._fail == call.split(":")[0]:
            raise AuditUnavailable("audit store down")

    def set_kill_switch(self, ks) -> None:
        self.calls.append(f"switch:{'on' if ks.on else 'off'}:{ks.by}")

    def write_intent(self, event) -> str:
        self._note(f"intent:{event.operation}:{event.result}:{event.principal}")
        return "key"

    def write_outcome(self, event) -> None:
        self._note(f"outcome:{event.operation}:{event.result}:{event.principal}")


def test_stop_switches_first_and_does_not_wait_for_the_audit_write():
    both = _Recorder()
    Limits(both, both, None).stop(by="user:a")
    assert both.calls == ["switch:on:user:a", "outcome:stop:on:user:a"]
    assert not any(
        call.startswith("intent") for call in both.calls
    )  # an intent can raise; stop must not


def test_reset_writes_the_audit_intent_before_it_touches_the_switch():
    both = _Recorder()
    Limits(both, both, None).reset(by="user:a")
    assert both.calls == ["intent:reset:off:user:a", "switch:off:user:a"]


def test_reset_leaves_the_switch_alone_when_the_audit_intent_fails():
    both = _Recorder(fail="intent")
    with pytest.raises(AuditUnavailable):
        Limits(both, both, None).reset(by="user:a")
    assert both.calls == ["intent:reset:off:user:a"]  # no switch call at all


# --- (b) PostgreSQL ----------------------------------------------------------------------------------


@pytest.fixture
def identities():
    """(owner DSN, {role: login role name}): a migrated schema, one fresh login role per identity with the
    grants applied in ONE migrate() call, and a `stranger` role that was never granted anything."""
    import psycopg
    from psycopg import sql

    for dsn in pg_schema():
        names = {role: f"{role[:2]}_{uuid.uuid4().hex[:10]}" for role in (*ROLES, "stranger")}
        with psycopg.connect(dsn, autocommit=True) as db:
            for name in names.values():
                db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(name)))
        try:
            mig.migrate(dsn, **{f"{role}_role": names[role] for role in ROLES})
            yield dsn, names
        finally:
            with psycopg.connect(dsn, autocommit=True) as db:
                for name in names.values():
                    db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(name)))
                    db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(name)))


def _as(dsn: str, role_name: str):
    import psycopg
    from psycopg.conninfo import make_conninfo

    db = psycopg.connect(make_conninfo(dsn, user=role_name))
    assert db.execute("SELECT current_user").fetchone()[0] == role_name
    db.rollback()
    return db


def _catalog(dsn: str) -> tuple[dict[str, str], list[str]]:
    """({table or view: its first column}, [sequences]) of the schema, from the catalog: `schema_migrations`
    and anything a migration made outside `GRANTS` are included."""
    import psycopg

    q = (
        "SELECT c.relname, c.relkind, (SELECT a.attname FROM pg_attribute a WHERE a.attrelid = c.oid "
        "AND a.attnum > 0 AND NOT a.attisdropped ORDER BY a.attnum LIMIT 1) FROM pg_class c "
        "JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname = current_schema() AND c.relkind IN ('r','p','v','m','f','S')"
    )
    with psycopg.connect(dsn, autocommit=True) as db:
        rows = db.execute(q).fetchall()
    return (
        {name: column for name, kind, column in rows if kind != "S"},
        [name for name, kind, _ in rows if kind == "S"],
    )


def _schema(dsn: str) -> str:
    import psycopg

    with psycopg.connect(dsn, autocommit=True) as db:
        return db.execute("SELECT current_schema()").fetchone()[0]


def _statements(schema: str, table: str, column: str) -> dict:
    """Schema-qualified, so a role with no right on the schema is refused ("permission denied for schema")
    instead of not finding the table through its search path."""
    from psycopg import sql

    t, c = sql.Identifier(schema, table), sql.Identifier(column)
    return {
        "SELECT": sql.SQL("SELECT * FROM {}").format(t),
        "INSERT": sql.SQL("INSERT INTO {} DEFAULT VALUES").format(t),
        "UPDATE": sql.SQL("UPDATE {} SET {} = DEFAULT").format(t, c),
        "DELETE": sql.SQL("DELETE FROM {}").format(t),
        "TRUNCATE": sql.SQL("TRUNCATE {}").format(t),
    }


def _expected(role: str, relation: str) -> set[str]:
    grant = mig.GRANTS.get(relation)
    return HOLDS[role](grant) if (grant and role in HOLDS) else set()


@pytest.mark.parametrize("role", [*ROLES, "stranger"])
def test_pg_each_role_is_refused_what_the_map_does_not_give(identities, role):
    """One real statement per cell, connected AS the role. Every statement is rolled back. A cell the map
    gives must get past the privilege check (it may fail later on a constraint or a trigger: not our subject),
    which also proves a refusal is about the table and not about a missing right on the schema."""
    import psycopg

    dsn, names = identities
    tables, _ = _catalog(dsn)
    schema = _schema(dsn)
    assert set(_tables()) <= set(tables) and "schema_migrations" in tables
    wrong, refused, passed = [], 0, 0
    with _as(dsn, names[role]) as db:
        for table, column in sorted(tables.items()):
            for privilege, statement in _statements(schema, table, column).items():
                try:
                    db.execute(statement)
                    denied = False
                except psycopg.errors.InsufficientPrivilege:
                    denied = True
                except psycopg.Error:
                    denied = False  # past the privilege check; stopped by a constraint or a trigger
                finally:
                    db.rollback()
                if denied == (privilege in _expected(role, table)):
                    wrong.append(
                        f"{role} {privilege} {table}: {'refused' if denied else 'allowed'}"
                    )
                refused, passed = refused + denied, passed + (not denied)
    assert wrong == []
    assert refused + passed == len(tables) * len(PRIVILEGES)
    assert refused >= len(tables)  # TRUNCATE at least, on every table
    if role in ("runtime", "portal"):
        assert passed > 0
    if role == "stranger":
        assert passed == 0


def test_pg_the_catalog_agrees_with_the_matrix_for_every_relation_of_the_schema(identities):
    """`has_table_privilege` (direct, inherited and PUBLIC grants) for the five privileges plus REFERENCES and
    TRIGGER, on every relation of the schema, with the three roles granted together."""
    import psycopg

    dsn, names = identities
    tables, sequences = _catalog(dsn)
    wrong = []
    with psycopg.connect(dsn, autocommit=True) as db:
        for role, name in names.items():
            for table in tables:
                held = {
                    p
                    for p in mig._TABLE_PRIVS
                    if db.execute(
                        "SELECT has_table_privilege(%s, %s, %s)", (name, table, p)
                    ).fetchone()[0]
                }
                if held != _expected(role, table):
                    wrong.append(f"{role} on {table}: {sorted(held)}")
            for sequence in sequences:
                held = {
                    p
                    for p in ("USAGE", "SELECT", "UPDATE")
                    if db.execute(
                        "SELECT has_sequence_privilege(%s, %s, %s)", (name, sequence, p)
                    ).fetchone()[0]
                }
                if held != (_expected(role, sequence) if role == "runtime" else set()):
                    wrong.append(f"{role} on sequence {sequence}: {sorted(held)}")
        schema = db.execute("SELECT current_schema()").fetchone()[0]
        q = "SELECT has_schema_privilege(%s, %s, %s)"
        assert not db.execute(q, (names["stranger"], schema, "USAGE")).fetchone()[0]
        for role in ROLES:
            assert db.execute(q, (names[role], schema, "USAGE")).fetchone()[0], role
            assert not db.execute(q, (names[role], schema, "CREATE")).fetchone()[0], role
    assert wrong == []


@pytest.mark.parametrize("role", ["portal", "purge", "stranger"])
def test_pg_only_the_runtime_role_may_draw_from_a_sequence(identities, role):
    import psycopg

    dsn, names = identities
    _, sequences = _catalog(dsn)
    schema = _schema(dsn)
    assert sequences
    with _as(dsn, names[role]) as db:
        for sequence in sequences:
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                db.execute("SELECT nextval(%s::regclass)", (f"{schema}.{sequence}",))
            db.rollback()


@pytest.mark.parametrize("role", ["portal", "purge"])  # the stranger: see the matrix test above
def test_pg_no_role_but_the_runtime_role_can_read_or_write_the_stop_state(identities, role):
    import psycopg

    dsn, names = identities
    with _as(dsn, names[role]) as db:
        for statement in (
            'SELECT "on" FROM kill_switch',
            'UPDATE kill_switch SET "on" = false',
            'INSERT INTO kill_switch (id, schema_version, "on", ts) VALUES (1, 1, false, now())',
            "DELETE FROM kill_switch",
            "TRUNCATE kill_switch",
        ):
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                db.execute(statement)
            db.rollback()
    assert _stop_is_on(dsn) is False  # the seeded row, untouched


def _stop_is_on(dsn: str) -> bool:
    import psycopg

    with psycopg.connect(dsn, autocommit=True) as db:
        return db.execute('SELECT "on" FROM kill_switch WHERE id = 1').fetchone()[0]


def test_pg_the_runtime_role_can_switch_the_stop_on(identities):
    """The emergency stop works with the runtime identity alone. Must stay true after step B."""
    dsn, names = identities
    assert _stop_is_on(dsn) is False
    with _as(dsn, names["runtime"]) as db:
        db.execute('UPDATE kill_switch SET "on" = true, "by" = %s, ts = now() WHERE id = 1', ("t",))
        db.commit()
    assert _stop_is_on(dsn) is True


def test_pg_the_runtime_role_cannot_remove_the_stop_row(identities):
    """A missing row reads as ON (fail closed), but a role that could delete it could also hide who stopped."""
    import psycopg

    dsn, names = identities
    with _as(dsn, names["runtime"]) as db:
        for statement in ("DELETE FROM kill_switch", "TRUNCATE kill_switch"):
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                db.execute(statement)
            db.rollback()


# --- STEP B target state: xfail until it is built ------------------------------------------------------
# strict=True: the day one of these passes, pytest reports it as a failure and the marker must go.
# raises=AssertionError: a renamed table or column is an ERROR here, not a silent "still expected to fail".

_STEP_B = "step B not built: stop and reset are one row the runtime role may UPDATE (migrate.py:55)"


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=_STEP_B)
def test_step_b_the_grant_map_gives_the_runtime_role_no_way_to_switch_the_stop_off():
    assert "UPDATE" not in HOLDS["runtime"](mig.GRANTS[STOP_TABLE])


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=_STEP_B)
def test_pg_step_b_the_runtime_role_cannot_switch_the_stop_off(identities):
    """With the stop ON, the runtime identity tries both ways the code has today (a plain UPDATE, and the
    upsert of postgres.py:453-457). Whatever the database answers, the stop must still be ON afterwards."""
    import psycopg

    dsn, names = identities
    with psycopg.connect(dsn, autocommit=True) as db:
        db.execute('UPDATE kill_switch SET "on" = true WHERE id = 1')
    for statement in (
        'UPDATE kill_switch SET "on" = false WHERE id = 1',
        (
            'INSERT INTO kill_switch (id, schema_version, "on", ts) VALUES (1, 1, false, now()) '
            'ON CONFLICT (id) DO UPDATE SET "on" = EXCLUDED."on"'
        ),
    ):
        with _as(dsn, names["runtime"]) as db:
            try:
                db.execute(statement)
                db.commit()
            except psycopg.Error:
                db.rollback()  # refused: what step B wants
        assert _stop_is_on(dsn) is True, statement
