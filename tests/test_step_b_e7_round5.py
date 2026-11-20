"""Round 5 review of the stop-year validation step (review-ts-watermark-5): schema-qualified privilege checks and
limit seeding (a TEMP table must not shadow ours), a lock limit for the migration files that does not end the wait
for another migrate, the whole validation step mapped to exit 75 on a lost connection, source-level mutants of the
REAL `_stop_timeouts`, a clear error for a NULL `current_schema()`, and the exit-code wording. Needs
HADAVIN_TEST_PG_DSN."""

from __future__ import annotations

import contextlib
import inspect
import os
import threading
import time
import uuid
from pathlib import Path

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo

from hadavin_sdk import cli
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store import migrate as migrate_mod
from tests import test_step_b_e7_migration_0009 as e7
from tests import test_step_b_e7_round4 as r4
from tests.test_step_b_e7_migration_0009 import drop_world, make_not_valid, make_world

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)

RUNBOOK = Path(__file__).resolve().parents[1] / "docs" / "stop-state-runbook.md"
SHOW = "SELECT current_setting('lock_timeout'), current_setting('statement_timeout')"


@pytest.fixture(name="w")
def world():
    w = make_world()
    try:
        w.migrate()
        yield w
    finally:
        drop_world(w)


# --- A: bare names (a TEMP table shadows ours: pg_temp comes first for relations) --------------------------------


def test_the_portal_privilege_check_reads_our_table_not_a_temp_table_of_the_same_name(w):
    with psycopg.connect(w.scoped) as db:
        real = migrate_mod._in_schema(db, "spend")
        db.execute(sql.SQL("GRANT INSERT ON {} TO {}").format(real, sql.Identifier(w.portal)))
        db.execute(
            "CREATE TEMP TABLE spend (x int)"
        )  # no grant on it: a bare name would read this one
        assert "spend:INSERT" in migrate_mod._excess_privileges(db, w.portal)
        db.execute(sql.SQL("REVOKE INSERT ON {} FROM {}").format(real, sql.Identifier(w.portal)))
        db.execute(sql.SQL("GRANT INSERT ON pg_temp.spend TO {}").format(sql.Identifier(w.portal)))
        assert migrate_mod._excess_privileges(db, w.portal) == []  # the temp grant is not ours


def test_the_limits_seed_writes_our_table_not_a_temp_table_of_the_same_name(w):
    with psycopg.connect(w.scoped) as db:
        real = migrate_mod._in_schema(db, "hadavin_limits")
        db.execute(sql.SQL("INSERT INTO {} (name, value) VALUES ('planted', 1)").format(real))
        db.execute(sql.SQL("CREATE TEMP TABLE hadavin_limits (LIKE {} INCLUDING ALL)").format(real))
        migrate_mod._seed_limits(db)
        assert db.execute("SELECT count(*) FROM pg_temp.hadavin_limits").fetchone()[0] == 0
        names = {r[0] for r in db.execute(sql.SQL("SELECT name FROM {}").format(real)).fetchall()}
        assert names == set(migrate_mod.money_limits())  # seeded, and the planted row is gone


# --- B: a lock limit for the files, set after the advisory lock ----------------------------------------------------


def _lock_seconds() -> int:
    return int(migrate_mod.VALIDATE_LOCK_TIMEOUT.rstrip("s"))


def _at_0008(up, monkeypatch):
    """Apply the files up to 0008 only (the same trick as the upgrade test of e7)."""
    real, grants = migrate_mod._migration_files, dict(migrate_mod.GRANTS)
    with monkeypatch.context() as m:
        m.setattr(
            migrate_mod,
            "_migration_files",
            lambda *a, **k: [p for p in real(*a, **k) if p.name < "0009"],
        )
        m.setattr(
            migrate_mod,
            "GRANTS",
            {k: v for k, v in grants.items() if k not in e7.NEW_TABLES},
        )
        m.setattr(
            migrate_mod,
            "FUNCTION_GRANTS",
            {
                k: v
                for k, v in migrate_mod.FUNCTION_GRANTS.items()
                if k not in migrate_mod.MONEY_FUNCTIONS
            },
        )
        up.migrate()


