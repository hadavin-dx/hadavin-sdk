"""Round 6 review of the stop-year validation step (review-ts-watermark-6): the lock limit of `migrate` runs from its
advisory lock to just before its commit (ledger steps, files, grants, checks) and is the LOCK limit only, observed on
the real path through `migrate()`; a lock wait anywhere in that span is exit 75 with nothing applied; a connection
lost outside the validation step is exit 3; the runbook says exactly that. Source-level mutants of the REAL
migrate.py for the whole span. Needs HADAVIN_TEST_PG_DSN."""

from __future__ import annotations

import os
import time

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo

from hadavin_sdk import cli
from hadavin_sdk.store import migrate as migrate_mod
from tests import test_step_b_e7_migration_0009 as e7
from tests import test_step_b_e7_round4 as r4
from tests import test_step_b_e7_round5 as r5
from tests.test_step_b_e7_migration_0009 import drop_world, make_world

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)


def _role_kwargs(up) -> dict:
    return {
        "runtime_role": up.runtime,
        "portal_role": up.portal,
        "purge_role": up.purge,
        "reset_role": up.reset,
    }


def _role_flags(up) -> list[str]:
    return [
        "--runtime-role",
        up.runtime,
        "--portal-role",
        up.portal,
        "--purge-role",
        up.purge,
        "--reset-role",
        up.reset,
    ]


# --- M1: what the limits really are while the real migrate() runs its files and its grants -------------------------


class Probe:
    """The real connection of `migrate`; reads the two limits on it right before each migration file and each first
    statement of a grant step, and keeps every statement in order."""

    def __init__(self, db, file_texts, seen):
        self._db, self._files, self._seen = db, file_texts, seen

    def __enter__(self):
        self._db.__enter__()
        return self

    def __exit__(self, *exc):
        return self._db.__exit__(*exc)

    def __getattr__(self, name):
        return getattr(self._db, name)

    def execute(self, query, *args, **kwargs):
        text = query if isinstance(query, str) else query.as_string(self._db)
        if text in self._files:
            self._seen["file"].append(tuple(self._db.execute(r5.SHOW).fetchone()))
        elif text.startswith("GRANT USAGE ON SCHEMA"):
            self._seen["grant"].append(tuple(self._db.execute(r5.SHOW).fetchone()))
        self._seen["calls"].append((text, args[0] if args else None))
        return self._db.execute(query, *args, **kwargs)


def limits_inside_migrate_scenario(monkeypatch):
    """A fresh schema, a session statement_timeout of 77s (neither the default nor our 60s), the real `migrate()`:
    every file and every grant step runs with lock_timeout 5s and the statement limit UNCHANGED, and the very last
    statement of the transaction puts the session's own values back."""
    up = make_world()
    try:
        files = {migrate_mod._read_migration(p)[0] for p in migrate_mod._migration_files()}
        seen: dict = {"file": [], "grant": [], "calls": []}
        real = migrate_mod.connect
        dsn = make_conninfo(up.dsn, options=f"-c search_path={up.schema} -c statement_timeout=77s")
        with monkeypatch.context() as m:
            m.setattr(migrate_mod, "connect", lambda *a, **k: Probe(real(*a, **k), files, seen))
            applied = migrate_mod.migrate(dsn, **_role_kwargs(up))
        assert len(seen["file"]) == len(applied) == len(files) > 0
        assert set(seen["file"]) == {("5s", "77s")}, seen["file"]
        assert len(seen["grant"]) == 4  # runtime, purge, reset, portal
        assert set(seen["grant"]) == {("5s", "77s")}, seen["grant"]
        last_text, last_params = seen["calls"][-1]
        assert "set_config('lock_timeout'" in last_text
        assert list(last_params) == ["0", "77s"]
    finally:
        drop_world(up)


def test_the_files_and_the_grants_of_a_real_migrate_run_under_the_lock_limit_only(monkeypatch):
    limits_inside_migrate_scenario(monkeypatch)


# --- m3: a lock wait after the files (grant phase) and before them (ledger) is exit 75, nothing applied -------------


