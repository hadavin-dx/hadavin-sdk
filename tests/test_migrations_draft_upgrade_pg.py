"""Upgrade path of a database that ran an older DRAFT of 0010/0011 (hostile re-read 2, M1). Real PostgreSQL, a
throwaway schema and logins (the World of test_stop_state_roles). The draft DB is built the way the real drafts
left one: a migrated world, the recorded checksum of 0011 replaced, and the old 7-argument hadavin_reserve_spend
(caps passed by the caller) added as the owner and granted to the runtime.

* named roles: a changed 0010/0011 is a ConfigError naming the file and the remedy; --no-roles keeps the warning;
* an unmapped overload refuses migrate with each function named by its argument types and the DROP statement;
* --reset-draft drops what the draft made (the operator's step, here the recipe), the unmapped overloads of the
  schema (only the migration owner's, only hadavin_*), re-applies, and the runtime can no longer book with caps of
  its own choosing;
* --accept-changed-draft on a DB whose objects do NOT match is the operator's call: it records the checksum and
  nothing else (documented, asserted)."""

# ruff: noqa: S608  (test SQL built from constants and a throwaway schema name)
from __future__ import annotations

import logging
import os

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg
from psycopg import errors

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store import migrate as mig
from tests.test_stop_state_roles import stop_world  # noqa: F401 - the fixture

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)
V11, V10 = "0011_money_definer", "0010_money_guard"
OLD7 = "hadavin_reserve_spend(text, text, date, numeric, numeric, numeric, text)"
OLD7_TYPES = "text, text, date, numeric, numeric, numeric, text"


def _draft(w, version=V11, with_old_overload=True):
    """A database that holds an older draft: a different recorded checksum and the old 7-argument overload."""
    w.do(f"UPDATE schema_migrations SET checksum = '{'f' * 64}' WHERE version = '{version}'")
    if with_old_overload:
        w.do(
            f"""CREATE FUNCTION {OLD7} RETURNS boolean LANGUAGE sql SECURITY DEFINER AS
            $$ SELECT true $$"""
        )
        w.grant(
            f"GRANT EXECUTE ON FUNCTION {w.schema}.{OLD7} TO {{}}", w.runtime
        )  # as the old migrate did


def _recipe(w):
    """What docs/migration-checksums.md tells the operator to drop before --reset-draft 0011."""
    w.do(
        "DROP TABLE hadavin_caps, hadavin_limits; "
        "ALTER TABLE spend DROP CONSTRAINT spend_usd_range; "
        "ALTER TABLE spend_month DROP CONSTRAINT spend_month_usd_range"
    )


def _runtime_can_run_old(w):
    return w.run(
        "SELECT has_function_privilege(%s, to_regprocedure(%s), 'EXECUTE')",
        (w.runtime, f"{w.schema}.{OLD7}"),
    )[0][0]


def _old_exists(w):
    return w.run("SELECT to_regprocedure(%s) IS NOT NULL", (f"{w.schema}.{OLD7}",))[0][0]


def test_named_roles_refuse_a_changed_money_draft_with_the_remedy(w):
    _draft(w, with_old_overload=False)
    with pytest.raises(ConfigError) as caught:
        w.migrate()
    msg = str(caught.value)
    assert f"{V11}.sql" in msg and "older draft of an unreleased migration" in msg
    assert f"--reset-draft {V11}" in msg and f"--accept-changed-draft {V11}" in msg
    assert "drop what the draft made" in msg


def test_each_single_role_is_enough_to_make_it_the_production_path(w):
    _draft(w, V10, with_old_overload=False)
    for role in ("runtime_role", "purge_role", "release_role", "reset_role", "caps_role"):
        name = w.new_role("x" + role[:3])
        with pytest.raises(ConfigError, match=f"{V10}.sql"):
            mig.migrate(w.scoped, **{role: name})


def test_no_roles_keeps_the_warning(w, caplog):
    _draft(w, with_old_overload=False)
    with caplog.at_level(logging.WARNING, logger="hadavin_sdk.migrate"):
        assert mig.migrate(w.scoped, no_roles=True) == []
    assert any(f"{V11}.sql differs" in r.getMessage() for r in caplog.records)


@pytest.mark.parametrize("version", ["0008_release_expired_spend", "0009_stop_state_hardening"])
def test_0008_and_0009_keep_the_warning_with_roles(w, caplog, version):
    _draft(w, version, with_old_overload=False)
    with caplog.at_level(logging.WARNING, logger="hadavin_sdk.migrate"):
        assert w.migrate() == []
    assert any(f"{version}.sql differs" in r.getMessage() for r in caplog.records)


def test_the_unmapped_old_overload_refuses_and_names_every_function_with_its_types(w):
    # the checksum matches here (the unmapped refusal is independent of it): only the stray overloads are wrong
    _draft(w, with_old_overload=True)
    w.do(
        f"UPDATE schema_migrations SET checksum = NULL WHERE version = '{V11}'"
    )  # trusted on first use
    w.do(
        "CREATE FUNCTION hadavin_stray(integer, text) RETURNS integer LANGUAGE sql AS $$ SELECT 1 $$"
    )
    with pytest.raises(ConfigError) as caught:
        w.migrate()
    msg = str(caught.value)
    assert f"{w.schema}.hadavin_reserve_spend({OLD7_TYPES})" in msg
    assert f"{w.schema}.hadavin_stray(integer, text)" in msg
    assert (
        "drop it (DROP FUNCTION <schema>.<name>(<types>)) or run migrate --reset-draft"
        in msg.replace("Drop it", "drop it")
    )
    assert f'DROP FUNCTION "{w.schema}"."hadavin_reserve_spend"({OLD7_TYPES})' in msg
    assert _old_exists(w)  # the refusal rolled back; nothing was dropped behind the operator's back


