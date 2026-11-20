"""Ticket A (audit drain): the tick writes parked audit events from the outbox table, and a running process
writes its own memory-parked events at its next successful write.

Written by a different agent than the builder, from the ticket's invariants 1-8. The PostgreSQL cases (E6, E7 and
the two cross-process cases, which start real child processes) skip without HADAVIN_TEST_PG_DSN."""

import json
import logging
import os
import re
import secrets
import subprocess
import sys
import threading
from datetime import UTC
from pathlib import Path

import pytest
import yaml

from hadavin_sdk import defaults
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.app import build
from hadavin_sdk.approvals import FakeChannel
from hadavin_sdk.audit import chain as audit
from hadavin_sdk.config import load_config
from hadavin_sdk.models import AuditEvent
from hadavin_sdk.registry import load_registry
from hadavin_sdk.runtime import tick
from hadavin_sdk.runtime.tick import run_tick
from tests.conftest import qualify
from tests.money_caps_seed import seed_registry_caps

REPO = Path(__file__).resolve().parents[1]
STEP = "audit_drain"
SIG = "sig" + "-audit-drain"  # built from parts
MARK = "BODYTEXT" + "-must-not-leak"  # stands for payload text inside an unreadable outbox body


def _event(i=0, **kw):
    fields = {"run_id": "run-1", "domain": "step", "principal": "p", "source": "s", "result": "ok"}
    return AuditEvent(operation=f"n{i}", **{**fields, **kw})


def _log():
    return audit.ChainAudit(audit._Db.memory())


def _ids(log):
    return [e.event_id for e in log.events()]


def _outbox(log):
    """The outbox rows by their original event id: a poison row is renamed with the quarantine prefix."""
    rows = log._db.run("SELECT event_id, body FROM audit_outbox ORDER BY event_id")
    return sorted((i.removeprefix(defaults.AUDIT_QUARANTINE_PREFIX), b) for i, b in rows)


def _park(log, event):
    """As the code does after a failed append: the event waits in the outbox table."""
    log._db.run(
        "INSERT INTO audit_outbox (event_id, body) VALUES (?, ?)",
        (event.event_id, event.model_dump_json()),
    )


def _boom(*a, **k):
    raise OSError("down")


def _database_down(mp, log):
    """Neither a transaction (the append) nor a statement (the outbox insert) works."""
    mp.setattr(log._db, "transaction", _boom)
    mp.setattr(log._db, "run", _boom)


def _use_chain(cfg_dir, **backends):
    path = cfg_dir / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["backends"]["audit"] = {"kind": "chain"}
    data["backends"].update(backends)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


@pytest.fixture
def app(live_cfg_dir, fake_system):
    """The fixture app with the `chain` audit on the memory store."""
    _use_chain(live_cfg_dir)
    qualify(load_registry(load_config(live_cfg_dir)))
    built = build(
        live_cfg_dir,
        ["test-agent"],
        secrets=FakeSecretProvider({"fixture-token": fake_system.token}),
        channel=FakeChannel(SIG),
        timeout_s=0.5,
    )
    assert isinstance(built.audit, audit.ChainAudit)
    return built


# --- normal ----------------------------------------------------------------------------------------------


def test_n1_audit_drain_is_the_last_tick_step():
    names = [s.name for s in tick.STEPS]
    assert names.count(STEP) == 1  # first: without the row this fails here, not in the lookup below
    assert next(s for s in tick.STEPS if s.name == STEP).every_s == 0
    # audit_drain comes before expire_reservations and check_caps, which is the last step
    assert names[-3:] == [STEP, "expire_reservations", "check_caps"]


def test_n2_one_tick_writes_a_parked_outcome_to_the_chain(app, monkeypatch, caplog):
    log, event = app.audit, _event()
    with monkeypatch.context() as mp:
        mp.setattr(log, "_append", _boom)
        assert log.write_outcome(event) is None  # never raises (invariant 3)
    assert [r[0] for r in _outbox(log)] == [event.event_id] and event.event_id not in _ids(log)
    caplog.set_level("INFO", logger="hadavin_sdk.tick")
    assert run_tick(app) == 0
    assert _ids(log).count(event.event_id) == 1 and _outbox(log) == []
    state = app.store.get_tick_state(STEP)
    assert state.last_error is None and state.last_ok_at is not None
    assert "audit_drain drained=1" in caplog.text
    # invariant 6: the drained event keeps its own time, and the chain still verifies
    at = log._db.run("SELECT at FROM audit_entries WHERE event_id = ?", (event.event_id,))[0][0]
    assert at == event.ts.astimezone(UTC).isoformat(timespec="microseconds")
    assert log.events()[-1] == event and log.verify().ok
    assert run_tick(app) == 0 and _ids(log).count(event.event_id) == 1  # a second tick adds nothing


@pytest.mark.parametrize("writer", ["write_intent", "write_outcome"])
def test_n3_the_next_successful_write_flushes_what_this_process_parked(writer, monkeypatch):
    log, parked, other = _log(), _event(0), _event(1)
    with monkeypatch.context() as mp:
        _database_down(mp, log)
        assert log.write_outcome(parked) is None
    assert log._pending == [parked] and _outbox(log) == []
    assert getattr(log, writer)(other) == other.event_id
    assert log._pending == []
    assert _ids(log) == [other.event_id, parked.event_id]  # chain order is write order
    assert log.events()[1].ts == parked.ts and log.verify().ok


# --- edge ------------------------------------------------------------------------------------------------


def test_e1_an_audit_without_reconcile_is_a_step_that_passes(app):
    class NoReconcile:
        def checkpoint(self):
            return None

    app.audit = NoReconcile()
    assert run_tick(app, steps=[next(s for s in tick.STEPS if s.name == STEP)]) == 0
    assert app.store.get_tick_state(STEP).last_error is None


def test_e2_an_empty_outbox_is_ok(app, caplog):
    caplog.set_level("INFO", logger="hadavin_sdk.tick")
    assert run_tick(app) == 0
    assert app.store.get_tick_state(STEP).last_error is None
    assert "audit_drain drained=0" in caplog.text and app.audit.events() == []


def test_e3_an_event_already_in_the_chain_only_loses_its_outbox_row(app):
    log, event = app.audit, _event()
    log.write_intent(event)
    _park(log, event)
    assert run_tick(app) == 0
    assert _outbox(log) == [] and _ids(log) == [event.event_id] and log.verify().ok


