"""Crash matrix part 2 for the signed trigger endpoint and its worker (ticket D, step D).

Part 1 (test_t5_crash_matrix.py) killed the worker on ONE path of the agent loop: the model says
"nothing to do". This file kills it on three paths that part 1 did not cover:

- `read`: the model reads one log through a read tool, then says "nothing to do" (NO_ACTION).
- `propose`: the model reads one log, then proposes an action at level "suggest". The gate asks for
  approval, the approval request is saved and sent, the run stays WAITING_FOR_APPROVAL (open).
- `approve`: a person approved the request of the `propose` path (the decision is recorded). The
  tick's `reconcile` step then runs the action through `Runtime.on_decided -> execute -> verify` with
  a fake executor. The kill is made inside that tick (a child process), not inside the worker.

Every collaborator of the runtime sits behind ONE CrashPoints object, wrapped after the runtime was
built (the runtime keeps its own store reference): the runtime's store, the store handed to the
Runner, the limits' store, the audit sink, the model double, the read tool box, the fake executor
and the fake channel. Points are `<name>.<method>:before` and `:after`, with `nth` for repeated
methods. Two runs of the same tables:

- PostgreSQL (needs HADAVIN_TEST_PG_DSN): a child process is killed with `os._exit` at the point, a
  second child is started, then (a) the SAME request is signed again and sent BEFORE any tick, (b)
  the real tick steps `sweep`, `reconcile` and `stuck` run with a later clock, (c) the request is sent
  once more.
- memory store, mode "raise": the thread that reaches the point dies there; same sequence.

The expectation tables below were written from the code BEFORE the first run. A row says what the
store, the model double, the read tool, the fake executor and the fake channel hold right AFTER each
call; the state BEFORE a call is the state after the previous one. A trace test replays each path
without a crash and compares the sequence of calls with the table, so a wrong table fails fast.

Pure reads (`get_kill_switch`, `spend_totals`, `get_run` of the loop) change nothing, so the `:after`
point of a repeated read is the same moment as the `:before` of the next call: only the first read
of each kind has an `:after` point.

With CRASH_MATRIX_OBSERVED set to a file path, every case appends one JSON line with what it saw.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from hadavin_sdk.approvals import FakeChannel
from hadavin_sdk.approvals.cards import Delivery
from hadavin_sdk.config import load_config
from hadavin_sdk.models import ApprovalDecision, Reply, RunResult, RunState, ToolCall, now
from hadavin_sdk.registry import load_registry
from hadavin_sdk.runtime import tick
from hadavin_sdk.store import MemoryStore
from hadavin_sdk.testing.crash import CrashPoints, SimulatedCrash
from hadavin_sdk.triggers import worker
from tests.contracts.kinds.store_postgres import pg_schema
from tests.fixtures import k5_tools
from tests.k5_support import build_runtime, edit_config, k5_cfg
from tests.triggers.crash_launcher import (
    AGENT,
    DSN_ENV,
    HOST,
    PRINCIPAL,
    RESERVES,
    ROOT,
    SECRETS_ENV,
    Child,
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
from tests.triggers.test_t5_crash_matrix import (
    FIRE_WAIT_S,
    SECRET,  # the fake secret of part 1 (`_wsgi_post` signs with it)
    _backends_gone,
    _memory_rows,
    _tag,
    _wsgi_post,
)
from tests.triggers.test_t5_postgres import DOCUMENT, _arm, _ref, _rows, _run_id

if os.environ.get("HADAVIN_TEST_PG_DSN"):  # set: the driver must be there, never a silent skip
    from psycopg.conninfo import make_conninfo

SENDER, KEY = "sender-a", "key-1"
ONE = {SENDER: SECRET}
OK = (200, 202)
IN_PROGRESS = ("RECEIVED", "WORKING")
OBSERVED_ENV = "CRASH_MATRIX_OBSERVED"
KILL_WAIT_S = 20.0
TICK_LATER = timedelta(hours=1)  # past the stuck floor (420 s), before the approval step ends (4 h)
TICK_STEPS = ("sweep", "reconcile", "stuck")
LOG_TEXT = "ERROR upstream 10.0.0.5 refused; rollout revision 17 failed"
APPROVAL_SIGNING = "sig" + "-p2-test"  # built from parts

STORE_WRITES = (
    "create_run",
    "transition",
    "touch",
    "put_redaction_map",
    *(() if RESERVES else ("add_cost",)),  # with reserve/settle the settle books the run cost
    "add_tool_call",
    "save_plan",
    "save_gate_decision",
    "save_approval_request",
    "update_approval_request",
)
LIMITS_READS = (
    ("get_kill_switch", "spend_totals", "reserve_spend", "settle_spend")
    if RESERVES
    else ("get_kill_switch", "spend_totals", "add_spend")
)
PURE_READS = ("store.get_kill_switch", "store.spend_totals", "loop.get_run")

# --- the expectation tables (written before the first run) ------------------------------------------
#
# One row per call that the path makes on a wrapped collaborator, in order (agent_loop.py line
# numbers). Columns: call, where, and the state right AFTER the call:
#   row    the run row's state (None: no row)
#   llm    model calls made so far (the double counts a call when `chat` is entered)
#   tool   read-tool calls made so far (counted when the tool box is entered)
#   req    the approval request: None, "unsent" (saved, `sent_at` empty), "sent", "approved"
#   cards  messages posted to the channel for this run (approval sends and abstain cards)
#   acts   actions executed by the fake executor
# `store.*` is the runtime's store (writes), the limits' store (reads) or the Runner's store; `loop.get_run`
# is the same `get_run` as the runtime calls it.
Row = tuple[str, str, str | None, int, int, str | None, int, int]

W, R = "WORKING", "RECEIVED"


def _reserve(llm: int, tool: int) -> tuple[Row, ...]:
    """Where the live loop reserves the worst case before a model call (core-b: limits.reserve reads
    the stop state, then `reserve_spend`). Older loops book nothing before the call."""
    if not RESERVES:
        return ()
    return (
        ("store.get_kill_switch", "limits.reserve stop state", W, llm, tool, None, 0, 0),
        ("store.reserve_spend", "limits.reserve the worst case", W, llm, tool, None, 0, 0),
    )


def _book(llm: int, tool: int) -> tuple[Row, ...]:
    """The booking after the model call: `settle_spend` (one store call, books the run cost too) with
    reserve/settle; `add_spend` and `add_cost` before."""
    if RESERVES:
        return (("store.settle_spend", "limits.settle the real cost", W, llm, tool, None, 0, 0),)
    return (
        ("store.add_spend", "485 via limits.py:18", W, llm, tool, None, 0, 0),
        ("store.add_cost", "486", W, llm, tool, None, 0, 0),
    )

_COMMON: tuple[Row, ...] = (
    ("store.create_run", "389", R, 0, 0, None, 0, 0),
    ("audit.write_outcome", "394 run received", R, 0, 0, None, 0, 0),
    ("loop.get_run", "330 via 395", R, 0, 0, None, 0, 0),
    ("store.transition", "331 RECEIVED to WORKING", W, 0, 0, None, 0, 0),
    ("audit.write_outcome", "332 state WORKING", W, 0, 0, None, 0, 0),
    ("store.get_kill_switch", "404 via limits.py:21", W, 0, 0, None, 0, 0),
    ("store.spend_totals", "404 via limits.py:23", W, 0, 0, None, 0, 0),
    ("store.put_redaction_map", "408", W, 0, 0, None, 0, 0),
    ("store.put_redaction_map", "424", W, 0, 0, None, 0, 0),
    ("store.get_kill_switch", "466 step 1", W, 0, 0, None, 0, 0),
    ("store.spend_totals", "466 step 1", W, 0, 0, None, 0, 0),
    ("store.touch", "468 heartbeat", W, 0, 0, None, 0, 0),
    *_reserve(0, 0),
    ("llm.chat", "470 model call 1 (a read-tool call)", W, 1, 0, None, 0, 0),
    *_book(1, 0),
    ("store.get_kill_switch", "505 before the tool", W, 1, 0, None, 0, 0),
    ("store.spend_totals", "505 before the tool", W, 1, 0, None, 0, 0),
    ("tool.invoke", "513 the read tool", W, 1, 1, None, 0, 0),
    ("store.put_redaction_map", "520 after the tool", W, 1, 1, None, 0, 0),
    ("store.put_redaction_map", "543 with the record", W, 1, 1, None, 0, 0),
    ("store.add_tool_call", "544 evidence stored", W, 1, 1, None, 0, 0),
    ("audit.write_outcome", "554 tool note", W, 1, 1, None, 0, 0),
    ("store.get_kill_switch", "466 step 2", W, 1, 1, None, 0, 0),
    ("store.spend_totals", "466 step 2", W, 1, 1, None, 0, 0),
    ("store.touch", "468 heartbeat 2", W, 1, 1, None, 0, 0),
)
READ_ROWS: tuple[Row, ...] = (
    *_COMMON,
    *_reserve(1, 1),
    ("llm.chat", "470 model call 2 (nothing to do)", W, 2, 1, None, 0, 0),
    *_book(2, 1),
    ("loop.get_run", "330 via 496", W, 2, 1, None, 0, 0),
    ("store.transition", "331 WORKING to NO_ACTION (final)", "NO_ACTION", 2, 1, None, 0, 0),
    ("audit.write_outcome", "332 state NO_ACTION", "NO_ACTION", 2, 1, None, 0, 0),
    ("chan.post_card", "626 abstain card posted", "NO_ACTION", 2, 1, None, 1, 0),
    ("audit.write_outcome", "628 abstain card audited", "NO_ACTION", 2, 1, None, 1, 0),
)
_P, _WA = "PLAN_READY", "WAITING_FOR_APPROVAL"
PROPOSE_ROWS: tuple[Row, ...] = (
    *_COMMON,
    *_reserve(1, 1),
    ("llm.chat", "470 model call 2 (a proposal)", W, 2, 1, None, 0, 0),
    *_book(2, 1),
    ("store.put_redaction_map", "694 proposal check", W, 2, 1, None, 0, 0),
    ("audit.write_outcome", "705 cited evidence", W, 2, 1, None, 0, 0),
    ("store.save_plan", "713", W, 2, 1, None, 0, 0),
    ("loop.get_run", "330 via 714", W, 2, 1, None, 0, 0),
    ("store.transition", "331 WORKING to PLAN_READY", _P, 2, 1, None, 0, 0),
    ("audit.write_outcome", "332 state PLAN_READY", _P, 2, 1, None, 0, 0),
    ("store.get_kill_switch", "716 gate", _P, 2, 1, None, 0, 0),
    ("store.spend_totals", "716 gate", _P, 2, 1, None, 0, 0),
    ("audit.write_intent", "733 gate decision", _P, 2, 1, None, 0, 0),
    ("store.save_gate_decision", "747", _P, 2, 1, None, 0, 0),
    ("loop.get_run", "330 via 762", _P, 2, 1, None, 0, 0),
    ("store.transition", "331 PLAN_READY to WAITING_FOR_APPROVAL", _WA, 2, 1, None, 0, 0),
    ("audit.write_outcome", "332 state WAITING", _WA, 2, 1, None, 0, 0),
    ("store.save_approval_request", "requests.py:107", _WA, 2, 1, "unsent", 0, 0),
    ("chan.send", "requests.py:116 the approval card", _WA, 2, 1, "unsent", 1, 0),
    ("store.update_approval_request", "requests.py:126 sent_at", _WA, 2, 1, "sent", 1, 0),
    ("audit.write_outcome", "requests.py:109 request audited", _WA, 2, 1, "sent", 1, 0),
)
_EX, _VF, _OK = "EXECUTING", "VERIFYING", "SUCCEEDED"
_Q = "approved"
# `approve` starts where `propose` ends (row waiting, 2 model calls, 1 tool call, request approved,
# 1 card) and covers the tick that runs the decision.
APPROVE_START = (_WA, 2, 1, _Q, 1, 0)
APPROVE_ROWS: tuple[Row, ...] = (
    ("chan.update", "tick.py:94 message updated", _WA, 2, 1, _Q, 1, 0),
    ("loop.get_run", "801 on_decided", _WA, 2, 1, _Q, 1, 0),
    ("loop.get_run", "807 execute", _WA, 2, 1, _Q, 1, 0),
    ("store.get_kill_switch", "790 recheck", _WA, 2, 1, _Q, 1, 0),
    ("store.spend_totals", "790 recheck", _WA, 2, 1, _Q, 1, 0),
    ("audit.write_intent", "821 execute intent", _WA, 2, 1, _Q, 1, 0),
    ("loop.get_run", "330 via 877", _WA, 2, 1, _Q, 1, 0),
    ("store.transition", "331 WAITING to EXECUTING", _EX, 2, 1, _Q, 1, 0),
    ("audit.write_outcome", "332 state EXECUTING", _EX, 2, 1, _Q, 1, 0),
    ("exec.execute", "886 the side effect", _EX, 2, 1, _Q, 1, 1),
    ("audit.write_outcome", "889 action result", _EX, 2, 1, _Q, 1, 1),
    ("loop.get_run", "330 via 899", _EX, 2, 1, _Q, 1, 1),
    ("store.transition", "331 EXECUTING to VERIFYING", _VF, 2, 1, _Q, 1, 1),
    ("audit.write_outcome", "332 state VERIFYING", _VF, 2, 1, _Q, 1, 1),
    ("exec.verify", "901 the check", _VF, 2, 1, _Q, 1, 1),
    ("loop.get_run", "330 via 906", _VF, 2, 1, _Q, 1, 1),
    ("store.transition", "331 VERIFYING to SUCCEEDED (final)", _OK, 2, 1, _Q, 1, 1),
    ("audit.write_outcome", "332 state SUCCEEDED", _OK, 2, 1, _Q, 1, 1),
)
READ_SCRIPT = ({"tool": "app"}, {"noaction": True})
PROPOSE_SCRIPT = ({"tool": "app"}, {"propose": {"title": "Draft one", "amount": "12.50"}})
ACTION = "create_draft_record"  # an http contract, reversible with a rollback: needs approval


@dataclass(frozen=True)
class Path_:
    """One path: its config level, the model's script, its table and where a fresh run ends."""

    name: str
    suggest: bool  # the action runs at level "suggest" (else "shadow")
    script: tuple[dict, ...]
    rows: tuple[Row, ...]
    start: tuple  # the state before the first row
    final: str  # where a whole fresh run ends (state)
    fresh_cards: int  # cards a whole fresh run posts
    via: str  # "worker": the kill is in the worker's run; "tick": the kill is in the tick


