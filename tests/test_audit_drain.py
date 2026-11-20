"""Ticket A (audit drain): the tick writes parked audit events from the outbox table, and a running process
writes its own memory-parked events at its next successful write.

Written by a different agent than the builder, from the ticket's invariants 1-8. The PostgreSQL cases (E6, E7 and
the two cross-process cases, which start real child processes) skip without HADAVIN_TEST_PG_DSN."""

import json
import logging
import os
import secrets
import subprocess
import sys
import threading
from datetime import UTC
from pathlib import Path

import pytest
import yaml

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
    return log._db.run("SELECT event_id, body FROM audit_outbox ORDER BY event_id")


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
    assert tick.STEPS[-1].name == STEP and tick.STEPS[-1].every_s == 0
    assert [s.name for s in tick.STEPS].count(STEP) == 1


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
    assert run_tick(app, steps=[tick.STEPS[-1]]) == 0
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
    assert tried == [trigger.event_id, a.event_id, b.event_id]  # c was not tried after b failed
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
        assert run_tick(app, steps=[tick.STEPS[-1]]) == 0  # nothing drained is not a failure
        assert [r[0] for r in _outbox(log)] == [event.event_id]
    assert log.events() == []
    assert run_tick(app, steps=[tick.STEPS[-1]]) == 0
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
    assert app.store.get_tick_state(STEP).last_error.startswith("OperationalError: ")
    assert "failed=audit_drain" in caplog.text


def test_an_outbox_that_cannot_be_reached_is_a_quiet_return(app, monkeypatch):
    """Invariant 5: a connectivity error reading the outbox keeps the quiet return (retried next tick)."""
    event = _event()
    _park(app.audit, event)
    with monkeypatch.context() as mp:
        mp.setattr(app.audit._db, "run", _boom)
        assert app.audit.reconcile() == 0
        assert run_tick(app, steps=[tick.STEPS[-1]]) == 0
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
    log, event = app.audit, _event(result="x" * (1 << 20))
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
        qualify(load_registry(load_config(cfg_dir)))
        yield _Pg(cfg_dir, runtime_dsn, PURGE_DSN[runtime_dsn])


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
        assert state.last_error.startswith("InsufficientPrivilege: ") and state.last_ok_at is None
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
        assert run_tick(app, steps=[tick.STEPS[-1]]) == 0
    lines = [r.getMessage() for r in caplog.records if r.name == "hadavin_sdk.tick"]
    assert lines[0] == "audit_drain drained=1" and len(lines) == 2  # then the summary line