def test_e4_a_flush_stops_at_the_first_failure_and_keeps_the_rest_in_order(monkeypatch):
    log, (a, b, c), trigger = _log(), [_event(i) for i in range(3)], _event(9)
    with monkeypatch.context() as mp:
        _database_down(mp, log)
        for e in (a, b, c):
            log.write_outcome(e)
    assert log._pending == [a, b, c]
    real, tried = log._append, []

    def flaky(event):
        tried.append(event.event_id)
        if event.event_id == b.event_id:
            raise OSError("down again")
        return real(event)

    monkeypatch.setattr(log, "_append", flaky)
    assert log.write_intent(trigger) == trigger.event_id  # a flush failure is never raised
    assert log._pending == [b, c]
    assert _ids(log) == [trigger.event_id, a.event_id]
    attempts = (
        defaults.AUDIT_FLUSH_ATTEMPTS
    )  # A10: b is retried with backoff, c is still never tried
    assert tried == [trigger.event_id, a.event_id] + [b.event_id] * attempts
    monkeypatch.setattr(log, "_append", real)
    assert log.reconcile() == 2 and log._pending == []
    assert _ids(log) == [e.event_id for e in (trigger, a, b, c)] and log.verify().ok


@pytest.mark.parametrize("writer", ["write_intent", "write_outcome"])
def test_e5_a_failed_triggering_append_makes_no_flush_attempt(writer, monkeypatch):
    log, parked, later = _log(), _event(0), _event(1)
    with monkeypatch.context() as mp:
        _database_down(mp, log)
        log.write_outcome(parked)
    tried, flushes, real_flush = [], [], log._flush_pending

    def failing(event):
        tried.append(event.event_id)
        raise OSError("down")

    monkeypatch.setattr(log, "_append", failing)
    monkeypatch.setattr(log, "_flush_pending", lambda: flushes.append(1) or real_flush())
    if writer == "write_intent":
        with pytest.raises(audit.AuditUnavailable):
            log.write_intent(later)
    else:
        assert log.write_outcome(later) is None
    assert tried == [later.event_id] and flushes == []
    assert log._pending == [parked] and log.events() == []


@pytest.mark.parametrize("writer", ["write_intent", "write_outcome"])
def test_a_flush_that_breaks_is_never_the_writers_error(writer, monkeypatch):
    log, parked, later = _log(), _event(0), _event(1)
    with monkeypatch.context() as mp:
        _database_down(mp, log)
        log.write_outcome(parked)

    def broken(event):
        raise RuntimeError("drain broke")

    monkeypatch.setattr(log, "_drain", broken)
    assert getattr(log, writer)(later) == later.event_id  # invariant 3
    assert log._pending == [parked] and _ids(log) == [later.event_id]


def test_write_intent_raises_only_duplicate_or_unavailable(monkeypatch):
    log, event = _log(), _event()
    log.write_intent(event)
    with pytest.raises(audit.DuplicateEvent):
        log.write_intent(event)
    assert log.write_outcome(event) == event.event_id  # a duplicate outcome is not an error
    monkeypatch.setattr(log, "_append", _boom)
    with pytest.raises(audit.AuditUnavailable):
        log.write_intent(_event(1))


def test_an_outbox_row_that_cannot_be_written_yet_is_kept(app, monkeypatch):
    """Invariant 1: the outbox row is deleted only after its event is in the chain."""
    log, event = app.audit, _event()
    _park(log, event)
    with monkeypatch.context() as mp:
        mp.setattr(log, "_append", _boom)
        assert (
            run_tick(app, steps=[next(s for s in tick.STEPS if s.name == STEP)]) == 0
        )  # nothing drained is not a failure
        assert [r[0] for r in _outbox(log)] == [event.event_id]
    assert log.events() == []
    assert run_tick(app, steps=[next(s for s in tick.STEPS if s.name == STEP)]) == 0
    assert _ids(log) == [event.event_id] and _outbox(log) == []


def test_reconcile_writes_memory_first_then_the_outbox(monkeypatch):
    log, in_memory, in_table = _log(), _event(0), _event(1)
    with monkeypatch.context() as mp:
        _database_down(mp, log)
        log.write_outcome(in_memory)
    _park(log, in_table)
    assert log.reconcile() == 2
    assert _ids(log) == [in_memory.event_id, in_table.event_id]
    assert log._pending == [] and _outbox(log) == [] and log.reconcile() == 0


def test_an_outbox_that_answers_with_an_error_fails_the_step(app, caplog):
    """Invariant 5 on the memory chain: a missing table is not "nothing to do"."""
    app.audit._db.run("DROP TABLE audit_outbox")
    caplog.set_level("INFO", logger="hadavin_sdk.tick")
    assert run_tick(app) == 1
    assert app.store.get_tick_state(STEP).last_error.startswith(
        "RuntimeError: audit outbox: read failed (OperationalError)"
    )
    assert "failed=audit_drain" in caplog.text


def test_an_outbox_that_cannot_be_reached_is_a_quiet_return(app, monkeypatch):
    """Invariant 5: a connectivity error reading the outbox keeps the quiet return (retried next tick)."""
    event = _event()
    _park(app.audit, event)
    with monkeypatch.context() as mp:
        mp.setattr(app.audit._db, "run", _boom)
        assert app.audit.reconcile() == 0
        assert run_tick(app, steps=[next(s for s in tick.STEPS if s.name == STEP)]) == 0
    assert app.store.get_tick_state(STEP).last_error is None
    assert [r[0] for r in _outbox(app.audit)] == [event.event_id]  # still there for the next tick


# --- hostile ---------------------------------------------------------------------------------------------


def test_h1_unreadable_rows_are_kept_and_never_block_the_rows_after_them(app, caplog):
    log = app.audit
    good_first, good_last = _event(0, event_id="evt-a"), _event(1, event_id="evt-e")
    moved = _event(2, event_id="evt-elsewhere", result=MARK)
    bad = [
        ("evt-b", f"not json {MARK}"),
        ("evt-c", json.dumps({"wrong": "shape", "text": MARK})),
        ("evt-d", moved.model_dump_json()),  # a readable event under another row's id
    ]
    _park(log, good_first)
    _park(log, good_last)
    for event_id, body in bad:
        log._db.run("INSERT INTO audit_outbox (event_id, body) VALUES (?, ?)", (event_id, body))
    assert [r[0] for r in _outbox(log)] == ["evt-a", "evt-b", "evt-c", "evt-d", "evt-e"]
    caplog.set_level("INFO")
    assert run_tick(app) == 1
    assert _ids(log) == ["evt-a", "evt-e"]  # the row after the bad ones was not blocked
    assert _outbox(log) == bad  # kept, unchanged
    state = app.store.get_tick_state(STEP)
    assert state.last_error == "RuntimeError: audit outbox: 3 unreadable rows kept"
    assert state.last_ok_at is None
    for _, body in bad:
        assert body not in state.last_error and body not in caplog.text
    assert MARK not in state.last_error and MARK not in caplog.text
    assert "step=audit_drain error_kind=RuntimeError" in caplog.text
    assert log.verify().ok
    assert run_tick(app) == 1 and _outbox(log) == bad and _ids(log) == ["evt-a", "evt-e"]