PATHS: dict[str, Path_] = {
    "read": Path_("read", False, READ_SCRIPT, READ_ROWS, (None, 0, 0, None, 0, 0), "NO_ACTION", 1, "worker"),
    "propose": Path_("propose", True, PROPOSE_SCRIPT, PROPOSE_ROWS, (None, 0, 0, None, 0, 0), _WA, 1, "worker"),
    "approve": Path_("approve", True, PROPOSE_SCRIPT, APPROVE_ROWS, APPROVE_START, _OK, 1, "tick"),
}  # fmt: skip


@dataclass(frozen=True)
class Point:
    """One kill point and what is expected right after the kill (the state of the table)."""

    id: str
    path: str
    point: str
    nth: int
    where: str
    row: str | None
    llm: int
    tool: int
    req: str | None
    cards: int
    acts: int


def _points(path: Path_) -> list[Point]:
    out, before, seen, reads = [], path.start, {}, set()
    for number, (call, where, *after) in enumerate(path.rows, start=1):
        seen[call] = seen.get(call, 0) + 1
        for edge, state in (("before", before), ("after", tuple(after))):
            if edge == "after" and call in PURE_READS:
                if call in reads:
                    continue
                reads.add(call)
            out.append(
                Point(
                    id=f"{path.name}{number:02d}-{call}-{seen[call]}-{edge}",
                    path=path.name,
                    point=f"{call}:{edge}",
                    nth=seen[call],
                    where=where,
                    row=state[0],
                    llm=state[1],
                    tool=state[2],
                    req=state[3],
                    cards=state[4],
                    acts=state[5],
                )
            )
        before = tuple(after)
    return out


