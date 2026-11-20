"""Concurrent, seeded fuzz of the signed trigger endpoint (ORDER 016, item 4b).

`test_t5_fuzz.py` is sequential, has a fixed clock and never reaches a 503. This file reuses its
generator, oracle and wire helpers by import and adds what only parallel clients can show:

C1  memory store, in-process calls from 16 threads, a small pool of keys in short bursts, one to
    four loop slots, a model double with random delays. C1b: the two 503 paths held open by hand.
C2  the same with a store wrapper by seed: slow `get_run`, `get_run` down for a window of calls and
    then back, slow `create_run`.
C3  a moving clock: jumps over the 300 s window in both directions, steps backwards. The oracle
    uses the clock value the endpoint itself saw (the clock is wrapped and records it).
C4  raw sockets against the real quiet server from 8 threads, slow senders, early closes,
    pipelined second requests; every valid request is sent twice at the same time.
C5  C1 on PostgreSQL (HADAVIN_TEST_PG_DSN), rows read back by SQL.
C6  `Runner.close()` while 8 threads send.

The oracle knows for every request whether it is validly signed, valid in body, which sender, key
and document. Invariants (numbers as in the order):
I1 only the endpoint's known status codes. I2 a refusal has an empty body, a 2xx body holds exactly
run_id and state. I3 one row per (sender, key); the row holds the hash of exactly one document;
requests with it get 2xx or 503, requests with the other one get 409 or 503. I4 no row for a request
that was not validly signed and valid in body. I5 a 2xx or 409 is only sent when a matching row exists
(read in the client thread right after the answer). I6 the model double is called at most once per
row. I7 afterwards no thread is left, every slot is free, nothing on stderr, no body token, key,
signature or secret in the log. I8 a 503 retried once the pool is free gets 2xx or 409.

Counts of the statuses and of keys with overlapping requests are written to the terminal report, so
it is visible that the races happened. Every message starts with layer, seed and case number.
"""

from __future__ import annotations

import contextlib
import hashlib
import os
import random
import re
import threading
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from types import SimpleNamespace

import pytest

from hadavin_sdk.models import Reply
from hadavin_sdk.store import MemoryStore
from hadavin_sdk.triggers import worker
from tests.contracts.kinds.store_postgres import pg_schema
from tests.k5_support import build_runtime, k5_cfg
from tests.triggers.crash_launcher import AGENT, PRINCIPAL, TENANT, CountingLLM
from tests.triggers.test_t5_fuzz import (
    A_NEW,
    A_OLD,
    ALL_SECRETS,
    B_ONLY,
    CLOCK,
    DOC_POOL,
    ENDPOINT_STATUSES,
    HEX64,
    INPROC,
    KEY_MARK,
    KEY_POOL,
    MAX_BODY,
    NOW,
    OK,
    PATH,
    POST,
    SECRETS,
    SENDER_A,
    SENDER_B,
    SERVER_STATUSES,
    TOKEN,
    Case,
    Model,
    WireCase,
    _valid_body,
    call_inproc,
    check_answer,
    check_log,
    check_wire,
    exchange,
    make_case,
    product_log,
    ref_of,
    render,
    run_id_of,
    serving,
    sig_hex,
    sql_rows,
    wire_cases,
)

if os.environ.get("HADAVIN_TEST_PG_DSN"):  # set: the driver must be there, never a silent skip
    import psycopg

SEEDS = {"c1-1": 20261120_41, "c1-2": 20261120_42, "c1-4": 20261120_43, "c2": 20261120_44}
SEEDS |= {"c3": 20261120_45, "c4": 20261120_46, "c5": 20261120_47, "c6": 20261120_48}
SEEDS |= {"c1b": 20261120_49}
WINDOW_S = 300
HOT_SHARE = 0.40  # of the requests: a valid one for one of the bursts' few keys
EDGES = (-300, -299, -1, 0, 1, 299, 300)
ACK_OR_REFUSAL = OK | {409, 503}  # what a request that reaches `start` may get
DRIVE_TIMEOUT_S = 60.0
THREAD_NAME = "fz-client"
TS_PLAIN = re.compile(r"ts[+-]\d+|ts-zero-padded-12")
REPORT: list[str] = []


def say(text: str) -> None:
    """One line for the terminal report (a test's own print is captured, this is not)."""
    REPORT.append(text)
    reporter = _REPORTER.get("tr")
    if reporter is not None:
        reporter.write_line(text)


_REPORTER: dict[str, object] = {}


@pytest.fixture(autouse=True)
def _terminal(request):
    _REPORTER["tr"] = request.config.pluginmanager.get_plugin("terminalreporter")
    yield
    _REPORTER.pop("tr", None)


# ---- doubles ------------------------------------------------------------------------------------


def delays_mixed(rng: random.Random) -> float:
    r = rng.random()
    if r < 0.65:
        return 0.0
    return rng.uniform(0.002, 0.015) if r < 0.95 else rng.uniform(0.15, 0.30)


def delays_short(rng: random.Random) -> float:
    return 0.0 if rng.random() < 0.6 else rng.uniform(0.002, 0.015)


class RecLLM(CountingLLM):
    """The model double: thread safe, counts calls per sha256 of the document it is handed, sleeps a
    seeded random time, and can be held shut with `gate` (a call then waits until it is set)."""

    def __init__(self, seed: int, delay=delays_mixed, gate: threading.Event | None = None) -> None:
        super().__init__(None, 0.0)
        self.counts: Counter[str] = Counter()
        self._rl, self._rng, self._delay, self.gate = threading.Lock(), random.Random(seed), delay, gate  # noqa: S311, E501

    def chat(self, messages, *, system, route, tools=None, documents=None, output_schema=None):
        digest = hashlib.sha256(documents[0]).hexdigest() if documents else "none"
        with self._rl:
            self.counts[digest] += 1
            pause = self._delay(self._rng)
        if self.gate is not None:
            self.gate.wait(30)
        if pause:
            time.sleep(pause)
        return Reply(text="Nothing to do.", model_id="fake-model")


