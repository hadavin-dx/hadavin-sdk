"""`migrate()` against a real PostgreSQL: a late number, a newer database, the read-back after each file
(planted files), a hidden COMMIT, an older release's structure after the newest migrations.

Every test works in a fresh scratch schema of the test database (`HADAVIN_TEST_PG_DSN`). Planted files are made up.
A skip is a failed evidence run (with the DSN set none can happen: `tests/test_migration_rules.py` checks it); in CI `test_ci_has_its_inputs` fails when the database or `psql` is missing."""

from __future__ import annotations

import contextlib
import os
import re
import shutil
import subprocess
import threading
import time
import uuid
from pathlib import Path

import pytest

from hadavin_sdk.errors import ConfigError
from tests.fixtures import migration_role as helper
from tests.fixtures import runbook as rb
from tests.fixtures.dsn_skip import require_module
from tests.fixtures.migration_role import (
    PLAIN_ROLE,
    create_login_role,
    ensure_plain_role,
    login_dsn,
    set_login_password,
)

psycopg = require_module("psycopg")  # with the DSN set a missing driver FAILS (never a skip)
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from hadavin_sdk.store import migrate as mig
from hadavin_sdk.store.migration_numbers import MigrationNumberError
from tests.fixtures.released_stub import made_up_files_are_not_released

DSN = os.environ.get("HADAVIN_TEST_PG_DSN")
needs_pg = pytest.mark.skipif(
    not DSN, reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)"
)
# The newest migration of the previous release. No tag or release exists yet (checked 2026-11-07: `git tag` is empty,
# the GitHub releases and tags lists are empty, CHANGELOG.md says "Unreleased"), so the last
# migration on main is the released base: 0005_evidence (on main since ce70eb5, 2026-11-04). The person who cuts the first release moves this
# constant when the first tag exists.
PREVIOUS_RELEASE_LAST = "0005_evidence"
# Nothing in the real folder follows it today, so the test below also plants a newer file of its own (it is never empty).
PLANTED_NEXT = "0006_next.sql"
REAL = [p.stem for p in mig._migration_files()]


def missing_ci_inputs(environ, which) -> list[str]:
    """Names of the inputs a CI run needs and does not have; [] outside CI."""
    if not environ.get("CI"):
        return []
    missing = []
    if not environ.get("HADAVIN_TEST_PG_DSN"):
        missing.append("HADAVIN_TEST_PG_DSN")
    if which("psql") is None:
        missing.append("psql")
    return missing


def test_ci_has_its_inputs():
    assert missing_ci_inputs(os.environ, shutil.which) == [], "CI must have a database and psql"


def test_the_ci_rule_itself():
    never = lambda _name: None
    found = lambda name: "/usr/bin/" + name
    assert missing_ci_inputs({"CI": "true"}, found) == ["HADAVIN_TEST_PG_DSN"]
    assert missing_ci_inputs({"CI": "true", "HADAVIN_TEST_PG_DSN": "x"}, never) == ["psql"]
    assert missing_ci_inputs({"CI": "true", "HADAVIN_TEST_PG_DSN": "x"}, found) == []
    assert missing_ci_inputs({}, never) == []


@pytest.fixture
def scratch():
    """(dsn scoped to a fresh empty schema, schema name); the schema is dropped afterwards."""
    if not DSN:
        pytest.skip("HADAVIN_TEST_PG_DSN not set")
    schema = f"hadavin_test_{uuid.uuid4().hex[:12]}"
    with psycopg.connect(DSN, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    try:
        yield make_conninfo(DSN, options=f"-c search_path={schema}"), schema
    finally:
        with psycopg.connect(DSN, autocommit=True) as db:
            db.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def _ledger(dsn) -> list[str] | None:
    with psycopg.connect(dsn, autocommit=True) as db:
        if db.execute("SELECT to_regclass('schema_migrations')").fetchone()[0] is None:
            return None
        return [r[0] for r in db.execute("SELECT version FROM schema_migrations ORDER BY 1")]


def _dynamic(*statements: str) -> str:
    """A migration file whose statements run inside a function body (`EXECUTE`): the text rules read only the start of a
    statement, so this is what a file does to reach the read-back with statements the text rules refuse."""
    runs = " ".join(f"EXECUTE '{st.replace(chr(39), chr(39) * 2)}';" for st in statements)
    return (
        "CREATE OR REPLACE FUNCTION hadavin_test_dyn_runner() RETURNS void LANGUAGE plpgsql AS $$ BEGIN "
        f"{runs} END $$;\nSELECT hadavin_test_dyn_runner();\n"
    )


def _who(role: str) -> str:
    """How a line of the refusal names a grantee: PUBLIC is written `everyone (PUBLIC)`."""
    return "everyone (PUBLIC)" if role == "PUBLIC" else role


def _kept_nothing(text) -> bool:
    """The refusal says the run kept nothing: at step 2 "Nothing was changed. No file ran.", later "The whole run is
    rolled back"."""
    text = str(text)
    return "Nothing was changed." in text or "The whole run is rolled back" in text


def _give_create_then(schema: str, other: str, statement: str) -> str:
    """A migration file that, inside a function body, gives `other` CREATE on the schema and then runs `statement`
    (a hand-over needs the new owner to hold CREATE there). The words CREATE ON SCHEMA are split because the text
    rule reads a function body too."""
    return (
        "CREATE OR REPLACE FUNCTION hadavin_test_hand() RETURNS void LANGUAGE plpgsql AS $$ BEGIN "
        f"EXECUTE 'GRANT CRE' || 'ATE ON SCHEMA {schema} TO {other}'; "
        f"EXECUTE '{statement}'; END $$;\nSELECT hadavin_test_hand();\n"
    )


def _with_files(monkeypatch, tmp_path: Path, planted: dict[str, str]):
    """`migrate()` sees the real files plus the planted ones."""
    paths = []
    for name, text in planted.items():
        p = tmp_path / name
        p.write_text(text, encoding="utf-8")
        paths.append(p)
    files = mig._migration_files() + paths
    monkeypatch.setattr(mig, "_migration_files", lambda: files)


def _apply_by_hand(dsn, stems):
    """Apply the files by hand as the same plain role `migrate()` runs as (`mig.connect`), so it owns what they make."""
    with mig.connect(dsn) as db:
        db.execute(
            "CREATE TABLE schema_migrations (version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
        )
        for stem in stems:
            db.execute((mig.MIGRATIONS / f"{stem}.sql").read_text(encoding="utf-8"))
            db.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (stem,))


@needs_pg
def test_late_number_is_refused(scratch):
    """FAIL-BEFORE 1: 0001-0003 and 0005 are applied, 0004 is new for this database: refused, 0004 does not run."""
    dsn, _ = scratch
    _apply_by_hand(dsn, [s for s in REAL if s != "0004_audit_checkpoint_meta"])
    with pytest.raises(ConfigError, match="0004") as e:
        mig.migrate(dsn)
    assert type(e.value) is MigrationNumberError
    assert "0004_audit_checkpoint_meta" not in _ledger(dsn)


@needs_pg
def test_newer_database_message(scratch):
    """FAIL-BEFORE 6: the ledger holds a name above every file: this database is newer than the release."""
    dsn, _ = scratch
    mig.migrate(dsn)
    with psycopg.connect(dsn, autocommit=True) as db:
        db.execute("INSERT INTO schema_migrations (version) VALUES ('0007_z')")
    with pytest.raises(ConfigError) as e:
        mig.migrate(dsn)
    msg = str(e.value)
    assert "newer than this release" in msg
    assert "drop what it made" not in msg
    assert "rename the ledger row by hand" not in msg


@needs_pg
def test_a_normal_run_applies_every_file_once_and_is_repeatable(scratch):
    dsn, _ = scratch
    assert mig.migrate(dsn) == REAL
    assert mig.migrate(dsn) == []
    assert _ledger(dsn) == REAL


# --- what a file leaves changed is found by the read-back and the whole run is rolled back ---------------------

_FLIP = (
    "CREATE OR REPLACE FUNCTION hadavin_test_flip(item TEXT, val TEXT) RETURNS void LANGUAGE plpgsql AS $$\n"
    "BEGIN PERFORM set_config(item, val, true); END $$;\n"
)
PLANTS = {
    "drop_trigger": (
        "DROP TRIGGER audit_entries_no_truncate ON audit_entries;\n",
        "audit_entries_no_truncate",
    ),
    "disable_trigger": (
        "ALTER TABLE audit_entries DISABLE TRIGGER audit_entries_no_truncate;\n",
        "audit_entries_no_truncate",
    ),
    "replica_trigger": (
        "ALTER TABLE audit_entries ENABLE REPLICA TRIGGER audit_entries_no_truncate;\n",
        "audit_entries_no_truncate",
    ),
    "trigger_always": (
        "ALTER TABLE audit_entries ENABLE ALWAYS TRIGGER audit_entries_no_truncate;\n",
        "audit_entries_no_truncate changed: enabled state",
    ),
    "trigger_definition": (
        (
            "CREATE OR REPLACE TRIGGER audit_entries_no_truncate AFTER TRUNCATE ON audit_entries\n"
            "FOR EACH STATEMENT EXECUTE FUNCTION hadavin_audit_append_only();\n"
        ),
        "audit_entries_no_truncate changed: definition",
    ),
    "function_body": (
        (
            "CREATE OR REPLACE FUNCTION hadavin_audit_append_only() RETURNS trigger LANGUAGE plpgsql AS\n"
            "$$ BEGIN RETURN NULL; END $$;\n"
        ),
        "audit_entries_no_truncate changed: function text",
    ),
    "function_security_mode": (
        "ALTER FUNCTION hadavin_audit_append_only() SECURITY DEFINER;\n",
        "audit_entries_no_truncate changed: function security mode",
    ),
    "function_settings": (
        "ALTER FUNCTION hadavin_audit_append_only() SET work_mem = '1MB';\n",
        "audit_entries_no_truncate changed: function settings",
    ),
    "table_renamed": (
        "ALTER TABLE audit_entries RENAME TO audit_entries_moved;\n",
        "its table was renamed from audit_entries to audit_entries_moved",
    ),
    "replication_role": (
        _FLIP + "SELECT hadavin_test_flip('session_replication_role', 'replica');\n",
        "session_replication_role",
    ),
    "search_path": (_FLIP + "SELECT hadavin_test_flip('search_path', 'public');\n", "search_path"),
    "scs": (
        _FLIP + "SELECT hadavin_test_flip('standard_conforming_strings', 'off');\n",
        "standard_conforming_strings",
    ),
    "backslash_quote": (
        _FLIP + "SELECT hadavin_test_flip('backslash_quote', 'on');\n",
        "backslash_quote",
    ),
    "encoding": (
        _FLIP + "SELECT hadavin_test_flip('client_encoding', 'LATIN1');\n",
        "client_encoding",
    ),
}


@contextlib.contextmanager
def _plain_role_may_set(parameter: str | None):
    """Only a superuser may set some server parameters (session_replication_role); the plain role `migrate()` runs as
    gets exactly that one right for the length of a plant test (PostgreSQL 15 and later)."""
    if parameter is None:
        yield
        return
    role = sql.Identifier(PLAIN_ROLE)
    param = sql.SQL(parameter)
    with psycopg.connect(DSN, autocommit=True) as db:
        ensure_plain_role(db)
        db.execute(sql.SQL("GRANT SET ON PARAMETER {} TO {}").format(param, role))
    try:
        yield
    finally:
        with psycopg.connect(DSN, autocommit=True) as db:
            db.execute(sql.SQL("REVOKE SET ON PARAMETER {} FROM {}").format(param, role))


@needs_pg
@pytest.mark.parametrize("plant", sorted(PLANTS))
def test_h11_the_read_back_refuses_a_planted_file(scratch, monkeypatch, tmp_path, plant):
    dsn, _ = scratch
    mig.migrate(dsn)  # call 1: the real folder
    body, item = PLANTS[plant]
    with _plain_role_may_set("session_replication_role" if plant == "replication_role" else None):
        if plant == "replication_role":
            # `migrate` refuses a role with a parameter grant before any file runs (see
            # test_a_parameter_grant_is_refused_by_a_real_server); here that first refusal is switched off to prove the
            # read-back is a second line that finds the changed setting too.
            monkeypatch.setattr(mig, "_PARAMETER_TABLE_SQL", "SELECT false")
        _run_plant(dsn, monkeypatch, tmp_path, body, item)


def _run_plant(dsn, monkeypatch, tmp_path, body, item):
    _with_files(monkeypatch, tmp_path, {"0006_plant.sql": body})
    with pytest.raises(ConfigError) as e:  # call 2: real folder plus the planted file
        mig.migrate(dsn)
    assert "0006_plant.sql" in str(e.value) and item in str(e.value), str(e.value)
    assert not str(e.value).startswith("migrations are inconsistent"), (
        "it is the read-back, not the scan"
    )
    if "audit_entries" in item or "trigger" in item or "table" in item:
        assert "changed a trigger" in str(e.value) and "session" not in str(e.value), str(e.value)
    assert _ledger(dsn) == REAL, "the ledger holds the five real stems and no planted stem"
    with psycopg.connect(
        dsn, autocommit=True
    ) as db:  # the trigger the plant touched is still in force
        row = db.execute(
            "SELECT tgenabled FROM pg_trigger WHERE tgname = 'audit_entries_no_truncate'"
        ).fetchone()
    assert row == ("O",)


@needs_pg
def test_h11_a_function_owner_change_is_refused(scratch, monkeypatch, tmp_path):
    """The owner of the trigger function is read back: handing it to another role is a trigger change. The new owner
    needs CREATE on the schema, so the file gives it first (inside the function body; since P3a-2 the same right held
    BEFORE the run is refused at step 2). Killed by: mutant T7 (function owner not compared) of
    tests/migrate_mutants.py."""
    dsn, schema = scratch
    other = "hadavin_test_fo_" + uuid.uuid4().hex[:8]
    _create_roles(other)
    try:
        mig.migrate(dsn)
        _admin(
            sql.SQL("GRANT CREATE ON SCHEMA {} TO {} WITH GRANT OPTION").format(
                sql.Identifier(schema), sql.Identifier(PLAIN_ROLE)
            )
        )
        _let_the_plain_role_belong_to(other)
        body = _give_create_then(
            schema, other, f"ALTER FUNCTION hadavin_audit_append_only() OWNER TO {other}"
        )
        _with_files(monkeypatch, tmp_path, {"0006_owner.sql": body})
        with pytest.raises(
            ConfigError, match="audit_entries_no_truncate changed: function owner"
        ) as e:
            mig.migrate(dsn)
        assert "changed a trigger" in str(e.value) and _ledger(dsn) == REAL
    finally:
        _drop_roles(other)


@needs_pg
def test_h11_a_listed_trigger_change_passes_for_that_file_and_trigger_only(
    scratch, monkeypatch, tmp_path
):
    """The reviewed list (`migrations_trigger_changes.json`) is the only way to change a trigger. Here a fake list names
    the file and the trigger: the replaced definition is kept, and the same text under another file name is refused.
    Killed by: mutants T10 and T11 (wiring tests) and T13 (the list is not passed to the read-back)."""
    dsn, _ = scratch
    mig.migrate(dsn)
    body = PLANTS["trigger_definition"][0]
    real_files = mig._migration_files
    monkeypatch.setattr(
        mig,
        "_trigger_changes",
        lambda: frozenset(
            {mig.TriggerChange("0006_listed", None, "audit_entries", "audit_entries_no_truncate")}
        ),
    )
    _with_files(monkeypatch, tmp_path, {"0006_other.sql": body})
    with pytest.raises(ConfigError, match="changed a trigger"):
        mig.migrate(dsn)
    assert _ledger(dsn) == REAL
    monkeypatch.setattr(
        mig, "_migration_files", real_files
    )  # (not `monkeypatch.undo()`: it undoes the plain-role connect)
    _with_files(monkeypatch, tmp_path, {"0006_listed.sql": body})
    assert mig.migrate(dsn) == ["0006_listed"]
    with psycopg.connect(dsn, autocommit=True) as db:
        (definition,) = db.execute(
            "SELECT pg_get_triggerdef(oid) FROM pg_trigger WHERE tgname = 'audit_entries_no_truncate' "
            "AND tgrelid = 'audit_entries'::regclass"
        ).fetchone()
    assert "AFTER TRUNCATE" in definition


@needs_pg
def test_h11_a_role_switched_inside_a_file_is_refused(scratch, monkeypatch, tmp_path):
    dsn, _ = scratch
    role = "hadavin_test_r_" + uuid.uuid4().hex[:8]
    body = (
        "CREATE OR REPLACE FUNCTION hadavin_test_switch() RETURNS void LANGUAGE plpgsql AS $$\n"
        f"BEGIN EXECUTE 'SET LOCAL ROLE {role}'; END $$;\nSELECT hadavin_test_switch();\n"
    )
    with psycopg.connect(DSN, autocommit=True) as db:
        db.execute(sql.SQL("CREATE ROLE {}").format(sql.Identifier(role)))
    try:
        mig.migrate(dsn)
        with psycopg.connect(
            DSN, autocommit=True
        ) as db:  # a plain role the migration role may switch to
            db.execute(
                sql.SQL("GRANT {} TO {}").format(sql.Identifier(role), sql.Identifier(PLAIN_ROLE))
            )
        _with_files(monkeypatch, tmp_path, {"0006_role.sql": body})
        with pytest.raises(ConfigError) as e:
            mig.migrate(dsn)
        assert "current_user" in str(e.value) and "0006_role.sql" in str(e.value)
        assert _ledger(dsn) == REAL
    finally:
        with psycopg.connect(DSN, autocommit=True) as db:
            db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


def _create_roles(*roles: str, login_password: str | None = None) -> None:
    with psycopg.connect(DSN, autocommit=True) as db:
        for role in roles:
            if login_password and role == roles[0]:
                create_login_role(db, role, login_password)
            else:
                db.execute(sql.SQL("CREATE ROLE {}").format(sql.Identifier(role)))


def _let_the_plain_role_grant(role: str) -> None:
    """The plain role `migrate()` runs as holds `role` with the ADMIN option (before migrate starts, so it is part of the
    baseline): without it a `GRANT role TO x` in a planted function would fail for lack of rights, not reach the read-back."""
    with psycopg.connect(DSN, autocommit=True) as db:
        ensure_plain_role(db)
        db.execute(
            sql.SQL("GRANT {} TO {} WITH ADMIN OPTION").format(
                sql.Identifier(role), sql.Identifier(PLAIN_ROLE)
            )
        )


def _let_the_plain_role_belong_to(role: str) -> None:
    """The migration user is a member of `role` (so `role` is in the set of roles whose memberships `migrate` compares; a
    role that the migration user has nothing to do with is not)."""
    with psycopg.connect(DSN, autocommit=True) as db:
        ensure_plain_role(db)
        db.execute(
            sql.SQL("GRANT {} TO {}").format(sql.Identifier(role), sql.Identifier(PLAIN_ROLE))
        )


def _drop_roles(*roles: str) -> None:
    with psycopg.connect(DSN, autocommit=True) as db:
        for role in roles:
            db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
            db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


@needs_pg
@pytest.mark.parametrize("how", ["function_body", "function_body_with_admin_option"])
def test_h11_a_role_grant_hidden_in_a_function_body_is_refused(scratch, monkeypatch, tmp_path, how):
    """the statement rule reads `GRANT r TO s` only at the start of a statement; here it sits in a `$$` body
    and the file then calls the function. The read-back of `pg_auth_members` refuses it and nothing is kept.
    Killed by: mutant R1 (membership not compared) and mutant R2 (membership not read after the file)."""
    dsn, _ = scratch
    a, b = "hadavin_test_ga_" + uuid.uuid4().hex[:8], "hadavin_test_gb_" + uuid.uuid4().hex[:8]
    option = " WITH ADMIN OPTION" if how.endswith("admin_option") else ""
    body = (
        "CREATE OR REPLACE FUNCTION hadavin_test_grant() RETURNS void LANGUAGE plpgsql AS $$\n"
        f"BEGIN GRANT {a} TO {b}{option}; END $$;\nSELECT hadavin_test_grant();\n"
    )
    _create_roles(a, b)
    _let_the_plain_role_grant(a)
    _let_the_plain_role_belong_to(b)  # `b` is a role the migration user belongs to: it is compared
    try:
        mig.migrate(dsn)
        _with_files(monkeypatch, tmp_path, {"0006_grant.sql": body})
        with pytest.raises(ConfigError) as e:
            mig.migrate(dsn)
        msg = str(e.value)
        assert "0006_grant.sql" in msg and f"role {a} has a new member {b}" in msg, msg
        assert "a role membership changed while the file ran" in msg, msg
        assert not msg.startswith("migrations are inconsistent"), "the read-back, not the scan"
        assert _ledger(dsn) == REAL
        with psycopg.connect(DSN, autocommit=True) as db:
            assert db.execute("SELECT pg_has_role(%s, %s, 'MEMBER')", (b, a)).fetchone() == (False,)
    finally:
        _drop_roles(a, b)


@needs_pg
@pytest.mark.parametrize("granted_before_by", ["the_plain_role", "the_login_superuser"])
def test_h11_a_changed_grant_option_of_an_existing_membership_is_refused(
    scratch, monkeypatch, tmp_path, granted_before_by
):
    """The membership `a` -> `b` exists BEFORE migrate starts, without the admin option. A `$$` body then runs
    `GRANT a TO b WITH ADMIN OPTION` (the same membership, one more right) and the file calls it. The read-back compares
    every column of `pg_auth_members`, not only the two names, so it refuses and nothing is kept. With
    `the_plain_role` as the first grantor the same catalog row is changed in place; with `the_login_superuser` a second
    row (another grantor) is added. Killed by: mutant R4 (the other columns are not read)."""
    dsn, _ = scratch
    a, b = "hadavin_test_oa_" + uuid.uuid4().hex[:8], "hadavin_test_ob_" + uuid.uuid4().hex[:8]
    _create_roles(a, b)
    _let_the_plain_role_grant(a)
    _let_the_plain_role_belong_to(b)
    try:
        with psycopg.connect(DSN, autocommit=True) as db:
            if granted_before_by == "the_plain_role":
                db.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(PLAIN_ROLE)))
            db.execute(sql.SQL("GRANT {} TO {}").format(sql.Identifier(a), sql.Identifier(b)))
        body = (
            "CREATE OR REPLACE FUNCTION hadavin_test_grant() RETURNS void LANGUAGE plpgsql AS $$\n"
            f"BEGIN GRANT {a} TO {b} WITH ADMIN OPTION; END $$;\nSELECT hadavin_test_grant();\n"
        )
        mig.migrate(dsn)
        _with_files(monkeypatch, tmp_path, {"0006_option.sql": body})
        with pytest.raises(ConfigError) as e:
            mig.migrate(dsn)
        msg = str(e.value)
        assert "0006_option.sql" in msg and f"role {a}" in msg and b in msg, msg
        assert "with grant option" in msg, msg  # the changed column, in words
        assert "{" not in msg and "admin_option" not in msg, msg  # no raw JSON
        assert not msg.startswith("migrations are inconsistent"), "the read-back, not the scan"
        assert _ledger(dsn) == REAL
        with psycopg.connect(DSN, autocommit=True) as db:
            rows = db.execute(
                "SELECT admin_option FROM pg_auth_members WHERE roleid = %s::regrole AND member = %s::regrole",
                (a, b),
            ).fetchall()
        assert rows and not any(r[0] for r in rows), rows  # the whole run was rolled back
    finally:
        _drop_roles(a, b)


@needs_pg
def test_h11_a_grant_of_a_role_that_was_a_member_before_is_not_a_refusal(
    scratch, monkeypatch, tmp_path
):
    """The baseline is the membership at the start: a file that changes nothing about it passes."""
    dsn, _ = scratch
    a, b = "hadavin_test_ma_" + uuid.uuid4().hex[:8], "hadavin_test_mb_" + uuid.uuid4().hex[:8]
    _create_roles(a, b)
    _let_the_plain_role_belong_to(b)
    try:
        with psycopg.connect(DSN, autocommit=True) as db:
            db.execute(sql.SQL("GRANT {} TO {}").format(sql.Identifier(a), sql.Identifier(b)))
        _with_files(monkeypatch, tmp_path, {"0006_ok.sql": "SELECT 1;\n"})
        assert mig.migrate(dsn) == [*REAL, "0006_ok"]
    finally:
        _drop_roles(a, b)


@pytest.fixture
def owner_dsn(scratch):
    """(dsn, other role) for a LOGIN role that is NOT a superuser, owns what it creates in the scratch schema and may
    switch to `other` (a membership that exists BEFORE migrate starts, so it is part of the baseline)."""
    dsn, schema = scratch
    owner, other = (
        "hadavin_test_own_" + uuid.uuid4().hex[:8],
        "hadavin_test_oth_" + uuid.uuid4().hex[:8],
    )
    password = f"pw-{uuid.uuid4().hex}"
    _create_roles(owner, other, login_password=password)
    with psycopg.connect(DSN, autocommit=True) as db:
        db.execute(sql.SQL("GRANT {} TO {}").format(sql.Identifier(other), sql.Identifier(owner)))
        db.execute(
            sql.SQL("GRANT USAGE, CREATE ON SCHEMA {} TO {}").format(
                sql.Identifier(schema), sql.Identifier(owner)
            )
        )
    try:
        yield make_conninfo(dsn, user=owner, password=password), other
    finally:
        _drop_roles(owner, other)


@needs_pg
def test_migrate_as_a_login_role_that_is_not_a_superuser_runs_and_refuses_the_plants(
    owner_dsn, monkeypatch, tmp_path
):
    """the docs say run migrate with a role that is not a superuser; every other test connects as the superuser.
    Here the migration role is a plain LOGIN owner: the real files apply, a DISABLE TRIGGER and a SET LOCAL ROLE are
    refused with the same read-back messages as for a superuser, and a second run with the real files is clean.
    Killed by: mutant M61 (read-back removed from migrate()), as for the superuser plants this test repeats."""
    dsn, other = owner_dsn
    with psycopg.connect(dsn, autocommit=True) as db:
        assert db.execute("SELECT current_setting('is_superuser')").fetchone() == ("off",)
    assert mig.migrate(dsn) == REAL
    assert mig.migrate(dsn) == []
    plants = {
        "0006_dis.sql": (
            "ALTER TABLE audit_entries DISABLE TRIGGER audit_entries_no_truncate;\n",
            "audit_entries_no_truncate",
        ),
        "0006_role.sql": (
            (
                "CREATE OR REPLACE FUNCTION hadavin_test_switch() RETURNS void LANGUAGE plpgsql AS $$\n"
                f"BEGIN EXECUTE 'SET LOCAL ROLE {other}'; END $$;\nSELECT hadavin_test_switch();\n"
            ),
            "current_user",
        ),
    }
    for name, (body, item) in plants.items():
        _with_files(monkeypatch, tmp_path, {name: body})
        with pytest.raises(ConfigError) as e:
            mig.migrate(dsn)
        assert name in str(e.value) and item in str(e.value), str(e.value)
        assert not str(e.value).startswith("migrations are inconsistent")
        assert _ledger(dsn) == REAL
        monkeypatch.undo()  # the next plant is planted next to the real files only