ALL_POINTS: dict[str, list[Point]] = {name: _points(path) for name, path in PATHS.items()}


# Money at the start of a path (RESERVES): `approve` starts from a whole propose run (two model calls, each
# reserved and settled); the others start with nothing booked.
MONEY_START: dict[str, tuple[int, int]] = {"approve": (2, 2)}


def money_at_kill(point: Point) -> tuple[int, int]:
    """(reservations booked, settled) at the kill, from the TABLE of the path (not from a run): a
    `reserve_spend` / `settle_spend` row counts once its `:after` point is passed and not at its `:before`."""
    start = MONEY_START.get(point.path, (0, 0))
    number = int(point.id[len(point.path) : len(point.path) + 2])
    reserved, settled = calls_done(
        [row[0] for row in PATHS[point.path].rows], number, point.point.rpartition(":")[2]
    )
    return start[0] + reserved, start[1] + settled


def money_full(path: str) -> int:
    """Reservations of a whole run of the path: the start plus one per `reserve_spend` row."""
    return MONEY_START.get(path, (0, 0))[0] + sum(
        row[0] == "store.reserve_spend" for row in PATHS[path].rows
    )


def after_tick(path: str, row: str | None, req: str | None) -> tuple[str, str | None] | None:
    """(state, reason) after restart and tick, from the code of tick.py (STUCK, the orphan rule,
    `reconcile`) and of `Runtime.execute`: what the table says the run is, the tick makes of it."""
    if row is None:
        return None  # no row: the retry makes a fresh run (its end is `Path_.final`)
    if row in (*IN_PROGRESS, "PLAN_READY"):
        return "NEEDS_PERSON", "interrupted"
    if row == "WAITING_FOR_APPROVAL":
        if req == "approved":  # decided and recorded: `reconcile` runs it
            return "SUCCEEDED", None
        return (row, None) if req else ("NEEDS_PERSON", "approval_missing")
    if row == "EXECUTING":
        return "NEEDS_PERSON", "outcome_unknown"
    if row == "VERIFYING":
        return "NEEDS_PERSON", "verify_interrupted"
    return row, None


