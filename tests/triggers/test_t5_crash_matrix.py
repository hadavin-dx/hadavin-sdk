"""Crash matrix for the signed trigger endpoint and its worker (ticket D, step D).

One row per crash point on the path of ONE signed request: every store call of `Runner.start`
(worker.py:124-152) and of `Runtime.handle` (agent_loop.py:352-585, the "nothing to do" path), the
audit writes and the model call, each `:before` and `:after`. The points are wrap points of
`hadavin_sdk.testing.crash.CrashPoints`: no hook lives in the worker.

Two runs of the same table:
- PostgreSQL (needs HADAVIN_TEST_PG_DSN; skipped without it, never skipped with it): a child process
  is killed at the point (`os._exit`, exit code 137), a second child is started, the tick's `stuck`
  step runs a day later, then the same request is signed again and sent again.
- memory store, same process, mode "raise": the thread that reaches the point dies there
  (`SimulatedCrash`). Only the points where that is a fair stand-in for a kill are run (see
  `MEMORY_POINTS`).

This file is also the child script: `python -m tests.triggers.test_t5_crash_matrix --config-dir ...`
(the launcher of crash_launcher.py wraps four store methods only; this child wraps all of them, the
audit sink and the model double, with ONE CrashPoints object, after the runtime is built).

The expectation table below was written from the code BEFORE the first run. Where a run showed a
different end state the table says so in a comment next to the row.

With CRASH_MATRIX_OBSERVED set to a file path, every case appends one JSON line with what it saw.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from wsgiref.util import setup_testing_defaults

import pytest

from hadavin_sdk.approvals import hmac_v0
from hadavin_sdk.audit import LocalDirSink
from hadavin_sdk.config import load_config
from hadavin_sdk.models import RunState, now
from hadavin_sdk.registry import load_registry
from hadavin_sdk.runtime import tick
from hadavin_sdk.store import MemoryStore
from hadavin_sdk.store.protocol import NotFound
from hadavin_sdk.testing.crash import CrashPoints, SimulatedCrash
from hadavin_sdk.triggers import worker
from tests.contracts.kinds.store_postgres import pg_schema
from tests.k5_support import build_runtime, k5_cfg
from tests.triggers.crash_launcher import (
    AGENT,
    DSN_ENV,
    HOST,
    PATH,
    PREFIX,
    PRINCIPAL,
    RESERVES,
    ROOT,
    SECRETS_ENV,
    Child,
    CountingLLM,
    _all_runs,
    install_pg_test_seeding,
    make_trigger_app,
    signed_post,
    wire_body,
)
from tests.triggers.crash_money import (
    assert_end_state,
    assert_kill_state,
    calls_done,
    memory_money,
    pg_money,
)
from tests.triggers.test_t5_postgres import (
    DOCUMENT,
    _arm,
    _calls,
    _killed,
    _ref,
    _rows,
    _run_id,
    _settled,
    _stuck_tick,
)

if os.environ.get("HADAVIN_TEST_PG_DSN"):  # set: the driver must be there, never a silent skip
    import psycopg
    from psycopg.conninfo import make_conninfo

SENDER, KEY = "sender-a", "key-1"
SECRET = "cm" * 4 + "c" * 32  # a fake secret, built from parts (40 characters)
ONE = {SENDER: SECRET}
OK = (200, 202)
IN_PROGRESS = ("RECEIVED", "WORKING")
FINAL = "NO_ACTION"  # where the model double's "nothing to do" ends a run
OBSERVED_ENV = "CRASH_MATRIX_OBSERVED"
FIRE_WAIT_S = 10.0

# What the child (and the memory run) wraps. "store" = the write and limits methods of the runtime
# plus `get_run` of the store handed to the Runner; "loop" = `get_run` as the runtime calls it (a
# name of its own, so a point can tell the Runner's reads from the loop's reads).
STORE_POINTS = (
    ("create_run", "transition", "touch", "put_redaction_map")
    if RESERVES  # the settle books the run cost: `add_cost` is no call of the loop any more
    else ("create_run", "transition", "touch", "put_redaction_map", "add_cost")
)
LIMITS_POINTS = (
    ("get_kill_switch", "spend_totals", "reserve_spend", "settle_spend")
    if RESERVES
    else ("get_kill_switch", "spend_totals", "add_spend")
)
RUNNER_POINTS = ("get_run",)

# --- the expectation table (written before the first run) ------------------------------------------
#
# Every call `handle` makes on a wrapped collaborator for one fresh request, in order, on the path
# "the model answers with no tool call" (agent_loop.py line numbers):
#   (method, nth call of that method, where, run row before the call, row after it,
#    model calls made before the call, after it).
# Row None = no row. The row changes only at create_run and at the two transitions; the model
# double counts a call when `chat` is entered, so the count changes inside llm.chat.
HANDLE_STEPS: tuple[tuple[str, int, str, str | None, str, int, int], ...] = (
    ("store.create_run", 1, "389", None, "RECEIVED", 0, 0),
    ("audit.write_outcome", 1, "394 run received", "RECEIVED", "RECEIVED", 0, 0),
    ("loop.get_run", 1, "330 via 395", "RECEIVED", "RECEIVED", 0, 0),
    ("store.transition", 1, "331 RECEIVED to WORKING", "RECEIVED", "WORKING", 0, 0),
    ("audit.write_outcome", 2, "332 state WORKING", "WORKING", "WORKING", 0, 0),
    ("store.get_kill_switch", 1, "404 via limits.py:21", "WORKING", "WORKING", 0, 0),
    ("store.spend_totals", 1, "404 via limits.py:23", "WORKING", "WORKING", 0, 0),
    ("store.put_redaction_map", 1, "408", "WORKING", "WORKING", 0, 0),
    ("store.put_redaction_map", 2, "424", "WORKING", "WORKING", 0, 0),
    ("store.get_kill_switch", 2, "466 via limits.py:21", "WORKING", "WORKING", 0, 0),
    ("store.spend_totals", 2, "466 via limits.py:23", "WORKING", "WORKING", 0, 0),
    ("store.touch", 1, "468 heartbeat", "WORKING", "WORKING", 0, 0),
    *(
        (  # the worst case is reserved before the call and settled after it (limits.reserve / settle)
            ("store.get_kill_switch", 3, "limits.reserve stop state", "WORKING", "WORKING", 0, 0),
            ("store.reserve_spend", 1, "limits.reserve the worst case", "WORKING", "WORKING", 0, 0),
            ("llm.chat", 1, "470 the model call", "WORKING", "WORKING", 0, 1),
            ("store.settle_spend", 1, "limits.settle the real cost", "WORKING", "WORKING", 1, 1),
        )
        if RESERVES
        else (
            ("llm.chat", 1, "470 the model call", "WORKING", "WORKING", 0, 1),
            ("store.add_spend", 1, "485 via limits.py:18", "WORKING", "WORKING", 1, 1),
            ("store.add_cost", 1, "486", "WORKING", "WORKING", 1, 1),
        )
    ),
    ("loop.get_run", 2, "330 via 496, 616", "WORKING", "WORKING", 1, 1),
    ("store.transition", 2, "331 WORKING to NO_ACTION (final)", "WORKING", FINAL, 1, 1),
    ("audit.write_outcome", 3, "332 state NO_ACTION", FINAL, FINAL, 1, 1),
    ("audit.write_outcome", 4, "628 abstain card posted", FINAL, FINAL, 1, 1),
)


@dataclass(frozen=True)
class Point:
    """One row of the matrix. `ack`, `row` and `calls` list what is ALLOWED: more than one value
    only where two threads race (the request thread reads while the loop thread writes)."""

    id: str
    point: str
    nth: int
    moment: str  # the named moment of the backlog item this point belongs to
    where: str
    ack: tuple[int | None, ...]  # what the client may have got before the kill (None: no answer)
    row: tuple[str | None, ...]  # the run row right after the kill
    calls: tuple[int, ...]  # model calls in total, over kill, restart, tick and retry
    thread: str  # which thread reaches the point: "request" or "loop"
    slow_create_s: float = 0.0  # child only: `create_run` waits this long first (a slow database)
    llm_delay_s: float = 0.0  # child only: the model double takes this long


def _ack_for(row: str | None) -> tuple[int | None, ...]:
    """Invariant 7: no 2xx without a row. With a row the request thread may or may not have read it
    before the kill; a row that is final may have been read as 200."""
    if row is None:
        return (None,)
    return (None, 202) if row in IN_PROGRESS else (None, 202, 200)


def _handle_points() -> list[Point]:
    out = []
    for n, (method, nth, where, before, after, calls_before, calls_after) in enumerate(
        HANDLE_STEPS, start=1
    ):
        for edge, row, made in (("before", before, calls_before), ("after", after, calls_after)):
            # No row: the retry is accepted as new and runs once. A row: nothing runs again.
            total = 1 if row is None else made
            moment = "after submit" if method == "store.create_run" else "during handle"
            out.append(
                Point(
                    id=f"h{n:02d}-{method}-{nth}-{edge}",
                    point=f"{method}:{edge}",
                    nth=nth,
                    moment=moment,
                    where=f"agent_loop.py:{where}",
                    ack=_ack_for(row),
                    row=(row,),
                    calls=(total,),
                    thread="loop",
                )
            )
    return out


# The request thread (`Runner.start`). `store.get_run:after` fires only when the read RETURNED a
# row (crash.py:165-169: a NotFound skips the `:after` hit), so its first firing is the first read
# that found the row, before the answer is written.
RUNNER_POINT_LIST: tuple[Point, ...] = (
    Point(
        id="r1-store.get_run-1-before",
        point="store.get_run:before",
        nth=1,
        moment="after verify",
        where="worker.py:127 (first read, before any store call of the request)",
        ack=(None,),
        row=(None,),
        calls=(1,),
        thread="request",
    ),
    Point(
        id="r2-store.get_run-2-before-slow-create",
        point="store.get_run:before",
        nth=2,
        moment="after submit",
        where="worker.py:139 (first poll after _submit; the loop has not written the row yet)",
        ack=(None,),
        row=(None,),
        calls=(1,),
        thread="request",
        slow_create_s=1.0,
    ),
    Point(
        id="r3-store.get_run-4-before-slow-create",
        point="store.get_run:before",
        nth=4,
        moment="after submit",
        where="worker.py:139 (a later poll, still no row)",
        ack=(None,),
        row=(None,),
        calls=(1,),
        thread="request",
        slow_create_s=1.0,
    ),
    Point(
        id="r4-store.get_run-2-before-racing",
        point="store.get_run:before",
        nth=2,
        moment="after submit",
        where="worker.py:139 (first poll after _submit, racing the loop thread)",
        ack=(None,),
        row=(None, "RECEIVED", "WORKING"),
        calls=(0, 1),
        thread="request",
        llm_delay_s=1.0,
    ),
    Point(
        id="r5-store.get_run-1-after-first-hit",
        point="store.get_run:after",
        nth=1,
        moment="after row seen",
        where="worker.py:139-141 (the first read that found the row, before the answer)",
        ack=(None,),
        row=("RECEIVED", "WORKING"),
        calls=(0, 1),
        thread="request",
        llm_delay_s=1.0,
    ),
)

POINTS: tuple[Point, ...] = (*RUNNER_POINT_LIST[:1], *_handle_points(), *RUNNER_POINT_LIST[1:])

# Same-process raise mode kills one THREAD, not the process. That stands in for a kill only where
# nothing else is running: every loop-thread point (the request thread then only reads the row) and
# the very first read of the request thread (no loop started yet). At the other request-thread
# points the loop thread would run on to its end, which a real kill never allows.
MEMORY_POINTS: tuple[Point, ...] = tuple(
    p for p in POINTS if p.thread == "loop" or p.id.startswith("r1-")
)


def money_at_kill(point: Point) -> set[tuple[int, int]]:
    """(reservations booked, settled) at the kill, from the table `HANDLE_STEPS` (NOT from a run): the
    store calls `reserve_spend` and `settle_spend` complete before their `:after` point and not before
    their `:before` point. The request-thread points: r1-r3 come before any reserve; r4 and r5 race the
    loop thread, which may or may not have reserved yet (the model double waits 1 s, so never settled)."""
    if point.id.startswith("h"):
        number, edge = int(point.id[1:3]), point.point.rpartition(":")[2]
        return {calls_done([step[0] for step in HANDLE_STEPS], number, edge)}
    return {(0, 0), (1, 0)} if point.id[:2] in ("r4", "r5") else {(0, 0)}


def _after_tick(row: str | None) -> tuple[str, str | None] | None:
    """(state, reason) after restart and tick: a cut-off run goes to a person, a final one stays."""
    if row is None:
        return None
    return ("NEEDS_PERSON", "interrupted") if row in IN_PROGRESS else (row, None)


def _params(points: tuple[Point, ...]) -> list:
    return [pytest.param(p, id=p.id) for p in points]


def _observe(store: str, point: Point, **seen: object) -> None:
    path = os.environ.get(OBSERVED_ENV)
    if path:
        with Path(path).open("a", encoding="utf-8") as out:
            out.write(json.dumps({"store": store, "id": point.id, **seen}) + "\n")


def test_the_table_covers_every_wrapped_call_once():
    """The table itself: 19 calls of `handle`, each before and after, plus 5 request-thread
    points; unique ids; every point names a wrapped method; the four named moments all appear."""
    assert len(HANDLE_STEPS) == (20 if RESERVES else 19) and len(POINTS) == 2 * len(HANDLE_STEPS) + 5
    assert len({p.id for p in POINTS}) == len(POINTS)
    assert len({(p.point, p.nth, p.slow_create_s, p.llm_delay_s) for p in POINTS}) == len(POINTS)
    wrapped = {f"store.{m}" for m in (*STORE_POINTS, *LIMITS_POINTS, *RUNNER_POINTS)}
    wrapped |= {"loop.get_run", "audit.write_outcome", "llm.chat"}
    assert {p.point.partition(":")[0] for p in POINTS} == wrapped
    assert {p.moment for p in POINTS} == {
        "after verify",
        "after submit",
        "after row seen",
        "during handle",
    }
    assert all(max(p.calls) <= 1 for p in POINTS)
    assert all(None in p.ack for p in POINTS)  # no point PROMISES an answer before the kill
    assert all(p.ack == (None,) for p in POINTS if p.row == (None,) or p.thread == "request")


def test_reserves_is_what_the_loop_really_does(tmp_path):
    """RESERVES picks the crash table. One full request through the real loop (memory store): the number of
    `store.reserve_spend` calls must be 1 exactly when RESERVES is True, else 0. A table for the wrong booking
    would otherwise run with crash points the child never reaches."""
    seen: list[str] = []

    class Spy:
        def __init__(self, target):
            self._target = target

        def reserve_spend(self, *args, **kwargs):
            seen.append("reserve_spend")
            return self._target.reserve_spend(*args, **kwargs)

        def __getattr__(self, attr):
            return getattr(self._target, attr)

    store = MemoryStore()
    config_dir = k5_cfg(tmp_path / "w")
    runtime, _cards = build_runtime(config_dir, CountingLLM(tmp_path / "calls", 0.0), store=store)
    runtime.limits.store = Spy(store)
    wsgi, runner = worker.make_app(make_trigger_app(runtime, store, ONE))
    try:
        status, data = _wsgi_post(wsgi, wire_body(KEY, DOCUMENT))
        assert status in OK, (status, data)
        assert _memory_settled(store, _run_id(SENDER, KEY)) == FINAL
    finally:
        runner.close()
    assert seen == (["reserve_spend"] if RESERVES else []), (
        f"RESERVES={RESERVES} but the loop made {len(seen)} reserve_spend call(s)"
    )


# --- wiring shared by the child and the memory run ---------------------------------------------------


class _SlowCreate:
    """A store whose `create_run` waits first; everything else is the target's."""

    def __init__(self, target: object, delay_s: float) -> None:
        self._target, self._delay_s = target, delay_s

    def create_run(self, run):
        time.sleep(self._delay_s)
        return self._target.create_run(run)

    def __getattr__(self, attr: str):
        if attr in ("_target", "_delay_s"):
            raise AttributeError(attr)
        return getattr(self._target, attr)


