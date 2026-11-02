"""`hadavin-sdk tick`: one idempotent pass of housekeeping steps, run every 30-60 s by any scheduler.

Contract (design v5 kernel, section 4):
* ``STEPS`` runs in order: sweep, reconcile, stuck, checkpoint, measure_levels, purge_seen_actions, weekly_report (K6). Later PRs
  only **append** a ``TickStep``.
* Each step runs in its own ``try``: a failure is logged as ``step=<name> error_kind=<type>
  message=<redacted, <= 500 chars>`` and written to ``tick_state``; the other steps still run.
* A step with ``every_s > 0`` runs only if ``now - tick_state.last_run_at >= every_s``.
* The tick summary line (``heartbeat``) is not a step: it is logged after the steps, is never recorded in
  ``tick_state`` and cannot change the exit code. The external heartbeat
  (a ping sent by the CLI entrypoint for every exit code) is PENDING (K7): nothing sends it today.
* Exit codes: 0 all ok; 1 a step failed (store still reachable); 2 config error, or the store answers but is
  not ready (missing table or grant: run ``migrate``); 4 store unreachable (connection refused, dropped or
  timed out), before any step or when it stops answering during the steps; 3 is the CLI wrapper's code for any
  other uncaught error.

Concurrent ticks are safe: every state change is a compare-and-set, and a loser (``StaleState``) skips.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from hadavin_sdk.guard.redact import redact
from hadavin_sdk.models import AuditEvent, RunState, TickState
from hadavin_sdk.runtime.runs import IllegalTransition, advance
from hadavin_sdk.store.protocol import StaleState, is_connectivity_error

if TYPE_CHECKING:
    from hadavin_sdk.app import App

S = RunState
_LOG = logging.getLogger("hadavin_sdk.tick")
OK, FAILED, SKIPPED = "ok", "failed", "skipped"


@dataclass
class TickContext:
    app: App
    now: datetime
    results: dict[str, str] = field(default_factory=dict)  # step name -> ok / failed / skipped
    # A step's own numbers, set as `ctx.detail[step.name] = {...}` (counts and codes only, never run content);
    # saved with its tick_state row. A step that sets nothing keeps the detail of its last run.
    detail: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass(frozen=True)
class TickStep:
    name: str  # unique, [a-z_]+ (the tick_state CHECK)
    every_s: int | Callable[[App], int]  # 0 = every tick; a callable reads it from the app's config
    fn: Callable[[TickContext], None]

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-z_]+", self.name) or (
            not callable(self.every_s) and self.every_s < 0
        ):
            raise ValueError(f"tick step name must be [a-z_]+ and every_s >= 0: {self.name!r}")


def _each(items: list[Any], fn: Callable[[Any], None], what: str) -> None:
    """Run fn per item; a CAS loser is skipped quietly, any other error is logged and the step fails at the
    end, after every item had its turn (one bad row never blocks the rest)."""
    first: Exception | None = None
    for item in items:
        try:
            fn(item)
        except (StaleState, IllegalTransition):
            _LOG.debug("%s: moved by another worker, skipped", what)
        except Exception as exc:  # noqa: BLE001 - isolate the item; re-raised below
            _LOG.warning("%s: %s", what, type(exc).__name__)
            first = first or exc
    if first is not None:
        raise first


def sweep(ctx: TickContext) -> None:
    """Escalate or expire due approvals; resend requests whose channel send failed."""
    ctx.app.approvals.sweep(ctx.now)
    ctx.app.approvals.resend_unsent(ctx.now)


def reconcile(ctx: TickContext) -> None:
    """Advance runs whose approval ended (APPROVED runs the plan). The receiver only records decisions."""
    store, runtime = ctx.app.store, ctx.app.runtime
    ended = store.list_approvals({"APPROVED", "REJECTED", "EXPIRED"})
    # ponytail: scans every ended approval each tick; filter by a reconciled flag when the table grows.

    def one(req) -> None:
        if store.get_run(req.run_id).state is not S.WAITING_FOR_APPROVAL:
            return
        ctx.app.approvals.update_message(req)  # decisions arrive record-only: show the outcome now
        runtime.on_decided(req.run_id, req.status, store.get_approval_decision(req.approval_id))

    _each(ended, one, "reconcile")


def stuck_after_s(app: App, agent_id: str) -> float:
    """max_steps x call_timeout_s x max_attempts + 60 (design 12.7): the longest a healthy run stays quiet."""
    llm = app.config.backends.llm
    agent = app.registry.agents.get(agent_id)
    steps = (
        agent.max_steps
        if agent
        else max((a.max_steps for a in app.registry.agents.values()), default=1)
    )
    return steps * getattr(llm, "call_timeout_s", 60) * getattr(llm, "max_attempts", 1) + 60


STUCK = {
    S.RECEIVED: "interrupted",
    S.WORKING: "interrupted",
    S.PLAN_READY: "interrupted",
    S.EXECUTING: "outcome_unknown",  # never re-executed: a person checks the system
    # ponytail: re-run verify once needs the stored RunResult; until then a person checks.
    S.VERIFYING: "verify_interrupted",
}


def stuck(ctx: TickContext) -> None:
    """Runs quiet for longer than their agent's stuck_after_s go to NEEDS_PERSON with a reason."""
    app = ctx.app
    floor = min((stuck_after_s(app, a) for a in app.registry.agents), default=60)
    for state, reason in STUCK.items():
        candidates = app.store.list_runs(state, ctx.now - timedelta(seconds=floor))

        def one(run, state=state, reason=reason) -> None:
            if run.updated_at >= ctx.now - timedelta(seconds=stuck_after_s(app, run.agent_id)):
                return
            advance(app.store, run.run_id, state, S.NEEDS_PERSON, reason)
            app.audit.write_outcome(
                AuditEvent(
                    run_id=run.run_id,
                    domain="run",
                    operation="state",
                    principal="system:tick",
                    source="tick",
                    result=S.NEEDS_PERSON.value,
                    error_code=reason,
                )
            )

        _each(candidates, one, f"stuck {state.value}")

    # A crash between WAITING_FOR_APPROVAL and saving the request leaves a wait nobody can answer.
    waiting = app.store.list_runs(S.WAITING_FOR_APPROVAL, ctx.now - timedelta(seconds=floor))
    if waiting:
        asked = {
            r.run_id
            for r in app.store.list_approvals({"PENDING", "APPROVED", "REJECTED", "EXPIRED"})
        }
        # ponytail: lists every approval; a by-run lookup when the table grows.

        def orphan(run) -> None:
            if run.run_id in asked:
                return
            advance(
                app.store, run.run_id, S.WAITING_FOR_APPROVAL, S.NEEDS_PERSON, "approval_missing"
            )
            app.audit.write_outcome(
                AuditEvent(
                    run_id=run.run_id,
                    domain="run",
                    operation="state",
                    principal="system:tick",
                    source="tick",
                    result=S.NEEDS_PERSON.value,
                    error_code="approval_missing",
                )
            )

        _each(waiting, orphan, "stuck WAITING_FOR_APPROVAL")


