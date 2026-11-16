"""Pure decision helpers around the classifier (R-APEXC-016..030). Everything the executor and the approval wrapper will
call in stage 2; written and unit-tested now so the rules are executable, not prose. `off` switches a rule off for the
mutation check. No clock: callers pass timestamps (the Clock port in ports.py is the only source of "now")."""

from __future__ import annotations

import hashlib
import json
import re
import threading
from datetime import timedelta

from apexc.classify import (
    NONE,
    attester_ok,
    classify_full,
    cumulative_minor,
    emp,
    evidence_fresh,
    has_step,
    master_editors,
    roles_of,
    tier_for,
    ver_ok,
)
from apexc.normalise import minor, norm_id, parse_ts
from apexc.ports import IdempotencyConflict

UNDO_COMMAND_TEMPLATE = "dequeue {key}"
FREE_TEXT_CAP = 2000
UNTRUSTED_TEXT = frozenset(
    {
        "invoice.invoice_number",
        "invoice.lines",
        "invoice.memo",
        "invoice.footer",
        "invoice.email_body",
        "invoice.vendor_name",
        "vendor.name",
        "po.lines",
    }
)


def render_undo_command(key: str) -> str:
    """The declared undo of release_to_payment_queue as the core's `undo_test` must render it."""
    return UNDO_COMMAND_TEMPLATE.format(key=key)


# ---- holds and lifting ------------------------------------------------------------------------------------
def holds_for(types: set[str]) -> list[str]:
    """R-APEXC-020: one hold per reason, placed by deterministic code (actor=system) from classifier output."""
    return sorted(types)


def reasons_lifted(action: str, pol: dict) -> set[str]:
    """A ruling action lifts only the hold reasons listed for it; waiting/rejecting/escalating/handing back lift nothing."""
    return set(pol["ruling_lifts"].get(action, []))


def evidence_ok(
    action: str,
    reason: str,
    evidence: dict | None,
    lifter: str,
    directory: dict,
    callbacks: dict,
    vendor_id: str,
    pol: dict,
    led: dict | None = None,
) -> bool:
    """M-7/M6: a lifting ruling on an evidence-bearing hold must carry evidence that RESOLVES in a ledger, or it lifts nothing:
    a receipt id must be a GRN on one of this invoice's POs; a corrected-invoice ref must be a correction logged for THIS invoice
    and vendor; a ruling id must be a not_duplicate ruling row for THIS invoice made by the lifter; a callback id must be a
    confirmed callback record. An id already used by another invoice is refused. `led` carries the ledgers
    (invoice, grns, corrections, rulings, used_by); without it nothing resolves, so the answer is False (fail closed)."""
    need = pol["lift_evidence"].get(action)
    if need is None:
        return True
    val = (evidence or {}).get(need)
    if not isinstance(val, str) or not val or led is None:
        return False
    inv = led["invoice"]
    if led.get("used_by", {}).get(val, inv["invoice_id"]) != inv["invoice_id"]:
        return False  # evidence cannot be re-used across invoices
    ctx = {"directory": directory}
    if action == "confirm_receipt":
        g = led["grns"].get(val)
        return bool(g) and g["po_id"] in inv["po_refs"]
    if action == "accept_corrected":
        c = led["corrections"].get(val)
        return bool(c) and c["invoice_id"] == inv["invoice_id"] and c["vendor_id"] == vendor_id
    if action == "verify_new_vendor":
        rec = callbacks.get(val)
        return (
            bool(rec)
            and rec["state"] == "confirmed"
            and rec["topic"] == "new_vendor"
            and rec["vendor_id"] == vendor_id
            and attester_ok(rec["attested_by"], {lifter}, ctx, pol)
        )
    if action == "confirm_not_duplicate":
        mine = [r for r in led["rulings"] if r["invoice_id"] == inv["invoice_id"] and r["ruling"] == "not_duplicate"]
        row = next((r for r in mine if r["ruling_id"] == val and r["by"] == lifter), None)
        if row is None:
            return False
        if reason != "cross_vendor_duplicate":
            return True
        second = (evidence or {}).get("second_lifter")  # two people who both ACTED (a ruling row each), or a controller
        two = (
            bool(second)
            and second in directory
            and emp(ctx, second) != emp(ctx, lifter)
            and has_step(ctx, second, "approve_resolution", pol)
            and any(r["by"] == second for r in mine)
        )
        return "finance_controller" in roles_of(ctx, lifter) or two
    return False


