"""M6: `migrate` records a checksum per applied file and refuses a changed released file; an unreleased file
(UNRELEASED_MIGRATIONS) may change with a loud warning. Also: a released migration (older than 0008) never changes.
Real PostgreSQL in a throwaway schema; needs HADAVIN_TEST_PG_DSN."""

from __future__ import annotations

import logging
import os
import shutil
import uuid

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store import migrate as mig

NEEDS_PG = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)
UNRELEASED = sorted(mig.UNRELEASED_MIGRATIONS)


def test_the_unreleased_set_is_exactly_0008_to_0011_and_all_of_them_exist():
    assert [s[:4] for s in UNRELEASED] == ["0008", "0009", "0010", "0011"]
    assert {p.stem for p in mig._migration_files()} >= mig.UNRELEASED_MIGRATIONS


@pytest.fixture(name="env")
def schema_env():
    dsn = os.environ["HADAVIN_TEST_PG_DSN"]
    schema = f"ck_{uuid.uuid4().hex[:10]}"
    with psycopg.connect(dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    scoped = make_conninfo(dsn, options=f"-c search_path={schema}")
    try:
        yield scoped
    finally:
        with psycopg.connect(dsn, autocommit=True) as db:
            db.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def _ledger(scoped):
    with psycopg.connect(scoped, autocommit=True) as db:
        return dict(db.execute("SELECT version, checksum FROM schema_migrations").fetchall())


def _set(scoped, version, checksum):
    with psycopg.connect(scoped, autocommit=True) as db:
        db.execute(
            "UPDATE schema_migrations SET checksum = %s WHERE version = %s", (checksum, version)
        )


@NEEDS_PG
def test_a_fresh_database_records_the_checksum_of_every_file(env):
    mig.migrate(env, no_roles=True)
    ledger = _ledger(env)
    files = mig._migration_files()
    assert set(ledger) == {p.stem for p in files}
    assert all(ledger[p.stem] == mig._checksum(p) and len(ledger[p.stem]) == 64 for p in files)
    assert (
        mig.migrate(env, no_roles=True) == []
    )  # a second run with nothing changed applies nothing


@NEEDS_PG
def test_a_tampered_released_file_is_refused_and_named(env, tmp_path, monkeypatch):
    mig.migrate(env, no_roles=True)
    folder = tmp_path / "m"
    shutil.copytree(mig.MIGRATIONS, folder)
    target = folder / "0003_approvals_tick.sql"
    target.write_bytes(target.read_bytes() + b"\n-- tampered\n")
    monkeypatch.setattr(mig, "_migration_files", lambda: sorted(folder.glob("*.sql")))
    with pytest.raises(ConfigError, match=r"0003_approvals_tick\.sql was changed"):
        mig.migrate(env, no_roles=True)
    assert _ledger(env)["0003_approvals_tick"] != mig._checksum(target)  # nothing was re-recorded


@NEEDS_PG
def test_a_changed_recorded_checksum_of_a_released_file_is_refused(env):
    mig.migrate(env, no_roles=True)
    _set(env, "0001_core", "0" * 64)
    with pytest.raises(ConfigError, match=r"0001_core\.sql"):
        mig.migrate(env, no_roles=True)


@NEEDS_PG
def test_a_crlf_copy_of_a_released_file_is_not_a_change(env, tmp_path, monkeypatch):
    mig.migrate(env, no_roles=True)
    folder = tmp_path / "m"
    shutil.copytree(mig.MIGRATIONS, folder)
    t = folder / "0002_audit_chain.sql"
    t.write_bytes(t.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    monkeypatch.setattr(mig, "_migration_files", lambda: sorted(folder.glob("*.sql")))
    assert mig.migrate(env, no_roles=True) == []


@NEEDS_PG
@pytest.mark.parametrize("version", UNRELEASED)
def test_a_changed_unreleased_file_is_allowed_with_a_warning_and_recorded(env, caplog, version):
    mig.migrate(env, no_roles=True)
    _set(env, version, "f" * 64)  # the DB holds an earlier draft
    with caplog.at_level(logging.WARNING, logger="hadavin_sdk.migrate"):
        assert mig.migrate(env, no_roles=True) == []
    warned = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
    assert any(f"{version}.sql changed" in m and "NOT re-run" in m for m in warned), warned
    path = next(p for p in mig._migration_files() if p.stem == version)
    assert _ledger(env)[version] == mig._checksum(path)
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="hadavin_sdk.migrate"):
        mig.migrate(env, no_roles=True)
    assert not [
        r for r in caplog.records if "changed since" in r.getMessage()
    ]  # quiet once recorded


@NEEDS_PG
def test_a_ledger_without_the_checksum_column_gets_it_and_is_filled(env):
    mig.migrate(env, no_roles=True)
    with psycopg.connect(env, autocommit=True) as db:
        db.execute("ALTER TABLE schema_migrations DROP COLUMN checksum")
    assert mig.migrate(env, no_roles=True) == []
    ledger = _ledger(env)
    assert all(v is not None for v in ledger.values())