def checkpoint(ctx: TickContext) -> None:
    """Sign an audit checkpoint when the audit kind has them (`chain`); others have nothing to do."""
    fn = getattr(ctx.app.audit, "checkpoint", None)
    if fn is not None:
        fn()


def _policy(app: App):
    """The measurement policy of this deployment (documented defaults when there is no measure)."""
    from hadavin_sdk.measure import DEFAULT_POLICY

    measure = getattr(app, "measure", None)
    return measure.policy if measure is not None else DEFAULT_POLICY


def measure_levels(ctx: TickContext) -> None:
    """K6: re-check the demotion rules and the ceiling (idempotent). Nothing to do when the app has no measure."""
    measure = getattr(ctx.app, "measure", None)
    if measure is not None:
        measure.enforce(ctx.now)


def weekly_report(ctx: TickContext) -> None:
    """K6: write and announce the report for the last complete ISO week when it has none yet."""
    measure = getattr(ctx.app, "measure", None)
    if measure is not None:
        measure.weekly_report(ctx.now)


def purge_seen_actions(ctx: TickContext) -> None:
    """K6: delete click nonces older than twice the signature window (they can never be replayed)."""
    measure = getattr(ctx.app, "measure", None)
    if measure is not None:
        measure.purge_seen(ctx.now)


def heartbeat(ctx: TickContext) -> None:
    """After the steps (not a step): one line with this tick's outcome."""
    failed = sorted(n for n, r in ctx.results.items() if r == FAILED)
    _LOG.info("tick ok=%s failed=%s", not failed, ",".join(failed) or "-")