@needs_pg
def test_h11_same_run_a_drop_in_the_first_run_leaves_no_ledger(scratch, monkeypatch, tmp_path):
    """ONE migrate() call on the real files plus a planted file: refused, and nothing of the run is kept."""
    dsn, _ = scratch
    _with_files(
        monkeypatch,
        tmp_path,
        {"0006_drop.sql": "DROP TRIGGER audit_entries_no_truncate ON audit_entries;\n"},
    )
    with pytest.raises(ConfigError) as e:
        mig.migrate(dsn)
    assert "0006_drop.sql" in str(e.value) and "audit_entries_no_truncate" in str(e.value)
    assert not _ledger(dsn), "the ledger does not exist or holds no row"


@needs_pg
def test_a_hidden_commit_is_found_by_the_transaction_backstop(scratch, monkeypatch, tmp_path):
    """The text rule refuses COMMIT; with that rule switched off in the test, the clock and id read-back still
    sees the new transaction after the file (the backstop for a COMMIT the text rules cannot see)."""
    dsn, _ = scratch
    monkeypatch.setattr(mig, "refused_statements", lambda text: [])
    _with_files(monkeypatch, tmp_path, {"0006_commit.sql": "SELECT 1;\nCOMMIT;\n"})
    with pytest.raises(ConfigError) as e:
        mig.migrate(dsn)
    msg = str(e.value)
    assert "0006_commit.sql" in msg and "transaction_timestamp" in msg and "txid_current" in msg, (
        msg
    )
    assert "0006_commit" not in (_ledger(dsn) or [])


@needs_pg
def test_a_session_that_reads_strings_the_old_way_is_refused_before_any_file(scratch):
    dsn, _ = scratch
    off = make_conninfo(dsn, options=dsn_options(dsn) + " -c standard_conforming_strings=off")
    with pytest.raises(ConfigError, match="standard_conforming_strings"):
        mig.migrate(off)
    assert not _ledger(dsn)


def dsn_options(dsn: str) -> str:
    from psycopg.conninfo import conninfo_to_dict

    return conninfo_to_dict(dsn).get("options", "")


@needs_pg
def test_triggers_of_another_schema_are_not_read(scratch, monkeypatch, tmp_path):
    """Case (xvi): a trigger in a schema other than the migration schema may change without a refusal."""
    dsn, _ = scratch
    other = "hadavin_test_o_" + uuid.uuid4().hex[:8]
    with psycopg.connect(DSN, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(other)))
        db.execute(sql.SQL("CREATE TABLE {}.t (x int)").format(sql.Identifier(other)))
        db.execute(
            sql.SQL(
                "CREATE FUNCTION {0}.f() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END $$"
            ).format(sql.Identifier(other))
        )
        db.execute(
            sql.SQL(
                "CREATE TRIGGER trg BEFORE INSERT ON {0}.t FOR EACH ROW EXECUTE FUNCTION {0}.f()"
            ).format(sql.Identifier(other))
        )
        ensure_plain_role(
            db
        )  # the plain role `migrate()` runs as may use and own the other schema's table
        db.execute(
            sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                sql.Identifier(other), sql.Identifier(PLAIN_ROLE)
            )
        )
        db.execute(
            sql.SQL("ALTER TABLE {}.t OWNER TO {}").format(
                sql.Identifier(other), sql.Identifier(PLAIN_ROLE)
            )
        )
    try:
        mig.migrate(dsn)
        body = f'ALTER TABLE "{other}".t DISABLE TRIGGER trg;\n'
        _with_files(monkeypatch, tmp_path, {"0006_other.sql": body})
        assert mig.migrate(dsn) == ["0006_other"]
    finally:
        with psycopg.connect(DSN, autocommit=True) as db:
            db.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(other)))


# --- the downgrade-read test: the previous release's structure is still readable after the newest migrations ----------


def _columns(dsn: str) -> dict[tuple[str, str], tuple[str, str]]:
    with psycopg.connect(dsn, autocommit=True) as db:
        rows = db.execute(
            "SELECT table_name, column_name, data_type, is_nullable FROM information_schema.columns "
            "WHERE table_schema = current_schema() ORDER BY 1, 2"
        ).fetchall()
    return {(t, c): (d, n) for t, c, d, n in rows}


def _old_and_new_columns(dsn, monkeypatch, tmp_path, planted_sql: str):
    """Build the schema of the previous release by hand, record its columns, then run `migrate()` with the real files
    that follow it plus one planted newer file. Returns (old columns, new columns)."""
    upto = REAL.index(PREVIOUS_RELEASE_LAST) + 1
    _apply_by_hand(dsn, REAL[:upto])
    old = _columns(dsn)
    assert old, "the previous release has tables"
    with psycopg.connect(dsn, autocommit=True) as db:
        db.execute("INSERT INTO audit_checkpoints (seq, hash, signature) VALUES (1, 'h', 's')")
    _with_files(monkeypatch, tmp_path, {PLANTED_NEXT: planted_sql})
    applied = mig.migrate(dsn)
    assert applied == [*REAL[upto:], PLANTED_NEXT[:-4]], (
        "the test must apply a newer file, or it proves nothing"
    )
    return old, _columns(dsn)


def _old_reader(dsn, old) -> None:
    """The old code's reads: the old column list on every old table."""
    with psycopg.connect(dsn, autocommit=True) as db:
        for table in sorted({t for t, _ in old}):
            cols = sql.SQL(", ").join(sql.Identifier(c) for t, c in sorted(old) if t == table)
            db.execute(
                sql.SQL("SELECT {} FROM {} LIMIT 1").format(cols, sql.Identifier(table))
            ).fetchall()
        assert db.execute("SELECT seq, hash, signature FROM audit_checkpoints").fetchall() == [
            (1, "h", "s")
        ]


def _problems(old, new):
    lost = sorted(set(old) - set(new))
    changed = sorted(k for k in old if k in new and old[k] != new[k] and k not in ACCEPTED_CHANGES)
    return lost, changed


@needs_pg
def test_the_previous_release_columns_survive_the_newest_migrations(scratch, monkeypatch, tmp_path):
    """Build the previous release's schema (files up to PREVIOUS_RELEASE_LAST), record every column, apply the files
    after it (the real ones, and one planted additive file, so the test is never empty): every old column is still
    there with the same type and nullability, and the old code's reads still run (a new column may be added; an old
    one may not go, change type or become NOT NULL without a named exception).

    Honest limit: today no real migration follows `PREVIOUS_RELEASE_LAST`, so this test compares the
    previous release's columns with themselves plus the one planted file. It is tautological for the real files until
    the first real migration after the release lands; the comparison itself is proven by
    `test_the_comparison_catches_a_dropped_or_retyped_old_column`."""
    dsn, _ = scratch
    old, new = _old_and_new_columns(
        dsn,
        monkeypatch,
        tmp_path,
        "ALTER TABLE audit_checkpoints ADD COLUMN hadavin_test_note TEXT;\n",
    )
    assert ("audit_checkpoints", "hadavin_test_note") in new, "the planted newer file ran"
    lost, changed = _problems(old, new)
    assert not lost, f"columns of the previous release are gone: {lost}"
    assert not changed, f"columns of the previous release changed type or nullability: {changed}"
    _old_reader(dsn, old)


@needs_pg
@pytest.mark.parametrize(
    "planted, lost_key, changed_key",
    [
        (
            "ALTER TABLE audit_checkpoints DROP COLUMN signature;\n",
            ("audit_checkpoints", "signature"),
            None,
        ),
        (
            "ALTER TABLE audit_checkpoints ALTER COLUMN signature TYPE BYTEA USING signature::bytea;\n",
            None,
            ("audit_checkpoints", "signature"),
        ),
    ],
)
def test_the_comparison_catches_a_dropped_or_retyped_old_column(
    scratch, monkeypatch, tmp_path, planted, lost_key, changed_key
):
    """The comparison above is a real check: a newer file that drops or retypes an old column is reported."""
    dsn, _ = scratch
    old, new = _old_and_new_columns(dsn, monkeypatch, tmp_path, planted)
    lost, changed = _problems(old, new)
    assert (lost_key in lost) if lost_key else (changed_key in changed), (lost, changed)


def test_the_constant_is_the_last_migration_on_main():
    """There is no release tag, so the last migration on main is the released base. A newer real file
    arriving in the folder does not move it; the person who cuts the first release does."""
    assert PREVIOUS_RELEASE_LAST == "0005_evidence"
    assert PREVIOUS_RELEASE_LAST in REAL


# A changed column of the previous release is accepted only by name, with the test that proves the change is safe.
ACCEPTED_CHANGES: dict[tuple[str, str], str] = {}


def test_an_accepted_change_names_a_real_test():
    import importlib

    for key, dotted in ACCEPTED_CHANGES.items():
        module_name, _, func = dotted.rpartition(".")
        target = getattr(importlib.import_module(module_name), func, None)
        assert callable(target) and func.startswith("test_"), (
            f"{key}: {dotted} is not a test function"
        )


# --- the runbook of CHANGELOG.md, RUN (cases (b) and (g)) ---------------------------------------------------------------
# Every statement below is cut out of the runbook text (tests/fixtures/runbook.py); the hand file goes through
# `psql -X -v ON_ERROR_STOP=1 -f`, as the runbook says. Then `migrate()` must accept the database.

FALSE_ROW = (
    "0006" + "_evidence"
)  # the name the older note gave; written in two parts so a search for it finds none
EVIDENCE = "0005_evidence"


def _psql(schema: str, tmp_path: Path, *steps: str):
    """Run the hand file made from `steps` with psql, return the finished process (never raises on a failed file)."""
    return _psql_text(tmp_path, rb.hand_file(schema, *steps))


def _psql_text(tmp_path: Path, text: str, env_extra: dict | None = None, stop_flag: bool = True):
    """Run `text` (a whole hand file) with the psql command of the runbook; never raises on a failed file."""
    assert shutil.which("psql"), "psql is needed for the runbook tests (HADAVIN_TEST_PG_DSN is set)"
    parts = conninfo_to_dict(DSN)
    env = {k: v for k, v in os.environ.items() if not k.startswith("PG")}
    for key, var in (
        ("host", "PGHOST"),
        ("port", "PGPORT"),
        ("user", "PGUSER"),
        ("dbname", "PGDATABASE"),
        ("password", "PGPASSWORD"),
    ):
        if parts.get(key):
            env[var] = str(parts[key])
    env.update(env_extra or {})
    (tmp_path / "hand.sql").write_text(text, encoding="utf-8")
    assert rb.PSQL_ARGS == [
        "psql",
        "-X",
        "-v",
        "ON_ERROR_STOP=1",
    ]  # the rule of the runbook, written out below
    run = {
        "cwd": tmp_path,
        "env": env,
        "capture_output": True,
        "text": True,
        "timeout": 60,
    }
    if stop_flag:
        return subprocess.run(
            ["/usr/bin/env", "psql", "-X", "-v", "ON_ERROR_STOP=1", "-f", "hand.sql"],
            check=False,
            **run,
        )
    # the person forgot `-v`: only the file's own first line stops psql
    return subprocess.run(
        ["/usr/bin/env", "psql", "-X", "-v", "ON_ERROR_STOP=0", "-f", "hand.sql"],
        check=False,
        **run,
    )


def _sql(dsn, text: str, params=None):
    with psycopg.connect(dsn, autocommit=True) as db:
        cur = db.execute(text, params)
        return cur.fetchall() if cur.description else None


def _as_migrator(dsn, text: str) -> None:
    """Run `text` as the plain migration role (`mig.connect`), so the objects it makes belong to that role."""
    with mig.connect(dsn) as db:
        db.execute(text)


def _has_error_column(dsn) -> bool:
    query = rb.span_in(rb.case("g"), "SELECT column_name FROM information_schema.columns")
    return bool(_sql(dsn, query))


def _insert_tool_call(dsn, call_id="c1", with_error=False):
    if with_error:
        stmt = (
            "INSERT INTO tool_calls (call_id, run_id, tool, inputs, output, output_sha256, created_at, error) "
            "VALUES (%s, 'r', 't', '{}', 'o', 'h', now(), TRUE)"
        )
    else:
        stmt = (
            "INSERT INTO tool_calls (call_id, run_id, tool, inputs, output, output_sha256, created_at) "
            "VALUES (%s, 'r', 't', '{}', 'o', 'h', now())"
        )
    _sql(dsn, stmt, (call_id,))


@needs_pg
def test_runbook_case_b_renames_the_old_notes_row_back_and_migrate_accepts_it(scratch, tmp_path):
    """A database that followed the older note (ledger row 0006 evidence): refused with a pointer to case (b); the
    hand file of case (b) (the UPDATE, its DO check, the evidence tables block) puts the row back; migrate accepts."""
    dsn, schema = scratch
    mig.migrate(dsn)
    _sql(dsn, "UPDATE schema_migrations SET version = %s WHERE version = %s", (FALSE_ROW, EVIDENCE))
    with pytest.raises(ConfigError) as e:
        mig.migrate(dsn)
    assert FALSE_ROW in str(e.value) and "Migration repair steps, case (b)" in str(e.value)
    assert _ledger(dsn) is not None and EVIDENCE not in _ledger(dsn)
    done = _psql(
        schema,
        tmp_path,
        rb.rename_step(FALSE_ROW, EVIDENCE),
        rb.do_check(EVIDENCE, FALSE_ROW),
        rb.evidence_block(),
    )
    assert done.returncode == 0, done.stderr
    assert _ledger(dsn) == REAL
    assert mig.migrate(dsn) == []


@needs_pg
def test_runbook_case_b_also_repairs_an_early_table_in_the_same_file(scratch, tmp_path):
    """Row 0006 AND a tool_calls without `error` (both of the old note's victims at once): the rename alone would
    accept the broken table for good; with the evidence block of case (g) in the file the column comes back."""
    dsn, schema = scratch
    mig.migrate(dsn)
    _insert_tool_call(dsn)
    _sql(dsn, "ALTER TABLE tool_calls DROP COLUMN error")
    _sql(dsn, "UPDATE schema_migrations SET version = %s WHERE version = %s", (FALSE_ROW, EVIDENCE))
    done = _psql(
        schema,
        tmp_path,
        rb.rename_step(FALSE_ROW, EVIDENCE),
        rb.do_check(EVIDENCE, FALSE_ROW),
        rb.evidence_block(),
    )
    assert done.returncode == 0, done.stderr
    assert _has_error_column(dsn)
    assert _ledger(dsn) == REAL
    assert mig.migrate(dsn) == []
    _insert_tool_call(dsn, "c2", with_error=True)  # the write the service makes
    assert _sql(dsn, "SELECT error FROM tool_calls WHERE call_id = 'c1'") == [(False,)]


@needs_pg
def test_runbook_case_b_keeps_nothing_when_an_evidence_table_is_missing(scratch, tmp_path):
    dsn, schema = scratch
    mig.migrate(dsn)
    _sql(dsn, "DROP TABLE redaction_maps")
    _sql(dsn, "UPDATE schema_migrations SET version = %s WHERE version = %s", (FALSE_ROW, EVIDENCE))
    done = _psql(
        schema,
        tmp_path,
        rb.rename_step(FALSE_ROW, EVIDENCE),
        rb.do_check(EVIDENCE, FALSE_ROW),
        rb.evidence_block(),
    )
    assert done.returncode != 0 and "stop, a person must look" in done.stderr
    assert FALSE_ROW in (_ledger(dsn) or []) and EVIDENCE not in (_ledger(dsn) or [])


@needs_pg
def test_runbook_case_g_adds_the_missing_error_column_and_keeps_every_row(scratch, tmp_path):
    """Ledger row 0005 evidence over an early tool_calls (no `error`): migrate does not notice; the check query of
    case (g) does; the repair file adds the column, keeps the rows, changes no ledger row; it can be run twice."""
    dsn, schema = scratch
    mig.migrate(dsn)
    _insert_tool_call(dsn)
    _sql(dsn, "ALTER TABLE tool_calls DROP COLUMN error")
    assert not _has_error_column(dsn)
    before = _ledger(dsn)
    assert mig.migrate(dsn) == []  # the gap the runbook case is for: no refusal, nothing repaired
    assert not _has_error_column(dsn)
    for _ in range(2):  # the second run is safe
        done = _psql(schema, tmp_path, rb.evidence_block())
        assert done.returncode == 0, done.stderr
    assert _has_error_column(dsn)
    assert _ledger(dsn) == before == REAL
    assert _sql(dsn, "SELECT error FROM tool_calls WHERE call_id = 'c1'") == [(False,)]
    assert mig.migrate(dsn) == []
    _insert_tool_call(dsn, "c2", with_error=True)


@needs_pg
def test_runbook_case_g_keeps_nothing_when_the_tables_differ_in_more_than_error(scratch, tmp_path):
    dsn, schema = scratch
    mig.migrate(dsn)
    _sql(dsn, "ALTER TABLE tool_calls DROP COLUMN error")
    _sql(dsn, "ALTER TABLE tool_calls DROP COLUMN attempt")
    done = _psql(schema, tmp_path, rb.evidence_block())
    assert done.returncode != 0 and "a person must look" in done.stderr
    assert not _has_error_column(dsn)  # the ALTER was undone with the rest of the file


# --- the recipe a refusal prints, RUN with psql, and the hand-file header --------------------------------


def _late_0004_message(dsn) -> str:
    """The database of FAIL-BEFORE 1 (0004 never applied, the rest is): the refusal message, which holds the recipe."""
    _apply_by_hand(dsn, [s for s in REAL if s != "0004_audit_checkpoint_meta"])
    with pytest.raises(MigrationNumberError) as e:
        mig.migrate(dsn)
    return str(e.value)


def _recipe_of(message: str) -> str:
    start = message.index("-- RECIPE begins")
    end = message.index("-- RECIPE ends") + len("-- RECIPE ends")
    return message[start:end] + "\n"


@needs_pg
def test_h1_hand_recipe_works(scratch, tmp_path):
    """the lines between the two RECIPE lines of the refusal message, saved to a file and run with
    `psql -X -v ON_ERROR_STOP=1 -f`, apply the late file and its ledger row; `migrate()` then has nothing to do."""
    dsn, _ = scratch
    message = _late_0004_message(dsn)
    assert "0004_audit_checkpoint_meta" not in _ledger(dsn)
    assert "key_label" not in {c for _, c in _columns(dsn)}
    done = _psql_text(tmp_path, _recipe_of(message))
    assert done.returncode == 0, done.stderr
    assert _ledger(dsn) == REAL
    assert {"alg", "key_label"} <= {c for t, c in _columns(dsn) if t == "audit_checkpoints"}
    assert mig.migrate(dsn) == []


@needs_pg
def test_h4_a_second_run_of_the_recipe_fails_and_keeps_nothing(scratch, tmp_path):
    """Case (a): 'running the same recipe twice is safe: the second run fails, and keeps nothing'."""
    dsn, _ = scratch
    recipe = _recipe_of(_late_0004_message(dsn))
    assert _psql_text(tmp_path, recipe).returncode == 0
    before = (_ledger(dsn), _columns(dsn))
    again = _psql_text(tmp_path, recipe)
    assert again.returncode != 0 and "schema_migrations" in again.stderr, again.stderr
    assert (_ledger(dsn), _columns(dsn)) == before


@needs_pg
def test_h4_a_recipe_that_fails_half_way_leaves_nothing(scratch, monkeypatch, tmp_path):
    """a late file whose second statement fails: the first statement, the ledger row and the lock are all undone."""
    dsn, _ = scratch
    _apply_by_hand(dsn, [s for s in REAL if s != "0004_audit_checkpoint_meta"])
    body = "INSERT INTO audit_checkpoints (seq, hash, signature) VALUES (7, 'a', 'b');\nSELECT 1 / 0;\n"
    planted = tmp_path / "0004_late_fail.sql"  # takes the place of the real 0004
    planted.write_text(body, encoding="utf-8")
    files = [p for p in mig._migration_files() if p.stem != "0004_audit_checkpoint_meta"] + [
        planted
    ]
    monkeypatch.setattr(mig, "_migration_files", lambda: files)
    # the planted file is not a released one: this test is about the recipe, not about the released-files check
    made_up_files_are_not_released(monkeypatch)
    with pytest.raises(MigrationNumberError) as e:
        mig.migrate(dsn)
    done = _psql_text(tmp_path, _recipe_of(str(e.value)))
    assert done.returncode != 0 and "division by zero" in done.stderr, done.stderr
    assert _ledger(dsn) == [r for r in REAL if r != "0004_audit_checkpoint_meta"]
    assert _sql(dsn, "SELECT count(*) FROM audit_checkpoints WHERE seq = 7") == [(0,)]


@needs_pg
def test_the_recipe_stops_at_the_first_error_even_without_the_stop_flag(
    scratch, monkeypatch, tmp_path
):
    """The recipe's own first line `\\set ON_ERROR_STOP on` does the stopping when the person forgets `-v`: psql exits
    with an error code instead of 0 (without the line it carries on and exits 0 although a statement failed)."""
    dsn, _ = scratch
    _apply_by_hand(dsn, [s for s in REAL if s != "0004_audit_checkpoint_meta"])
    planted = tmp_path / "0004_late_fail.sql"
    planted.write_text("SELECT 1 / 0;\n", encoding="utf-8")
    files = [p for p in mig._migration_files() if p.stem != "0004_audit_checkpoint_meta"] + [
        planted
    ]
    monkeypatch.setattr(mig, "_migration_files", lambda: files)
    # the planted file is not a released one: this test is about the recipe, not about the released-files check
    made_up_files_are_not_released(monkeypatch)
    with pytest.raises(MigrationNumberError) as e:
        mig.migrate(dsn)
    done = _psql_text(tmp_path, _recipe_of(str(e.value)), stop_flag=False)
    assert done.returncode != 0 and "division by zero" in done.stderr, done.stderr
    assert "0004_late_fail" not in _ledger(dsn)


@needs_pg
def test_the_recipe_and_the_runbook_header_start_with_the_timeouts(scratch):
    """both headers carry the two SET LOCAL lines right after BEGIN and before the lock."""
    dsn, _ = scratch
    lines = _recipe_of(_late_0004_message(dsn)).splitlines()
    at = lines.index("BEGIN;")
    assert lines[at + 1 : at + 3] == list(rb.TIMEOUTS)
    assert lines[at + 3].startswith("SELECT pg_advisory_xact_lock(")


@needs_pg
def test_a_hand_file_waiting_for_a_table_lock_stops_after_the_lock_timeout(scratch, tmp_path):
    """Run: another session holds ACCESS EXCLUSIVE on `tool_calls`; the hand file does not queue behind it for
    ever (and so does not stop every reader of a live table): it fails when the lock limit of `RECIPE_TIMEOUTS` runs out and keeps nothing."""
    dsn, schema = scratch
    mig.migrate(dsn)
    with psycopg.connect(dsn) as holder:
        holder.execute("LOCK TABLE tool_calls IN ACCESS EXCLUSIVE MODE")
        done = _psql(schema, tmp_path, "ALTER TABLE tool_calls ADD COLUMN hadavin_test_wait TEXT;")
    assert done.returncode != 0 and "lock timeout" in done.stderr, done.stderr
    assert ("tool_calls", "hadavin_test_wait") not in _columns(dsn)


@needs_pg
def test_case_a_current_user_assertion_stops_the_file_for_the_wrong_role(scratch, tmp_path):
    """the DO block of case (a) raises unless current_user is the named migration role."""
    dsn, schema = scratch
    block = rb.block_with("<MIGRATION ROLE>")
    with psycopg.connect(dsn) as db:
        me = db.execute("SELECT current_user").fetchone()[0]
    wrong = _psql(schema, tmp_path, block.replace("<MIGRATION ROLE>", "somebody_else"))
    assert wrong.returncode != 0 and "must be run by the migration role" in wrong.stderr
    right = _psql(schema, tmp_path, block.replace("<MIGRATION ROLE>", me))
    assert right.returncode == 0, right.stderr


# --- case (e), the three evidence variants, RUN -------------------------------------------------------------------------

BRANCH_ROW = "0005_measure"  # a made-up ledger row of a branch build
RENAMED = "0006_measure"  # the made-up folder file that has the same text after the number
BRANCH_FILE = {RENAMED + ".sql": "SELECT 1;\n"}


def _branch_database(dsn, *, evidence_row: str | None, tables: bool, error_column: bool = True):
    """Ledger 0001 to 0004 plus the branch row, and the evidence row and tables as the variant says."""
    _apply_by_hand(dsn, REAL[:4])
    _sql(dsn, "INSERT INTO schema_migrations (version) VALUES (%s)", (BRANCH_ROW,))
    if tables:  # made by hand as the migration role (the owner of every other table; a superuser's tables are refused)
        _as_migrator(dsn, (mig.MIGRATIONS / "0005_evidence.sql").read_text(encoding="utf-8"))
        if not error_column:
            _as_migrator(dsn, "ALTER TABLE tool_calls DROP COLUMN error")
    if evidence_row:
        _sql(dsn, "INSERT INTO schema_migrations (version) VALUES (%s)", (evidence_row,))


def _case_e_steps(variant: str, wrong: str | None) -> list[str]:
    e = rb.case("e")
    rename_branch = (
        rb.span_in(e, "UPDATE schema_migrations SET version = '<NEW>'")
        .replace("<NEW>", RENAMED)
        .replace("<OLD>", BRANCH_ROW)
    )
    steps = [rename_branch, rb.do_check(RENAMED, BRANCH_ROW)]
    insert = rb.span_in(e, "INSERT INTO schema_migrations (version) VALUES ('0005_evidence');")
    if variant == "E1":
        update = rb.span_in(e, "UPDATE schema_migrations SET version = '0005_evidence'").replace(
            "<the wrong name>", wrong
        )
        steps += [update, rb.do_check(EVIDENCE, wrong), rb.evidence_block()]
    elif variant == "E2":
        # the pasted file makes the tables, so it runs as the migration role (the runbook says so): `SET LOCAL ROLE`
        # stands for "connected as the migration role" here, and the check of case (a) proves it
        steps = [
            f'SET LOCAL ROLE "{PLAIN_ROLE}";',
            rb.block_with("<MIGRATION ROLE>").replace("<MIGRATION ROLE>", PLAIN_ROLE),
            *steps,
            (mig.MIGRATIONS / "0005_evidence.sql").read_text(encoding="utf-8"),
            insert,
        ]
    else:
        steps += [rb.evidence_block(), insert]
    return steps