def can_lift_hold(reason: str, *, actor: str, user_id: str, directory: dict, ruling_actions: set[str], cleared: bool, pol: dict,
                  evidence: dict | None = None, callbacks: dict | None = None, vendor_id: str = "", led: dict | None = None) -> bool:  # fmt: skip
    """R-APEXC-020: person-only lifting; roles come from the DIRECTORY, never from the caller. A hold on reason R is lifted only
    by a ruling ACTION that lists R (reasons_lifted) made by a person holding approve_resolution WITH the action's evidence;
    duplicate_exact needs a finance controller; a hard-block hold only by the clear step (clear_hard_block)."""
    ctx = {"directory": directory}
    if actor != "human" or user_id not in directory:
        return False
    roles = roles_of(ctx, user_id)
    steps = {s for r in roles for s in pol["roles"].get(r, [])}
    if reason in pol["hard_block_types"]:
        return cleared and "clear_hard_block" in steps
    acts = [a for a in ruling_actions if reason in reasons_lifted(a, pol)]
    if not acts or "approve_resolution" not in steps:
        return False
    if not any(evidence_ok(a, reason, evidence, user_id, directory, callbacks or {}, vendor_id, pol, led) for a in acts):
        return False
    return "finance_controller" in roles if reason == "duplicate_exact" else True


def clear_evidence_ok(typ: str, evidence_id: str, clearer: str, case: dict, pol: dict) -> bool:
    """Fail closed: a malformed ledger record (missing field, bad timestamp) is simply not valid evidence."""
    try:
        return _clear_evidence_ok(typ, evidence_id, clearer, case, pol)
    except (KeyError, TypeError, ValueError, AttributeError):
        return False


def _clear_evidence_ok(typ: str, evidence_id: str, clearer: str, case: dict, pol: dict) -> bool:
    """B3: a hard-block clear needs evidence that RESOLVES in the callback ledger: a confirmed record for THIS vendor whose topic is the
    one `clear_topic_by_type` names for the type, with the dialled number on the vendor's trusted list (an attestation topic needs
    none), attested by someone with attest_callback who is a different PERSON from the clearer, the submitter and every master editor;
    the person who made the vendor's earlier bank verification may not attest a fresh callback (attest_conflict)."""
    ctx, v = case["context"], case["context"]["vendor"]
    rec = ctx["callbacks"].get(evidence_id)
    if rec is None or not attest_topic_ok(rec["topic"], typ, pol):
        return False
    topic = rec["topic"]
    excluded = master_editors(ctx) | {case["invoice"]["submitted_by"], clearer}
    ver = {"callback_id": evidence_id, "attested_by": rec.get("attested_by"), "ts": rec.get("ts")}
    if not (
        ver_ok(ver, topic, v, ctx)
        and attester_ok(rec["attested_by"], excluded, ctx, pol)
        and evidence_fresh(topic, rec["ts"], ctx, pol)  # B-1: newer than the change it clears, with no later master event
    ):
        return False
    prior = (v["bank"].get("verification") or {}).get("attested_by")
    fresh_call = prior is not None and (v["bank"].get("verification") or {}).get("callback_id") != evidence_id
    return not (topic == "bank" and fresh_call and attest_conflict(prior, rec["attested_by"], ctx["directory"]))


def hold_aging_due(placed_at: str, now: str, pol: dict) -> bool:
    """R-APEXC-020: a hold older than hold_aging_days escalates to a human (never auto-lifts)."""
    return parse_ts(now) - parse_ts(placed_at) >= timedelta(days=pol["windows"]["hold_aging_days"])


def hold_pressure(n_held_invoices_for_vendor: int, n_held_by_submitter_today: int, pol: dict) -> dict:
    """R-APEXC-020: the hold is ALWAYS placed (never fail open past a cap). Past the caps a human is told, and the submitter is rate
    limited. Counts are INVOICES, not hold reasons."""
    h = pol["holds"]
    return {"place": True, "escalate": n_held_invoices_for_vendor >= h["max_open_invoices_per_vendor"],
            "rate_limit_submitter": n_held_by_submitter_today >= h["max_per_submitter_per_day"]}  # fmt: skip