class Clock:
    """The endpoint's clock. It records the value each thread was last given, so the client can say
    what the endpoint saw. `moving` jumps over the window in both directions and steps backwards."""

    OFFSETS = (-900, -601, -600, -301, -300, -299, 0, 299, 300, 301, 599, 600, 601, 900)

    def __init__(self, seed: int = 0, moving: bool = False) -> None:
        self.t, self.moving = CLOCK, moving
        self._rng, self._lock, self.local = random.Random(seed), threading.Lock(), threading.local()  # noqa: S311
        self.calls = 0
        self.jumps = 0
        self.backwards = 0

    def freeze(self) -> None:
        with self._lock:
            self.moving, self.t = False, CLOCK

    def __call__(self) -> float:
        with self._lock:
            self.calls += 1
            if self.moving:
                roll = self._rng.random()
                if roll < 0.05:
                    self.t = NOW + self._rng.choice(self.OFFSETS) + self._rng.random() * 0.99
                    self.jumps += 1
                elif roll < 0.15:
                    self.t -= self._rng.uniform(0, 5)
                    self.backwards += 1
                else:
                    self.t += self._rng.uniform(0, 0.5)
            value = self.t
        self.local.last = value
        return value


class FaultStore:
    """The Runner's view of the store: `get_run` slow by seed and down for a window of calls, then
    healthy. Everything else is the inner store. A raise is a connectivity error (an OSError)."""

    def __init__(self, inner, seed: int, outage_at: int, outage_len: int, slow_max_s=0.05) -> None:
        self._inner, self._lock = inner, threading.Lock()
        self._rng = random.Random(seed)  # noqa: S311
        self._at, self._len, self._slow = outage_at, outage_len, slow_max_s
        self.calls = self.raised = self.slowed = 0
        self.healed = False
        self.local = threading.local()

    def get_run(self, run_id):
        with self._lock:
            self.calls += 1
            down = not self.healed and self._at <= self.calls < self._at + self._len
            pause = 0.0
            if not self.healed and not down and self._rng.random() < 0.3:
                pause = self._rng.uniform(0, self._slow)
                self.slowed += 1
            self.raised += down
        if down:
            self.local.raised = True
            raise ConnectionError("store down")
        if pause:
            time.sleep(pause)
        return self._inner.get_run(run_id)

    def __getattr__(self, name):
        return getattr(self._inner, name)


class SlowCreateStore:
    """The runtime's view of the store: `create_run` delayed by seed."""

    def __init__(self, inner, seed: int) -> None:
        self._inner, self._lock = inner, threading.Lock()
        self._rng = random.Random(seed)  # noqa: S311
        self.healed = False

    def create_run(self, run):
        with self._lock:
            pause = 0.0 if self.healed or self._rng.random() < 0.5 else self._rng.uniform(0, 0.03)
        if pause:
            time.sleep(pause)
        return self._inner.create_run(run)

    def __getattr__(self, name):
        return getattr(self._inner, name)


# ---- the stack ----------------------------------------------------------------------------------


def make_stack2(
    tmp_path, runtime_store, runner_store, llm, *, max_running, ack_wait_s, clock, max_waiting=32
):
    """The WSGI callable and its Runner. The Runtime works on `runtime_store`, the Runner reads
    rows through `runner_store` (a separate object, so the two can fail apart)."""
    runtime, _cards = build_runtime(k5_cfg(tmp_path), llm, store=runtime_store)
    names = {f"{s}-secret-{i}": v for s, values in SECRETS.items() for i, v in enumerate(values)}
    senders = [
        SimpleNamespace(
            id=sender,
            secret_names=[f"{sender}-secret-{i}" for i in range(len(values))],
            agent_id=AGENT,
            principal_id=PRINCIPAL,
        )
        for sender, values in SECRETS.items()
    ]
    triggers = SimpleNamespace(
        tenant=TENANT,
        senders=senders,
        max_body_bytes=MAX_BODY,
        max_running=max_running,
        ack_wait_s=ack_wait_s,
        poll_s=0.002,
        max_waiting=max_waiting,
    )
    app = SimpleNamespace(
        config=SimpleNamespace(triggers=triggers),
        registry=runtime.registry,
        runtime=runtime,
        store=runner_store,
        trigger_resolve=names.__getitem__,
    )
    return worker.make_app(app, clock=clock)


def mem_snapshot(store: MemoryStore) -> dict[str, tuple[str, str, str]]:
    """Every row at one instant (under the store's own lock: the per-state listing can see a
    moving row twice or not at all)."""
    with store._lock:
        return {rid: (r.agent_id, r.principal_id, r.trigger_ref) for rid, r in store._runs.items()}


def sql_snapshot(dsn: str) -> dict[str, tuple[str, str, str]]:
    return {rid: (agent, principal, ref) for rid, agent, principal, ref in sql_rows(dsn)}


# ---- requests -----------------------------------------------------------------------------------


def hot_case(rng: random.Random, index: int, keys: tuple[str, ...], ts_value: int) -> Case:
    """A validly signed, valid request for a key of the burst, built with the oracle's own helpers."""
    sender = rng.choice((SENDER_A, SENDER_B))
    secret = rng.choice((A_OLD, A_NEW)) if sender == SENDER_A else B_ONLY
    key = rng.choice(keys)
    doc = DOC_POOL[0] if rng.random() < 0.75 else rng.choice(DOC_POOL[1:])
    body, _tight, style = _valid_body(rng, key, doc)
    ts = str(ts_value)
    good = sig_hex(body, ts, secret)
    return Case(
        index=index,
        notes=[f"hot/{style}/{doc[-18:]}"],
        method=POST,
        path=PATH,
        sent=body,
        length=str(len(body)),
        ts=ts,
        sig="v0=" + good,
        made_sig=good,
        noise=[],
        refusal=None,
        signed=True,
        sender=sender,
        key=key,
        document=doc.encode("utf-8"),
    )