def wire(points: CrashPoints, runtime, plain, slow_create_s: float = 0.0):
    """Put ONE CrashPoints object around everything the runtime was built with (the runtime keeps
    its own references, so this runs AFTER the build). Returns the store for the Runner."""
    inner = _SlowCreate(plain, slow_create_s) if slow_create_s else plain
    runtime.store = points.wrap(points.wrap(inner, "store", STORE_POINTS), "loop", ("get_run",))
    runtime.limits.store = points.wrap(plain, "store", LIMITS_POINTS)
    runtime.audit = points.wrap(runtime.audit, "audit", ("write_outcome",))
    runtime.llm = points.wrap(runtime.llm, "llm", ("chat",))
    return points.wrap(plain, "store", RUNNER_POINTS)


# --- PostgreSQL: a child process killed at each point ------------------------------------------------


class MatrixChild(Child):
    """A child that runs THIS module as its script (same output files, port line and kill as the
    launcher's `Child`)."""

    def __init__(self, work_dir: Path, config_dir: Path, *args: str, dsn: str) -> None:
        work_dir.mkdir(parents=True, exist_ok=True)
        self._out, self._err = work_dir / "stdout.txt", work_dir / "stderr.txt"
        env = {**os.environ, SECRETS_ENV: json.dumps(ONE), DSN_ENV: dsn}
        command = [
            sys.executable,
            "-m",
            "tests.triggers.test_t5_crash_matrix",
            "--config-dir",
            str(config_dir),
            *args,
        ]
        with self._out.open("wb") as out, self._err.open("wb") as err:
            self.proc = subprocess.Popen(  # noqa: S603 - this interpreter, this repo's module, no shell
                command, cwd=ROOT, env=env, stdout=out, stderr=err, stdin=subprocess.DEVNULL
            )
        self.port = 0


