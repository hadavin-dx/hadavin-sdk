"""`migrate()` against a real PostgreSQL: a late number, a newer database, the read-back after each file
(planted files), a hidden COMMIT, an older release's structure after the newest migrations.

Every test works in a fresh scratch schema of the test database (`HADAVIN_TEST_PG_DSN`). Planted files are made up.
A skip is a failed evidence run (with the DSN set none can happen: `tests/test_migration_rules.py` checks it); in CI `test_ci_has_its_inputs` fails when the database or `psql` is missing."""

from __future__ import annotations

import contextlib
import os
import shutil
import subprocess
import threading
import uuid
from pathlib import Path

import pytest

from hadavin_sdk.errors import ConfigError
from tests.fixtures import runbook as rb
from tests.fixtures.dsn_skip import require_module
from tests.fixtures.migration_role import PLAIN_ROLE, ensure_plain_role

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
    """The owner of the trigger function is read back: handing it to another role is a trigger change. Killed by: mutant T7
    (function owner not compared) of tests/migrate_mutants.py."""
    dsn, schema = scratch
    other = "hadavin_test_fo_" + uuid.uuid4().hex[:8]
    _create_roles(other)
    with psycopg.connect(DSN, autocommit=True) as db:
        db.execute(
            sql.SQL("GRANT CREATE ON SCHEMA {} TO {}").format(
                sql.Identifier(schema), sql.Identifier(other)
            )
        )
    _let_the_plain_role_grant(
        other
    )  # the plain role may give an object to a role it is a member of
    try:
        mig.migrate(dsn)
        body = f"ALTER FUNCTION hadavin_audit_append_only() OWNER TO {other};\n"
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
                db.execute(
                    sql.SQL("CREATE ROLE {} LOGIN NOSUPERUSER PASSWORD {}").format(
                        sql.Identifier(role), sql.Literal(login_password)
                    )
                )
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
    try:
        mig.migrate(dsn)
        _with_files(monkeypatch, tmp_path, {"0006_grant.sql": body})
        with pytest.raises(ConfigError) as e:
            mig.migrate(dsn)
        msg = str(e.value)
        assert "0006_grant.sql" in msg and f"role {a} has a new member {b}" in msg, msg
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
        assert "admin_option" in msg, msg  # the changed column is named
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
        assert "checking and granting the roles" in text and "lock_timeout" in text, text
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
    """(dsn of a login role with none of the four flags, schema); the role is dropped afterwards."""
    dsn, schema = scratch
    role = f"mig_{uuid.uuid4().hex[:10]}"
    with psycopg.connect(DSN, autocommit=True) as db:
        db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(role)))
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
        yield make_conninfo(dsn, user=role), role
    finally:
        with psycopg.connect(DSN, autocommit=True) as db:
            db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
            db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


@needs_pg
@pytest.mark.real_connect
@pytest.mark.parametrize("flag", ["SUPERUSER", "CREATEROLE", "CREATEDB", "BYPASSRLS"])
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
    }[flag] in str(e.value)
    assert "CREATE ROLE migration_role LOGIN NOSUPERUSER" in str(e.value), (
        "the message says how to make a plain role"
    )
    assert _ledger(dsn) is None, "nothing was created"


@needs_pg
@pytest.mark.real_connect
@pytest.mark.parametrize("inherit", ["TRUE", "FALSE"])
def test_a_plain_role_that_is_a_member_of_a_privileged_role_is_refused_by_a_real_server(
    plain_role, inherit
):
    """A member of a role with CREATEROLE can use or `SET ROLE` to it, so the plain login alone is not enough."""
    dsn, role = plain_role
    boss = role + "_boss"
    with psycopg.connect(DSN, autocommit=True) as db:
        db.execute(sql.SQL("CREATE ROLE {} NOLOGIN CREATEROLE").format(sql.Identifier(boss)))
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
    """The helper changes the owner of the schema in use: on `public` it must refuse and change nothing."""
    from tests.fixtures.migration_role import NotAScratchSchema, plain_role_connect

    owner_sql = "SELECT nspowner::regrole::text FROM pg_namespace WHERE nspname = 'public'"
    with psycopg.connect(DSN, autocommit=True) as db:
        before = db.execute(owner_sql).fetchone()
    with pytest.raises(NotAScratchSchema):
        plain_role_connect(psycopg.connect)(DSN, autocommit=True)
    with psycopg.connect(DSN, autocommit=True) as db:
        assert db.execute(owner_sql).fetchone() == before


