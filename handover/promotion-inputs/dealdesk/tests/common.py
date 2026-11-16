"""Shared test helpers: load the data, and run an implementation (gate or oracle) in one normalised shape."""

import json
from pathlib import Path

import oracle

from dealdesk import gate_rules as gate

D = Path(__file__).resolve().parent.parent
M = json.loads((D / "config/approval_matrix.json").read_text())
BOOK = json.loads((D / "tests/fixtures/pricebook.json").read_text())
CODE = {
    "sales_manager": "c:sm", "regional_vp": "c:rvp", "cro": "c:cro", "legal_counsel": "l:lc",
    "general_counsel": "l:gc", "finance_controller": "f:fc", "cfo": "f:cfo",
}  # fmt: skip
STD = {"discount_bps": 0, "term_years": 1, "billing": "annual_prepay", "payment_terms_days": 30, "sla_tier": "standard"}


def deal(plan="enterprise", ccy="USD", seats=10, tier="strategic", rtype="new", arr="0"):
    return {"plan": plan, "currency": ccy, "seats": seats, "customer_tier": tier, "request_type": rtype, "arr_minor": arr}


def run_gate(d, terms):
    ev = gate.evaluate(d, BOOK, M, terms)
    return {"blocked": list(ev.blocked_by), "steps": [CODE[r] for _lane, r in ev.steps], "zone": ev.zone, "band": ev.size_band}


def run_oracle(d, terms):
    ev = oracle.evaluate(d, BOOK, M, terms)
    return {"blocked": ev["blocked"], "steps": [CODE[r] for _lane, r in ev["steps"]], "zone": ev["zone"], "band": ev["band"]}


IMPLS = [run_gate, run_oracle]