def _matrix_child(tmp_path: Path, dsn: str, point: Point | None = None) -> MatrixChild:
    """The worker "w" on the schema of `dsn`; a second call is a restart (same config, flag and
    calls file). The delays of `point` apply to the child that is killed only."""
    home = tmp_path / "w"
    if not (home / "config").exists():
        k5_cfg(home)
    args = ["--flag", str(home / "flag"), "--calls-file", str(home / "calls")]
    if point is not None:
        args += ["--slow-create-s", str(point.slow_create_s)]
        args += ["--llm-delay-s", str(point.llm_delay_s)]
    runs = len(list(home.glob("run-*")))
    tagged = make_conninfo(dsn, application_name=_tag(tmp_path))
    return MatrixChild(home / f"run-{runs}", home / "config", *args, dsn=tagged)


def _tag(tmp_path: Path) -> str:
    """The application_name of this test's children on the database server (unique per test)."""
    return "cm-" + hashlib.sha256(str(tmp_path).encode()).hexdigest()[:24]


def _backends_gone(dsn: str, tag: str) -> None:
    """Wait until the server holds no session of the killed child. A kill does not take back a
    statement the child had already sent: the server finishes it, so the row may appear a moment
    AFTER the process died. Only then is "the row after the kill" a stable reading."""
    deadline = time.monotonic() + FIRE_WAIT_S
    with psycopg.connect(dsn, autocommit=True) as db:
        while True:
            left = db.execute(
                "SELECT count(*) FROM pg_stat_activity WHERE application_name = %s", (tag,)
            ).fetchone()[0]
            if not left:
                return
            assert time.monotonic() < deadline, f"{left} session(s) of the killed child remain"
            time.sleep(0.01)