def _refused_then_repaired(dsn, schema, tmp_path, monkeypatch, variant, wrong=None):
    _with_files(monkeypatch, tmp_path, BRANCH_FILE)
    with pytest.raises(ConfigError) as e:
        mig.migrate(dsn)
    assert (
        BRANCH_ROW in str(e.value)
        or EVIDENCE in str(e.value)
        or "applied out of order" in str(e.value)
    )
    done = _psql(schema, tmp_path, *_case_e_steps(variant, wrong))
    assert done.returncode == 0, done.stderr
    assert sorted(_ledger(dsn)) == sorted([*REAL, RENAMED])
    assert mig.migrate(dsn) == []
    assert _has_error_column(dsn)
    _insert_tool_call(dsn, "c2", with_error=True)  # the write the service makes


@needs_pg
@pytest.mark.parametrize("error_column", [True, False], ids=["tables_whole", "error_missing"])
def test_case_e_e1_the_evidence_row_has_another_number_and_both_tables_exist(
    scratch, monkeypatch, tmp_path, error_column
):
    """E1."""
    dsn, schema = scratch
    _branch_database(dsn, evidence_row=FALSE_ROW, tables=True, error_column=error_column)
    _refused_then_repaired(dsn, schema, tmp_path, monkeypatch, "E1", FALSE_ROW)


@needs_pg
def test_case_e_e2_no_evidence_row_and_no_tables(scratch, monkeypatch, tmp_path):
    dsn, schema = scratch
    _branch_database(dsn, evidence_row=None, tables=False)
    _refused_then_repaired(dsn, schema, tmp_path, monkeypatch, "E2")


@needs_pg
@pytest.mark.parametrize("error_column", [True, False], ids=["tables_whole", "error_missing"])
def test_case_e_e3_no_evidence_row_but_both_tables_exist(
    scratch, monkeypatch, tmp_path, error_column
):
    dsn, schema = scratch
    _branch_database(dsn, evidence_row=None, tables=True, error_column=error_column)
    _refused_then_repaired(dsn, schema, tmp_path, monkeypatch, "E3")


@needs_pg
def test_case_e_e1_with_one_table_missing_keeps_nothing(scratch, monkeypatch, tmp_path):
    """'If only one table exists, stop': the block of case (g) inside E1 stops the file and the renames are undone."""
    dsn, schema = scratch
    _branch_database(dsn, evidence_row=FALSE_ROW, tables=True)
    _sql(dsn, "DROP TABLE redaction_maps")
    done = _psql(schema, tmp_path, *_case_e_steps("E1", FALSE_ROW))
    assert done.returncode != 0 and "a person must look" in done.stderr
    assert BRANCH_ROW in _ledger(dsn) and FALSE_ROW in _ledger(dsn)


# --- migrate() sets the same limits as the hand recipe, RUN --------------------------------------------

# test-only values, short on purpose; the one that is not under test is long so that it cannot end the run first
WAIT_LIMIT_S = (
    20  # the longest this test lets the lock be held; the limit under test is a fraction of it
)
SHORT_LOCK = ("SET LOCAL lock_timeout = '1s';", "SET LOCAL statement_timeout = '20s';")
SHORT_STATEMENT = ("SET LOCAL lock_timeout = '20s';", "SET LOCAL statement_timeout = '1s';")


@needs_pg
def test_migrate_gives_up_waiting_for_a_table_lock_and_keeps_nothing(
    scratch, monkeypatch, tmp_path
):
    """another session holds ACCESS EXCLUSIVE on `tool_calls`; `migrate` does not queue behind it for ever: the
    limit of `mig.RECIPE_TIMEOUTS` (patched short here) ends the run, nothing is kept, no ledger row."""
    dsn, _ = scratch
    mig.migrate(dsn)
    before = _ledger(dsn)
    monkeypatch.setattr(mig, "RECIPE_TIMEOUTS", SHORT_LOCK)
    _with_files(
        monkeypatch,
        tmp_path,
        {PLANTED_NEXT: "ALTER TABLE tool_calls ADD COLUMN hadavin_test_wait TEXT;\n"},
    )
    with psycopg.connect(dsn) as holder:
        holder.execute("LOCK TABLE tool_calls IN ACCESS EXCLUSIVE MODE")
        # Without a limit `migrate` would wait for ever: let go of the lock after a while, so that the old code FAILS
        # this test (the run succeeds, nothing raises) instead of hanging it.
        let_go = threading.Timer(WAIT_LIMIT_S, holder.rollback)
        let_go.start()
        try:
            with pytest.raises(ConfigError, match=r"applying 0006_next\.sql.*lock_timeout") as got:
                mig.migrate(dsn)
            assert isinstance(got.value.__cause__, psycopg.errors.LockNotAvailable)
        finally:
            let_go.cancel()
    assert _ledger(dsn) == before
    assert ("tool_calls", "hadavin_test_wait") not in _columns(dsn)


@needs_pg
def test_migrate_stops_a_file_that_runs_past_the_statement_limit(scratch, monkeypatch, tmp_path):
    """a file whose statement runs longer than the statement limit of `mig.RECIPE_TIMEOUTS` (patched short here)
    fails the run and keeps nothing."""
    dsn, _ = scratch
    mig.migrate(dsn)
    before = _ledger(dsn)
    monkeypatch.setattr(mig, "RECIPE_TIMEOUTS", SHORT_STATEMENT)
    _with_files(monkeypatch, tmp_path, {PLANTED_NEXT: "SELECT pg_sleep(30);\n"})
    with pytest.raises(ConfigError, match=r"applying 0006_next\.sql.*statement_timeout"):
        mig.migrate(dsn)
    assert _ledger(dsn) == before


@needs_pg
def test_the_limits_migrate_runs_with_are_the_ones_in_the_constant(scratch, monkeypatch, tmp_path):
    """a planted file reads the two settings from the server inside the run (`1/0` when one differs): they are the
    values of `mig.RECIPE_TIMEOUTS` (patched to values that print back unchanged), and a wrong expectation fails, so
    the probe can fail."""
    dsn, _ = scratch
    monkeypatch.setattr(
        mig,
        "RECIPE_TIMEOUTS",
        ("SET LOCAL lock_timeout = '7s';", "SET LOCAL statement_timeout = '9s';"),
    )
    lock_t, stmt_t = (line.split("= ")[1].strip("';") for line in mig.RECIPE_TIMEOUTS)

    def probe(lock_expected: str) -> str:
        return (
            f"SELECT 1 / ((current_setting('lock_timeout') = '{lock_expected}' "
            f"AND current_setting('statement_timeout') = '{stmt_t}')::int);\n"
        )

    real_files = mig._migration_files
    _with_files(monkeypatch, tmp_path, {PLANTED_NEXT: probe("99s")})
    with pytest.raises(psycopg.errors.DivisionByZero):
        mig.migrate(dsn)
    # (no `monkeypatch.undo()` here: it would also undo the test-only plain-role connect of conftest)
    monkeypatch.setattr(mig, "_migration_files", real_files)
    _with_files(monkeypatch, tmp_path, {PLANTED_NEXT: probe(lock_t)})
    assert mig.migrate(dsn)[-1] == PLANTED_NEXT[:-4]


@needs_pg
def test_the_limits_also_cover_the_grant_phase_of_a_run_with_no_pending_file(scratch, monkeypatch):
    """nothing is pending, but a role grant waits for another session's uncommitted change of the rights of a table: the run stops
    after the lock limit, in plain words naming the step and the setting, and keeps nothing."""
    dsn, _ = scratch
    mig.migrate(dsn)
    before = _ledger(dsn)
    role = "hadavin_test_rt_" + uuid.uuid4().hex[:8]
    with psycopg.connect(dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE ROLE {}").format(sql.Identifier(role)))
    monkeypatch.setattr(mig, "RECIPE_TIMEOUTS", SHORT_LOCK)
    try:
        with psycopg.connect(dsn) as holder:
            # A GRANT takes no table lock; two changes of the rights of one table wait for each other, so the
            # holder's uncommitted GRANT is what the migrate GRANT/REVOKE queues behind.
            holder.execute(sql.SQL("GRANT SELECT ON tool_calls TO {}").format(sql.Identifier(role)))
            let_go = threading.Timer(WAIT_LIMIT_S, holder.rollback)
            let_go.start()
            try:
                with pytest.raises(ConfigError) as got:
                    mig.migrate(dsn, runtime_role=role)
            finally:
                let_go.cancel()
                holder.rollback()  # the holder's own GRANT is not kept either
        text = str(got.value)
        assert "while granting the roles" in text and "lock_timeout" in text, text
        assert "kept nothing" in text and "Migration repair steps" in text
        assert _ledger(dsn) == before
        with psycopg.connect(dsn) as db:  # nothing of the grants was kept
            assert not db.execute(
                "SELECT has_table_privilege(%s, 'tool_calls', 'SELECT')", (role,)
            ).fetchone()[0]
    finally:
        with psycopg.connect(dsn, autocommit=True) as db:
            db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
            db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


@needs_pg
def test_a_file_that_changes_a_limit_itself_is_refused_by_the_read_back(
    scratch, monkeypatch, tmp_path
):
    """a migration file that `SET LOCAL`s a limit is refused after that file (the limits are a guarantee for
    every file), and nothing of the run is kept. Killed by: mutant L1 (the limits are not in the read-back)."""
    dsn, _ = scratch
    monkeypatch.setattr(mig, "RECIPE_TIMEOUTS", SHORT_LOCK)  # statement limit 20s, lock limit 1s
    # the text scan refuses a `SET LOCAL` of a limit (test_migration_numbers); a function can still change it, so the
    # read-back is the guard that this test exercises
    _with_files(
        monkeypatch,
        tmp_path,
        {PLANTED_NEXT: _FLIP + "SELECT hadavin_test_flip('statement_timeout', '11s');\n"},
    )
    with pytest.raises(
        ConfigError, match=r"0006_next\.sql.*statement_timeout was '20s' and is now '11s'"
    ):
        mig.migrate(dsn)
    assert _ledger(dsn) in (None, [])


# --- the migration role is checked against a real server ------------------------------------------------


@pytest.fixture
def plain_role(scratch):
    """(dsn of a login role with none of the five flags, schema); the role is dropped afterwards."""
    dsn, schema = scratch
    role = f"mig_{uuid.uuid4().hex[:10]}"
    with psycopg.connect(DSN, autocommit=True) as db:
        password = create_login_role(db, role)
        db.execute(
            sql.SQL("GRANT ALL ON SCHEMA {} TO {}").format(
                sql.Identifier(schema), sql.Identifier(role)
            )
        )
        db.execute(
            sql.SQL("GRANT CREATE ON DATABASE {} TO {}").format(
                sql.Identifier(db.execute("SELECT current_database()").fetchone()[0]),
                sql.Identifier(role),
            )
        )
    try:
        yield make_conninfo(dsn, user=role, password=password), role
    finally:
        with psycopg.connect(DSN, autocommit=True) as db:
            db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
            db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


@needs_pg
@pytest.mark.real_connect
@pytest.mark.parametrize(
    "flag", ["SUPERUSER", "CREATEROLE", "CREATEDB", "BYPASSRLS", "REPLICATION"]
)
def test_a_migration_role_with_a_privilege_flag_is_refused_by_a_real_server(plain_role, flag):
    """Killed by: mutants S1..S5 (no check, or one flag not read), on a real server."""
    dsn, role = plain_role
    with psycopg.connect(DSN, autocommit=True) as db:
        db.execute(sql.SQL(f"ALTER ROLE {{}} {flag}").format(sql.Identifier(role)))
    with pytest.raises(ConfigError, match="must not be a superuser") as e:
        mig.migrate(dsn)
    assert {
        "SUPERUSER": "rolsuper",
        "CREATEROLE": "rolcreaterole",
        "CREATEDB": "rolcreatedb",
        "BYPASSRLS": "rolbypassrls",
        "REPLICATION": "rolreplication",
    }[flag] in str(e.value)
    assert "CREATE ROLE migration_role LOGIN NOSUPERUSER" in str(e.value), (
        "the message says how to make a plain role"
    )
    assert _ledger(dsn) is None, "nothing was created"


@needs_pg
@pytest.mark.real_connect
@pytest.mark.parametrize(
    ("inherit", "flag"),
    [
        ("TRUE", "CREATEROLE"),
        ("FALSE", "CREATEROLE"),
        ("TRUE", "REPLICATION"),
        ("FALSE", "REPLICATION"),
    ],
)
def test_a_plain_role_that_is_a_member_of_a_privileged_role_is_refused_by_a_real_server(
    plain_role, inherit, flag
):
    """A member of a role with CREATEROLE can use or `SET ROLE` to it, so the plain login alone is not enough."""
    dsn, role = plain_role
    boss = role + "_boss"
    with psycopg.connect(DSN, autocommit=True) as db:
        db.execute(sql.SQL(f"CREATE ROLE {{}} NOLOGIN {flag}").format(sql.Identifier(boss)))
        try:
            db.execute(
                sql.SQL(f"GRANT {{}} TO {{}} WITH INHERIT {inherit}").format(
                    sql.Identifier(boss), sql.Identifier(role)
                )
            )
            with pytest.raises(ConfigError, match="member of a role that is a superuser") as e:
                mig.migrate(dsn)
            assert boss in str(e.value)
            assert _ledger(dsn) is None, "nothing was created"
        finally:
            db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(boss)))


@needs_pg
@pytest.mark.real_connect
def test_the_test_helper_refuses_to_take_over_a_schema_that_is_not_a_scratch_one():
    """The helper changes the owner of the schema in use: on a schema whose name has no test prefix (made here, so the
    test does not depend on `public`) it must refuse and change nothing. Killed by: mutant B3."""
    from tests.fixtures.migration_role import NotAScratchSchema, plain_role_connect

    other = "other_app_" + uuid.uuid4().hex[:8]
    owner_sql = "SELECT nspowner::regrole::text FROM pg_namespace WHERE nspname = %s"
    with psycopg.connect(DSN, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(other)))
        before = db.execute(owner_sql, (other,)).fetchone()
    try:
        with pytest.raises(NotAScratchSchema):
            plain_role_connect(psycopg.connect)(
                make_conninfo(DSN, options=f"-c search_path={other}"), autocommit=True
            )
        with psycopg.connect(DSN, autocommit=True) as db:
            assert db.execute(owner_sql, (other,)).fetchone() == before
    finally:
        with psycopg.connect(DSN, autocommit=True) as db:
            db.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(other)))


@needs_pg
@pytest.mark.real_connect
def test_a_plain_migration_role_runs_with_the_real_connect(plain_role):
    """There is no override: a login role with none of the five flags runs `migrate()` with the real `connect`."""
    dsn, _ = plain_role
    assert mig.migrate(dsn) == REAL
    assert mig.migrate(dsn) == []


# --- the upgrade from a database a superuser login built: every table is owned by that login ------------------------------


def _build_as_the_superuser(dsn) -> None:
    """The first build as the superuser login (the usual start of a demo): the real files, the ledger and every table
    are owned by that login, not by the plain migration role that runs `migrate` later."""
    with psycopg.connect(dsn, autocommit=True) as db:
        db.execute(
            "CREATE TABLE schema_migrations (version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
        )
        for stem in REAL:
            db.execute((mig.MIGRATIONS / f"{stem}.sql").read_text(encoding="utf-8"))
            db.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (stem,))


@needs_pg
@pytest.mark.real_connect
def test_tables_owned_by_another_role_are_refused_with_the_sql_that_hands_them_over(
    scratch, plain_role, monkeypatch, tmp_path
):
    """The tables belong to the old superuser login. Without this check the plain migration role would run a later
    `ALTER TABLE` into 'must be owner of table' (and its grants would do nothing without an error). `migrate` refuses
    first, names the objects and their owner, and prints the `ALTER ... OWNER TO` lines; after an administrator runs
    them, a file that alters a table applies. Killed by: mutant O1 (the ownership check is not called) and OA5 (the ledger table is not a managed name)."""
    dsn, role = plain_role
    super_dsn, _ = scratch  # the same schema, reached with the superuser login
    _build_as_the_superuser(super_dsn)
    _with_files(
        monkeypatch,
        tmp_path,
        {"0006_alter.sql": "ALTER TABLE spend ADD COLUMN note_after_handover TEXT;\n"},
    )
    with pytest.raises(ConfigError) as e:
        mig.migrate(dsn)
    msg = str(e.value)
    assert "cannot change" in msg and "another role owns" in msg, msg
    assert "case (h)" in msg and f'OWNER TO "{role}";' in msg, msg
    # three parts, in this order: what is wrong, that nothing changed, what the administrator does
    wrong, unchanged, todo = (
        msg.find(x) for x in ("cannot change", "Nothing was changed.", "case (h)")
    )
    assert 0 <= wrong < unchanged < todo, msg
    assert "SECURITY DEFINER" in msg, msg
    with psycopg.connect(DSN, autocommit=True) as db:
        login = db.execute("SELECT current_user").fetchone()[0]
    assert "ALTER TABLE" in msg and "audit_entries" in msg and f"owner {login}" in msg, msg
    assert "schema_migrations" in msg, (
        "the ledger table is one of the package's own objects: " + msg
    )
    assert _ledger(super_dsn) == REAL, "nothing was changed"
    # the administrator runs the printed lines (as the superuser login, in one transaction)
    statements = [
        m for m in msg[msg.index("case (h): ") + len("case (h): ") :].split(";") if m.strip()
    ]
    assert statements and all(s.strip().startswith("ALTER ") for s in statements), statements
    schema = conninfo_to_dict(super_dsn)["options"].rsplit("search_path=", 1)[1]
    done = _psql(
        schema, tmp_path, *[s.strip() + ";" for s in statements]
    )  # the hand file of case (h)
    assert done.returncode == 0, done.stderr
    assert mig.migrate(dsn) == ["0006_alter"]
    with psycopg.connect(dsn, autocommit=True) as db:
        assert db.execute(
            "SELECT count(*) FROM information_schema.columns WHERE table_schema = current_schema() "
            "AND table_name = 'spend' AND column_name = 'note_after_handover'"
        ).fetchone() == (1,)


@needs_pg
@pytest.mark.real_connect
def test_one_table_owned_by_another_role_is_enough_to_refuse_and_a_function_is_named(
    scratch, plain_role, monkeypatch
):
    """A database the plain role built, except one table and one function that the superuser login made: both are named
    and the `ALTER` lines say TABLE and FUNCTION; objects the role owns are not listed."""
    dsn, _role = plain_role
    super_dsn, _ = scratch
    _manage(monkeypatch, "hadavin_test_foreign", "hadavin_test_foreign_fn")
    assert mig.migrate(dsn) == REAL
    with psycopg.connect(super_dsn, autocommit=True) as db:
        db.execute("CREATE TABLE hadavin_test_foreign (id INT)")
        db.execute(
            "CREATE FUNCTION hadavin_test_foreign_fn(a int) RETURNS int LANGUAGE sql AS 'SELECT 1'"
        )
    with pytest.raises(ConfigError) as e:
        mig.migrate(dsn)
    msg = str(e.value)
    assert "cannot change 2 object(s)" in msg, msg
    assert 'ALTER TABLE "' in msg and "hadavin_test_foreign" in msg and "ALTER FUNCTION" in msg, msg
    assert "audit_entries" not in msg and "tool_calls" not in msg, msg


# --- the migration role: session user, built-in server roles, parameter grants ----------------------------------------


@needs_pg
@pytest.mark.real_connect
def test_a_superuser_login_that_switches_to_a_plain_role_is_refused(scratch, plain_role):
    """The login (session user) is a superuser; `-c role=` switched the current user to a plain role. A file could undo
    the switch inside a function body, so the session user is checked too. Killed by: mutant SU1."""
    _dsn, role = plain_role
    super_dsn, _ = scratch
    options = conninfo_to_dict(super_dsn)["options"] + f" -c role={role}"
    switched = make_conninfo(super_dsn, options=options)
    with pytest.raises(ConfigError, match="must not be a superuser"):
        mig.migrate(switched)
    assert _ledger(super_dsn) is None, "nothing was created"


BUILT_IN_ROLES = [
    "pg_execute_server_program",
    "pg_write_server_files",
    "pg_read_server_files",
    "pg_write_all_data",
    "pg_signal_backend",
    "pg_monitor",
]


@needs_pg
@pytest.mark.real_connect
@pytest.mark.parametrize("built_in", BUILT_IN_ROLES)
def test_a_member_of_a_built_in_server_role_is_refused_by_a_real_server(plain_role, built_in):
    """These roles run programs, write files or read all data on the server. Killed by: mutant PD1."""
    dsn, role = plain_role
    with psycopg.connect(DSN, autocommit=True) as db:
        db.execute(sql.SQL(f"GRANT {built_in} TO {{}}").format(sql.Identifier(role)))
    with pytest.raises(ConfigError, match="built-in server role") as e:
        mig.migrate(dsn)
    assert built_in in str(e.value)
    assert _ledger(dsn) is None, "nothing was created"


@needs_pg
@pytest.mark.real_connect
def test_the_session_user_is_checked_for_membership_too(scratch, plain_role):
    """The login is a member of a built-in server role and switched to a plain role it may switch to: the current user
    holds nothing, the session user does. Killed by: mutant SU2."""
    _dsn, role = plain_role
    super_dsn, schema = scratch
    other = role + "_b"
    with psycopg.connect(DSN, autocommit=True) as db:
        db.execute(sql.SQL("CREATE ROLE {}").format(sql.Identifier(other)))
        try:
            # the switched-to role can use the scratch schema, so a run that is NOT refused would go on to apply the files
            # (and the test would fail on "DID NOT RAISE"), not stop on a missing schema
            db.execute(
                sql.SQL("GRANT ALL ON SCHEMA {} TO {}").format(
                    sql.Identifier(schema), sql.Identifier(other)
                )
            )
            db.execute(
                sql.SQL("GRANT {} TO {}").format(sql.Identifier(other), sql.Identifier(role))
            )
            db.execute(sql.SQL("GRANT pg_signal_backend TO {}").format(sql.Identifier(role)))
            login = login_dsn(
                super_dsn,
                role,
                options=conninfo_to_dict(super_dsn)["options"] + f" -c role={other}",
            )
            with pytest.raises(ConfigError, match="built-in server role"):
                mig.migrate(login)
        finally:
            db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(other)))
            db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(other)))


@needs_pg
@pytest.mark.real_connect
def test_a_parameter_grant_is_refused_by_a_real_server(plain_role):
    """A grant on a server setting lets a file change what the checks rely on. Killed by: mutant PA1."""
    dsn, role = plain_role
    with psycopg.connect(DSN, autocommit=True) as db:
        db.execute(
            sql.SQL("GRANT SET ON PARAMETER session_replication_role TO {}").format(
                sql.Identifier(role)
            )
        )
    try:
        with pytest.raises(ConfigError, match="server settings it must not change") as e:
            mig.migrate(dsn)
        assert "session_replication_role" in str(e.value)
        assert _ledger(dsn) is None, "nothing was created"
    finally:
        with psycopg.connect(DSN, autocommit=True) as db:
            db.execute(
                sql.SQL("REVOKE SET ON PARAMETER session_replication_role FROM {}").format(
                    sql.Identifier(role)
                )
            )


# --- the plain-role SQL that the refusal prints ------------------------------------------------------------------------


def _role_from_the_printed_sql(schema: str, grant_option: bool) -> tuple[str, str, str]:
    """Make a login role, a runtime role and a portal role; the migration role gets ONLY what `PLAIN_MIGRATION_ROLE_SQL`
    prints (with or without its grant option)."""
    suffix = uuid.uuid4().hex[:8]
    role, rt, pt = (
        f"hadavin_test_pm_{suffix}",
        f"hadavin_test_rt_{suffix}",
        f"hadavin_test_pt_{suffix}",
    )
    printed = mig.PLAIN_MIGRATION_ROLE_SQL.replace("migration_role", role).replace(
        "<schema>", sql.Identifier(schema).as_string()
    )
    if not grant_option:
        printed = printed.replace(" WITH GRANT OPTION", "")
    with psycopg.connect(DSN, autocommit=True) as db:
        db.execute(printed)
        set_login_password(
            db, role
        )  # the printed SQL sets none (a person adds the login method that fits)
        for other in (rt, pt):
            db.execute(sql.SQL("CREATE ROLE {}").format(sql.Identifier(other)))
        db.execute(
            sql.SQL("GRANT CREATE ON DATABASE {} TO {}").format(
                sql.Identifier(db.execute("SELECT current_database()").fetchone()[0]),
                sql.Identifier(role),
            )
        )
    return role, rt, pt


def _drop_all(*roles: str) -> None:
    with psycopg.connect(DSN, autocommit=True) as db:
        for r in roles:
            db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(r)))
            db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(r)))


@needs_pg
@pytest.mark.real_connect
def test_a_role_made_with_the_printed_sql_only_can_pass_usage_on_to_the_runtime_and_portal_roles(
    scratch,
):
    """The printed SQL carries the grant option, so `migrate` with a runtime and a portal role works for a role that
    is not the owner of the schema. Killed by: mutant GO1 (the grant option is left out of the printed SQL)."""
    super_dsn, schema = scratch
    role, rt, pt = _role_from_the_printed_sql(schema, grant_option=True)
    try:
        assert mig.migrate(login_dsn(super_dsn, role), runtime_role=rt, portal_role=pt) == REAL
        with psycopg.connect(DSN, autocommit=True) as db:
            assert db.execute(
                "SELECT has_schema_privilege(%s, %s, 'USAGE')", (rt, schema)
            ).fetchone() == (True,)
    finally:
        _drop_all(role, rt, pt)


@needs_pg
@pytest.mark.real_connect
def test_a_role_without_the_grant_option_is_refused_when_its_grants_would_do_nothing(scratch):
    """Without the grant option `GRANT USAGE ON SCHEMA ... TO runtime_role` only warns; `migrate` checks that the role
    really can use the schema afterwards and refuses. Killed by: no list mutant today (the check of grant options is covered by the shipped-file runs); it is a control test."""
    super_dsn, schema = scratch
    role, rt, pt = _role_from_the_printed_sql(schema, grant_option=False)
    try:
        with pytest.raises(ConfigError, match="cannot use the schema"):
            mig.migrate(login_dsn(super_dsn, role), runtime_role=rt)
        assert _ledger(super_dsn) is None, "the refusal rolled everything back"
    finally:
        _drop_all(role, rt, pt)


# --- objects another role owns: kinds, partitions, names, cap, safe owners, extensions -----------------------------------


def _manage(monkeypatch, *names: str) -> None:
    """Make the package also manage these made-up names: the ownership check looks only at what the package manages
    (`_managed_names`), and these tests make foreign objects with names the package never uses."""
    real = mig._managed_names

    def with_names(texts, schema):
        relations, functions = real(texts, schema)
        return sorted({*relations, *names}), sorted({*functions, *names})

    monkeypatch.setattr(mig, "_managed_names", with_names)