def ts_mutated(case: Case) -> bool:
    return any(n.startswith("ts") and not TS_PLAIN.fullmatch(n) for n in case.notes)


def build_jobs(
    seed: int, count: int, *, phase: int, allow_nul: bool = True, drop_ts_mutated: bool = False
) -> list[Case]:
    """Refused requests of the sequential generator mixed with hot valid ones. The hot ones use two
    keys (one key every fourth burst) at a time, so at most four runs are born per burst."""
    rng = random.Random(seed)  # noqa: S311 - a seeded test generator
    jobs: list[Case] = []
    extra, cap = 0, max(3, count // 60)
    while len(jobs) < count:
        index = len(jobs)
        if rng.random() < HOT_SHARE:
            burst = index // phase
            pair = (KEY_POOL[(2 * burst) % 24], KEY_POOL[(2 * burst + 1) % 24])
            keys = pair[:1] if burst % 4 == 0 else pair
            edge = rng.random() < 0.3
            ts_value = NOW + (rng.choice(EDGES) if edge else rng.randint(-WINDOW_S, WINDOW_S))
            jobs.append(hot_case(rng, index, keys, ts_value))
            continue
        case = make_case(rng, index, INPROC)
        if case.refusal is None:
            if extra >= cap or (not allow_nul and b"\x00" in (case.document or b"")):
                continue
            extra += 1
        if drop_ts_mutated and ts_mutated(case):
            continue
        jobs.append(case)
    return jobs


def fresh_case(tag: str, n: int) -> Case:
    """A valid request for a key nobody used (the same helpers, a fixed timestamp)."""
    rng = random.Random(n)  # noqa: S311
    case = hot_case(rng, 10**6 + n, (f"{KEY_MARK}{tag}-{n}",), NOW)
    return case


# ---- the context of one layer -------------------------------------------------------------------


@dataclass
class Rec:
    case: Case
    allowed: frozenset[int] = frozenset()
    reached: bool = False  # the oracle: the request reached `start`
    status: int = 0
    t0: float = 0.0
    t1: float = 0.0
    raised: bool = False
    retry: bool = False
    thread: str = ""


@dataclass
class Ctx:
    name: str
    seed: int
    wsgi: object = None
    runner: object = None
    llm: RecLLM | None = None
    clock: Clock | None = None
    fault: FaultStore | None = None
    snapshot: object = None  # () -> dict of rows
    read_ref: object = None  # (run_id) -> trigger_ref or None
    decide: object = None  # (case, observed clock) -> (allowed, reached)
    max_running: int = 1
    ack_wait_s: float = 1.0
    recs: list[Rec] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)
    stop: threading.Event = field(default_factory=threading.Event)
    maybe_ids: dict[str, tuple[str, str]] = field(default_factory=dict)
    samples: int = 0

    def problem(self, case: Case | None, text: str) -> None:
        where = f"[{self.name} seed={self.seed}"
        if case is not None:
            where += f" case={case.index} mutations={case.notes}"
        with self.lock:
            if len(self.problems) < 40:
                self.problems.append(f"{where}] {text}")


def decide_static(case: Case, observed) -> tuple[frozenset[int], bool]:
    if case.refusal is None:
        return frozenset(ACK_OR_REFUSAL), True
    return frozenset({case.refusal}), False


def decide_moving(case: Case, observed) -> tuple[frozenset[int], bool]:
    """Exact as the clock value the endpoint saw says. A request that is not signed, or is refused
    before the signature is checked, does not depend on the clock (the generator's notes say so)."""
    if not case.signed:
        assert case.refusal is not None, "an unsigned case that must reach start"
        return frozenset({case.refusal}), False
    assert observed is not None, "a signed request and the endpoint never read the clock"
    inside = abs(int(observed) - int(str(case.ts))) <= WINDOW_S
    if not inside:
        return frozenset({401}), False
    if case.refusal is None:
        return frozenset(ACK_OR_REFUSAL), True
    return frozenset({case.refusal}), False


def loose(allowed: frozenset[int]) -> Model:
    model = Model()
    model.expected = lambda _case: allowed  # type: ignore[method-assign]
    return model


def op_inproc(ctx: Ctx, case: Case, *, retry: bool = False) -> Rec:
    """One request from a client thread, every per-request invariant checked on the spot."""
    rec = Rec(case, retry=retry, thread=threading.current_thread().name)
    if ctx.clock is not None:
        ctx.clock.local.last = None
    if ctx.fault is not None:
        ctx.fault.local.raised = False
    rec.t0 = time.monotonic()
    try:
        status_line, headers, body, errors = call_inproc(ctx.wsgi, case)
    except BaseException as exc:  # noqa: BLE001 - nothing may escape the callable
        ctx.problem(case, f"the callable raised {exc!r}")
        return rec
    rec.t1 = time.monotonic()
    rec.status = status = int(status_line.split(" ", 1)[0])
    try:
        observed = ctx.clock.local.last if ctx.clock is not None else None
        rec.allowed, rec.reached = ctx.decide(case, observed)
        if ctx.fault is not None and ctx.fault.local.raised:  # the store raised inside this call
            rec.raised, rec.allowed = True, frozenset({503})
        assert status in ENDPOINT_STATUSES, f"I1 unknown status {status_line!r}"
        check_answer(case, status, body, loose(rec.allowed), "I1/I2")
        assert errors == "", f"wsgi.errors: {errors[:200]!r}"
        names = [name.lower() for name, _ in headers]
        assert dict(headers)["Content-Length"] == str(len(body)), f"I2 {headers}"
        assert ("content-type" in names) == (status in OK), f"I2 {headers}"
        assert TOKEN.encode() not in body and "server" not in names, f"I2 {headers}"
        check_row(ctx, case, status)
    except AssertionError as exc:
        ctx.problem(case, f"{exc} (status {status}, allowed {sorted(rec.allowed)})")
    with ctx.lock:
        ctx.recs.append(rec)
    return rec