@pytest.fixture
def dsn():
    """A DSN on a fresh migrated schema; the schema is dropped afterwards."""
    yield from pg_schema()


@pytest.mark.parametrize("point", _params(POINTS))
def test_pg_kill_at_point(point: Point, dsn, tmp_path):
    """Kill the worker process at `point` on PostgreSQL, restart it, run the tick's stuck step a
    day later, send the same request signed again. Checked for every point: the client got a 2xx
    only if a matching row exists; at most one row; after the tick no row is RECEIVED or WORKING;
    the retry is never a 5xx other than 503 (and here it is the 200 or 2xx of the table); at most
    one model call in total. Checked per point: the row at the kill and the number of calls."""
    body, run_id = wire_body(KEY, DOCUMENT), _run_id(SENDER, KEY)
    identity = (run_id, AGENT, PRINCIPAL, _ref(SENDER, KEY, DOCUMENT))
    home = tmp_path / "w"
    flag = _arm(tmp_path, "w", point.point, point.nth)
    with _matrix_child(tmp_path, dsn, point) as child:
        ack_status, ack_data = signed_post(child.port, body, SECRET)
        _killed(child)
    assert not flag.exists()
    _backends_gone(dsn, _tag(tmp_path))

    rows = _rows(dsn)
    assert len(rows) <= 1
    row = rows[0][4] if rows else None
    calls_at_kill = _calls(home / "calls")
    assert ack_status in point.ack, (ack_status, ack_data)
    if ack_status in OK:  # an acknowledged request has its row (invariant 7)
        assert rows and rows[0][:4] == identity
        assert json.loads(ack_data)["run_id"] == run_id
    assert row in point.row, rows
    assert all(found[:4] == identity for found in rows)
    money_kill = (0, 0)
    if RESERVES:  # the money at the kill: one open hold between reserve and settle, none before, settled after
        money_kill = assert_kill_state(*pg_money(dsn, run_id), money_at_kill(point), point.id)
        assert row is not None or money_kill == (0, 0)  # no run row, no hold

    expected = _after_tick(row)
    with _matrix_child(tmp_path, dsn) as child:
        assert _stuck_tick(tmp_path, "w", dsn) == 0
        after = _rows(dsn)
        assert after == ([] if expected is None else [(*identity, *expected)])
        retry_status, retry_data = signed_post(child.port, body, SECRET)
        if expected is None:  # no row: accepted as a new request, runs once
            assert retry_status in OK, (retry_status, retry_data)
            assert json.loads(retry_data)["run_id"] == run_id
            assert _settled(dsn, run_id) == (*identity, FINAL, None)
        else:  # a row: answered from it, nothing runs
            assert retry_status == 200, (retry_status, retry_data)
            assert json.loads(retry_data) == {"run_id": run_id, "state": expected[0]}
            assert _rows(dsn) == after
        assert child.proc.poll() is None  # the restarted worker did not die

    end = _rows(dsn)
    assert len(end) == 1 and end[0][:4] == identity and end[0][4] not in IN_PROGRESS
    if RESERVES:  # an open hold stays open (no expiry step here); a retry never books a second hold
        assert_end_state(*pg_money(dsn, run_id), money_kill, row, 1, point.id)
    total = _calls(home / "calls")
    _observe(
        "postgres",
        point,
        ack=ack_status,
        row=row,
        calls_at_kill=calls_at_kill,
        after=None if expected is None else list(expected),
        retry=retry_status,
        end=list(end[0][4:]),
        calls=total,
    )
    assert total <= 1  # never two model calls for one key
    assert total in point.calls, (total, calls_at_kill)