def test_h2_a_one_megabyte_body_is_drained_whole(app):
    log, event = app.audit, _event(decision="x" * (1 << 20))
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(log, "_append", _boom)
        assert log.write_outcome(event) is None
    assert len(_outbox(log)[0][1]) > 1 << 20
    assert run_tick(app) == 0
    assert log.events() == [event] and _outbox(log) == [] and log.verify().ok
    assert app.store.get_tick_state(STEP).last_error is None


def test_h3_two_hundred_writes_with_the_database_down_then_one_success(monkeypatch):
    log, parked, last = _log(), [_event(i) for i in range(200)], _event(200)
    with monkeypatch.context() as mp:
        _database_down(mp, log)
        assert [log.write_outcome(e) for e in parked] == [None] * 200
    assert len(log._pending) == 200
    assert log.write_outcome(last) == last.event_id
    assert log._pending == [] and _outbox(log) == []
    assert _ids(log) == [last.event_id] + [
        e.event_id for e in parked
    ]  # 201, each once, in write order
    v = log.verify()
    assert v.ok and v.rows == 201, v.problems


def test_two_threads_flushing_write_each_parked_event_once(monkeypatch):
    """`_flush_pending` is safe for two threads: no event twice, none lost, none left."""
    log, parked = _log(), [_event(i) for i in range(60)]
    with monkeypatch.context() as mp:
        _database_down(mp, log)
        for e in parked:
            log.write_outcome(e)
    gate, counts = threading.Barrier(2), []

    def flush():
        gate.wait()
        counts.append(log._flush_pending())

    threads = [threading.Thread(target=flush) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sum(counts) == 60 and log._pending == []
    assert _ids(log) == [e.event_id for e in parked] and log.verify().ok


# --- PostgreSQL (skipped without HADAVIN_TEST_PG_DSN) -------------------------------------------------------


class _Pg:
    """One fresh migrated schema with a runtime role (as `migrate --runtime-role` grants it) and a config
    directory that reads both DSNs through the `env` secrets kind, so a child process can be handed them."""

    def __init__(self, cfg_dir, runtime_dsn, purge_dsn):
        from psycopg.conninfo import conninfo_to_dict, make_conninfo

        self.cfg_dir, self.runtime_dsn = cfg_dir, runtime_dsn
        parts = conninfo_to_dict(runtime_dsn)
        self.role = parts["user"]
        self.admin_dsn = make_conninfo(os.environ["HADAVIN_TEST_PG_DSN"], options=parts["options"])
        self.secrets = {
            "HADAVIN_SECRET_PG_DSN": runtime_dsn,
            "HADAVIN_SECRET_PG_PURGE": purge_dsn,
            "HADAVIN_SECRET_FIXTURE_TOKEN": secrets.token_hex(16),
        }

    def admin(self, statement, params=()):
        import psycopg

        with psycopg.connect(self.admin_dsn, autocommit=True) as db:
            cur = db.execute(statement, params)
            return cur.fetchall() if cur.description else []

    def grant(self, verb, privilege, table):
        from psycopg import sql

        word = sql.SQL("TO" if verb == "GRANT" else "FROM")
        self.admin(
            sql.SQL("{} {} ON {} {} {}").format(
                sql.SQL(verb),
                sql.SQL(privilege),
                sql.Identifier(table),
                word,
                sql.Identifier(self.role),
            )
        )

    def park(self, events):
        import psycopg

        with psycopg.connect(self.admin_dsn, autocommit=True) as db:
            for e in events:
                db.execute(
                    "INSERT INTO audit_outbox (event_id, body) VALUES (%s, %s)",
                    (e.event_id, e.model_dump_json()),
                )

    def chain_ids(self):
        return [r[0] for r in self.admin("SELECT event_id FROM audit_entries ORDER BY seq")]

    def outbox_ids(self):
        return [r[0] for r in self.admin("SELECT event_id FROM audit_outbox ORDER BY event_id")]

    def app(self):
        provider = FakeSecretProvider(
            {
                "pg-dsn": self.runtime_dsn,
                "pg-purge": self.secrets["HADAVIN_SECRET_PG_PURGE"],
                "fixture-token": self.secrets["HADAVIN_SECRET_FIXTURE_TOKEN"],
            }
        )
        return build(self.cfg_dir, ["test-agent"], secrets=provider, channel=FakeChannel(SIG))

    def child(self, *argv):
        """A real child process: its own interpreter, its own connection, the runtime role's DSN."""
        env = {**os.environ, **self.secrets, "PYTHONPATH": str(REPO)}
        env.pop("HADAVIN_CONFIG_DIR", None)
        return subprocess.run(  # noqa: S603 (fixed argv, no shell)
            [sys.executable, *argv],
            cwd=REPO,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )

    def cli(self, *args):
        return self.child("-m", "hadavin_sdk.cli", "--config", str(self.cfg_dir), *args)


@pytest.fixture
def pg(cfg_dir):
    pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")
    from tests.contracts.kinds.store_postgres import PURGE_DSN, pg_schema

    for runtime_dsn in pg_schema(runtime=True):
        _use_chain(
            cfg_dir,
            secrets={"kind": "env"},
            store={
                "kind": "postgres",
                "dsn_secret_name": "pg-dsn",
                "purge_dsn_secret_name": "pg-purge",
            },
        )
        registry = load_registry(load_config(cfg_dir))
        qualify(registry)
        out = _Pg(cfg_dir, runtime_dsn, PURGE_DSN[runtime_dsn])
        seed_registry_caps(
            out.admin_dsn, None, registry
        )  # the owner seeds the caps: check_caps finds no drift
        yield out


def _close(*apps):
    for a in apps:
        a.store._db.close()


def test_e6_two_ticks_at_once_write_each_of_fifty_rows_exactly_once(pg):
    events = [_event(i) for i in range(50)]
    pg.park(events)
    apps = [pg.app(), pg.app()]  # two connections, as two tick processes have
    try:
        gate, codes = threading.Barrier(2), []

        def one(app):
            gate.wait()
            codes.append(run_tick(app))

        threads = [threading.Thread(target=one, args=(a,)) for a in apps]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert codes == [0, 0]
        assert sorted(pg.chain_ids()) == sorted(e.event_id for e in events)  # 50 rows, each once
        assert pg.outbox_ids() == []
        v = apps[0].audit.verify()
        assert v.ok and v.rows == 50, v.problems
        assert apps[0].store.get_tick_state(STEP).last_error is None
    finally:
        _close(*apps)


def test_e7_a_runtime_role_that_cannot_read_the_outbox_fails_the_step(pg, caplog):
    event = _event()
    pg.park([event])
    pg.grant("REVOKE", "SELECT", "audit_outbox")
    app = pg.app()
    try:
        caplog.set_level("INFO", logger="hadavin_sdk.tick")
        assert run_tick(app) == 1
        state = app.store.get_tick_state(STEP)
        assert (
            state.last_error.startswith(
                "RuntimeError: audit outbox: read failed (InsufficientPrivilege)"
            )
            and state.last_ok_at is None
        )
        assert "failed=audit_drain" in caplog.text
        assert pg.chain_ids() == [] and pg.outbox_ids() == [event.event_id]
        pg.grant("GRANT", "SELECT", "audit_outbox")
        assert run_tick(app) == 0  # the grant is back: the same row is drained
        assert pg.chain_ids() == [event.event_id] and pg.outbox_ids() == []
    finally:
        _close(app)


# Child 1: one process that writes one outcome through the configured store and audit, then exits.
_WRITER = """
import json, sys
from hadavin_sdk.backends.factory import make
from hadavin_sdk.config import load_config
from hadavin_sdk.models import AuditEvent

b = load_config(sys.argv[1]).backends
secrets = make("secrets", b.secrets)
store = make("store", b.store, secrets)
log = make("audit", b.audit, secrets, store=store, signer=None, anchor=None)
event = AuditEvent(
    event_id=sys.argv[2], run_id="run-x", domain="run", operation="state", principal="p", source="child"
)
print(json.dumps({"key": log.write_outcome(event), "pending": len(log._pending)}))
"""


def _write_in_a_child(pg, event_id):
    done = pg.child("-c", _WRITER, str(pg.cfg_dir), event_id)
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout.strip().splitlines()[-1])