def check_row(ctx: Ctx, case: Case, status: int) -> None:
    """I5, in the client thread, right after the answer."""
    if status not in OK and status != 409:
        return
    ref = ctx.read_ref(run_id_of(case.sender, case.key))
    mine = ref_of(case.sender, case.key, case.document)
    assert ref is not None, f"I5 a {status} was sent and the store has no row"
    if status in OK:
        assert ref == mine, f"I5/I3 a {status} for a document that is not the row's"
    else:
        assert ref != mine, "I5/I3 a 409 for the document the row holds"


def drive(ctx: Ctx, jobs: list, work, threads: int, timeout_s: float = DRIVE_TIMEOUT_S) -> None:
    """`threads` clients take the jobs in order. Joined with a timeout: a thread that does not end
    fails the test (it never hangs it)."""
    todo, guard = iter(range(len(jobs))), threading.Lock()

    def client() -> None:
        while not ctx.stop.is_set():
            with guard:
                i = next(todo, None)
            if i is None:
                return
            try:
                work(jobs[i])
            except BaseException as exc:  # noqa: BLE001
                ctx.problem(jobs[i] if isinstance(jobs[i], Case) else None, f"client: {exc!r}")

    pool = [
        threading.Thread(target=client, name=f"{THREAD_NAME}-{ctx.name}-{k}", daemon=True)
        for k in range(threads)
    ]
    for t in pool:
        t.start()
    deadline = time.monotonic() + timeout_s
    for t in pool:
        t.join(max(0.0, deadline - time.monotonic()))
    alive = [t.name for t in pool if t.is_alive()]
    if alive:
        ctx.stop.set()
        for t in pool:
            t.join(2.0)
        raise AssertionError(f"[{ctx.name} seed={ctx.seed}] client threads did not end: {alive}")


@contextlib.contextmanager
def sampling(ctx: Ctx, allowed: dict[str, tuple[str, str]], interval_s: float = 0.01):
    """A thread that takes a snapshot of the rows while the clients run: I3/I4 mid-flight."""
    done = threading.Event()

    def look() -> None:
        while not done.is_set():
            try:
                rows = ctx.snapshot()
            except Exception as exc:  # noqa: BLE001
                ctx.problem(None, f"sampler: {exc!r}")
                return
            ctx.samples += 1
            for rid, (agent, principal, ref) in rows.items():
                who = allowed.get(rid)
                if who is None:
                    ctx.problem(None, f"I4 mid-flight: a row for a request that was never valid {rid}")
                elif not ref.startswith(f"{who[0]}/{who[1]}#") or (agent, principal) != (
                    AGENT,
                    PRINCIPAL,
                ):
                    ctx.problem(None, f"I3 mid-flight: the row {rid} is wrong: {ref[:60]}")
            done.wait(interval_s)

    thread = threading.Thread(target=look, name=f"{THREAD_NAME}-sampler", daemon=True)
    thread.start()
    try:
        yield
    finally:
        done.set()
        thread.join(10.0)
        if thread.is_alive():
            ctx.problem(None, "the sampler thread did not end")


def settle(ctx: Ctx, timeout_s: float = 30.0) -> None:
    """Wait until no loop is running; then every slot must be free."""
    runner = ctx.runner
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        with runner._lock:
            if not runner._jobs:
                break
        time.sleep(0.01)
    else:
        raise AssertionError(f"[{ctx.name} seed={ctx.seed}] I7 loops still running after {timeout_s} s")
    taken = 0
    try:
        while taken < ctx.max_running and runner._slots.acquire(blocking=False):
            taken += 1
    finally:
        for _ in range(taken):
            runner._slots.release()
    assert taken == ctx.max_running, f"[{ctx.name} seed={ctx.seed}] I7 only {taken} slot(s) free"


def retry_503(ctx: Ctx, run_one) -> int:
    """I8: every 503 of a request that reached start, sent again once the pool is free."""
    seen, again = set(), 0
    for rec in list(ctx.recs):
        if rec.status != 503 or not rec.reached or rec.case.index in seen:
            continue
        seen.add(rec.case.index)
        got = run_one(rec.case)
        again += 1
        if got.status not in OK | {409}:
            ctx.problem(rec.case, f"I8 the retry of a 503 got {got.status}")
    return again


def overlap_keys(recs: list[Rec]) -> int:
    """Run ids with two or more requests (that reached start) whose time spans overlap."""
    spans: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for r in recs:
        if r.reached and r.t1:
            spans[run_id_of(r.case.sender, r.case.key)].append((r.t0, r.t1))
    count = 0
    for items in spans.values():
        items.sort()
        reach = items[0][1]
        for t0, t1 in items[1:]:
            if t0 < reach:
                count += 1
                break
            reach = max(reach, t1)
    return count


def analyse(ctx: Ctx, recs: list[Rec], extra_ok: dict[str, tuple[str, str]] | None = None) -> dict:
    """The invariants that need the whole run. `extra_ok`: run ids a row may have without a request
    that is known to have reached start (a request cut off by the client)."""
    rows = ctx.snapshot()
    reaching: dict[str, set[str]] = defaultdict(set)  # run id -> hashes of the documents sent
    for r in recs:
        if r.reached:
            rid = run_id_of(r.case.sender, r.case.key)
            reaching[rid].add(hashlib.sha256(r.case.document).hexdigest())
    for rid, (agent, principal, ref) in rows.items():
        if rid not in reaching and rid not in (extra_ok or {}):
            ctx.problem(None, f"I4 a row for a request that was not valid: {rid}")
            continue
        if (agent, principal) != (AGENT, PRINCIPAL):
            ctx.problem(None, f"I3 {rid} wrong identity {agent} {principal}")
        sender_key, _, digest = ref.partition("#")
        if rid in reaching:
            want = {run_id_of(*sender_key.split("/", 1))}
            if want != {rid} or digest not in reaching[rid]:
                ctx.problem(None, f"I3 the row {rid} is for another key or document: {ref[:70]}")
    for r in recs:
        rid = run_id_of(r.case.sender, r.case.key) if r.case.key else None
        if r.status not in OK and r.status != 409:
            continue
        row = rows.get(rid)
        mine = hashlib.sha256(r.case.document).hexdigest()
        if row is None:
            ctx.problem(r.case, f"I5 {r.status} and no row at the end")
        elif (row[2].partition("#")[2] == mine) != (r.status in OK):
            ctx.problem(r.case, f"I3 a {r.status} for a document unlike the row's")
    hashes = Counter(ref.partition("#")[2] for _, _, ref in rows.values())
    if ctx.llm is not None:
        for digest, calls in ctx.llm.counts.items():
            if calls > hashes.get(digest, 0):
                ctx.problem(None, f"I6 the model was called {calls} times, rows {hashes.get(digest, 0)}")
    return rows


