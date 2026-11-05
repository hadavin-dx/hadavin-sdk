"""Differential tests: the implementation against the SECOND author's oracle (tests/oracle_indep.py, written from the spec alone).
Seeded random inputs (no extra dependency). A disagreement is either an implementation bug or a spec ambiguity; each one is resolved in gate_rules.md."""

import json

import oracle_indep as oi
import pytest
from engine_kit import BOOK, MATRIX, POLICY, D
from properties_rng import Mini

from dealdesk import desk_rules as dr

NOW, TODAY = "2026-11-09T09:00:00Z", "2026-11-09"
CLAUSES = list(POLICY["clauses"])
BAD_CLAUSES = ["MFN_pricing", " mfn_pricing", "mfn_pricing ", "nope", "", "liability_cap_2x\u200b"]
REGIONS = list(POLICY["tax"]["rates_bps"])
CCY = ["USD", "GBP", "EUR", "CAD", "AUD"]


def rand_case(r):
    ccy = CCY[r.n(5)]
    d = {"plan": ["team", "business", "enterprise"][r.n(3)], "currency": ccy, "customer_tier": ["smb", "mid", "enterprise", "strategic"][r.n(4)],
         "request_type": ["new", "expansion", "renewal"][r.n(3)], "seats": 1 + r.n(900), "arr_minor": str(r.n(80_000_000)), "deal_id": "deal-1",
         "account_id": "acct-1", "tax_region": POLICY["tax"]["default_region"][ccy] if r.n(10) else REGIONS[r.n(len(REGIONS))]}  # fmt: skip
    bps = [0, 1, 999, 1000, 1001, 2000, 2001, 3000, 3001, 4000, 4001, 5000, 9999, 10000][r.n(14)] if r.n(2) else r.n(10001)
    t = {"discount_bps": bps, "term_years": 1 + r.n(3), "billing": ["annual_prepay", "quarterly", "monthly"][r.n(3)],
         "payment_terms_days": [30, 45, 60, 90, 120][r.n(5)], "sla_tier": ["standard", "enhanced", "custom"][r.n(3)]}  # fmt: skip
    cl = [CLAUSES[r.n(len(CLAUSES))] for _ in range(r.n(4))]
    if r.n(12) == 0:
        cl.append(BAD_CLAUSES[r.n(len(BAD_CLAUSES))])
    others = []
    for i in range(r.n(4)):
        lt = 500_000 * (1 + r.n(200))
        others.append({"deal_id": f"deal-{2 + r.n(3)}" if r.n(6) else "deal-1", "currency": ccy if r.n(5) else CCY[r.n(5)], "list_total": lt,
                       "discount": lt * r.n(5000) // 10000, "state": ["pending", "approved", "drafted", "committed", "rejected", "superseded"][r.n(6)],
                       "created_ts": ["2026-11-01T00:00:00Z", "2026-08-11T09:00:00Z", "2026-08-11T08:59:59Z", "2026-07-01T00:00:00Z", "2026-11-20T00:00:00Z"][r.n(5)]})  # fmt: skip
    claim = r.n(8) == 0
    cert = [None, "2026-11-08", "2026-11-09", "2027-01-01"][r.n(4)]
    return d, t, cl, others, claim, cert


def norm_impl(f):
    if f.deny:
        return {"deny": f.deny}
    return {"deny": None, "list_total": f.list_total, "discount": f.discount, "net": f.net, "tax_minor": f.tax_minor, "total": f.total,
            "size_band": f.size_band, "discount_band": f.discount_band, "zone": f.zone, "blocked": list(f.blocked),
            "steps": [list(s) for s in f.steps], "cum_bps": f.cum_bps, "downsell": f.downsell}  # fmt: skip


def norm_or(o):
    if o.get("deny"):
        return {"deny": o["deny"]}
    return {k: ([list(s) for s in o[k]] if k == "steps" else list(o[k]) if k == "blocked" else o[k]) for k in
            ("deny", "list_total", "discount", "net", "tax_minor", "total", "size_band", "discount_band", "zone", "blocked", "steps", "cum_bps", "downsell")}  # fmt: skip


