"""The worker half of the signed trigger endpoint: one process that serves the endpoint and runs the agent loop.

`Runner.start` is what the endpoint calls for a verified request. It answers 2xx only after the store has returned
the run row and that row is for the same agent, principal and `trigger_ref` (same sender, key and document). The
answer is always decided from the ROW, never from which exception the loop raised. 202 = the run is RECEIVED or
WORKING, 200 = any later state, 409 = a row exists for the same key but another document (no run is written;
one `trigger.conflict` audit event with ids and both payload hashes, at most `triggers.conflict_events_per_minute` per sender per minute (10 only for a directly built Runner), see `_conflict`),
503 = store not reachable, or no row within `ack_wait_s` (not acknowledged; send again with the same key; it
may already be running). A request that finds no free slot is not refused at once: it waits for the row like any other, because another
request for the same key may be writing it right now. While it waits it looks for a free slot and for the row
at each look, and takes a free slot at its next look; the looks come less and less often (the pause doubles up to
one second, about ten reads in five seconds);
with neither a slot nor a row by the end of `ack_wait_s` it gets 503. At most
one run per key rests on the primary key of the runs table, and every answer on the stored row: nothing in this
process remembers keys. At most `max_waiting` requests are inside `start` at one time; one more is answered
503 at once and the store is not asked (a store that hangs must not pile up request threads without end).

Several threads at once: what was read, and what was not
- `Runtime` keeps no per-run state on itself: its fields are set once in `__init__` (runtime/agent_loop.py:208-213)
  and a run's working data are locals of `handle` (396-398).
- The memory store takes one lock for every method that reads or writes rows (store/memory.py:31, 52, 58, 64);
  `create_run` checks and inserts under that lock, so of two calls with one run id exactly one wins.
- The call that loses gets `StaleState`, and `handle` then returns the stored run without any work when agent,
  principal and `trigger_ref` are equal, else raises `StaleState` again (agent_loop.py:335-349, 388-393). Two
  parallel `start` calls with one key therefore give one row and one loop.
- The local audit sink writes under a lock (audit/local_dir.py:30, 82); the recorded model double too (llm/fake.py:27).
- Spend: with core-b's limits the main call reserves the worst case before and settles after (agent_loop
  reserve/settle), so parallel runs cannot overshoot through the main call; the ungated sites (document screen,
  shadow cards, k1b/evals) are still charged after the fact. Without core-b's limits (this branch alone) the budget
  is read before a model call and the cost is added after it (limits.py:17-30), so N runs of one agent in parallel
  can pass a budget by up to N calls. `max_running` comes from the configuration only (no default here), and a
  configured value above 1 is warned about at start as long as the runtime's limits object has no `reserve` method.
- NOT READ, so not shown safe: the real model clients, the detector, the read tools, the card channel, the
  PostgreSQL store and the chain audit under threads. With `max_running` 1 only one loop runs at a time, but the
  short `get_run` reads of request threads still run next to it.
- `handle` runs on a pool thread. If it raises, the class name is logged and nothing else; the process goes on and
  a run that was cut off is ended by the tick's stuck step, so the tick MUST run in the deployment.
  What the sender gets then: acknowledged, then NEEDS_PERSON with no notification and no stored document; the sender
  must poll the run state. This is not "never lost" and not "handed to a person".

Deployment conditions (door review M2, M3)
- A reverse proxy with per-peer connection limits is required in front of this server: it has 256 global slots and no
  per-peer limit.
- One secret per tenant and per stage: the tenant is not part of the signed string, so a shared secret makes a request
  for one tenant or stage valid for another within the 300 second window.

Start: `python -m hadavin_sdk.triggers.worker --config-dir <dir> [--host H] [--port P] [--allow-non-loopback]`.
The stdlib server is not hardened: by default it listens on 127.0.0.1 only (a host that is not loopback needs
`--allow-non-loopback`, see `check_bind`), and TLS is the job of the proxy in front of it.

Settings: core-b's `config.triggers` (`TriggerSettings`) has `tenant`, `senders` (a mapping of sender id to
sender; a sender has `secret_names`, `agent_id`, `principal_id`), `max_body_bytes`, `max_running`,
`conflict_events_per_minute` and `ack_wait_s`, and these are read by direct access: a config object without one is a start failure, not a
default. `host`, `port` and `allow_non_loopback` are command-line options (127.0.0.1, 8081, off); `poll_s` and
`max_waiting` are the constants `POLL_S` and `MAX_WAITING` (arguments of `make_app` for a test). The secrets are
read through `App.trigger_secret`.
"""

from __future__ import annotations

import argparse
import ipaddress
import logging
import re
import signal
import sys
import threading
import time
from collections.abc import Callable, Iterable, Mapping
from concurrent.futures import Future, ThreadPoolExecutor
from concurrent.futures import wait as wait_all
from pathlib import Path
from typing import Any, Final, Self
from wsgiref.simple_server import WSGIServer

from hadavin_sdk.errors import ConfigError as AnyConfigError
from hadavin_sdk.models import AuditEvent, Run, RunState, now
from hadavin_sdk.store.protocol import (
    NotFound,
    StaleState,
    StoreUnavailable,
    is_connectivity_error,
)
from hadavin_sdk.triggers.endpoint import (
    PATH,
    Accepted,
    check_secrets,
    health_only_app,
    make_wsgi,
    sender_map,
)
from hadavin_sdk.triggers.server import (
    MAX_CONNECTIONS,
    READ_DEADLINE_S,
    QuietRequestHandler,
    QuietServer,
)