@needs_pg
@pytest.mark.real_connect
def test_a_plain_migration_role_runs_with_the_real_connect(plain_role):
    """There is no override: a login role with none of the four flags runs `migrate()` with the real `connect`."""
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
    them, a file that alters a table applies. Killed by: mutant O1 (the ownership check is not called)."""
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
    with psycopg.connect(DSN, autocommit=True) as db:
        login = db.execute("SELECT current_user").fetchone()[0]
    assert "ALTER TABLE" in msg and "audit_entries" in msg and f"owner {login}" in msg, msg
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
    scratch, plain_role
):
    """A database the plain role built, except one table and one function that the superuser login made: both are named
    and the `ALTER` lines say TABLE and FUNCTION; objects the role owns are not listed."""
    dsn, _role = plain_role
    super_dsn, _ = scratch
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
    super_dsn, _ = scratch
    other = role + "_b"
    with psycopg.connect(DSN, autocommit=True) as db:
        db.execute(sql.SQL("CREATE ROLE {}").format(sql.Identifier(other)))
        try:
            db.execute(
                sql.SQL("GRANT {} TO {}").format(sql.Identifier(other), sql.Identifier(role))
            )
            db.execute(sql.SQL("GRANT pg_signal_backend TO {}").format(sql.Identifier(role)))
            login = make_conninfo(
                super_dsn,
                user=role,
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
        assert (
            mig.migrate(make_conninfo(super_dsn, user=role), runtime_role=rt, portal_role=pt)
            == REAL
        )
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
    really can use the schema afterwards and refuses. Killed by: mutant GO2 (the check is gone)."""
    super_dsn, schema = scratch
    role, rt, pt = _role_from_the_printed_sql(schema, grant_option=False)
    try:
        with pytest.raises(ConfigError, match="cannot use the schema"):
            mig.migrate(make_conninfo(super_dsn, user=role), runtime_role=rt)
        assert _ledger(super_dsn) is None, "the refusal rolled everything back"
    finally:
        _drop_all(role, rt, pt)


# --- objects another role owns: kinds, partitions, names, cap, safe owners, extensions -----------------------------------


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
    scratch, plain_role, tmp_path
):
    """`ALTER FUNCTION` fails on a procedure or an aggregate; the line says PROCEDURE or AGGREGATE, and a function that
    takes arguments keeps them. Killed by: mutant FO1 (every routine is printed as FUNCTION)."""
    dsn, _role = plain_role
    super_dsn, _ = scratch
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
def test_a_partition_owned_by_another_role_is_listed(scratch, plain_role):
    """A partition has an automatic dependency on its parent, but it is a table of its own that the plain role cannot
    change. Killed by: mutant FO2 (the dependency test hides it)."""
    dsn, role = plain_role
    super_dsn, _ = scratch
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
def test_a_name_with_a_newline_is_never_copied_into_a_printed_statement(scratch, plain_role):
    """The other role chose the table's name. The list shows it escaped; no statement is printed for it, and the message
    says a person must write that one by hand. Killed by: mutant FO3 (every name is printed)."""
    dsn, _role = plain_role
    super_dsn, _ = scratch
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
    scratch, plain_role, tmp_path
):
    """The cap is for the names in the list only; a person needs every `ALTER` line. Killed by: mutant FO4."""
    dsn, _role = plain_role
    super_dsn, _ = scratch
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
    extension, and one that puts a view into the schema covers the table half. Killed by: mutants EX1 (the extension
    test is gone from the function half) and EX2 (gone from the table half)."""
    dsn, _role = plain_role
    super_dsn, _ = scratch
    assert mig.migrate(dsn) == REAL
    with psycopg.connect(super_dsn, autocommit=True) as db:
        db.execute(
            sql.SQL("CREATE EXTENSION citext SCHEMA {}").format(
                sql.Identifier(conninfo_to_dict(super_dsn)["options"].rsplit("search_path=", 1)[1])
            )
        )
        db.execute(
            sql.SQL("CREATE EXTENSION pg_stat_statements SCHEMA {}").format(
                sql.Identifier(conninfo_to_dict(super_dsn)["options"].rsplit("search_path=", 1)[1])
            )
        )
    assert mig.migrate(dsn) == []


@needs_pg
@pytest.mark.real_connect
def test_the_function_half_of_the_ownership_check_finds_a_function_alone(scratch, plain_role):
    """Only a function is foreign (no table). Killed by: mutant OW2 (the function half finds nothing)."""
    dsn, _role = plain_role
    super_dsn, _ = scratch
    assert mig.migrate(dsn) == REAL
    with psycopg.connect(super_dsn, autocommit=True) as db:
        db.execute("CREATE FUNCTION hadavin_test_only_fn() RETURNS int LANGUAGE sql AS 'SELECT 1'")
    with pytest.raises(ConfigError, match=r"cannot change 1 object"):
        mig.migrate(dsn)