def expected_acts(path: str, point: Point) -> int:
    """Actions executed in total over kill, restart, tick and retry: none on the paths without an
    approval; on `approve` the tick runs a decided run that was not yet executing, once, and never
    runs one that had begun (EXECUTING and later go to a person)."""
    if path != "approve":
        return 0
    return 1 if point.row == "WAITING_FOR_APPROVAL" else point.acts


# --- shared wiring (child process and memory run) -----------------------------------------------------


class Files:
    """Counters that survive a kill: every double appends one line to a file."""

    def __init__(self, home: Path) -> None:
        home.mkdir(parents=True, exist_ok=True)
        self.calls, self.tools, self.acts, self.chan = (
            home / name for name in ("calls", "tools", "acts", "chan")
        )

    @staticmethod
    def lines(path: Path) -> list[str]:
        return path.read_text(encoding="utf-8").splitlines() if path.exists() else []

    def model_calls(self) -> int:
        return len(self.lines(self.calls))

    def tool_calls(self) -> list[str]:
        return self.lines(self.tools)

    def executed(self) -> list[dict]:
        return [json.loads(x) for x in self.lines(self.acts) if '"execute"' in x]

    def cards(self) -> int:
        return sum(1 for x in self.lines(self.chan) if x in ("send", "post"))


def _append(path: Path, line: str) -> None:
    with path.open("ab") as out:  # one write per line, appended
        out.write((line + "\n").encode("utf-8"))


class PathLLM:
    """A scripted model: the step follows from the messages, so a fresh run starts at step 1. A step
    is a read-tool call, a proposal (`create_draft_record`, citing the last tool result) or nothing."""

    def __init__(self, script: tuple[dict, ...], files: Files) -> None:
        self._steps, self._files, self._lock = script, files, threading.Lock()

    def chat(self, messages, *, system, route, tools=None, documents=None, output_schema=None):
        with self._lock:
            _append(self._files.calls, "chat")
        index = (len(messages) - 1) // 2
        step = self._steps[index] if index < len(self._steps) else {"noaction": True}
        if "tool" in step:
            call = ToolCall(name="read_logs", input={"name": step["tool"]})
            return Reply(text="reading", tool_calls=[call], model_id="fake-model")
        if "propose" in step:
            ids = re.findall(r"call_id=(\S+?)[ >]", json.dumps(messages))
            inputs = {**step["propose"], "evidence": ids[-1:]}
            call = ToolCall(name=ACTION, input=inputs)
            return Reply(text="A draft is needed.", tool_calls=[call], model_id="fake-model")
        return Reply(text="Nothing to do.", model_id="fake-model")


class CountingBox:
    """Stands in for the runtime's tool box: one line per call (name and arguments)."""

    def __init__(self, box: object, path: Path) -> None:
        self._box, self._path = box, path

    def invoke(self, name, args, mapping):
        _append(self._path, json.dumps({"tool": name, "args": args}, sort_keys=True))
        return self._box.invoke(name, args, mapping)

    def __getattr__(self, attr: str):
        if attr in ("_box", "_path"):
            raise AttributeError(attr)
        return getattr(self._box, attr)


