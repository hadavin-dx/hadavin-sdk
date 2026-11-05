"""Test harness helpers: the ONLY place a clock can be advanced, and the scenario-to-executor runner (end-to-end flows).

The harness plays the PEOPLE (it lifts, clears and approves as the scenario's users would, through the executor's own methods, which
validate everything against the ledgers). It never hands the executor a bound set, a cooling start, extra SoD steps or a cleared set:
`Executor.release(invoice_id, approval_ids)` derives all of that itself."""

from __future__ import annotations

import copy
from datetime import timedelta

from apexc.classify import classify_full, duplicates, roles_of
from apexc.executor import Executor
from apexc.fakes import Audit, FakeClock, FakeErp, FakePayments
from apexc.normalise import fmt_ts, parse_ts


class HarnessClock(FakeClock):
    def set(self, ts: str) -> None:
        self._t = parse_ts(ts)

    def advance(self, minutes: int) -> None:
        self._t += timedelta(minutes=minutes)


def build(case: dict, pol: dict, tenant: str = "t1", level: str = "suggest", schedule=None, live: bool = True, audit=None):
    """Fakes loaded with the case's world, an executor, and the clock at the case's time."""
    ctx = case["context"]
    clock = HarnessClock(ctx["now"])
    erp = FakeErp(tenant, pol, clock)
    erp.vendors[ctx["vendor"]["vendor_id"]] = copy.deepcopy(ctx["vendor"])
    erp.callbacks.update(ctx["callbacks"])
    erp.callbacks.update({c["callback_id"]: c for c in case["scenario"]["callbacks"]})
    erp.rulings = copy.deepcopy(ctx.get("rulings", []))
    erp.cases[case["invoice"]["invoice_id"]] = copy.deepcopy(case)
    pay = FakePayments(tenant, ctx["directory"], pol, schedule)
    audit = audit or Audit()
    return erp, pay, clock, audit, Executor(erp, pay, clock, audit, pol, ctx["directory"], level, live=live)


def _attester(case: dict, taken: set[str]) -> str:
    """A treasury officer (attest_callback) who is none of the people already on this invoice."""
    d = case["context"]["directory"]
    ids = {d[u]["employee_id"] for u in taken if u in d}
    return next(u for u, r in d.items() if "treasury_officer" in r["roles"] and r["employee_id"] not in ids)


def evidence_for(erp: FakeErp, case: dict, pol: dict, typ: str, taken: set[str]) -> str:
    """The callback-ledger record a clear of `typ` rests on: the scenario's own record when its topic fits, else one the harness
    writes (an out-of-band confirmation by another person, stamped at the scenario's cooling start)."""
    sc, ctx = case["scenario"], case["context"]
    topic, ev = pol["clear_topic_by_type"][typ], sc["clear"]["evidence_id"]
    rec = erp.callbacks.get(ev)
    if rec and rec["topic"] == topic:
        return ev
    new = f"{ev}-{topic}"
    if new not in erp.callbacks:
        start = fmt_ts(parse_ts(ctx["now"]) + timedelta(minutes=sc["cooling_start_min"]))
        erp.callbacks[new] = {"callback_id": new, "vendor_id": ctx["vendor"]["vendor_id"], "topic": topic, "state": "confirmed",
                              "dialed": ctx["vendor"]["contact"]["trusted_phones"][0], "attested_by": _attester(case, taken), "ts": start}  # fmt: skip
    return new


def settle(ex: Executor, erp: FakeErp, case: dict, pol: dict) -> None:
    """Place the holds, then lift and clear them as the scenario's people would (through the executor, which validates)."""
    ctx, sc = case["context"], case["scenario"]
    inv_id, inv = case["invoice"]["invoice_id"], case["invoice"]
    ex.place_holds(inv_id)
    people = {inv["submitted_by"]} | {a["by"] for a in sc["approvals"]} | ({sc["clear"]["by"]} if sc["clear"] else set())
    for _ in range(3):  # a ruling can reveal a further exception (it gets its own hold): keep lifting until nothing is open
        types = classify_full(erp.read_case(inv_id), pol)[0]
        todo = [t for t in sorted(types) if erp.hold_rows(inv_id).get(t, {"open": True})["open"]]
        if not todo:
            break
        for t in todo:
            if t in pol["hard_block_types"]:
                if sc["clear"]:
                    ex.clear(inv_id, t, sc["clear"]["by"], evidence_for(erp, case, pol, t, people))
                continue
            for lf in sc["lifts"]:
                if pol["lift_action_by_type"].get(t) != lf["action"]:
                    continue
                ev = lf.get("evidence") or {}
                if lf["action"] == "confirm_receipt":
                    erp.grns[ev["receipt_id"]] = {"po_id": inv["po_refs"][0]}
                elif lf["action"] == "accept_corrected":
                    erp.corrections[ev["corrected_ref"]] = {"invoice_id": inv_id, "vendor_id": ctx["vendor"]["vendor_id"]}
                elif lf["action"] == "confirm_not_duplicate" and not any(
                    r["ruling_id"] == ev["ruling_id"] and r["by"] == lf["by"] for r in erp.rulings
                ):
                    role = (
                        "finance_controller" if "finance_controller" in roles_of({"directory": ex.directory}, lf["by"]) else "ap_supervisor"
                    )
                    for hid in sorted(duplicates(inv, ctx, pol)[1]) or [""]:
                        erp.add_ruling(role, {"ruling_id": ev["ruling_id"], "invoice_id": inv_id, "history_id": hid, "ruling": "not_duplicate",
                                              "by": lf["by"], "role": role, "ts": fmt_ts(parse_ts(ctx["now"]) + timedelta(minutes=1))})  # fmt: skip
                ex.lift(inv_id, t, lf["by"], lf["action"], lf.get("evidence"))