# ---- time and approvals -----------------------------------------------------------------------------------
def cooling_ok(start_ts: str, now: str, pol: dict, off: frozenset = NONE) -> bool:
    """R-APEXC-022: release allowed when now >= start + cooling_off_hours (inclusive)."""
    if "R-APEXC-022" in off:
        return True
    return parse_ts(now) >= parse_ts(start_ts) + timedelta(hours=pol["windows"]["cooling_off_hours"])


def approval_expired(requested_at: str, now: str, pol: dict) -> bool:
    """R-APEXC-030: an approval request older than approvals.ttl_hours is void."""
    return parse_ts(now) - parse_ts(requested_at) > timedelta(hours=pol["approvals"]["ttl_hours"])


def undo_window_open(queued_at: str, now: str, pol: dict) -> bool:
    """The queue entry can be dequeued until min_queue_to_run_hours after queueing; times are absolute (UTC)."""
    return parse_ts(now) < parse_ts(queued_at) + timedelta(hours=pol["queue"]["min_queue_to_run_hours"])


def role_allows(roles: list[str], step: str, pol: dict) -> bool:
    return any(step in pol["roles"].get(r, []) for r in roles)


def sod_violations(steps: list[tuple[str, str]], directory: dict, pol: dict, off: frozenset = NONE) -> list[str]:
    """R-APEXC-019: `steps` = [(user_id, step)] for ONE invoice, keyed on the PERSON (employee id)."""
    if "R-APEXC-019" in off:
        return []
    ctx = {"directory": directory}
    out = []
    by_person: dict[str, set[str]] = {}
    for user, step in steps:
        by_person.setdefault(emp(ctx, user), set()).add(step)
        if step in pol["distinct_steps"] and not role_allows(roles_of(ctx, user), step, pol):
            out.append(f"{user}:{step}:role_lacks_step")
    out += [f"{p}:{'+'.join(sorted(s))}" for p, s in by_person.items() if len(s & set(pol["distinct_steps"])) > 1]
    return out


def attest_conflict(prior_verifier: str, attester: str, directory: dict) -> bool:
    """The person who made the pre-existing bank verification may not also attest the callback of the same invoice."""
    ctx = {"directory": directory}
    return emp(ctx, prior_verifier) == emp(ctx, attester)


def approver_cap_ok(n_cleared_short: int, pol: dict, n_cleared_long: int = 0) -> bool:
    """R-APEXC-016: cap on invoices one PERSON may clear for one vendor, in the short (cumulative) AND the long window."""
    t = pol["tiers"]
    return n_cleared_short < t["approver_cap_per_vendor_window"] and n_cleared_long < t["approver_cap_long"]


def choose_approver(eligible: list[str], counts: dict, vendor_total_cleared: int, directory: dict, pol: dict) -> tuple[str | None, str]:
    """Picks the first eligible approver whose PERSON (employee id) is under both caps; `counts` is keyed by employee id. When the
    vendor as a whole is at its window cap, or every eligible approver is capped, the answer is an explicit escalation to a
    human review queue, never a silent stall."""
    ctx = {"directory": directory}
    if vendor_total_cleared >= pol["tiers"]["vendor_cap_per_window"]:
        return None, "escalate:vendor_cap"
    for u in eligible:
        c = counts.get(emp(ctx, u), {})
        if approver_cap_ok(c.get("short", 0), pol, c.get("long", 0)):
            return u, "ok"
    return None, "escalate:approver_capacity"


def roster_gap(directory: dict, submitter: str) -> list[str]:
    """The hard-block path needs four DIFFERENT people besides the submitter: a clearer and a plan-1 approver (both controllers), an
    attester and a plan-2 approver (treasury or controller). A small client may not have them; the gap is escalated outside, not waited on."""
    sub = directory[submitter]["employee_id"] if submitter in directory else None
    people = {}
    for rec in directory.values():
        if rec["employee_id"] != sub:
            people.setdefault(rec["employee_id"], set()).update(rec["roles"])
    ctl = {e for e, r in people.items() if "finance_controller" in r}
    trs = {e for e, r in people.items() if "treasury_officer" in r}
    gap = []
    if len(ctl) < 2:
        gap.append("two finance_controller people")
    if not trs:
        gap.append("one treasury_officer")
    if len(ctl | trs) < 4:
        gap.append("four distinct controller/treasury people")
    return gap