def test_reset_draft_drops_the_old_overload_and_the_runtime_cannot_book_with_its_own_caps(w):
    _draft(w)
    assert _runtime_can_run_old(w)
    _recipe(w)
    w.do(f"DELETE FROM schema_migrations WHERE version = '{V11}'")  # (reset-draft does this itself)
    w.do(f"INSERT INTO schema_migrations (version, checksum) VALUES ('{V11}', '{'f' * 64}')")
    assert w.migrate(reset_draft=V11) == [V11]
    assert not _old_exists(w)
    assert w.migrate() == []  # clean state
    # the exploit of the hostile re-read: reserve 500 with caps 1e12 against a table cap of 1
    w.do(
        "INSERT INTO hadavin_caps (agent_id, day_cap, month_cap, set_by) VALUES ('ag1', 1, 1, 'op')"
    )
    with w.as_(w.runtime) as db:
        with pytest.raises(errors.UndefinedFunction):
            db.execute(
                "SELECT * FROM hadavin_reserve_spend('x1', 'ag1', current_date, 500, 1e12, 1e12, 'r')"
            )
        with pytest.raises(psycopg.Error) as err:
            db.execute("SELECT * FROM hadavin_reserve_spend('x2', 'ag1', current_date, 500, 'r')")
        assert getattr(err.value.diag, "sqlstate", "") != ""
    assert w.run("SELECT count(*) FROM spend_reservations")[0][0] == 0


def test_reset_draft_drops_only_functions_the_migration_owner_owns(w):
    other = w.new_role("own")
    w.grant(f"GRANT USAGE, CREATE ON SCHEMA {w.schema} TO {{}}", other)
    _draft(w, with_old_overload=False)
    with psycopg.connect(w.dsn_of(other), autocommit=True) as db:
        db.execute(
            "CREATE FUNCTION hadavin_foreign(integer) RETURNS integer LANGUAGE sql AS $$ SELECT 1 $$"
        )
    with w.admin() as db:
        db.execute(
            "CREATE FUNCTION hadavin_mine(integer) RETURNS integer LANGUAGE sql AS $$ SELECT 1 $$"
        )
        db.execute(
            "CREATE FUNCTION not_ours(integer) RETURNS integer LANGUAGE sql AS $$ SELECT 1 $$"
        )
    with w.admin() as db, db.transaction():
        dropped = mig._drop_unmapped_functions(db)
    assert dropped == [f"{w.schema}.hadavin_mine(integer)"]
    left = {
        r[0]
        for r in w.run(
            "SELECT proname FROM pg_proc WHERE pronamespace = to_regnamespace(%s)", (w.schema,)
        )
    }
    assert {"hadavin_foreign", "not_ours"} <= left and "hadavin_mine" not in left
    assert "hadavin_reserve_spend" in left  # a mapped function is never touched


def test_accept_changed_draft_on_objects_that_do_not_match_is_the_operators_call(w):
    # the old overload and the older bodies stay: accept only records the checksum (documented), and the
    # unmapped-function refusal is what still stops migrate when an old overload is there
    _draft(w)
    with pytest.raises(ConfigError, match="in neither FUNCTION_GRANTS"):
        w.migrate(accept_changed_draft=(V11,))
    assert _old_exists(w) and _runtime_can_run_old(w)
    w.do(f"DROP FUNCTION {OLD7}")  # the operator drops it, then accepts
    assert (
        w.migrate(accept_changed_draft=(V11,)) == []
    )  # no overload, accepted: the operator vouches
    ledger = dict(w.run("SELECT version, checksum FROM schema_migrations"))
    assert ledger[V11] == mig._read_migration(mig.MIGRATIONS / f"{V11}.sql")[1]


# --- mutants: each refusal must be what stops it -------------------------------------------------------------


def test_mutant_strict_off_lets_a_changed_draft_through_with_roles(w, monkeypatch):
    _draft(w, with_old_overload=False)
    real = mig._verify_applied
    monkeypatch.setattr(mig, "_verify_applied", lambda *a, **k: real(*a, **{**k, "strict": False}))
    assert w.migrate() == []  # the mutant: no refusal, so the test above is the one that kills it


def test_mutant_money_wall_set_empty_does_not_refuse(w, monkeypatch):
    _draft(w, with_old_overload=False)
    monkeypatch.setattr(mig, "MONEY_WALL_DRAFTS", frozenset())
    assert w.migrate() == []


def test_mutant_no_drop_on_reset_leaves_the_overload_and_migrate_still_refuses(w, monkeypatch):
    _draft(w)
    _recipe(w)
    w.do(f"DELETE FROM schema_migrations WHERE version = '{V11}'")
    w.do(f"INSERT INTO schema_migrations (version, checksum) VALUES ('{V11}', '{'f' * 64}')")
    monkeypatch.setattr(mig, "_drop_unmapped_functions", lambda db: [])
    with pytest.raises(ConfigError, match="in neither FUNCTION_GRANTS"):
        w.migrate(reset_draft=V11)
    assert _old_exists(w)


def test_the_message_builder_is_what_carries_the_remedy(w):
    _draft(w)
    with w.admin() as db:
        text = mig._unmapped_message(db)
    assert "run migrate --reset-draft <version>" in text and OLD7_TYPES in text
