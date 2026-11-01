"""The pipeline: GATES, GENERATE, VALIDATE (C1), AUDIT INTENT (C5), EXECUTE (C2, C3, C4), LEDGER (design 3, 9).

Fixed order, one bounded retry loop, no model-chosen tools, no memory. Every question ends in exactly one ledger
line and one outcome event. Nothing a server says reaches the model: a retry carries only a validator rule id or a
SQLSTATE hint from `policy`. The agreement check is NOT built (the amendments recommend against it for v1).
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import re
import time
import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Protocol

from pydantic import ValidationError

from askdata import llm_io
from askdata.audit import AskAudit
from askdata.ledger import Attempt, Budget, Final, LedgerLine, QueryLedger, utc_stamp
from askdata.meter import KillSwitch, Meter, MeterError, call_cost, fmt_usd, worst_case_usd
from askdata.pgsource import Limits, PgError, RunResult
from askdata.policy import REASONS, Outcome, decide, exit_code, pick_reason, rule_hint
from askdata.prompt import Prompt
from askdata.safe_text import clean
from askdata.validate import RULES, Rejected, Validated, validate
from hadavin_sdk.audit.protocol import AuditUnavailable
from hadavin_sdk.config import Route
from hadavin_sdk.guard.injection import RegexDetector, injection_check
from hadavin_sdk.llm.protocol import LLM, ProviderError, ProviderExhausted, UnusableAnswer

_SCHEMA_CHARS = len(json.dumps(llm_io.GENERATE_SCHEMA))  # the forced tool schema is sent too
NO_ROWS_NOTE = "0 rows: check the filters"


class Executor(Protocol):
    def run(
        self, canonical_sql: str, *, sql_sha256: str | None = None, limits: Limits | None = None
    ) -> RunResult: ...


@dataclass(frozen=True)
class Settings:
    route: str = "sql_generate"
    max_attempts: int = 3
    max_question_chars: int = 500
    restricted_terms: tuple[str, ...] = (
        "email", "e-mail", "mail address", "password", "passwd", "ssn", "social security",
        "card number", "credit card", "iban",
    )  # fmt: skip
    store_question: bool = True
    live: bool = True  # a live (paid) route also needs a fresh external_usd in the meter
    transient_backoff_s: float = 1.0
    # requests ONE chat() may send (the LLM kind retries inside it); the meter reserves for all of them
    llm_max_attempts: int = 1
    injection_threshold: float = (
        0.05  # the sweep in tests/demo_askdata/test_demo_gaps.py (A-19 F-27)
    )


@dataclass
class Answer:
    query_id: str
    outcome: Outcome
    reason: str | None
    exit_code: int
    sentence: str
    line: LedgerLine
    ledger_sha256: str
    result: RunResult | None = None
    canonical_sql: str | None = None
    sql_sha256: str | None = None
    assumptions: list[str] = field(default_factory=list)
    clarifying_question: str | None = None
    abort: bool = False  # SQLSTATE 28xxx: the caller must stop the process (exit 4)


class Pipeline:
    def __init__(
        self,
        *,
        llm: LLM,
        routes: dict[str, Route],
        executor: Executor,
        audit: AskAudit,
        ledger: QueryLedger,
        meter: Meter,
        kill: KillSwitch,
        prompt: Prompt,
        config_hash: str,
        settings: Settings | None = None,
        validator: Any = validate,
        sleep: Any = time.sleep,
    ) -> None:
        self.llm, self.routes, self.executor, self.audit = llm, routes, executor, audit
        self.ledger, self.meter, self.kill = ledger, meter, kill
        self.prompt, self.config_hash = prompt, config_hash
        self.s = settings or Settings()
        self.validator, self.sleep = validator, sleep
        self._detector = RegexDetector(self.s.injection_threshold)
        self._terms = [
            re.compile(rf"(?<!\w){re.escape(t)}(?!\w)", re.IGNORECASE)
            for t in self.s.restricted_terms
        ]

    # ------------------------------------------------------------------------------------------------ gates
    def _gate(self, question: str) -> str | None:
        """A reason code if the question is refused before any model call, else None. No LLM involved."""
        if self.kill.is_on():
            return "kill_switch"
        if len(question) > self.s.max_question_chars or not question.strip():
            return "out_of_scope"
        if any(t.search(question) for t in self._terms):
            return "restricted_data"
        if injection_check(self._detector, question, "question").flagged:
            return "injection_suspected"
        return None

    # ------------------------------------------------------------------------------------------------- ask
    def ask(self, question: str, *, asker: str = "claimed:anonymous") -> Answer:
        qid = uuid.uuid4().hex
        t0 = time.monotonic()
        run = _Run(
            qid,
            utc_stamp(),
            clean(asker)[:64],
            question,
            hashlib.sha256(question.encode("utf-8")).hexdigest(),
        )
        gate = self._gate(question)
        try:
            if gate:
                run.reason = gate
            else:
                self._generate_and_execute(run)
        except (
            BaseException
        ):  # Ctrl-C and the like: the question still ends in exactly one ledger line
            run.terminal.append("model_unavailable")
            with contextlib.suppress(
                Exception
            ):  # the interrupt, not a ledger problem, is what propagates
                self._finish(run, int((time.monotonic() - t0) * 1000))
            raise
        return self._finish(run, int((time.monotonic() - t0) * 1000))

    def _generate_and_execute(self, run: _Run) -> None:
        route = self.routes[self.s.route]
        prev_sql: str | None = None
        hint: str | None = None
        streak = 0
        once: set[str] = set()
        while run.calls < self.s.max_attempts:
            if self.kill.is_on():
                run.terminal.append("kill_switch")
                return
            messages = llm_io.build_messages(self.prompt.text, run.question, prev_sql, hint)
            # ONE request's worst case: the prompt AND the forced tool schema that travels with it.
            per_try = worst_case_usd(
                route, len(llm_io.SYSTEM) + len(messages[0]["content"]) + _SCHEMA_CHARS
            )
            # the kind may send this many requests inside one chat(): its own bound when it knows it
            worst = per_try * getattr(self.llm, "max_requests", self.s.llm_max_attempts)
            try:
                rid = self.meter.reserve(worst, live=self.s.live)
            except MeterError:  # OverBudget or an unreadable meter file: do not spend
                run.terminal.append("over_budget")
                return
            run.calls += 1
            n = run.calls
            t = time.monotonic()
            try:
                reply = self.llm.chat(
                    messages,
                    system=llm_io.SYSTEM,
                    route=self.s.route,
                    output_schema=llm_io.GENERATE_SCHEMA,
                )
            except (ProviderError, OSError, TimeoutError) as err:
                known = isinstance(err, ProviderError)
                cost = call_cost(
                    per_try,
                    worst,
                    sent=getattr(err, "attempts", 1) if known else self.s.llm_max_attempts,
                    reply_cost=None,
                    refused=known and not isinstance(err, ProviderExhausted | UnusableAnswer),
                    answered=getattr(err, "answered", 0),
                    billed=Decimal(getattr(err, "billed_usd", 0)),
                )
                self._model_failed(run, rid, worst, cost, n, t)
                return
            except Exception:  # noqa: BLE001 - unknown failure inside the kind: it may have sent a request
                self._model_failed(run, rid, worst, worst, n, t)
                return
            except (
                BaseException
            ):  # Ctrl-C and the like: close the reservation (as spent) before leaving
                self._settle(run, worst, worst, rid)
                raise
            actual = call_cost(
                per_try,
                worst,
                sent=reply.attempts,
                reply_cost=reply.cost_usd,
                answered=reply.answered,
            )
            run.cost += actual
            run.tokens_in += reply.input_tokens
            run.tokens_out += reply.output_tokens
            run.model_id = reply.model_id
            charged = self._settle(run, worst, actual, rid)
            base = {
                "n": n,
                "duration_ms": _ms(t),
                "tokens_in": reply.input_tokens,
                "tokens_out": reply.output_tokens,
                "cost_usd": fmt_usd(actual),
            }
            if not charged:  # the money is spent but not recorded: keep the attempt in the ledger
                run.attempts.append(Attempt(schema_ok=False, **base))
                return
            try:
                out = llm_io.parse_reply(reply)
            except llm_io.SchemaViolation:
                run.attempts.append(Attempt(schema_ok=False, **base))
                streak += 1
                if streak >= 2:
                    run.terminal.append("schema_violation")
                    return
                run.last_reason = "schema_violation"
                prev_sql, hint = None, llm_io.SCHEMA_HINT
                continue
            streak = 0
            if out.decision == "abstain":
                run.attempts.append(Attempt(schema_ok=True, **base))
                run.abstain = out
                return
            run.assumptions = [clean(a)[:300] for a in out.assumptions[:20]]
            run.rule_id = None
            sql_text = out.sql or ""
            try:
                ok: Validated = self.validator(sql_text)
            except Rejected as rej:
                run.attempts.append(
                    Attempt(
                        schema_ok=True,
                        sql_text=clean(sql_text)[:4000],
                        validator_rule=rej.rule,
                        **base,
                    )
                )
                run.rule_id = rej.rule
                run.last_reason = "write_request" if rej.rule == "V03" else "unsafe_query"
                prev_sql, hint = sql_text, rule_hint(rej.rule, RULES)
                continue
            status, retry_hint = self._execute(run, ok, sql_text, base, once)
            if status != "retry":
                return
            prev_sql, hint = sql_text, retry_hint

    def _settle(
        self, run: _Run, reserved: Decimal, actual: Decimal, rid: str | None = None
    ) -> bool:
        """Replace the reservation with the real cost. False (and the question ends over budget) if the meter
        cannot be written."""
        try:
            self.meter.settle(reserved, actual, rid)
        except MeterError:
            run.terminal.append("over_budget")
            return False
        return True

    def _model_failed(
        self, run: _Run, rid: str, reserved: Decimal, cost: Decimal, n: int, started: float
    ) -> None:
        """The model call produced no reply: book what the requests that were sent cost, record the attempt."""
        self._settle(run, reserved, cost, rid)
        run.cost += cost
        run.attempts.append(
            Attempt(n=n, schema_ok=False, duration_ms=_ms(started), cost_usd=fmt_usd(cost))
        )
        run.terminal.append("model_unavailable")

    def _execute(
        self, run: _Run, ok: Validated, sql_text: str, base: dict, once: set[str]
    ) -> tuple[str, str | None]:
        """Run one accepted statement. Returns ("done", None) when answered, ("stop", None) when the question
        ends, ("retry", hint) for another model attempt. A transient failure is resent ONCE without using a model
        attempt (and with its own intent event)."""
        for resend in range(2):
            try:
                eid = self.audit.intent(
                    run.query_id, question_sha256=run.q_sha, sql_sha256=ok.sha256
                )
            except AuditUnavailable:
                run.attempts.append(
                    Attempt(
                        schema_ok=True,
                        sql_text=clean(sql_text)[:4000],
                        canonical_sql=clean(ok.canonical_sql)[:4000],
                        sql_sha256=ok.sha256,
                        **base,
                    )
                )
                run.terminal.append("audit_unavailable")
                return "stop", None
            run.intents.append(eid)
            t = time.monotonic()
            common = {
                "schema_ok": True, "sql_text": clean(sql_text)[:4000], "canonical_sql": clean(ok.canonical_sql)[:4000],
                "sql_sha256": ok.sha256, "intent_event_id": eid, "executed": True,
            }  # fmt: skip
            try:
                res = self.executor.run(ok.canonical_sql, sql_sha256=ok.sha256)
            except PgError as err:
                state = err.sqlstate
                timing = {**base, "duration_ms": base["duration_ms"] + _ms(t)}
                attempt = Attempt(
                    sqlstate=state, sqlstate_class=state[:2] if state else None, **common, **timing
                )
                if "hash mismatch" in err.what:
                    run.attempts.append(attempt)
                    run.alarm.add("hash_mismatch")
                    run.last_reason = "execution_failed"
                    return "stop", None
                dec = decide(state)
                run.last_reason = dec.reason
                if dec.alarm:
                    run.alarm.add(dec.alarm)
                if dec.action == "reconnect" and resend == 0:
                    run.attempts.append(
                        attempt
                    )  # kept for the record; the resend is not a model attempt
                    self.sleep(self.s.transient_backoff_s)
                    continue
                run.attempts.append(attempt)
                if dec.action == "abort":
                    run.abort, run.last_reason = True, "execution_failed"
                    return "stop", None
                if dec.action in ("stop", "reconnect"):
                    return "stop", None
                if dec.action == "retry_once":
                    key = state or "none"
                    if key in once:
                        return "stop", None
                    once.add(key)
                return "retry", dec.hint
            timing = {**base, "duration_ms": base["duration_ms"] + _ms(t)}
            run.attempts.append(
                Attempt(rows=len(res.rows), truncated=res.truncated, **common, **timing)
            )
            run.result, run.ok = res, ok
            return "done", None
        return "stop", None

    # ---------------------------------------------------------------------------------------------- finish
    def _finish(self, run: _Run, latency_ms: int) -> Answer:
        clarifying: str | None = None
        if run.result is not None:
            outcome, reason = "answered", None
        elif run.abstain is not None:
            reason = run.abstain.abstain_reason
            outcome = REASONS[reason].outcome
            clarifying = run.abstain.clarifying_question
        elif run.reason:  # a gate
            reason = run.reason
            outcome = REASONS[reason].outcome
        else:
            reason = pick_reason([*run.terminal, *([run.last_reason] if run.last_reason else [])])
            outcome = REASONS[reason].outcome
        final = None
        if run.result is not None and run.ok is not None:
            final = Final(
                sql_sha256=run.ok.sha256, canonical_sql=run.ok.canonical_sql, wire_sha256=run.result.wire_sha256 or run.ok.sha256,
                result_sha256=run.result.result_sha256, row_count=len(run.result.rows), truncated=run.result.truncated,
            )  # fmt: skip
        try:
            snap = self.meter.snapshot()
            budget = Budget(
                spent_usd=fmt_usd(snap["askdata_spent"]), cap_usd=fmt_usd(snap["demo_cap"])
            )  # type: ignore[arg-type]
        except MeterError:
            budget = Budget(spent_usd="0", cap_usd="0")
        route = self.routes[self.s.route]
        fields: dict[str, Any] = dict(  # noqa: C408
            query_id=run.query_id, ts=run.ts, asker=run.asker,
            question=clean(run.question)[:500] if self.s.store_question else None, question_sha256=run.q_sha,
            outcome=outcome, reason_code=reason, rule_id=run.rule_id,
            attempts=run.attempts[: 6], final=final, assumptions=run.assumptions[:20], intent_event_ids=run.intents,
            prompt_sha256=self.prompt.prompt_sha256, config_hash=self.config_hash, catalog_sha256=self.prompt.catalog_sha256,
            model_id=run.model_id or route.model_id, route=self.s.route, tokens_in=run.tokens_in, tokens_out=run.tokens_out,
            cost_usd=fmt_usd(run.cost), latency_ms=latency_ms, budget=budget, alarm=sorted(run.alarm),
        )  # fmt: skip
        try:
            line = LedgerLine(**fields)
        except ValidationError:  # never lose the question: a minimal failed line is still written
            outcome, reason, final = "failed", "execution_failed", None
            line = LedgerLine(
                **{
                    **fields,
                    "outcome": outcome,
                    "reason_code": reason,
                    "attempts": [],
                    "final": None,
                    "assumptions": [],
                }
            )
        sha = self.ledger.append(line)
        self.audit.outcome(
            run.query_id, question_sha256=run.q_sha, decision=outcome, ledger_sha256=sha,
            sql_sha256=final.sql_sha256 if final else None, rule_id=line.rule_id, error_code=reason,
        )  # fmt: skip
        sentence = "" if outcome == "answered" else REASONS[reason].sentence  # type: ignore[index]
        if outcome == "answered" and run.result is not None and not run.result.rows:
            sentence = NO_ROWS_NOTE
        return Answer(
            query_id=run.query_id, outcome=outcome, reason=reason, exit_code=exit_code(outcome, reason), sentence=sentence,
            line=line, ledger_sha256=sha, result=run.result, canonical_sql=final.canonical_sql if final else None,
            sql_sha256=final.sql_sha256 if final else None, assumptions=run.assumptions, clarifying_question=clarifying,
            abort=run.abort,
        )  # fmt: skip


@dataclass
class _Run:
    query_id: str
    ts: str
    asker: str
    question: str
    q_sha: str
    attempts: list[Attempt] = field(default_factory=list)
    intents: list[str] = field(default_factory=list)
    terminal: list[str] = field(default_factory=list)
    alarm: set[str] = field(default_factory=set)
    assumptions: list[str] = field(default_factory=list)
    reason: str | None = None  # a gate's reason
    last_reason: str | None = None
    rule_id: str | None = None
    cost: Decimal = Decimal(0)
    tokens_in: int = 0
    tokens_out: int = 0
    model_id: str = ""
    abstain: Any = None
    result: RunResult | None = None
    ok: Validated | None = None
    abort: bool = False
    calls: int = 0


def _ms(t: float) -> int:
    return int((time.monotonic() - t) * 1000)


__all__ = ["Answer", "Executor", "Pipeline", "Settings"]