STEPS: list[TickStep] = [
    TickStep("sweep", 0, sweep),
    TickStep("reconcile", 0, reconcile),
    TickStep("stuck", 0, stuck),
    TickStep("checkpoint", 0, checkpoint),
    TickStep("measure_levels", lambda app: _policy(app).enforce_every_s, measure_levels),
    TickStep("purge_seen_actions", lambda app: _policy(app).purge_every_s, purge_seen_actions),
    # every tick: a report nobody was told of is retried at once
    TickStep("weekly_report", 0, weekly_report),
]
STORE_UNREACHABLE = 4
STORE_NOT_READY = (
    2  # the store answers but a table or grant is missing: same code as a config error
)


def _safe_log(msg: str, *args: object) -> None:
    """Log an error line; a failing log handler must never change the exit code."""
    try:
        _LOG.error(msg, *args)
    except Exception:  # noqa: BLE001, S110 - nothing left to report to
        pass


_PROBE = "heartbeat"  # the tick_state key read once, to find out whether the store answers


_DRIVERS = ("psycopg", "urllib", "http", "botocore", "boto3", "socket", "ssl")


def _message(exc: Exception) -> str:
    """Redacted and one line. Driver and network errors carry hosts and users: their type says enough."""
    if type(exc).__module__.split(".")[0] in _DRIVERS or isinstance(exc, OSError):
        return "(driver error; details withheld)"
    return redact(str(exc)).text.replace("\n", " ")[:500]


def _run_step(ctx: TickContext, step: TickStep) -> str:
    store = ctx.app.store
    prev, error = None, None
    try:
        prev = store.get_tick_state(step.name)
        every = step.every_s(ctx.app) if callable(step.every_s) else step.every_s
        if every and prev and (ctx.now - prev.last_run_at).total_seconds() < every:
            return SKIPPED
        step.fn(ctx)
    except Exception as exc:  # noqa: BLE001 - one step never stops the others
        error = f"{type(exc).__name__}: {_message(exc)}"
        _LOG.error("step=%s error_kind=%s message=%s", step.name, type(exc).__name__, _message(exc))
    try:
        store.save_tick_state(
            TickState(
                step=step.name,
                last_run_at=ctx.now,
                last_ok_at=ctx.now if error is None else (prev.last_ok_at if prev else None),
                last_error=error,
                detail=ctx.detail.get(step.name, prev.detail if prev else None),
            )
        )
    except Exception as exc:  # noqa: BLE001 - an unrecorded step counts as failed
        _LOG.error(
            "step=%s error_kind=%s message=tick_state not saved", step.name, type(exc).__name__
        )
        return FAILED
    return OK if error is None else FAILED


def run_tick(app: App, now: datetime | None = None, steps: list[TickStep] | None = None) -> int:
    """One tick. Returns the exit code: 0 ok, 1 a step failed, 4 the store is unreachable, 2 the store answers but
    is not ready (STORE_NOT_READY). A config that does not load is the caller's, before this runs."""
    ctx = TickContext(app, now or app.approvals.clock())
    try:
        app.store.get_tick_state(_PROBE)  # the store answers, or nothing runs
    except Exception as exc:  # noqa: BLE001 - any store failure: change nothing
        if is_connectivity_error(exc):
            _safe_log("step=- error_kind=%s message=store unreachable", type(exc).__name__)
            return STORE_UNREACHABLE
        _safe_log(
            "step=- error_kind=%s message=store answers but is not ready: run hadavin-sdk migrate "
            "and check the runtime role's grants",
            type(exc).__name__,
        )
        return STORE_NOT_READY
    for step in STEPS if steps is None else steps:
        ctx.results[step.name] = _run_step(ctx, step)
    try:
        heartbeat(ctx)
    except Exception as exc:  # noqa: BLE001 - a log line never changes the exit code
        _safe_log("step=- error_kind=%s message=heartbeat line not written", type(exc).__name__)
    if FAILED in ctx.results.values():
        # A scheduler must tell "the store went away" (4) from "a step failed with the store up" (1).
        try:
            app.store.get_tick_state(_PROBE)
        except Exception as exc:  # noqa: BLE001 - any store failure
            if is_connectivity_error(exc):
                _safe_log(
                    "step=- error_kind=%s message=store unreachable after the steps",
                    type(exc).__name__,
                )
                return STORE_UNREACHABLE
            # answers but not ready: the step failures stand, exit 1
    return 1 if FAILED in ctx.results.values() else 0