def _plan1_after_a_lift(case: dict) -> str:
    """M1: lifting a hold and approving plan 1 are different duties, so plan 1 is a supervisor who is none of the lifters, the submitter or the
    plan-2 approvers (the scenario data names the lifter as its approver; the harness plays the second person the rule now demands)."""
    d, sc = case["context"]["directory"], case["scenario"]
    taken = {
        d[u]["employee_id"]
        for u in [lf["by"] for lf in sc["lifts"]]
        + [case["invoice"]["submitted_by"]]
        + [a["by"] for a in sc["approvals"] if a["plan"] == "plan_2"]
    }
    return next(u for u, r in sorted(d.items(), key=lambda kv: (not kv[0].startswith("u-sup"), kv[0])) if "ap_supervisor" in r["roles"] and r["employee_id"] not in taken)  # fmt: skip


def approvals_spec(case: dict) -> list[tuple[str, str]]:
    """(person, plan) the scenario's approvals: after a lift plan 1 is ANOTHER supervisor (M1), else the first approver."""
    sc = case["scenario"]
    out = []
    if sc["lifts"]:
        out.append((_plan1_after_a_lift(case), "plan_1"))
    elif sc["approvals"]:
        out.append((sc["approvals"][0]["by"], "plan_1"))
    return out + [(a["by"], "plan_2") for a in sc["approvals"] if a["plan"] == "plan_2"]


def approve_all(ex: Executor, case: dict) -> list[str]:
    return [ex.approve(case["invoice"]["invoice_id"], by, plan)["approval_id"] for by, plan in approvals_spec(case)]


def run_release(case: dict, pol: dict, fresh: dict | None = None, mutate=None, schedule=None, level: str = "suggest"):
    """Settle the holds, move to the final release attempt of the scenario, collect the approvals, optionally change the world (the
    swapped payee / raised amount of the scenarios), then release."""
    erp, pay, clock, audit, ex = build(case, pol, level=level, schedule=schedule)
    ctx, sc = case["context"], case["scenario"]
    inv_id = case["invoice"]["invoice_id"]
    settle(ex, erp, case, pol)
    last = sc["release_attempts"][-1]
    clock.set(fmt_ts(parse_ts(ctx["now"]) + timedelta(minutes=last["at_min"])))
    ids = approve_all(ex, case)
    if fresh is not None:
        erp.cases[inv_id] = copy.deepcopy(fresh)
        if fresh["context"]["vendor"]:
            erp.vendors[fresh["context"]["vendor"]["vendor_id"]] = copy.deepcopy(fresh["context"]["vendor"])
    if mutate:
        mutate(ex, erp, pay)
    out = ex.release(inv_id, ids)
    return out, ex, erp, pay


def cleared_records(case: dict, pol: dict) -> list[dict]:
    """Shape-valid ledger rows for the PURE rule tests (release_recheck / cleared_types); the executor tests go through Executor.clear."""
    sc, exp = case["scenario"], case["expected"]
    recs = []
    if sc["clear"]:
        for t in exp["exception_types"]:
            if t in pol["hard_block_types"]:
                recs.append({"type": t, "by": sc["clear"]["by"], "ts": "t", "evidence_id": sc["clear"]["evidence_id"], "kind": "clear"})
    for lf in sc["lifts"]:
        if lf["action"] == "verify_new_vendor":
            recs.append({"type": "new_vendor", "by": lf["by"], "ts": "t", "evidence_id": lf["evidence"]["callback_id"], "kind": "verify"})
    return recs


def led_for(case: dict) -> dict:
    """The ledgers that make the scenario's own lift evidence resolve (for the pure can_lift_hold tests)."""
    inv, vid = case["invoice"], case["context"]["vendor"]["vendor_id"]
    led = {"invoice": inv, "grns": {}, "corrections": {}, "rulings": list(case["context"].get("rulings", [])), "used_by": {}}
    for lf in case["scenario"]["lifts"]:
        ev = lf.get("evidence") or {}
        if "receipt_id" in ev:
            led["grns"][ev["receipt_id"]] = {"po_id": inv["po_refs"][0]}
        if "corrected_ref" in ev:
            led["corrections"][ev["corrected_ref"]] = {"invoice_id": inv["invoice_id"], "vendor_id": vid}
        if "ruling_id" in ev:
            led["rulings"].append({"ruling_id": ev["ruling_id"], "invoice_id": inv["invoice_id"], "history_id": "h", "ruling": "not_duplicate",
                                   "by": lf["by"], "role": "finance_controller", "ts": "2026-10-20T10:00:00Z"})  # fmt: skip
    return led