def _hand_over(super_dsn, tmp_path, msg: str):
    """Run the printed statements as the administrator (the superuser login) and return the finished psql process."""
    statements = [
        m.strip() + ";"
        for m in msg[msg.index("case (h): ") + len("case (h): ") :].split(";")
        if m.strip().startswith("ALTER ")
    ]
    schema = conninfo_to_dict(super_dsn)["options"].rsplit("search_path=", 1)[1].split(" ")[0]
    return statements, _psql(schema, tmp_path, *statements)


@needs_pg
@pytest.mark.real_connect
def test_a_procedure_and_an_aggregate_get_their_own_words_and_the_printed_lines_run(
    scratch, plain_role, tmp_path, monkeypatch
):
    """`ALTER FUNCTION` fails on a procedure or an aggregate; the line says PROCEDURE or AGGREGATE, and a function that
    takes arguments keeps them. Killed by: mutant FO1 (every routine is printed as FUNCTION)."""
    dsn, _role = plain_role
    super_dsn, _ = scratch
    _manage(monkeypatch, "hadavin_test_proc", "hadavin_test_agg", "hadavin_test_fn")
    assert mig.migrate(dsn) == REAL
    with psycopg.connect(super_dsn, autocommit=True) as db:
        db.execute("CREATE PROCEDURE hadavin_test_proc(a int) LANGUAGE sql AS 'SELECT 1'")
        db.execute("CREATE AGGREGATE hadavin_test_agg(int) (sfunc = int4pl, stype = int)")
        db.execute(
            "CREATE FUNCTION hadavin_test_fn(a int, b text) RETURNS int LANGUAGE sql AS 'SELECT 1'"
        )
    with pytest.raises(ConfigError) as e:
        mig.migrate(dsn)
    msg = str(e.value)
    assert "cannot change 3 object(s)" in msg, msg
    statements, done = _hand_over(super_dsn, tmp_path, msg)
    assert any(s.startswith("ALTER PROCEDURE") for s in statements), statements
    assert any(s.startswith("ALTER AGGREGATE") for s in statements), statements
    assert any(s.startswith("ALTER FUNCTION") and "(a integer, b text)" in s for s in statements), (
        statements
    )
    assert done.returncode == 0, done.stderr
    assert mig.migrate(dsn) == []


@needs_pg
@pytest.mark.real_connect
def test_a_partition_owned_by_another_role_is_listed(scratch, plain_role, monkeypatch):
    """A partition has an automatic dependency on its parent, but it is a table of its own that the plain role cannot
    change. Killed by: mutant FO2 (the dependency test hides it)."""
    dsn, role = plain_role
    super_dsn, _ = scratch
    _manage(monkeypatch, "hadavin_test_part", "hadavin_test_parent")
    assert mig.migrate(dsn) == REAL
    with psycopg.connect(super_dsn, autocommit=True) as db:
        db.execute("CREATE TABLE hadavin_test_parent (id int) PARTITION BY RANGE (id)")
        db.execute(
            "CREATE TABLE hadavin_test_part PARTITION OF hadavin_test_parent FOR VALUES FROM (0) TO (10)"
        )
        db.execute(
            sql.SQL("ALTER TABLE hadavin_test_parent OWNER TO {}").format(sql.Identifier(role))
        )
    with pytest.raises(ConfigError) as e:
        mig.migrate(dsn)
    msg = str(e.value)
    assert "cannot change 1 object(s)" in msg and "hadavin_test_part" in msg, msg
    assert "hadavin_test_parent" not in msg, msg


@needs_pg
@pytest.mark.real_connect
def test_a_name_with_a_newline_is_never_copied_into_a_printed_statement(
    scratch, plain_role, monkeypatch
):
    """The other role chose the table's name. The list shows it escaped; no statement is printed for it, and the message
    says a person must write that one by hand. Killed by: mutant FO3 (every name is printed)."""
    dsn, _role = plain_role
    super_dsn, _ = scratch
    _manage(monkeypatch, "hadavin_test_bad\nname", "hadavin_test_fine")
    assert mig.migrate(dsn) == REAL
    with psycopg.connect(super_dsn, autocommit=True) as db:
        db.execute('CREATE TABLE "hadavin_test_bad\nname" (id int)')
        db.execute("CREATE TABLE hadavin_test_fine (id int)")
    with pytest.raises(ConfigError) as e:
        mig.migrate(dsn)
    msg = str(e.value)
    assert mig._label("hadavin_test_bad\nname") in msg and "bad\nname" not in msg, msg
    assert "by hand" in msg, msg
    assert msg.count("ALTER TABLE") == 1 and "hadavin_test_fine" in msg, msg


@needs_pg
@pytest.mark.real_connect
def test_every_statement_is_printed_when_more_than_the_shown_names_are_foreign(
    scratch, plain_role, tmp_path, monkeypatch
):
    """The cap is for the names in the list only; a person needs every `ALTER` line. Killed by: mutant FO4."""
    dsn, _role = plain_role
    super_dsn, _ = scratch
    _manage(monkeypatch, *[f"hadavin_test_many_{i:02d}" for i in range(25)])
    assert mig.migrate(dsn) == REAL
    with psycopg.connect(super_dsn, autocommit=True) as db:
        for i in range(25):
            db.execute(f"CREATE TABLE hadavin_test_many_{i:02d} (id int)")
    with pytest.raises(ConfigError) as e:
        mig.migrate(dsn)
    msg = str(e.value)
    assert "cannot change 25 object(s)" in msg and "and 5 more" in msg, msg
    statements, done = _hand_over(super_dsn, tmp_path, msg)
    assert len(statements) == 25, len(statements)
    assert done.returncode == 0, done.stderr
    assert mig.migrate(dsn) == []


@needs_pg
@pytest.mark.real_connect
@pytest.mark.parametrize("inherit", ["TRUE", "FALSE"])
def test_an_owner_the_migration_role_belongs_to_is_safe_only_when_it_inherits(
    plain_role, scratch, inherit
):
    """Owner = a role the migration role is a member of. With INHERIT TRUE the migration role has the owner's rights
    (it may alter the table): no refusal. With INHERIT FALSE it must first `SET ROLE`: refused. Killed by: mutant
    OW1 (USAGE becomes MEMBER, which is true for both)."""
    dsn, role = plain_role
    super_dsn, _ = scratch
    assert mig.migrate(dsn) == REAL
    boss = role + "_boss"
    with psycopg.connect(DSN, autocommit=True) as db:
        db.execute(sql.SQL("CREATE ROLE {}").format(sql.Identifier(boss)))
        try:
            with psycopg.connect(super_dsn, autocommit=True) as sdb:
                sdb.execute(sql.SQL("ALTER TABLE spend OWNER TO {}").format(sql.Identifier(boss)))
            db.execute(
                sql.SQL(f"GRANT {{}} TO {{}} WITH INHERIT {inherit}").format(
                    sql.Identifier(boss), sql.Identifier(role)
                )
            )
            if inherit == "TRUE":
                assert mig.migrate(dsn) == []
            else:
                with pytest.raises(ConfigError, match="cannot change 1 object"):
                    mig.migrate(dsn)
        finally:
            db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(boss)))
            db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(boss)))


@needs_pg
@pytest.mark.real_connect
def test_objects_of_an_installed_extension_are_not_listed(scratch, plain_role):
    """An extension installed by the superuser puts functions and types of its own into the schema; they belong to the
    extension and are not listed (the owner rule skips what an extension owns). A view of an extension that everyone may
    read IS refused, without a statement: `test_an_extension_view_readable_by_everyone_is_refused_without_a_statement`.
    Killed by: mutant EX1 (the extension test is gone from the function half)."""
    dsn, _role = plain_role
    super_dsn, _ = scratch
    assert mig.migrate(dsn) == REAL
    with psycopg.connect(super_dsn, autocommit=True) as db:
        db.execute(
            sql.SQL("CREATE EXTENSION citext SCHEMA {}").format(
                sql.Identifier(conninfo_to_dict(super_dsn)["options"].rsplit("search_path=", 1)[1])
            )
        )
    assert mig.migrate(dsn) == []


def _extension_owns(super_dsn: str, statements: list[str]) -> None:
    """Install `citext` in the schema of the run, then run each statement as the superuser login."""
    schema = conninfo_to_dict(super_dsn)["options"].rsplit("search_path=", 1)[1]
    with psycopg.connect(super_dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE EXTENSION citext SCHEMA {}").format(sql.Identifier(schema)))
        for statement in statements:
            db.execute(statement)


@needs_pg
@pytest.mark.real_connect
def test_the_owner_check_leaves_a_managed_function_of_an_extension_to_the_state_check(
    scratch, plain_role, monkeypatch
):
    """The same name as a function of the files, owned by the superuser login and made a member of an installed
    extension. The early owner check (`_FOREIGN_OWNED_SQL`, step 1, "cannot change N object") skips it, as it skips
    what an extension owns; the state check of step 2 still refuses it ("before any migration file ran"), because an
    object that the family does not own is wrong whoever made it (ticket P3a-2, rule E1). Without the extension the
    early check refuses it (`test_the_function_half_of_the_ownership_check_finds_a_function_alone`). Killed by:
    mutant EX1 (the extension test is gone from the function half: the early message appears instead)."""
    dsn, _role = plain_role
    super_dsn, _ = scratch
    _manage(monkeypatch, "hadavin_test_ext_fn")
    assert mig.migrate(dsn) == REAL
    _extension_owns(
        super_dsn,
        [
            "CREATE FUNCTION hadavin_test_ext_fn() RETURNS int LANGUAGE sql AS 'SELECT 1'",
            "ALTER EXTENSION citext ADD FUNCTION hadavin_test_ext_fn()",
        ],
    )
    with pytest.raises(
        ConfigError, match=r"(?s)before any migration file ran.*hadavin_test_ext_fn"
    ) as e:
        mig.migrate(dsn)
    assert "cannot change" not in str(e.value)


@needs_pg
@pytest.mark.real_connect
def test_the_owner_check_leaves_a_managed_table_of_an_extension_to_the_state_check(
    scratch, plain_role
):
    """A table of the grant map, owned by the superuser login and made a member of an installed extension: the early
    owner check skips it and the state check of step 2 refuses it, as for the function above. Killed by: mutant EX2
    (the extension test is gone from the table half: the early message appears instead)."""
    dsn, _role = plain_role
    super_dsn, _ = scratch
    assert mig.migrate(dsn) == REAL
    _extension_owns(
        super_dsn,
        [
            "ALTER TABLE dead_letters OWNER TO CURRENT_USER",
            "ALTER EXTENSION citext ADD TABLE dead_letters",
        ],
    )
    with pytest.raises(ConfigError, match=r"(?s)before any migration file ran.*dead_letters") as e:
        mig.migrate(dsn)
    assert "cannot change" not in str(e.value)


@needs_pg
@pytest.mark.real_connect
def test_an_extension_view_readable_by_everyone_is_refused_without_a_statement(scratch, plain_role):
    """`pg_stat_statements` puts two views into the schema that everyone may read. A REVOKE would be undone by the next
    `ALTER EXTENSION ... UPDATE`, so the line names the extension and prints no statement (a person decides). Killed by:
    mutant EX2 (the extension test is gone from the table half)."""
    dsn, _role = plain_role
    super_dsn, _ = scratch
    assert mig.migrate(dsn) == REAL
    with psycopg.connect(super_dsn, autocommit=True) as db:
        db.execute(
            sql.SQL("CREATE EXTENSION pg_stat_statements SCHEMA {}").format(
                sql.Identifier(conninfo_to_dict(super_dsn)["options"].rsplit("search_path=", 1)[1])
            )
        )
    with pytest.raises(ConfigError, match="belongs to the extension pg_stat_statements") as e:
        mig.migrate(dsn)
    lines = [ln for ln in str(e.value).splitlines() if "pg_stat_statements" in ln]
    assert lines and all("no statement is printed" in ln and "To remove" not in ln for ln in lines)


@needs_pg
@pytest.mark.real_connect
def test_the_function_half_of_the_ownership_check_finds_a_function_alone(
    scratch, plain_role, monkeypatch
):
    """Only a function is foreign (no table). Killed by: mutant OW2 (the function half finds nothing)."""
    dsn, _role = plain_role
    super_dsn, _ = scratch
    _manage(monkeypatch, "hadavin_test_only_fn")
    assert mig.migrate(dsn) == REAL
    with psycopg.connect(super_dsn, autocommit=True) as db:
        db.execute("CREATE FUNCTION hadavin_test_only_fn() RETURNS int LANGUAGE sql AS 'SELECT 1'")
    with pytest.raises(ConfigError, match=r"cannot change 1 object"):
        mig.migrate(dsn)


@needs_pg
@pytest.mark.real_connect
def test_tables_and_functions_of_another_application_in_the_schema_are_never_refused_or_listed(
    scratch, plain_role
):
    """A schema that another application shares: its tables, views, sequences and functions are owned by a login the
    migration role cannot act as, and are none of this package's business. No refusal, and (with one package table also
    foreign) the message and the printed lines name the package table only. Killed by: mutants OA1 (the table half
    lists every relation) and OA2 (the function half lists every function)."""
    dsn, _role = plain_role
    super_dsn, _ = scratch
    assert mig.migrate(dsn) == REAL
    with psycopg.connect(super_dsn, autocommit=True) as db:
        db.execute("CREATE TABLE hadavin_test_other_app (id serial PRIMARY KEY)")
        db.execute("CREATE VIEW hadavin_test_other_view AS SELECT 1 AS one")
        db.execute("CREATE FUNCTION hadavin_test_other_fn() RETURNS int LANGUAGE sql AS 'SELECT 1'")
    assert mig.migrate(dsn) == [], "another application's objects must not stop the run"
    with psycopg.connect(super_dsn, autocommit=True) as db:
        db.execute("ALTER TABLE dead_letters OWNER TO CURRENT_USER")
        db.execute("ALTER TABLE spend OWNER TO CURRENT_USER")
    with pytest.raises(ConfigError) as e:
        mig.migrate(dsn)
    msg = str(e.value)
    assert "cannot change" in msg and "of this package" in msg, msg
    assert "dead_letters" in msg or "spend" in msg, msg
    assert "hadavin_test_other" not in msg, msg


@needs_pg
@pytest.mark.real_connect
def test_a_function_a_migration_file_creates_counts_as_managed(scratch, plain_role, tmp_path):
    """The function the real files create is managed by name: when the superuser login owns it, the run is refused.
    Killed by: mutant OA3 (functions are never added to the managed names)."""
    dsn, _role = plain_role
    super_dsn, _ = scratch
    assert mig.migrate(dsn) == REAL
    with psycopg.connect(super_dsn, autocommit=True) as db:
        names = [
            r[0]
            for r in db.execute(
                "SELECT p.proname FROM pg_proc p WHERE p.pronamespace = current_schema()::regnamespace"
            ).fetchall()
        ]
        assert names, "the real files create at least one function"
        for fn in names:
            for (args,) in db.execute(
                "SELECT pg_get_function_identity_arguments(p.oid) FROM pg_proc p "
                "WHERE p.proname = %s AND p.pronamespace = current_schema()::regnamespace",
                (fn,),
            ).fetchall():
                db.execute(
                    sql.SQL("ALTER FUNCTION {}({}) OWNER TO CURRENT_USER").format(
                        sql.Identifier(fn), sql.SQL(args)
                    )
                )
    with pytest.raises(ConfigError, match=r"cannot change \d+ object"):
        mig.migrate(dsn)


@needs_pg
@pytest.mark.real_connect
def test_functions_with_capitals_or_a_space_in_the_name_count_as_managed(
    scratch, plain_role, monkeypatch, tmp_path
):
    """A file creates `Mixed_Case_Fn()` (stored as `mixed_case_fn`) and `"Odd Name Fn"()`; the superuser login then takes
    them over. The next run is refused and names both. Killed by: mutants MN1 and MN2."""
    dsn, _role = plain_role
    super_dsn, _ = scratch
    body = (
        "CREATE OR REPLACE FUNCTION Mixed_Case_Fn() RETURNS int LANGUAGE sql AS $$ SELECT 1 $$;\n"
        'CREATE OR REPLACE FUNCTION "Odd Name Fn"() RETURNS int LANGUAGE sql AS $$ SELECT 2 $$;\n'
    )
    _with_files(monkeypatch, tmp_path, {"0006_names.sql": body})
    assert mig.migrate(dsn) == REAL + ["0006_names"]
    with psycopg.connect(super_dsn, autocommit=True) as db:
        db.execute("ALTER FUNCTION mixed_case_fn() OWNER TO CURRENT_USER")
        db.execute('ALTER FUNCTION "Odd Name Fn"() OWNER TO CURRENT_USER')
    with pytest.raises(ConfigError) as e:
        mig.migrate(dsn)
    assert "mixed_case_fn" in str(e.value) and "Odd Name Fn" in str(e.value), str(e.value)


def test_one_connection_target_is_one_entry_whatever_the_search_path():
    """Killed by: mutant DD1 (the whole connection string, with its search path, is the entry)."""
    a = "host=h port=1 dbname=d user=u options='-c search_path=hadavin_test_a'"
    b = "host=h port=1 dbname=d user=u options='-c search_path=hadavin_test_b'"
    assert (
        helper._target_key(a)
        == helper._target_key(b)
        != helper._target_key("host=h port=2 dbname=d user=u")
    )


@needs_pg
def test_a_test_role_left_by_a_killed_process_is_swept_and_a_live_one_is_not(scratch):
    """Three roles named like the helper's: one stale (nobody holds its process lock, no session), one with a live
    session, one whose process lock is held. Only the stale one, and what it owns, is dropped. Killed by: mutants SW1
    (the sweep is not called when the role is made), SW2 (a role with a session is dropped) and SW3 (a role whose lock is
    held is dropped)."""
    stale, live, held = (f"hadavin_test_migrator_{uuid.uuid4().hex[:8]}" for _ in range(3))
    schema = conninfo_to_dict(scratch[0])["options"].rsplit("search_path=", 1)[1]
    with psycopg.connect(DSN, autocommit=True) as db:
        passwords = {r: create_login_role(db, r) for r in (stale, live, held)}
        db.execute(
            sql.SQL("CREATE TABLE {}.{} (a int)").format(
                sql.Identifier(schema), sql.Identifier("hadavin_test_stale_tbl")
            )
        )
        db.execute(
            sql.SQL("ALTER TABLE {}.{} OWNER TO {}").format(
                sql.Identifier(schema),
                sql.Identifier("hadavin_test_stale_tbl"),
                sql.Identifier(stale),
            )
        )
    with (
        psycopg.connect(
            make_conninfo(DSN, user=live, password=passwords[live]), autocommit=True
        ) as session,
        psycopg.connect(DSN, autocommit=True) as holder,
    ):
        holder.execute("SELECT pg_advisory_lock(%s)", (helper._mark_key(held.rsplit("_", 1)[1]),))
        session.execute("SELECT 1")
        with psycopg.connect(DSN, autocommit=True) as db:
            dropped = helper.sweep_stale_roles(db)
            assert stale in dropped and live not in dropped and held not in dropped, dropped
            assert PLAIN_ROLE not in dropped
            assert not _role_exists(stale) and _role_exists(live) and _role_exists(held)
            assert not db.execute(
                "SELECT 1 FROM pg_class WHERE relname = 'hadavin_test_stale_tbl'"
            ).fetchone(), "what the stale role owned went with it"
    _drop_roles(*[r for r in (live, held, stale) if _role_exists(r)])


@contextlib.contextmanager
def _databases_and_a_stale_role(count: int = 2):
    """Throwaway databases (`count` names) and a role named like the helper's, made as the test login; everything is
    dropped afterwards (the databases with FORCE), and a failure of the cleanup is not allowed to hide a failure of the
    test. Yields (role, [database names])."""
    name = f"hadavin_test_migrator_{uuid.uuid4().hex[:8]}"
    names = [f"hadavin_test_db_{uuid.uuid4().hex[:8]}" for _ in range(count)]
    made = []
    try:
        with psycopg.connect(DSN, autocommit=True) as admin:
            create_login_role(admin, name)
            try:
                for d in names:
                    admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(d)))
                    made.append(d)
            except psycopg.errors.InsufficientPrivilege:
                pytest.fail(
                    "TEST SETUP PROBLEM: this test needs CREATEDB on the HADAVIN_TEST_PG_DSN login"
                )
        yield name, names
    finally:
        _clean_up(
            [
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(d))
                for d in made
            ]
            + [
                sql.SQL("DROP OWNED BY {}").format(sql.Identifier(name)),
                sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(name)),
            ]
        )


def _clean_up(statements) -> None:
    """Run each statement of a cleanup on its own, so that one that fails does not skip the others, and say in ONE line
    what failed (a failed cleanup must not hide the failure of the test, and must not stay silent either)."""
    failed = []
    for statement in statements:
        try:
            with psycopg.connect(DSN, autocommit=True) as admin:
                admin.execute(statement)
        except psycopg.Error as e:
            failed.append(type(e).__name__)
    if failed:
        print(
            "cleanup of a test failed in "
            + str(len(failed))
            + " statement(s): "
            + ", ".join(failed)
        )


@needs_pg
def test_a_role_held_from_one_database_is_not_swept_from_another_database_of_the_server(
    monkeypatch,
):
    """A role belongs to the whole server, an advisory lock to one database. The live process holds its mark from
    database X; a second test process sweeps from database Y of the same server: its try-lock on Y succeeds, so only
    the connection named like the role keeps the role. Killed by: mutant SW7 (the sweep does not look at the name of
    the connections)."""
    monkeypatch.setattr(helper, "_MARKS", {})
    with (
        _databases_and_a_stale_role() as (name, (db_x, db_y)),
        psycopg.connect(make_conninfo(DSN, dbname=db_x), autocommit=True) as in_x,
        psycopg.connect(make_conninfo(DSN, dbname=db_y), autocommit=True) as in_y,
    ):
        with monkeypatch.context() as as_that_process:  # only the hold is made as the other process
            as_that_process.setattr(helper, "_TOKEN", name.rsplit("_", 1)[1])
            as_that_process.setattr(helper, "PLAIN_ROLE", name)
            helper._mark_the_role(in_x)
        try:
            assert name not in helper.sweep_stale_roles(in_y), "a live process's role was dropped"
            assert _role_exists(name)
        finally:
            helper._close_the_marks()
        for _ in range(100):  # the server ends the closed session a moment later
            if name in helper.sweep_stale_roles(in_y):
                break
            time.sleep(0.05)
        else:
            pytest.fail(
                "TEST SETUP PROBLEM: the server did not end the closed marking connection in 5 s, so the role never looked stale"
            )


@needs_pg
def test_a_stale_role_that_owns_objects_in_another_database_is_left_and_the_databases_are_named(
    capsys,
):
    """DROP OWNED works in one database; the role owns a schema in database X, the sweep runs in Y. The role stays, and
    the one line names X. Killed by: mutant SW14 (the databases are not named)."""
    with _databases_and_a_stale_role() as (name, (db_x, db_y)):
        with psycopg.connect(make_conninfo(DSN, dbname=db_x), autocommit=True) as in_x:
            in_x.execute(
                sql.SQL("CREATE SCHEMA hadavin_test_owned AUTHORIZATION {}").format(
                    sql.Identifier(name)
                )
            )
        in_y_dsn = make_conninfo(DSN, dbname=db_y)
        with psycopg.connect(in_y_dsn, autocommit=True) as in_y:
            assert name not in helper.sweep_stale_roles(in_y)
        assert _role_exists(name)
        out = capsys.readouterr().out
        assert name in out and db_x in out and db_y not in out, out


@needs_pg
def test_a_role_that_owns_a_schema_that_is_not_a_scratch_schema_is_not_swept():
    """A role named like the helper's but made by a person, owning a real schema, is not dropped with what it owns.
    Killed by: mutant SW13 (the schemas the role owns are not looked at)."""
    with (
        _databases_and_a_stale_role(1) as (name, (db_x,)),
        psycopg.connect(make_conninfo(DSN, dbname=db_x), autocommit=True) as in_x,
    ):
        in_x.execute(
            sql.SQL("CREATE SCHEMA real_data AUTHORIZATION {}").format(sql.Identifier(name))
        )
        assert name not in helper.sweep_stale_roles(in_x)
        assert _role_exists(name)
        in_x.execute("DROP SCHEMA real_data")
        assert name in helper.sweep_stale_roles(in_x), "without it the role is swept"


@needs_pg
def test_a_login_that_cannot_see_other_sessions_sweeps_nothing_on_a_real_server():
    """A plain login sees no `application_name` of other users, so a live role could look unused: nothing is swept.
    Killed by: mutant SW11 (the right is not asked)."""
    with _databases_and_a_stale_role(1) as (name, _):
        with psycopg.connect(DSN, autocommit=True) as admin:
            plain = f"hadavin_test_pl_{uuid.uuid4().hex[:8]}"
            create_login_role(admin, plain)
        try:
            with psycopg.connect(login_dsn(DSN, plain), autocommit=True) as db:
                assert helper.sweep_stale_roles(db) == []
            assert _role_exists(name), (
                "the stale role was left alone by a login that cannot see sessions"
            )
        finally:
            _drop_roles(plain)


@needs_pg
def test_the_exit_hook_drops_what_the_role_owns_in_every_used_database_and_then_the_role(
    monkeypatch, capsys
):
    """The role owns a schema in each of two databases: dropping it database by database fails with a false "not
    dropped" line. The hook drops what it owns everywhere first and the role once. Killed by: mutant SW15 (only the
    first database is cleaned)."""
    with _databases_and_a_stale_role() as (name, (db_x, db_y)):
        targets = set()
        for d in (db_x, db_y):
            with psycopg.connect(make_conninfo(DSN, dbname=d), autocommit=True) as db:
                db.execute(
                    sql.SQL("CREATE SCHEMA hadavin_test_owned AUTHORIZATION {}").format(
                        sql.Identifier(name)
                    )
                )
            targets.add(helper._target_key(make_conninfo(DSN, dbname=d)))
        monkeypatch.setattr(helper, "PLAIN_ROLE", name)
        monkeypatch.setattr(helper, "_USED_DSNS", targets)
        monkeypatch.delenv("HADAVIN_TEST_PG_DSN", raising=False)
        helper._drop_the_role_at_exit()
        assert not _role_exists(name)
        assert "was not dropped" not in capsys.readouterr().out


# --- role changes made by ANOTHER session while a file runs ---------------------------------------------------------


_SLOW_START_LIMIT = (
    3.0  # seconds; the run's own lock_timeout is 5 s (see `migrate`), this leaves a margin
)


