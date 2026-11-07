"""`migrate()` against a real PostgreSQL (P3a-2): a late number, a newer database, the read-back after each file
(planted files), a hidden COMMIT, an older release's structure after the newest migrations.

Every test works in a fresh scratch schema of the test database (`HADAVIN_TEST_PG_DSN`). Planted files are made up.
A skip is a failed evidence run (with the DSN set none can happen: `tests/test_migration_rules.py` checks it); in CI `test_ci_has_its_inputs` fails when the database or `psql` is missing."""

from __future__ import annotations

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

psycopg = require_module("psycopg")  # with the DSN set a missing driver FAILS (never a skip)
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from hadavin_sdk.store import migrate as mig
from hadavin_sdk.store.migration_numbers import MigrationNumberError

DSN = os.environ.get("HADAVIN_TEST_PG_DSN")
needs_pg = pytest.mark.skipif(
    not DSN, reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)"
)
# The newest migration of the previous release. No tag or release exists yet (checked 2026-11-07: `git tag` is empty,
# the GitHub releases and tags lists are empty, CHANGELOG.md says "Unreleased"), so, as order 89 (q195) says, the last
# migration on main is the released base: 0005_evidence (on main since ce70eb5, 2026-11-04). The lead moves this
# constant when the first tag exists.
PREVIOUS_RELEASE_LAST = "0005_evidence"
# Nothing in the real folder follows it today, so the test below also plants a newer file of its own (it is never empty).
PLANTED_NEXT = "0006_p3a_next.sql"
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
    schema = f"p3a_{uuid.uuid4().hex[:12]}"
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
    with psycopg.connect(dsn, autocommit=True) as db:
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


# --- H11: what a file leaves changed is found by the read-back and the whole run is rolled back ---------------------

_FLIP = (
    "CREATE OR REPLACE FUNCTION p3a_flip(item TEXT, val TEXT) RETURNS void LANGUAGE plpgsql AS $$\n"
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
    "replication_role": (
        _FLIP + "SELECT p3a_flip('session_replication_role', 'replica');\n",
        "session_replication_role",
    ),
    "search_path": (_FLIP + "SELECT p3a_flip('search_path', 'public');\n", "search_path"),
    "scs": (
        _FLIP + "SELECT p3a_flip('standard_conforming_strings', 'off');\n",
        "standard_conforming_strings",
    ),
    "backslash_quote": (_FLIP + "SELECT p3a_flip('backslash_quote', 'on');\n", "backslash_quote"),
    "encoding": (_FLIP + "SELECT p3a_flip('client_encoding', 'LATIN1');\n", "client_encoding"),
}


@needs_pg
@pytest.mark.parametrize("plant", sorted(PLANTS))
def test_h11_the_read_back_refuses_a_planted_file(scratch, monkeypatch, tmp_path, plant):
    dsn, _ = scratch
    mig.migrate(dsn)  # call 1: the real folder
    body, item = PLANTS[plant]
    _with_files(monkeypatch, tmp_path, {"0006_p3a_plant.sql": body})
    with pytest.raises(ConfigError) as e:  # call 2: real folder plus the planted file
        mig.migrate(dsn)
    assert "0006_p3a_plant.sql" in str(e.value) and item in str(e.value), str(e.value)
    assert not str(e.value).startswith("migrations are inconsistent"), (
        "it is the read-back, not the scan"
    )
    assert _ledger(dsn) == REAL, "the ledger holds the five real stems and no planted stem"
    with psycopg.connect(
        dsn, autocommit=True
    ) as db:  # the trigger the plant touched is still in force
        row = db.execute(
            "SELECT tgenabled FROM pg_trigger WHERE tgname = 'audit_entries_no_truncate'"
        ).fetchone()
    assert row == ("O",)