def busy_grant_scenario(monkeypatch, cfg_dir=None):
    """Another session holds an uncommitted GRANT on our schema (a locked catalog row). An upgrade from 0008 applies
    its files, reaches the first grant step, waits for that row, and must give up with StopTablesBusy (exit 75 on the
    CLI) within the lock limit; the files it had applied are rolled back with it."""
    up = make_world()
    try:
        r5._at_0008(up, monkeypatch)
        r5.own_advisory_key(monkeypatch)
        before = up.run("SELECT version FROM schema_migrations ORDER BY 1")
        entered = []
        real = migrate_mod._apply_grants

        def spy(db, *args, **kwargs):
            entered.append(db.execute("SELECT count(*) FROM schema_migrations").fetchone()[0])
            return real(db, *args, **kwargs)

        with up.admin() as blocker, monkeypatch.context() as m:
            m.setattr(migrate_mod, "_apply_grants", spy)
            blocker.execute(
                "SET idle_in_transaction_session_timeout = '25s'"
            )  # cannot hang the suite
            blocker.execute("BEGIN")
            blocker.execute(
                sql.SQL("GRANT CREATE ON SCHEMA {} TO {}").format(
                    sql.Identifier(up.schema), sql.Identifier(up.portal)
                )
            )
            started = time.monotonic()
            with pytest.raises(migrate_mod.StopTablesBusy, match="LockNotAvailable"):
                up.migrate()
            assert time.monotonic() - started < 20
            # the wait was in the grant phase, with every file applied inside the transaction
            assert entered == [len(migrate_mod._migration_files())]
            if cfg_dir is not None:
                r4._cli_cfg(cfg_dir)
                monkeypatch.setenv("HADAVIN_MIGRATE_DSN", up.scoped)
                assert cli.main(["--config", str(cfg_dir), "migrate", *_role_flags(up)]) == 75
                assert len(entered) == 2
            blocker.execute("ROLLBACK")
        assert up.run("SELECT version FROM schema_migrations ORDER BY 1") == before  # rolled back
        up.migrate()  # with the other session gone, the same upgrade goes through
        assert ("0009_stop_state_hardening",) in up.run("SELECT version FROM schema_migrations")
    finally:
        drop_world(up)


def test_a_lock_wait_in_the_grant_phase_gives_up_with_exit_75_and_rolls_the_files_back(
    monkeypatch, cfg_dir
):
    busy_grant_scenario(monkeypatch, cfg_dir)


def busy_ledger_scenario(monkeypatch):
    """Another session holds ACCESS EXCLUSIVE on the ledger: `migrate` gives up within the limit in its ledger steps
    (it holds no stop-table lock there, but waiting gains nothing)."""
    up = make_world()
    try:
        up.migrate()
        r5.own_advisory_key(monkeypatch)
        with up.admin() as blocker:
            blocker.execute("SET idle_in_transaction_session_timeout = '25s'")
            blocker.execute("BEGIN")
            blocker.execute("LOCK TABLE schema_migrations IN ACCESS EXCLUSIVE MODE")
            started = time.monotonic()
            with pytest.raises(migrate_mod.StopTablesBusy, match="LockNotAvailable"):
                up.migrate()
            assert time.monotonic() - started < 20
            blocker.execute("ROLLBACK")
        assert up.migrate() == []
    finally:
        drop_world(up)


def test_a_lock_wait_in_the_ledger_steps_gives_up_with_a_retry_condition(monkeypatch):
    busy_ledger_scenario(monkeypatch)


# --- m2: a connection lost outside the validation step is exit 3 (here: in the grant phase) -------------------------


def test_a_connection_lost_in_the_grant_phase_exits_3_and_applies_nothing(
    monkeypatch, cfg_dir, capsys
):
    up = make_world()
    try:
        r5._at_0008(up, monkeypatch)
        before = up.run("SELECT version FROM schema_migrations ORDER BY 1")
        real = migrate_mod._apply_grants

        def lose(db, *args, **kwargs):
            with psycopg.connect(up.dsn, autocommit=True) as other:
                other.execute("SELECT pg_terminate_backend(%s)", (db.info.backend_pid,))
            return real(db, *args, **kwargs)

        r4._cli_cfg(cfg_dir)
        monkeypatch.setenv("HADAVIN_MIGRATE_DSN", up.scoped)
        with monkeypatch.context() as m:
            m.setattr(migrate_mod, "_apply_grants", lose)
            assert cli.main(["--config", str(cfg_dir), "migrate", *_role_flags(up)]) == 3
        assert "retry later" not in capsys.readouterr().err
        assert up.run("SELECT version FROM schema_migrations ORDER BY 1") == before
    finally:
        drop_world(up)


