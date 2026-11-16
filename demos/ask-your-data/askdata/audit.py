"""Audit mapping (design 10): the core `AuditSink` holds hashes and codes only; the ledger holds the text.

One INTENT event per execution, written through `write_intent` BEFORE the statement is sent (a failure raises
`AuditUnavailable` and nothing runs). One OUTCOME event per question through `write_outcome` (never raises); its
`result` is the SHA-256 of the exact ledger line. The sink is any `AuditSink`; `local_dir` is the demo default.

The only integrity claim made anywhere is "local integrity check": it finds accidental damage and edits that touch
one file; it does not stop someone who can write both the ledger and the audit folder.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from askdata.ledger import QueryLedger
from hadavin_sdk.audit.local_dir import LocalDirSink
from hadavin_sdk.audit.protocol import AuditSink
from hadavin_sdk.models import AuditEvent

DOMAIN = "askdata"
SOURCE = "askdata-cli"
DISCLAIMER = (
    "This detects accidental damage and edits that touch only one file. "
    "It does not stop someone who can write this folder from rewriting both."
)


def local_dir_sink(root: Path) -> AuditSink:
    """The demo default sink. A client config picks another kind; the pipeline only needs the protocol."""
    return LocalDirSink(Path(root))


class AskAudit:
    def __init__(self, sink: AuditSink, *, principal: str) -> None:
        self.sink = sink
        self.principal = principal  # "claimed:<name>": there is no authentication

    def intent(self, query_id: str, *, question_sha256: str, sql_sha256: str) -> str:
        """Write the intent for ONE execution; returns its event id. Raises `AuditUnavailable`."""
        event = AuditEvent(
            run_id=query_id, domain=DOMAIN, operation="execute", principal=self.principal, source=SOURCE,
            object_ref=sql_sha256, inputs_hash=question_sha256, decision="intent",
        )  # fmt: skip
        self.sink.write_intent(event)
        return event.event_id

    def outcome(
        self,
        query_id: str,
        *,
        question_sha256: str,
        decision: str,
        ledger_sha256: str,
        sql_sha256: str | None = None,
        rule_id: str | None = None,
        error_code: str | None = None,
    ) -> None:
        """Write the outcome after the ledger line is stored. Never raises (the sink keeps it in its outbox)."""
        self.sink.write_outcome(
            AuditEvent(
                run_id=query_id,
                domain=DOMAIN,
                operation="ask",
                principal=self.principal,
                source=SOURCE,
                object_ref=sql_sha256,
                inputs_hash=question_sha256,
                decision=decision,
                rule_id=rule_id,
                result=ledger_sha256,
                error_code=error_code,
            )
        )

    def switch(self, state: str) -> None:
        """Record a kill-switch change BEFORE the flag file changes (raises `AuditUnavailable`)."""
        self.sink.write_intent(
            AuditEvent(
                run_id="0" * 32,
                domain=DOMAIN,
                operation="killswitch",
                principal=self.principal,
                source=SOURCE,
                decision=state,
            )
        )


@dataclass
class VerifyReport:
    events_ok: int = 0
    events_total: int = 0
    lines_ok: int = 0
    lines_total: int = 0
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return (
            not self.problems
            and self.events_ok == self.events_total
            and self.lines_ok == self.lines_total
        )

    def text(self) -> str:
        head = (
            f"local integrity check: {self.events_ok} of {self.events_total} events "
            f"and {self.lines_ok} of {self.lines_total} ledger lines match"
        )
        body = [f"  problem: {p}" for p in self.problems]
        return "\n".join([head, *body, DISCLAIMER])


def verify(ledger: QueryLedger, sink: AuditSink) -> VerifyReport:
    """Check every event object against the sink's index, every ledger line against its outcome event's `result`,
    and reconcile: each executed attempt has an intent event, each outcome has a line and each line an outcome."""
    rep = VerifyReport()
    read = ledger.read()
    try:
        events = [e for e in sink.events() if e.domain == DOMAIN]
    except (
        OSError,
        ValueError,
        KeyError,
    ):  # a missing or corrupt event object: report it, do not crash
        events = []
        rep.problems.append("the audit events could not be read (missing or corrupt object)")
    rep.events_total = len(events)
    for e in events:
        try:
            ok = sink.verify_object(
                f"{e.event_id}.json"
            )  # the sink's object key is "<event_id>.json"
        except OSError:
            ok = False
        rep.events_ok += ok
        if not ok:
            rep.problems.append(f"event {e.event_id} does not match the audit index")
    rep.lines_total = len(read.items) + len(read.bad)
    for n in read.bad:
        rep.problems.append(f"ledger line {n} is torn or invalid")
    outcomes = {e.run_id: e for e in events if e.operation == "ask"}
    intents = {e.event_id: e for e in events if e.operation == "execute"}
    referenced: set[str] = set()
    seen: set[str] = set()
    for item in read.items:
        line = item.line
        out = outcomes.get(line.query_id)
        if line.query_id in seen:
            rep.problems.append(f"query {line.query_id[:8]} appears twice in the ledger")
        seen.add(line.query_id)
        if out is None:
            rep.problems.append(f"ledger line {item.number} has no outcome event")
        elif out.result != item.sha256:
            rep.problems.append(f"ledger line {item.number} differs from its outcome event")
        else:
            rep.lines_ok += 1
        for attempt in line.attempts:
            if attempt.executed and attempt.intent_event_id not in intents:
                rep.problems.append(
                    f"query {line.query_id[:8]} attempt {attempt.n} ran without an intent event"
                )
        for eid in line.intent_event_ids:
            referenced.add(eid)
            if eid not in intents or intents[eid].run_id != line.query_id:
                rep.problems.append(f"query {line.query_id[:8]} names a missing intent event")
    for qid in outcomes.keys() - seen:
        rep.problems.append(f"outcome event for query {qid[:8]} has no ledger line")
    for eid in intents.keys() - referenced:
        rep.problems.append(f"intent event {eid} is not in any ledger line")
    return rep