def busy_file_scenario(monkeypatch, cfg_dir=None):
    """A long reader holds a lock on a stop table while an upgrade needs ACCESS EXCLUSIVE on it: `migrate` must give
    up with StopTablesBusy (exit 75 on the CLI) within the lock limit and apply nothing, not queue behind the reader."""
    up = make_world()
    try:
        _at_0008(up, monkeypatch)
        before = up.run("SELECT count(*) FROM schema_migrations")[0][0]
        with up.admin() as blocker:
            blocker.execute(
                "SET idle_in_transaction_session_timeout = '25s'"
            )  # cannot hang the suite
            blocker.execute("BEGIN")
            blocker.execute("SELECT count(*) FROM kill_switch_stops")  # ACCESS SHARE until the end
            started = time.monotonic()
            with pytest.raises(migrate_mod.StopTablesBusy, match="migration file"):
                up.migrate()
            assert time.monotonic() - started < 20
            if cfg_dir is not None:
                r4._cli_cfg(cfg_dir)
                monkeypatch.setenv("HADAVIN_MIGRATE_DSN", up.scoped)
                assert cli.main(["--config", str(cfg_dir), "migrate", "--no-roles"]) == 75
            blocker.execute("ROLLBACK")
        assert up.run("SELECT count(*) FROM schema_migrations")[0][0] == before  # nothing applied
        up.migrate()  # with the reader gone, the same upgrade goes through
        assert ("0009_stop_state_hardening",) in up.run("SELECT version FROM schema_migrations")
    finally:
        drop_world(up)


def test_an_upgrade_behind_a_long_reader_gives_up_with_exit_75_and_applies_nothing(
    monkeypatch, cfg_dir
):
    busy_file_scenario(monkeypatch, cfg_dir)


def advisory_wait_scenario(w):
    """A second `migrate` waits for the first on the advisory lock for LONGER than the lock limit and then runs."""
    holder = psycopg.connect(w.scoped, autocommit=True)
    out: dict = {}
    try:
        holder.execute("SET idle_in_transaction_session_timeout = '40s'")
        holder.execute("BEGIN")
        holder.execute("SELECT pg_advisory_xact_lock(%s)", (migrate_mod._LOCK,))

        def run():
            started = time.monotonic()
            try:
                out["applied"] = w.migrate()
            except BaseException as exc:  # noqa: BLE001 - handed to the test thread
                out["err"] = exc
            out["seconds"] = time.monotonic() - started

        thread = threading.Thread(target=run)
        thread.start()
        time.sleep(_lock_seconds() + 2)
        assert thread.is_alive(), out  # still waiting after the limit: the wait has no limit
        holder.execute("ROLLBACK")
        thread.join(60)
    finally:
        holder.close()
    assert "err" not in out, out
    assert out["applied"] == [] and out["seconds"] >= _lock_seconds()


def test_a_second_migrate_waits_on_the_advisory_lock_longer_than_the_lock_limit(w):
    advisory_wait_scenario(w)


def lock_only_scenario(w):
    with psycopg.connect(w.scoped) as db, db.transaction():
        before = db.execute(SHOW).fetchone()
        with migrate_mod._stop_timeouts(db, lock_only=True):
            lock, statement = db.execute(SHOW).fetchone()
            assert lock == "5s"
            assert statement == before[1]  # the files run under no statement limit
        assert db.execute(SHOW).fetchone() == before


def test_the_file_loop_limit_is_the_lock_wait_only(w):
    lock_only_scenario(w)


# --- C: a lost connection anywhere in the validation step is exit 75 -----------------------------------------------


class Flaky:
    """The real connection, but statement number `fail_at` raises a lost-connection error (0: none)."""

    def __init__(self, db, fail_at=0):
        self._db, self.fail_at, self.count = db, fail_at, 0

    def execute(self, *args, **kwargs):
        self.count += 1
        if self.count == self.fail_at:
            raise psycopg.OperationalError("injected: server closed the connection unexpectedly")
        return self._db.execute(*args, **kwargs)

    @property
    def info(self):
        return self._db.info


def lost_connection_scenario(w):
    for step in (migrate_mod.settle_stop_constraints, migrate_mod.validate_constraints):
        make_not_valid(w, tables=("kill_switch_stops",))
        with psycopg.connect(w.scoped) as db, db.transaction():
            counter = Flaky(db)
            step(counter)
        total = counter.count
        assert total >= 8, (step.__name__, total)  # setup, reads, VALIDATE, restore are all counted
        for k in range(1, total + 1):
            make_not_valid(w, tables=("kill_switch_stops",))
            with (
                psycopg.connect(w.scoped) as db,
                db.transaction(),
                pytest.raises(migrate_mod.StopTablesBusy, match="OperationalError"),
            ):
                step(Flaky(db, fail_at=k))