def test_cross_process_an_outcome_parked_by_one_process_is_written_by_the_tick_of_another(pg):
    event_id = "evt-" + secrets.token_hex(8)
    pg.grant("REVOKE", "INSERT", "audit_entries")
    assert _write_in_a_child(pg, event_id) == {"key": None, "pending": 0}  # child 1 has exited
    assert pg.chain_ids() == [] and pg.outbox_ids() == [event_id]
    pg.grant("GRANT", "INSERT", "audit_entries")
    ticked = pg.cli("tick")  # child 2
    assert ticked.returncode == 0, ticked.stderr
    assert "audit_drain drained=1" in ticked.stderr and "failed=-" in ticked.stderr
    assert pg.chain_ids() == [event_id] and pg.outbox_ids() == []  # the parent's own connection
    verified = pg.cli("audit", "verify")
    assert verified.returncode == 0, verified.stdout + verified.stderr


def test_cross_process_an_event_parked_only_in_memory_dies_with_its_process(pg):
    """The stated limit (invariant 7): with the outbox also unwritable, the event lives in the child's memory
    and no later tick can write it."""
    event_id = "evt-" + secrets.token_hex(8)
    pg.grant("REVOKE", "INSERT", "audit_entries")
    pg.grant("REVOKE", "INSERT", "audit_outbox")
    assert _write_in_a_child(pg, event_id) == {"key": None, "pending": 1}
    pg.grant("GRANT", "INSERT", "audit_entries")
    pg.grant("GRANT", "INSERT", "audit_outbox")
    ticked = pg.cli("tick")
    assert ticked.returncode == 0, ticked.stderr
    assert "audit_drain drained=0" in ticked.stderr
    assert event_id not in pg.chain_ids() and pg.outbox_ids() == []


def test_tick_logs_the_drain_count_on_the_tick_logger(app, caplog):
    _park(app.audit, _event())
    with caplog.at_level(logging.INFO, logger="hadavin_sdk.tick"):
        assert run_tick(app, steps=[next(s for s in tick.STEPS if s.name == STEP)]) == 0
    lines = [r.getMessage() for r in caplog.records if r.name == "hadavin_sdk.tick"]
    assert lines[0] == "audit_drain drained=1" and len(lines) == 2  # then the summary line


# =========================================================================================================
# Fix round 1 (tests by a different agent than the builder): a drain failure that is not an outage fails the
# step, and one bad event no longer blocks the rest. "Refused" below is the database answering with an error
# (on the memory chain a real sqlite3 error from a trigger); an "outage" is OSError, StoreUnavailable or
# psycopg's OperationalError/InterfaceError.
# =========================================================================================================

# The audit step alone, selected by name (other steps come after it). A list filter, not `next`: a STEPS
# without the row must fail test n1 on its count, not the import of this file.
LAST = [s for s in tick.STEPS if s.name == STEP]
# Stands for row text inside the database's own error message.
REFUSAL = "REFUSALTEXT-must-not-leak"


def _refuse(log, *events):
    """The memory database now rejects the chain row of these events (sqlite3.IntegrityError): the stand-in for
    a missing INSERT grant or a row the database will not take. `_allow_all` takes it back."""
    log._db.run("CREATE TABLE IF NOT EXISTS test_refused (event_id TEXT PRIMARY KEY)")
    log._db.run(
        "CREATE TRIGGER IF NOT EXISTS test_refuse BEFORE INSERT ON audit_entries "
        "WHEN NEW.event_id IN (SELECT event_id FROM test_refused) "
        "BEGIN SELECT RAISE(ABORT, 'REFUSALTEXT-must-not-leak'); END"
    )
    for e in events:
        log._db.run("INSERT INTO test_refused (event_id) VALUES (?)", (e.event_id,))


def _release(log):
    """The operator action of tickets/A-audit-drain.md: put every quarantined row back under its own event id."""
    prefix = defaults.AUDIT_QUARANTINE_PREFIX
    for (qid,) in log._db.run(
        "SELECT event_id FROM audit_outbox WHERE event_id LIKE ?", (prefix + "%",)
    ):
        log._db.run(
            "INSERT INTO audit_outbox (event_id, body) SELECT substr(event_id, ?), body FROM audit_outbox "
            "WHERE event_id = ?",
            (len(prefix) + 1, qid),
        )
        log._db.run("DELETE FROM audit_outbox WHERE event_id = ?", (qid,))


def _allow_all(log):
    log._db.run("DELETE FROM test_refused")


def _append_fails_for(mp, log, exc, *events):
    """`_append` raises `exc` for these events only; every other event is appended for real."""
    real, ids, tried = log._append, {e.event_id for e in events}, []

    def flaky(event):
        tried.append(event.event_id)
        if event.event_id in ids:
            raise exc
        return real(event)

    mp.setattr(log, "_append", flaky)
    return tried