def attest_topic_ok(topic: str, exception_type: str, pol: dict) -> bool:
    """The callback being attested must be about the exception it clears: bank for bank_change, contact for contact_change..."""
    return pol["clear_topic_by_type"].get(exception_type) == topic


# ---- identities -------------------------------------------------------------------------------------------
def identity_can(identity: str, op: str, pol: dict, kind: str = "write") -> bool:
    """Least privilege (hard rule): exact rights per identity, from policy.identities."""
    return op in pol["identities"].get(identity, {}).get(kind, [])


def authorize_op(identity: str, op: str, pol: dict, kind: str = "write") -> None:
    """Enforcement point: every STATE-CHANGING executor/ERP/ledger/payments/callout/egress method calls this first (the read port calls it for reads); a call by the wrong identity is DENIED. Pure reads of the fakes (lookup, open_holds) take no identity."""
    if not identity_can(identity, op, pol, kind):
        raise PermissionError(f"{identity} may not {kind} {op}")


def identity_conflicts(pol: dict) -> list[str]:
    """No identity may hold both an approval-side right and an action-side right (the approver never acts, the actor never approves)."""
    c = pol["identity_conflicts"]
    return [
        i for i, r in pol["identities"].items() if set(r["write"]) & set(c["approval_side"]) and set(r["write"]) & set(c["action_side"])
    ]


def resolution_tier(action: str, types: set[str], band_tier: str, pol: dict, off: frozenset = NONE) -> tuple[str, bool]:
    """R-APEXC-016 (direction split). Returns (tier, controller_required)."""
    if action == "escalate_hard_block":
        return "blocked", True
    if action in pol["no_money_actions"]:
        return ("human_nonmoney" if band_tier != "none" else "none"), False
    if action == "confirm_not_duplicate":
        return band_tier, "duplicate_exact" in types and "R-APEXC-008" not in off
    return band_tier, False


def may_reject(directory: dict, user: str, earlier_submitter: str, current_submitter: str, pol: dict) -> bool:
    """Who may set an invoice to 'rejected': per the directory a supervisor or controller who is a different PERSON from both
    the earlier invoice's submitter and the current one."""
    ctx = {"directory": directory}
    me = emp(ctx, user)
    return (
        me != emp(ctx, earlier_submitter)
        and me != emp(ctx, current_submitter)
        and any(r in pol["reject_roles"] for r in roles_of(ctx, user))
    )


# ---- release binding, recheck, idempotency ----------------------------------------------------------------
def case_tier(case: dict, pol: dict, off: frozenset = NONE) -> tuple[set[str], set[str], str]:
    types, ev = classify_full(case, pol, off)
    inv = case["invoice"]
    return types, ev, tier_for(types, inv["currency"], cumulative_minor(case, pol), pol, off)


def cleared_types(records: list[dict], directory: dict, pol: dict) -> set[str]:
    """B-2: the ledgered, explicit set of exception types a person cleared (who, when, evidence id). A hard-block type needs the
    clear step (clear_hard_block), anything else approve_resolution; a record without an evidence id clears nothing."""
    ctx = {"directory": directory}
    out = set()
    for r in records:
        step = "clear_hard_block" if r["type"] in pol["hard_block_types"] else "approve_resolution"
        if r.get("evidence_id") and r["by"] in directory and has_step(ctx, r["by"], step, pol):
            out.add(r["type"])
    return out


