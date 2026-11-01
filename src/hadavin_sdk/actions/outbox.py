"""Intent -> call -> settle, on the Store and the audit sink the platform already has (one intent mechanism).

Never call the processor inside a store transaction: it holds the lock across a network call, and a rollback would hide an
intent whose effect happened. The order is: (A) the audit INTENT event is written (`AuditSink.write_intent`; if it raises
`AuditUnavailable` nothing happens) and an attempt row is created in the Store; (B) the processor is called OUTSIDE any
transaction with the business key as its idempotency key; (C) the attempt is settled with a compare-and-set and the audit
OUTCOME event is written (`write_outcome`, which never raises: it falls back to the audit outbox).

An attempt is a `Run` row named from the business key and an attempt number (`outbox-<sha256(key)[:32]>-<n>`, the key itself in `trigger_ref`): the existing
`Store.create_run` / `transition` give atomic create and compare-and-set, `list_runs(EXECUTING, updated_before)` lists stale
intents, and no table is added. EXECUTING = open, SUCCEEDED = applied, ROLLED_BACK = definitely not applied (the key may be
attempted again as attempt n+1), STOPPED = unknown after the escalation age (a person decides; no new attempt starts).

Relation to `actions.executor.Executor`: the Executor makes one HTTP call and looks the result up on a timeout; it is a
`Processor` (apply + lookup) and knows nothing of intents. This module is what makes a retry safe around it.
Apply results are typed: `Applied`, `NotApplied` (a definite failure before any effect) or `Unknown` (the effect may have
happened). Any other exception is a programmer error: it propagates and leaves the attempt OPEN (reconcile resolves it).
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Protocol

from hadavin_sdk.audit.protocol import AuditSink, AuditUnavailable
from hadavin_sdk.models import AuditEvent, Run, RunState
from hadavin_sdk.store.protocol import NotFound, StaleState, Store

DOMAIN = "outbox"
MAX_ATTEMPTS = 5  # a key attempted this many times without an outcome goes to a person


class Status(StrEnum):
    APPLIED = "applied"
    NOT_APPLIED = "not_applied"
    UNKNOWN = "unknown"
    DUPLICATE = "duplicate"
    IN_DOUBT = (
        "in_doubt"  # an earlier attempt is open and could not be resolved: not retried blindly
    )
    AUDIT_UNAVAILABLE = "audit_unavailable"
    ESCALATED = "escalated"


@dataclass(frozen=True)
class Applied:
    ref: str = ""


@dataclass(frozen=True)
class NotApplied:
    reason: str = ""


@dataclass(frozen=True)
class Unknown:
    reason: str = ""


ApplyResult = Applied | NotApplied | Unknown


class Processor(Protocol):
    def apply(self, key: str) -> ApplyResult:
        """Do the action with `key` as the idempotency key."""
        ...

    def lookup(self, key: str) -> ApplyResult | None:
        """`Applied` if done, `NotApplied` if definitely not, None when it cannot tell."""
        ...


@dataclass(frozen=True)
class Result:
    status: Status
    attempt: int
    ref: str = ""


def _run_id(key: str, attempt: int) -> str:
    return f"outbox-{hashlib.sha256(key.encode()).hexdigest()[:32]}-{attempt}"


def _event(
    key: str, attempt: int, operation: str, principal: str, result: str | None = None
) -> AuditEvent:
    return AuditEvent(
        run_id=_run_id(key, attempt), domain=DOMAIN, operation=operation, principal=principal, source="outbox",
        object_ref=hashlib.sha256(key.encode()).hexdigest()[:32], result=result,
    )  # fmt: skip


class Outbox:
    def __init__(
        self, store: Store, audit: AuditSink, processor: Processor, *, principal: str = "svc:outbox"
    ) -> None:
        self.store, self.audit, self.processor, self.principal = store, audit, processor, principal

    def _attempts(self, key: str) -> list[Run]:
        out: list[Run] = []
        for n in range(1, MAX_ATTEMPTS + 1):
            try:
                out.append(self.store.get_run(_run_id(key, n)))
            except NotFound:
                break
        return out

    def _settle(self, key: str, attempt: int, new: RunState, operation: str, reason: str) -> bool:
        """Compare-and-set EXECUTING -> new: False when another process settled it first (that one's outcome stands)."""
        try:
            self.store.transition(_run_id(key, attempt), RunState.EXECUTING, new, reason)
        except StaleState:
            return False
        self.audit.write_outcome(_event(key, attempt, operation, self.principal, reason))
        return True

    def run(self, key: str) -> Result:
        if not isinstance(key, str) or not 0 < len(key) <= 200 or not key.isprintable():
            raise ValueError("key must be bounded printable text")
        prior = self._attempts(key)
        if prior:
            last = prior[-1]
            if last.state is RunState.SUCCEEDED:
                return Result(Status.DUPLICATE, len(prior), last.reason_code or "")
            if last.state is RunState.STOPPED:
                return Result(Status.ESCALATED, len(prior))
            # an earlier attempt has no outcome: never a blind second call
            if last.state is RunState.EXECUTING:
                found = self._resolve(key, len(prior))
                if found is None or found.status is not Status.NOT_APPLIED:
                    return Result(
                        Status.IN_DOUBT if found is None else found.status,
                        len(prior),
                        found.ref if found else "",
                    )
                prior = self._attempts(key)
            if len(prior) >= MAX_ATTEMPTS:
                return Result(Status.ESCALATED, len(prior))
        attempt = len(prior) + 1
        try:
            self.audit.write_intent(_event(key, attempt, "intent", self.principal))
        except AuditUnavailable:
            return Result(Status.AUDIT_UNAVAILABLE, attempt)
        try:
            self.store.create_run(
                Run(
                    run_id=_run_id(key, attempt),
                    agent_id=DOMAIN,
                    principal_id=self.principal,
                    trigger_kind="event",
                    trigger_ref=key,
                    state=RunState.EXECUTING,
                )
            )
        except StaleState:  # another process opened this attempt first
            return Result(Status.IN_DOUBT, attempt)
        res = self.processor.apply(key)
        return self._record(key, attempt, res)

    def _record(self, key: str, attempt: int, res: ApplyResult | None) -> Result:
        if isinstance(res, Applied):
            self._settle(key, attempt, RunState.SUCCEEDED, "applied", res.ref[:200])
            return Result(Status.APPLIED, attempt, res.ref)
        if isinstance(res, NotApplied):
            self._settle(key, attempt, RunState.ROLLED_BACK, "not_applied", res.reason[:200])
            return Result(Status.NOT_APPLIED, attempt)
        return Result(Status.UNKNOWN, attempt)  # Unknown, or None: stays EXECUTING for reconcile

    def _resolve(self, key: str, attempt: int) -> Result | None:
        try:
            found = self.processor.lookup(key)
        except (TimeoutError, ConnectionError, OSError):
            return None
        if found is None:
            return None
        return self._record(key, attempt, found)

    def reconcile(
        self,
        *,
        now: datetime,
        min_age: timedelta,
        escalate_after: timedelta,
        escalate: Callable[[str], None] = lambda run_id: None,
    ) -> dict[str, str]:
        """Resolve every open attempt at least `min_age` old by looking its key up (the key is the attempt's `trigger_ref`).
        An answer settles it; no answer leaves it open until `escalate_after`, then it becomes STOPPED and `escalate(run_id)`
        is called (a person decides; no new attempt starts). One failing key never stops the batch, and two reconcilers are
        safe: the settle is a compare-and-set, the loser reports `settled_elsewhere`."""
        out: dict[str, str] = {}
        for run in self.store.list_runs(RunState.EXECUTING, now - min_age):
            if run.agent_id != DOMAIN:
                continue
            try:
                out[run.run_id] = self._reconcile_one(run, now, escalate_after, escalate)
            except Exception as exc:  # noqa: BLE001 - per-key isolation: record the class, go on
                out[run.run_id] = f"error:{type(exc).__name__}"
        return out

    def _reconcile_one(
        self, run: Run, now: datetime, escalate_after: timedelta, escalate: Callable[[str], None]
    ) -> str:
        attempt = int(run.run_id.rsplit("-", 1)[1])
        key = run.trigger_ref
        try:
            found = self.processor.lookup(key)
        except (TimeoutError, ConnectionError, OSError):
            found = None
        if isinstance(found, Applied | NotApplied):
            before = self.store.get_run(run.run_id).state
            self._record(key, attempt, found)
            return (
                "settled_elsewhere"
                if before is not RunState.EXECUTING
                else ("applied" if isinstance(found, Applied) else "not_applied")
            )
        if now - run.updated_at < escalate_after:
            return "open"
        try:
            self.store.transition(run.run_id, RunState.EXECUTING, RunState.STOPPED, "stale")
        except StaleState:
            return "settled_elsewhere"
        self.audit.write_outcome(_event(key, attempt, "escalated", self.principal, "stale"))
        escalate(run.run_id)
        return "escalated"
