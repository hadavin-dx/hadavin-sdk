"""`hadavin-sdk tick`: one idempotent pass of housekeeping steps, run every 30-60 s by any scheduler.

Contract (design v5 kernel, section 4):
* ``STEPS`` runs in order: sweep, reconcile, stuck, checkpoint, purge_evidence (by default daily). Later PRs only
  **append** a ``TickStep``; a deployment that needs another step appends one to this list too.
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
* Three refusals do NOT come back as an exit code. For an app whose stage is not exactly demo, ``run_tick`` RAISES
  ``ConfigError`` when it is given ``now=`` or ``steps=`` (both are for tests; the command line never passes them),
  and when a built-in step is missing from ``STEPS``. A caller must catch the error; an uncaught one ends a Python
  process with exit code 1, which this list reads as "a step failed" (the command line reports it as a config
  error, exit code 2).
* The time enters the steps through ``TickContext``. Outside demo a context that is given a time is refused
  (``ConfigError``), so a step called by hand cannot work with a time of the caller's choice:
  ``purge_evidence(TickContext(app, <time>))`` raises there. ``purge_evidence(TickContext(app))`` (the app's clock)
  is not refused; calling one step by hand is not a supported entry point (no supported way exists today to run
  only some steps outside demo).

Concurrent ticks are safe: every state change is a compare-and-set, and a loser (``StaleState``) skips.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from hadavin_sdk.errors import ConfigError
from hadavin_sdk.guard.runmap import safe_head
from hadavin_sdk.models import AuditEvent, RunState, TickState
from hadavin_sdk.runtime.runs import IllegalTransition, advance
from hadavin_sdk.stages import is_live
from hadavin_sdk.store.protocol import StaleState, is_connectivity_error

if TYPE_CHECKING:
    from hadavin_sdk.app import App

S = RunState
TICK_SLACK_S = 60  # the longest gap between ticks (design: every 30-60 s)
_LOG = logging.getLogger("hadavin_sdk.tick")
OK, FAILED, SKIPPED = "ok", "failed", "skipped"


NO_GIVEN_TIME = "now= is for tests; it is refused in pilot and prod"


@dataclass(frozen=True)
class TickContext:
    """What a tick hands to every step: the app, the ONE time all steps work with, and the results so far.

    This is where the time enters the steps (the approval sweep, the stuck-run check, the evidence purge delete by
    age from it). `TickContext(app)` takes the time from the app's clock. `TickContext(app, <time>)` is for tests:
    outside demo (pilot, prod and any stage value that is not exactly demo) a context that is given a time is refused
    with a ConfigError, whoever builds it (`run_tick`, or a caller that runs one step by hand). The time cannot be
    changed afterwards (the object is frozen); `results` is filled in as the steps run. `app` must carry its config
    (`app.config.environment`)."""

    app: App
    now: datetime | None = None  # None: the app's clock. Always a time once the object exists.
    results: dict[str, str] = field(default_factory=dict)  # step name -> ok / failed / skipped

    def __post_init__(self) -> None:
        if self.now is None:
            object.__setattr__(self, "now", self.app.approvals.clock())
        elif is_live(self.app.config.environment):
            raise ConfigError(NO_GIVEN_TIME)


def _now(ctx: TickContext) -> datetime:
    """The time of this tick, for a step. Outside demo only a real `TickContext` is taken (its time came from the
    clock): a stand-in object that merely has a `now` is refused, so a hand-made time cannot reach a step that way."""
    if not isinstance(ctx, TickContext) and is_live(ctx.app.config.environment):
        raise ConfigError(NO_GIVEN_TIME)
    return ctx.now


@dataclass(frozen=True)
class TickStep:
    name: str  # unique, [a-z_]+ (the tick_state CHECK)
    every_s: int  # 0 = every tick
    fn: Callable[[TickContext], None]
    # Interval read from the config at run time (so it is not frozen at import); wins over `every_s`.
    interval: Callable[[TickContext], int] | None = None

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-z_]+", self.name) or self.every_s < 0:
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
    ctx.app.approvals.sweep(_now(ctx))
    ctx.app.approvals.resend_unsent(_now(ctx))


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
        candidates = app.store.list_runs(state, _now(ctx) - timedelta(seconds=floor))

        def one(run, state=state, reason=reason) -> None:
            if run.updated_at >= _now(ctx) - timedelta(seconds=stuck_after_s(app, run.agent_id)):
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
    waiting = app.store.list_runs(S.WAITING_FOR_APPROVAL, _now(ctx) - timedelta(seconds=floor))
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


def purge_evidence(ctx: TickContext) -> None:
    """Delete tool calls and redaction maps past their retention, at most about every `retention.purge_every_s`.

    The two CEILINGS always run first and need no hook: a redaction map older than `held_maps_max_days` (400) and
    a tool call older than `held_tool_calls_max_days` (400) go whatever any hold says. Then the ordinary purge
    (30 days by default): runs that `hooks.hold_run_ids()` names (labelled wrong, harmful or missed, or demoted;
    none before K6) keep their tool calls and maps until the ceilings. A hold is NOT retroactive: a run already
    purged before it was named is gone. If the hook raises, the ordinary purge is skipped (keeping too much for a
    while is the safe direction), the ceilings have already run, the error is logged, and the step then FAILS so
    `tick_state.last_error` shows it."""
    app = ctx.app
    keep = app.config.retention
    store = app.purge_store or app.store  # the deleting identity, when one is configured
    maps = store.purge_redaction_maps(
        _now(ctx) - timedelta(days=keep.held_maps_max_days),
        keep_run_ids=frozenset(),
        keep_open=False,
    )
    calls = store.purge_tool_calls(
        _now(ctx) - timedelta(days=keep.held_tool_calls_max_days), keep_run_ids=frozenset()
    )
    hook = app.runtime.hooks.hold_run_ids
    try:
        held = frozenset(hook() or ()) if keep.hold_labelled and hook is not None else frozenset()
    except Exception as exc:
        _LOG.error(
            "purge_evidence: hold_run_ids raised %s: ordinary purge skipped this tick, ceilings applied",
            type(exc).__name__,
        )
        raise
    calls += store.purge_tool_calls(
        _now(ctx) - timedelta(days=keep.tool_calls_days), keep_run_ids=held
    )
    maps += store.purge_redaction_maps(
        _now(ctx) - timedelta(days=keep.redaction_maps_days), keep_run_ids=held
    )
    _LOG.info("purge_evidence tool_calls=%d redaction_maps=%d held_runs=%d", calls, maps, len(held))


def reprobe_sources(ctx: TickContext) -> None:
    """Probe every configured source's scope again (design 6.6): RBAC can widen after start-up. A problem fails
    the step loudly (`tick_state.last_error`, exit 1) until the scope is read-only again."""
    from hadavin_sdk import sources as sources_mod

    app = ctx.app
    found: list[str] = []
    for key, source in app.sources.items():
        token = sources_mod.PROBING.set(True)
        try:
            problems = sources_mod.scope_problems({key: source}, app.config.scope_inventory)
        finally:
            sources_mod.PROBING.reset(token)
        if problems:  # fail CLOSED: tools stop reading this source until a probe passes again
            app.disabled_sources.add(key)
            found += problems
        else:
            app.disabled_sources.discard(key)
    if found:
        raise RuntimeError("source scope: " + "; ".join(found))


def heartbeat(ctx: TickContext) -> None:
    """After the steps (not a step): one line with this tick's outcome."""
    failed = sorted(n for n, r in ctx.results.items() if r == FAILED)
    _LOG.info("tick ok=%s failed=%s", not failed, ",".join(failed) or "-")


