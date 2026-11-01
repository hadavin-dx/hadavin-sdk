"""K2 Upgrade safety and audit integrity: the migration ledger, the one grant map, the portal role, and the
stored-plan hash. The database tests need HADAVIN_TEST_PG_DSN (CI: the postgres service) and skip without it."""

import json
import uuid
from pathlib import Path
from typing import ClassVar

import pytest

from hadavin_sdk import cli
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.models import Plan
from hadavin_sdk.store import migrate as mig
from tests.contracts.kinds.store_postgres import pg_schema

FIXTURE = Path(__file__).parent / "fixtures" / "plan_v1.json"


def _dir(tmp_path: Path, files: dict[str, str]) -> list[Path]:
    for name, text in files.items():
        (tmp_path / name).write_text(text, encoding="utf-8")
    return sorted(tmp_path.glob("*.sql"))


# --- ledger -------------------------------------------------------------------------------------------


def test_the_real_ledger_and_grant_map_agree_with_the_migrations():
    files = mig._migration_files()
    assert len(files) >= 4, "the scan would check nothing"
    assert mig.check_ledger(files) == []
    assert mig.check_grants(files) == []


def test_plant_duplicate_number_is_caught(tmp_path):
    files = _dir(tmp_path, {"0001_a.sql": "", "0002_b.sql": "", "0002_c.sql": ""})
    assert mig.check_ledger(files) == ["two migrations are numbered 0002"]


def test_plant_gap_is_caught(tmp_path):
    files = _dir(tmp_path, {"0001_a.sql": "", "0003_b.sql": ""})
    assert mig.check_ledger(files) == ["migration 0002 is missing"]


def test_plant_first_file_not_numbered_one_is_caught(tmp_path):
    assert mig.check_ledger(_dir(tmp_path, {"0002_a.sql": ""})) == ["migration 0001 is missing"]


def test_plant_badly_named_file_is_caught(tmp_path):
    files = _dir(tmp_path, {"0001_a.sql": "", "5_b.sql": "", "0002_Bad.sql": ""})
    assert mig.check_ledger(files) == [
        "0002_Bad.sql: not named NNNN_<name>.sql",
        "5_b.sql: not named NNNN_<name>.sql",
    ]


# --- the grant map -----------------------------------------------------------------------------------


def test_plant_table_missing_from_the_map_is_caught(tmp_path):
    files = _dir(tmp_path, {"0001_a.sql": "CREATE TABLE runs (\n    id TEXT\n);\n"})
    problems = mig.check_grants(files)
    assert "runs" not in " ".join(problems[:1]), problems  # runs is mapped
    files = _dir(tmp_path, {"0001_a.sql": "CREATE TABLE brand_new (\n    id TEXT\n);\n"})
    assert "brand_new (table) is created by a migration but is not in GRANTS" in mig.check_grants(
        files
    )


def test_plant_view_missing_from_the_map_is_caught(tmp_path):
    files = _dir(tmp_path, {"0001_a.sql": "CREATE OR REPLACE VIEW run_summary AS SELECT 1;\n"})
    assert "run_summary (view) is created by a migration but is not in GRANTS" in mig.check_grants(
        files
    )


def test_plant_serial_sequence_missing_from_the_map_is_caught(tmp_path):
    sql_text = "CREATE TABLE IF NOT EXISTS events (\n    seq BIGSERIAL PRIMARY KEY\n);\n"
    problems = mig.check_grants(_dir(tmp_path, {"0001_a.sql": sql_text}))
    assert "events_seq_seq (sequence) is created by a migration but is not in GRANTS" in problems


def test_a_table_named_only_in_a_comment_is_not_created(tmp_path):
    files = _dir(tmp_path, {"0001_a.sql": "-- CREATE TABLE ghost (x INT);\n/* CREATE VIEW v */\n"})
    assert not any("ghost" in p or " v " in p for p in mig.check_grants(files))


def test_plant_map_entry_with_no_migration_is_caught(tmp_path):
    problems = mig.check_grants(_dir(tmp_path, {"0001_a.sql": "SELECT 1;\n"}))
    assert "GRANTS names runs, which no migration creates" in problems