@needs_pg
def test_h11_a_role_switched_inside_a_file_is_refused(scratch, monkeypatch, tmp_path):
    dsn, _ = scratch
    role = "p3a_r_" + uuid.uuid4().hex[:8]
    body = (
        "CREATE OR REPLACE FUNCTION p3a_switch() RETURNS void LANGUAGE plpgsql AS $$\n"
        f"BEGIN EXECUTE 'SET LOCAL ROLE {role}'; END $$;\nSELECT p3a_switch();\n"
    )
    with psycopg.connect(DSN, autocommit=True) as db:
        db.execute(sql.SQL("CREATE ROLE {}").format(sql.Identifier(role)))
    try:
        mig.migrate(dsn)
        _with_files(monkeypatch, tmp_path, {"0006_p3a_role.sql": body})
        with pytest.raises(ConfigError) as e:
            mig.migrate(dsn)
        assert "current_user" in str(e.value) and "0006_p3a_role.sql" in str(e.value)
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


def _drop_roles(*roles: str) -> None:
    with psycopg.connect(DSN, autocommit=True) as db:
        for role in roles:
            db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
            db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


@needs_pg
@pytest.mark.parametrize("how", ["function_body", "function_body_with_admin_option"])
def test_h11_a_role_grant_hidden_in_a_function_body_is_refused(scratch, monkeypatch, tmp_path, how):
    """Design F1: the statement rule reads `GRANT r TO s` only at the start of a statement; here it sits in a `$$` body
    and the file then calls the function. The read-back of `pg_auth_members` refuses it and nothing is kept.
    Killed by: mutant R1 (membership not compared) and mutant R2 (membership not read after the file)."""
    dsn, _ = scratch
    a, b = "p3a_ga_" + uuid.uuid4().hex[:8], "p3a_gb_" + uuid.uuid4().hex[:8]
    option = " WITH ADMIN OPTION" if how.endswith("admin_option") else ""
    body = (
        "CREATE OR REPLACE FUNCTION p3a_grant() RETURNS void LANGUAGE plpgsql AS $$\n"
        f"BEGIN GRANT {a} TO {b}{option}; END $$;\nSELECT p3a_grant();\n"
    )
    _create_roles(a, b)
    try:
        mig.migrate(dsn)
        _with_files(monkeypatch, tmp_path, {"0006_p3a_grant.sql": body})
        with pytest.raises(ConfigError) as e:
            mig.migrate(dsn)
        msg = str(e.value)
        assert "0006_p3a_grant.sql" in msg and f"role {a} has a new member {b}" in msg, msg
        assert not msg.startswith("migrations are inconsistent"), "the read-back, not the scan"
        assert _ledger(dsn) == REAL
        with psycopg.connect(DSN, autocommit=True) as db:
            assert db.execute("SELECT pg_has_role(%s, %s, 'MEMBER')", (b, a)).fetchone() == (False,)
    finally:
        _drop_roles(a, b)


@needs_pg
def test_h11_a_grant_of_a_role_that_was_a_member_before_is_not_a_refusal(
    scratch, monkeypatch, tmp_path
):
    """The baseline is the membership at the start: a file that changes nothing about it passes."""
    dsn, _ = scratch
    a, b = "p3a_ma_" + uuid.uuid4().hex[:8], "p3a_mb_" + uuid.uuid4().hex[:8]
    _create_roles(a, b)
    try:
        with psycopg.connect(DSN, autocommit=True) as db:
            db.execute(sql.SQL("GRANT {} TO {}").format(sql.Identifier(a), sql.Identifier(b)))
        _with_files(monkeypatch, tmp_path, {"0006_p3a_ok.sql": "SELECT 1;\n"})
        assert mig.migrate(dsn) == [*REAL, "0006_p3a_ok"]
    finally:
        _drop_roles(a, b)