def finish(ctx: Ctx, baseline: set, run_one, lines: list[str], signatures: set[str]) -> dict:
    """After the clients: settle, I8 retries, a fresh request per slot, close, no thread left."""
    settle(ctx)
    if ctx.fault is not None:
        ctx.fault.healed = True
    if ctx.clock is not None:
        ctx.clock.freeze()
    retried = retry_503(ctx, run_one)
    settle(ctx)
    for n in range(ctx.max_running + 1):
        fresh = fresh_case(ctx.name, n)
        signatures.add(fresh.made_sig)
        got = run_one(fresh)
        if got.status not in OK:
            ctx.problem(fresh, f"I7 a fresh valid request got {got.status} on a free pool")
    settle(ctx)
    ctx.runner.close()
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        left = [t.name for t in threading.enumerate() if t.ident not in baseline and t.is_alive()]
        if not left:
            break
        time.sleep(0.02)
    assert not left, f"[{ctx.name} seed={ctx.seed}] I7 threads left: {left}"
    return {"retried": retried}


def summary(ctx: Ctx, recs: list[Rec], rows: dict, extra: str = "") -> None:
    codes = Counter(r.status for r in recs)
    sent, reached = len(recs), sum(r.reached for r in recs)
    line = ", ".join(f"{c}:{n}" for c, n in sorted(codes.items()))
    say(
        f"{ctx.name} seed={ctx.seed}: sent={sent} valid={reached} ({reached / max(sent, 1):.0%}) "
        f"rows={len(rows)} overlapping_keys={overlap_keys(recs)} samples={ctx.samples} "
        f"model_calls={sum(ctx.llm.counts.values()) if ctx.llm else 0} statuses[{line}] {extra}"
    )


def fail_on_problems(ctx: Ctx) -> None:
    assert not ctx.problems, f"{len(ctx.problems)} problem(s), the first:\n" + "\n".join(
        ctx.problems[:8]
    )


# ---- C1, C2, C3, C5: in-process layers ----------------------------------------------------------


def run_layer(
    tmp_path,
    capsys,
    *,
    name,
    seed,
    count,
    threads,
    max_running,
    ack_wait_s,
    max_waiting=32,
    fault=False,
    moving=False,
    dsn=None,
    delay=delays_mixed,
    phase=40,
) -> dict:
    baseline = {t.ident for t in threading.enumerate()}
    jobs = build_jobs(
        seed, count, phase=phase, allow_nul=dsn is None, drop_ts_mutated=moving
    )
    clock = Clock(seed, moving)
    llm = RecLLM(seed, delay)
    conns, tl = [], threading.local()
    ctx = Ctx(name, seed, llm=llm, clock=clock, max_running=max_running, ack_wait_s=ack_wait_s)
    ctx.decide = decide_moving if moving else decide_static
    if dsn is not None:
        from hadavin_sdk.store.postgres import PostgresStore, connect

        rt_conn, runner_conn = connect(dsn), connect(dsn)
        conns += [rt_conn, runner_conn]
        runtime_store, runner_store = PostgresStore(rt_conn), PostgresStore(runner_conn)

        def read_ref(rid):
            if not hasattr(tl, "conn"):
                tl.conn = psycopg.connect(dsn, autocommit=True)
                with ctx.lock:
                    conns.append(tl.conn)
            row = tl.conn.execute("SELECT trigger_ref FROM runs WHERE run_id = %s", (rid,)).fetchone()
            return row[0] if row else None

        def snapshot():
            if not hasattr(tl, "snap"):
                tl.snap = psycopg.connect(dsn, autocommit=True)
                with ctx.lock:
                    conns.append(tl.snap)
            found = tl.snap.execute(
                "SELECT run_id, agent_id, principal_id, trigger_ref FROM runs"
            ).fetchall()
            return {rid: (a, p, ref) for rid, a, p, ref in found}

        ctx.read_ref, ctx.snapshot = read_ref, snapshot
    else:
        raw = MemoryStore()
        runtime_store, runner_store = raw, raw
        if fault:
            rng = random.Random(seed)  # noqa: S311
            ctx.fault = FaultStore(raw, seed, rng.randint(60, 140), rng.randint(40, 70))
            runner_store, runtime_store = ctx.fault, SlowCreateStore(raw, seed)
        ctx.snapshot = lambda: mem_snapshot(raw)

        def read_ref(rid):
            with raw._lock:
                run = raw._runs.get(rid)
                return None if run is None else run.trigger_ref

        ctx.read_ref = read_ref
    ctx.wsgi, ctx.runner = make_stack2(
        tmp_path,
        runtime_store,
        runner_store,
        llm,
        max_running=max_running,
        ack_wait_s=ack_wait_s,
        max_waiting=max_waiting,
        clock=clock,
    )
    valid = {
        run_id_of(c.sender, c.key): (c.sender, c.key) for c in jobs if c.refusal is None
    }
    valid |= {
        run_id_of(c.sender, c.key): (c.sender, c.key)
        for c in (fresh_case(name, n) for n in range(max_running + 1))
    }
    signatures = {c.made_sig for c in jobs}
    try:
        with product_log() as lines:
            with sampling(ctx, valid, 0.01 if dsn is None else 0.05):
                drive(ctx, jobs, lambda case: op_inproc(ctx, case), threads)
            extra = finish(
                ctx, baseline, lambda case: op_inproc(ctx, case, retry=True), lines, signatures
            )
            fail_on_problems(ctx)
            rows = analyse(ctx, ctx.recs, valid)
            fail_on_problems(ctx)
            check_log(lines, signatures, f"[{name} seed={seed}]")
    finally:
        with contextlib.suppress(Exception):
            ctx.runner.close(0)
        for conn in conns:
            with contextlib.suppress(Exception):
                conn.close()
    captured = capsys.readouterr()
    assert captured.err == "", f"[{name} seed={seed}] I7 stderr: {captured.err[:400]!r}"
    detail = f"retried_503={extra['retried']}"
    if ctx.fault is not None:
        detail += (
            f" get_run_calls={ctx.fault.calls} raised={ctx.fault.raised} slowed={ctx.fault.slowed}"
        )
    if moving:
        detail += f" clock_calls={clock.calls} jumps={clock.jumps} backwards={clock.backwards}"
    summary(ctx, ctx.recs, rows, detail)
    return {"ctx": ctx, "rows": rows}