def test_plant_wrong_kind_is_caught(tmp_path):
    files = _dir(tmp_path, {"0001_a.sql": "CREATE VIEW runs AS SELECT 1;\n"})
    assert "GRANTS says runs is a table; the migrations create a view" in mig.check_grants(files)


def test_the_portal_relations_exclude_the_never_list():
    portal = {n for n, g in mig.GRANTS.items() if g.portal}
    assert not portal & {"redaction_maps", "events", "tick_state", "kill_switch", "audit_outbox"}
    assert {"runs", "plans", "audit_entries", "audit_checkpoints"} <= portal
    assert all(g.kind != "sequence" for g in mig.GRANTS.values() if g.portal)


def test_migrate_refuses_an_inconsistent_ledger_before_connecting(monkeypatch, tmp_path):
    files = _dir(tmp_path, {"0001_a.sql": "CREATE TABLE brand_new (\n    id TEXT\n);\n"})
    monkeypatch.setattr(mig, "_migration_files", lambda: files)

    def no_db(*a, **k):
        raise AssertionError("connected")

    monkeypatch.setattr(mig, "connect", no_db)
    with pytest.raises(ConfigError, match="brand_new"):
        mig.migrate("postgresql://unused")


def test_migrate_refuses_one_role_for_runtime_and_portal():
    with pytest.raises(ConfigError, match="different roles"):
        mig.migrate("postgresql://unused", runtime_role="same_role", portal_role="same_role")


def test_portal_role_must_be_a_plain_name():
    with pytest.raises(ConfigError, match="plain database role"):
        mig.migrate("postgresql://unused", portal_role="x; DROP TABLE runs")


def test_cli_migrate_passes_the_portal_role(cfg_dir, monkeypatch):
    import yaml

    path = cfg_dir / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["backends"]["store"] = {"kind": "postgres", "dsn_secret_name": "pg-dsn"}
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    monkeypatch.setenv("HADAVIN_MIGRATE_DSN", "postgresql://unused")
    seen = {}

    def fake(dsn, **kw):
        seen.update(kw)
        return []

    monkeypatch.setattr("hadavin_sdk.store.migrate.migrate", fake)
    args = ["--config", str(cfg_dir), "migrate", "--runtime-role", "rt", "--portal-role", "pt"]
    assert cli.main(args) == 0
    assert (seen["runtime_role"], seen["portal_role"]) == ("rt", "pt")


# --- plan hash ---------------------------------------------------------------------------------------


def test_a_stored_v1_plan_rehashes_to_its_stored_hash():
    stored = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert Plan(**stored["plan"]).hash() == stored["hash"]


def test_every_plan_field_after_v1_is_in_the_omit_set():
    """When Plan gains a field, this fails until it joins `_HASH_OMIT_IF_DEFAULT` (the v1 hash stays put)."""
    v1 = set(json.loads(FIXTURE.read_text(encoding="utf-8"))["plan"])
    assert set(Plan.model_fields) - v1 <= Plan._HASH_OMIT_IF_DEFAULT
    assert Plan._HASH_OMIT_IF_DEFAULT <= set(Plan.model_fields)


def test_a_new_field_at_its_default_leaves_the_v1_hash_and_a_set_value_changes_it():
    class PlanV2(Plan):
        _HASH_OMIT_IF_DEFAULT: ClassVar[frozenset[str]] = frozenset({"note"})
        note: str = ""

    stored = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert PlanV2(**stored["plan"]).hash() == stored["hash"]
    assert PlanV2(**stored["plan"], note="x").hash() != stored["hash"]


def test_a_new_field_not_in_the_omit_set_would_change_the_v1_hash():
    class PlanV2(Plan):
        note: str = ""

    stored = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert PlanV2(**stored["plan"]).hash() != stored["hash"]  # why the omit set exists


# --- with a database ---------------------------------------------------------------------------------


def _can(db, role, relation, priv):
    q = "SELECT has_table_privilege(%s, %s, %s)"
    return db.execute(q, (role, relation, priv)).fetchone()[0]


