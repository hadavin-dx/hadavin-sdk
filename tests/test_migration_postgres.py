"""`migrate()` against a real PostgreSQL (P3a-2): a late number, a newer database, the read-back after each file
(planted files), a hidden COMMIT, an older release's structure after the newest migrations.

Every test works in a fresh scratch schema of the test database (`HADAVIN_TEST_PG_DSN`). Planted files are made up.
A skip is a failed evidence run (with the DSN set none can happen: `tests/test_migration_rules.py` checks it); in CI `test_ci_has_its_inputs` fails when the database or `psql` is missing."""

from __future__ import annotations

import os
import shutil
import subprocess
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
# The newest migration of the previous release (the lead sets it when the first tag exists; no tag yet).
PREVIOUS_RELEASE_LAST = "0004_audit_checkpoint_meta"
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


@needs_pg
def test_the_previous_release_columns_survive_the_newest_migrations(scratch):
    """Build the previous release's schema (files up to PREVIOUS_RELEASE_LAST), record every column, apply the
    rest: every old column is still there with the same type and nullability, and the old code's reads still run
    (a new column may be added; an old one may not go, change type or become NOT NULL without a named exception)."""
    dsn, _ = scratch
    upto = REAL.index(PREVIOUS_RELEASE_LAST) + 1
    _apply_by_hand(dsn, REAL[:upto])
    old = _columns(dsn)
    assert old, "the previous release has tables"
    with psycopg.connect(dsn, autocommit=True) as db:
        db.execute("INSERT INTO audit_checkpoints (seq, hash, signature) VALUES (1, 'h', 's')")
    assert mig.migrate(dsn) == REAL[upto:]
    new = _columns(dsn)
    lost = sorted(set(old) - set(new))
    changed = sorted(k for k in old if k in new and old[k] != new[k] and k not in ACCEPTED_CHANGES)
    assert not lost, f"columns of the previous release are gone: {lost}"
    assert not changed, f"columns of the previous release changed type or nullability: {changed}"
    with psycopg.connect(
        dsn, autocommit=True
    ) as db:  # the old reader: the old column list on every old table
        for table in sorted({t for t, _ in old}):
            cols = ", ".join(f'"{c}"' for t, c in sorted(old) if t == table)
            db.execute(f'SELECT {cols} FROM "{table}" LIMIT 1').fetchall()  # noqa: S608 - names from the catalog
        assert db.execute("SELECT seq, hash, signature FROM audit_checkpoints").fetchall() == [
            (1, "h", "s")
        ]


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
    path = tmp_path / "hand.sql"
    path.write_text(rb.hand_file(schema, *steps), encoding="utf-8")
    assert rb.PSQL_ARGS == [
        "psql",
        "-X",
        "-v",
        "ON_ERROR_STOP=1",
    ]  # the rule of the runbook, written out below
    return subprocess.run(
        ["/usr/bin/env", "psql", "-X", "-v", "ON_ERROR_STOP=1", "-f", "hand.sql"],
        check=False,
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
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