def _delete_fails_for(mp, log, exc, *events):
    """The outbox DELETE of these events raises `exc`; every other statement runs for real."""
    real, ids = log._db.run, {e.event_id for e in events}

    def run(sql, params=()):
        if sql.startswith("DELETE FROM audit_outbox") and params and params[0] in ids:
            raise exc
        return real(sql, params)

    mp.setattr(log._db, "run", run)


def _outage(kind):
    if kind == "OSError":
        return ConnectionRefusedError("refused " + REFUSAL)
    if kind == "StoreUnavailable":
        from hadavin_sdk.store.protocol import StoreUnavailable

        return StoreUnavailable("gone " + REFUSAL)
    psycopg = pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")
    return getattr(psycopg, kind)("dropped " + REFUSAL)


OUTAGES = ["OSError", "StoreUnavailable", "OperationalError", "InterfaceError"]


def _three(**kw):
    return [_event(i, event_id=f"evt-{c}", **kw) for i, c in enumerate("abc")]


def _park_in_memory(log, *events):
    """As after a write with the whole database down: the events wait in this process's memory."""
    with pytest.MonkeyPatch.context() as mp:
        _database_down(mp, log)
        for e in events:
            assert log.write_outcome(e) is None
    assert log._pending == list(events) and _outbox(log) == []


# --- (1) a row the database refuses, between two good rows ----------------------------------------------------


def test_f1_a_refused_row_between_two_good_rows_fails_the_step_and_blocks_nothing(app, caplog):
    log, (a, b, c) = app.audit, _three(result=MARK)
    for e in (a, b, c):
        _park(log, e)
    _refuse(log, b)
    with pytest.raises(
        audit.sqlite3.IntegrityError, match=REFUSAL
    ):  # the refusal is a real sqlite error
        log._append(b)
    caplog.set_level("DEBUG")
    assert run_tick(app) == 1
    assert _ids(log) == [a.event_id, c.event_id]  # the row after the refused one was drained
    assert _outbox(log) == [(b.event_id, b.model_dump_json())]  # kept, unchanged
    state = app.store.get_tick_state(STEP)
    assert state.last_error == "RuntimeError: audit outbox: 1 rows not writable"
    assert state.last_ok_at is None
    for text in (MARK, REFUSAL, b.event_id, b.model_dump_json()):
        assert text not in state.last_error
    assert MARK not in caplog.text and REFUSAL not in caplog.text
    assert "step=audit_drain error_kind=RuntimeError" in caplog.text
    assert "failed=audit_drain" in caplog.text
    assert "audit outbox: drained=2 unreadable=0 not_writable=1 not_deleted=0 (kept)" in caplog.text
    assert log.verify().ok
    assert run_tick(app) == 1 and [r[0] for r in _outbox(log)] == [b.event_id]  # every tick says so
    _allow_all(log)
    assert run_tick(app) == 1  # a quarantined row stays quarantined until the operator releases it
    _release(log)
    assert (
        run_tick(app) == 0
    )  # the refusal is gone: the same row is drained, once: the same row is drained, once
    assert _ids(log) == [a.event_id, c.event_id, b.event_id] and _outbox(log) == []
    assert app.store.get_tick_state(STEP).last_error is None and log.verify().ok


def test_f1_reconcile_raises_only_after_the_whole_loop_and_with_counts_only():
    log, (a, b, c) = _log(), _three(result=MARK)
    for e in (a, b, c):
        _park(log, e)
    _refuse(log, a, b)
    with pytest.raises(RuntimeError) as caught:
        log.reconcile()
    assert str(caught.value) == "audit outbox: 2 rows not writable"
    assert type(caught.value) is RuntimeError and caught.value.__cause__ is None
    assert _ids(log) == [c.event_id] and [r[0] for r in _outbox(log)] == [a.event_id, b.event_id]


# --- (2) an outage on append stays quiet ----------------------------------------------------------------------


@pytest.mark.parametrize("kind", OUTAGES)
def test_f2_an_outage_on_append_keeps_the_row_and_the_step_ok(kind, app, monkeypatch, caplog):
    log, (a, b, c) = app.audit, _three()
    for e in (a, b, c):
        _park(log, e)
    caplog.set_level("DEBUG")
    with monkeypatch.context() as mp:
        _append_fails_for(mp, log, _outage(kind), b)
        assert (
            log.reconcile() == 1
        )  # no raise; the pass stops at the outage row (nothing newer past it)
        assert [r[0] for r in _outbox(log)] == [b.event_id, c.event_id]
        assert run_tick(app, steps=LAST) == 0
        assert [r[0] for r in _outbox(log)] == [b.event_id, c.event_id]  # still kept
    state = app.store.get_tick_state(STEP)
    assert state.last_error is None and state.last_ok_at is not None
    assert "not_writable" not in caplog.text and "failed=audit_drain" not in caplog.text
    assert REFUSAL not in caplog.text
    assert _ids(log) == [a.event_id]
    assert run_tick(app, steps=LAST) == 0  # the database is back
    assert _ids(log) == [a.event_id, b.event_id, c.event_id] and _outbox(log) == []


def test_f2_a_sqlite_error_on_append_is_not_an_outage(monkeypatch):
    """On the memory chain any sqlite3 error (here OperationalError, the class name psycopg uses for an outage)
    is the database answering, so it is counted."""
    log, event = _log(), _event()
    _park(log, event)
    _append_fails_for(monkeypatch, log, audit.sqlite3.OperationalError("disk I/O error"), event)
    # A sqlite3 OperationalError (locked, I/O) is transient, not an outage and not permanent: the row is refused
    # for now, stays in the outbox, and the step says so.
    with pytest.raises(RuntimeError, match=r"^audit outbox: 1 rows refused for a transient error"):
        log.reconcile()
    assert [r[0] for r in _outbox(log)] == [event.event_id] and log.events() == []


def test_f2_an_outage_does_not_hide_a_refused_row_of_the_same_drain(monkeypatch):
    log, (a, b, c) = _log(), _three()
    for e in (a, b, c):
        _park(log, e)
    _refuse(log, a)
    _append_fails_for(monkeypatch, log, OSError("down"), b)
    with pytest.raises(RuntimeError, match=r"^audit outbox: 1 rows not writable$"):
        log.reconcile()
    assert _ids(log) == [] and [r[0] for r in _outbox(log)] == [a.event_id, b.event_id, c.event_id]


