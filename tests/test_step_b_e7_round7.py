"""Round 7 review of the stop-year validation step (review-ts-watermark-7): the wait for another `migrate` has no
limit whatever the login's default `lock_timeout` is; a migration file may not set the two limits `migrate` owns; no
restore before the commit, so a refusal keeps exit 2 on a connection that died unnoticed; a role change is announced
only after the commit; the exit-75 text of the span names the lock wait only. Source-level mutants of the REAL
migrate.py and migration_numbers.py. Needs HADAVIN_TEST_PG_DSN."""

from __future__ import annotations

import os
import threading
import time

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg
from psycopg import errors, sql
from psycopg.conninfo import make_conninfo

from hadavin_sdk import cli
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.store import migrate as migrate_mod
from hadavin_sdk.store import migration_numbers
from tests import test_migration_numbers as lexer_tests
from tests import test_step_b_e7_round4 as r4
from tests import test_step_b_e7_round5 as r5
from tests import test_step_b_e7_round6 as r6
from tests.test_step_b_e7_migration_0009 import drop_world, make_world

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)

SESSION_LIMIT = 2  # seconds: the login's own default in the m1 scenario, below our 5s


# --- m1: the advisory wait has no limit, whatever the session default is ------------------------------------------


def session_default_scenario():
    """The login arrives with lock_timeout 2s (what ALTER DATABASE or ALTER ROLE ... SET, or the DSN, gives). A
    second `migrate` still waits for the first on the advisory lock for longer than that, then runs."""
    up = make_world()
    holder = psycopg.connect(up.scoped, autocommit=True)
    out: dict = {}
    try:
        up.migrate()
        dsn = make_conninfo(
            up.dsn, options=f"-c search_path={up.schema} -c lock_timeout={SESSION_LIMIT}s"
        )
        with psycopg.connect(dsn) as db:
            assert db.execute("SHOW lock_timeout").fetchone()[0] == f"{SESSION_LIMIT}s"
        holder.execute("SET idle_in_transaction_session_timeout = '40s'")
        holder.execute("BEGIN")
        holder.execute("SELECT pg_advisory_xact_lock(%s)", (migrate_mod._LOCK,))

        def run():
            started = time.monotonic()
            try:
                out["applied"] = migrate_mod.migrate(dsn, **r6._role_kwargs(up))
            except BaseException as exc:  # noqa: BLE001 - handed to the test thread
                out["err"] = exc
            out["seconds"] = time.monotonic() - started

        thread = threading.Thread(target=run)
        thread.start()
        time.sleep(SESSION_LIMIT + 3)
        assert thread.is_alive(), out  # still waiting after the session's own limit
        holder.execute("ROLLBACK")
        thread.join(60)
        assert "err" not in out, out
        assert out["applied"] == [] and out["seconds"] >= SESSION_LIMIT + 3
    finally:
        holder.close()
        drop_world(up)


def test_a_second_migrate_waits_longer_than_a_session_default_lock_timeout():
    session_default_scenario()


# --- n1: no restore before the commit --------------------------------------------------------------------------------


class Dying(r6.Probe):
    """The real connection of `migrate`; once `state["dead"]` is set every further statement raises a
    lost-connection error (a connection that died without the client noticing). The rollback still goes through the
    real connection."""

    def __init__(self, db, state):
        super().__init__(db, set(), {})
        self._state = state

    def execute(self, query, *args, **kwargs):
        if self._state["dead"]:
            raise psycopg.OperationalError("injected: the connection is gone")
        return self._db.execute(query, *args, **kwargs)


def test_a_refusal_keeps_exit_2_when_the_connection_died_unnoticed(monkeypatch, cfg_dir, capsys):
    up = make_world()
    try:
        up.migrate()
        state = {"dead": False}
        real = migrate_mod.connect

        def refuse(*args, **kwargs):
            state["dead"] = True
            return ["someone_else"]

        r4._cli_cfg(cfg_dir)
        monkeypatch.setenv("HADAVIN_MIGRATE_DSN", up.scoped)
        with monkeypatch.context() as m:
            m.setattr(migrate_mod, "connect", lambda *a, **k: Dying(real(*a, **k), state))
            m.setattr(migrate_mod, "who_else_can_clear", refuse)
            assert cli.main(["--config", str(cfg_dir), "migrate", *r6._role_flags(up)]) == 2
        assert state["dead"]
        assert "could clear a stop" in capsys.readouterr().err
    finally:
        drop_world(up)


# --- n3: a role change is announced only after the commit ------------------------------------------------------------


def _set_wide(up):
    """A role-wide search_path default on the runtime role: the next migrate pins this database and reports it."""
    with psycopg.connect(up.dsn, autocommit=True) as db:
        db.execute(
            sql.SQL("ALTER ROLE {} SET search_path = other_app").format(sql.Identifier(up.runtime))
        )


def _failing(exc):
    def boom(*args, **kwargs):
        raise exc

    return boom