def binding_fields(case: dict, pol: dict, cleared: frozenset | set = frozenset()) -> dict:
    """What an approval is bound to (R-APEXC-029): invoice, amount, currency, the release tier AFTER the hard blocks that were
    cleared, master version (REQUIRED), payee tuple, the cleared set and the original types. A cleared new_vendor keeps its
    four-eyes floor: only hard-block types leave the tier computation."""
    inv, v = case["invoice"], case["context"]["vendor"]
    b = v["bank"]
    types = classify_full(case, pol)[0]
    tier = tier_for(types - (set(cleared) & set(pol["hard_block_types"])), inv["currency"], cumulative_minor(case, pol), pol)
    return {"invoice_id": inv["invoice_id"], "vendor_id": v["vendor_id"], "total_minor": str(minor(inv["total_minor"])), "currency": inv["currency"], "tier": tier,
            "invoice_number": inv["invoice_number"], "po_refs": list(inv["po_refs"]),
            "lines": hashlib.sha256(json.dumps(inv["lines"], sort_keys=True).encode()).hexdigest()[:16], "master_version": v["master_version"], "payee": [norm_id(b["account"]), norm_id(b["routing"]), norm_id(b["bank_name"])],
            "cleared": sorted(cleared), "types": sorted(types)}  # fmt: skip


def _typed(rec, required: dict, optional: dict | None = None) -> bool:
    """Exact keys and exact types (a bool is not an int, an int is not a float, NaN is never an int): one shape check for every ledger row."""
    if not isinstance(rec, dict):
        return False
    spec = {**required, **(optional or {})}
    if not set(required) <= set(rec) <= set(spec):
        return False
    return all(type(rec[k]) in (spec[k] if isinstance(spec[k], tuple) else (spec[k],)) for k in rec)


def _str_list(x) -> bool:
    return type(x) is list and all(type(i) is str for i in x)


BOUND_FIELDS = {"invoice_id": str, "vendor_id": str, "total_minor": str, "currency": str, "tier": str, "invoice_number": str, "po_refs": list,
                "lines": str, "master_version": int, "payee": list, "cleared": list, "types": list}  # fmt: skip
APPROVAL_FIELDS = {"approval_id": str, "invoice_id": str, "vendor_id": str, "plan": str, "by": str, "bound": dict, "config_version": str,
                   "currency": str, "single_minor": int, "ts": str, "consumed": bool}  # fmt: skip


def validate_approval(row) -> bool:
    """M1 (v7): the ONE shape an approval row may have, checked on write, on every read that counts it and at release. Exact keys and types, the
    bound set with exactly the binding fields (no odd keys), a parseable timestamp. A forged or half-written row is simply not an approval."""
    try:
        if not _typed(row, APPROVAL_FIELDS):
            return False
        b = row["bound"]
        if (
            not _typed(b, BOUND_FIELDS)
            or not all(_str_list(b[k]) for k in ("po_refs", "payee", "cleared", "types"))
            or len(b["payee"]) != 3
        ):
            return False
        parse_ts(row["ts"])
        minor(b["total_minor"])
        return row["single_minor"] >= 0
    except (KeyError, TypeError, ValueError):
        return False


def validate_ruling(row) -> bool:
    return _typed(row, {k: str for k in ("ruling_id", "invoice_id", "history_id", "ruling", "by", "role")}, {"ts": str})


def validate_clear(rec) -> bool:
    return _typed(rec, {"invoice_id": str, "type": str, "by": str, "kind": str, "evidence_id": (str, type(None))}, {"ts": str})


def validate_evidence(ev) -> bool:
    """Lift evidence: a flat dict of strings (ids and names), nothing else."""
    return ev is None or (type(ev) is dict and all(type(k) is str and type(v) is str for k, v in ev.items()))


def payee_binding(vendor: dict) -> str:
    b = vendor["bank"]
    return hashlib.sha256(
        json.dumps([norm_id(b["account"]), norm_id(b["routing"]), norm_id(b["bank_name"]), vendor["master_version"]]).encode()
    ).hexdigest()