# --- memory store: the same table, same process, mode "raise" ----------------------------------------


def _wsgi_post(wsgi, body: bytes) -> tuple[int | None, bytes]:
    """One signed request through the WSGI callable in this process. (None, b"") when the
    request thread itself hit the crash point."""
    seen: dict = {}
    environ: dict = {}
    setup_testing_defaults(environ)
    environ.update(
        {
            "REQUEST_METHOD": "POST",
            "PATH_INFO": PATH,
            "CONTENT_LENGTH": str(len(body)),
            "wsgi.input": io.BytesIO(body),
        }
    )
    for name, value in hmac_v0.sign(body, int(time.time()), SECRET, PREFIX).items():
        environ["HTTP_" + name.upper().replace("-", "_")] = value

    def start_response(status, headers, exc_info=None):
        seen["status"] = int(status.split()[0])

    try:
        data = b"".join(wsgi(environ, start_response))
    except SimulatedCrash:
        return None, b""
    return seen["status"], data


def _memory_rows(store) -> list[tuple]:
    return sorted(
        (
            run.run_id,
            run.agent_id,
            run.principal_id,
            run.trigger_ref,
            RunState(run.state).value,
            run.reason_code,
        )
        for run in _all_runs(store)
    )


def _memory_tick(config_dir: Path, store, audit_dir: Path) -> int:
    cfg = load_config(config_dir)
    app = SimpleNamespace(
        config=cfg, registry=load_registry(cfg), store=store, audit=LocalDirSink(audit_dir)
    )
    steps = [step for step in tick.STEPS if step.name == "stuck"]
    assert len(steps) == 1
    return tick.run_tick(app, now=now() + timedelta(days=1), steps=steps)