def test_a_lost_connection_at_every_statement_of_the_step_is_a_retry_condition(w):
    lost_connection_scenario(w)


def lost_connection_keeps_original_scenario(w):
    with psycopg.connect(w.scoped) as db:
        pid = db.info.backend_pid
        caught = []
        with pytest.raises(psycopg.OperationalError) as err, migrate_mod._stop_timeouts(db):
            with psycopg.connect(w.dsn, autocommit=True) as other:
                other.execute("SELECT pg_terminate_backend(%s)", (pid,))
            try:
                db.execute("SELECT 1")
            except psycopg.OperationalError as exc:
                caught.append(exc)
                raise
        assert (
            caught and err.value is caught[0]
        )  # not replaced by the failure of a restore on a dead connection


def test_a_dead_connection_keeps_its_original_error_through_the_timeout_context(w):
    lost_connection_keeps_original_scenario(w)


# --- D: source-level mutants of the REAL migrate.py ----------------------------------------------------------------

SOURCE_PATH = Path(migrate_mod.__file__)


@contextlib.contextmanager
def mutated(old: str, new: str):
    """Edit the real source text (`old` must occur exactly once) and run it again inside the module's own namespace
    (every name is rebound; the functions called through `migrate_mod.` are then the mutants); put everything back."""
    text = SOURCE_PATH.read_text(encoding="utf-8")
    assert text.count(old) == 1, old
    namespace = vars(migrate_mod)
    snapshot = dict(namespace)
    try:
        exec(compile(text.replace(old, new), str(SOURCE_PATH), "exec"), namespace)  # noqa: S102
        yield
    finally:
        namespace.clear()
        namespace.update(snapshot)


INTRANS = "if db.info.transaction_status == pq.TransactionStatus.INTRANS:"
LOCK_SET = 'VALIDATE_LOCK_TIMEOUT = "5s"'
STMT_SET = '"60s"  # the check scans'
SETTLE_MAP = (
    '        raise _busy(exc, "validate the stop-year constraints") from None\n    return planted'
)
VALIDATE_MAP = (
    '        raise _busy(exc, "validate the stop-year constraints") from None\n    return done'
)
FILE_LOOP = "with _stop_timeouts(db, lock_only=True):"
LOCK_MAP = "except errors.LockNotAvailable as exc:"
ADVISORY = '        db.execute("SELECT pg_advisory_xact_lock(%s)", (_LOCK,))\n'
EXCESS_TARGET = "target = _qualified("
SEED_INSERT = '.format(_in_schema(db, "hadavin_limits")),\n            (name, value),'


def _killed(fn, *args):
    with pytest.raises(BaseException) as err:  # noqa: PT011
        fn(*args)
    assert not isinstance(err.value, KeyboardInterrupt)
    print(
        f"  killed by {type(err.value).__name__}: {str(err.value)[:100]!r}"
    )  # seen with -s in the raw logs


TIMEOUT_MUTANTS = [
    (
        "restore only in a healthy transaction -> restore also on a dead connection",
        INTRANS,
        "if db.info.transaction_status != pq.TransactionStatus.INERROR:",
        [lost_connection_keeps_original_scenario],
    ),
    (
        "restore always",
        INTRANS,
        "if True:",
        [r4.test_the_timeouts_are_restored_when_the_step_raises_and_the_original_error_survives],
    ),
    (
        "restore never in a healthy transaction",
        INTRANS,
        "if db.info.transaction_status != pq.TransactionStatus.INTRANS:",
        [
            r4.test_the_timeouts_are_restored_when_the_step_raises_and_the_original_error_survives,
            e7.test_the_settle_step_puts_the_transaction_timeouts_back,
        ],
    ),
    (
        "restore never",
        INTRANS,
        "if False:",
        [e7.test_the_settle_step_puts_the_transaction_timeouts_back],
    ),
    (
        "lock constant changed",
        LOCK_SET,
        'VALIDATE_LOCK_TIMEOUT = "7s"',
        [r4.test_the_runbook_states_the_numbers_the_code_uses],
    ),
    (
        "statement constant changed",
        STMT_SET,
        '"90s"  # the check scans',
        [r4.test_the_runbook_states_the_numbers_the_code_uses],
    ),
    (
        "file loop also gets the statement limit",
        "old[1] if lock_only else VALIDATE_STATEMENT_TIMEOUT",
        "VALIDATE_STATEMENT_TIMEOUT",
        [lock_only_scenario],
    ),
]