# --- (3) a DELETE that fails for one row ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "exc",
    [audit.sqlite3.OperationalError("database is locked " + REFUSAL), OSError("down " + REFUSAL)],
    ids=["refused", "outage"],
)
def test_f3_a_failed_delete_is_counted_and_the_next_drain_deletes_without_a_duplicate(
    exc, app, monkeypatch, caplog
):
    log, (a, b, c) = app.audit, _three(result=MARK)
    for e in (a, b, c):
        _park(log, e)
    caplog.set_level("DEBUG")
    with monkeypatch.context() as mp:
        _delete_fails_for(mp, log, exc, a)
        assert run_tick(app, steps=LAST) == 1
    assert _ids(log) == [
        e.event_id for e in (a, b, c)
    ]  # a is in the chain; b and c were not blocked
    assert [r[0] for r in _outbox(log)] == [a.event_id]  # only the row whose delete failed is left
    state = app.store.get_tick_state(STEP)
    assert state.last_error == "RuntimeError: audit outbox: 1 rows not deleted"
    assert MARK not in caplog.text and REFUSAL not in caplog.text
    assert "audit outbox: drained=2 unreadable=0 not_writable=0 not_deleted=1 (kept)" in caplog.text
    assert run_tick(app, steps=LAST) == 0  # the second drain: the row goes, the chain is unchanged
    assert _outbox(log) == [] and _ids(log) == [e.event_id for e in (a, b, c)]
    assert _ids(log).count(a.event_id) == 1 and log.verify().ok
    assert app.store.get_tick_state(STEP).last_error is None


# --- (4) the combined text ------------------------------------------------------------------------------------


def _mixed(log, mp, unreadable, refused, undeletable, good=2):
    """An outbox with that many rows of each kind, interleaved by id. Returns the ids that must stay."""
    kept, refused_events, undeletable_events = [], [], []
    for i in range(unreadable):
        log._db.run(
            "INSERT INTO audit_outbox (event_id, body) VALUES (?, ?)",
            (f"evt-{i}-u", f"junk {MARK}"),
        )
        kept.append(f"evt-{i}-u")
    for i in range(refused):
        refused_events.append(_event(i, event_id=f"evt-{i}-r", result=MARK))
    for i in range(undeletable):
        undeletable_events.append(_event(i, event_id=f"evt-{i}-d", result=MARK))
    for i in range(good):
        _park(log, _event(i, event_id=f"evt-{i}-g"))
    for e in refused_events + undeletable_events:
        _park(log, e)
        kept.append(e.event_id)
    if refused_events:
        _refuse(log, *refused_events)
    _delete_fails_for(mp, log, audit.sqlite3.OperationalError("locked"), *undeletable_events)
    return sorted(kept)


@pytest.mark.parametrize(
    ("counts", "text"),
    [
        (
            (2, 1, 3),
            "audit outbox: 2 unreadable rows kept, 1 rows not writable, 3 rows not deleted",
        ),
        ((1, 0, 2), "audit outbox: 1 unreadable rows kept, 2 rows not deleted"),
        ((3, 2, 0), "audit outbox: 3 unreadable rows kept, 2 rows not writable"),
        ((0, 4, 1), "audit outbox: 4 rows not writable, 1 rows not deleted"),
    ],
)
def test_f4_the_error_text_is_the_non_zero_counts_in_a_fixed_order(counts, text, app, caplog):
    log = app.audit
    caplog.set_level("DEBUG")
    with pytest.MonkeyPatch.context() as mp:
        kept = _mixed(log, mp, *counts)
        with pytest.raises(RuntimeError) as caught:
            log.reconcile()
        assert str(caught.value) == text
        assert [r[0] for r in _outbox(log)] == kept  # nothing but the good rows left the outbox
        assert run_tick(app, steps=LAST) == 1
    # the tick was a second pass: the undeletable rows are in the chain by then and their delete failed again, and
    # the refused rows are the quarantined ones of the first pass
    second = re.sub(
        r"(\d+) rows not writable",
        r"\1 poison rows quarantined earlier (event_id prefix 'poison:'; "
        r"operator removal: tickets/A-audit-drain.md)",
        text,
    )
    assert app.store.get_tick_state(STEP).last_error == "RuntimeError: " + second
    assert MARK not in caplog.text and REFUSAL not in caplog.text
    assert (
        "audit outbox: drained=2 unreadable={} not_writable={} not_deleted={} (kept)".format(
            *counts
        )
        in caplog.text
    )
    assert sorted(_ids(log)) == sorted(
        [f"evt-{i}-g" for i in range(2)] + [f"evt-{i}-d" for i in range(counts[2])]
    )
    assert log.verify().ok


def test_f4_a_clean_drain_after_a_failed_one_raises_nothing(app):
    log = app.audit
    with pytest.MonkeyPatch.context() as mp:
        _mixed(log, mp, 0, 1, 1)
        assert run_tick(app, steps=LAST) == 1
    _allow_all(log)
    _release(log)
    assert run_tick(app, steps=LAST) == 0 and _outbox(log) == []
    assert sorted(_ids(log)) == ["evt-0-d", "evt-0-g", "evt-0-r", "evt-1-g"] and log.verify().ok


# --- (5) _flush_pending ---------------------------------------------------------------------------------------


def test_f5_a_flush_moves_a_refused_event_aside_and_writes_the_ones_after_it(caplog):
    log, (a, b, c) = _log(), _three(result=MARK)
    _park_in_memory(log, a, b, c)
    _refuse(log, b)
    caplog.set_level("DEBUG")
    assert log._flush_pending() == 2  # nothing raised; b is not counted as written
    assert _ids(log) == [a.event_id, c.event_id]  # first and third, in order
    assert log._unwritable == [b] and log._pending == [] and _outbox(log) == []
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert [r.getMessage() for r in warnings] == [
        "audit pending flush: written=2 not_writable=1 (kept in memory, total=1)"
    ]
    assert MARK not in caplog.text and REFUSAL not in caplog.text and b.event_id not in caplog.text
    assert log.verify().ok
    # a later flush with another refused event: the total counts what is kept, the count what this flush moved
    d, e = _event(3, event_id="evt-d"), _event(4, event_id="evt-e")
    _park_in_memory(log, d, e)
    _refuse(log, d)
    caplog.clear()
    assert log._flush_pending() == 1
    assert log._unwritable == [b, d] and log._pending == []
    assert _ids(log) == [a.event_id, c.event_id, e.event_id]
    assert "audit pending flush: written=1 not_writable=1 (kept in memory, total=2)" in caplog.text
    caplog.clear()
    assert (
        log._flush_pending() == 0 and caplog.text == ""
    )  # nothing pending: no warning, no retry of b, d
    assert log._unwritable == [b, d]