def _memory_settled(store, run_id: str) -> str:
    deadline = time.monotonic() + FIRE_WAIT_S
    while True:
        try:
            state = RunState(store.get_run(run_id).state).value
        except NotFound:
            state = None
        if state is not None and state not in IN_PROGRESS:
            return state
        assert time.monotonic() < deadline, f"run did not end: {state}"
        time.sleep(0.01)


def _memory_ack(point: Point) -> tuple[int | None, ...]:
    """Raise mode keeps the request thread alive when the LOOP thread dies, so it always answers:
    503 when the loop ended with no row (worker.py:143-144), else from the row."""
    if point.thread == "request":
        return (None,)
    if point.row == (None,):
        return (503,)
    return tuple(status for status in point.ack if status is not None)


@pytest.mark.parametrize("point", _params(MEMORY_POINTS))
def test_memory_raise_at_point(point: Point, tmp_path):
    """The thread that reaches `point` dies there (same process, memory store); then a new Runtime
    and Runner on the same store ("restart"), the stuck step a day later, the same request signed
    again. Same checks as on PostgreSQL."""
    body, run_id = wire_body(KEY, DOCUMENT), _run_id(SENDER, KEY)
    identity = (run_id, AGENT, PRINCIPAL, _ref(SENDER, KEY, DOCUMENT))
    config_dir, calls_file, store = k5_cfg(tmp_path / "w"), tmp_path / "calls", MemoryStore()

    with CrashPoints() as points:
        runtime, _cards = build_runtime(config_dir, CountingLLM(calls_file, 0.0), store=store)
        for_runner = wire(points, runtime, store)
        wsgi, runner = worker.make_app(make_trigger_app(runtime, for_runner, ONE))
        try:
            points.arm(point.point, nth=point.nth)
            ack_status, ack_data = _wsgi_post(wsgi, body)
            deadline = time.monotonic() + FIRE_WAIT_S
            while not points.fired and time.monotonic() < deadline:
                time.sleep(0.005)
        finally:
            runner.close()
        assert points.fired == (point.point,)

    rows = _memory_rows(store)
    assert len(rows) <= 1
    row = rows[0][4] if rows else None
    assert ack_status in _memory_ack(point), (ack_status, ack_data)
    if ack_status in OK:
        assert rows and rows[0][:4] == identity
        assert json.loads(ack_data)["run_id"] == run_id
    assert row in point.row, rows
    money_kill = (0, 0)
    if RESERVES:
        money_kill = assert_kill_state(*memory_money(store, run_id), money_at_kill(point), point.id)
        assert row is not None or money_kill == (0, 0)

    expected = _after_tick(row)
    runtime, _cards = build_runtime(config_dir, CountingLLM(calls_file, 0.0), store=store)
    wsgi, runner = worker.make_app(make_trigger_app(runtime, store, ONE))
    try:
        assert _memory_tick(config_dir, store, tmp_path / "tick-audit") == 0
        after = _memory_rows(store)
        assert after == ([] if expected is None else [(*identity, *expected)])
        retry_status, retry_data = _wsgi_post(wsgi, body)
        if expected is None:
            assert retry_status in OK, (retry_status, retry_data)
            assert json.loads(retry_data)["run_id"] == run_id
            assert _memory_settled(store, run_id) == FINAL
        else:
            assert retry_status == 200, (retry_status, retry_data)
            assert json.loads(retry_data) == {"run_id": run_id, "state": expected[0]}
            assert _memory_rows(store) == after
    finally:
        runner.close()

    end = _memory_rows(store)
    assert len(end) == 1 and end[0][:4] == identity and end[0][4] not in IN_PROGRESS
    if RESERVES:
        assert_end_state(*memory_money(store, run_id), money_kill, row, 1, point.id)
    total = _calls(calls_file)
    _observe(
        "memory",
        point,
        ack=ack_status,
        row=row,
        after=None if expected is None else list(expected),
        retry=retry_status,
        end=list(end[0][4:]),
        calls=total,
    )
    assert total <= 1
    assert total in point.calls