STEPS: list[TickStep] = [
    TickStep("sweep", 0, sweep),
    TickStep("reconcile", 0, reconcile),
    TickStep("stuck", 0, stuck),
    TickStep("checkpoint", 0, checkpoint),
    TickStep(
        "purge_evidence",
        0,
        purge_evidence,
        interval=lambda ctx: ctx.app.config.retention.purge_every_s,
    ),  # its own interval: Config.retention.purge_every_s
    TickStep(
        "reprobe_sources",
        0,
        reprobe_sources,
        interval=lambda ctx: ctx.app.config.evidence.source_reprobe_s,
    ),
]
# The names of the steps above, remembered when the module is loaded. Outside demo a tick refuses to run when one of
# them is no longer in `STEPS` (see `run_tick`). A deployment adds a step by appending to `STEPS`.
_BUILT_IN: tuple[str, ...] = tuple(step.name for step in STEPS)


def _missing_built_in_steps() -> list[str]:
    """The built-in steps that are not in `STEPS` right now (by name), in their built-in order."""
    present = {step.name for step in STEPS}
    return [name for name in _BUILT_IN if name not in present]


STORE_UNREACHABLE = 4
STORE_NOT_READY = (
    2  # the store answers but a table or grant is missing: same code as a config error
)


def _safe_log(msg: str, *args: object) -> None:
    """Log an error line; a failing log handler must never change the exit code."""
    try:
        _LOG.error(msg, *args)
    except Exception:  # noqa: BLE001, S110 - safe to swallow: this IS the error report, so there is nowhere left to report to; the caller still returns its exit code
        pass