def _after_the_file_starts(marker: str, key: int, statements: list[str]):
    """The file waits on an advisory lock (`_slow_file`) that this call takes first, on a connection of its own. A second
    session (the superuser login) waits until a backend running the file is really blocked on that lock, runs
    `statements`, and only then releases the lock, so the file ends after the changes (the order is recorded in `order`
    and the tests assert it). Returns (thread, done event, errors, order, gate connection to close)."""
    gate = psycopg.connect(DSN, autocommit=True)
    gate.execute("SELECT pg_advisory_lock(%s)", (key,))
    done, errors, order = threading.Event(), [], []
    started = time.monotonic()

    def work():
        try:
            with psycopg.connect(DSN, autocommit=True) as db:
                for _ in range(600):
                    if db.execute(
                        "SELECT count(*) FROM pg_stat_activity WHERE query LIKE %s AND wait_event_type = 'Lock' "
                        "AND wait_event = 'advisory' AND pid <> pg_backend_pid()",
                        (f"%{marker}%",),
                    ).fetchone()[0]:
                        break
                    time.sleep(0.05)
                else:
                    raise AssertionError("TEST SETUP PROBLEM: the file never started waiting")
                waited = time.monotonic() - started
                if waited > _SLOW_START_LIMIT:
                    raise AssertionError(
                        f"TEST SETUP PROBLEM, a timing flake and not a defect: the file started waiting after {waited:.1f} s and the run's own "
                        f"lock_timeout is 5 s, so the run may stop on that before this test changes anything; run the "
                        "test again on a quiet machine"
                    )
                order.append("file_is_waiting")
                for statement in statements:
                    db.execute(statement)
                order.append("roles_changed")
            gate.execute("SELECT pg_advisory_unlock(%s)", (key,))
            order.append("file_released")
        except (psycopg.Error, AssertionError) as e:  # reported by the test
            errors.append(e)
            gate.close()  # never leave the file waiting
        finally:
            done.set()

    thread = threading.Thread(target=work, daemon=True)
    thread.start()
    return thread, done, errors, order, gate


def _slow_file(monkeypatch, tmp_path) -> tuple[str, int]:
    marker = "marker_" + uuid.uuid4().hex
    key = uuid.uuid4().int % (2**62)
    _with_files(
        monkeypatch,
        tmp_path,
        {"0006_slow.sql": f"SELECT pg_advisory_xact_lock({key}); -- {marker}\n"},
    )
    return marker, key


_ORDER = ["file_is_waiting", "roles_changed", "file_released"]


@needs_pg
def test_another_session_changing_unrelated_roles_does_not_stop_the_run(
    scratch, monkeypatch, tmp_path
):
    """The server holds every role: while the file runs, another session makes roles, grants one to the other and saves a
    setting for a role that has nothing to do with the migration user. That is not a change to the migration user's
    rights, so the run goes on. Killed by: mutants SC1 (the members query reads the whole server) and SC2 (the settings
    query reads the whole server)."""
    dsn, _ = scratch
    x, y = "hadavin_test_ux_" + uuid.uuid4().hex[:8], "hadavin_test_uy_" + uuid.uuid4().hex[:8]
    mig.migrate(dsn)
    marker, key = _slow_file(monkeypatch, tmp_path)
    thread, done, errors, order, gate = _after_the_file_starts(
        marker,
        key,
        [
            f'CREATE ROLE "{x}"',
            f'CREATE ROLE "{y}"',
            f'GRANT "{x}" TO "{y}"',
            f"ALTER ROLE \"{x}\" SET work_mem = '5MB'",
        ],
    )
    try:
        assert mig.migrate(dsn) == ["0006_slow"]
        assert done.wait(10) and not errors, errors
        assert order == _ORDER, order
        with psycopg.connect(
            DSN, autocommit=True
        ) as db:  # the other session really did change the roles
            assert db.execute("SELECT pg_has_role(%s, %s, 'MEMBER')", (y, x)).fetchone() == (True,)
    finally:
        thread.join(10)
        gate.close()
        _drop_roles(*[r for r in (y, x) if _role_exists(r)])


def _role_exists(role: str) -> bool:
    with psycopg.connect(DSN, autocommit=True) as db:
        return (
            db.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (role,)).fetchone() is not None
        )


@needs_pg
@pytest.mark.parametrize("what", ["membership", "saved_setting"])
def test_another_session_changing_the_migration_users_own_roles_stops_the_run(
    scratch, monkeypatch, tmp_path, what
):
    """A change to the migration user's own membership or saved settings while the file runs is refused, with the words
    that it may be another session; nothing is kept. Killed by: mutants SC3 (the scope is empty) and SC4 (the new
    message is gone)."""
    dsn, _ = scratch
    a = "hadavin_test_sa_" + uuid.uuid4().hex[:8]
    _create_roles(a)
    mig.migrate(dsn)
    marker, key = _slow_file(monkeypatch, tmp_path)
    statement = (
        f'GRANT "{a}" TO "{PLAIN_ROLE}"'
        if what == "membership"
        else f"ALTER ROLE \"{PLAIN_ROLE}\" SET work_mem = '5MB'"
    )
    thread, done, errors, order, gate = _after_the_file_starts(marker, key, [statement])
    try:
        with pytest.raises(ConfigError) as e:
            mig.migrate(dsn)
        msg = str(e.value)
        assert done.wait(10) and not errors, errors
        assert order == _ORDER, order
        assert "0006_slow.sql" in msg, msg
        if what == "membership":
            assert (
                "a role membership changed while the file ran (it may be another session; run migrate again)"
                in msg
            ), msg
            assert f"role {a} has a new member {PLAIN_ROLE}" in msg, msg
        else:
            assert f"saved setting in every database for role {PLAIN_ROLE} is new" in msg, msg
        assert _ledger(dsn) == REAL, "nothing of the run was kept"
    finally:
        thread.join(10)
        gate.close()
        with psycopg.connect(DSN, autocommit=True) as db:
            db.execute(sql.SQL("ALTER ROLE {} RESET work_mem").format(sql.Identifier(PLAIN_ROLE)))
        _drop_roles(a)


@needs_pg
@pytest.mark.parametrize("what", ["membership", "saved_setting"])
def test_another_session_changing_a_role_that_a_named_role_belongs_to_stops_the_run(
    scratch, monkeypatch, tmp_path, what
):
    """The runtime role N is a member of role Y, and the migration user has nothing to do with Y. While the file runs,
    a second session gives Y another role (or saves a setting for Y): N can now use that, so the run is refused.
    Killed by: mutant NR1 (the roles a named role belongs to are left out of the scope)."""
    dsn, _ = scratch
    n, y, p_ = (f"hadavin_test_{t}_" + uuid.uuid4().hex[:8] for t in ("nn", "yy", "pp"))
    _create_roles(n, y, p_)
    with psycopg.connect(DSN, autocommit=True) as db:
        db.execute(sql.SQL("GRANT {} TO {}").format(sql.Identifier(y), sql.Identifier(n)))
    mig.migrate(dsn)
    marker, key = _slow_file(monkeypatch, tmp_path)
    statement = (
        f'GRANT "{p_}" TO "{y}"'
        if what == "membership"
        else f"ALTER ROLE \"{y}\" SET work_mem = '5MB'"
    )
    thread, done, errors, order, gate = _after_the_file_starts(marker, key, [statement])
    try:
        with pytest.raises(ConfigError) as e:
            mig.migrate(dsn, runtime_role=n)
        msg = str(e.value)
        assert done.wait(10) and not errors, errors
        assert order == _ORDER, order
        assert "0006_slow.sql" in msg, msg
        if what == "membership":
            assert "a role membership changed while the file ran" in msg and y in msg, msg
        else:
            assert f"role {y} is new" in msg, msg
        assert _ledger(dsn) == REAL, "nothing of the run was kept"
    finally:
        thread.join(10)
        gate.close()
        _drop_roles(*[r for r in (y, n, p_) if _role_exists(r)])


@needs_pg
def test_a_new_member_of_a_named_role_stops_the_run(scratch, monkeypatch, tmp_path):
    """The runtime role N belongs to nobody the migration user belongs to. While the file runs, a second session makes
    another role Z a member of N: Z can now do what N can, so the run is refused. Killed by: mutant NM1 (the named
    roles are not `own` in the members read-back)."""
    dsn, _ = scratch
    n, z = (f"hadavin_test_{t}_" + uuid.uuid4().hex[:8] for t in ("nm", "zz"))
    _create_roles(n, z)
    mig.migrate(dsn)
    marker, key = _slow_file(monkeypatch, tmp_path)
    thread, done, errors, order, gate = _after_the_file_starts(
        marker, key, [f'GRANT "{n}" TO "{z}"']
    )
    try:
        with pytest.raises(ConfigError) as e:
            mig.migrate(dsn, runtime_role=n)
        assert done.wait(10) and not errors, errors
        assert order == _ORDER, order
        assert "has a new member" in str(e.value) and z in str(e.value), str(e.value)
        assert _ledger(dsn) == REAL, "nothing of the run was kept"
    finally:
        thread.join(10)
        gate.close()
        _drop_roles(*[r for r in (z, n) if _role_exists(r)])


@needs_pg
@pytest.mark.parametrize("sql_text", ["members", "settings"])
def test_a_superuser_among_the_named_roles_does_not_widen_the_read_back(sql_text):
    """A superuser is a member of every role, so a superuser in the list of named roles would put the whole server in the
    compared set and an unrelated change would stop the run. The named set leaves superusers out. Killed by: mutant NS1
    (members read-back; the settings read-back has the same line and is covered by the same test)."""
    boss, me, x, y = (f"hadavin_test_{t}_" + uuid.uuid4().hex[:8] for t in ("bs", "me", "ux", "uy"))
    with psycopg.connect(DSN, autocommit=True) as db:
        db.execute(sql.SQL("CREATE ROLE {} SUPERUSER").format(sql.Identifier(boss)))
        password = create_login_role(
            db, me
        )  # the session is a plain login, as the migration user is
        _create_roles(x, y)
        db.execute(sql.SQL("GRANT {} TO {}").format(sql.Identifier(x), sql.Identifier(y)))
        db.execute(sql.SQL("ALTER ROLE {} SET work_mem = '5MB'").format(sql.Identifier(x)))
    try:
        query = mig._READBACK_MEMBERS_SQL if sql_text == "members" else mig._READBACK_SETTINGS_SQL
        with psycopg.connect(make_conninfo(DSN, user=me, password=password)) as db:
            rows = db.execute(query, ([boss],)).fetchall()
        text = " ".join(str(c) for row in rows for c in row)
        assert x not in text and y not in text, rows
    finally:
        _drop_roles(*[r for r in (boss, me, y, x) if _role_exists(r)])


@needs_pg
@pytest.mark.parametrize(
    "how, expected",
    [
        ("column_update_via_group", "can use it through the role"),
        ("select_on_the_ledger", "schema_migrations: "),
        ("create_in_the_schema", " has CREATE"),
    ],
)
def test_the_portal_role_is_refused_what_the_other_roles_are_refused(scratch, how, expected):
    """The portal role gets the same scan as the runtime and purge roles (`verify`): a right on one column
    that comes through a group role, SELECT on the migration ledger (not in the portal map), and CREATE on the schema.
    The old check read table rights only. Killed by: no list mutant today; it guards the refusal of the portal role (the three cases here are outside both maps)."""
    dsn, schema = scratch
    pt, group = (f"hadavin_test_{t}_" + uuid.uuid4().hex[:8] for t in ("pt", "gr"))
    _create_roles(pt, group)
    mig.migrate(dsn)
    q = sql.Identifier(schema)
    with psycopg.connect(DSN, autocommit=True) as db:
        if how == "column_update_via_group":
            db.execute(
                sql.SQL("GRANT UPDATE (state) ON {}.runs TO {}").format(q, sql.Identifier(group))
            )
            db.execute(sql.SQL("GRANT {} TO {}").format(sql.Identifier(group), sql.Identifier(pt)))
        elif how == "select_on_the_ledger":
            db.execute(
                sql.SQL("GRANT SELECT ON {}.schema_migrations TO {}").format(q, sql.Identifier(pt))
            )
        else:
            db.execute(sql.SQL("GRANT CREATE ON SCHEMA {} TO {}").format(q, sql.Identifier(pt)))
    try:
        with pytest.raises(ConfigError) as e:
            mig.migrate(dsn, portal_role=pt)
        msg = str(e.value)
        assert "rights that the grant map does not give" in msg, msg
        assert expected in msg, msg
        assert _ledger(dsn) == REAL, "nothing was kept"
    finally:
        _drop_roles(*[r for r in (pt, group) if _role_exists(r)])


# --- parameter grants held through a role the migration user belongs to ----------------------------------------------


@needs_pg
@pytest.mark.real_connect
@pytest.mark.parametrize("privilege", ["SET", "ALTER SYSTEM"])
@pytest.mark.parametrize("via", ["direct", "session_user", "member_inherit", "member_noinherit"])
def test_a_parameter_grant_is_refused_however_the_migration_user_holds_it(
    plain_role, scratch, privilege, via
):
    """The grant sits on the migration user, on the session user (the login that switched to another role), on a role it
    belongs to and inherits, or on a role it belongs to WITHOUT inheriting (it can still `SET ROLE` to it). Killed by:
    mutants PA2 (the ALTER SYSTEM half is gone), PA3 (the session user is not asked) and PA4 (only the user itself)."""
    dsn, role = plain_role
    super_dsn, schema = scratch
    holder = role
    other = role + "_g"
    with psycopg.connect(DSN, autocommit=True) as db:
        db.execute(sql.SQL("CREATE ROLE {}").format(sql.Identifier(other)))
        if via.startswith("member"):
            holder = other
            db.execute(
                sql.SQL(
                    f"GRANT {{}} TO {{}} WITH INHERIT {'TRUE' if via.endswith('_inherit') else 'FALSE'}"
                ).format(sql.Identifier(other), sql.Identifier(role))
            )
        if via == "session_user":
            db.execute(
                sql.SQL("GRANT {} TO {}").format(sql.Identifier(other), sql.Identifier(role))
            )
            db.execute(  # see test_the_session_user_is_checked_for_membership_too: a run that is not refused must go on
                sql.SQL("GRANT ALL ON SCHEMA {} TO {}").format(
                    sql.Identifier(schema), sql.Identifier(other)
                )
            )
            dsn = login_dsn(
                super_dsn,
                role,
                options=conninfo_to_dict(super_dsn)["options"] + f" -c role={other}",
            )
        db.execute(
            sql.SQL(f"GRANT {privilege} ON PARAMETER work_mem TO {{}}").format(
                sql.Identifier(holder)
            )
        )
    try:
        with pytest.raises(ConfigError, match="server settings it must not change") as e:
            mig.migrate(dsn)
        assert "work_mem" in str(e.value)
        assert _ledger(dsn) is None, "nothing was created"
    finally:
        with psycopg.connect(DSN, autocommit=True) as db:
            db.execute(
                sql.SQL(f"REVOKE {privilege} ON PARAMETER work_mem FROM {{}}").format(
                    sql.Identifier(holder)
                )
            )
            db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(other)))
            db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(other)))


# --- the exemption for the database owner role, zero-argument aggregates and owned sequences --------------------------


@needs_pg
@pytest.mark.real_connect
def test_the_owner_of_a_database_belongs_to_pg_database_owner_and_is_not_refused(scratch):
    """The one built-in role that is allowed: the owner of a database is implicitly a member of `pg_database_owner`.
    Killed by: mutant DO1 (the exemption is gone)."""
    super_dsn, _ = scratch
    suffix = uuid.uuid4().hex[:8]
    role, database = f"hadavin_test_dbo_{suffix}", f"hadavin_test_db_{suffix}"
    try:  # opened before anything is made, so a failure half way still cleans up
        with psycopg.connect(DSN, autocommit=True) as db:
            password = create_login_role(db, role)
            db.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(database), sql.Identifier(role)
                )
            )
        dsn = make_conninfo(super_dsn, user=role, password=password, dbname=database, options="")
        assert mig.migrate(dsn) == REAL
    finally:
        _clean_up(
            [
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(database)),
                sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(role)),
            ]
        )


@needs_pg
@pytest.mark.real_connect
def test_an_aggregate_with_no_arguments_is_revoked_with_empty_brackets(
    scratch, plain_role, tmp_path
):
    """The server names the arguments of an aggregate with none `*`; GRANT, REVOKE and ALTER ROUTINE write `()` for it
    (`(*)` is a syntax error there). The aggregate keeps the default right for everyone; the printed REVOKE must run.
    Old name: `test_an_aggregate_with_no_arguments_is_printed_with_a_star`. Killed by: V10.
    Re-pointed in commit 3b: the new check (ticket P3a-2, 3.4 line 3) does not judge the default right for everyone on a
    function that ANOTHER role owns, so the old test (a superuser made the aggregate) no longer reached a refusal; the
    migration role makes the aggregate now, which is the case the rule still refuses."""
    dsn, _role = plain_role
    _super_dsn, schema = scratch
    with psycopg.connect(dsn, autocommit=True) as db:
        db.execute(
            "CREATE AGGREGATE hadavin_test_zero_agg(*) (sfunc = int8inc, stype = int8, initcond = '0')"
        )
    with pytest.raises(ConfigError) as e:
        mig.migrate(dsn)
    text = str(e.value)
    statements = re.findall(r"To remove: (REVOKE EXECUTE ON ROUTINE [^;]*;)", text)
    assert len(statements) == 1 and '"hadavin_test_zero_agg"()' in statements[0], (
        text
    )  # names are quoted now
    assert "(*)" not in statements[0]
    done = _psql(schema, tmp_path, *statements)
    assert done.returncode == 0, done.stderr
    assert mig.migrate(dsn) == REAL


@needs_pg
@pytest.mark.real_connect
def test_a_sequence_that_belongs_to_a_table_column_is_not_listed_on_its_own(scratch, plain_role):
    """The tables belong to the old login and so do their serial sequences; the sequences go with their tables, so only the
    tables are listed (one `ALTER TABLE ... OWNER TO` moves a column's sequence too). Killed by: mutant OS1."""
    dsn, _role = plain_role
    super_dsn, _ = scratch
    _build_as_the_superuser(super_dsn)
    with pytest.raises(ConfigError) as e:
        mig.migrate(dsn)
    msg = str(e.value)
    assert "approval_decisions" in msg and "ALTER TABLE" in msg, msg
    assert "approval_decisions_seq_seq" not in msg and "ALTER SEQUENCE" not in msg, msg


# --- the SQL the refusal prints: CREATE needs no grant option ----------------------------------------------------------


@needs_pg
@pytest.mark.real_connect
def test_the_printed_role_may_pass_usage_on_but_not_create(scratch):
    """The migration role passes USAGE on to the runtime and portal roles, so only USAGE carries the grant option; CREATE
    is held without it (a role that can pass CREATE on could let another role make objects in the schema). Killed by:
    mutant PR1 (the grant option is on both)."""
    _dsn, schema = scratch
    role, rt, pt = _role_from_the_printed_sql(schema, grant_option=True)
    try:
        with psycopg.connect(DSN, autocommit=True) as db:
            q = "SELECT has_schema_privilege(%s, %s, %s)"
            assert db.execute(q, (role, schema, "USAGE WITH GRANT OPTION")).fetchone() == (True,)
            assert db.execute(q, (role, schema, "CREATE")).fetchone() == (True,)
            assert db.execute(q, (role, schema, "CREATE WITH GRANT OPTION")).fetchone() == (False,)
    finally:
        _drop_all(role, rt, pt)


# --- the test role of a process is gone when the process ends -------------------------------------------------------------


@needs_pg
def test_the_plain_test_role_and_what_it_owns_are_dropped_when_the_process_exits():
    """A child process makes the role (the way `plain_role_connect` does), lets it own a schema with a table, and exits
    normally; the exit hook takes the role off the server. Killed by: mutant TR1 (the hook does nothing)."""
    import multiprocessing

    from tests.fixtures.role_child import make_the_role_and_own_a_schema

    schema = f"hadavin_test_exit_{uuid.uuid4().hex[:8]}"
    context = multiprocessing.get_context(
        "spawn"
    )  # a fresh interpreter that ends normally, so its exit hooks run
    names = context.Queue()
    child = context.Process(target=make_the_role_and_own_a_schema, args=(DSN, schema, names))
    child.start()
    role = names.get(timeout=60)
    child.join(60)
    assert child.exitcode == 0, child.exitcode
    try:
        assert role.startswith("hadavin_test_migrator_")
        assert not _role_exists(role), "the role is still on the server"
        with psycopg.connect(DSN, autocommit=True) as db:
            assert (
                db.execute("SELECT 1 FROM pg_namespace WHERE nspname = %s", (schema,)).fetchone()
                is None
            ), "what the role owned is still there"
    finally:
        with psycopg.connect(DSN, autocommit=True) as db:
            db.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema)))
            if _role_exists(role):
                db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


# --- rights read back for every role (round 9): a right for a role the run does not name is refused --------------


def _acl_of(dsn, schema: str, relation: str) -> list[str]:
    with psycopg.connect(dsn, autocommit=True) as db:
        return [
            r[0]
            for r in db.execute(
                "SELECT (aclexplode(c.relacl)).grantee::regrole::text FROM pg_class c "
                "JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = %s AND c.relname = %s",
                (schema, relation),
            )
        ]


@needs_pg
@pytest.mark.parametrize(
    "grant",
    [
        "GRANT SELECT ON audit_entries TO {other};",
        "GRANT SELECT ON audit_entries TO PUBLIC;",
        "GRANT SELECT (seq) ON audit_entries TO {other};",
        "GRANT USAGE ON SEQUENCE approval_decisions_seq_seq TO {other};",
        "GRANT EXECUTE ON FUNCTION hadavin_audit_append_only() TO {other};",
    ],
)
@pytest.mark.parametrize("with_roles", [False, True])
def test_a_right_for_a_role_the_run_does_not_name_is_refused(
    scratch, monkeypatch, tmp_path, grant, with_roles
):
    """A file may hold `GRANT ... ON ... TO <any role>`; nothing used to read the rights back for roles other than the
    three of the run. Now a right for a third role or for PUBLIC (relation, column, sequence, function), with or without
    role arguments, is refused in plain words and nothing is kept. Killed by: mutants AC1 (relation rights not read),
    AC2 (column rights not read), AC3 (function rights not read), AC4 (PUBLIC or any role is allowed)."""
    dsn, _schema = scratch
    other = "hadavin_test_ac_" + uuid.uuid4().hex[:8]
    _create_roles(other)
    try:
        _with_files(monkeypatch, tmp_path, {"0006_grant.sql": grant.format(other=other) + "\n"})
        roles = {}
        if with_roles:
            run_as = "hadavin_test_ac_rt_" + uuid.uuid4().hex[:6]
            _create_roles(run_as)
            roles = {"runtime_role": run_as}
        try:
            with pytest.raises(ConfigError, match="rights that the grant map does not give") as e:
                mig.migrate(dsn, **roles)
            text = str(e.value)
            assert _kept_nothing(text)
            # Re-pointed in commit 3b: step 4 removes the default right for everyone from the function a file names
            # BEFORE the last check, so a function line never says "everyone (PUBLIC) has" any more (the function case
            # for PUBLIC has its own test below); a relation line still does.
            assert ("everyone (PUBLIC) has" in text) == ("PUBLIC" in grant)
            assert (f"{other} has" in text) == ("{other}" in grant)
            assert "0006_grant" not in (_ledger(dsn) or [])
        finally:
            if with_roles:
                _drop_roles(roles["runtime_role"])
    finally:
        _drop_roles(other)


@needs_pg
@pytest.mark.parametrize("with_roles", [False, True])
def test_a_file_that_grants_execute_on_its_function_to_everyone_leaves_nobody_but_the_owner(
    scratch, monkeypatch, tmp_path, with_roles
):
    """Split out of `test_a_right_for_a_role_the_run_does_not_name_is_refused` in commit 3b. The old test expected a
    refusal for `GRANT EXECUTE ON FUNCTION <package function> TO PUBLIC`. The new order removes everyone's right to
    execute from every function the files name (step 4) BEFORE the last check, and an explicit grant to PUBLIC is the same
    entry as the default, so the run ends clean: the run returns, the file is in the ledger and the function has no
    right for everyone. What still counts is the final state, which is asserted on the server."""
    dsn, schema = scratch
    _with_files(
        monkeypatch,
        tmp_path,
        {"0006_grant.sql": "GRANT EXECUTE ON FUNCTION hadavin_audit_append_only() TO PUBLIC;\n"},
    )
    roles = {}
    if with_roles:
        roles = {"runtime_role": "hadavin_test_ac_rt_" + uuid.uuid4().hex[:6]}
        _create_roles(roles["runtime_role"])
    try:
        assert "0006_grant" in mig.migrate(dsn, **roles)
        assert "0006_grant" in (_ledger(dsn) or [])
        with psycopg.connect(dsn, autocommit=True) as db:
            everyone = db.execute(
                "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace, "
                "aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) a "
                "WHERE n.nspname = %s AND p.proname = 'hadavin_audit_append_only' AND a.grantee = 0",
                (schema,),
            ).fetchone()[0]
        assert everyone == 0
    finally:
        if with_roles:
            _drop_roles(roles["runtime_role"])


@needs_pg
def test_the_named_roles_and_the_owner_may_hold_rights_and_a_function_loses_the_default_for_everyone(
    scratch,
):
    """The three named roles keep what the grant map gives; the default right 'everyone may call it' of the trigger
    function is removed (only the owner stays). Killed by: mutant AC5 (the default is not removed)."""
    dsn, schema = scratch
    run_as = "hadavin_test_ac_ok_" + uuid.uuid4().hex[:6]
    _create_roles(run_as)
    try:
        assert mig.migrate(dsn, runtime_role=run_as) == REAL
        assert run_as in _acl_of(dsn, schema, "audit_entries")
        with psycopg.connect(dsn, autocommit=True) as db:
            acl = db.execute(
                "SELECT (aclexplode(p.proacl)).grantee FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
                "WHERE n.nspname = %s AND p.proname = 'hadavin_audit_append_only'",
                (schema,),
            ).fetchall()
        assert acl and all(g != 0 for (g,) in acl)
    finally:
        _drop_roles(run_as)


@needs_pg
def test_a_security_definer_function_is_refused_unless_a_reviewer_listed_it(
    scratch, monkeypatch, tmp_path
):
    """Such a function runs with the rights of its owner, the migration role. Refused unless its name is on
    `REVIEWED_DEFINER_FUNCTIONS`. Killed by: mutants SD1 (not read) and SD2 (the list is not read)."""
    dsn, _schema = scratch
    body = (
        "CREATE OR REPLACE FUNCTION hadavin_test_definer() RETURNS int LANGUAGE sql SECURITY DEFINER "
        "AS $$ SELECT 1 $$;\n"
    )
    _with_files(monkeypatch, tmp_path, {"0006_definer.sql": body})
    with pytest.raises(ConfigError, match="SECURITY DEFINER") as e:
        mig.migrate(dsn)
    assert "hadavin_test_definer" in str(e.value) and _kept_nothing(str(e.value))
    assert "0006_definer" not in (_ledger(dsn) or [])
    monkeypatch.setattr(
        mig, "REVIEWED_DEFINER_FUNCTIONS", frozenset({(mig.RUN_SCHEMA, "hadavin_test_definer", "")})
    )
    assert mig.migrate(dsn) == REAL + ["0006_definer"]