@pytest.mark.parametrize(
    ("slots", "ack", "waiting", "seed"),
    [(1, 0.3, 8, "c1-1"), (2, 0.5, 12, "c1-2"), (4, 1.0, 32, "c1-4")],
    ids=["max_running=1", "max_running=2", "max_running=4"],
)
def test_c1_memory_16_threads_hot_keys_and_slow_model(tmp_path, capsys, slots, ack, waiting, seed):
    got = run_layer(
        tmp_path,
        capsys,
        name=f"C1/{slots}",
        seed=SEEDS[seed],
        count=1000,
        threads=16,
        max_running=slots,
        ack_wait_s=ack,
        max_waiting=waiting,
    )
    recs = got["ctx"].recs
    assert len(recs) >= 1000 and overlap_keys(recs) > 0, "no key had overlapping requests"


def test_c1b_the_two_503_paths_held_open_by_hand(tmp_path):
    """The model is held shut: one run keeps the only slot. Two new keys wait for it, a third is
    refused at once (max_waiting 2, 503 and the store is not asked), the two waiting ones get 503 when
    ack_wait_s is over; no row is written for any of them. After the release the same three requests
    are acknowledged (I8)."""
    seed = SEEDS["c1b"]
    gate = threading.Event()
    llm = RecLLM(seed, delay=lambda _rng: 0.0, gate=gate)
    store = MemoryStore()
    baseline = {t.ident for t in threading.enumerate()}
    ctx = Ctx("C1b", seed, llm=llm, max_running=1, ack_wait_s=0.4, clock=Clock())
    ctx.decide, ctx.snapshot = decide_static, lambda: mem_snapshot(store)
    ctx.read_ref = lambda rid: (mem_snapshot(store).get(rid) or (0, 0, None))[2]
    wsgi, runner = make_stack2(
        tmp_path, store, store, llm, max_running=1, ack_wait_s=0.4, max_waiting=2, clock=ctx.clock
    )
    ctx.wsgi, ctx.runner = wsgi, runner
    cases = [fresh_case("c1b", n) for n in range(4)]
    out: dict[int, Rec] = {}
    done: list[threading.Thread] = []

    def send(n: int) -> None:
        out[n] = op_inproc(ctx, cases[n])

    try:
        with product_log() as lines:
            first = threading.Thread(target=send, args=(0,), name=f"{THREAD_NAME}-c1b-0")
            first.start()
            first.join(10)
            assert not first.is_alive() and out[0].status in OK, "the holding run was not acknowledged"
            for n in (1, 2):
                t = threading.Thread(target=send, args=(n,), name=f"{THREAD_NAME}-c1b-{n}")
                t.start()
                done.append(t)
            time.sleep(0.15)  # both are inside start, waiting for a slot
            began = time.monotonic()
            send(3)
            assert out[3].status == 503 and time.monotonic() - began < 0.2, "not refused at once"
            for t in done:
                t.join(10)
            assert not any(t.is_alive() for t in done), "a waiting request did not end"
            assert out[1].status == 503 and out[2].status == 503
            assert min(out[1].t1 - out[1].t0, out[2].t1 - out[2].t0) >= 0.35, "answered too early"
            assert max(out[1].t1 - out[1].t0, out[2].t1 - out[2].t0) < 3.0, "past its deadline"
            rows = mem_snapshot(store)
            for n in (1, 2, 3):
                assert run_id_of(cases[n].sender, cases[n].key) not in rows, "a 503 left a row"
            text = "\n".join(lines)
            assert "too many waiting requests" in text, "the max_waiting path was not taken"
            gate.set()
            settle(ctx)
            for n in (1, 2, 3):
                got = op_inproc(ctx, cases[n], retry=True)
                assert got.status in OK, f"I8 retry of case {n} got {got.status}"
            settle(ctx)
            fail_on_problems(ctx)
            check_log(lines, {c.made_sig for c in cases}, "[C1b]")
    finally:
        gate.set()
        runner.close()
    left = [t.name for t in threading.enumerate() if t.ident not in baseline and t.is_alive()]
    assert not left, f"threads left: {left}"
    say(
        "C1b: 4 requests, 503 at once (max_waiting) and 503 after ack_wait_s, no row written, "
        "retries acknowledged"
    )


# ---- C2: a failing and slow store ---------------------------------------------------------------