def test_f5_a_flush_with_every_event_refused_empties_pending_and_raises_nothing(caplog):
    log, (a, b, c) = _log(), _three()
    _park_in_memory(log, a, b, c)
    _refuse(log, a, b, c)
    caplog.set_level("WARNING")
    assert log._flush_pending() == 0
    assert log._unwritable == [a, b, c] and log._pending == [] and log.events() == []
    assert "audit pending flush: written=0 not_writable=3 (kept in memory, total=3)" in caplog.text


@pytest.mark.parametrize("kind", OUTAGES)
def test_f5_a_flush_stops_at_an_outage_and_keeps_the_rest_in_order(kind, monkeypatch, caplog):
    log, (a, b, c) = _log(), _three()
    _park_in_memory(log, a, b, c)
    caplog.set_level("DEBUG")
    with monkeypatch.context() as mp:
        tried = _append_fails_for(mp, log, _outage(kind), b)
        assert log._flush_pending() == 1
        assert (
            tried == [a.event_id] + [b.event_id] * defaults.AUDIT_FLUSH_ATTEMPTS
        )  # A10: retried with backoff; c not tried
    assert _ids(log) == [a.event_id]
    assert log._pending == [b, c] and log._unwritable == []
    assert "not_writable" not in caplog.text
    assert log._flush_pending() == 2  # the database is back
    assert _ids(log) == [e.event_id for e in (a, b, c)] and log._pending == [] and log.verify().ok


def test_f5_reconcile_still_drains_the_outbox_after_its_flush_moved_an_event_aside(caplog):
    """A refused memory-parked event is moved aside by the flush inside reconcile; the outbox drain after it
    still runs to its end, and only then the call raises (fix round 2: the event moved aside is counted)."""
    log, (a, b, c) = _log(), _three()
    _park_in_memory(log, a, b)
    _park(log, c)
    _refuse(log, a)
    caplog.set_level("WARNING")
    with pytest.raises(RuntimeError, match="^audit outbox: 1 events not writable in memory$"):
        log.reconcile()
    # b from memory, c from the outbox; no outbox row has a problem
    assert _ids(log) == [b.event_id, c.event_id] and log._unwritable == [a] and _outbox(log) == []
    assert "audit outbox: drained=2 unreadable=0 not_writable=0" in caplog.text


# --- (7) the writers' contracts when the flush moves events aside ---------------------------------------------


@pytest.mark.parametrize("writer", ["write_intent", "write_outcome"])
def test_f7_a_writer_whose_flush_moves_events_aside_returns_its_key(writer, caplog):
    log, (a, b, c), later = _log(), _three(), _event(9, event_id="evt-z")
    _park_in_memory(log, a, b, c)
    _refuse(log, a, c)
    caplog.set_level("WARNING")
    assert getattr(log, writer)(later) == later.event_id  # nothing raised
    assert _ids(log) == [later.event_id, b.event_id]
    assert log._unwritable == [a, c] and log._pending == []
    assert "audit pending flush: written=1 not_writable=2 (kept in memory, total=2)" in caplog.text
    assert log.verify().ok


def test_f7_write_outcome_never_raises_and_write_intent_raises_only_its_two_errors(monkeypatch):
    log, (a, b, c) = _log(), _three()
    _park_in_memory(log, a)
    _refuse(log, a, b)
    first = _event(5, event_id="evt-first")
    assert log.write_intent(first) == first.event_id  # its flush moves `a` aside
    assert log._unwritable == [a]
    with pytest.raises(audit.DuplicateEvent):
        log.write_intent(first)
    assert log.write_outcome(first) == first.event_id  # a duplicate outcome is not an error
    # the writer's own event is refused: the intent is "unavailable", the outcome is parked in the outbox
    with pytest.raises(audit.AuditUnavailable) as caught:
        log.write_intent(b)
    assert type(caught.value) is audit.AuditUnavailable and REFUSAL not in str(caught.value)
    assert log.write_outcome(b) is None
    assert [r[0] for r in _outbox(log)] == [b.event_id]
    assert (
        log._unwritable == [a] and log._pending == []
    )  # the writer's own refusal is not "moved aside"
    # with the database down the two contracts are the same as before
    with monkeypatch.context() as mp:
        _database_down(mp, log)
        with pytest.raises(audit.AuditUnavailable):
            log.write_intent(c)
        assert log.write_outcome(c) is None
    assert log._pending == [c] and log._unwritable == [a]
    assert _ids(log) == [first.event_id] and log.verify().ok


# --- (6) PostgreSQL: a real runtime-role login without INSERT on audit_entries --------------------------------


def test_f6_pg_a_runtime_role_that_cannot_insert_fails_the_step_and_keeps_the_row(pg):
    event = _event(event_id="evt-" + secrets.token_hex(8), result=MARK)
    pg.park([event])
    pg.grant("REVOKE", "INSERT", "audit_entries")
    ticked = pg.cli("tick")  # a real child process that logs in as the runtime role
    assert ticked.returncode == 1, ticked.stderr
    assert "step=audit_drain error_kind=RuntimeError" in ticked.stderr
    assert "audit outbox: 1 rows not writable" in ticked.stderr
    assert "failed=audit_drain" in ticked.stderr and "audit_drain drained=" not in ticked.stderr
    assert MARK not in ticked.stderr and MARK not in ticked.stdout
    assert pg.outbox_ids() == [event.event_id] and pg.chain_ids() == []  # the row is still parked
    app = pg.app()
    try:
        state = app.store.get_tick_state(STEP)
        assert state.last_error == "RuntimeError: audit outbox: 1 rows not writable"
        assert state.last_ok_at is None
    finally:
        _close(app)
    pg.grant("GRANT", "INSERT", "audit_entries")
    again = pg.cli("tick")
    assert again.returncode == 0, again.stderr
    assert "audit_drain drained=1" in again.stderr and "failed=-" in again.stderr
    assert pg.chain_ids() == [event.event_id] and pg.outbox_ids() == []  # exactly once
    app = pg.app()
    try:
        assert app.store.get_tick_state(STEP).last_error is None
        v = app.audit.verify()
        assert v.ok and v.rows == 1, v.problems
    finally:
        _close(app)