@pytest.mark.parametrize(
    ("name", "old", "new", "checks"), TIMEOUT_MUTANTS, ids=[m[0] for m in TIMEOUT_MUTANTS]
)
def test_mutants_of_the_real_timeout_context_are_killed(w, name, old, new, checks):
    assert old != new, name
    with mutated(old, new):
        for check in checks:
            args = (w,) if check.__code__.co_argcount else ()
            _killed(check, *args)
    # and the unmutated source passes the same checks
    for check in checks:
        check(*((w,) if check.__code__.co_argcount else ()))


def test_mutants_that_drop_the_exit_75_mapping_of_the_whole_step_are_killed(w):
    for old in (SETTLE_MAP, VALIDATE_MAP):
        text_old = old.replace("raise _busy", "raise ValueError")
        with mutated(old, text_old):
            _killed(lost_connection_scenario, w)


def test_mutants_of_the_file_loop_lock_limit_are_killed(monkeypatch):
    for old, new in (
        (FILE_LOOP, "with contextlib.nullcontext():"),  # no limit at all: the upgrade queues
        (LOCK_MAP, "except KeyError as exc:"),  # no mapping: a raw LockNotAvailable
    ):
        with mutated(old, new), monkeypatch.context() as m:
            m.setattr(e7, "migrate", migrate_mod.migrate)  # the world calls the mutant
            _killed(busy_file_scenario, m)


def test_a_limit_set_before_the_advisory_lock_is_killed_by_the_wait_test(w, monkeypatch):
    early = "        db.execute(\"SELECT set_config('lock_timeout', '5s', true)\")\n" + ADVISORY
    with mutated(ADVISORY, early), monkeypatch.context() as m:
        m.setattr(e7, "migrate", migrate_mod.migrate)
        _killed(advisory_wait_scenario, w)


def test_mutants_of_the_qualified_names_are_killed(w):
    with mutated(EXCESS_TARGET, "target = (lambda db, n: n)("):
        _killed(
            test_the_portal_privilege_check_reads_our_table_not_a_temp_table_of_the_same_name, w
        )
    with mutated(
        SEED_INSERT, '.format(sql.Identifier("hadavin_limits")),\n            (name, value),'
    ):
        _killed(test_the_limits_seed_writes_our_table_not_a_temp_table_of_the_same_name, w)
    delete_old = 'sql.SQL("DELETE FROM {} WHERE name <> ALL(%s::text[])").format(\n            _in_schema(db, "hadavin_limits")\n        )'
    delete_new = 'sql.SQL("DELETE FROM {} WHERE name <> ALL(%s::text[])").format(\n            sql.Identifier("hadavin_limits")\n        )'
    with mutated(delete_old, delete_new):
        _killed(test_the_limits_seed_writes_our_table_not_a_temp_table_of_the_same_name, w)


# --- n1: a NULL current_schema() -------------------------------------------------------------------------------------


def test_a_search_path_with_no_existing_schema_is_a_clear_config_error(w):
    conninfo = make_conninfo(w.dsn, options=f"-c search_path=no_such_schema_{uuid.uuid4().hex[:8]}")
    with psycopg.connect(conninfo) as db:
        assert db.execute("SELECT current_schema()").fetchone()[0] is None
        for call in (
            lambda: migrate_mod._in_schema(db, "spend"),
            lambda: migrate_mod._qualified(db, "spend"),
            lambda: migrate_mod.validate_constraints(db),
        ):
            with pytest.raises(ConfigError, match=r"current_schema\(\) is NULL"):
                call()


# --- n2: the exit codes: migrate has no connectivity code of its own, and says so --------------------------------------


def test_migrate_exits_3_not_4_for_an_unreachable_database_and_the_runbook_says_why(
    cfg_dir, monkeypatch
):
    text = " ".join(RUNBOOK.read_text(encoding="utf-8").split())
    assert "`migrate` has no connectivity code of its own" in text
    assert "it exits 3 like every other uncaught error of the command" in text
    assert "is_connectivity_error" not in inspect.getsource(cli._migrate)  # nor does the code
    r4._cli_cfg(cfg_dir)
    monkeypatch.setenv("HADAVIN_MIGRATE_DSN", "postgresql://u@127.0.0.1:1/x?connect_timeout=2")
    for args in (["--no-roles"], ["--validate-constraints"]):
        assert cli.main(["--config", str(cfg_dir), "migrate", *args]) == 3