_PROBE = "heartbeat"  # the tick_state key read once, to find out whether the store answers


_DRIVERS = ("psycopg", "urllib", "http", "botocore", "boto3", "socket", "ssl")


def _message(exc: Exception) -> str:
    """Redacted and one line. Driver and network errors carry hosts and users: their type says enough."""
    if type(exc).__module__.split(".")[0] in _DRIVERS or isinstance(exc, OSError):
        return "(driver error; details withheld)"
    # redact first, then keep the first 500 characters (a cut first splits a secret); `safe_head` bounds the work
    return safe_head(str(exc), 500).replace("\n", " ")


def _run_step(ctx: TickContext, step: TickStep) -> str:
    store = ctx.app.store
    prev, error = None, None
    try:
        prev = store.get_tick_state(step.name)
        every = step.interval(ctx) if step.interval else step.every_s
        if (
            step.interval
        ):  # a tick comes every 30-60 s: due a tick-period early, so the cadence does not drift
            every = max(every - TICK_SLACK_S, every // 2)
        # A step whose last run FAILED is due again at the next tick (a persistently raising hold hook must
        # not push the 30-day purge a whole interval away each time).
        if (
            every
            and prev
            and prev.last_error is None
            and (_now(ctx) - prev.last_run_at).total_seconds() < every
        ):
            return SKIPPED
        step.fn(ctx)
    except Exception as exc:  # noqa: BLE001 - one step never stops the others
        error = f"{type(exc).__name__}: {_message(exc)}"
        _LOG.error("step=%s error_kind=%s message=%s", step.name, type(exc).__name__, _message(exc))
    try:
        store.save_tick_state(
            TickState(
                step=step.name,
                last_run_at=_now(ctx),
                last_ok_at=_now(ctx) if error is None else (prev.last_ok_at if prev else None),
                last_error=error,
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
    is not ready (STORE_NOT_READY). A config that does not load is the caller's, before this runs.

    `now=` and `steps=` are for tests. `now=` sets the time every step works with (the approval sweep, the stuck-run
    check, the evidence purge), so a time in the future would delete evidence early. `steps=` replaces the list of
    steps, so a tick could return 0 without the sweep or the purge ever running. Outside demo (pilot, prod and any
    stage value that is not exactly demo) a tick that is given either one (not None; an empty list counts as given)
    RAISES a ConfigError before anything runs. With both given, `now=` is the one named. A tick called with neither
    keyword takes the time from the app's clock and runs `STEPS`.

    `STEPS` (the module's list) is where a step is added: append a `TickStep`. Outside demo a tick also RAISES a
    ConfigError ("a built-in tick step is missing: <names>") before anything runs when one of the steps this module
    defines is no longer in `STEPS` by name, so an emptied or cut list cannot return 0 with no sweep and no purge.
    An appended step runs after the built-in ones. In demo the list is run as it is.

    `app` must carry its config: `app.config.environment` is read on every call.

    The same rule holds one level down, where the time enters the steps: a `TickContext` that is given a time is
    refused outside demo, so `purge_evidence(TickContext(app, <time>))` raises too (see `TickContext`).

    Not covered by these refusals: a changed or patched `runtime.tick.STEPS` that still holds every built-in name
    (reordering, or replacing a step's function); a clock that tells the wrong time (`app.approvals.clock` replaced
    after build, or a hand-built `Approvals(clock=...)`); and the methods that take a time or a cut-off date
    directly, below the tick: `Approvals.sweep(at=)`, `Approvals.resend_unsent(at=)`, and the store's
    `purge_tool_calls(before)` and `purge_redaction_maps(before)` (the store knows no stage)."""
    given = [name for name, value in (("now", now), ("steps", steps)) if value is not None]
    live = is_live(app.config.environment)
    if given and live:
        raise ConfigError(f"{given[0]}= is for tests; it is refused in pilot and prod")
    if live and (missing := _missing_built_in_steps()):
        raise ConfigError(f"a built-in tick step is missing: {', '.join(missing)}")
    ctx = TickContext(app, now)
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