def test_evaluate_full_agrees_with_the_independent_oracle_on_3000_random_cases():
    r, n_deny, n_block, n_cum, n_clause = Mini(20261101), 0, 0, 0, 0
    for i in range(3000):
        d, t, cl, others, claim, cert = rand_case(r)
        a = norm_impl(dr.evaluate_full(d, BOOK, MATRIX, POLICY, t, cl, others, NOW, TODAY, claim, cert))
        try:
            b = norm_or(oi.evaluate_full(d, BOOK, MATRIX, POLICY, t, cl, others, NOW, TODAY, claim, cert))
        except ValueError:
            b = None
        assert a == b, (i, d, t, cl, others, claim, cert, a, b)
        n_deny += bool(a["deny"])
        n_block += bool(a.get("blocked"))
        n_cum += a.get("cum_bps") is not None
        n_clause += bool(cl)
    assert n_deny > 100 and n_block > 100 and n_cum > 100 and n_clause > 1000  # the sample actually exercises every branch


def test_accept_decision_agrees_with_the_oracle_on_every_combination_of_the_nine_checks():
    people = {None: None, "ok": {"person_id": "p1", "employee_id": "e1", "role": "regional_vp", "active": True},
              "inactive": {"person_id": "p1", "employee_id": "e1", "role": "regional_vp", "active": False},
              "low": {"person_id": "p1", "employee_id": "e1", "role": "sales_manager", "active": True},
              "wrong_lane": {"person_id": "p1", "employee_id": "e1", "role": "legal_counsel", "active": True},
              "self": {"person_id": "p9", "employee_id": "e9", "role": "regional_vp", "active": True}}  # fmt: skip
    n = 0
    for state in ("open", "decided", "expired", "voided"):
        for sig in (True, False):
            for ap in people.values():
                for acc in ([], ["e1"]):
                    for qh in (True, False):
                        for sn in (True, False):
                            for dt in (0, 72 * 3600, 72 * 3600 + 1, -1):
                                ts = 1_793_000_000
                                f = lambda s: (
                                    __import__("datetime")
                                    .datetime.fromtimestamp(s, __import__("datetime").UTC)
                                    .strftime("%Y-%m-%dT%H:%M:%SZ")
                                )
                                kw = dict(state=state, sig_ok=sig, approver=ap, requester={"person_id": "p9", "employee_id": "e9"}, accepted_employees=acc,  # noqa: C408
                                          lane="commercial", min_role="regional_vp", matrix=MATRIX, quote_hash_ok=qh, snapshot_ok=sn, request_ts=f(ts), receipt_ts=f(ts + dt))  # fmt: skip
                                assert dr.accept_decision(**kw) == oi.accept_decision(**kw), kw
                                n += 1
    assert n == 4 * 2 * 6 * 2 * 2 * 2 * 4


def _texts():
    out = []
    for f in ("dev_a", "dev_b"):
        for line in (D / f"demo_only/data/{f}.jsonl").read_text(encoding="utf-8").splitlines():
            c = json.loads(line)
            out.append((c["case_id"], c["request"]["text"]))
    return out


@pytest.mark.parametrize(("cid", "text"), _texts())
def test_trace_agrees_with_the_oracle_on_every_gold_message(cid, text):
    from dealdesk import gate_rules as g

    a, b = g.traceability(text), oi.trace(text)
    assert (a["status"], a["reason"], a["discount_bps"], a["price"]) == (
        b["status"],
        b["reason"],
        b["discount_bps"],
        b["price"],
    ), (cid, a, b)
    if a["status"] != "ok":
        return  # hand-backs carry no terms in the oracle
    got = {k: v for k, v in a["terms"].items()}
    assert got == {k: b["terms"].get(k) for k in got}, (cid, a["terms"], b["terms"])