def announce_scenario(monkeypatch):
    """A run that changes a role setting and then ends in a refusal or a lock timeout is rolled back: the callback
    hears nothing. The next, successful run hears the change once."""
    up = make_world()
    try:
        up.migrate()
        _set_wide(up)
        seen: list[str] = []
        for exc, raised in (
            (ConfigError("a named role can still maintain the stop tables"), ConfigError),
            (errors.LockNotAvailable("injected"), migrate_mod.StopTablesBusy),
        ):
            with monkeypatch.context() as m:
                m.setattr(migrate_mod, "check_maintain", _failing(exc))
                with pytest.raises(raised):
                    migrate_mod.migrate(
                        up.scoped, **r6._role_kwargs(up), on_role_change=seen.append
                    )
            assert seen == [], seen
        migrate_mod.migrate(up.scoped, **r6._role_kwargs(up), on_role_change=seen.append)
        assert len(seen) == 1 and up.runtime in seen[0]
    finally:
        drop_world(up)


def test_a_role_change_is_announced_only_after_the_commit(monkeypatch):
    announce_scenario(monkeypatch)


# --- n2, n3: what the command line prints for a 75 and for a refusal ---------------------------------------------------


def test_the_cli_prints_no_changed_line_and_a_plain_lock_message_for_a_run_that_is_rolled_back(
    monkeypatch, cfg_dir, capsys
):
    up = make_world()
    try:
        up.migrate()
        _set_wide(up)
        r4._cli_cfg(cfg_dir)
        monkeypatch.setenv("HADAVIN_MIGRATE_DSN", up.scoped)
        argv = ["--config", str(cfg_dir), "migrate", *r6._role_flags(up)]
        capsys.readouterr()
        with monkeypatch.context() as m:
            m.setattr(migrate_mod, "check_maintain", _failing(errors.LockNotAvailable("injected")))
            assert cli.main(argv) == 75
        err = capsys.readouterr().err
        assert "retry later: could not get a lock" in err and "waited 5s" in err
        assert err.count("nothing was applied") == 1  # said once
        for wrong in ("changed:", "scan took longer", "the connection failed"):
            assert wrong not in err, (
                err
            )  # causes that cannot apply to a lock wait, and no role-change line
        with monkeypatch.context() as m:
            m.setattr(migrate_mod, "check_maintain", _failing(ConfigError("refused here")))
            assert cli.main(argv) == 2
        assert "changed:" not in capsys.readouterr().err
        assert cli.main(argv) == 0
        err = capsys.readouterr().err
        assert "changed: " in err and up.runtime in err
    finally:
        drop_world(up)


# --- m1, m2, n4: the runbook says what the code does -----------------------------------------------------------------


def test_the_runbook_states_the_round_7_rules():
    text = " ".join(r5.RUNBOOK.read_text(encoding="utf-8").split())
    for sentence in (
        (
            "`migrate` sets `lock_timeout` to 0 for that wait itself, so a default of the role, the database or the "
            "DSN does not end it"
        ),
        (
            "A migration file may not set `lock_timeout` or `statement_timeout` (nor any other setting): `migrate` "
            "owns both limits"
        ),
        (
            "a row outside the range (for `--validate-constraints` only: in a plain `migrate` such a row is the "
            "warning above and the exit is 0)"
        ),
        "(opening the connection, the ledger steps, the file loop, the grants and checks, the commit;",
        "only after the commit, so never for a run that ends in 75 or 2",
    ):
        assert sentence in text, sentence
    assert (
        "until just before it commits" not in text
    )  # the commit ends the limit; nothing is put back


# --- mutants of the real sources ---------------------------------------------------------------------------------------

ZERO = '    _lock_limit(db, "0")\n'
BUFFER = "            changes = list(check_role_settings(db, named))\n"
EARLY = "            [on_role_change(c) for c in changes if on_role_change]\n"
SET_RULE = "        elif m := _SET.match(s):\n"

ROUND7_MUTANTS = [
    (
        "the advisory wait inherits the session's lock_timeout (the 0 is not set)",
        migrate_mod,
        ZERO,
        "",
        session_default_scenario,
    ),
    (
        "a role change is announced inside the transaction",
        migrate_mod,
        BUFFER,
        BUFFER + EARLY,
        announce_scenario,
    ),
    (
        "the lexer allows SET LOCAL lock_timeout again",
        migration_numbers,
        SET_RULE,
        '        elif (m := _SET.match(s)) and "lock_timeout" not in s.lower():\n',
        lexer_tests.limits_refused_scenario,
    ),
    (
        "the lexer allows SET LOCAL statement_timeout again",
        migration_numbers,
        SET_RULE,
        '        elif (m := _SET.match(s)) and "statement_timeout" not in s.lower():\n',
        lexer_tests.limits_refused_scenario,
    ),
]


@pytest.mark.parametrize(
    ("name", "module", "old", "new", "check"), ROUND7_MUTANTS, ids=[m[0] for m in ROUND7_MUTANTS]
)
def test_mutants_of_round_7_are_killed(monkeypatch, name, module, old, new, check):
    """Each scenario also runs unmutated as a test of its own (and must pass there)."""
    assert old != new, name
    with r5.mutated(old, new, module), monkeypatch.context() as m:
        r5._killed(check, *((m,) if check.__code__.co_argcount else ()))
