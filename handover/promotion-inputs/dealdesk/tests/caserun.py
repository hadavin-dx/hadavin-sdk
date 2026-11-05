"""Runs a gold file (the dev gold, or the held-out split run by tests_oneshot) against the implementation. Used by the default run (dev) and tests_oneshot (test)."""

import threading

from engine_kit import BOOK, MATRIX, POLICY, STD, Kit, mk_deal

from dealdesk import desk_rules as dr
from dealdesk import gate_rules as g

NOW, TODAY = "2026-11-09T09:00:00Z", "2026-11-09"


def norm(f):
    if f.deny:
        return {"deny": f.deny}
    return {"deny": None, "list_total": f.list_total, "discount": f.discount, "net": f.net, "tax_minor": f.tax_minor, "total": f.total, "size_band": f.size_band,
            "discount_band": f.discount_band, "zone": f.zone, "blocked": list(f.blocked), "steps": [list(s) for s in f.steps], "cum_bps": f.cum_bps,
            "downsell": f.downsell}  # fmt: skip


def check_decide(row):
    i = row["input"]
    got = norm(
        dr.evaluate_full(
            i["deal"], BOOK, MATRIX, POLICY, i["terms"], i["clauses"], i["others"], NOW, TODAY, i["claim"], i["cert"]
        )
    )
    exp = {k: row["expected"].get(k) for k in got}
    return got == exp


def check_accept(row):
    acc, rule = dr.accept_decision(matrix=MATRIX, **row["input"])
    return {"accepted": acc, "rule_id": rule} == row["expected"]


def check_trace(row):
    a = g.traceability(row["input"]["text"])
    e = row["expected"]
    ok = (a["status"], a["reason"], a["discount_bps"]) == (e["status"], e["reason"], e["discount_bps"]) and a["price"] == (
        tuple(e["price"]) if e["price"] else None
    )
    if e["status"] == "ok" and e.get("terms"):
        ok = ok and a["terms"] == e["terms"]
    return ok


def _k(seats, plan="business", ccy="USD", ids=("deal-b",), acct="acct-s", name="Scenario Works"):
    deals = [mk_deal(d, acct, name, plan=plan, ccy=ccy, seats=seats) for d in ids]
    return Kit(deals=deals)