POLL_S: Final[float] = 0.05  # how often `start` looks for the row while it waits
NO_SLOT_POLL_CAP_S: Final[float] = 1.0  # with no free slot the wait doubles from POLL_S up to this
POLL_S_MIN: Final[float] = 0.01
POLL_S_MAX: Final[float] = 1.0
# `max_running` has NO number here: it is read from `config.triggers.max_running` (core-b's `TriggerSettings`, filled
# from `defaults.TRIGGER_MAX_RUNNING`), the one source (d-fix22). See the module text on spend and parallel runs.
# The values of `defaults.TRIGGER_MAX_RUNNING_CEILING`, `TRIGGER_ACK_WAIT_S` and `TRIGGER_ACK_WAIT_S_CEILING`
# (core-b); a test compares them where `defaults` has them.
MAX_RUNNING_CEILING: Final[int] = 64
ACK_WAIT_S: Final[float] = 5.0
ACK_WAIT_S_CEILING: Final[float] = 30.0
# Requests inside `start` at one time (the first store read counts: a store that hangs blocks right there); one
# more is answered 503 at once. Above 50 so that 50 parallel requests of one key all get their answer.
MAX_WAITING: Final[int] = 128
CLOSE_WAIT_S: Final[float] = 30.0  # how long `close` waits for running loops
SOCKET_SLACK_S: Final[float] = 10.0  # a connection may stay open ack_wait_s plus this
READ_DEADLINE_S_CEILING: Final[float] = 300.0
MAX_CONNECTIONS_CEILING: Final[int] = 4096
LOOPBACK: Final[str] = "127.0.0.1"
PORT: Final[int] = 8081
TRIGGER_KIND: Final[str] = "event"
STUCK_STEP: Final[str] = "stuck"  # the tick step that ends a cut-off run
TICK_MAX_AGE_S: Final[float] = 600.0  # a good "stuck" tick older than this is warned about at start
IN_PROGRESS: Final[frozenset[RunState]] = frozenset({RunState.RECEIVED, RunState.WORKING})
NO_ACK: Final[tuple[int, dict[str, str]]] = (503, {})
CONFLICT: Final[tuple[int, dict[str, str]]] = (409, {})
EXIT_OK, EXIT_CONFIG, EXIT_FAILED = 0, 2, 3
# A signed 409 is written to the audit as `trigger.conflict` (domain "trigger", operation "conflict"; the chain
# audit stores `domain.operation` as the entry kind). At most this many per sender per minute: the 409 is still
# answered, the extra events are only counted. `make_app` reads the number from `config.triggers.
# conflict_events_per_minute` (core-b's `TriggerSettings`, d-fix24) and passes it on; this constant is only the value
# of a Runner built directly (tests, library use), never what the worker uses.
CONFLICT_EVENTS_PER_MINUTE: Final[int] = 10
CONFLICT_WINDOW_S: Final[float] = 60.0
CONFLICT_DOMAIN: Final[str] = "trigger"
CONFLICT_OPERATION: Final[str] = "conflict"
AUDIT_WRITE_TIMEOUT_S: Final[float] = (
    2.0  # a request waits this long for its conflict audit write, then the 409 goes out anyway
)
DEGRADED_WARN_EVERY_S: Final[float] = (
    300.0  # a degraded worker logs its re-check failure class at most this often (and when it changes)
)
HASH_RE: Final = re.compile(r"[0-9a-f]{64}")
PING_RUN_ID: Final[str] = (
    "run-" + "0" * 32
)  # a run id that is never stored: the cheapest store call is get_run

HEALTH_RECHECK_S: Final[float] = (
    5.0  # a worker that started with the store down asks the store this often
)
HEALTH_PING_TIMEOUT_S: Final[float] = (
    2.0  # the /health store ping is given this long, then it is "down"
)

_LOG = logging.getLogger("hadavin_sdk.triggers")


def _monotonic() -> float:
    """The clock of the degraded re-check's WARNING rate limit (a function so a test can patch it)."""
    return time.monotonic()


class ConfigError(AnyConfigError):
    """A start refusal written in THIS file: its text is built here from ids and bounds, so `main` prints it.
    Any other config or store error is printed by class name only (its text could hold a value)."""


# What a store raises when it answered and the answer is a refusal. A database driver's own error classes are
# recognised by module name (no driver import here).
STORE_ERRORS: Final[tuple[type[BaseException], ...]] = (StoreUnavailable, StaleState, NotFound)
STORE_ERROR_MODULES: Final[tuple[str, ...]] = ("psycopg", "sqlite3")


def is_store_error(exc: BaseException) -> bool:
    """True for an error that comes from the store: not reachable, or reached and refusing."""
    if isinstance(exc, STORE_ERRORS) or is_connectivity_error(exc):
        return True
    return any(c.__module__.split(".")[0] in STORE_ERROR_MODULES for c in type(exc).__mro__)


