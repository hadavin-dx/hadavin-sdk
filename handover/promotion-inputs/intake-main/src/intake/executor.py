"""The single governed writer (purpose-limit). The agent never holds a draft-store put method: it PROPOSES an action here, naming only `kind`, `key`, `payload`, a `receipt_id` and (for a
clarification) `body` and `attachments`. EVERYTHING the executor's safety depends on is derived SERVER-SIDE, never read from the proposal:
  * the verified sender (hence the only allowed recipient and the cap bucket) comes from the ledger receipt, which the ingest gateway wrote with its own authentication result;
  * whether an action class needs approval comes from the ACTION_CLASSES table below (policy `executor.approval_required_classes`);
  * whether it was approved comes from the human-side service's signed-record check (`approved(action_key)`), not from a flag in the proposal.
Order of checks: type and class allowlist (a non-string or unknown kind is a typed denial, never an exception), kill switch, receipt, egress on the clarification, approval, dry-run (the
default: nothing is written), per-day and per-sender caps counting only NEW effects, then the idempotent write and a recorded undo (compensation by rejecting, never deleting).
Every refusal is a typed denial: {"status": "refused", "denial": <code>, "reason": ...} with a code from DENIALS."""

from __future__ import annotations

from collections.abc import Callable

from .egress import check_egress

DENIALS = ("bad_action", "forbidden_class", "kill_switch", "unknown_receipt", "egress", "needs_approval", "cap", "nothing_to_undo")
ACTION_CLASSES = {"draft": {"needs_approval": False}, "flag": {"needs_approval": False}, "clarification": {"needs_approval": False}}
FORBIDDEN = frozenset(
    {
        "alter_schema",
        "bulk_delete",
        "grant_permission",
        "change_permission",
        "rotate_credential",
        "change_credential",
        "erp_write",
        "payment",
        "release_payment",
        "update_customer",
        "delete_order",
    }
)


class FakeExecutor:
    def __init__(
        self,
        writer,
        compensate: Callable[[str], None],
        ledger,
        *,
        approved: Callable[[str], bool] = lambda _key: False,
        approval_required: tuple[str, ...] = (),
        dry_run: bool = True,
        kill_switch: bool = False,
        max_writes_per_day: int = 500,
        max_writes_per_sender_per_day: int = 50,
    ) -> None:
        self._writer, self._compensate, self._ledger, self._approved = writer, compensate, ledger, approved
        self._approval_required = set(approval_required)
        self.dry_run, self.kill_switch = dry_run, kill_switch
        self._cap_day, self._cap_sender = max_writes_per_day, max_writes_per_sender_per_day
        self._today = 0
        self._per_sender: dict[str, int] = {}
        self._done: dict[str, dict] = {}
        self.audit: list[dict] = []

    def _deny(self, code: str, reason: str) -> dict:
        r = {"status": "refused", "denial": code, "reason": reason}
        self.audit.append(r)
        return r

    def _ok(self, status: str, **extra) -> dict:
        r = {"status": status, **extra}
        self.audit.append(r)
        return r

    def propose(self, action: object) -> dict:
        if not isinstance(action, dict) or not isinstance(action.get("kind"), str) or not isinstance(action.get("key"), str):
            return self._deny("bad_action", "an action needs a string kind and a string key")
        kind = action["kind"]
        if kind in FORBIDDEN or kind not in ACTION_CLASSES:
            return self._deny("forbidden_class", "action class is outside the executor's allowlist")
        if self.kill_switch:
            return self._deny("kill_switch", "kill switch is on")
        rid = action.get("receipt_id")
        receipt = self._ledger.get(rid) if isinstance(rid, str) else None
        if receipt is None:
            return self._deny("unknown_receipt", "no ledger receipt for this action")
        verified = receipt.verified_sender
        if kind == "clarification":
            payload = action.get("payload")
            recipient = getattr(payload, "recipient", None)
            problems = check_egress(
                recipient=recipient,
                verified_sender=verified,
                body=str(action.get("body", "")),
                attachments=tuple(action.get("attachments", ())),
            )
            if problems:
                return self._deny("egress", "; ".join(problems))
        if (kind in self._approval_required or ACTION_CLASSES[kind]["needs_approval"]) and not self._approved(action["key"]):
            return self._deny("needs_approval", "no signed approval record")
        if self.dry_run:
            return self._ok("dry_run", reason="nothing was written", would_write={"kind": kind, "key": action["key"]})
        bucket = (verified or "unverified:" + receipt.message_id.split("@")[-1]).casefold()
        if self._today >= self._cap_day or self._per_sender.get(bucket, 0) >= self._cap_sender:
            return self._deny("cap", "write cap reached")
        method = getattr(self._writer, f"put_{kind}")
        res = method(action["key"], action["payload"], *action.get("extra", ()), sender=bucket)
        if res.outcome == "applied":
            self._today += 1
            self._per_sender[bucket] = self._per_sender.get(bucket, 0) + 1
        eid = f"x-{len(self._done) + 1:06d}"
        self._done[eid] = {"draft_id": res.draft_id, "outcome": res.outcome, "undone": False}
        return self._ok(res.outcome, execution_id=eid, draft_id=res.draft_id)

    def undo(self, execution_id: str) -> dict:
        rec = self._done.get(execution_id) if isinstance(execution_id, str) else None
        if rec is None or rec["undone"] or rec["outcome"] != "applied":
            return self._deny("nothing_to_undo", "nothing to undo")
        self._compensate(rec["draft_id"])
        rec["undone"] = True
        return self._ok("undone", reason="compensated by rejecting the draft (no delete)", execution_id=execution_id)