# --- m2, n1, n2: the runbook says what the code does ----------------------------------------------------------------


def test_the_runbook_states_the_span_of_the_lock_limit_and_the_real_exit_3_cases():
    text = " ".join(r5.RUNBOOK.read_text(encoding="utf-8").split())
    for sentence in (
        # item 2 and n2: where the lock limit applies, and to which locks
        (
            "from the moment it holds its advisory lock until just before it commits: the ledger steps, the "
            "migration files, and the grant, revoke, ALTER FUNCTION and check steps after them"
        ),
        "It covers every lock wait of every statement there, on any table or catalog row",
        "the statement limit does not apply outside the validation step",
        "Before the advisory lock there is NO limit, on purpose",
        # exit 75
        (
            "a lock wait over 5 seconds (in the ledger steps, a migration file, the validation step, or the grant "
            "and check steps), a scan over 60 seconds in the validation step"
        ),
        # m2: exit 3, in the real order
        (
            "lost outside the validation step (opening the connection, the file loop, the grants and checks, the "
            "commit; for `--validate-constraints` the commit too)"
        ),
        # n1: the limits are constants on purpose
        (
            "Both limits are constants in the code on purpose (safety limits of an operator tool): there is no "
            "config key and no flag for them"
        ),
    ):
        assert sentence in text, sentence
    for gone in (
        "BEFORE the validation step",
        "have no limit",
        "only for the file loop",
        "(the ACCESS EXCLUSIVE locks of ADD CONSTRAINT and the index build), but only",
    ):
        assert gone not in text, gone


# --- mutants of the real source, for the whole span ----------------------------------------------------------------

AFTER_FILES = "        q = \"SELECT pg_has_role(%s, %s, 'MEMBER')\""
LEDGER = "        _ensure_ledger(db)\n"
NO_LIMIT = "db.execute(\"SELECT set_config('lock_timeout', '0', true)\")\n"

SPAN_MUTANTS = [
    (
        "file loop and grants also get the 60s statement limit (lock_only dropped at the call site)",
        r5.FILE_LOOP,
        "with _stop_timeouts(db):",
        [limits_inside_migrate_scenario],
    ),
    (
        "no limit anywhere",
        r5.FILE_LOOP,
        "with contextlib.nullcontext():",
        [limits_inside_migrate_scenario, busy_grant_scenario, busy_ledger_scenario],
    ),
    (
        "a lock timeout is not mapped to the retry condition",
        r5.LOCK_MAP,
        "except KeyError as exc:",
        [busy_grant_scenario, busy_ledger_scenario],
    ),
    (
        "the limit ends after the file loop (the round 5 behaviour)",
        AFTER_FILES,
        "        " + NO_LIMIT + AFTER_FILES,
        [limits_inside_migrate_scenario, busy_grant_scenario],
    ),
    (
        "the ledger steps wait without a limit",
        LEDGER,
        "        " + NO_LIMIT + LEDGER,
        [busy_ledger_scenario],
    ),
]


@pytest.mark.parametrize(
    ("name", "old", "new", "checks"), SPAN_MUTANTS, ids=[m[0] for m in SPAN_MUTANTS]
)
def test_mutants_of_the_lock_limit_span_are_killed(monkeypatch, name, old, new, checks):
    """Each scenario also runs unmutated as a test of its own above (and must pass there)."""
    assert old != new, name
    for check in checks:
        with r5.mutated(old, new), monkeypatch.context() as m:
            m.setattr(e7, "migrate", migrate_mod.migrate)  # the world calls the mutant
            r5._killed(check, m)
