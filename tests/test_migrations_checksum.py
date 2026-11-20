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


def test_the_unreleased_set_is_exactly_0008_to_0012_and_all_of_them_exist():
    assert [s[:4] for s in UNRELEASED] == ["0008", "0009", "0010", "0011", "0012"]
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
    assert all(
        ledger[p.stem] == mig._read_migration(p)[1] and len(ledger[p.stem]) == 64 for p in files
    )
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
    with pytest.raises(ConfigError, match=r"0003_approvals_tick\.sql was changed after"):
        mig.migrate(env, no_roles=True)
    assert (
        _ledger(env)["0003_approvals_tick"] != mig._read_migration(target)[1]
    )  # nothing was re-recorded


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


def _warnings(caplog):
    return [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]


@NEEDS_PG
@pytest.mark.parametrize("version", UNRELEASED)
def test_a_changed_unreleased_file_warns_on_every_run_and_keeps_the_applied_checksum(
    env, caplog, version
):
    mig.migrate(env, no_roles=True)
    _set(env, version, "f" * 64)  # the DB holds an earlier draft
    for _ in range(2):
        caplog.clear()
        with caplog.at_level(logging.WARNING, logger="hadavin_sdk.migrate"):
            assert mig.migrate(env, no_roles=True) == []
        msgs = [m for m in _warnings(caplog) if f"{version}.sql differs" in m]
        assert msgs and "NOTHING of the changed file reaches" in msgs[0], _warnings(caplog)
        assert f"--reset-draft {version}" in msgs[0] and "re-applied" not in msgs[0]
        assert _ledger(env)[version] == "f" * 64  # not overwritten


@NEEDS_PG
def test_accept_changed_draft_records_the_file_checksum_and_ends_the_warning(env, caplog):
    mig.migrate(env, no_roles=True)
    v = "0011_money_definer"
    _set(env, v, "f" * 64)
    mig.migrate(env, no_roles=True, accept_changed_draft=(v,))
    path = next(p for p in mig._migration_files() if p.stem == v)
    assert _ledger(env)[v] == mig._read_migration(path)[1]
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="hadavin_sdk.migrate"):
        mig.migrate(env, no_roles=True)
    assert not [m for m in _warnings(caplog) if "differs from what" in m]


@NEEDS_PG
def test_accept_and_reset_refuse_a_released_version(env):
    mig.migrate(env, no_roles=True)
    with pytest.raises(ConfigError, match="only an unreleased"):
        mig.migrate(env, no_roles=True, accept_changed_draft=("0003_approvals_tick",))
    with pytest.raises(ConfigError, match="only an unreleased"):
        mig.migrate(env, no_roles=True, reset_draft="0007_spend_reservations")
    assert len(_ledger(env)) == len(mig._migration_files())  # nothing deleted


@NEEDS_PG
def test_reset_draft_deletes_that_row_and_every_later_one_only(env):
    mig.migrate(env, no_roles=True)
    with psycopg.connect(env, autocommit=True) as db:
        mig._reset_draft(db, "0010_money_guard", mig._migration_files())
    assert "0010_money_guard" not in _ledger(env) and "0011_money_definer" not in _ledger(env)
    assert "0009_stop_state_hardening" in _ledger(env) and "0007_spend_reservations" in _ledger(env)


@NEEDS_PG
def test_a_refused_run_with_reset_draft_leaves_the_ledger_alone(env):
    mig.migrate(env, no_roles=True)
    # the draft's objects still exist, so applying 0011 again fails; the transaction rolls back the delete
    with pytest.raises(psycopg.Error):
        mig.migrate(env, no_roles=True, reset_draft="0011_money_definer")
    assert "0011_money_definer" in _ledger(env)


@NEEDS_PG
def test_a_null_checksum_on_a_released_file_that_differs_from_the_package_is_refused(
    env, tmp_path, monkeypatch
):
    mig.migrate(env, no_roles=True)
    _set(env, "0003_approvals_tick", None)
    folder = tmp_path / "m"
    shutil.copytree(mig.MIGRATIONS, folder)
    t = folder / "0003_approvals_tick.sql"
    t.write_bytes(t.read_bytes() + b"\n-- edited\n")
    monkeypatch.setattr(mig, "_migration_files", lambda: sorted(folder.glob("*.sql")))
    with pytest.raises(
        ConfigError, match=r"0003_approvals_tick\.sql was changed after its release"
    ):
        mig.migrate(env, no_roles=True)


@NEEDS_PG
def test_a_fresh_install_of_an_edited_released_file_is_refused(env, tmp_path, monkeypatch):
    folder = tmp_path / "m"
    shutil.copytree(mig.MIGRATIONS, folder)
    t = folder / "0001_core.sql"
    t.write_bytes(t.read_bytes() + b"\n-- edited\n")
    monkeypatch.setattr(mig, "_migration_files", lambda: sorted(folder.glob("*.sql")))
    with pytest.raises(ConfigError, match=r"0001_core\.sql was changed after its release"):
        mig.migrate(env, no_roles=True)


@NEEDS_PG
def test_a_null_checksum_on_an_unreleased_file_is_trusted_once_with_a_warning(env, caplog):
    mig.migrate(env, no_roles=True)
    _set(env, "0010_money_guard", None)
    with caplog.at_level(logging.WARNING, logger="hadavin_sdk.migrate"):
        mig.migrate(env, no_roles=True)
    assert any("0010_money_guard.sql was applied before" in m for m in _warnings(caplog))
    assert _ledger(env)["0010_money_guard"] is not None


@NEEDS_PG
def test_the_column_is_not_altered_when_it_exists(env):
    """A migrate login that is not the ledger owner may not ALTER it, so with the column present migrate must not try."""
    mig.migrate(env, no_roles=True)
    seen = []

    class Spy:
        def __init__(self, db):
            self.db = db

        def execute(self, q, *a):
            seen.append(q)
            return self.db.execute(q, *a)

    with psycopg.connect(env, autocommit=True) as db:
        mig._ensure_ledger(Spy(db))
    assert seen and not any("ALTER TABLE" in q for q in seen), seen


def test_the_packaged_released_hashes_equal_the_test_fixture():
    import json
    from pathlib import Path

    fixture = Path(__file__).parent / "fixtures" / "migrations_released.json"
    assert json.loads(fixture.read_text()) == mig._released_hashes()


@NEEDS_PG
def test_a_ledger_without_the_checksum_column_gets_it_and_is_filled(env):
    mig.migrate(env, no_roles=True)
    with psycopg.connect(env, autocommit=True) as db:
        db.execute("ALTER TABLE schema_migrations DROP COLUMN checksum")
    assert mig.migrate(env, no_roles=True) == []
    ledger = _ledger(env)
    assert all(v is not None for v in ledger.values())