# --- the child script ---------------------------------------------------------------------------------


def child_main(argv: list[str] | None = None) -> int:
    """A trigger worker on PostgreSQL with every collaborator of the runtime behind ONE
    CrashPoints object in mode "exit". Prints `port <n>` once the socket is bound."""
    from hadavin_sdk.store.postgres import PostgresStore, connect

    parser = argparse.ArgumentParser(prog="python -m tests.triggers.test_t5_crash_matrix")
    parser.add_argument("--config-dir", type=Path, required=True)
    parser.add_argument("--flag", type=Path, required=True)
    parser.add_argument("--calls-file", type=Path, required=True)
    parser.add_argument("--slow-create-s", type=float, default=0.0)
    parser.add_argument("--llm-delay-s", type=float, default=0.0)
    args = parser.parse_args(argv)

    secrets = json.loads(os.environ[SECRETS_ENV])
    install_pg_test_seeding()
    plain = PostgresStore(connect(os.environ[DSN_ENV]))
    llm = CountingLLM(args.calls_file, args.llm_delay_s)
    runtime, _cards = build_runtime(args.config_dir, llm, store=plain)
    points = CrashPoints(mode="exit", flag_path=args.flag)
    for_runner = wire(points, runtime, plain, args.slow_create_s)
    wsgi, runner = worker.make_app(make_trigger_app(runtime, for_runner, secrets))
    server = worker.make_server(HOST, 0, wsgi, worker.ACK_WAIT_S + worker.SOCKET_SLACK_S)
    print(f"port {server.server_port}", flush=True)
    code = worker.serve(server, runner)
    print("stopped", flush=True)
    return code


if __name__ == "__main__":
    sys.exit(child_main())