def release_recheck(
    fresh_case: dict, bound: dict, pol: dict, cleared_records: list[dict] | None = None, off: frozenset = NONE
) -> tuple[bool, str | None]:
    """R-APEXC-017/029. From FRESH reads recompute the binding fields (tier and cumulative included, with the ledgered cleared set)
    and refuse on any difference; then refuse any type that was NOT in the original classification (`new_types`) and any hard-block,
    abstain or new-vendor type that was not explicitly cleared (`uncleared`). Re-running the classifier is fine now: its output is
    compared with the ORIGINAL classification and the ledgered cleared set, so a cleared hard block, a verified new vendor and a
    cooled-off bank change all pass, while a NEW bank edit, a raised total or a new collision does not."""
    if "R-APEXC-017" in off:
        return True, None
    cleared = cleared_types(cleared_records or [], fresh_case["context"]["directory"], pol)
    now_fields = binding_fields(fresh_case, pol, cleared)
    diff = sorted(k for k in now_fields if k != "types" and now_fields[k] != bound[k])
    if diff:
        return False, "binding_mismatch:" + ",".join(diff)
    fresh = set(now_fields["types"])
    new = fresh - set(bound["types"])
    if new:
        return False, "new_types:" + ",".join(sorted(new))
    bad = (fresh & (set(pol["hard_block_types"]) | set(pol["abstain_types"]) | {"new_vendor"})) - cleared
    if bad:
        return False, "uncleared:" + ",".join(sorted(bad))
    return True, None


class ApplyDenied(Exception):
    """The payments port definitely refused (nothing was applied)."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class ReleaseStore:
    """Reference ordering for execute-time work (R-APEXC-023/029). Under ONE lock: look the key up; found with the same payload
    returns the stored status (`duplicate_ignored` once applied, `pending` while an earlier attempt is unresolved, `dequeued`
    after an undo), found with a different payload raises IdempotencyConflict; a NEW key inserts a `pending` row BEFORE the
    recheck/apply, so a retry after `timeout_after_apply` can never apply twice (it sees `pending` and must `reconcile`)."""

    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}
        self.rechecks = 0
        self.applies = 0
        self._lock = threading.Lock()

    def peek(self, key: str, payload: dict) -> tuple[bool, str] | None:
        """(same payload?, status) of the one row for this key, or None. Used to answer a replay or an edited re-release."""
        with self._lock:
            row = self.rows.get(key)
            return None if row is None else (row["blob"] == json.dumps(payload, sort_keys=True), row["status"])

    def lookup(self, key: str) -> dict | None:
        with self._lock:
            row = self.rows.get(key)
            return None if row is None else {"status": row["status"], "result": row["result"]}

    def snapshot(self) -> tuple[dict, int, int]:
        """A consistent copy of the rows and the counters, taken under this store's own lock (ControlState.to_json uses it)."""
        with self._lock:
            return {k: dict(r) for k, r in self.rows.items()}, self.rechecks, self.applies

    def execute(self, key: str, payload: dict, recheck, apply) -> tuple[str, dict | None]:
        blob = json.dumps(payload, sort_keys=True)
        with self._lock:
            row = self.rows.get(key)
            if row is not None:
                if row["blob"] != blob:
                    raise IdempotencyConflict(key)
                return {"applied": "duplicate_ignored"}.get(row["status"], row["status"]), row["result"]
            self.rows[key] = {"blob": blob, "status": "pending", "result": None}
            self.rechecks += 1
        try:
            ok, why = recheck()
        except (
            BaseException
        ):  # minor 2: a recheck that crashes applied nothing, so it must not strand a `pending` row (sticky until reconcile)
            with self._lock:
                self.rows.pop(key, None)
            raise
        if not ok:
            with self._lock:
                del self.rows[key]  # nothing was applied: a denial leaves no row, so a corrected retry can run
            return "denied:" + (why or ""), None
        try:
            result = apply()  # may raise (timeout after apply): the row stays `pending` until reconcile
        except ApplyDenied as e:  # a definite refusal (unique index, bad ruling): nothing applied, so no row is left pending
            with self._lock:
                del self.rows[key]
            return "denied:" + e.reason, None
        with self._lock:
            self.rows[key].update(status="applied", result=result)
            self.applies += 1
        return "applied", result

    def reconcile(self, key: str, found: dict | None) -> str:
        """Resolve a `pending` row from a lookup in the payments port: found => applied (no second apply); not found => safe retry."""
        with self._lock:
            row = self.rows[key]
            if row["status"] != "pending":
                return row["status"]
            if found is None:
                del self.rows[key]
                return "retry_safe"
            if found.get("status") == "dequeued":  # m5 (review 9): only a COMPLETE queue entry is "applied"
                row["status"] = "dequeued"
                return "dequeued"
            if found.get("status") != "queued":
                return "pending"  # an incomplete entry: a person looks; nothing is called a success
            row.update(status="applied", result=found)
            self.applies += 1
            return "applied"

    def dequeue(self, key: str) -> str:
        with self._lock:
            row = self.rows[key]
            if row["status"] == "applied":
                row["status"] = "dequeued"
            return row["status"]