@pytest.fixture
def owner_dsn(scratch):
    """(dsn, other role) for a LOGIN role that is NOT a superuser, owns what it creates in the scratch schema and may
    switch to `other` (a membership that exists BEFORE migrate starts, so it is part of the baseline)."""
    dsn, schema = scratch
    owner, other = "p3a_own_" + uuid.uuid4().hex[:8], "p3a_oth_" + uuid.uuid4().hex[:8]
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
    """M-3: the docs say run migrate with a role that is not a superuser; every other test connects as the superuser.
    Here the migration role is a plain LOGIN owner: the real files apply, a DISABLE TRIGGER and a SET LOCAL ROLE are
    refused with the same read-back messages as for a superuser, and a second run with the real files is clean.
    Killed by: mutant M61 (read-back removed from migrate()), as for the superuser plants this test repeats."""
    dsn, other = owner_dsn
    with psycopg.connect(dsn, autocommit=True) as db:
        assert db.execute("SELECT current_setting('is_superuser')").fetchone() == ("off",)
    assert mig.migrate(dsn) == REAL
    assert mig.migrate(dsn) == []
    plants = {
        "0006_p3a_dis.sql": (
            "ALTER TABLE audit_entries DISABLE TRIGGER audit_entries_no_truncate;\n",
            "audit_entries_no_truncate",
        ),
        "0006_p3a_role.sql": (
            (
                "CREATE OR REPLACE FUNCTION p3a_switch() RETURNS void LANGUAGE plpgsql AS $$\n"
                f"BEGIN EXECUTE 'SET LOCAL ROLE {other}'; END $$;\nSELECT p3a_switch();\n"
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
        {"0006_p3a_drop.sql": "DROP TRIGGER audit_entries_no_truncate ON audit_entries;\n"},
    )
    with pytest.raises(ConfigError) as e:
        mig.migrate(dsn)
    assert "0006_p3a_drop.sql" in str(e.value) and "audit_entries_no_truncate" in str(e.value)
    assert not _ledger(dsn), "the ledger does not exist or holds no row"


@needs_pg
def test_a_hidden_commit_is_found_by_the_transaction_backstop(scratch, monkeypatch, tmp_path):
    """The text rule refuses COMMIT; with that rule switched off in the test, the clock and id read-back still
    sees the new transaction after the file (the backstop for a COMMIT the text rules cannot see)."""
    dsn, _ = scratch
    monkeypatch.setattr(mig, "refused_statements", lambda text: [])
    _with_files(monkeypatch, tmp_path, {"0006_p3a_commit.sql": "SELECT 1;\nCOMMIT;\n"})
    with pytest.raises(ConfigError) as e:
        mig.migrate(dsn)
    msg = str(e.value)
    assert (
        "0006_p3a_commit.sql" in msg and "transaction_timestamp" in msg and "txid_current" in msg
    ), msg
    assert "0006_p3a_commit" not in (_ledger(dsn) or [])


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
    other = "p3a_o_" + uuid.uuid4().hex[:8]
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
    try:
        mig.migrate(dsn)
        body = f'ALTER TABLE "{other}".t DISABLE TRIGGER trg;\n'
        _with_files(monkeypatch, tmp_path, {"0006_p3a_other.sql": body})
        assert mig.migrate(dsn) == ["0006_p3a_other"]
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
            cols = ", ".join(f'"{c}"' for t, c in sorted(old) if t == table)
            db.execute(f'SELECT {cols} FROM "{table}" LIMIT 1').fetchall()  # noqa: S608 - names from the catalog
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
    Killed by: mutant R11 (the planted file is not added: the test would apply nothing and say nothing)."""
    dsn, _ = scratch
    old, new = _old_and_new_columns(
        dsn, monkeypatch, tmp_path, "ALTER TABLE audit_checkpoints ADD COLUMN p3a_note TEXT;\n"
    )
    assert ("audit_checkpoints", "p3a_note") in new, "the planted newer file ran"
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
    """The comparison above is a real check: a newer file that drops or retypes an old column is reported.
    Killed by: mutant R10a (`lost` always empty) for the drop, R10b (`changed` always empty) for the retype."""
    dsn, _ = scratch
    old, new = _old_and_new_columns(dsn, monkeypatch, tmp_path, planted)
    lost, changed = _problems(old, new)
    assert (lost_key in lost) if lost_key else (changed_key in changed), (lost, changed)


def test_the_constant_is_the_last_migration_on_main():
    """Order 89 (q195): there is no release tag, so the last migration on main is the released base. A newer real file
    arriving in the folder does not move it; the lead does, when the first tag exists.
    Killed by: mutant R9 (the constant set back to 0004_audit_checkpoint_meta)."""
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


# --- the recipe a refusal prints, RUN with psql (ticket H1 and H4), and the hand-file header --------------------------------


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
    """H1: the lines between the two RECIPE lines of the refusal message, saved to a file and run with
    `psql -X -v ON_ERROR_STOP=1 -f`, apply the late file and its ledger row; `migrate()` then has nothing to do.
    Killed by: mutant R12 (hand_recipe leaves out the ledger INSERT) and R13 (the recipe leaves out the file's SQL)."""
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
    """H4: a late file whose second statement fails: the first statement, the ledger row and the lock are all undone.
    Killed by: mutant R14 (the recipe has no BEGIN) and R15 (the recipe's first line `\\set ON_ERROR_STOP on` removed)."""
    dsn, _ = scratch
    _apply_by_hand(dsn, [s for s in REAL if s != "0004_audit_checkpoint_meta"])
    body = "INSERT INTO audit_checkpoints (seq, hash, signature) VALUES (7, 'a', 'b');\nSELECT 1 / 0;\n"
    planted = tmp_path / "0004_p3a_late_fail.sql"  # takes the place of the real 0004
    planted.write_text(body, encoding="utf-8")
    files = [p for p in mig._migration_files() if p.stem != "0004_audit_checkpoint_meta"] + [
        planted
    ]
    monkeypatch.setattr(mig, "_migration_files", lambda: files)
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
    with an error code instead of 0 (without the line it carries on and exits 0 although a statement failed).
    Killed by: mutant R15 (the first line removed)."""
    dsn, _ = scratch
    _apply_by_hand(dsn, [s for s in REAL if s != "0004_audit_checkpoint_meta"])
    planted = tmp_path / "0004_p3a_late_fail.sql"
    planted.write_text("SELECT 1 / 0;\n", encoding="utf-8")
    files = [p for p in mig._migration_files() if p.stem != "0004_audit_checkpoint_meta"] + [
        planted
    ]
    monkeypatch.setattr(mig, "_migration_files", lambda: files)
    with pytest.raises(MigrationNumberError) as e:
        mig.migrate(dsn)
    done = _psql_text(tmp_path, _recipe_of(str(e.value)), stop_flag=False)
    assert done.returncode != 0 and "division by zero" in done.stderr, done.stderr
    assert "0004_p3a_late_fail" not in _ledger(dsn)


@needs_pg
def test_the_recipe_and_the_runbook_header_start_with_the_timeouts(scratch):
    """F2: both headers carry the two SET LOCAL lines right after BEGIN and before the lock.
    Killed by: mutant R16 (the recipe has no timeouts)."""
    dsn, _ = scratch
    lines = _recipe_of(_late_0004_message(dsn)).splitlines()
    at = lines.index("BEGIN;")
    assert lines[at + 1 : at + 3] == list(rb.TIMEOUTS)
    assert lines[at + 3].startswith("SELECT pg_advisory_xact_lock(")


@needs_pg
def test_a_hand_file_waiting_for_a_table_lock_stops_after_the_lock_timeout(scratch, tmp_path):
    """F2, run: another session holds ACCESS EXCLUSIVE on `tool_calls`; the hand file does not queue behind it for
    ever (and so does not stop every reader of a live table): it fails when the lock limit of `RECIPE_TIMEOUTS` runs out and keeps nothing.
    Killed by: mutant R16b (the timeouts left out of the runbook header helper)."""
    dsn, schema = scratch
    mig.migrate(dsn)
    with psycopg.connect(dsn) as holder:
        holder.execute("LOCK TABLE tool_calls IN ACCESS EXCLUSIVE MODE")
        done = _psql(schema, tmp_path, "ALTER TABLE tool_calls ADD COLUMN p3a_wait TEXT;")
    assert done.returncode != 0 and "lock timeout" in done.stderr, done.stderr
    assert ("tool_calls", "p3a_wait") not in _columns(dsn)


@needs_pg
def test_case_a_current_user_assertion_stops_the_file_for_the_wrong_role(scratch, tmp_path):
    """F7: the DO block of case (a) raises unless current_user is the named migration role.
    Killed by: mutant R17 (the block's comparison reversed)."""
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
    if tables:
        _sql(dsn, (mig.MIGRATIONS / "0005_evidence.sql").read_text(encoding="utf-8"))
        if not error_column:
            _sql(dsn, "ALTER TABLE tool_calls DROP COLUMN error")
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
        steps += [(mig.MIGRATIONS / "0005_evidence.sql").read_text(encoding="utf-8"), insert]
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
    """E1. Killed by: mutant R18 (case (e) loses 'always put the block of case (g)': the error_missing run keeps the broken table) via the text pin, and by mutant R19 (E1's UPDATE names the wrong row)."""
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


# --- migrate() sets the same limits as the hand recipe (order 140, F2 drift), RUN --------------------------------------------

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
    """F2: another session holds ACCESS EXCLUSIVE on `tool_calls`; `migrate` does not queue behind it for ever: the
    limit of `mig.RECIPE_TIMEOUTS` (patched short here) ends the run, nothing is kept, no ledger row.
    Killed by: mutants R26 (the limits not set), R28 (the lock-wait line left out)."""
    dsn, _ = scratch
    mig.migrate(dsn)
    before = _ledger(dsn)
    monkeypatch.setattr(mig, "RECIPE_TIMEOUTS", SHORT_LOCK)
    _with_files(
        monkeypatch, tmp_path, {PLANTED_NEXT: "ALTER TABLE tool_calls ADD COLUMN p3a_wait TEXT;\n"}
    )
    with psycopg.connect(dsn) as holder:
        holder.execute("LOCK TABLE tool_calls IN ACCESS EXCLUSIVE MODE")
        # Without a limit `migrate` would wait for ever: let go of the lock after a while, so that the old code FAILS
        # this test (the run succeeds, nothing raises) instead of hanging it.
        let_go = threading.Timer(WAIT_LIMIT_S, holder.rollback)
        let_go.start()
        try:
            with pytest.raises(psycopg.errors.LockNotAvailable):
                mig.migrate(dsn)
        finally:
            let_go.cancel()
    assert _ledger(dsn) == before
    assert ("tool_calls", "p3a_wait") not in _columns(dsn)


@needs_pg
def test_migrate_stops_a_file_that_runs_past_the_statement_limit(scratch, monkeypatch, tmp_path):
    """F2: a file whose statement runs longer than the statement limit of `mig.RECIPE_TIMEOUTS` (patched short here)
    fails the run and keeps nothing. Killed by: mutants R26 (the limits not set), R28 (the statement line left out)."""
    dsn, _ = scratch
    mig.migrate(dsn)
    before = _ledger(dsn)
    monkeypatch.setattr(mig, "RECIPE_TIMEOUTS", SHORT_STATEMENT)
    _with_files(monkeypatch, tmp_path, {PLANTED_NEXT: "SELECT pg_sleep(30);\n"})
    with pytest.raises(psycopg.errors.QueryCanceled):
        mig.migrate(dsn)
    assert _ledger(dsn) == before


@needs_pg
def test_the_limits_migrate_runs_with_are_the_ones_in_the_constant(scratch, monkeypatch, tmp_path):
    """F2: a planted file reads the two settings from the server inside the run (`1/0` when one differs): they are the
    values of `mig.RECIPE_TIMEOUTS` (patched to values that print back unchanged), and a wrong expectation fails, so
    the probe can fail. Killed by: mutants R26 (not set), R28 (one line left out), R34 (a literal value in migrate)."""
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

    _with_files(monkeypatch, tmp_path, {PLANTED_NEXT: probe("99s")})
    with pytest.raises(psycopg.errors.DivisionByZero):
        mig.migrate(dsn)
    monkeypatch.undo()
    monkeypatch.setattr(
        mig,
        "RECIPE_TIMEOUTS",
        ("SET LOCAL lock_timeout = '7s';", "SET LOCAL statement_timeout = '9s';"),
    )
    _with_files(monkeypatch, tmp_path, {PLANTED_NEXT: probe(lock_t)})
    assert mig.migrate(dsn)[-1] == PLANTED_NEXT[:-4]