def _seq_can(db, role, relation, priv):
    q = "SELECT has_sequence_privilege(%s, %s, %s)"
    return db.execute(q, (role, relation, priv)).fetchone()[0]


@pytest.fixture
def roles():
    """A migrated schema and two fresh login roles, runtime and portal; dropped afterwards."""
    import psycopg
    from psycopg import sql

    for dsn in pg_schema():
        names = ("rt_" + uuid.uuid4().hex[:10], "pt_" + uuid.uuid4().hex[:10])
        with psycopg.connect(dsn, autocommit=True) as db:
            for n in names:
                db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(n)))
        try:
            yield dsn, *names
        finally:
            with psycopg.connect(dsn, autocommit=True) as db:
                for n in names:
                    db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(n)))
                    db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(n)))


def test_the_runtime_role_holds_exactly_the_merged_map(roles):
    import psycopg

    dsn, runtime, _ = roles
    mig.migrate(dsn, runtime_role=runtime)
    every = ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE")
    with psycopg.connect(dsn, autocommit=True) as db:
        for name, grant in mig.GRANTS.items():
            if grant.kind == "sequence":
                assert _seq_can(db, runtime, name, "USAGE"), name
                assert not _seq_can(db, runtime, name, "UPDATE"), name
                continue
            held = {p for p in every if _can(db, runtime, name, p)}
            assert held == set(grant.runtime.split(", ")), name


def test_the_runtime_role_cannot_update_or_delete_the_audit_log(roles):
    import psycopg

    dsn, runtime, _ = roles
    mig.migrate(dsn, runtime_role=runtime)
    from psycopg.conninfo import make_conninfo

    with psycopg.connect(make_conninfo(dsn, user=runtime), autocommit=True) as db:
        assert db.execute("SELECT current_user").fetchone()[0] == runtime
        for statement in (
            "UPDATE audit_entries SET body = '{}'",
            "DELETE FROM audit_entries",
            "UPDATE audit_checkpoints SET hash = 'x'",
            "TRUNCATE audit_entries",
        ):
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                db.execute(statement)


def test_the_portal_role_reads_only_the_portal_relations(roles):
    import psycopg

    dsn, runtime, portal = roles
    mig.migrate(dsn, runtime_role=runtime, portal_role=portal)
    with psycopg.connect(dsn, autocommit=True) as db:
        for name, grant in mig.GRANTS.items():
            if grant.kind == "sequence":
                assert not _seq_can(db, portal, name, "USAGE"), name
                continue
            held = {
                p
                for p in ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE")
                if _can(db, portal, name, p)
            }
            assert held == ({"SELECT"} if grant.portal else set()), name
    from psycopg.conninfo import make_conninfo

    with psycopg.connect(make_conninfo(dsn, user=portal), autocommit=True) as db:
        db.execute("SELECT count(*) FROM runs")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            db.execute("SELECT count(*) FROM kill_switch")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            db.execute("DELETE FROM runs")


def test_running_migrate_again_resets_a_portal_role_to_the_map(roles):
    import psycopg
    from psycopg import sql

    dsn, _, portal = roles
    mig.migrate(dsn, portal_role=portal)
    with psycopg.connect(dsn, autocommit=True) as db:
        db.execute(
            sql.SQL("GRANT UPDATE ON runs, kill_switch TO {}").format(sql.Identifier(portal))
        )
        assert _can(db, portal, "kill_switch", "UPDATE")
    assert mig.migrate(dsn, portal_role=portal) == []
    with psycopg.connect(dsn, autocommit=True) as db:
        assert not _can(db, portal, "runs", "UPDATE")
        assert not _can(db, portal, "kill_switch", "UPDATE")


def test_the_store_contract_suite_runs_as_a_non_owner_role():
    import psycopg

    for dsn in pg_schema(runtime=True):
        with psycopg.connect(dsn, autocommit=True) as db:
            user = db.execute("SELECT current_user").fetchone()[0]
            owner = db.execute(
                "SELECT tableowner FROM pg_tables WHERE tablename = 'runs' AND schemaname = current_schema()"
            ).fetchone()[0]
        assert user.startswith("rt_") and user != owner