# --- the marking connection and the sweep guard (round 9) ----------------------------------------------------------


def _sessions_named(name: str) -> int:
    with psycopg.connect(DSN, autocommit=True) as db:
        return db.execute(
            "SELECT count(*) FROM pg_stat_activity WHERE application_name = %s AND datname = current_database()",
            (
                name,
            ),  # this database only: the marks of other databases of this process are not counted
        ).fetchone()[0]


@needs_pg
def test_a_marking_connection_that_died_is_opened_again_and_the_role_is_not_swept(
    scratch, monkeypatch
):
    """The marking connection can die (a restart, an idle limit, `pg_terminate_backend`); without it another test run
    would drop the role of this run while it is in use. The next connect opens it again. Killed by: mutant SW17 (a
    dead marking connection is kept)."""
    dsn, _schema = scratch
    connect = helper.plain_role_connect(
        lambda dsn, **k: psycopg.connect(dsn, autocommit=True, **k)  # as the store's `connect`
    )
    connect(dsn).close()
    assert _sessions_named(helper.PLAIN_ROLE) == 1, (
        "TEST SETUP PROBLEM: the marking connection of this run is not the one session of this database"
    )
    with psycopg.connect(DSN, autocommit=True) as admin:
        admin.execute(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE application_name = %s",
            (helper.PLAIN_ROLE,),
        )
    deadline = time.monotonic() + 10
    while _sessions_named(helper.PLAIN_ROLE) and time.monotonic() < deadline:
        time.sleep(0.05)
    assert _sessions_named(helper.PLAIN_ROLE) == 0, (
        "TEST SETUP PROBLEM: the server did not end the marking connection in 10 s"
    )
    connect(dsn).close()
    assert _sessions_named(helper.PLAIN_ROLE) == 1, (
        "the marking connection was not opened again"
    )  # a defect, not setup
    with monkeypatch.context() as other_run, psycopg.connect(DSN, autocommit=True) as admin:
        other_run.setattr(helper, "PLAIN_ROLE", "hadavin_test_migrator_" + uuid.uuid4().hex[:8])
        assert helper.PLAIN_ROLE not in helper.sweep_stale_roles(
            admin
        )  # a run that is not this one
    assert _role_exists(helper.PLAIN_ROLE)  # the role of this run is still there


_OWNED_OBJECTS = {
    "table": (
        "CREATE TABLE public.hadavin_real_t (id int)",
        "ALTER TABLE public.hadavin_real_t OWNER TO {}",
    ),
    "sequence": (  # has no row type, so only the relation clause can see it (a table is also seen by the type clause)
        "CREATE SEQUENCE public.hadavin_real_s",
        "ALTER SEQUENCE public.hadavin_real_s OWNER TO {}",
    ),
    "function": (
        "CREATE FUNCTION public.hadavin_real_f() RETURNS int LANGUAGE sql AS 'SELECT 1'",
        "ALTER FUNCTION public.hadavin_real_f() OWNER TO {}",
    ),
    "type": (
        "CREATE TYPE public.hadavin_real_ty AS ENUM ('a')",
        "ALTER TYPE public.hadavin_real_ty OWNER TO {}",
    ),
}


@needs_pg
@pytest.mark.parametrize("what", sorted(_OWNED_OBJECTS))
def test_a_role_that_owns_a_table_function_or_type_outside_a_scratch_schema_is_not_swept(what):
    """The guard looked at schemas only, but `DROP OWNED BY` also drops what a role owns inside a schema that it does not
    own, such as `public`. Now a role that owns any such object is left alone. Killed by: mutants SG1 (tables, views and sequences
    not looked at), SG2 (functions), SG3 (types)."""
    create, hand_over = _OWNED_OBJECTS[what]
    with (
        _databases_and_a_stale_role(1) as (name, (db_x,)),
        psycopg.connect(make_conninfo(DSN, dbname=db_x), autocommit=True) as in_x,
    ):
        in_x.execute(create)
        in_x.execute(sql.SQL(hand_over.replace("{}", "{r}")).format(r=sql.Identifier(name)))
        assert name not in helper.sweep_stale_roles(in_x)
        assert _role_exists(name)
        in_x.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(name)))
        assert name in helper.sweep_stale_roles(in_x), "without it the role is swept"


@needs_pg
def test_a_security_definer_function_made_by_dynamic_sql_is_found_by_what_is_new(
    scratch, monkeypatch, tmp_path, second_schema
):
    """The text rules read only a `CREATE FUNCTION` at the start of a statement; here a function body makes the
    function by `EXECUTE`, in a second schema (so no list of the run's own schema finds it). What is new in the database
    after the files is looked at too. Guards: new functions are found by what is new in the catalog, not by the file text (no list mutant today)."""
    dsn, _schema = scratch
    body = (
        "CREATE OR REPLACE FUNCTION hadavin_test_maker() RETURNS void LANGUAGE plpgsql AS $$ BEGIN "
        f"EXECUTE 'CREATE OR REPLACE FUNCTION \"{second_schema}\".hadavin_test_hidden() RETURNS int LANGUAGE sql SECURITY DEFINER AS $q$ SELECT 1 $q$'; "
        "END $$;\nSELECT hadavin_test_maker();\n"
    )
    _with_files(monkeypatch, tmp_path, {"0006_dynamic.sql": body})
    with pytest.raises(ConfigError, match="SECURITY DEFINER") as e:
        mig.migrate(dsn)
    assert "hadavin_test_hidden" in str(e.value)
    assert "0006_dynamic" not in (_ledger(dsn) or [])


@needs_pg
def test_a_run_that_cannot_get_the_migration_lock_gives_up_and_names_the_holder(scratch):
    """Any role that may connect can take the lock number and never let go. The run waits at most `lock_wait_seconds`,
    changes nothing, and names the session that holds the lock. Killed by: mutants LW1 (the wait is not limited, caught
    by the wiring test), LW2 (the holder is not named)."""
    dsn, _schema = scratch
    holder_name = "hadavin_test_lock_holder_" + uuid.uuid4().hex[:6]
    with psycopg.connect(
        make_conninfo(DSN, application_name=holder_name), autocommit=True
    ) as holder:
        holder.execute("SELECT pg_advisory_lock(%s)", (mig.MIGRATE_LOCK,))
        started = time.monotonic()
        with pytest.raises(ConfigError, match="waited 1 seconds for the migration lock") as e:
            mig.migrate(dsn, lock_wait_seconds=1)
        assert time.monotonic() - started < 30, (
            "TEST SETUP PROBLEM, a timing flake and not a defect: a 1 second wait took 30 s on this machine"
        )
        assert holder_name in str(e.value) and _kept_nothing(str(e.value))
    assert _ledger(dsn) is None, "nothing was made"
    assert mig.migrate(dsn) == REAL, "after the holder is gone the run goes through"


# --- rights that escaped the read-back in round 9 (round 10) ---------------------------------------------------------


@pytest.fixture
def second_schema():
    """A second schema in the same database that the migration role may create in (a database before PostgreSQL 15, or
    one where an administrator granted it)."""
    name = "hadavin_test_o_" + uuid.uuid4().hex[:10]
    with psycopg.connect(DSN, autocommit=True) as db:
        ensure_plain_role(db)  # the role exists also when a test runs alone
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(name)))
        db.execute(
            sql.SQL("GRANT USAGE, CREATE ON SCHEMA {} TO {}").format(
                sql.Identifier(name), sql.Identifier(PLAIN_ROLE)
            )
        )
    try:
        yield name
    finally:
        with psycopg.connect(DSN, autocommit=True) as db:
            db.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(name)))


@needs_pg
def test_a_security_definer_function_written_with_another_schema_is_made_owner_only_by_the_run(
    scratch, monkeypatch, tmp_path, second_schema
):
    """Old name: `test_a_security_definer_function_written_with_another_schema_is_refused`. Re-pointed in commit 3b
    (ticket P3a-2, rule S7): the old code refused a SECURITY DEFINER function that a file wrote with another schema
    before the dot because it was new. The new check judges who can CALL it: step 4 removes the default right of everyone
    to call a function that a file names, also in another schema, so only the owner can call it and rule S7 ("a function
    that a subject or everyone may execute") has nothing to refuse. The hidden form, where the file does not name the
    function (dynamic SQL), is the one that is still refused, by the test just above. Asserted on the server: the
    run returns, and nobody but the owner holds EXECUTE. Class: a read limited to one schema. Guards: a function in another schema (no list mutant today)."""
    dsn, _schema = scratch
    body = (
        f'CREATE OR REPLACE FUNCTION "{second_schema}".hadavin_test_f() RETURNS int LANGUAGE sql SECURITY DEFINER '
        "AS $$ SELECT 1 $$;\n"
    )
    _with_files(monkeypatch, tmp_path, {"0006_other_schema.sql": body})
    assert mig.migrate(dsn) == REAL + ["0006_other_schema"]
    with psycopg.connect(DSN, autocommit=True) as db:
        callers = db.execute(
            "SELECT a.grantee = 0, a.grantee = p.proowner FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace, "
            "aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) a "
            "WHERE n.nspname = %s AND p.proname = 'hadavin_test_f' AND p.prosecdef",
            (second_schema,),
        ).fetchall()
    assert callers and all(owner and not everyone for everyone, owner in callers), callers


@needs_pg
def test_a_plain_function_in_another_schema_loses_the_default_right_for_everyone(
    scratch, monkeypatch, tmp_path, second_schema
):
    """A function that a file makes in another schema is not SECURITY DEFINER here, but it still has the default
    'everyone may call it': that default is removed, as for the functions of the run's schema. Guards: a function in another schema (no list mutant today)."""
    dsn, _schema = scratch
    body = f'CREATE OR REPLACE FUNCTION "{second_schema}".hadavin_test_g() RETURNS int LANGUAGE sql AS $$ SELECT 1 $$;\n'
    _with_files(monkeypatch, tmp_path, {"0006_other_schema.sql": body})
    assert mig.migrate(dsn) == REAL + ["0006_other_schema"]
    with psycopg.connect(DSN, autocommit=True) as db:
        grantees = db.execute(
            "SELECT (aclexplode(p.proacl)).grantee FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
            "WHERE n.nspname = %s AND p.proname = 'hadavin_test_g'",
            (second_schema,),
        ).fetchall()
    assert grantees and all(g != 0 for (g,) in grantees)


@needs_pg
def test_a_function_replaced_with_the_same_id_and_made_security_definer_is_found(
    scratch, monkeypatch, tmp_path, second_schema
):
    """A function made by an earlier run (named in no file) keeps its id when a later file replaces it by dynamic SQL;
    what is compared is its state, not whether its id is new. Guards: a replaced function is found by its id (no list mutant today)."""
    dsn, _schema = scratch
    maker = (
        "CREATE OR REPLACE FUNCTION hadavin_test_maker2() RETURNS void LANGUAGE plpgsql AS $$ BEGIN "
        f"EXECUTE 'CREATE OR REPLACE FUNCTION \"{second_schema}\".hadavin_test_dyn() RETURNS int LANGUAGE sql AS $q$ SELECT 1 $q$'; "
        "END $$;\nSELECT hadavin_test_maker2();\n"
    )
    _with_files(monkeypatch, tmp_path, {"0006_first.sql": maker})
    assert mig.migrate(dsn) == REAL + ["0006_first"]
    again = (
        "CREATE OR REPLACE FUNCTION hadavin_test_maker3() RETURNS void LANGUAGE plpgsql AS $$ BEGIN "
        f"EXECUTE 'CREATE OR REPLACE FUNCTION \"{second_schema}\".hadavin_test_dyn() RETURNS int LANGUAGE sql SECURITY DEFINER AS $q$ SELECT 1 $q$'; "
        "END $$;\nSELECT hadavin_test_maker3();\n"
    )
    _with_files(monkeypatch, tmp_path, {"0007_second.sql": again})
    with pytest.raises(ConfigError, match="SECURITY DEFINER") as e:
        mig.migrate(dsn)
    assert "hadavin_test_dyn" in str(e.value)


@needs_pg
def test_a_table_made_by_dynamic_sql_and_opened_to_everyone_is_refused(
    scratch, monkeypatch, tmp_path
):
    """The text rules and the names in `GRANTS` do not see a table that a function body makes. What is new in the
    database after the files is read. Guards: new relations are read (no list mutant today)."""
    dsn, schema = scratch
    body = (
        "CREATE OR REPLACE FUNCTION hadavin_test_mk() RETURNS void LANGUAGE plpgsql AS $$ BEGIN "
        "EXECUTE 'CRE' || 'ATE TABLE hadavin_test_open (a int)'; "
        "EXECUTE 'GRANT SELECT ON hadavin_test_open TO PUBLIC'; END $$;\nSELECT hadavin_test_mk();\n"
    )
    _with_files(monkeypatch, tmp_path, {"0006_dyn_table.sql": body})
    with pytest.raises(
        ConfigError, match=f"table {schema}.hadavin_test_open: everyone \\(PUBLIC\\) has SELECT"
    ) as e:
        mig.migrate(dsn)
    assert _kept_nothing(str(e.value))
    assert _ledger(dsn) is None


@needs_pg
@pytest.mark.parametrize("scope", ["schema", "database"])
def test_a_default_right_that_an_administrator_set_is_refused_and_the_message_says_so(
    scratch, scope
):
    """`ALTER DEFAULT PRIVILEGES` of the migration role (for the schema, or for every schema) decides the rights of the
    tables made later, also outside `migrate`. A file cannot set it (refused by text), an administrator can; the
    read-back finds it and does not blame a file. Class: a right that is not on an existing object. Killed by:
    mutant DP1 (the default rights are not read)."""
    dsn, schema = scratch
    where = (
        sql.SQL("IN SCHEMA {} ").format(sql.Identifier(schema))
        if scope == "schema"
        else sql.SQL("")
    )
    role = sql.Identifier(PLAIN_ROLE)
    admin_sets = sql.SQL(
        "ALTER DEFAULT PRIVILEGES FOR ROLE {} {}GRANT SELECT ON TABLES TO PUBLIC"
    ).format(role, where)
    admin_undoes = sql.SQL(
        "ALTER DEFAULT PRIVILEGES FOR ROLE {} {}REVOKE SELECT ON TABLES FROM PUBLIC"
    ).format(role, where)
    with psycopg.connect(DSN, autocommit=True) as db:
        ensure_plain_role(db)  # the role exists also when this test runs alone
        db.execute(admin_sets)
    try:
        with pytest.raises(
            ConfigError, match="on every new (table|function|sequence|type) that"
        ) as e:
            mig.migrate(dsn)
        text = str(e.value)
        assert "everyone (PUBLIC) gets SELECT on every new table that" in text
        assert "a database administrator" in text and _kept_nothing(text)
        assert _ledger(dsn) is None
    finally:
        with psycopg.connect(DSN, autocommit=True) as db:
            db.execute(admin_undoes)
    assert mig.migrate(dsn) == REAL


@needs_pg
def test_a_file_that_sets_default_rights_or_changes_a_publication_is_refused_by_text(
    scratch, monkeypatch, tmp_path
):
    dsn, schema = scratch
    for name, body in {
        "0006_default.sql": f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} GRANT SELECT ON TABLES TO PUBLIC;\n",
        "0006_publication.sql": "ALTER PUBLICATION hadavin_pub ADD TABLE audit_entries;\n",
    }.items():
        with monkeypatch.context() as m:
            _with_files(m, tmp_path, {name: body})
            with pytest.raises(Exception, match="guard cannot read"):
                mig.migrate(dsn)


@needs_pg
@pytest.mark.parametrize("right", ["CREATE", "USAGE"])
def test_a_role_that_may_create_in_the_schema_is_refused_but_one_that_may_only_look_is_not(
    scratch, right
):
    """CREATE in the package schema lets a role plant a function that a role of this package then calls; the rights on
    the schema were never read. USAGE for everyone only lets a name be looked up, so it is not refused; USAGE for a third
    role is (commit 3b, see the comment in the test). Killed by: mutant SC1 (the schema rights are not read)."""
    dsn, schema = scratch
    other = "hadavin_test_sc_" + uuid.uuid4().hex[:8]
    _create_roles(other)
    try:
        with psycopg.connect(DSN, autocommit=True) as db:
            db.execute(
                sql.SQL(f"GRANT {right} ON SCHEMA {{}} TO {{}}").format(
                    sql.Identifier(schema), sql.Identifier(other)
                )
            )
        if right == "CREATE":
            with pytest.raises(
                ConfigError, match=f"schema {schema}: {other} has CREATE on the schema of the run"
            ) as e:
                mig.migrate(dsn)
            assert _kept_nothing(str(e.value)) and _ledger(dsn) is None
        else:
            # Re-pointed in commit 3b (ticket P3a-2, rule O1): the old test let a third role keep USAGE on the schema of
            # the run. The new check allows only the owner, the migration role and the named roles as grantees on the
            # schema, so a third role's USAGE is refused, with the line that names the role. Everyone's USAGE is the
            # one allowed exception (rule O2, the default of the `public` schema from PostgreSQL 15): it only lets a
            # name be looked up.
            with pytest.raises(ConfigError, match=f"schema {schema}: {other} has USAGE") as e:
                mig.migrate(dsn)
            assert _kept_nothing(str(e.value)) and _ledger(dsn) is None
            with psycopg.connect(DSN, autocommit=True) as db:
                db.execute(
                    sql.SQL("REVOKE USAGE ON SCHEMA {} FROM {}").format(
                        sql.Identifier(schema), sql.Identifier(other)
                    )
                )
                db.execute(
                    sql.SQL("GRANT USAGE ON SCHEMA {} TO PUBLIC").format(sql.Identifier(schema))
                )
            assert mig.migrate(dsn) == REAL
    finally:
        _drop_roles(other)
    with psycopg.connect(DSN, autocommit=True) as db:  # PUBLIC may not create either
        db.execute(sql.SQL("GRANT CREATE ON SCHEMA {} TO PUBLIC").format(sql.Identifier(schema)))
    with pytest.raises(
        ConfigError, match=r"everyone \(PUBLIC\) has CREATE on the schema of the run"
    ):
        mig.migrate(dsn)


@needs_pg
def test_an_owner_a_file_handed_an_object_to_is_refused_even_when_the_migration_role_belongs_to_it(
    scratch, monkeypatch, tmp_path
):
    """`ALTER TABLE approval_decisions OWNER TO other` (the migration role is a member of `other`) needs CREATE for
    `other` on the schema; the file gives it, and the end of the run refuses that right and keeps nothing. Killed by:
    the end-of-run mutants (E1..E26) of tests/migrate_mutants.py."""
    dsn, schema = scratch
    other = "hadavin_test_ow_" + uuid.uuid4().hex[:8]
    _create_roles(other)
    try:
        assert mig.migrate(dsn) == REAL
        _admin(
            sql.SQL("GRANT CREATE ON SCHEMA {} TO {} WITH GRANT OPTION").format(
                sql.Identifier(schema), sql.Identifier(PLAIN_ROLE)
            )
        )
        _let_the_plain_role_belong_to(other)
        body = _give_create_then(schema, other, f"ALTER TABLE approval_decisions OWNER TO {other}")
        _with_files(monkeypatch, tmp_path, {"0006_hand_over.sql": body})
        with pytest.raises(ConfigError, match=f"schema {schema}: {other} has CREATE") as e:
            mig.migrate(dsn)
        assert other in str(e.value) and _ledger(dsn) == REAL
    finally:
        _drop_roles(other)


@needs_pg
def test_a_right_that_an_earlier_run_gave_is_named_as_such_in_the_refusal(scratch):
    """A later run that names no role finds the rights an earlier run gave to the runtime role; the refusal once said
    'remove the statement from the migration file' although no file was at fault. Guards the wording of the refusal (no list mutant today).
    Re-pointed in commit 3b (the wording changed, the intent did not): the rights are now found at step 2, before any
    file runs, so the refusal says that no file ran and nothing was changed, names the role and prints the REVOKE
    statements. It never tells the reader to remove a statement from a file. (The old sentence 'an earlier run or a
    database administrator' and the hint 'name it in this run' are gone with the old message.)"""
    dsn, _schema = scratch
    run_as = "hadavin_test_er_" + uuid.uuid4().hex[:8]
    _create_roles(run_as)
    try:
        assert mig.migrate(dsn, runtime_role=run_as) == REAL
        with pytest.raises(
            ConfigError, match="before any migration file ran, this database already holds rights"
        ) as e:
            mig.migrate(dsn)
        text = str(e.value)
        assert (
            f"{run_as} has" in text and "To remove: REVOKE" in text and f'FROM "{run_as}"' in text
        )
        assert "Nothing was changed. No file ran." in text
        assert "remove that statement" not in text and "migration file made it" not in text
        assert _ledger(dsn) == REAL, "the ledger is as the first run left it"
    finally:
        _drop_roles(run_as)


@needs_pg
def test_a_named_role_may_not_pass_a_function_right_on(scratch, monkeypatch, tmp_path):
    """`WITH GRANT OPTION` on a function lets the runtime role hand EXECUTE to anyone later; the ACL of a function is not
    reset by the grant map, so it is read. Since round 12 the right itself is refused as well
    (`test_a_named_role_gets_no_right_on_a_function`); the line about the grant option stays in the message. Pin: passes
    on 8382bdd. Killed by: mutant GO4 (the grant option of a function right is not read)."""
    dsn, _schema = scratch
    run_as = "hadavin_test_go_" + uuid.uuid4().hex[:8]
    _create_roles(run_as)
    try:
        _with_files(
            monkeypatch,
            tmp_path,
            {
                "0006_option.sql": f"GRANT EXECUTE ON FUNCTION hadavin_audit_append_only() TO {run_as} WITH GRANT OPTION;\n"
            },
        )
        with pytest.raises(ConfigError, match="may pass EXECUTE on to others") as e:
            mig.migrate(dsn, runtime_role=run_as)
        assert _kept_nothing(str(e.value))
    finally:
        _drop_roles(run_as)


@needs_pg
def test_the_lock_wait_has_an_upper_bound_that_the_server_accepts(scratch):
    """`lock_timeout` is a whole number of milliseconds in 32 bits; above 2147483 seconds the server answered with a raw
    driver error. Now a `ConfigError` before anything runs. Killed by: mutant LW4 (no upper bound)."""
    dsn, _schema = scratch
    refused = driver_error = None
    try:
        mig.migrate(dsn, lock_wait_seconds=mig.MAX_LOCK_WAIT_SECONDS + 1)
    except ConfigError as e:
        refused = str(e)
    except psycopg.Error as e:
        driver_error = str(e)
    assert driver_error is None, f"a raw driver error instead of a ConfigError: {driver_error}"
    assert refused is not None and "from 1 to 2147483" in refused, refused
    assert mig.MAX_LOCK_WAIT_SECONDS * 1000 <= 2**31 - 1 < (mig.MAX_LOCK_WAIT_SECONDS + 1) * 1000


@needs_pg
def test_a_lock_holder_that_this_login_cannot_look_into_is_named_in_plain_words(scratch):
    """For the session of another user the server shows NULL in some columns of `pg_stat_activity`; the message said
    'state None, connected since None'. Killed by: mutant LW5 (NULL is printed as None). The holder logs in as a plain
    role of its own, so the migration (as the plain role of the helper, or as a login that is not a superuser) is another
    user and the server hides those columns, whatever login the test database was given.
    Pin: it also passes on the source before round 11 (42fc259), as the independent run of 8382bdd showed; it holds the behaviour in place."""
    dsn, _schema = scratch
    holder_role = "hadavin_test_lh_" + uuid.uuid4().hex[:8]
    made_up = "made-up-" + uuid.uuid4().hex  # new for each run; never a written value
    _create_roles(holder_role, login_password=made_up)
    try:
        with psycopg.connect(login_dsn(DSN, holder_role), autocommit=True) as holder:
            holder.execute("SELECT pg_advisory_lock(%s)", (mig.MIGRATE_LOCK,))
            with pytest.raises(ConfigError, match="waited 1 seconds") as e:
                mig.migrate(dsn, lock_wait_seconds=1)
    finally:
        _drop_roles(holder_role)
    text = str(e.value)
    assert "None" not in text, text
    assert "not visible to this login" in text, text


def test_a_null_column_of_the_activity_view_is_worded_for_a_reader():
    assert mig._seen(None) == "not visible to this login"
    assert mig._seen("idle") == "idle"


@needs_pg
def test_a_statement_limit_saved_for_the_migration_role_does_not_end_the_lock_wait(scratch):
    """The wait for the migration lock is a statement too, so a `statement_timeout` saved for the login ended it early
    (error code 57014) and the message named the wrong limit. Now the wait has the lock limit only. Killed by: mutant
    LW6 (the statement limit is not switched off for the wait)."""
    dsn, _schema = scratch
    assert mig.migrate(dsn) == REAL  # also makes the plain role of the test run
    with psycopg.connect(DSN, autocommit=True) as admin:
        admin.execute(
            sql.SQL("ALTER ROLE {} SET statement_timeout = '300ms'").format(
                sql.Identifier(PLAIN_ROLE)
            )
        )
    try:
        with psycopg.connect(DSN, autocommit=True) as holder:
            holder.execute("SELECT pg_advisory_lock(%s)", (mig.MIGRATE_LOCK,))
            with pytest.raises(ConfigError, match="waited 2 seconds for the migration lock") as e:
                mig.migrate(dsn, lock_wait_seconds=2)
        assert "statement" not in str(e.value).lower().split("holds it")[0]
    finally:
        with psycopg.connect(DSN, autocommit=True) as admin:
            admin.execute(
                sql.SQL("ALTER ROLE {} RESET statement_timeout").format(sql.Identifier(PLAIN_ROLE))
            )


@needs_pg
def test_a_login_that_cannot_read_which_databases_hold_a_role_does_not_fail_the_sweep(
    capsys, monkeypatch
):
    """The one line that names the databases reads `pg_shdepend`; a login that may not read it must not turn the report
    into an error of the test setup. Killed by: mutant SW18 (the read is not guarded)."""
    with _databases_and_a_stale_role() as (name, (db_x, db_y)):
        with psycopg.connect(make_conninfo(DSN, dbname=db_x), autocommit=True) as in_x:
            in_x.execute(
                sql.SQL("CREATE SCHEMA hadavin_test_owned AUTHORIZATION {}").format(
                    sql.Identifier(name)
                )
            )

        def refused(db, role):
            raise psycopg.errors.InsufficientPrivilege("permission denied for table pg_shdepend")

        monkeypatch.setattr(helper, "_databases_that_still_hold", refused)
        with psycopg.connect(make_conninfo(DSN, dbname=db_y), autocommit=True) as in_y:
            raised = dropped = None
            try:
                dropped = helper.sweep_stale_roles(in_y)
            except psycopg.Error as e:
                raised = str(e)
        out = capsys.readouterr().out
        assert raised is None, f"the sweep raised: {raised}"
        assert name not in dropped
        assert name in out and "this login cannot read pg_shdepend" in out, out