class CountingExec:
    """A fake executor: one line per execution, with what the approval said."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def execute(self, plan, decision, approval, **kw):
        said = getattr(approval, "decision", None)
        _append(self._path, json.dumps({"act": "execute", "plan": plan.plan_id, "approval": said}))
        return RunResult(outcome="succeeded", external_ref="ext-1")

    def verify(self, plan, result):
        _append(self._path, json.dumps({"act": "verify"}))
        return True


class CountingChannel(FakeChannel):
    """The fake channel; each message is one line in a file."""

    def __init__(self, path: Path) -> None:
        super().__init__(APPROVAL_SIGNING)
        self._path = path

    def send(self, req, approver_ids):
        _append(self._path, "send")
        return super().send(req, approver_ids)

    def update(self, req):
        _append(self._path, "update")
        super().update(req)

    def post_card(self, card):
        _append(self._path, "post")
        return super().post_card(card)


def build_stack(config_dir: Path, store, files: Files, path: Path_, points=None):
    """A runtime with the doubles above, the real `Approvals`, and (with `points`) every
    collaborator behind ONE CrashPoints object. Built first, wrapped after: the runtime keeps its
    own references. Returns an object with `runtime`, `approvals` and `for_runner` (the Runner's)."""
    from hadavin_sdk.approvals.requests import Approvals

    k5_tools.RESULTS["app"] = LOG_TEXT
    runtime, _cards = build_runtime(config_dir, PathLLM(path.script, files), store=store)
    hooks = runtime.hooks
    hooks.toolbox = CountingBox(hooks.toolbox, files.tools)
    chan, ex = CountingChannel(files.chan), CountingExec(files.acts)
    for_runner = store
    if points is not None:
        runtime.store = points.wrap(points.wrap(store, "store", STORE_WRITES), "loop", ("get_run",))
        runtime.limits.store = points.wrap(store, "store", LIMITS_READS)
        runtime.audit = points.wrap(runtime.audit, "audit", ("write_outcome", "write_intent"))
        runtime.llm = points.wrap(runtime.llm, "llm", ("chat",))
        hooks.toolbox = points.wrap(hooks.toolbox, "tool", ("invoke",))
        chan = points.wrap(chan, "chan", ("send", "update", "post_card"))
        ex = points.wrap(ex, "exec", ("execute", "verify"))
        for_runner = points.wrap(store, "store", ("get_run",))
    approvals = Approvals(
        runtime.store,
        runtime.audit,
        runtime.registry,
        chan,
        lambda run_id, status, decision: runtime.on_decided(run_id, status, decision),
        detector=runtime.detector,
    )

    def request_approval(plan, decision, requested_by):
        req = approvals.request(plan, decision, requested_by)
        return Delivery(ok=True, ref=req.channel_ref)

    hooks.request_approval = request_approval
    hooks.post_card = lambda card: chan.post_card(card)
    hooks.execute, hooks.verify = ex.execute, ex.verify
    return SimpleNamespace(runtime=runtime, approvals=approvals, for_runner=for_runner)


def run_tick(stack, config_dir: Path, store) -> int:
    """The real steps `sweep`, `reconcile` and `stuck` with the clock one hour later."""
    cfg = load_config(config_dir)
    app = SimpleNamespace(
        config=cfg,
        registry=stack.runtime.registry,
        store=store,
        audit=stack.runtime.audit,
        approvals=stack.approvals,
        runtime=stack.runtime,
    )
    steps = [step for step in tick.STEPS if step.name in TICK_STEPS]
    assert [step.name for step in steps] == list(TICK_STEPS)
    return tick.run_tick(app, now=now() + TICK_LATER, steps=steps)


def decide_approval(stack, store) -> None:
    """Record the approval of the one pending request (the receiver's job in a deployment)."""
    (req,) = store.list_approvals({"PENDING"})
    ok, why = stack.approvals.decide(
        ApprovalDecision(
            approval_id=req.approval_id,
            plan_hash=req.plan_hash,
            step=req.current_step,
            decision="approve",
            approver_id="user:a",
            channel="fake",
        ),
        record_only=True,
    )
    assert (ok, why) == (True, "approved")


def start_waiting_run(stack, store, run_id: str) -> None:
    """The setup of the `approve` path: one run that waits for approval, then the approval."""
    stack.runtime.handle(
        AGENT,
        PRINCIPAL,
        DOCUMENT.encode("utf-8"),
        trigger_kind=worker.TRIGGER_KIND,
        trigger_ref=_ref(SENDER, KEY, DOCUMENT),
        run_id=run_id,
    )
    assert RunState(store.get_run(run_id).state) is RunState.WAITING_FOR_APPROVAL
    decide_approval(stack, store)


def req_state(requests) -> str | None:
    assert len(requests) <= 1, requests  # at most one approval request for the one run
    if not requests:
        return None
    req = requests[0]
    if req.status == "APPROVED":
        return "approved"
    assert req.status == "PENDING", req.status
    return "sent" if req.sent_at is not None else "unsent"


ALL_STATUSES = {"PENDING", "APPROVED", "REJECTED", "EXPIRED"}


# --- the tables themselves, and a trace of each path without a crash ----------------------------------


class Recorder(CrashPoints):
    """Records every point instead of crashing: the sequence of wrapped calls of a whole path."""

    def __init__(self) -> None:
        super().__init__(mode="raise")
        self.log: list[str] = []

    def hit(self, point: str) -> None:
        self.log.append(point)


def _expected_log(path: Path_) -> list[str]:
    return [f"{row[0]}:{edge}" for row in path.rows for edge in ("before", "after")]


def make_config(home: Path, path: Path_) -> Path:
    """The tooled test agent of k5_support. A path at "suggest" needs the contract of an executor
    that is not `none` and, for a tooled agent, a green replay record: the record is written for the
    config as it is at "shadow" (the config hash does not cover levels), then the level is raised."""
    cfg = k5_cfg(home, levels={ACTION: "shadow"} if path.suggest else None)
    if path.suggest:
        reg = load_registry(load_config(cfg))
        agent = reg.agents[AGENT]
        record = {
            "agent_id": AGENT,
            "config_hash": reg.config_hash(AGENT),
            "model_id": reg.config.routes[agent.model_route].model_id,
            "prompt_sha256": reg.prompt_sha256(AGENT),
            "bundle_sha256": "b" * 64,
            "k": 3,
            "pass_k": 1.0,
            "pass_rate": 1.0,
            "threshold": 1.0,
            "green": True,
            "ts": "2026-11-01T00:00:00+00:00",
        }
        (cfg / "replay-records.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
        edit_config(cfg, lambda d: d[0]["levels"].update({ACTION: "suggest"}), "agents.yaml")
    return cfg


@pytest.mark.parametrize("name", list(PATHS))
def test_trace_of_a_path_without_a_crash_matches_its_table(name, tmp_path):
    """Replays the path in this process with a recorder in every wrap point: the sequence of wrapped
    calls equals the table, and the counters at the end equal the last row."""
    path = PATHS[name]
    config_dir, store, files = (
        make_config(tmp_path / "w", path),
        MemoryStore(),
        Files(tmp_path / "state"),
    )
    run_id = _run_id(SENDER, KEY)
    if path.via == "tick":
        start_waiting_run(build_stack(config_dir, store, files, path), store, run_id)
    with Recorder() as rec:
        stack = build_stack(config_dir, store, files, path, rec)
        if path.via == "worker":
            stack.runtime.handle(
                AGENT,
                PRINCIPAL,
                DOCUMENT.encode("utf-8"),
                trigger_kind=worker.TRIGGER_KIND,
                trigger_ref=_ref(SENDER, KEY, DOCUMENT),
                run_id=run_id,
            )
        else:
            assert run_tick(stack, config_dir, store) == 0
    assert rec.log == _expected_log(path)
    last = path.rows[-1]
    assert RunState(store.get_run(run_id).state).value == last[2] == path.final
    assert (files.model_calls(), len(files.tool_calls())) == (last[3], last[4])
    assert req_state(store.list_approvals(ALL_STATUSES)) == last[5]
    assert (files.cards(), len(files.executed())) == (last[6], last[7])


def test_the_tables_are_well_formed():
    """Unique ids; the three paths; the number of points; every point names a wrapped method."""
    points = [p for ps in ALL_POINTS.values() for p in ps]
    assert len({p.id for p in points}) == len(points)
    assert {name: len(ps) for name, ps in ALL_POINTS.items()} == {
        # reserve/settle: per model call two rows more (stop state, reserve_spend) and one less (settle books
        # the run cost, so no add_cost); the two extra `get_kill_switch` rows add no `:after` point (pure read)
        "read": 2 * 35 - 9 if RESERVES else 2 * 33 - 7,
        "propose": 2 * 47 - 12 if RESERVES else 2 * 45 - 10,
        "approve": 2 * 18 - 4,
    }
    assert {p.point.partition(".")[0] for p in points} == {
        "store",
        "loop",
        "audit",
        "llm",
        "tool",
        "chan",
        "exec",
    }
    assert {p.point.partition(".")[0] for p in ALL_POINTS["approve"]} == {
        "chan",
        "loop",
        "store",
        "audit",
        "exec",
    }


# --- PostgreSQL: a child process killed at each point -------------------------------------------------


class PathChild(Child):
    """A child that runs THIS module as its script: the worker ("serve") or one tick ("tick")."""

    def __init__(
        self, work_dir: Path, args: list[str], *, dsn: str, tick_only: bool = False
    ) -> None:
        work_dir.mkdir(parents=True, exist_ok=True)
        self._out, self._err = work_dir / "stdout.txt", work_dir / "stderr.txt"
        self._tick_only = tick_only
        env = {**os.environ, SECRETS_ENV: json.dumps(ONE), DSN_ENV: dsn}
        command = [sys.executable, "-m", "tests.triggers.test_t5_crash_matrix_paths", *args]
        with self._out.open("wb") as out, self._err.open("wb") as err:
            self.proc = subprocess.Popen(  # noqa: S603 - this interpreter, this repo's module, no shell
                command, cwd=ROOT, env=env, stdout=out, stderr=err, stdin=subprocess.DEVNULL
            )
        self.port = 0

    def __enter__(self):
        if self._tick_only:
            return self
        return super().__enter__()


def _child(tmp_path: Path, dsn: str, mode: str, path: Path_) -> PathChild:
    """The worker (or a tick child) on the schema of `dsn`; a second call is a restart (same
    config, flag, files)."""
    home = tmp_path / "w"
    runs = len(list(home.glob("run-*")))
    args = [
        "--config-dir",
        str(home / "config"),
        "--flag",
        str(home / "flag"),
        "--files-dir",
        str(home / "state"),
        "--path",
        path.name,
        "--mode",
        mode,
    ]
    tagged = make_conninfo(dsn, application_name=_tag(tmp_path))
    return PathChild(home / f"run-{runs}", args, dsn=tagged, tick_only=mode == "tick")


def _killed(child: PathChild) -> None:
    """The child ended at the armed point: exit code and marker of the crash helper."""
    code = child.wait(KILL_WAIT_S)
    assert code == 137, (code, child.stderr()[-2000:])
    assert "simulate crash" in child.stdout() and "stopped" not in child.stdout()


def _pg_store(dsn: str):
    from hadavin_sdk.store.postgres import PostgresStore, connect

    conn = connect(dsn)
    return conn, PostgresStore(conn)


def _pg_requests(dsn: str):
    conn, store = _pg_store(dsn)
    try:
        return store.list_approvals(ALL_STATUSES)
    finally:
        conn.close()


def _pg_tick(dsn: str, tmp_path: Path, path: Path_) -> int:
    conn, store = _pg_store(dsn)
    try:
        home = tmp_path / "w"
        stack = build_stack(home / "config", store, Files(home / "state"), path)
        return run_tick(stack, home / "config", store)
    finally:
        conn.close()


def _settled_to(dsn: str, run_id: str, state: str, request: str | None) -> tuple:
    """Waits for the row state AND the path's final approval request: the loop moves the row to WAITING before
    it saves the request, and a tick in that gap (the test clock is an hour ahead) reads an orphan wait."""
    deadline = time.monotonic() + FIRE_WAIT_S
    while True:
        mine = [row for row in _rows(dsn) if row[0] == run_id]
        if mine and mine[0][4] == state and req_state(_pg_requests(dsn)) == request:
            return mine[0]
        assert time.monotonic() < deadline, f"run did not reach {state}/{request}: {mine}"
        time.sleep(0.02)


def _observe(store: str, point: Point, **seen: object) -> None:
    target = os.environ.get(OBSERVED_ENV)
    if target:
        with Path(target).open("a", encoding="utf-8") as out:
            out.write(json.dumps({"store": store, "id": point.id, **seen}) + "\n")


XFAIL_PG: dict[str, str] = {}
XFAIL_MEMORY: dict[str, str] = {}


def _params(points: list[Point], xfail: dict[str, str]) -> list:
    return [
        pytest.param(
            p,
            id=p.id,
            marks=[pytest.mark.xfail(strict=True, reason=xfail[p.id])] if p.id in xfail else [],
        )
        for p in points
    ]


def _all(xfail: dict[str, str]) -> list:
    return _params([p for ps in ALL_POINTS.values() for p in ps], xfail)


def _check_invariants(
    files: Files, point: Point, row_at_kill: str | None, calls_at_kill: int, final_state: str
) -> dict:
    """The invariants that hold at every point; returns the counters for the report."""
    path = PATHS[point.path]
    full = path.rows[-1][3]
    model = files.model_calls()
    assert model <= (full if row_at_kill is None else calls_at_kill), (model, calls_at_kill)
    if (
        row_at_kill is None
    ):  # no row: never called before the kill; the retry's fresh run calls once
        assert calls_at_kill == 0 and model == full
    tools = files.tool_calls()
    assert len(tools) == len(set(tools)) <= 1, tools  # no read tool twice with the same arguments
    done = files.executed()
    assert len(done) <= 1 and all(x["approval"] == "approve" for x in done), done
    assert len(done) == expected_acts(point.path, point), done
    assert final_state not in (*IN_PROGRESS, "PLAN_READY", "EXECUTING", "VERIFYING")
    return {"model": model, "tools": len(tools), "acts": len(done), "cards": files.cards()}


@pytest.fixture
def dsn():
    """A DSN on a fresh migrated schema; the schema is dropped afterwards."""
    yield from pg_schema()


@pytest.mark.parametrize("point", _all(XFAIL_PG))
def test_pg_kill_at_point(point: Point, dsn, tmp_path):
    """Kill the process at `point` on PostgreSQL; restart; (a) the same request again before any
    tick; (b) the tick steps a later clock; (c) the request again. Checks the invariants."""
    path = PATHS[point.path]
    body, run_id = wire_body(KEY, DOCUMENT), _run_id(SENDER, KEY)
    identity = (run_id, AGENT, PRINCIPAL, _ref(SENDER, KEY, DOCUMENT))
    home = tmp_path / "w"
    config_dir, files = make_config(home, path), Files(home / "state")
    ack_status, ack_data = None, b""
    if path.via == "tick":  # the setup: a run that waits, and the person's approval
        conn, store = _pg_store(dsn)
        try:
            start_waiting_run(build_stack(config_dir, store, files, path), store, run_id)
        finally:
            conn.close()
    flag = _arm(tmp_path, "w", point.point, point.nth)
    if path.via == "worker":
        with _child(tmp_path, dsn, "serve", path) as child:
            ack_status, ack_data = signed_post(child.port, body, SECRET)
            _killed(child)
    else:
        with _child(tmp_path, dsn, "tick", path) as child:
            _killed(child)
    assert not flag.exists()
    _backends_gone(dsn, _tag(tmp_path))

    rows = _rows(dsn)
    assert len(rows) <= 1 and all(found[:4] == identity for found in rows)
    row = rows[0][4] if rows else None
    req = req_state(_pg_requests(dsn))
    calls_at_kill = files.model_calls()
    at_kill = (
        row,
        calls_at_kill,
        len(files.tool_calls()),
        req,
        files.cards(),
        len(files.executed()),
    )
    assert at_kill == (point.row, point.llm, point.tool, point.req, point.cards, point.acts)
    if RESERVES:  # one open hold between reserve and settle, none before, settled after; open stays open
        money_kill = assert_kill_state(*pg_money(dsn, run_id), {money_at_kill(point)}, point.id)
        assert row is not None or money_kill == (0, 0)  # no run row, no hold
    assert ack_status in ((None,) if row is None else (None, 202, 200)), (ack_status, ack_data)
    if ack_status in OK:
        assert rows and json.loads(ack_data)["run_id"] == run_id

    expected = after_tick(point.path, row, req)
    state_after = path.final if expected is None else expected[0]
    with _child(tmp_path, dsn, "serve", path) as child:
        status_a, data_a = signed_post(child.port, body, SECRET)  # (a) before any tick
        if row is None:  # no row: accepted as new, runs the whole path once
            assert status_a in OK, (status_a, data_a)
            assert json.loads(data_a)["run_id"] == run_id
            _settled_to(dsn, run_id, path.final, path.rows[-1][5])
        else:  # a row: answered from it, nothing runs
            assert status_a == (202 if row in IN_PROGRESS else 200), (status_a, data_a)
            assert json.loads(data_a) == {"run_id": run_id, "state": row}
            assert _rows(dsn) == rows
        calls_after_a = files.model_calls()
        assert _pg_tick(dsn, tmp_path, path) == 0  # (b)
        after = _rows(dsn)
        want_after = (*identity, state_after, None if expected is None else expected[1])
        assert after == [want_after]
        status_c, data_c = signed_post(child.port, body, SECRET)  # (c) after the tick
        assert status_c == 200, (status_c, data_c)
        assert json.loads(data_c) == {"run_id": run_id, "state": state_after}
        assert _rows(dsn) == after
        assert child.proc.poll() is None  # the restarted worker did not die
    assert files.model_calls() == calls_after_a

    end_req = req_state(_pg_requests(dsn))
    if row == "WAITING_FOR_APPROVAL" and req in ("unsent", "sent") and path.name == "propose":
        assert (state_after, end_req) == (
            "WAITING_FOR_APPROVAL",
            "sent",
        )  # still waiting, request kept
    if row == "WAITING_FOR_APPROVAL" and req is None:
        assert (state_after, end_req) == ("NEEDS_PERSON", None)
        assert files.cards() == 0  # nobody was told: no card, only the tick's audit line
    want_cards = path.fresh_cards if row is None else point.cards + (req == "unsent")
    seen = _check_invariants(files, point, row, calls_at_kill, state_after)
    assert seen["cards"] == want_cards, (seen, want_cards)
    if RESERVES:  # no second hold from the restart, the tick or the retry; the day total is the rows' sum
        assert_end_state(*pg_money(dsn, run_id), money_kill, row, money_full(point.path), point.id)
    _observe(
        "postgres",
        point,
        ack=ack_status,
        row=row,
        request=req,
        retry_a=status_a,
        after=state_after,
        reason=want_after[5],
        retry_c=status_c,
        end_request=end_req,
        **seen,
    )


# --- memory store: the same tables, same process, mode "raise" -----------------------------------------


def _memory_requests(store):
    return store.list_approvals(ALL_STATUSES)


def _memory_wait(store, run_id: str, state: str, request: str | None) -> None:
    """Waits for the row state AND the path's final approval request: the loop moves the row to WAITING before
    it saves the request, and a tick in that gap (the test clock is an hour ahead) reads an orphan wait."""
    deadline = time.monotonic() + FIRE_WAIT_S
    while True:
        found = [r for r in _memory_rows(store) if r[0] == run_id]
        if found and found[0][4] == state and req_state(_memory_requests(store)) == request:
            return
        assert time.monotonic() < deadline, f"run did not reach {state}/{request}: {found}"
        time.sleep(0.01)


@pytest.mark.parametrize("point", _all(XFAIL_MEMORY))
def test_memory_raise_at_point(point: Point, tmp_path):
    """The thread that reaches `point` dies there (memory store); then a new Runtime and Runner on
    the same store, (a) the request again, (b) the tick steps a later clock, (c) the request again."""
    path = PATHS[point.path]
    body, run_id = wire_body(KEY, DOCUMENT), _run_id(SENDER, KEY)
    identity = (run_id, AGENT, PRINCIPAL, _ref(SENDER, KEY, DOCUMENT))
    config_dir, files, store = (
        make_config(tmp_path / "w", path),
        Files(tmp_path / "state"),
        MemoryStore(),
    )
    ack_status, ack_data = None, b""
    if path.via == "tick":
        start_waiting_run(build_stack(config_dir, store, files, path), store, run_id)
    with CrashPoints() as points:
        stack = build_stack(config_dir, store, files, path, points)
        points.arm(point.point, nth=point.nth)
        if path.via == "worker":
            wsgi, runner = worker.make_app(make_trigger_app(stack.runtime, stack.for_runner, ONE))
            try:
                ack_status, ack_data = _wsgi_post(wsgi, body)
                deadline = time.monotonic() + FIRE_WAIT_S
                while not points.fired and time.monotonic() < deadline:
                    time.sleep(0.005)
            finally:
                runner.close()
        else:
            try:
                run_tick(stack, config_dir, store)
            except SimulatedCrash:
                pass
        assert points.fired == (point.point,)

    rows = _memory_rows(store)
    assert len(rows) <= 1 and all(found[:4] == identity for found in rows)
    row = rows[0][4] if rows else None
    req = req_state(_memory_requests(store))
    calls_at_kill = files.model_calls()
    at_kill = (
        row,
        calls_at_kill,
        len(files.tool_calls()),
        req,
        files.cards(),
        len(files.executed()),
    )
    assert at_kill == (point.row, point.llm, point.tool, point.req, point.cards, point.acts)
    if RESERVES:
        money_kill = assert_kill_state(*memory_money(store, run_id), {money_at_kill(point)}, point.id)
        assert row is not None or money_kill == (0, 0)
    if path.via == "worker":  # the request thread survives the loop thread and always answers
        assert ack_status in ((503,) if row is None else (202, 200)), (ack_status, ack_data)

    expected = after_tick(point.path, row, req)
    state_after = path.final if expected is None else expected[0]
    stack = build_stack(config_dir, store, files, path)
    wsgi, runner = worker.make_app(make_trigger_app(stack.runtime, store, ONE))
    try:
        status_a, data_a = _wsgi_post(wsgi, body)  # (a) before any tick
        if row is None:
            assert status_a in OK, (status_a, data_a)
            _memory_wait(store, run_id, path.final, path.rows[-1][5])
        else:
            assert status_a == (202 if row in IN_PROGRESS else 200), (status_a, data_a)
            assert json.loads(data_a) == {"run_id": run_id, "state": row}
            assert _memory_rows(store) == rows
        calls_after_a = files.model_calls()
        assert run_tick(stack, config_dir, store) == 0  # (b)
        after = _memory_rows(store)
        want_after = (*identity, state_after, None if expected is None else expected[1])
        assert after == [want_after]
        status_c, data_c = _wsgi_post(wsgi, body)  # (c) after the tick
        assert status_c == 200, (status_c, data_c)
        assert json.loads(data_c) == {"run_id": run_id, "state": state_after}
        assert _memory_rows(store) == after
    finally:
        runner.close()
    assert files.model_calls() == calls_after_a

    end_req = req_state(_memory_requests(store))
    if row == "WAITING_FOR_APPROVAL" and req in ("unsent", "sent") and path.name == "propose":
        assert (state_after, end_req) == ("WAITING_FOR_APPROVAL", "sent")
    if row == "WAITING_FOR_APPROVAL" and req is None:
        assert (state_after, end_req) == ("NEEDS_PERSON", None)
        assert files.cards() == 0
    want_cards = path.fresh_cards if row is None else point.cards + (req == "unsent")
    seen = _check_invariants(files, point, row, calls_at_kill, state_after)
    assert seen["cards"] == want_cards, (seen, want_cards)
    if RESERVES:
        assert_end_state(*memory_money(store, run_id), money_kill, row, money_full(point.path), point.id)
    _observe(
        "memory",
        point,
        ack=ack_status,
        row=row,
        request=req,
        retry_a=status_a,
        after=state_after,
        reason=want_after[5],
        retry_c=status_c,
        end_request=end_req,
        **seen,
    )


# --- the child script ----------------------------------------------------------------------------------


def child_main(argv: list[str] | None = None) -> int:
    """The worker ("serve") or one tick ("tick") on PostgreSQL, every collaborator of the runtime
    behind ONE CrashPoints object in mode "exit". "serve" prints `port <n>` once the socket is bound."""
    from hadavin_sdk.store.postgres import PostgresStore, connect

    parser = argparse.ArgumentParser(prog="python -m tests.triggers.test_t5_crash_matrix_paths")
    parser.add_argument("--config-dir", type=Path, required=True)
    parser.add_argument("--flag", type=Path, required=True)
    parser.add_argument("--files-dir", type=Path, required=True)
    parser.add_argument("--path", choices=sorted(PATHS), required=True)
    parser.add_argument("--mode", choices=("serve", "tick"), required=True)
    args = parser.parse_args(argv)

    install_pg_test_seeding()
    plain = PostgresStore(connect(os.environ[DSN_ENV]))
    points = CrashPoints(mode="exit", flag_path=args.flag)
    stack = build_stack(args.config_dir, plain, Files(args.files_dir), PATHS[args.path], points)
    if args.mode == "tick":
        print(f"tick {run_tick(stack, args.config_dir, plain)}", flush=True)
        return 0
    app = make_trigger_app(stack.runtime, stack.for_runner, json.loads(os.environ[SECRETS_ENV]))
    wsgi, runner = worker.make_app(app)
    server = worker.make_server(HOST, 0, wsgi, worker.ACK_WAIT_S + worker.SOCKET_SLACK_S)
    print(f"port {server.server_port}", flush=True)
    code = worker.serve(server, runner)
    print("stopped", flush=True)
    return code


if __name__ == "__main__":
    sys.exit(child_main())