def test_c2_memory_slow_and_down_store_gives_503_and_recovers(tmp_path, capsys):
    got = run_layer(
        tmp_path,
        capsys,
        name="C2",
        seed=SEEDS["c2"],
        count=1300,
        threads=16,
        max_running=2,
        ack_wait_s=1.0,
        fault=True,
    )
    ctx = got["ctx"]
    assert ctx.fault.raised > 0, "the outage window was never reached"
    raised = [r for r in ctx.recs if r.raised]
    assert raised and all(r.status == 503 for r in raised), "an outage request was not a 503"
    assert ctx.fault.slowed > 20, "get_run was hardly ever slow"
    assert Counter(r.status for r in ctx.recs if r.retry)[503] == 0


# ---- C3: a moving clock -------------------------------------------------------------------------


def test_c3_memory_moving_clock_accepts_and_refuses_as_the_clock_it_saw_says(tmp_path, capsys):
    got = run_layer(
        tmp_path,
        capsys,
        name="C3",
        seed=SEEDS["c3"],
        count=1500,
        threads=16,
        max_running=2,
        ack_wait_s=1.0,
        moving=True,
    )
    recs = got["ctx"].recs
    inside = sum(1 for r in recs if r.reached)
    outside = sum(1 for r in recs if r.case.signed and not r.reached and r.status == 401)
    assert inside > 100 and outside > 100, f"the clock did not cross the window: {inside} {outside}"


# ---- C5: PostgreSQL -----------------------------------------------------------------------------


@pytest.fixture
def dsn():
    """A DSN on a fresh migrated schema; the schema is dropped afterwards."""
    yield from pg_schema()


def test_c5_postgresql_8_threads_hot_keys_rows_read_back_by_sql(dsn, tmp_path, capsys):
    got = run_layer(
        tmp_path,
        capsys,
        name="C5",
        seed=SEEDS["c5"],
        count=500,
        threads=8,
        max_running=2,
        ack_wait_s=3.0,
        dsn=dsn,
        delay=delays_short,
        phase=30,
    )
    sql = sql_snapshot(dsn)
    assert sql == got["rows"] and sql, "the rows by SQL are not the rows analysed"
    assert overlap_keys(got["ctx"].recs) > 0, "no key had overlapping requests"


# ---- C4: raw sockets, the real quiet server -----------------------------------------------------


def test_c4_raw_sockets_8_threads_against_the_quiet_server(tmp_path, capsys):
    seed = SEEDS["c4"]
    baseline = {t.ident for t in threading.enumerate()}
    base = wire_cases(seed, 330)
    jobs: list[WireCase] = []
    skipped = 0
    for wc in base:
        # a cut or dropped request whose bytes cut off only junk after the body is still complete
        if wc.kind in ("cut", "early-close") and wc.base is not None and wc.base.unread:
            skipped += 1
            continue
        jobs.append(wc)
        if wc.expect == "model" and wc.base.refusal is None:
            jobs.append(wc)  # the same request twice, at the same moment
    valid, maybe = {}, {}
    for wc in jobs:
        b = wc.base
        if b is not None and b.refusal is None and b.sender and b.key:
            who = (b.sender, b.key)
            (valid if wc.expect == "model" else maybe)[run_id_of(*who)] = who
    afterwards = [fresh_case("c4", n) for n in range(3)]
    allowed = valid | maybe | {run_id_of(c.sender, c.key): (c.sender, c.key) for c in afterwards}
    raw = MemoryStore()
    llm = RecLLM(seed, delays_short)
    ctx = Ctx("C4", seed, llm=llm, max_running=2, ack_wait_s=5.0, clock=Clock())
    ctx.decide, ctx.snapshot = decide_static, lambda: mem_snapshot(raw)

    def read_ref(rid):
        with raw._lock:
            run = raw._runs.get(rid)
            return None if run is None else run.trigger_ref

    ctx.read_ref = read_ref
    wsgi, runner = make_stack2(
        tmp_path, raw, raw, llm, max_running=2, ack_wait_s=5.0, clock=ctx.clock
    )
    ctx.wsgi, ctx.runner = wsgi, runner
    signatures = {wc.base.made_sig for wc in jobs if wc.base is not None}
    wire_recs: list[Rec] = []

    def work(wc: WireCase, port: int) -> None:
        b = wc.base
        where = wc.where(seed)
        rec = Rec(b if b is not None else Case(0, [], "", "", b"", "", "", "", "", []))
        rec.thread = threading.current_thread().name
        rec.t0 = time.monotonic()
        seen = exchange(port, wc)
        rec.t1 = time.monotonic()
        rec.status = seen.status or 0
        rec.reached = wc.expect == "model" and b.refusal is None
        rec.allowed = frozenset({b.refusal}) if b is not None and b.refusal is not None else frozenset()
        model = Model()
        model.expected = lambda case: (
            frozenset({case.refusal}) if case.refusal is not None else ACK_OR_REFUSAL
        )  # type: ignore[method-assign]
        try:
            check_wire(wc, seen, model, where)
            if rec.status not in ENDPOINT_STATUSES | SERVER_STATUSES and seen.raw:
                raise AssertionError(f"I1 unknown status {rec.status}")
            if wc.expect == "model" and rec.reached:
                check_row(ctx, b, rec.status)
        except AssertionError as exc:
            ctx.problem(None, f"{where} {exc}")
        with ctx.lock:
            wire_recs.append(rec)

    try:
        with product_log() as lines:
            with serving(wsgi) as server:
                port = server.server_port
                with sampling(ctx, allowed, 0.01):
                    drive(ctx, jobs, lambda wc: work(wc, port), 8)
                settle(ctx)
                fresh_status = []
                for c in afterwards:  # the pool is free: a valid request is acknowledged
                    one = WireCase(0, "afterwards", c, render(c, random.Random(seed)))  # noqa: S311
                    seen = exchange(port, one)
                    fresh_status.append(seen.status)
                    signatures.add(c.made_sig)
                    check_row(ctx, c, seen.status or 0)
                retry_503s = 0
                for rec in list(wire_recs):  # I8
                    if rec.status == 503 and rec.reached:
                        retry_503s += 1
                        again = exchange(port, next(w for w in jobs if w.base is rec.case))
                        if again.status not in OK | {409}:
                            ctx.problem(rec.case, f"I8 the retry of a 503 got {again.status}")
                settle(ctx)
            runner.close()
            left = [t.name for t in threading.enumerate() if t.ident not in baseline]
            assert not left, f"I7 threads left: {left}"
            assert all(s in OK for s in fresh_status), f"I7 afterwards: {fresh_status}"
            fail_on_problems(ctx)
            ctx.recs = [r for r in wire_recs if r.reached]
            rows = analyse(ctx, ctx.recs, {**maybe, **allowed})
            fail_on_problems(ctx)
            check_log(lines, signatures, f"[C4 seed={seed}]")
    finally:
        with contextlib.suppress(Exception):
            runner.close(0)
    captured = capsys.readouterr()
    assert captured.err == "", f"[C4 seed={seed}] I7 stderr: {captured.err[:400]!r}"
    assert captured.out == "", f"[C4 seed={seed}] stdout: {captured.out[:400]!r}"
    codes = Counter(r.status for r in wire_recs)
    line = ", ".join(f"{c}:{n}" for c, n in sorted(codes.items()))
    say(
        f"C4 seed={seed}: sent={len(wire_recs)} (skipped {skipped}) valid={len(ctx.recs)} "
        f"({len(ctx.recs) / max(len(wire_recs), 1):.0%}) rows={len(rows)} "
        f"overlapping_keys={overlap_keys(ctx.recs)} no_answer={codes[0]} "
        f"retried_503={retry_503s} statuses[{line}]"
    )
    assert len(wire_recs) >= 400, f"only {len(wire_recs)} requests were sent"
    assert overlap_keys(ctx.recs) > 5