@needs_pg
def test_a_refused_read_in_the_sweep_does_not_abort_the_transaction_of_the_caller(
    capsys, monkeypatch
):
    """`plain_role_connect` runs the sweep on a connection that is inside a transaction. A read the server refuses (a real
    server error, not one raised by Python) put that whole transaction in the failed state, so the next statement failed
    and the lock of the setup stayed taken. The read is now in a savepoint. Killed by: mutant SW20 (no savepoint).
    Pin: it also passes on the source before round 11 (42fc259), as the independent run of 8382bdd showed; it holds the behaviour in place and its mutant shows that it can fail."""
    with _databases_and_a_stale_role() as (name, (db_x, db_y)):
        with psycopg.connect(make_conninfo(DSN, dbname=db_x), autocommit=True) as in_x:
            in_x.execute(
                sql.SQL("CREATE SCHEMA hadavin_test_owned AUTHORIZATION {}").format(
                    sql.Identifier(name)
                )
            )

        def refused(db, role):
            db.execute(
                "SELECT 1 / 0"
            )  # the server refuses: the transaction is now failed unless a savepoint holds it

        monkeypatch.setattr(helper, "_databases_that_still_hold", refused)
        with psycopg.connect(
            make_conninfo(DSN, dbname=db_y)
        ) as in_y:  # not autocommit: inside a transaction
            in_y.execute("SELECT 1")
            helper.sweep_stale_roles(in_y)
            try:
                got = in_y.execute("SELECT 2").fetchone()
            except psycopg.errors.InFailedSqlTransaction:
                got = None
            assert got == (2,), "the caller's transaction is still usable"
    assert name in capsys.readouterr().out


@needs_pg
def test_a_marking_connection_that_cannot_get_its_lock_ends_with_a_plain_error_not_a_hang(
    monkeypatch,
):
    """After a half-open death the server may still hold the old lock of this run; a blocking wait would hang the test
    setup for ever. Now it tries again for a few seconds and then says what to do. Killed by: mutant SW19 (a blocking
    wait)."""
    with psycopg.connect(DSN, autocommit=True) as db:
        helper._mark_the_role(
            db
        )  # this run's marking connection holds the lock, as an old half-open one would
        monkeypatch.setattr(helper, "_MARKS", {})  # a run that has lost track of it
        monkeypatch.setattr(helper, "_MARK_WAIT_SECONDS", 1)
        started = time.monotonic()
        with pytest.raises(RuntimeError, match="could not take its lock") as e:
            helper._mark_the_role(db)
    assert "pg_terminate_backend" in str(e.value)
    assert time.monotonic() - started >= 0.9, (
        "it must try for the whole wait, not give up at the first miss"
    )
    assert time.monotonic() - started < 30, (
        "TEST SETUP PROBLEM, a timing flake and not a defect: a 1 second wait took 30 s"
    )


@needs_pg
def test_the_holder_named_is_the_one_that_holds_the_real_lock_not_one_with_the_same_two_words(
    scratch,
):
    """An advisory lock made of two whole numbers (`pg_advisory_lock(int, int)`) whose halves equal the two halves of
    the migration lock's number has the same `classid` and `objid` in `pg_locks`; only `objsubid` tells them apart
    (1 for one 64-bit number, 2 for two). Without it, an older session with the look-alike lock was named as the holder.
    Killed by: mutant LW7 (`objsubid` is not compared)."""
    dsn, _schema = scratch
    high = mig.MIGRATE_LOCK >> 32
    low = mig.MIGRATE_LOCK & 0xFFFFFFFF
    low = low - (1 << 32) if low >= (1 << 31) else low
    decoy_name = "hadavin_test_decoy_" + uuid.uuid4().hex[:6]
    real_name = "hadavin_test_real_" + uuid.uuid4().hex[:6]
    with (
        psycopg.connect(make_conninfo(DSN, application_name=decoy_name), autocommit=True) as decoy,
        psycopg.connect(make_conninfo(DSN, application_name=real_name), autocommit=True) as real,
    ):
        decoy.execute("SELECT pg_advisory_lock(%s::int, %s::int)", (high, low))
        real.execute("SELECT pg_advisory_lock(%s)", (mig.MIGRATE_LOCK,))
        with pytest.raises(ConfigError, match="waited 1 seconds") as e:
            mig.migrate(dsn, lock_wait_seconds=1)
    assert real_name in str(e.value) and decoy_name not in str(e.value), str(e.value)


# --- rights and owners of objects that existed before the run (round 11) -------------------------------------------------

X = "hadavin_test_x"


def _admin(*statements):
    with psycopg.connect(DSN, autocommit=True) as db:
        ensure_plain_role(db)
        for st in statements:
            db.execute(st)


def _pre_existing(schema, kind, name, *, in_schema=None):
    """An object that exists before the run, owned by the migration role, that no list names. (A migration file cannot
    make one: the text scan lists every table, view and sequence a file creates and refuses one missing from the grant
    map. So an object like this comes from an earlier release, another application or a person.)"""
    where = sql.Identifier(in_schema or schema)
    made = {
        "table": "CREATE TABLE {}.{} (a int)",
        "sequence": "CREATE SEQUENCE {}.{}",
        "view": "CREATE VIEW {}.{} AS SELECT 1 AS a",
    }[kind]
    _admin(
        sql.SQL(made).format(where, sql.Identifier(name)),
        sql.SQL(f"ALTER {kind.upper()} {{}}.{{}} OWNER TO {{}}").format(
            where, sql.Identifier(name), sql.Identifier(PLAIN_ROLE)
        ),
    )


@needs_pg
@pytest.mark.parametrize(
    "later",
    [f"GRANT SELECT ON {X} TO PUBLIC;\n", f"GRANT SELECT (a) ON {X} TO PUBLIC;\n"],
    ids=["table", "column"],
)
def test_a_right_given_on_a_table_that_existed_before_the_run_is_refused(
    scratch, monkeypatch, tmp_path, later
):
    """The table `x` existed before the run (owned by the migration role, in no list). The file holds a plain
    `GRANT ... ON x TO PUBLIC`, a statement the text rules allow. `x` is neither in the grant map nor new, so nothing read
    its rights. Class: a right or an owner changes on an object that existed before the run. Guards: the rights of a relation are read (no list mutant today). The message names the table with its schema, and the column when
    the right is on one column."""
    dsn, schema = scratch
    _pre_existing(schema, "table", X)
    _with_files(monkeypatch, tmp_path, {"0006_open.sql": later})
    # Re-pointed in commit 3b: a right on one column is a line of its own kind now ("column <schema>.<table>, column a:")
    # and the statement is part of the line; a right on the whole table keeps "table <schema>.<table>:".
    on_column = "(a)" in later
    word = "column" if on_column else "table"
    with pytest.raises(
        ConfigError,
        match=f"{word} {schema}.{X}{', column a' if on_column else ''}: everyone \\(PUBLIC\\) has SELECT",
    ) as e:
        mig.migrate(dsn)
    assert _kept_nothing(str(e.value))
    assert ('To remove: REVOKE SELECT ("a") ON TABLE' in str(e.value)) == on_column
    assert _ledger(dsn) is None


@needs_pg
def test_a_second_right_on_a_column_that_already_had_one_is_refused(
    scratch, monkeypatch, tmp_path, named_role, second_schema
):
    """The column `a` already holds a right (an administrator gave it to a named role) before the run. The file adds a
    right for PUBLIC on the same column. The set of columns that hold a right does not change, only what the right says,
    so the table counts as changed only when the text of the rights is part of its state. Guards: the rights of a column are read (no list mutant today; a first right on a column still changes the set, so only this case
    shows it).
    Re-pointed in commit 3b: there is no before/after comparison any more; the state is judged whoever made it. The
    earlier right is given to a THIRD role (one the run does not name: the check does not judge a third role's right on
    an object of another schema, ticket P3a-2 section 1.4), because the same right for a role the run names is now
    refused at step 2 before any file runs. The file then adds the right for everyone, and the end of the run refuses
    that one: a column that already holds a right of someone else does not hide a new right for everyone."""
    dsn, schema = scratch
    _pre_existing(schema, "table", X, in_schema=second_schema)
    _admin(
        sql.SQL("GRANT SELECT (a) ON {}.{} TO {}").format(
            sql.Identifier(second_schema), sql.Identifier(X), sql.Identifier(named_role)
        )
    )
    _with_files(
        monkeypatch,
        tmp_path,
        {"0006_open.sql": f'GRANT SELECT (a) ON "{second_schema}".{X} TO PUBLIC;\n'},
    )
    with pytest.raises(
        ConfigError, match=f"column {second_schema}.{X}, column a: everyone \\(PUBLIC\\) has SELECT"
    ):
        mig.migrate(dsn)


@needs_pg
def test_a_right_given_on_a_table_of_another_schema_is_refused(
    scratch, monkeypatch, tmp_path, second_schema
):
    """Same class, a table of another schema that the migration role owns. Guards: tables of another schema are read (no list mutant today)."""
    dsn, schema = scratch
    _pre_existing(schema, "table", X, in_schema=second_schema)
    _with_files(
        monkeypatch,
        tmp_path,
        {"0006_open.sql": f'GRANT SELECT ON "{second_schema}".{X} TO PUBLIC;\n'},
    )
    with pytest.raises(
        ConfigError, match=f"table {second_schema}.{X}: everyone \\(PUBLIC\\) has SELECT"
    ):
        mig.migrate(dsn)


@needs_pg
def test_an_owner_handed_over_in_the_run_schema_is_refused(scratch, monkeypatch, tmp_path):
    """A file hands a table to a role the migration role belongs to. The new owner needs CREATE on the schema, and the
    file itself gives it (inside a function body); the right is what the end of the run refuses (a group owner is
    allowed since rev 2 of P3a-2: the refusal is the CREATE right, not the owner). Same class as the old
    `was handed to` check (retired with the comparison); the owner side of the check is read on a real server by
    `test_a_foreign_owner_of_a_table_the_package_manages_is_refused_at_the_end_of_the_run` in
    tests/test_migration_verify_pg.py. Guards: an owner handed over in the run schema is refused (no list mutant today)."""
    dsn, schema = scratch
    other = "hadavin_test_ow_" + uuid.uuid4().hex[:8]
    _create_roles(other)
    try:
        _pre_existing(schema, "table", X)
        _let_the_plain_role_belong_to(other)
        _admin(
            sql.SQL("GRANT CREATE ON SCHEMA {} TO {} WITH GRANT OPTION").format(
                sql.Identifier(schema), sql.Identifier(PLAIN_ROLE)
            )
        )
        body = _give_create_then(schema, other, f"ALTER TABLE {X} OWNER TO {other}")
        _with_files(monkeypatch, tmp_path, {"0006_hand.sql": body})
        with pytest.raises(ConfigError, match=f"schema {schema}: {other} has CREATE") as e:
            mig.migrate(dsn)
        assert "The whole run is rolled back" in str(e.value)
    finally:
        _drop_roles(other)


@needs_pg
@pytest.mark.parametrize("change", ["acl", "owner"])
def test_a_schema_that_a_file_changed_is_read_back_whatever_schema_it_is(
    scratch, monkeypatch, tmp_path, second_schema, change
):
    """`GRANT CREATE ON SCHEMA other TO PUBLIC` inside a function body changed a schema that the run does not live in; only
    the schema of the run was read. Guards: changed schemas are read (no list mutant today).
    Re-pointed in commit 3b (ticket P3a-2, 3.3 rule O5 struck, and 10.3 items 3 and 11). The `acl` case keeps its intent:
    a right for everyone is judged in EVERY schema. The `owner` case pinned a REFUSAL that the new design drops on
    purpose: the schema is handed to a role the migration role belongs to (the only kind of role a plain migration role
    can hand an object to: the server wants it to be able to switch to the new owner), and a group owner is allowed. It
    is now the clean control for that choice: the run returns and the schema is owned by the group. The class
    "a changed schema is not read" stays covered by the `acl` case and, for the run's own schema, by
    `test_a_foreign_owner_of_a_table_the_package_manages_is_refused_at_the_end_of_the_run` (tests/test_migration_verify_pg.py).
    NEEDS THE LEAD'S SIGN-OFF as a refusal dropped on purpose (ticket 5.4, rev 3 F6)."""
    dsn, _schema = scratch
    other = "hadavin_test_sw_" + uuid.uuid4().hex[:8]
    _create_roles(other)
    try:
        with psycopg.connect(DSN, autocommit=True) as db:
            name = db.execute("SELECT current_database()").fetchone()[0]
        _admin(
            sql.SQL("ALTER SCHEMA {} OWNER TO {}").format(
                sql.Identifier(second_schema), sql.Identifier(PLAIN_ROLE)
            ),
            sql.SQL("GRANT CREATE ON DATABASE {} TO {}").format(
                sql.Identifier(name), sql.Identifier(other)
            ),
        )
        _let_the_plain_role_grant(other)
        statement = (
            f'GRANT ALL ON SCHEMA "{second_schema}" TO PUBLIC'
            if change == "acl"
            else f'ALTER SCHEMA "{second_schema}" OWNER TO {other}'
        )
        _with_files(monkeypatch, tmp_path, {"0006_schema.sql": _dynamic(statement)})
        if change == "acl":
            with pytest.raises(
                ConfigError, match=f"schema {second_schema}: everyone \\(PUBLIC\\) has CREATE"
            ):
                mig.migrate(dsn)
        else:
            assert "0006_schema" in mig.migrate(dsn)
            with psycopg.connect(DSN, autocommit=True) as db:
                owner = db.execute(
                    "SELECT pg_get_userbyid(nspowner) FROM pg_namespace WHERE nspname = %s",
                    (second_schema,),
                ).fetchone()[0]
            assert owner == other
    finally:
        _drop_roles(other)


@needs_pg
def test_a_foreign_table_that_a_file_opens_to_everyone_is_refused(scratch, monkeypatch, tmp_path):
    """A foreign table is a relation of its own kind ('f'); the read-back looked at r, p, v, m and S only. Killed by:
    mutant RK1 (the kind 'f' is left out)."""
    dsn, schema = scratch
    suffix = uuid.uuid4().hex[:8]
    wrapper, server = f"hadavin_test_w_{suffix}", f"hadavin_test_sv_{suffix}"
    try:
        _admin(
            sql.SQL("CREATE FOREIGN DATA WRAPPER {}").format(sql.Identifier(wrapper)),
            sql.SQL("CREATE SERVER {} FOREIGN DATA WRAPPER {}").format(
                sql.Identifier(server), sql.Identifier(wrapper)
            ),
            sql.SQL("GRANT USAGE ON FOREIGN SERVER {} TO {}").format(
                sql.Identifier(server), sql.Identifier(PLAIN_ROLE)
            ),
            sql.SQL("CREATE FOREIGN TABLE {}.hadavin_test_ft (a int) SERVER {}").format(
                sql.Identifier(schema), sql.Identifier(server)
            ),
            sql.SQL("ALTER FOREIGN TABLE {}.hadavin_test_ft OWNER TO {}").format(
                sql.Identifier(schema), sql.Identifier(PLAIN_ROLE)
            ),
        )
        _with_files(
            monkeypatch,
            tmp_path,
            {"0006_foreign.sql": _dynamic("GRANT SELECT ON hadavin_test_ft TO PUBLIC")},
        )
        with pytest.raises(
            ConfigError,
            match=f"foreign table {schema}.hadavin_test_ft: everyone \\(PUBLIC\\) has SELECT",
        ):
            mig.migrate(dsn)
    finally:
        _admin(
            sql.SQL("DROP SERVER IF EXISTS {} CASCADE").format(sql.Identifier(server)),
            sql.SQL("DROP FOREIGN DATA WRAPPER IF EXISTS {} CASCADE").format(
                sql.Identifier(wrapper)
            ),
        )


@pytest.fixture
def named_role():
    """A role that a run names as the runtime role."""
    role = "hadavin_test_nr_" + uuid.uuid4().hex[:8]
    _create_roles(role)
    try:
        yield role
    finally:
        _drop_roles(role)


@needs_pg
@pytest.mark.parametrize("columns", ["", " (run_id)"], ids=["table", "column"])
def test_a_right_that_a_named_role_may_pass_on_is_refused_on_a_table_of_the_grant_map(
    scratch, named_role, columns
):
    """`WITH GRANT OPTION` lets the named role give the right to anyone later. `migrate` takes back what the migration
    role itself gave before it grants again, so the option survives only when ANOTHER role gave the right: here a third
    role that an administrator let pass SELECT on. (That third role is refused too; this test reads the line about the
    named role.) Until round 11 this test used a table outside the grant map; a named role now gets no right at all
    there (`test_a_named_role_gets_no_right_on_what_is_not_in_the_grant_map`), so the option is shown where a named
    role may hold a right. Pin: the check existed on 8382bdd; only the wording of the place (schema first) is new.
    Killed by: mutant GO5 (the grant option of a relation is not read)."""
    dsn, schema = scratch
    giver = "hadavin_test_gv_" + uuid.uuid4().hex[:8]
    _create_roles(giver)
    try:
        assert mig.migrate(dsn) == REAL
        runs = sql.Identifier(schema, "runs")
        with psycopg.connect(DSN, autocommit=True) as db:
            db.execute(
                sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                    sql.Identifier(schema), sql.Identifier(giver)
                )
            )
            db.execute(
                sql.SQL(f"GRANT SELECT{columns} ON {{}} TO {{}} WITH GRANT OPTION").format(
                    runs, sql.Identifier(giver)
                )
            )
            db.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(giver)))
            db.execute(
                sql.SQL(f"GRANT SELECT{columns} ON {{}} TO {{}} WITH GRANT OPTION").format(
                    runs, sql.Identifier(named_role)
                )
            )
        with pytest.raises(ConfigError, match="may pass SELECT on to others") as e:
            mig.migrate(dsn, runtime_role=named_role)
        # Re-pointed in commit 3b: a line is now "<kind> <schema>.<name>[, column <c>]: <role> may pass <right> on to others"
        where = f"column {schema}.runs, column run_id" if columns else f"table {schema}.runs"
        assert f"{where}: {named_role} may pass SELECT on to others" in str(e.value)
        assert _kept_nothing(str(e.value))
    finally:
        _drop_roles(giver)


@needs_pg
def test_a_named_role_that_may_pass_the_schema_right_on_is_refused(scratch, named_role):
    """The grant option on the schema was read into a variable and dropped. Killed by: mutant GO6 (the grant option of a
    schema right is ignored)."""
    dsn, schema = scratch
    _admin(
        sql.SQL("GRANT USAGE ON SCHEMA {} TO {} WITH GRANT OPTION").format(
            sql.Identifier(schema), sql.Identifier(named_role)
        )
    )
    with pytest.raises(ConfigError, match="may pass USAGE on to others") as e:
        mig.migrate(dsn, runtime_role=named_role)
    assert _kept_nothing(str(e.value))


@needs_pg
@pytest.mark.parametrize(
    ("kind", "grant", "right"),
    [
        ("table", f"GRANT SELECT ON {X} TO {{r}};\n", "SELECT"),
        ("table", f"GRANT SELECT (a) ON {X} TO {{r}};\n", "SELECT"),
        ("table", f"GRANT INSERT ON {X} TO {{r}};\n", "INSERT"),
        ("table", f"GRANT DELETE ON {X} TO {{r}};\n", "DELETE"),
        ("sequence", f"GRANT USAGE ON SEQUENCE {X} TO {{r}};\n", "USAGE"),
        ("sequence", f"GRANT SELECT ON SEQUENCE {X} TO {{r}};\n", "SELECT"),
        ("sequence", f"GRANT UPDATE ON SEQUENCE {X} TO {{r}};\n", "UPDATE"),
        ("view", f"GRANT SELECT ON {X} TO {{r}};\n", "SELECT"),
    ],
    ids=[
        "select",
        "column_select",
        "insert",
        "delete",
        "sequence_usage",
        "sequence_select",
        "sequence_update",
        "view_select",
    ],
)
def test_a_named_role_gets_no_right_on_what_is_not_in_the_grant_map(
    scratch, monkeypatch, tmp_path, named_role, second_schema, kind, grant, right
):
    """Outside the grant map a named role (runtime, portal, purge) gets nothing: not SELECT either, on a table, a
    column, a view or a sequence, in any schema. (Until round 11 SELECT, and USAGE on a sequence, were accepted as
    "reading"; USAGE on a sequence lets the role call nextval, which changes the sequence, and SELECT on a table of
    another application in another schema is more than this package gives. Round 12 tightens this on purpose: the old
    cases `select_ok` and `sequence_usage_ok` expected the run to pass.) Fails on 8382bdd for `select`,
    `column_select`, `sequence_usage`, `sequence_select` and `view_select` (the run passed there); `insert`, `delete` and
    `sequence_update` were refused there too and fail only on the new wording of the place. Killed by: mutants RO1
    (any right of a named role is accepted outside the grant map) and RO3 (SELECT is accepted there)."""
    dsn, schema = scratch
    _pre_existing(schema, kind, X, in_schema=second_schema)
    _with_files(
        monkeypatch,
        tmp_path,
        {"0006_grant.sql": grant.format(r=named_role).replace(X, f'"{second_schema}".{X}', 1)},
    )
    with pytest.raises(ConfigError, match="NOT THIS PACKAGE'S OBJECT") as e:
        mig.migrate(dsn, runtime_role=named_role)
    # Re-pointed in commit 3b: a right on one column is a line of the kind "column", with the column after the table.
    on_column = "(a)" in grant
    shown = f"column {second_schema}.{X}, column a" if on_column else f"{kind} {second_schema}.{X}"
    assert f"{shown}: {named_role} has {right}" in str(e.value)
    assert "Confirm with the owner of" in str(e.value)
    assert "0006_grant" not in (_ledger(dsn) or [])


@needs_pg
@pytest.mark.parametrize(
    "case",
    ["other_schema", "member_role", "named_delete", "named_select", "member_role_select"],
)
def test_default_rights_are_read_for_every_schema_and_for_the_roles_the_migration_role_belongs_to(
    scratch, second_schema, named_role, case
):
    """`ALTER DEFAULT PRIVILEGES IN SCHEMA other ...` and `... FOR ROLE <a role the migration role belongs to> ...` set
    rights of objects made later; only the migration role itself, in the run schema or everywhere, was read. A named role
    gets no default right either, not one to read (round 12, on purpose: until round 11 the cases `named_select` and
    `member_role_select` expected the run to pass; a default right gives a role rights on tables that do not exist yet
    and that no grant map names). Fails on 8382bdd for `named_select` and `member_role_select`. Killed by: mutants DP2
    (only the run schema), DP3 (only the migration role itself), DP4 (a named role may have a default right)."""
    dsn, schema = scratch
    other = "hadavin_test_dr_" + uuid.uuid4().hex[:8]
    _create_roles(other)
    try:
        _let_the_plain_role_belong_to(other)
        who, scope, grantee, right = {
            "other_schema": (PLAIN_ROLE, f'IN SCHEMA "{second_schema}"', "PUBLIC", "SELECT"),
            "member_role": (other, f'IN SCHEMA "{schema}"', "PUBLIC", "SELECT"),
            "named_delete": (PLAIN_ROLE, f'IN SCHEMA "{second_schema}"', named_role, "DELETE"),
            "named_select": (PLAIN_ROLE, f'IN SCHEMA "{second_schema}"', named_role, "SELECT"),
            "member_role_select": (other, "", named_role, "SELECT"),
        }[case]
        _admin(
            sql.SQL(
                f"ALTER DEFAULT PRIVILEGES FOR ROLE {{}} {scope} GRANT {right} ON TABLES TO {{}}"
            ).format(
                sql.Identifier(who),
                sql.SQL("PUBLIC") if grantee == "PUBLIC" else sql.Identifier(grantee),
            )
        )
        with pytest.raises(
            ConfigError, match="on every new (table|function|sequence|type) that"
        ) as e:
            mig.migrate(dsn, runtime_role=named_role)
        text = str(e.value)
        assert (f"{_who(grantee)} gets {right} on every new table that {who} makes in ") in text
        assert _kept_nothing(text)
        # `member_role_select` is for every schema: PostgreSQL then keeps the role's own default rights in the list
        # next to the one for the named role; that own row is the owner's and is not reported
        assert f"{who} gets" not in text
    finally:
        _drop_roles(other)


@needs_pg
def test_a_default_right_that_a_group_of_the_migration_role_sets_for_a_third_role_is_refused(
    scratch, named_role
):
    """`ALTER DEFAULT PRIVILEGES FOR ROLE <group> ... GRANT ... TO <third role>`, where the migration role belongs to the
    group, gives a third role rights on every table the group makes later. Only the entries of the roles the migration
    role belongs to are read for a grantee that is neither a named role nor everyone. Killed by: mutant DP3."""
    dsn, schema = scratch
    group = "hadavin_test_dg_" + uuid.uuid4().hex[:8]
    third = "hadavin_test_dt_" + uuid.uuid4().hex[:8]
    _create_roles(group, third)
    try:
        _let_the_plain_role_belong_to(group)
        _admin(
            sql.SQL(
                f'ALTER DEFAULT PRIVILEGES FOR ROLE {{}} IN SCHEMA "{schema}" GRANT SELECT ON TABLES TO {{}}'
            ).format(sql.Identifier(group), sql.Identifier(third))
        )
        with pytest.raises(ConfigError, match="on every new table that") as e:
            mig.migrate(dsn, runtime_role=named_role)
        assert f"{third} gets SELECT on every new table that {group} makes in " in str(e.value)
        assert _kept_nothing(e.value)
    finally:
        _drop_roles(group, third)


@needs_pg
def test_a_named_role_that_may_pass_a_function_right_on_is_refused(
    scratch, monkeypatch, tmp_path, named_role, second_schema
):
    """`GRANT EXECUTE ON FUNCTION ... TO <named role> WITH GRANT OPTION` lets that role pass the right on. The message
    names the function with its schema and its argument list (on 8382bdd the last assertion was `... and schema`, which
    is always true; it now reads the message). Killed by: mutant GO4 (the grant option of a function right is
    ignored).
    Pin: it also passes on the source before round 11 (42fc259), as the independent run of 8382bdd showed; it holds the behaviour in place and its mutant shows that it can fail."""
    dsn, _schema = scratch
    _admin(
        sql.SQL(
            "CREATE FUNCTION {}.hadavin_test_gf() RETURNS int LANGUAGE sql AS $q$ SELECT 1 $q$"
        ).format(sql.Identifier(second_schema)),
        sql.SQL("ALTER FUNCTION {}.hadavin_test_gf() OWNER TO {}").format(
            sql.Identifier(second_schema), sql.Identifier(PLAIN_ROLE)
        ),
    )
    _with_files(
        monkeypatch,
        tmp_path,
        {
            "0006_option.sql": _dynamic(
                f'GRANT EXECUTE ON FUNCTION "{second_schema}".hadavin_test_gf() TO {named_role} WITH GRANT OPTION'
            )
        },
    )
    with pytest.raises(ConfigError, match="may pass EXECUTE on to others") as e:
        mig.migrate(dsn, runtime_role=named_role)
    assert (
        f"function {second_schema}.hadavin_test_gf(): {named_role} may pass EXECUTE on to others"
        in str(e.value)
    )


