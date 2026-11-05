"""Checks every demo-export must pass for this demo (stage 2 calls `check_export` in its export test; stage 1 unit-tests it).

Strict by design: a missing or empty list is an error (an export with no cases proves nothing), ports are compared case-insensitively
(an adapter named 'ERP' or 'erp_rest' is an ERP port), an ERP op must be an exact read method name ('POST', 'Create_Order' fail),
`executed` must be a mapping or null, and outcomes come from a closed set."""

from __future__ import annotations

from .adapters.port import READ_METHODS

TIERS = {"human", "four_eyes", "blocked"}
OUTCOMES = {"proposed", "approved", "rejected", "blocked", "abstained", "failed", "unknown", "no_action"}


def check_export(ex: dict) -> list[str]:
    errs: list[str] = []
    for key in ("cases", "approvals", "adapter_calls"):
        if not isinstance(ex.get(key), list):
            errs.append(f"{key}: missing or not a list")
    if not ex.get("cases"):
        errs.append("cases: empty (an export with no cases proves nothing)")
    for a in ex.get("approvals") or []:
        if a.get("tier") not in TIERS:
            errs.append(f"approval {a.get('approval_id')}: tier {a.get('tier')!r} not allowed (never 'auto')")
        e = a.get("executed")
        if e is not None:
            if not isinstance(e, dict):
                errs.append(f"approval {a.get('approval_id')}: executed must be a mapping or null")
            elif e.get("port") != "draft_store":
                errs.append(f"approval {a.get('approval_id')}: executed.port must be draft_store, got {e.get('port')!r}")
        ap = a.get("approvers")
        if a.get("tier") == "four_eyes" and not (isinstance(ap, list) and len(ap) >= 2):
            errs.append(f"approval {a.get('approval_id')}: four_eyes needs an ordered list of at least two approvers")
    for c in ex.get("cases") or []:
        if c.get("outcome") not in OUTCOMES:
            errs.append(f"case {c.get('case_id')}: outcome {c.get('outcome')!r} not in the allowed set (never auto_allowed)")
        if "tier" in c and c["tier"] not in TIERS | {None}:
            errs.append(f"case {c.get('case_id')}: tier {c.get('tier')!r} not allowed")
    for call in ex.get("adapter_calls") or []:
        port = str(call.get("port", "")).lower()
        if port.startswith("erp") and call.get("op") not in READ_METHODS:
            errs.append(f"adapter call {call.get('call_id')}: ERP op {call.get('op')!r} is not an exact read method")
    return errs