class Runner:
    """Starts at most `max_running` agent loops at a time and tells the endpoint what to answer.

    `store_failures` counts store errors on request paths and failed or timed-out `/health` pings. A degraded
    worker builds a new Runner when the store is back, so the count restarts at zero after that swap (the
    `/health` answer then reports the new Runner's count). Concurrent `health` callers that wait on one hung
    ping each count a failure when their 2 s run out, so a burst of calls adds one per caller, not one per ping."""

    def __init__(
        self,
        runtime: Any,
        store: Any,
        max_running: int,
        ack_wait_s: float = ACK_WAIT_S,
        *,
        poll_s: float = POLL_S,
        max_waiting: int = MAX_WAITING,
        audit: Any = None,
        conflict_events_per_minute: int = CONFLICT_EVENTS_PER_MINUTE,
        rate_clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if isinstance(max_running, bool) or not isinstance(max_running, int):
            raise ValueError("max_running must be a whole number")  # noqa: TRY004 - `make_app` turns it into a config error
        if isinstance(ack_wait_s, bool) or not isinstance(ack_wait_s, int | float):
            raise ValueError("ack_wait_s must be a number")  # noqa: TRY004 - same as above
        if isinstance(poll_s, bool) or not isinstance(poll_s, int | float):
            raise ValueError("poll_s must be a number")  # noqa: TRY004 - same as above
        if max_running < 1 or poll_s <= 0:
            raise ValueError("max_running and poll_s must be above zero")
        if max_running > MAX_RUNNING_CEILING:
            raise ValueError(f"max_running must be at most {MAX_RUNNING_CEILING}")
        if not (0 < ack_wait_s <= ACK_WAIT_S_CEILING):  # written so that NaN is refused too
            raise ValueError(f"ack_wait_s must be above zero and at most {ACK_WAIT_S_CEILING:g}")
        if not POLL_S_MIN <= poll_s <= POLL_S_MAX:
            raise ValueError(f"poll_s must be between {POLL_S_MIN:g} and {POLL_S_MAX:g}")
        if isinstance(max_waiting, bool) or not isinstance(max_waiting, int) or max_waiting < 1:
            raise ValueError("max_waiting must be a whole number above zero")
        if (
            isinstance(conflict_events_per_minute, bool)
            or not isinstance(conflict_events_per_minute, int)
            or conflict_events_per_minute < 1
        ):
            raise ValueError("conflict_events_per_minute must be a whole number above zero")
        self._runtime, self._store = runtime, store
        self._audit, self._cap, self._rate_clock = audit, conflict_events_per_minute, rate_clock
        self._stats_lock = threading.Lock()  # guards the counters and the conflict windows
        self._store_failures = 0
        self._conflict_windows: dict[
            str, tuple[float, int]
        ] = {}  # sender -> (window start, events seen)
        self._conflicts_dropped = 0
        self._audit_pending = (
            False  # one conflict audit write may be pending (guarded by _stats_lock)
        )
        self._last_drop_warning: float | None = None
        self._ack_wait_s, self._poll_s = float(ack_wait_s), float(poll_s)
        self._slots = threading.BoundedSemaphore(max_running)
        self._waiting = threading.BoundedSemaphore(max_waiting)  # requests inside `start`
        self._pool = ThreadPoolExecutor(max_workers=max_running, thread_name_prefix="trigger-run")
        self._lock = threading.Lock()  # guards _jobs and _closed
        self._jobs: set[Future[None]] = set()  # handle calls not yet ended, for `close` only
        self._closed = False
        self._ping_lock = threading.Lock()  # guards _ping
        self._ping: _Ping | None = None  # the one ping thread that may be pending
        self.owned_app: Any = (
            None  # set by `_recover`: the App whose connection a late close must also close
        )

    @property
    def ack_wait_s(self) -> float:
        """The wait for a row, in seconds, as checked and stored at construction (read-only)."""
        return self._ack_wait_s

    @property
    def store_failures(self) -> int:
        """Store errors seen on request paths and by the /health ping since start."""
        with self._stats_lock:
            return self._store_failures

    @property
    def conflict_events_dropped(self) -> int:
        """409 events over the per-sender cap: answered, not written to the audit, only counted."""
        with self._stats_lock:
            return self._conflicts_dropped

    def health(self) -> tuple[bool, int]:
        """(store is up, store failures since start) for ``GET /health``. The ping is `get_run` of an id that is
        never stored: NotFound is the store answering; any other error is a failure and is counted.

        The ping runs in its own thread and is given `HEALTH_PING_TIMEOUT_S`; one that does not return in time is
        "down" and is counted. At most one ping thread is pending: while it is, a new call waits for that same
        ping (it starts no second one), so a hung store costs one thread, not one per call."""
        with self._ping_lock:
            ping = self._ping
            if ping is None or ping.done.is_set():
                fresh = _Ping(self._store, self._count_store_failure)
                try:
                    fresh.thread.start()
                except Exception as exc:  # noqa: BLE001 - e.g. "can't start new thread": down, counted
                    self._count_store_failure()
                    _LOG.warning(
                        "trigger health: ping thread did not start (%s)", type(exc).__name__
                    )
                    return False, self.store_failures
                ping = self._ping = (
                    fresh  # assigned only after the thread runs: no wait on a dead ping
                )
        if not ping.done.wait(HEALTH_PING_TIMEOUT_S):
            self._count_store_failure()
            _LOG.debug("trigger health: store ping did not return in time")
            return False, self.store_failures
        return ping.up, self.store_failures

    def _count_store_failure(self) -> None:
        with self._stats_lock:
            self._store_failures += 1

    @property
    def running(self) -> int:
        """How many agent loops have not ended (the ones `close` would wait for)."""
        with self._lock:
            return len(self._jobs)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def close(self, wait_s: float = CLOSE_WAIT_S) -> None:
        """Take no new work, drop work that has not begun, wait up to `wait_s` for running loops.

        From this call on `start` begins no loop: a key with no row gets 503, a key whose row exists is still
        answered from that row. A loop that is already running is NOT cut off: it runs to its end, also after
        `wait_s` has passed (its thread then keeps the process alive until it ends). May be called twice.

        When loops are still running after `wait_s`, one WARNING line gives their number. The operator must
        give the process a grace period longer than the longest run: a process that is killed before a loop
        has ended leaves that run cut off, and its key then ends as "interrupted" with a person."""
        with self._lock:
            self._closed = True
            jobs = list(self._jobs)
        self._pool.shutdown(wait=False, cancel_futures=True)
        going = len(wait_all(jobs, timeout=wait_s).not_done)
        if going:
            _LOG.warning(
                "trigger worker: %d run(s) still going after the close wait; a kill now cuts them off"
                " (the grace period must be longer than the longest run)",
                going,
            )

    def start(self, req: Accepted) -> tuple[int, dict[str, str]]:
        """The status and answer body for one verified request. Never raises for a store or loop failure.
        With `max_waiting` requests already in here the answer is 503 at once and the store is not asked."""
        if not self._waiting.acquire(blocking=False):
            _LOG.warning("trigger start: too many waiting requests, refused")
            return NO_ACK
        try:
            return self._decide(req)
        finally:
            self._waiting.release()

    def _decide(self, req: Accepted) -> tuple[int, dict[str, str]]:
        try:
            found = self._row(req.run_id)
            if found is not None:
                return self._answered(found, req)
            job, closed = self._submit(req)
            if closed:
                return NO_ACK
            # job None = no free slot: wait for the row all the same, another request may be writing it.
            deadline = time.monotonic() + self._ack_wait_s
            pause, pause_cap = self._poll_s, max(self._poll_s, NO_SLOT_POLL_CAP_S)
            while True:
                # read BEFORE the row, so one look at the row follows the end of the loop
                ended = job is not None and job.done()
                found = self._row(req.run_id)
                if found is not None:
                    return self._answered(found, req)
                left = deadline - time.monotonic()
                if ended or left <= 0:
                    return NO_ACK  # the loop ended with no row, or the wait is over: no ack
                if job is None:  # no slot so far: take a free one, else look less often
                    if self._closed:
                        return NO_ACK  # closed while it waited: no loop begins here any more
                    job = self._submit(req)[0]
                    pause = self._poll_s if job is not None else min(pause * 2, pause_cap)
                time.sleep(min(pause, left))
        except Exception as exc:  # noqa: BLE001 - no ack in every case, the sender retries
            if is_store_error(exc):
                self._count_store_failure()
                what = "store unreachable" if is_connectivity_error(exc) else "store error"
                _LOG.warning("trigger start: %s (%s)", what, type(exc).__name__)
            else:  # a bug, not the store: a retry will not help, so it must stand out in the log
                _LOG.error("trigger start: internal error (%s)", type(exc).__name__)
            return NO_ACK

    def _answered(self, found: Run, req: Accepted) -> tuple[int, dict[str, str]]:
        reply = _answer(found, req)
        if reply is CONFLICT:
            self._conflict(found, req)
        return reply

    def _conflict(self, found: Run, req: Accepted) -> None:
        """A signed 409 is a forensic fact: one audit event, hashes only, at most `cap` per sender per minute.
        Beyond the cap, or while another audit write is still pending, the event is only counted, with one
        WARNING per minute. The write runs on its own daemon thread and the request waits at most
        `AUDIT_WRITE_TIMEOUT_S` for it; at most one write is pending. Never raises."""
        at = self._rate_clock()
        warn = False
        reason = ""
        with self._stats_lock:
            start, seen = self._conflict_windows.get(req.sender, (at, 0))
            if at - start >= CONFLICT_WINDOW_S or at < start:
                start, seen = at, 0
            seen += 1
            self._conflict_windows[req.sender] = (start, seen)
            if seen > self._cap:
                reason = f"over the cap of {self._cap} per minute for sender {req.sender}"
            elif self._audit is not None and self._audit_pending:
                reason = "an audit write is still pending"
            elif self._audit is not None:
                self._audit_pending = True
            if reason:
                self._conflicts_dropped += 1
                last = self._last_drop_warning
                if last is None or at - last >= CONFLICT_WINDOW_S or at < last:
                    self._last_drop_warning, warn = at, True
                dropped = self._conflicts_dropped
        if reason:
            if warn:
                _LOG.warning(
                    "trigger conflict events %s: %d not written so far (the 409 is still answered)",
                    reason,
                    dropped,
                )
            return
        if self._audit is None:
            return
        try:
            event = _conflict_event(found, req)
        except Exception as exc:  # noqa: BLE001 - the flag was set above: reset it, the 409 stands
            with self._stats_lock:
                self._audit_pending = False
            _LOG.warning("trigger conflict: audit event not built (%s)", type(exc).__name__)
            return
        done = threading.Event()

        def write() -> None:
            try:
                self._audit.write_outcome(event)
            except Exception as exc:  # noqa: BLE001 - the 409 stands whatever the audit does
                _LOG.warning("trigger conflict: audit write failed (%s)", type(exc).__name__)
            finally:
                with self._stats_lock:
                    self._audit_pending = False
                done.set()

        try:
            threading.Thread(target=write, name="trigger-audit", daemon=True).start()
        except Exception as exc:  # noqa: BLE001 - no thread: not written, the 409 stands
            with self._stats_lock:
                self._audit_pending = False
            _LOG.warning("trigger conflict: audit thread did not start (%s)", type(exc).__name__)
            return
        if not done.wait(AUDIT_WRITE_TIMEOUT_S):
            _LOG.warning("trigger conflict: audit write did not return in time; the 409 goes out")

    @property
    def audit_pending(self) -> bool:
        """True while a conflict audit write has not returned (at most one at a time)."""
        with self._stats_lock:
            return self._audit_pending

    def _row(self, run_id: str) -> Run | None:
        try:
            return self._store.get_run(run_id)
        except NotFound:
            return None

    def _submit(self, req: Accepted) -> tuple[Future[None] | None, bool]:
        """(the new handle call, or None when no slot is free; True when the Runner is closed)."""
        with self._lock:
            if self._closed:
                return None, True
            if not self._slots.acquire(blocking=False):
                return None, False
            try:
                job = self._pool.submit(self._run, req)
            except BaseException:
                self._slots.release()
                raise
            self._jobs.add(job)
        # Outside the lock: a job that has already ended runs the callback at once, in this thread.
        job.add_done_callback(self._ended)
        return job, False

    def _ended(self, job: Future[None]) -> None:
        """The slot is given back only here, when the loop has ended (or was dropped by `close`)."""
        with self._lock:
            self._jobs.discard(job)
        self._slots.release()
        # `_run` logs an Exception itself, so what is left here is a BaseException (or a failure outside `_run`).
        exc = None if job.cancelled() else job.exception()
        if exc is not None:
            level = logging.WARNING if isinstance(exc, Exception) else logging.ERROR
            _LOG.log(level, "trigger run: the loop thread ended with %s", type(exc).__name__)

    def _run(self, req: Accepted) -> None:
        try:
            self._runtime.handle(
                req.agent_id,
                req.principal_id,
                req.document,
                trigger_kind=TRIGGER_KIND,
                trigger_ref=req.trigger_ref,
                run_id=req.run_id,
            )
        except Exception as exc:  # noqa: BLE001 - never takes the process down; the tick ends a cut-off run
            _LOG.warning("trigger run %s: loop raised %s", req.run_id, type(exc).__name__)


class _Ping:
    """One store ping on its own daemon thread; `done` is set when it has returned, `up` is the answer."""

    def __init__(self, store: Any, on_failure: Callable[[], None]) -> None:
        self.done = threading.Event()
        self.up = False
        self._store, self._on_failure = store, on_failure
        self.thread = threading.Thread(target=self._run, name="trigger-ping", daemon=True)

    def _run(self) -> None:
        try:
            try:
                self._store.get_run(PING_RUN_ID)
            except NotFound:
                pass
            self.up = True
        except Exception as exc:  # noqa: BLE001 - down in every case; the class name only
            self._on_failure()
            _LOG.debug("trigger health: store ping failed (%s)", type(exc).__name__)
        finally:
            self.done.set()


def _hash_of(ref: object) -> str:
    """The payload hash of a trigger_ref (`sender/key#sha256`), or `-` when the text is not that shape."""
    tail = str(ref).rpartition("#")[2]
    return tail if HASH_RE.fullmatch(tail) else "-"


def _conflict_event(found: Run, req: Accepted) -> AuditEvent:
    """Hashes and ids only: the sender (in `source`), the key (`object_ref`), the new request's payload hash
    (`inputs_hash`) and the stored one (`output_hash`). Never the payload and never the signature (this module
    never sees it: it is not on `Accepted`)."""
    ref = req.trigger_ref
    key = ref.partition("/")[2].rpartition("#")[0]
    return AuditEvent(
        run_id=req.run_id,
        domain=CONFLICT_DOMAIN,
        operation=CONFLICT_OPERATION,
        principal=req.principal_id,
        source=f"trigger:{req.sender}",
        object_ref=key,
        inputs_hash=_hash_of(ref),
        output_hash=_hash_of(found.trigger_ref),
        result="conflict",
    )


def _answer(found: Run, req: Accepted) -> tuple[int, dict[str, str]]:
    """Decided from the stored row alone: 409 for a foreign row, else 202 while in progress and 200 after."""
    if (
        found.agent_id != req.agent_id
        or found.principal_id != req.principal_id
        or found.trigger_ref != req.trigger_ref
    ):
        _LOG.warning("trigger status=409 sender=%s run=%s", req.sender, req.run_id)
        return CONFLICT
    state = RunState(found.state)
    return (202 if state in IN_PROGRESS else 200), {"run_id": found.run_id, "state": state.value}


def _field(obj: Any, name: str, where: str) -> Any:
    """`obj.name` by direct access, or a ConfigError that names the field when core-b's object lacks it (the text is
    built here from names, never from a value)."""
    try:
        return getattr(obj, name)
    except AttributeError:
        raise ConfigError(
            f"{where} is missing: the config or App of core-b has no `{name}`"
        ) from None


def check_fields(settings: Any) -> None:
    """The fields core-b's `TriggerSettings` must have and that are read by direct access: a ConfigError when one is
    missing. Run by `_build_app` before the store is built, so this error never depends on the store being up."""
    for name in ("max_running", "conflict_events_per_minute"):
        if not hasattr(settings, name):
            raise ConfigError(f"triggers.{name} missing: core-b TriggerSettings required")


def trigger_settings(config: Any) -> Any:
    """`config.triggers`, or a ConfigError when the block is missing (or the field is not on the config)."""
    settings = _field(config, "triggers", "config.triggers")
    if settings is None:
        raise ConfigError("triggers block not configured (config.yaml has no `triggers:`)")
    return settings


def sender_list(settings: Any) -> list[tuple[str, Any]]:
    """(sender id, sender) pairs of `settings.senders`, through the one helper of the endpoint."""
    try:
        return list(sender_map(settings.senders).items())
    except ValueError as exc:  # a sender id listed twice: the text names the id
        raise ConfigError(str(exc)) from None


def check_senders(
    senders: list[tuple[str, Any]], agents: Iterable[str], principals: Mapping[str, Any]
) -> None:
    """Every sender runs as a qualified agent and as a principal of kind service, or the worker does not start."""
    qualified = set(agents)
    for sender_id, sender in senders:
        if sender.agent_id not in qualified:
            raise ConfigError(
                f"trigger sender {sender_id}: agent {sender.agent_id} is not qualified"
            )
        principal = principals.get(sender.principal_id)
        if principal is None:
            raise ConfigError(
                f"trigger sender {sender_id}: principal {sender.principal_id} is not in principals.yaml"
            )
        if _field(principal, "kind", f"principal {sender.principal_id} kind") != "service":
            raise ConfigError(
                f"trigger sender {sender_id}: principal {sender.principal_id} is not of kind service"
            )


def read_secrets(
    senders: list[tuple[str, Any]], resolve: Callable[[str], str]
) -> dict[str, tuple[str, ...]]:
    """The secret values of each sender, read once by name. A failure names the sender, never a value."""
    out: dict[str, tuple[str, ...]] = {}
    for sender_id, sender in senders:
        names = list(sender.secret_names)
        if len(names) > 1:
            _LOG.warning(
                "trigger sender %s accepts %d secrets: finish the swap", sender_id, len(names)
            )
        try:
            out[sender_id] = tuple(resolve(name) for name in names)
        except Exception as exc:  # noqa: BLE001 - any provider failure stops the start
            raise ConfigError(
                f"trigger sender {sender_id}: a secret could not be read ({type(exc).__name__})"
            ) from None
    return out


def check_bind(host: str, allow_non_loopback: bool) -> None:
    """Refuse a host that is not loopback unless the command-line flag `--allow-non-loopback` was given
    (`allow_non_loopback` is that flag, not a config setting). A host must be an IPv4
    address or the name localhost: any other text (an empty one would mean every interface) is refused, and
    so is every IPv6 address, the loopback one too, because the server opens an IPv4 socket only."""
    if host == "localhost":
        return
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        raise ConfigError("--host must be an IP address or localhost") from None
    if address.version != 4:
        raise ConfigError("--host is an IPv6 address: the server listens on IPv4 only")
    loopback = address.is_loopback
    if not loopback and allow_non_loopback is not True:
        raise ConfigError(
            f"--host {host} is not loopback: pass --allow-non-loopback to listen there"
        )


def secret_reader(app: Any) -> Callable[[str], str]:
    """The reader of sender secrets the App was built with: `App.trigger_secret`, a callable from a secret NAME
    to its value that refuses every name no sender lists (PermissionError). Without a reader the worker does
    not start."""
    return _field(app, "trigger_secret", "App.trigger_secret")  # type: ignore[no-any-return]


def check_durable(store: Any) -> bool:
    """False, with one warning, when the store keeps its rows in this process only. Never stops the start."""
    from hadavin_sdk.store.memory import MemoryStore

    if not isinstance(store, MemoryStore):
        return True
    _LOG.warning(
        "trigger worker: the store is the memory kind: acknowledged requests do not survive a restart"
    )
    return False


def check_store_stage(store: Any, config: Any) -> None:
    """A ConfigError when the store keeps its rows in this process only (`MemoryStore`) and the stage is not
    demo (`config.environment`, read with `stages.is_live`): a pilot or prod worker would answer 202 for rows
    that vanish on a restart (door review M4). Only a memory store reads the stage; any other kind passes."""
    from hadavin_sdk.stages import is_live
    from hadavin_sdk.store.memory import MemoryStore

    if isinstance(store, MemoryStore) and is_live(
        _field(config, "environment", "config.environment")
    ):
        raise ConfigError(
            "trigger worker: the memory store is for the demo stage only: acknowledged requests would not"
            " survive a restart (use the PostgreSQL store)"
        )


def check_spend(runtime: Any, max_running: int) -> bool:
    """False, with one warning, when more than one loop may run at a time and the runtime's limits object has
    no `reserve` method: the cost is then added after the model call, so parallel runs can pass a budget.
    Never stops the start: the configured value is used as it is."""
    if max_running <= 1 or hasattr(getattr(runtime, "limits", None), "reserve"):
        return True
    _LOG.warning(
        "trigger worker: max_running is %d and spend is not reserved before a model call: parallel runs can"
        " pass a budget; set triggers.max_running: 1 to rule that out",
        max_running,
    )
    return False


def make_app(
    app: Any,
    *,
    clock: Callable[[], float] = time.time,
    poll_s: float = POLL_S,
    max_waiting: int = MAX_WAITING,
    rate_clock: Callable[[], float] = time.monotonic,
) -> tuple[Any, Runner]:
    """The WSGI callable and its Runner from a built App (for `main`, or for a WSGI server of the client's
    choice). The caller closes the Runner."""
    settings = trigger_settings(app.config)
    resolve = secret_reader(app)
    senders = sender_list(settings)
    check_senders(senders, app.runtime.agents, app.registry.principals)
    secrets = read_secrets(senders, resolve)
    check_fields(settings)
    max_running = settings.max_running
    conflict_events_per_minute = settings.conflict_events_per_minute  # the one source (d-fix24)
    ack_wait_s = _field(settings, "ack_wait_s", "triggers.ack_wait_s")
    try:
        check_secrets(secrets)
        runner = Runner(
            app.runtime,
            app.store,
            max_running,
            ack_wait_s,
            poll_s=poll_s,
            max_waiting=max_waiting,
            audit=getattr(
                app, "audit", None
            ),  # an App stand-in without one: conflicts are counted only
            conflict_events_per_minute=conflict_events_per_minute,
            rate_clock=rate_clock,
        )
    except ValueError as exc:  # these messages name senders and bounds, never a value
        raise ConfigError(str(exc)) from None
    check_store_stage(app.store, app.config)
    check_durable(app.store)
    check_spend(app.runtime, max_running)
    try:
        return make_wsgi(settings, secrets, runner.start, clock, runner.health), runner
    except ValueError as exc:
        runner.close(0)
        raise ConfigError(str(exc)) from None
    except BaseException:
        runner.close(0)
        raise


def check_port(port: object) -> None:
    """A whole number from 0 (the system picks one) to 65535, or a ConfigError."""
    if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
        raise ConfigError("--port must be a whole number from 0 to 65535")


def check_server_bounds(max_connections: object, read_deadline_s: object) -> None:
    """The two bounds of the quiet server, or a ConfigError (NaN and infinity are refused with the rest)."""
    if (
        isinstance(max_connections, bool)
        or not isinstance(max_connections, int)
        or not 1 <= max_connections <= MAX_CONNECTIONS_CEILING
    ):
        raise ConfigError(
            f"max_connections must be a whole number from 1 to {MAX_CONNECTIONS_CEILING}"
        )
    if (
        isinstance(read_deadline_s, bool)
        or not isinstance(read_deadline_s, int | float)
        or not (
            0 < read_deadline_s <= READ_DEADLINE_S_CEILING
        )  # written so that NaN is refused too
    ):
        raise ConfigError(
            f"read_deadline_s must be above zero and at most {READ_DEADLINE_S_CEILING:g}"
        )


def make_server(
    host: str,
    port: int,
    wsgi: Any,
    socket_timeout_s: float,
    *,
    max_connections: int = MAX_CONNECTIONS,
    read_deadline_s: float = READ_DEADLINE_S,
) -> WSGIServer:
    """A bound stdlib server (not yet serving). The caller runs `serve_forever` and `server_close`. A port
    that is in use, or an address that cannot be bound, is a ConfigError (exit code 2 in `main`). The port
    is exclusive on every platform: on Windows because `QuietServer` turns the reuse option off and sets
    `SO_EXCLUSIVEADDRUSE`, elsewhere because the system refuses a second listener (see `QuietServer`)."""
    check_port(port)
    check_server_bounds(max_connections, read_deadline_s)
    handler = type(
        "TriggerHandler",
        (QuietRequestHandler,),
        {"timeout": socket_timeout_s, "read_deadline_s": read_deadline_s},
    )
    try:
        server = QuietServer((host, port), handler, max_connections=max_connections)
    except OSError as exc:  # port in use, or an address that cannot be bound: not the store
        raise ConfigError(f"cannot listen on {host}:{port} ({type(exc).__name__})") from None
    server.set_app(wsgi)
    return server


def qualified_agents(registry: Any) -> list[str]:
    """Every qualified agent, the way the tick command builds its App (the one copy inside `triggers`; the
    same loop in `cli` and the strict one in `Runtime.__init__` are for core-b, see
    handover/core-a/requests/004-shared-qualified-agents.md)."""
    from hadavin_sdk.runtime.agent_loop import Unqualified, assert_qualified

    agents = []
    for agent_id in registry.agents:
        try:
            assert_qualified(registry, agent_id)
            agents.append(agent_id)
        except Unqualified:
            _LOG.warning("trigger worker: %s is not qualified; its runs are refused", agent_id)
    return agents


def check_tick(store: Any) -> bool:
    """True when the store holds a good "stuck" tick not older than TICK_MAX_AGE_S. Else one warning; the
    start goes on in every case."""
    try:
        state = store.get_tick_state(STUCK_STEP)
        last = None if state is None else state.last_ok_at
        if last is not None and (now() - last).total_seconds() <= TICK_MAX_AGE_S:
            return True
        seen = "none recorded" if last is None else "the last good one is too old"
    except Exception as exc:  # noqa: BLE001 - a warning only: never a reason not to start
        seen = f"could not be read ({type(exc).__name__})"
    _LOG.warning(
        "trigger worker: no good %s tick in the last %d s (%s): is the tick running?",
        STUCK_STEP,
        TICK_MAX_AGE_S,
        seen,
    )
    return False


def serve(server: WSGIServer, runner: Any) -> int:
    """Serve until Ctrl-C or SIGTERM, then close the socket and wait for the running loops (`Runner.close`).
    Windows has Ctrl-C and Ctrl-Break only (SIGBREAK is handled like SIGTERM; SIGTERM is never delivered there).

    The signal handler only starts a thread that calls `server.shutdown()`: called in the thread that serves,
    `shutdown` would wait for itself. Not in the main thread no handler can be set; that is logged.

    Limits: a request thread that is in the middle of a request when the server stops is NOT waited for (it is
    a daemon thread; the process may end under it, the sender gets no answer and retries with the same key).
    Only the running loops are waited for, up to `Runner.close`'s wait. A second SIGTERM while `close` waits
    does nothing: the first one has already stopped the server, and only a kill ends the wait early."""

    def on_term(signum: int, frame: object) -> None:
        threading.Thread(target=server.shutdown, name="trigger-stop", daemon=True).start()

    names = [n for n in ("SIGTERM", "SIGBREAK") if hasattr(signal, n)]  # SIGBREAK: Windows only
    previous: dict[int, Any] = {}
    try:
        for name in names:
            number = getattr(signal, name)
            previous[number] = signal.signal(number, on_term)
    except ValueError:
        _LOG.warning("trigger worker: not the main thread, SIGTERM is not handled")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        _LOG.info("trigger worker: stopping, waiting for %d runs", runner.running)
        server.server_close()
        runner.close()
        for number, handler in previous.items():
            if handler is not None:  # None: the old handler was not set from Python
                signal.signal(number, handler)
    return EXIT_OK


def _build_app(args: argparse.Namespace) -> tuple[Any, Runner, Any]:
    """Load the config, build the App and the Runner: (wsgi, runner, app). The caller closes the Runner."""
    from hadavin_sdk.app import build
    from hadavin_sdk.config import load_config
    from hadavin_sdk.registry import load_registry

    config = load_config(args.config_dir)
    check_fields(
        trigger_settings(config)
    )  # before anything is built: no secret read, no connection
    host = args.host  # an empty --host is refused by `check_bind`, never turned into loopback
    port = args.port if args.port is not None else PORT
    check_port(port)
    check_bind(host, args.allow_non_loopback)
    app = build(args.config_dir, qualified_agents(load_registry(config)))
    runner = None
    try:
        wsgi, runner = make_app(app)
        check_tick(app.store)
    except BaseException:
        if runner is not None:
            runner.close(0)
        _close_app(app)  # `build` opened the store connection: a failed try must not leave it open
        raise
    return wsgi, runner, app


def _close_app(app: Any) -> None:
    """Close what `build` opened (the stores' connections), best effort, never raises. The App has no close and
    `PostgresStore` has none either: its connection `_db` is closed; a store with a `close` is closed with it."""
    seen: list[Any] = []
    for part in (getattr(app, "store", None), getattr(app, "purge_store", None)):
        if part is None or any(part is old for old in seen):
            continue
        seen.append(part)
        closer = getattr(part, "close", None) or getattr(getattr(part, "_db", None), "close", None)
        if callable(closer):
            try:
                closer()
            except Exception as exc:  # noqa: BLE001 - a dead connection may refuse to close
                _LOG.debug("trigger worker: store close failed (%s)", type(exc).__name__)


def _warn_no_audit(app: Any) -> None:
    """One WARNING when the App has no `audit`: the 409 conflict events then cannot be written. Only `main`
    calls this (never `make_app`, which tests feed with stand-ins)."""
    if not hasattr(app, "audit"):
        _LOG.warning(
            "trigger worker: the App (%s) has no 'audit' attribute: 409 conflict events are counted but not"
            " written to the audit",
            type(app).__name__,
        )


def _prepare(args: argparse.Namespace) -> tuple[WSGIServer, Runner]:
    wsgi, runner, app = _build_app(args)
    _warn_no_audit(app)
    port = args.port if args.port is not None else PORT
    try:
        timeout = runner.ack_wait_s + SOCKET_SLACK_S  # the value `make_app` read, default or not
        return make_server(args.host, port, wsgi, timeout), runner
    except BaseException:
        runner.close(0)
        _close_app(app)
        raise


def _recover(args: argparse.Namespace) -> tuple[Any, Runner]:
    """One try of a degraded worker to get the real app: build it and ping the store with `Runner.health`.
    Raises while the store is down (any error: the caller tries again later); on success (wsgi, runner)."""
    wsgi, runner, app = _build_app(args)
    kept = False
    try:
        up, _failures = runner.health()
        if not up:
            raise StoreUnavailable("store ping failed")
        _warn_no_audit(app)
        runner.owned_app = app
        kept = True
        return wsgi, runner
    finally:
        if not kept:  # every failed try closes the Runner and the connection `build` opened
            runner.close(0)
            _close_app(app)


class _Degraded:
    """What a worker that started with the store down serves, and the switch to the real app.

    As the WSGI callable it hands every request to the app held in `_app`, read per request: first
    `health_only_app` (``/health`` 503, an empty 503 elsewhere), and, once the store has answered a re-check,
    the real wsgi app. The Runner exists only inside `_recover`; the real app is put in place only after it is
    built, so no request is answered 2xx before that. `serve` uses it as its runner: `running` and `close`."""

    def __init__(self, args: argparse.Namespace) -> None:
        self._args = args
        self.failures = 1  # the failed start-up
        self._lock = threading.Lock()  # guards _app, _runner, _stopped and failures
        self._app: Callable[..., Any] = health_only_app(self.health)
        self._runner: Runner | None = None
        self._stopped = threading.Event()
        self._thread = threading.Thread(target=self._watch, name="trigger-recover", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def __call__(self, environ: Any, start_response: Any) -> Any:
        with self._lock:
            app = self._app
        return app(environ, start_response)

    def health(self) -> tuple[bool, int]:
        with self._lock:
            return False, self.failures

    @property
    def running(self) -> int:
        with self._lock:
            runner = self._runner
        return runner.running if runner is not None else 0

    def _watch(self) -> None:
        """Retry every error, forever, every `HEALTH_RECHECK_S`: the worker never exits by itself here. The
        exception class name (never its text) is logged at WARNING at most once per `DEGRADED_WARN_EVERY_S`,
        and once more whenever the class changes."""
        last = ""
        last_warned = 0.0
        while not self._stopped.wait(HEALTH_RECHECK_S):
            try:
                wsgi, runner = _recover(self._args)
            except Exception as exc:  # noqa: BLE001 - the class name only: the text could hold a value
                with self._lock:
                    self.failures += 1
                name = type(exc).__name__
                at = _monotonic()
                if name != last or at - last_warned >= DEGRADED_WARN_EVERY_S:
                    _LOG.warning("trigger worker: store re-check failed (%s): still degraded", name)
                    last, last_warned = name, at
                continue
            with self._lock:
                if not self._stopped.is_set():
                    self._runner, self._app = runner, wsgi
                    runner = None
            if runner is not None:  # stopped while building: nobody will serve with it
                runner.close(0)
                _close_app(runner.owned_app)  # and the connection `build` opened
                return
            _LOG.info("trigger worker: store is back, serving triggers")
            return

    def close(self) -> None:
        with self._lock:
            self._stopped.set()
            runner = self._runner
        if self._thread.is_alive():
            self._thread.join(1.0)  # a re-check in the middle of a build closes its own Runner
        if runner is not None:
            runner.close()


def _ack_wait_of(args: argparse.Namespace) -> float:
    """The `triggers.ack_wait_s` the real Runner will use (as `_prepare` takes it from the Runner), read from
    the config for a worker that has no Runner yet; `ACK_WAIT_S` when the config cannot say."""
    try:
        from hadavin_sdk.config import load_config

        value = _field(
            trigger_settings(load_config(args.config_dir)), "ack_wait_s", "triggers.ack_wait_s"
        )
    except Exception:  # noqa: BLE001 - the default; the real error shows when the app is built
        return ACK_WAIT_S
    if (
        isinstance(value, bool)
        or not isinstance(value, int | float)
        or not 0 < value <= ACK_WAIT_S_CEILING
    ):
        return ACK_WAIT_S
    return float(value)


def _serve_degraded(args: argparse.Namespace, exc: BaseException) -> int:
    """The store was not reachable at start: log one WARNING (class name only) and serve `/health` 503 and
    an empty 503 for every other path. Every `HEALTH_RECHECK_S` the store is tried again; when it answers, the
    real app replaces the degraded one in the same process (`_Degraded`). Stops on Ctrl-C or SIGTERM."""
    _LOG.warning(
        "trigger worker: store unreachable at start (%s): starting anyway; GET /health answers 503 until the"
        " store answers, re-checked every %g s",
        type(exc).__name__,
        HEALTH_RECHECK_S,
    )
    degraded = _Degraded(args)
    try:
        port = args.port if args.port is not None else PORT
        check_port(port)
        check_bind(args.host, args.allow_non_loopback)
        server = make_server(args.host, port, degraded, _ack_wait_of(args) + SOCKET_SLACK_S)
    except ConfigError as err:
        print(f"trigger worker: config error: {err}", file=sys.stderr)
        return EXIT_CONFIG
    _LOG.info(
        "trigger worker: listening on http://%s:%d (store down: /health only)",
        server.server_address[0],
        server.server_port,
    )
    degraded.start()
    return serve(server, degraded)


def _log_to_stderr() -> logging.Handler:
    """INFO lines of the `hadavin_sdk.triggers` logger on stderr; returns the handler (the one already there on a
    second call). Only that logger is set: the root logger, the rest of `hadavin_sdk` and with them the logging
    of every library in the process stay as they are. Undone by `_unlog_stderr`."""
    top = logging.getLogger(_LOG.name)
    top.setLevel(logging.INFO)
    for held in top.handlers:
        if getattr(held, "_trigger_worker", False):
            return held
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    handler._trigger_worker = True  # type: ignore[attr-defined]
    top.addHandler(handler)
    return handler


def _unlog_stderr() -> None:
    """Remove the handler `_log_to_stderr` added (every copy) and put the logger's level back to unset."""
    top = logging.getLogger(_LOG.name)
    for held in [h for h in top.handlers if getattr(h, "_trigger_worker", False)]:
        top.removeHandler(held)
    top.setLevel(logging.NOTSET)


_SAFE_SEGMENT = re.compile(r"[A-Za-z0-9_.-]{1,40}")


def _safe_segment(part: object) -> str:
    """One location segment as text, or `?` when it is not plain (an extra YAML key is user text). No slicing: a
    segment that does not match whole is replaced whole."""
    text = str(part)
    return text if _SAFE_SEGMENT.fullmatch(text) else "?"


def _loc_text(loc: object) -> str:
    return ".".join(_safe_segment(p) for p in loc)  # type: ignore[attr-defined]


def _error_type(kind: object) -> str:
    return _safe_segment(kind)


def _fields(exc: BaseException, limit: int = 10) -> str:
    """` (fields: a.b (missing), c (extra_forbidden))` from the pydantic error that `load_config` chained to a config
    error, else an empty string. Only the location and the error type are taken, never the message or the input:
    pydantic's text repeats the value that was given, and a config error of the SDK can hold one (a bad backend
    setting, a YAML error). A config error with no such cause stays class-name-only."""
    cause = exc.__cause__
    errors = getattr(cause, "errors", None)
    if not callable(errors):
        return ""
    try:
        found = errors(include_input=False, include_url=False, include_context=False)
        shown = [f"{_loc_text(e['loc'])} ({_error_type(e['type'])})" for e in found[:limit]]
    except Exception:  # noqa: BLE001 - not a pydantic error after all: class name only
        return ""
    if not shown:
        return ""
    more = f", and {len(found) - limit} more" if len(found) > limit else ""
    return f" (fields: {', '.join(shown)}{more})"


def main(argv: list[str] | None = None) -> int:
    """Exit codes: 0 stopped cleanly (Ctrl-C or SIGTERM), 2 config error, 3 anything else. A store that is not
    reachable at start is no exit: one WARNING, then the worker serves ``/health`` 503 only and re-checks the
    store every `HEALTH_RECHECK_S`, switching to normal serving when it answers (`_serve_degraded`)."""
    parser = argparse.ArgumentParser(prog="python -m hadavin_sdk.triggers.worker")
    parser.add_argument("--config-dir", type=Path, default=None)
    parser.add_argument("--host", default=LOOPBACK, help=f"default: {LOOPBACK}")
    parser.add_argument("--port", type=int, default=None, help=f"default: {PORT}")
    parser.add_argument(
        "--allow-non-loopback", action="store_true", help="listen on a host that is not loopback"
    )
    args = parser.parse_args(argv)
    _log_to_stderr()
    try:
        server, runner = _prepare(args)
    except StoreUnavailable as exc:  # a config error subclass: must come first
        return _serve_degraded(args, exc)
    except ConfigError as exc:  # written in this file: ids and bounds only
        print(f"trigger worker: config error: {exc}", file=sys.stderr)
        return EXIT_CONFIG
    except AnyConfigError as exc:  # class name and field paths only: the text could hold a value
        print(f"trigger worker: config error: {type(exc).__name__}{_fields(exc)}", file=sys.stderr)
        return EXIT_CONFIG
    except Exception as exc:  # noqa: BLE001 - class name only: the text could hold a value
        if is_connectivity_error(exc):
            return _serve_degraded(args, exc)
        print(f"trigger worker: start failed: {type(exc).__name__}", file=sys.stderr)
        return EXIT_FAILED
    _LOG.info(
        "trigger worker: listening on http://%s:%d%s; the tick must run too, or a cut-off run stays RECEIVED or WORKING",
        server.server_address[0],
        server.server_port,
        PATH,
    )
    return serve(server, runner)


if __name__ == "__main__":
    raise SystemExit(main())