def check_unique(entries: list[dict], new: dict, pol: dict, directory: dict, rulings: list[dict]) -> str | None:
    """R-APEXC-010 reference: the two unique indexes of the payments fake. A collision can be bypassed only by a RULING ID resolved
    against the ledger: it must exist, be the LATEST ruling for this (invoice, earlier invoice) pair, be a not_duplicate ruling for THIS
    invoice made by a finance controller (directory role) who is not the submitter, name the ONE earlier invoice (`history_id`) it
    collides with, and not be used by any other entry (`RulingReused`). Without a collision the ruling is never consulted. A made-up
    id, a ruling for another invoice, a revoked, reused or mis-aimed one all leave the collision standing."""
    ctx = {"directory": directory}
    rid = new.get("duplicate_ruling_id")
    rows = [x for x in rulings if x["ruling_id"] == rid] if rid else []
    r = max(rows, key=lambda x: parse_ts(x["ts"])) if rows else None
    latest = (
        max(
            (x for x in rulings if (x["invoice_id"], x["history_id"]) == (r["invoice_id"], r["history_id"])),
            key=lambda x: parse_ts(x["ts"]),
        )
        if r
        else None
    )

    def bypass(e: dict, collision: str) -> str:
        if not rid:
            return collision
        if (
            r is None
            or latest is not r
            or r["ruling"] != "not_duplicate"
            or r["invoice_id"] != new["invoice_id"]
            or r["role"] != "finance_controller"
            or r["role"] not in roles_of(ctx, r["by"])
            or emp(ctx, r["by"]) == emp(ctx, new.get("submitted_by", ""))
        ):
            return "InvalidRuling"
        if any(x.get("duplicate_ruling_id") == rid and x["idempotency_key"] != new["idempotency_key"] for x in entries):
            return "RulingReused"
        return collision if r["history_id"] != e["invoice_id"] else ""

    for e in entries:
        if e["idempotency_key"] == new["idempotency_key"]:
            continue
        if (e["vendor_id"], e["norm_number"], e["currency"], e["total_minor"]) == (
            new["vendor_id"],
            new["norm_number"],
            new["currency"],
            new["total_minor"],
        ):
            if err := bypass(e, "DuplicateBusinessKey"):
                return err
        if (e["vendor_id"], e["po_key"], e["currency"], e["total_minor"], e["received_day"]) == (
            new["vendor_id"],
            new["po_key"],
            new["currency"],
            new["total_minor"],
            new["received_day"],
        ):
            if err := bypass(e, "DuplicateExposure"):
                return err
    return None


def controller_present(tier: str, approver_roles: list[list[str]], pol: dict) -> bool:
    """R-APEXC-016/018: in tier four_eyes_over_max at least one of the approvers is a finance controller."""
    if not pol["approver_sets"].get(tier, {}).get("controller_required_in_one"):
        return True
    return any("finance_controller" in roles for roles in approver_roles)


def callback_slots_ok(template_id: str, slots: dict[str, str], pol: dict) -> bool:
    """R-APEXC-021: slot values come from structured values and must fullmatch the template's slot patterns exactly."""
    # M5: email templates are slot-validated too
    spec = pol["callback_templates"].get(template_id) or pol["email_templates"].get(template_id)
    if spec is None or set(slots) != set(spec["slots"]):
        return False
    return all(type(v) is str and re.fullmatch(spec["slots"][k], v) is not None for k, v in slots.items())


def expected_kind(types: set[str], tier: str, pol: dict) -> str:
    if types & set(pol["abstain_types"]):
        return "hand_back"
    if tier == "blocked":
        return "blocked_escalation"
    return "resolution" if types else "approve_match"


def allowed_actions(kind: str, types: set[str], pol: dict) -> set[str]:
    if kind == "hand_back":
        return {"hand_back"}
    if kind == "blocked_escalation":
        return {"escalate_hard_block"}
    if kind == "approve_match":
        return {"approve_match"}
    acts = {pol["recommended_action_by_type"][t] for t in types if t in pol["recommended_action_by_type"]} | {"request_credit"}
    for t in types:
        if t in pol["lift_action_by_type"]:
            acts.add(pol["lift_action_by_type"][t])
    return acts