@needs_pg
def test_the_database_owner_pseudo_role_is_refused_on_a_schema_it_does_not_own(scratch):
    """The built-in `pg_database_owner` stands for whoever owns the database. On a schema that it does not own, a right
    for it is a right for another role (the owner of the database is not a role of this package) and is refused like
    one. Until round 11 it was accepted on every schema (the test then was
    `test_the_database_owner_pseudo_role_may_have_rights_on_a_schema`); round 12 tightens this on purpose. Where it OWNS
    the schema its rights are the owner's: `test_the_printed_role_runs_in_a_schema_that_the_database_owner_role_owns`.
    Fails on 8382bdd (the run passed). Killed by: mutant PDO2 (the pseudo-role is skipped on every schema)."""
    dsn, schema = scratch
    _admin(sql.SQL("GRANT ALL ON SCHEMA {} TO pg_database_owner").format(sql.Identifier(schema)))
    with pytest.raises(
        ConfigError, match=f"schema {schema}: pg_database_owner has CREATE on the schema of the run"
    ) as e:
        mig.migrate(dsn)
    assert _kept_nothing(str(e.value)) and _ledger(dsn) is None


@needs_pg
def test_a_named_role_with_the_replication_flag_is_refused(scratch):
    """The runtime, portal and purge roles are checked for the powerful flags too: a role that can replicate can read
    every change made on the whole server. Killed by: mutant RF5 (the flag is not read for a named role)."""
    dsn, _schema = scratch
    role = "hadavin_test_rp_" + uuid.uuid4().hex[:8]
    _create_roles(role)
    try:
        _admin(sql.SQL("ALTER ROLE {} REPLICATION").format(sql.Identifier(role)))
        with pytest.raises(ConfigError, match="has the flag REPLICATION") as e:
            mig.migrate(dsn, runtime_role=role)
        assert role in str(e.value) and _ledger(dsn) is None
    finally:
        _drop_roles(role)


# --- round 12: scope of the comparison, named roles, default rights, SECURITY DEFINER, wording ------------------------
#
# "Fails on 8382bdd" in a docstring means: the test was run against the source of commit 8382bdd and failed for the
# reason the docstring gives. "Pin" means: the test also passes on 8382bdd; it holds a behaviour in place.


def _meanwhile(monkeypatch, *statements) -> list[str]:
    """Run `statements` in ANOTHER session (the administrator's, each committed at once) while the run is open: right
    after the first file ran, before its read-back. Returns the list that holds the file name once it happened."""
    real = mig._check_read_back
    happened: list[str] = []

    def then(db, saved, file_name, *args, **kwargs):
        if not happened:
            happened.append(file_name)
            with psycopg.connect(DSN, autocommit=True) as other_session:
                for st in statements:
                    other_session.execute(st)
        return real(db, saved, file_name, *args, **kwargs)

    monkeypatch.setattr(mig, "_check_read_back", then)
    return happened


def _definer_function(schema: str, owner: str) -> None:
    _admin(
        sql.SQL(
            "CREATE FUNCTION {}.hadavin_test_def() RETURNS int LANGUAGE sql SECURITY DEFINER AS $q$ SELECT 1 $q$"
        ).format(sql.Identifier(schema)),
        sql.SQL("ALTER FUNCTION {}.hadavin_test_def() OWNER TO {}").format(
            sql.Identifier(schema), sql.Identifier(owner)
        ),
    )


@needs_pg
@pytest.mark.parametrize("owner", ["the_migration_role", "a_role_it_belongs_to"])
def test_a_security_definer_function_of_the_migration_role_that_no_file_made_is_refused(
    scratch, owner
):
    """A SECURITY DEFINER function runs with the rights of its owner. One that sits in the schema of the run and is
    owned by the migration role (or by a role it belongs to) lets whoever may call it act as that role, for as long as
    it exists, whether a file of THIS run made it or not (an earlier run, a person, a file of an older release). Round
    11 stopped looking at functions no file touched; this one kind is looked at again. The message says no file of this
    run made it. Fails on 8382bdd (the run passed). Killed by: mutant SD6 (only functions this package names or a file
    changed are read)."""
    dsn, schema = scratch
    group = "hadavin_test_dg_" + uuid.uuid4().hex[:8]
    _create_roles(group)
    try:
        if owner == "the_migration_role":
            with psycopg.connect(DSN, autocommit=True) as db:
                ensure_plain_role(db)
            _definer_function(schema, PLAIN_ROLE)
        else:
            _let_the_plain_role_belong_to(group)
            _admin(
                sql.SQL("GRANT CREATE ON SCHEMA {} TO {}").format(
                    sql.Identifier(schema), sql.Identifier(group)
                )
            )
            _definer_function(schema, group)
            _admin(  # one cause only: the group keeps no right on the schema
                sql.SQL("REVOKE CREATE ON SCHEMA {} FROM {}").format(
                    sql.Identifier(schema), sql.Identifier(group)
                )
            )
        with pytest.raises(ConfigError, match="SECURITY DEFINER") as e:
            mig.migrate(dsn)
        text = str(e.value)
        # Re-pointed in commit 3b: the line is "function <schema>.<name>(): <owner> runs with the rights of its owner
        # (SECURITY DEFINER) and is not on the reviewed list" (rule O4); the "no file of this run made or changed it" part
        # is now the fact that the refusal comes at step 2, before any file ran.
        owner_role = PLAIN_ROLE if owner == "the_migration_role" else group
        assert (
            f"function {schema}.hadavin_test_def(): {owner_role} runs with the rights of its owner (SECURITY DEFINER) "
            "and is not on the reviewed list"
        ) in text
        assert "Nothing was changed. No file ran." in text
        assert "SECURITY INVOKER" in text
        assert _kept_nothing(text) and _ledger(dsn) is None
    finally:
        _admin(
            sql.SQL("DROP FUNCTION IF EXISTS {}.hadavin_test_def()").format(sql.Identifier(schema))
        )
        _drop_roles(group)


_DEFAULT_OK = {
    # case -> (the role the default is for, scope, statement tail)
    "tables_in_the_run_schema": ("group", "IN SCHEMA {schema}", "GRANT SELECT ON TABLES TO {me}"),
    "functions_everywhere": ("group", "", "GRANT EXECUTE ON FUNCTIONS TO {me}"),
    "sequences_everywhere": ("group", "", "GRANT USAGE ON SEQUENCES TO {me}"),
    "types_everywhere": ("group", "", "GRANT USAGE ON TYPES TO {me}"),
    "only_the_groups_own_row": ("group", "", "REVOKE UPDATE ON TABLES FROM {group}"),
}


@needs_pg
@pytest.mark.parametrize("case", list(_DEFAULT_OK))
def test_a_default_right_for_the_migration_role_itself_and_the_servers_own_default_are_not_a_strangers(
    scratch, case
):
    """A role the migration role belongs to gives the MIGRATION ROLE a default right on what that role makes later
    (`ALTER DEFAULT PRIVILEGES FOR ROLE grp ... GRANT ... TO migrator`): the migration role is not a stranger, the run
    goes through. For functions and types set for every schema, PostgreSQL then also writes its own built-in default
    into the list ("everyone may call a new function", "everyone may use a new type": `{=X/grp,grp=X/grp,...}`, seen on
    16.15); nobody set that entry and it says what holds with no list at all, so it is not refused either. Fails on
    8382bdd for the first four cases (refused: "<the migration role> gets ...", and for functions and types also
    "PUBLIC gets ..."). `only_the_groups_own_row` is a pin (the row of the role the default is for). Killed by: mutants
    DP6 (a right for the migration role is a stranger's), DP5 (the row of the role itself is a stranger's), DP7 (the
    server's own default is refused)."""
    dsn, schema = scratch
    group = "hadavin_test_dr_" + uuid.uuid4().hex[:8]
    _create_roles(group)
    try:
        _let_the_plain_role_belong_to(group)
        _for_role, scope, tail = _DEFAULT_OK[case]
        _admin(
            sql.SQL("ALTER DEFAULT PRIVILEGES FOR ROLE {group} " + scope + " " + tail).format(
                group=sql.Identifier(group),
                schema=sql.Identifier(schema),
                me=sql.Identifier(PLAIN_ROLE),
            )
        )
        assert mig.migrate(dsn) == REAL
    finally:
        _drop_roles(group)


_DEFAULT_REFUSED = {
    # case -> (scope, statement tail, the role named in the message, right, kind word)
    "named_functions_everywhere": (
        "",
        "GRANT EXECUTE ON FUNCTIONS TO {named}",
        "named",
        "EXECUTE",
        "function",
    ),
    "named_sequences_in_a_schema": (
        "IN SCHEMA {schema}",
        "GRANT USAGE ON SEQUENCES TO {named}",
        "named",
        "USAGE",
        "sequence",
    ),
    "named_types_everywhere": ("", "GRANT USAGE ON TYPES TO {named}", "named", "USAGE", "type"),
    "everyone_functions_in_a_schema": (
        "IN SCHEMA {schema}",
        "GRANT EXECUTE ON FUNCTIONS TO PUBLIC",
        "PUBLIC",
        "EXECUTE",
        "function",
    ),
    "everyone_sequences_everywhere": (
        "",
        "GRANT USAGE ON SEQUENCES TO PUBLIC",
        "PUBLIC",
        "USAGE",
        "sequence",
    ),
}


@needs_pg
@pytest.mark.parametrize("case", list(_DEFAULT_REFUSED))
def test_a_default_right_for_a_named_role_or_for_everyone_is_refused_for_functions_sequences_and_types(
    scratch, named_role, case
):
    """A default right of the migration role for a role named in the run (runtime, portal, purge) is refused for every
    kind of object, and so is one for everyone (PUBLIC) that somebody SET: for one schema (a list for one schema starts
    empty, so `EXECUTE` for everyone there was set by a person), or for a kind where the server has no such default
    (sequences). The message names the role that was given the right and prints the statement that undoes it; for a
    named role on functions or types it does NOT also blame PUBLIC for the server's own default. Fails on 8382bdd for
    the three `named_...` cases (accepted there, or refused blaming PUBLIC). The two `everyone_...` cases were refused
    on 8382bdd too and fail there only on the new wording (the place in words, the printed statement that undoes it).
    Killed by: mutants DP4 (a named role may have a default right) and DP8 (the server's own default is also skipped
    when it is set for one schema)."""
    dsn, schema = scratch
    scope, tail, who, right, kind = _DEFAULT_REFUSED[case]
    with psycopg.connect(DSN, autocommit=True) as db:
        ensure_plain_role(db)
    _admin(
        sql.SQL("ALTER DEFAULT PRIVILEGES FOR ROLE {me} " + scope + " " + tail).format(
            me=sql.Identifier(PLAIN_ROLE),
            schema=sql.Identifier(schema),
            named=sql.Identifier(named_role),
        )
    )
    try:
        with pytest.raises(
            ConfigError, match="on every new (table|function|sequence|type) that"
        ) as e:
            mig.migrate(dsn, runtime_role=named_role)
        text = str(e.value)
        role = named_role if who == "named" else "PUBLIC"
        place = f"the schema {schema}" if scope else "every schema"
        assert (
            f"{_who(role)} gets {right} on every new {kind} that {PLAIN_ROLE} makes in {place}"
            in text
        )
        assert ("everyone (PUBLIC) gets" in text) == (who == "PUBLIC"), text
        assert f"REVOKE {right} ON {kind.upper()}S FROM" in text
        assert _kept_nothing(text) and _ledger(dsn) is None
    finally:
        with psycopg.connect(DSN, autocommit=True) as db:  # the role lives for the whole process
            db.execute(
                sql.SQL(
                    "ALTER DEFAULT PRIVILEGES FOR ROLE {me} "
                    + scope
                    + " "
                    + tail.replace("GRANT", "REVOKE").replace(" TO ", " FROM ")
                ).format(
                    me=sql.Identifier(PLAIN_ROLE),
                    schema=sql.Identifier(schema),
                    named=sql.Identifier(named_role),
                )
            )


@needs_pg
def test_a_named_role_gets_no_right_on_a_function(scratch, monkeypatch, tmp_path, named_role):
    """The grant map holds tables, views and sequences; this package gives no role a right on a function (a trigger
    function is called by the trigger, not by the role). So `GRANT EXECUTE ON FUNCTION ... TO <the runtime role>` in a
    file is refused. (Until round 11 a named role could hold EXECUTE on a function; round 12 tightens this on purpose,
    following "a named role gets no right outside the grant map".) The file first takes the default right from
    everyone, so the named role's right is the ONE cause of the refusal. Fails on 8382bdd (the run passed). Killed by:
    mutant RO4 (a named role may have a right on a function)."""
    dsn, schema = scratch
    _with_files(
        monkeypatch,
        tmp_path,
        {
            "0006_fn.sql": "REVOKE ALL ON FUNCTION hadavin_audit_append_only() FROM PUBLIC;\n"
            f"GRANT EXECUTE ON FUNCTION hadavin_audit_append_only() TO {named_role};\n"
        },
    )
    with pytest.raises(ConfigError, match="rights that the grant map does not give") as e:
        mig.migrate(dsn, runtime_role=named_role)
    # Re-pointed in commit 3b: one line of the kind "function <schema>.<name>(): <role> has EXECUTE" and the printed
    # REVOKE; the refusal is the ONE line (the default for everyone was taken by the file) and it comes after the files
    # and the grants (step 6), so the run is rolled back.
    lines = [ln for ln in str(e.value).splitlines() if ln.startswith("  - ")]
    assert lines == [
        (
            f"  - function {schema}.hadavin_audit_append_only(): {named_role} has EXECUTE. To remove: "
            f'REVOKE EXECUTE ON ROUTINE "{schema}"."hadavin_audit_append_only"() FROM "{named_role}";'
        )
    ], str(e.value)
    assert _kept_nothing(str(e.value)) and "0006_fn" not in (_ledger(dsn) or [])


@needs_pg
@pytest.mark.parametrize("owner", ["the_migration_role", "another_role"])
def test_a_function_that_is_called_like_a_table_of_the_grant_map_is_not_this_packages(
    scratch, owner
):
    """The names this package manages are kept per catalog: `spend` is a TABLE of the grant map, so a FUNCTION `spend()`
    of another application in the same schema is not managed. Whoever owns it, the run goes through, its rights are
    not read and it keeps the default right of everyone to call it. Fails on 8382bdd (one list of names was used for
    both catalogs: with another owner the run was refused as "cannot change 1 object(s) of this package"; with the
    migration role as owner the right of the third role was refused). Killed by: mutants MC1 (the function half of the
    ownership check gets the relation names) and MC2 (the rights check takes a relation name for a function name)."""
    dsn, schema = scratch
    other = "hadavin_test_mc_" + uuid.uuid4().hex[:8]
    _create_roles(other)
    try:
        with psycopg.connect(DSN, autocommit=True) as db:
            ensure_plain_role(db)
        fn = sql.SQL("{}.spend()").format(sql.Identifier(schema))
        _admin(
            sql.SQL("CREATE FUNCTION {} RETURNS int LANGUAGE sql AS $q$ SELECT 1 $q$").format(fn),
            sql.SQL("GRANT EXECUTE ON FUNCTION {} TO {}").format(fn, sql.Identifier(other)),
            sql.SQL("ALTER FUNCTION {} OWNER TO {}").format(
                fn, sql.Identifier(PLAIN_ROLE if owner == "the_migration_role" else other)
            ),
        )
        if owner == "the_migration_role":
            # Re-pointed in commit 3b (ticket P3a-2, 3.4 line 3: a function of the migration role in the schema of the run
            # may be called by nobody else; the old code left it alone). The run is refused at step 2 and the refusal
            # names BOTH rights (everyone's and the third role's). That everyone's right is named at all shows `spend()`
            # was NOT taken for the table `spend` of the grant map: a managed function has the default for everyone
            # removed by step 4 and would not be named. The function keeps its rights (nothing was changed).
            with pytest.raises(ConfigError, match="before any migration file ran") as e:
                mig.migrate(dsn)
            lines = [ln for ln in str(e.value).splitlines() if ln.startswith("  - ")]
            assert any(
                f"function {schema}.spend(): everyone (PUBLIC) has EXECUTE" in ln for ln in lines
            )
            assert any(f"function {schema}.spend(): {other} has EXECUTE" in ln for ln in lines)
            assert "No file ran." in str(e.value) and _ledger(dsn) is None
            return
        assert mig.migrate(dsn) == REAL
        with psycopg.connect(DSN, autocommit=True) as db:
            everyone = db.execute(
                "SELECT has_function_privilege('public', p.oid, 'EXECUTE') FROM pg_proc p "
                "JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname = %s AND p.proname = 'spend'",
                (schema,),
            ).fetchone()[0]
        assert everyone is True
    finally:
        _admin(sql.SQL("DROP FUNCTION IF EXISTS {}.spend()").format(sql.Identifier(schema)))
        _drop_roles(other)


@contextlib.contextmanager
def _foreign_table(schema: str):
    """A foreign table `hadavin_test_ft` in `schema`, owned by the migration role (no remote server is ever asked)."""
    suffix = uuid.uuid4().hex[:8]
    wrapper, server = f"hadavin_test_w_{suffix}", f"hadavin_test_sv_{suffix}"
    try:
        _admin(
            sql.SQL("CREATE FOREIGN DATA WRAPPER {}").format(sql.Identifier(wrapper)),
            sql.SQL("CREATE SERVER {} FOREIGN DATA WRAPPER {}").format(
                sql.Identifier(server), sql.Identifier(wrapper)
            ),
            sql.SQL("GRANT USAGE ON FOREIGN SERVER {} TO {}").format(
                sql.Identifier(server), sql.Identifier(PLAIN_ROLE)
            ),
            sql.SQL("CREATE FOREIGN TABLE {}.hadavin_test_ft (a int) SERVER {}").format(
                sql.Identifier(schema), sql.Identifier(server)
            ),
            sql.SQL("ALTER FOREIGN TABLE {}.hadavin_test_ft OWNER TO {}").format(
                sql.Identifier(schema), sql.Identifier(PLAIN_ROLE)
            ),
        )
        yield
    finally:
        _admin(
            sql.SQL("DROP SERVER IF EXISTS {} CASCADE").format(sql.Identifier(server)),
            sql.SQL("DROP FOREIGN DATA WRAPPER IF EXISTS {} CASCADE").format(
                sql.Identifier(wrapper)
            ),
        )


@needs_pg
def test_a_named_role_that_can_read_a_foreign_table_in_the_run_schema_is_refused(
    scratch, named_role
):
    """The check of what a named role can really do read tables, views and sequences of the schema, not foreign tables
    (a table whose rows live on another server). An administrator gave the runtime role SELECT on one before the run:
    no file changed it, so nothing else looks at it. Fails on 8382bdd (the run passed). Killed by: mutant RK2 (the
    kind 'f' is left out of the role check)."""
    dsn, schema = scratch
    with _foreign_table(schema):
        _admin(
            sql.SQL("GRANT SELECT ON {}.hadavin_test_ft TO {}").format(
                sql.Identifier(schema), sql.Identifier(named_role)
            )
        )
        with pytest.raises(ConfigError, match="foreign table .*: .* has SELECT") as e:
            mig.migrate(dsn, runtime_role=named_role)
        # Re-pointed in commit 3b: the line names the kind, the schema and the table, then the role and the right.
        assert f"foreign table {schema}.hadavin_test_ft: {named_role} has SELECT" in str(e.value)
        assert 'REVOKE SELECT ON TABLE "' in str(e.value) and "No file ran." in str(e.value)


@needs_pg
def test_a_prepared_transaction_that_holds_the_migration_lock_is_named_as_one(scratch):
    """A prepared transaction (`PREPARE TRANSACTION`) keeps its locks and belongs to no session: the list of sessions
    shows nobody, and "a session this login cannot see" with the advice to end that session would send the reader the
    wrong way. The message names the prepared transaction that holds the lock, and ONLY that one: a second prepared
    transaction of the same database that holds no lock is not named (an administrator who finished it would lose another
    system's work). A server whose `max_prepared_transactions` is 0 FAILS this test visibly (ticket 6.3: no early return,
    no skip), on a developer machine and in CI alike: start the test server with `-c max_prepared_transactions=10`.
    Killed by: mutants LW8 (a lock without a session is not looked for) and V71 (the old listing of the database's
    prepared transactions replaces the join to the lock)."""
    dsn, _schema = scratch
    name = "hadavin_test_prep_" + uuid.uuid4().hex[:8]
    bystander = "hadavin_test_bystander_" + uuid.uuid4().hex[:8]
    with psycopg.connect(DSN, autocommit=True) as holder:
        allowed = holder.execute(
            "SELECT current_setting('max_prepared_transactions')::int"
        ).fetchone()[0]
        if allowed == 0:
            pytest.fail(
                "this server has max_prepared_transactions = 0; the prepared-transaction test cannot run. Start the "
                "test server with -c max_prepared_transactions=10.",
                pytrace=False,
            )
        holder.execute("BEGIN")
        # the bystander is prepared first and holds another advisory lock, not the migration lock
        holder.execute("SELECT pg_advisory_xact_lock(%s)", (mig.MIGRATE_LOCK + 1,))
        holder.execute(sql.SQL("PREPARE TRANSACTION {}").format(sql.Literal(bystander)))
        holder.execute("BEGIN")
        holder.execute("SELECT pg_advisory_xact_lock(%s)", (mig.MIGRATE_LOCK,))
        holder.execute(sql.SQL("PREPARE TRANSACTION {}").format(sql.Literal(name)))
    try:
        with pytest.raises(ConfigError, match="a prepared transaction holds it") as e:
            mig.migrate(dsn, lock_wait_seconds=1)
        text = str(e.value)
        assert name in text and "ROLLBACK PREPARED" in text and "Nothing was changed." in text
        assert "pg_terminate_backend" not in text
        assert bystander not in text, "the prepared transaction that holds no lock is named"
        assert f"ROLLBACK PREPARED '{name}'" in text
    finally:
        with psycopg.connect(DSN, autocommit=True) as db:
            db.execute(sql.SQL("ROLLBACK PREPARED {}").format(sql.Literal(name)))
            db.execute(sql.SQL("ROLLBACK PREPARED {}").format(sql.Literal(bystander)))
    assert mig.migrate(dsn) == REAL


# --- the same checks with the role the refusal message prints (it does not own the schema) ---------------------------


def _printed_role_in(schema: str, owner: str | None = None) -> tuple[str, str, str]:
    """The migration role exactly as `PLAIN_MIGRATION_ROLE_SQL` prints it (CREATE on the schema, USAGE with the grant
    option, nothing else): unlike the role of the other tests it does NOT own the schema. With `owner`, that role owns
    the schema."""
    role, rt, pt = _role_from_the_printed_sql(schema, grant_option=True)
    if owner:
        with psycopg.connect(DSN, autocommit=True) as db:
            db.execute(
                sql.SQL("ALTER SCHEMA {} OWNER TO {}").format(
                    sql.Identifier(schema), sql.Identifier(owner)
                )
            )
    return role, rt, pt


@needs_pg
@pytest.mark.real_connect
def test_the_printed_role_runs_in_a_schema_that_the_database_owner_role_owns(scratch):
    """The `public` schema of PostgreSQL 15 and later is owned by the built-in `pg_database_owner`. In a schema it owns,
    its rights are the owner's and the run goes through, also for a migration role that does not own the schema (the
    role the refusal message prints) and with a runtime and a portal role. Pin: passes on 8382bdd. Killed by: mutants
    SC12 (the migration role's own right on the schema is a stranger's) and SC13 (the owner's right on a schema is a
    stranger's)."""
    super_dsn, schema = scratch
    role, rt, pt = _printed_role_in(schema, owner="pg_database_owner")
    try:
        assert mig.migrate(login_dsn(super_dsn, role), runtime_role=rt, portal_role=pt) == REAL
        assert mig.migrate(login_dsn(super_dsn, role), runtime_role=rt, portal_role=pt) == []
    finally:
        _admin(sql.SQL("ALTER SCHEMA {} OWNER TO CURRENT_USER").format(sql.Identifier(schema)))
        _drop_all(role, rt, pt)


@needs_pg
@pytest.mark.real_connect
def test_with_the_printed_role_the_schema_and_default_right_checks_hold(scratch):
    """The new schema and default-right checks once more with the printed migration role (the other tests run as a role
    that owns the schema, which is more than the printed role has). In order: (1) a role the printed role belongs to
    gives IT a default right: accepted; (2) the printed role's default right for the runtime role: refused; (3) after
    that is undone, a right for `pg_database_owner` on the schema, which it does not own: refused; (4) undone: accepted.
    Fails on 8382bdd at step (1)."""
    super_dsn, schema = scratch
    group = "hadavin_test_pg_" + uuid.uuid4().hex[:8]
    _create_roles(group)
    role, rt, pt = _printed_role_in(schema)
    me, there = sql.Identifier(role), sql.Identifier(schema)
    dsn = login_dsn(super_dsn, role)
    try:
        _admin(
            sql.SQL("GRANT {} TO {}").format(sql.Identifier(group), me),
            sql.SQL("ALTER DEFAULT PRIVILEGES FOR ROLE {} GRANT EXECUTE ON FUNCTIONS TO {}").format(
                sql.Identifier(group), me
            ),
        )
        assert mig.migrate(dsn, runtime_role=rt, portal_role=pt) == REAL  # (1)
        _admin(
            sql.SQL(
                "ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA {} GRANT SELECT ON TABLES TO {}"
            ).format(me, there, sql.Identifier(rt))
        )
        with pytest.raises(
            ConfigError, match=f"{rt} gets SELECT on every new table that {role} makes"
        ):
            mig.migrate(dsn, runtime_role=rt, portal_role=pt)  # (2)
        _admin(
            sql.SQL(
                "ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA {} REVOKE SELECT ON TABLES FROM {}"
            ).format(me, there, sql.Identifier(rt)),
            sql.SQL("GRANT CREATE ON SCHEMA {} TO pg_database_owner").format(there),
        )
        with pytest.raises(
            ConfigError,
            match=f"schema {schema}: pg_database_owner has CREATE on the schema of the run",
        ):
            mig.migrate(dsn, runtime_role=rt, portal_role=pt)  # (3)
        _admin(sql.SQL("REVOKE CREATE ON SCHEMA {} FROM pg_database_owner").format(there))
        assert mig.migrate(dsn, runtime_role=rt, portal_role=pt) == []  # (4)
    finally:
        _drop_all(role, rt, pt)
        _drop_roles(group)