def run_scenario(row):
    s, p, ag = row["scenario"], row["params"], "agent_runtime"
    if s == "edit_after_approval":
        k = _k(p["seats"])
        q1 = k.propose("deal-b", {"discount_bps": p["bps"]})["quote_id"]
        k.desk.request_approval(ag, q1)
        old = k.open_approval(q1)
        k.decide(old, "p-sm-01")
        r2 = k.desk.edit_quote(ag, q1, terms={**STD, "discount_bps": p["bps2"]})
        k.desk.request_approval(ag, r2["quote_id"])
        a2 = k.open_approval(r2["quote_id"])
        k.decide(a2, "p-rvp-01", quote_hash=old["quote_hash"], terms_hash=old["terms_hash"])
        rec = k.store.get("decisions", f"{len(k.store.names('decisions')) - 1:08d}")
        return {"old_state": k.desk.status(ag, q1)["state"], "old_commit": k.ex.commit("commit_executor", q1, dry_run=False)["outcome"], "new_status": r2["status"],
                "stale_replay_rule": rec["rule_id"]}  # fmt: skip
    if s == "window_boundary":
        k = _k(p["seats"])
        q = k.propose("deal-b", {"discount_bps": p["bps"]})["quote_id"]
        k.desk.request_approval(ag, q)
        a = k.open_approval(q)
        k.clock.advance(hours=72, seconds=p["extra_s"])
        return {"accepted": k.decide(a, "p-sm-01")["status"] == "accepted"}
    if s == "sod_alias":
        k = _k(p["seats"])
        next(x for x in k.world.directory if x["person_id"] == "p-ae-01")["employee_id"] = "e-sm-01"
        q = k.propose("deal-b", {"discount_bps": p["bps"]})["quote_id"]
        k.desk.request_approval(ag, q)
        out = k.decide(k.open_approval(q), "p-sm-01")
        rec = k.store.get("decisions", "00000000")
        return {"accepted": out["status"] == "accepted", "rule": rec["rule_id"]}
    if s == "cumulative":
        k = Kit(
            deals=[
                mk_deal("deal-a", "acct-s", "Scenario Works", plan="enterprise", seats=100),
                mk_deal("deal-b", "acct-s", "Scenario Works", seats=p["seats_b"]),
            ]
        )
        k.propose("deal-a", {"discount_bps": 1000})
        r = k.propose("deal-b", {"discount_bps": p["bps_b"]})
        if r["status"] == "blocked":
            return {"deny": None, "blocked": r["blocked_by"], "steps": [], "cum_bps": None}
        if r["status"] == "denied":
            return {"deny": r["rule"], "blocked": [], "steps": [], "cum_bps": None}
        return {"deny": None, "blocked": [], "steps": r["steps"], "cum_bps": r["cum_bps"]}
    if s == "clause":
        k = _k(p["seats"])
        r = k.propose("deal-b", {"discount_bps": p["bps"]}, [p["clause"]])
        if r["status"] == "blocked":
            return {"deny": None, "blocked": r["blocked_by"], "steps": []}
        return {"deny": r.get("rule"), "blocked": [], "steps": r["steps"]}
    if s == "tax_rounding":
        k = _k(p["seats"], ccy=p["ccy"])
        r = k.propose("deal-b", {"discount_bps": p["bps"]})
        if r["status"] == "blocked":
            return {"net": None, "tax_minor": None, "total": None, "steps": [], "blocked": r["blocked_by"]}
        d = k.store.get("quotes", r["quote_id"])["doc"]
        return {"net": d["net"], "tax_minor": d["tax_minor"], "total": d["total"], "steps": r["steps"], "blocked": []}
    if s == "duplicates":
        k = _k(p["seats"])
        res = []
        ts = [
            threading.Thread(target=lambda: res.append(k.propose("deal-b", {"discount_bps": p["bps"]}))) for _ in range(p["dups"])
        ]
        [t.start() for t in ts]
        [t.join() for t in ts]
        return {"quotes": len(k.store.names("quotes"))}
    if s == "cooldown":
        k = _k(p["seats"], ids=("deal-b", "deal-c"))
        q = k.propose("deal-b", {"discount_bps": p["bps"]})["quote_id"]
        k.desk.request_approval(ag, q)
        k.decide(k.open_approval(q), "p-sm-01", "reject")
        q2 = k.propose("deal-c", {"discount_bps": p["bps"] + 100})["quote_id"]
        k.clock.advance(seconds=p["cooldown_s"])
        return {"denied": k.desk.request_approval(ag, q2).get("status") == "denied"}
    if s == "commit_expiry":
        k = _k(p["seats"])
        q = k.propose("deal-b", {"discount_bps": p["bps"]})["quote_id"]
        k.desk.request_approval(ag, q)
        k.decide(k.open_approval(q), "p-sm-01")
        k.desk.draft_quote("draft_writer", q)
        k.clock.advance(hours=24 * p["day"])
        return {"outcome": k.ex.commit("commit_executor", q)["outcome"]}
    k = _k(p["seats"])  # price_book_bump
    q = k.propose("deal-b", {"discount_bps": p["bps"]})["quote_id"]
    k.desk.request_approval(ag, q)
    k.decide(k.open_approval(q), "p-sm-01")
    k.world.book["plans"]["business"]["USD"]["list_seat"] += 1
    out = k.desk.draft_quote("draft_writer", q)
    return {"rule": out["rule"], "state": k.desk.status(ag, q)["state"]}


def run_rows(rows):
    """Returns the list of failing case ids."""
    bad = []
    for row in rows:
        if row["kind"] == "decide":
            ok = check_decide(row)
        elif row["kind"] == "accept":
            ok = check_accept(row)
        elif row["kind"] == "trace":
            ok = check_trace(row)
        else:
            exp = row["expected"]
            ok = run_scenario(row) == exp
        if not ok:
            bad.append(row["case_id"])
    return bad