def test_f6_pg_in_one_process_the_refused_row_does_not_block_and_is_drained_after_the_grant(
    pg, caplog
):
    """The same refusal on the tick's own connection: the failed INSERT's transaction is rolled back, so the
    connection still works for the next tick."""
    a, b = _event(0, event_id="evt-a-" + secrets.token_hex(4)), _event(1, event_id="evt-b-x")
    pg.park([a, b])
    pg.grant("REVOKE", "INSERT", "audit_entries")
    app = pg.app()
    try:
        caplog.set_level("INFO")
        assert run_tick(app) == 1
        state = app.store.get_tick_state(STEP)
        assert state.last_error == "RuntimeError: audit outbox: 2 rows not writable"
        assert pg.chain_ids() == [] and pg.outbox_ids() == sorted([a.event_id, b.event_id])
        assert (
            "permission denied" not in caplog.text
        )  # counts only: the database's text is not logged
        pg.grant("GRANT", "INSERT", "audit_entries")
        assert run_tick(app) == 0
        assert sorted(pg.chain_ids()) == sorted([a.event_id, b.event_id]) and pg.outbox_ids() == []
        assert app.store.get_tick_state(STEP).last_error is None and app.audit.verify().ok
    finally:
        _close(app)


# --- (8) fix round 2: events this process could never write are in the failure text ---------------------------


def test_f8_an_event_moved_aside_in_memory_fails_the_step_with_its_count(app, caplog):
    log, a = app.audit, _event(0, event_id="evt-a", result=MARK)
    _park_in_memory(log, a)
    _refuse(log, a)
    caplog.set_level("DEBUG")
    assert log._flush_pending() == 0 and log._unwritable == [a] and log._pending == []
    with pytest.raises(RuntimeError) as caught:
        log.reconcile()
    assert str(caught.value) == "audit outbox: 1 events not writable in memory"
    assert type(caught.value) is RuntimeError and caught.value.__cause__ is None
    assert run_tick(app, steps=LAST) == 1  # the tick step fails, on every tick of this process
    state = app.store.get_tick_state(STEP)
    assert state.last_error == "RuntimeError: audit outbox: 1 events not writable in memory"
    assert state.last_ok_at is None
    _allow_all(log)  # fix round 3: reconcile retries such an event once per run; now it is written
    assert run_tick(app, steps=LAST) == 0 and log._unwritable == [] and _ids(log) == [a.event_id]
    a = _event(
        1, event_id="evt-a2", result=MARK
    )  # a new refused event for the four-counts check below
    _park_in_memory(log, a)
    _refuse(log, a)
    assert log._flush_pending() == 0 and log._unwritable == [a]
    # all four counts at once: the first three keep their order and their texts, the new one is last
    with pytest.MonkeyPatch.context() as mp:
        kept = _mixed(log, mp, 2, 1, 3)
        with pytest.raises(RuntimeError) as caught:
            log.reconcile()
        assert str(caught.value) == (
            "audit outbox: 2 unreadable rows kept, 1 rows not writable, 3 rows not deleted, "
            "1 events not writable in memory"
        )
        assert [r[0] for r in _outbox(log)] == kept and log._unwritable == [a]
    # counts only, never event text
    for text in (MARK, REFUSAL, a.event_id):
        assert text not in caplog.text and text not in state.last_error
    assert log.verify().ok


# --- fix round 3: only connection-level errors count as an outage (chain._is_outage) --------------------------------
# Stand-ins named like psycopg's classes in a module that starts with "psycopg": the helper recognises driver errors
# by class name along the MRO (no driver import), exactly as store.protocol.is_connectivity_error does.


def _driver_error(name, sqlstate="__none__"):
    base = type("Error", (Exception,), {"__module__": "psycopg.errors"})
    cls = type(name, (base,), {"__module__": "psycopg.errors"})
    exc = cls("driver text that must not matter")
    if sqlstate != "__none__":
        exc.sqlstate = sqlstate
    return exc


@pytest.mark.parametrize(
    ("exc", "outage"),
    [
        (OSError("refused"), True),
        (_driver_error("InterfaceError"), True),
        (_driver_error("OperationalError"), True),  # no SQLSTATE: unknown, treated as an outage
        (_driver_error("OperationalError", None), True),
        (_driver_error("OperationalError", "08006"), True),  # connection failure
        (_driver_error("OperationalError", "08001"), True),
        (_driver_error("OperationalError", "57P01"), True),  # administrator shutdown
        (_driver_error("OperationalError", "57P03"), True),  # cannot connect now
        # Not an outage (the database answered) but NOT permanent either: see test_f9_permanent_classes.
        (_driver_error("OperationalError", "57014"), False),
        (_driver_error("OperationalError", "25006"), False),
        (_driver_error("ProgrammingError", "42501"), False),
        (RuntimeError("something else"), False),
        (ValueError("bad row"), False),
    ],
)
def test_f9_only_connection_level_errors_are_an_outage(exc, outage):
    assert audit._is_outage(exc) is outage


@pytest.mark.parametrize(
    ("exc", "permanent"),
    [
        (_driver_error("DataError", "22021"), True),  # class 22 (NUL in text)
        (_driver_error("IntegrityError", "23505"), True),  # class 23
        (_driver_error("ProgrammingError", "42501"), True),  # missing grant
        (_driver_error("OperationalError", "54000"), True),  # row too large for an index
        (_driver_error("DataError"), True),  # no SQLSTATE, a data error by class
        (ValueError("bad row"), True),
        (audit.sqlite3.IntegrityError("trigger refused"), True),
        # Wrong before (f9 pinned 57014 and 25006 as permanent): these all heal by waiting.
        (_driver_error("OperationalError", "57014"), False),  # statement timeout
        (_driver_error("OperationalError", "55P03"), False),  # lock not available
        (_driver_error("OperationalError", "40001"), False),  # serialization failure
        (_driver_error("OperationalError", "40P01"), False),  # deadlock
        (_driver_error("OperationalError", "53300"), False),  # too many connections
        (_driver_error("OperationalError", "53100"), False),  # disk full: an operator frees it
        (_driver_error("OperationalError", "25006"), False),  # read-only transaction (a failover)
        (_driver_error("OperationalError", "08006"), False),
        (_driver_error("OperationalError", "57P01"), False),
        (_driver_error("OperationalError"), False),
        (OSError("refused"), False),
        (audit.sqlite3.OperationalError("locked"), False),
    ],
)
def test_f9_only_the_known_permanent_classes_are_permanent(exc, permanent):
    assert audit._is_permanent(exc) is permanent


def test_f9_a_store_unavailable_is_an_outage():
    from hadavin_sdk.store.protocol import StoreUnavailable

    assert audit._is_outage(StoreUnavailable("down")) is True


def test_f9_a_sqlite_error_is_not_an_outage():
    import sqlite3

    assert audit._is_outage(sqlite3.IntegrityError("trigger refused")) is False


@pytest.fixture(autouse=True)
def _quarantine_at_once(monkeypatch):
    """The cases of this file pin the quarantine mechanics with the age set to 0; the age rule is tests/test_audit_drain_a11.py."""
    monkeypatch.setattr(defaults, "AUDIT_QUARANTINE_AFTER_S", 0)