# ---- C6: close under load -----------------------------------------------------------------------


def test_c6_runner_close_under_load(tmp_path, capsys):
    seed = SEEDS["c6"]
    baseline = {t.ident for t in threading.enumerate()}
    jobs = build_jobs(seed, 2500, phase=25)
    raw = MemoryStore()
    llm, clock = RecLLM(seed, delays_mixed), Clock()
    ctx = Ctx("C6", seed, llm=llm, clock=clock, max_running=2, ack_wait_s=2.0)
    ctx.decide, ctx.snapshot = decide_static, lambda: mem_snapshot(raw)

    def read_ref(rid):
        with raw._lock:
            run = raw._runs.get(rid)
            return None if run is None else run.trigger_ref

    ctx.read_ref = read_ref
    ctx.wsgi, ctx.runner = make_stack2(
        tmp_path, raw, raw, llm, max_running=2, ack_wait_s=2.0, max_waiting=32, clock=clock
    )
    valid = {run_id_of(c.sender, c.key): (c.sender, c.key) for c in jobs if c.refusal is None}
    after = [fresh_case("c6", n) for n in range(4)]
    valid |= {run_id_of(c.sender, c.key): (c.sender, c.key) for c in after}
    signatures = {c.made_sig for c in jobs} | {c.made_sig for c in after}
    closing: dict[str, float] = {}
    try:
        with product_log() as lines:
            with sampling(ctx, valid, 0.01):
                problems: list[BaseException] = []

                def guarded() -> None:
                    try:
                        drive(ctx, jobs, lambda case: op_inproc(ctx, case), 8)
                    except BaseException as exc:  # noqa: BLE001
                        problems.append(exc)

                senders = threading.Thread(target=guarded, name=f"{THREAD_NAME}-c6-main", daemon=True)
                senders.start()
                deadline = time.monotonic() + 30
                while len(ctx.recs) < 300 and time.monotonic() < deadline:
                    time.sleep(0.005)
                began = time.monotonic()
                ctx.runner.close(wait_s=15.0)
                closing["end"] = time.monotonic()
                closing["took"] = closing["end"] - began
                frozen = mem_snapshot(raw)  # every loop has ended: no row appears after this
                senders.join(DRIVE_TIMEOUT_S)
                assert not senders.is_alive(), "the senders did not end"
            assert not problems, f"the drive failed: {problems[0]!r}"
            assert closing["took"] < 15.0, f"close took {closing['took']:.1f} s"
            late, late_503 = 0, 0
            for rec in ctx.recs:
                latency = rec.t1 - rec.t0
                if latency > ctx.ack_wait_s + 2.5:
                    ctx.problem(rec.case, f"a request took {latency:.1f} s")
                if rec.reached and rec.t0 > closing["end"]:
                    late += 1
                    rid = run_id_of(rec.case.sender, rec.case.key)
                    if rid in frozen and rec.status not in OK | {409}:
                        ctx.problem(rec.case, f"after close a row exists and the answer is {rec.status}")
                    if rid not in frozen:
                        late_503 += 1
                        if rec.status != 503:
                            ctx.problem(rec.case, f"after close a new key got {rec.status}")
            for case in after:  # new requests after close: 503, no row, no loop
                got = op_inproc(ctx, case)
                if got.status != 503:
                    ctx.problem(case, f"after close a fresh request got {got.status}")
            assert late_503 > 0, "no new key arrived after the close"
            assert mem_snapshot(raw) == frozen, "a row appeared after close had returned"
            fail_on_problems(ctx)
            rows = analyse(ctx, ctx.recs, valid)
            fail_on_problems(ctx)
            check_log(lines, signatures, f"[C6 seed={seed}]")
    finally:
        with contextlib.suppress(Exception):
            ctx.runner.close(0)
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        left = [t.name for t in threading.enumerate() if t.ident not in baseline and t.is_alive()]
        if not left:
            break
        time.sleep(0.02)
    assert not left, f"I7 threads left: {left}"
    captured = capsys.readouterr()
    assert captured.err == "", f"[C6 seed={seed}] I7 stderr: {captured.err[:400]!r}"
    summary(
        ctx,
        ctx.recs,
        rows,
        f"close_took={closing['took']:.2f}s requests_after_close={late} new_keys_after_close={late_503}",
    )