def proposal_denial(args: dict, types: set[str], tier: str, captured_total: str, currency: str, pol: dict) -> str | None:
    """R-APEXC-015/017: the model's proposal must agree with the deterministic classifier output."""
    kind = expected_kind(types, tier, pol)
    if args["kind"] != kind:
        return "kind_mismatch"
    if args["recommended_action"] not in allowed_actions(kind, types, pol):
        return "action_not_allowed"
    if minor(args["amount_minor"]) != minor(captured_total) or args["currency"] != currency:
        return "amount_mismatch"
    return None


def scorecard_verdict_color(color: str, mode: str) -> str:
    """A scripted run can never score green: it is capped at amber (recording, not behaviour)."""
    return "amber" if mode == "scripted" and color == "green" else color


def scorecard_verdict_text(color: str) -> str:
    """The verdict text never claims live accuracy, whatever the colour (spec_stage2.md section 4)."""
    return f"Scripted plumbing check ({color}): the rules and gates behaved as designed on synthetic cases; not a statement about live accuracy."


def namespace(pol: dict, kind: str) -> str:
    """segregation: every per-client store, index, embedding set, cache, few-shot pool, eval set, log, secret and model config lives under
    `<client_id>/<kind>`; there is no shared namespace and an unknown kind raises."""
    if kind not in pol["namespaces"]:
        raise KeyError(kind)
    return f"{pol['client_id']}/{kind}"


def forbidden_paths(pol: dict) -> list[str]:
    """Path fragments of OTHER demos' data, evals, memory and kit examples that nothing in apexc may read."""
    return list(pol["isolation"]["forbidden_paths"])


def purpose_of(path: str, pol: dict) -> str:
    """purpose limitation: the stated purpose of a field. A field with no stated purpose is not used at all (KeyError)."""
    return pol["purposes"][path]


def last4(x: str) -> str:
    return norm_id(x)[-4:]


def model_view(case: dict, pol: dict) -> dict:
    """purpose limitation/R-APEXC-015: the ONLY thing the model sees, built from an allowlist (`policy.model_visible`). Vendor bank account,
    routing, tax id, phone, email, other vendors, history, rulings, callbacks and the directory are never in it; the invoice's own
    account and tax id appear as their last 4 only; free text is capped and marked untrusted."""
    inv, ctx = case["invoice"], case["context"]

    def cap(x):
        return x[:FREE_TEXT_CAP] if isinstance(x, str) else x

    full = {
        "invoice.invoice_number": cap(inv["invoice_number"]),
        "invoice.currency": inv["currency"],
        "invoice.lines": [
            {"line": ln["line"], "desc": cap(ln["desc"]), "qty": ln["qty"], "unit_price_minor": ln["unit_price_minor"]}
            for ln in inv["lines"]
        ],
        "invoice.total_minor": inv["total_minor"],
        "invoice.memo": cap(inv["memo"]),
        "invoice.footer": cap(inv["footer"]),
        "invoice.email_body": cap(inv["email_body"]),
        "invoice.vendor_name": cap(inv["vendor_claimed"]["name"]),
        "invoice.remit_account_last4": last4(inv["remit"]["account"]),
        "invoice.tax_id_last4": last4(inv["vendor_claimed"]["tax_id"]),
        "vendor.name": cap((ctx["vendor"] or {}).get("name")),
        "po.po_id": cap((ctx["po"] or {}).get("po_id")),
        "po.lines": [
            {
                "line": ln["line"],
                "desc": cap(ln["desc"]),
                "qty": ln["qty"],
                "unit_price_minor": ln["unit_price_minor"],
                "tax_rate_bp": ln["tax_rate_bp"],
            }
            for ln in (ctx["po"] or {}).get("lines", [])
        ],
        "receipts.qty": {str(r["line"]): r["qty"] for r in ctx["receipts"]},
    }
    view = {k: full[k] for k in pol["model_visible"]}
    view["untrusted_text_fields"] = sorted(k for k in view if k in UNTRUSTED_TEXT)  # vendor-controlled text: data, never instructions
    return view
