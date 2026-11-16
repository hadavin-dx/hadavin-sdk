"""Least-privilege identity table (least privilege). Deny-all start, exact actions, no wildcard, one identity per function.
Every public operation of Desk, Executor and the ports declares the action it needs (`requires`), so the table is enforced at each entry, not in three
places (review class 'identity enforced in three places only'). `JUSTIFICATION` gives the per-action reason; tests/test_controls.py holds the negative test of every denied pair."""

from __future__ import annotations

import functools

from dealdesk.errors import NotPermitted

ACTIONS = (
    "crm.read", "billing.read", "directory.read", "inbound.submit", "quote.propose", "quote.edit", "approval.request", "decision.record", "approval.expire",
    "quote.draft", "quote.commit", "quote.void_commit", "quote.read_status", "audit.append", "audit.read", "ledger.write", "ledger.read", "killswitch.set",
    "schema.migrate", "deploy.ci", "breakglass.use", "reply.send",
)  # fmt: skip

IDENTITIES: dict[str, frozenset[str]] = {
    "agent_runtime": frozenset(
        {"crm.read", "billing.read", "directory.read", "quote.propose", "quote.edit", "approval.request", "quote.read_status", "reply.send"}
    ),
    "decision_service": frozenset({"crm.read", "billing.read", "directory.read"}),  # the engine's own verifier: re-reads the systems of record for a decision; holds no write
    "requester_rep": frozenset({"inbound.submit", "quote.read_status"}),
    "approver_commercial": frozenset({"decision.record", "quote.read_status"}),
    "approver_legal": frozenset({"decision.record", "quote.read_status"}),
    "approver_finance": frozenset({"decision.record", "quote.read_status"}),
    "draft_writer": frozenset({"quote.draft", "crm.read", "billing.read", "directory.read"}),
    "commit_executor": frozenset({"quote.commit", "quote.void_commit", "crm.read", "billing.read", "directory.read"}),
    "scheduler": frozenset({"approval.expire"}),
    "ingest_writer": frozenset({"ledger.write", "audit.append"}),
    "reconciler": frozenset({"ledger.read", "audit.read"}),
    "audit_reader": frozenset({"audit.read"}),
    "support_operator": frozenset({"quote.read_status", "audit.read"}),
    "kill_switch_operator": frozenset({"killswitch.set"}),
    "migrations": frozenset({"schema.migrate"}),
    "ci_deploy": frozenset({"deploy.ci"}),
    "breakglass_dormant": frozenset(),  # granted only through a recorded, time-boxed process; holds nothing at rest
}  # fmt: skip

JUSTIFICATION = {
    ("agent_runtime", "crm.read"): "read the deal to compute the proposal", ("agent_runtime", "billing.read"): "read list price and terms",
    ("agent_runtime", "directory.read"): "route steps to roles", ("agent_runtime", "quote.propose"): "create a proposal (read-only class, no external effect)",
    ("agent_runtime", "quote.edit"): "supersede its own proposal; voids approvals, never creates them",
    ("agent_runtime", "approval.request"): "open the next approval step; a person decides", ("agent_runtime", "quote.read_status"): "tell the rep the status",
    ("requester_rep", "inbound.submit"): "send the request message", ("requester_rep", "quote.read_status"): "see own request status",
    ("approver_commercial", "decision.record"): "sign one decision for the commercial lane", ("approver_legal", "decision.record"): "legal lane decision",
    ("approver_finance", "decision.record"): "finance lane decision", ("draft_writer", "quote.draft"): "the single writer of drafts to the sink",
    ("commit_executor", "quote.commit"): "the single governed executor of the commit step", ("commit_executor", "quote.void_commit"): "recorded undo",
    ("scheduler", "approval.expire"): "expire unanswered approvals", ("ingest_writer", "ledger.write"): "write-ahead receipt of inbound messages",
    ("ingest_writer", "audit.append"): "append audit", ("reconciler", "ledger.read"): "compare ledger with source ids", ("reconciler", "audit.read"): "verify the chain",
    ("audit_reader", "audit.read"): "review", ("support_operator", "quote.read_status"): "support", ("support_operator", "audit.read"): "support read",
    ("kill_switch_operator", "killswitch.set"): "stop the executor (holds, never voids)", ("migrations", "schema.migrate"): "schema change window only",
    ("ci_deploy", "deploy.ci"): "ship a reviewed build",
}  # fmt: skip
JUSTIFICATION.update(
    {
        (i, a): "read-only support for its single function"
        for i, acts in IDENTITIES.items()
        for a in acts
        if (i, a) not in JUSTIFICATION
    }
)


def authorize(identity: object, action: str) -> None:
    if action not in ACTIONS:
        raise NotPermitted(f"unknown action {action!r}")
    if not isinstance(identity, str) or action not in IDENTITIES.get(identity, frozenset()):
        raise NotPermitted(f"{identity!r} may not {action}")


def requires(action: str):
    """Decorator: the first positional argument after self is the calling identity."""

    def deco(fn):
        @functools.wraps(fn)
        def wrapper(self, who, *a, **k):
            authorize(who, action)
            return fn(self, who, *a, **k)

        wrapper.required_action = action
        return wrapper

    return deco
