"""INDEPENDENT reference evaluator of the ordered pre-gate (gate_rules.md section 1). It imports NOTHING from refunds.* and reads only raw world and
case files. It is independent of `config.py` and `tools.py`, NOT of a primary implementation: there is no gate implementation yet, so this is the only
evaluator of the ordered list. Steps are separate functions in STEPS (the mutation harness reorders and drops them).

ERROR POLICY (one agreed behaviour, gate_rules.md section 1): a malformed MODEL-SUPPLIED argument is a deterministic DENY (AMOUNT_NOT_CANONICAL,
CURRENCY_UNSUPPORTED, BASIS_NOT_ALLOWED, LINES_INVALID, ...), exactly like `money.parse_minor`; a malformed PORT record (world, ticket, reservation, tag
list, tenant id) raises the typed `Malformed` and the caller fails closed (hand-back). Nothing else may escape: `validate_*` run once at the top.

Covered: steps 1-12 except the 'already-pending key returns the existing approval' half of step 11 (the reference excludes the action's OWN reservation
from the cumulatives instead). NOT covered (adapter/stage-2 concerns): the rejected-key cool-down clock, reservation CAS races, approval-time rules
(004/016), execute-time behaviour. Exposure is per currency; the goodwill window and the fraud flag use the STRONG cluster."""

import hashlib
import json
import re
import unicodedata
from datetime import UTC, datetime, timedelta
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "demo_only" / "data"
NOW = datetime(2026, 10, 20, 12, 0, 0, tzinfo=UTC)
DAY = 86400
DEFAULT_TENANT = "demo"
# (one_approver_max, hard_cap, goodwill_cap, goodwill_amount, customer_30d_cap, store_day_cap)
LIM = {
    "USD": (7500, 50000, 2500, 1500, 30000, 250000),
    "GBP": (6000, 40000, 2000, 1200, 24000, 200000),
    "CAD": (10000, 65000, 3500, 2000, 40000, 325000),
    "AUD": (11000, 75000, 3800, 2200, 45000, 375000),
}
TOOL = {
    "propose_refund": "refund",
    "propose_cancel_order": "cancel",
    "propose_reship": "reship",
    "propose_goodwill_credit": "goodwill",
}
BASES = {
    ("refund", "damaged"): {"line_total"},
    ("refund", "wrong_item"): {"line_total"},
    ("refund", "changed_mind"): {"line_total"},
    ("refund", "not_delivered"): {"remaining_refundable"},
    ("cancel", "cancel_before_ship"): {"remaining_refundable"},
    ("reship", "not_delivered"): {"lines_value"},
    ("goodwill", "late_delivery"): {"goodwill_config"},
}
DISPUTE_TAGS = {"dispute", "chargeback", "legal"}
SENTINELS = {"", "unknown", "none", "null", "n/a", "na", "0", "-", "redacted", "masked"}
FP = re.compile(r"fp-[0-9a-f]{10,64}")
ID = re.compile(r"[a-z0-9-]{1,40}")
CANON = re.compile(r"[1-9][0-9]{0,11}")
NUM = re.compile(r"[0-9]{1,12}")
KINDS = {"refund", "cancel", "reship", "goodwill"}
DROP = {"Cf", "Cc", "Zl", "Zp", "Mn"}


class Malformed(ValueError):
    code = "MALFORMED"


# ------------------------------------------------------------------------------------------------ small total helpers
def need(cond, msg):
    if not cond:
        raise Malformed(msg)


def is_str(x):
    return isinstance(x, str)


def num(x, what):
    need(is_str(x) and NUM.fullmatch(x) is not None, f"{what} must be a non-negative integer string")
    return int(x)


def age(t):
    need(is_str(t), "timestamp must be a string")
    try:
        dt = datetime.fromisoformat(t)
        need(dt.tzinfo is not None, "timestamp needs a timezone")
        return int((NOW - dt.astimezone(UTC)).total_seconds())
    except (ValueError, OverflowError) as e:
        raise Malformed(f"bad timestamp {t!r}") from e


def norm_tag(t):
    t = unicodedata.normalize("NFKC", t)
    t = "".join(ch for ch in t if unicodedata.category(ch) not in DROP)
    return t.strip().casefold()


def exact_email(e):
    e = unicodedata.normalize("NFKC", e).strip().casefold() if is_str(e) else ""
    local, _, dom = e.rpartition("@")
    return e if "@" in e and local and dom else ""


def fold_email(e):
    e = exact_email(e)
    if not e:
        return ""
    local, _, dom = e.rpartition("@")
    return f"{local.split('+', 1)[0] or local}@{dom}"


def same_address(a, b):
    if not is_str(a) or not is_str(b) or "@" not in a or "@" not in b:
        return False
    la, _, da = a.strip().rpartition("@")
    lb, _, db = b.strip().rpartition("@")
    return bool(la) and la == lb and da.casefold() == db.casefold()


def ship_key(st):
    toks = [
        t for t in re.split(r"[\W_]+", unicodedata.normalize("NFKC", st["line1"]).casefold()) if t
    ]  # recipient name is NOT part of the key
    pc = "".join(ch for ch in unicodedata.normalize("NFKC", st["postcode"]).casefold() if ch.isalnum())
    cc = st["country"].strip().casefold()
    if len(toks) < 2 or not any(any(ch.isdigit() for ch in t) for t in toks) or not pc or not cc:
        return None
    return (tuple(toks), pc, cc)


def usable_fp(fp):
    if not is_str(fp) or fp.strip().casefold() in SENTINELS or not FP.fullmatch(fp):
        return False
    body = fp[3:]
    return len(set(body)) >= 5 and not body.isdigit()


# ------------------------------------------------------------------------------------------------ validation of PORT data (raises Malformed)
def validate_world(world):
    need(
        isinstance(world, dict) and isinstance(world.get("customers"), list) and isinstance(world.get("orders"), list),
        "world needs customers and orders",
    )
    for c in world["customers"]:
        need(
            isinstance(c, dict)
            and is_str(c.get("customer_id"))
            and is_str(c.get("email"))
            and isinstance(c.get("fraud_flag"), bool),
            "bad customer",
        )
        need(c.get("instrument_fp") is None or is_str(c["instrument_fp"]), "bad fingerprint type")
        st = c.get("ship_to")
        need(isinstance(st, dict) and all(is_str(st.get(k)) for k in ("line1", "postcode", "country")), "bad ship_to")
    for o in world["orders"]:
        need(
            isinstance(o, dict) and all(is_str(o.get(k)) for k in ("order_id", "customer_id", "currency", "status")), "bad order"
        )
        need(
            o["currency"] in LIM
            and is_str(o.get("payments_currency"))
            and o["payments_currency"] in LIM
            and o.get("dispute_status") in ("none", "open", "lost")
            and isinstance(o.get("fraud_flag"), bool),
            "bad order flags",
        )
        need(isinstance(o.get("lines"), list) and o["lines"], "order needs lines")
        sub = refunded = 0
        for ln in o["lines"]:
            need(
                isinstance(ln, dict)
                and is_str(ln.get("line_id"))
                and isinstance(ln.get("qty"), int)
                and not isinstance(ln["qty"], bool)
                and ln["qty"] >= 1,
                "bad line",
            )
            need(is_str(ln.get("compensation")), "bad compensation")
            sub += num(ln.get("unit_minor"), "unit_minor") * ln["qty"]
            refunded += num(ln.get("refunded_minor"), "line refunded_minor")
        ship, ship_ref = (
            num(o.get("shipping_minor"), "shipping_minor"),
            num(o.get("shipping_refunded_minor"), "shipping_refunded_minor"),
        )
        need(num(o.get("captured_minor"), "captured_minor") == sub + ship, "captured != lines + shipping")
        need(
            num(o.get("refunded_minor"), "refunded_minor") == refunded + ship_ref,
            "order refunded_minor != lines + shipping refunded (sources disagree)",
        )
        num(o.get("goodwill_minor"), "goodwill_minor")
        need(isinstance(o.get("refunds"), list) and isinstance(o.get("other_actions"), list), "bad ledger lists")
        line_refunded = {ln["line_id"]: int(ln["refunded_minor"]) for ln in o["lines"]}
        total = 0
        for f in o["refunds"]:
            need(
                isinstance(f, dict) and isinstance(f.get("line_ids"), list) and all(is_str(i) for i in f["line_ids"]),
                "bad refund entry",
            )
            total += num(f.get("amount_minor"), "refund amount")
            age(f.get("ts"))
            need(
                all(line_refunded.get(i, 0) > 0 for i in f["line_ids"]),
                "refunds[].line_ids names a line with a zero counter (sources disagree)",
            )
        need(total == int(o["refunded_minor"]), "sum(refunds) != refunded_minor (sources disagree)")
        for a in o["other_actions"]:
            need(
                isinstance(a, dict)
                and is_str(a.get("kind"))
                and a["kind"] in KINDS
                and isinstance(a.get("line_ids"), list)
                and all(is_str(i) for i in a["line_ids"]),
                "bad action entry",
            )
            num(a.get("amount_minor"), "action amount")
            age(a.get("ts"))
        for k in ("delivered_at", "carrier_eta", "ship_address_changed_at"):
            need(k in o, f"order needs {k} (null when unknown)")
            if o[k] is not None:
                age(o[k])


def validate_case(case):
    need(isinstance(case, dict) and isinstance(case.get("ticket"), dict), "case needs a ticket")
    t = case["ticket"]
    need(isinstance(t.get("sender_verified"), bool), "sender_verified must be a bool")
    need(
        "verified_sender_email" in t and (t["verified_sender_email"] is None or is_str(t["verified_sender_email"])),
        "bad sender address",
    )
    need(case.get("tenant_id") is None or is_str(case["tenant_id"]), "bad tenant id")
    need(
        isinstance(t.get("tags"), list) and all(is_str(x) for x in t["tags"]),
        "tags must be a list of strings (a malformed tag field never means 'no dispute')",
    )
    need(
        isinstance(t.get("attachments"), list) and all(isinstance(a, dict) and is_str(a.get("type")) for a in t["attachments"]),
        "bad attachments",
    )
    need(case.get("order_hint") is None or is_str(case["order_hint"]), "bad order hint")
    ps = case.get("port_state", {})
    need(isinstance(ps, dict), "bad port_state")
    need(isinstance(ps.get("open_reservations", []), list), "open_reservations must be a list")
    need(
        isinstance(ps.get("store_day_refunded_minor", {}), dict) and isinstance(ps.get("open_proposals", {}), dict),
        "bad port_state sections",
    )
    for r in ps.get("open_reservations", []):
        need(isinstance(r, dict) and is_str(r.get("customer_id")), "bad reservation")
        num(r.get("amount_minor"), "reservation amount")
        need(r.get("order_id") is None or is_str(r["order_id"]), "bad reservation order")
    for v in ps.get("store_day_refunded_minor", {}).values():
        num(v, "store day total")
    for v in ps.get("open_proposals", {}).values():
        need(isinstance(v, int) and not isinstance(v, bool), "bad open proposal count")


def scope(world, tenant):
    """Fail closed (tenant-isolation rule): a multi-tenant world needs a known tenant id on the case AND on every record; a single-tenant world needs none."""
    tagged = [r for k in ("customers", "orders") for r in world[k] if isinstance(r, dict) and r.get("tenant_id") is not None]
    if not tagged:
        need(tenant is None, "case names a tenant but the world has none")
        return world
    need(len(tagged) == len(world["customers"]) + len(world["orders"]), "records without a tenant id in a multi-tenant world")
    need(is_str(tenant) and tenant in {r["tenant_id"] for r in tagged}, "unknown or missing tenant id")
    return {
        **world,
        "customers": [c for c in world["customers"] if c["tenant_id"] == tenant],
        "orders": [o for o in world["orders"] if o["tenant_id"] == tenant],
    }


def scoped(world, tenant):  # kept for the isolation test's mutation probe
    return scope(world, tenant)


def load(split):
    name = "world.json" if split == "dev" else "world_test.json"
    world = json.loads((DATA / name).read_text(encoding="utf-8"))
    cases = [
        json.loads(x) for x in (DATA / f"{'dev' if split == 'dev' else 'test'}.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    return world, cases


def cluster(world, cid, strong):
    keys = {}
    for c in world["customers"]:
        ks = set()
        if c.get("email_verified") is True and exact_email(c["email"]):
            ks.add(("e", exact_email(c["email"])))
        if usable_fp(c.get("instrument_fp")):
            ks.add(("f", c["instrument_fp"]))
        if not strong:
            if fold_email(c["email"]):
                ks.add(("a", fold_email(c["email"])))
            sk = ship_key(c["ship_to"])
            if sk:
                ks.add(("s", sk))
        keys[c["customer_id"]] = ks
    members, frontier = {cid}, [cid]
    while frontier:
        cur = frontier.pop()
        for other, ks in keys.items():
            if other not in members and ks & keys[cur]:
                members.add(other)
                frontier.append(other)
    return members


def executed(world, members, currency):
    out = []
    for o in world["orders"]:
        if o["customer_id"] in members and o["currency"] == currency:
            out += [(age(f["ts"]), int(f["amount_minor"]), "refund") for f in o["refunds"]]
            out += [(age(a["ts"]), int(a["amount_minor"]), a["kind"]) for a in o["other_actions"]]
    return out


class Ctx:
    pass


# ------------------------------------------------------------------------------------------------ the ordered steps
def s_sender(c):
    t = c.t
    if not t["sender_verified"] or not t["verified_sender_email"]:
        return "SENDER_UNVERIFIED"
    c.cust = next((x for x in c.world["customers"] if same_address(x["email"], t["verified_sender_email"])), None)
    oid = c.a.get("order_id")
    c.o = {o["order_id"]: o for o in c.world["orders"]}.get(oid) if is_str(oid) else None
    if c.cust is None or c.o is None or c.o["customer_id"] != c.cust["customer_id"]:
        return "OWNER_MISMATCH"
    return None


def s_resolution(c):
    hint = c.case.get("order_hint")
    if hint and hint != c.a["order_id"]:
        return "ORDER_HINT_MISMATCH"
    if not hint and sum(1 for x in c.world["orders"] if x["customer_id"] == c.cust["customer_id"]) > 1:
        return "ORDER_AMBIGUOUS"
    return None


def s_fraud(c):
    c.weak = cluster(c.world, c.cust["customer_id"], False)
    c.strong = cluster(c.world, c.cust["customer_id"], True)
    need(len(c.strong) <= 20, "oversized strong cluster: untrusted identity data, fail closed")
    if c.o["fraud_flag"] or any(x["fraud_flag"] for x in c.world["customers"] if x["customer_id"] in c.strong):
        return "FRAUD_HOLD"
    if c.o["dispute_status"] in ("open", "lost") or any(norm_tag(x) in DISPUTE_TAGS for x in c.t["tags"]):
        return "DISPUTE_HOLD"
    return None


def s_money(c):
    m = c.a.get("amount") if c.tool != "reship" else c.a.get("value")
    cur = m.get("currency") if isinstance(m, dict) else None
    amt = m.get("amount_minor") if isinstance(m, dict) else None
    if not is_str(cur) or cur not in LIM:
        return "CURRENCY_UNSUPPORTED"
    if not is_str(amt) or not CANON.fullmatch(amt):
        return "AMOUNT_NOT_CANONICAL"
    if cur != c.o["currency"]:
        return "ARG_CURRENCY_MISMATCH"
    if c.o.get("payments_currency") != c.o["currency"]:  # missing = mismatch: fail closed
        return "CURRENCY_MISMATCH"
    c.req, c.cur = int(amt), cur
    return None


def s_eligibility(c):
    o, tool, reason, t = c.o, c.tool, c.a.get("reason"), c.t
    imgs = sum(1 for x in t["attachments"] if x["type"] == "image")
    c.dage = age(o["delivered_at"]) if o["delivered_at"] else None
    need(c.dage is None or c.dage >= 0, "delivered_at is in the future")
    c.late = ((age(o["carrier_eta"]) - c.dage) if c.dage is not None else age(o["carrier_eta"])) if o["carrier_eta"] else None
    st = o["status"]
    if not is_str(reason):
        return "NOT_ELIGIBLE_REASON"
    if tool == "cancel":
        if any(a["kind"] == "cancel" for a in o["other_actions"]):
            return "NOT_CANCELLABLE"  # one cancel per order
        return None if st == "paid_unfulfilled" and reason == "cancel_before_ship" else "NOT_CANCELLABLE"
    if tool == "refund":
        if reason in ("damaged", "wrong_item"):
            if st != "delivered":
                return "NOT_ELIGIBLE_REASON"
            if c.dage is None or c.dage > 90 * DAY:
                return "OUTSIDE_WINDOW"
            return None if imgs >= 1 else "EVIDENCE_MISSING"
        if reason == "changed_mind":
            if st != "delivered" or c.dage is None:
                return "NOT_ELIGIBLE_REASON"
            return None if c.dage <= 30 * DAY else "OUTSIDE_WINDOW"
        if reason == "not_delivered":
            if st != "shipped":
                return "NOT_ELIGIBLE_REASON"
            return None if c.late is not None and c.late > 7 * DAY else "NOT_LATE_ENOUGH"
        return "NOT_ELIGIBLE_REASON"
    if tool == "reship":
        if reason != "not_delivered" or st != "shipped":
            return "NOT_ELIGIBLE_REASON"
        return None if c.late is not None and c.late > 7 * DAY else "NOT_LATE_ENOUGH"
    if reason != "late_delivery" or st not in ("delivered", "shipped"):
        return "NOT_ELIGIBLE_REASON"
    return None if c.late is not None and c.late > 7 * DAY else "NOT_LATE_ENOUGH"


def s_basis(c):
    tool, reason = c.tool, c.a["reason"]
    implicit = {"reship": "lines_value", "cancel": "remaining_refundable", "goodwill": "goodwill_config"}
    c.basis = c.a.get("basis") if tool == "refund" else implicit[tool]
    if not is_str(c.basis) or c.basis not in BASES.get((tool, reason), set()):
        return "BASIS_NOT_ALLOWED"
    if c.basis == "remaining_refundable" and tool == "refund" and int(c.o["refunded_minor"]) > 0:
        return "BASIS_NOT_ALLOWED"
    return None


def s_lines(c):
    c.lines = {x["line_id"]: x for x in c.o["lines"]}
    ids = c.a.get("line_ids", [])
    if c.tool in ("refund", "reship"):
        if not isinstance(ids, list) or not all(is_str(i) for i in ids):
            return "LINES_INVALID"
        if c.basis == "remaining_refundable":
            if sorted(ids) != sorted([*c.lines, "shipping"]):
                return "LINES_INVALID"
        elif not ids or any(i not in c.lines for i in ids) or len(set(ids)) != len(ids):
            return "LINES_INVALID"
    c.ids = ids if isinstance(ids, list) else []
    return None


def _sets(o):
    """Compensation sources, cross-checked: per-line counters/flags UNION refunds[].line_ids UNION other_actions[].line_ids. A legacy action with no
    line ids covers the whole order. An executed cancel compensates every line."""
    every = {x["line_id"] for x in o["lines"]}
    reship = {x["line_id"] for x in o["lines"] if x["compensation"] != "none"}
    refund = {x["line_id"] for x in o["lines"] if int(x["refunded_minor"]) > 0}
    cancel = False
    for f in o["refunds"]:
        refund |= set(f["line_ids"])
    for a in o["other_actions"]:
        covered = set(a["line_ids"]) or every
        if a["kind"] == "reship":
            reship |= covered
        elif a["kind"] == "cancel":
            cancel = True
    return reship, refund, cancel


def s_ledger(c):
    """Single compensation choke point: EVERY basis and action. A line is compensated once (refund OR reship OR cancel); goodwill once per order and per
    STRONG cluster per 90 days (same currency)."""
    o, tool = c.o, c.tool
    reship, refund, cancel = _sets(o)
    covered = list(c.lines) if c.basis == "remaining_refundable" else [i for i in c.ids if i in c.lines]
    if tool in ("refund", "reship") and c.basis in ("line_total", "lines_value") and any(c.lines[i]["qty"] > 1 for i in covered):
        return "QTY_UNCLEAR"
    if tool in ("refund", "reship") and cancel:
        return "LINE_COMPENSATED"
    if tool == "refund" and any(i in reship for i in covered):
        return "LINE_COMPENSATED"
    if tool == "reship" and any(i in reship or i in refund for i in covered):
        return "LINE_COMPENSATED"
    if (
        tool == "refund"
        and c.basis == "line_total"
        and any(int(c.lines[i]["unit_minor"]) * c.lines[i]["qty"] - int(c.lines[i]["refunded_minor"]) <= 0 for i in covered)
    ):
        return "LINE_ALREADY_REFUNDED"
    if tool == "goodwill":
        if int(o["goodwill_minor"]) > 0:
            return "GOODWILL_ALREADY"
        if any(k == "goodwill" and ag <= 90 * DAY for ag, _, k in executed(c.world, c.strong, c.cur)):
            return "GOODWILL_ALREADY"
    if c.basis == "remaining_refundable" and int(o["captured_minor"]) - int(o["refunded_minor"]) <= 0:
        return "OVER_REFUNDABLE"
    return None


def s_authority(c):
    lines, ids, o = c.lines, c.ids, c.o
    if c.basis == "line_total":
        want = sum(int(lines[i]["unit_minor"]) * lines[i]["qty"] - int(lines[i]["refunded_minor"]) for i in ids)
    elif c.basis == "lines_value":
        want = sum(int(lines[i]["unit_minor"]) * lines[i]["qty"] for i in ids)
    elif c.basis == "goodwill_config":
        want = LIM[c.cur][3]
    else:
        want = int(o["captured_minor"]) - int(o["refunded_minor"])
    return None if c.req == want else "AUTHORITY_MISMATCH"


def own_key(c):
    """Same recipe as adapters.ports.business_key (tests/test_reference.py compares them): tenant | action | order | sorted line ids (a whole-order
    refund names every line AND 'shipping') | amount | currency."""
    ids = sorted(c.ids) if c.tool in ("refund", "reship") else []
    tenant = c.case.get("tenant_id") or DEFAULT_TENANT
    return hashlib.sha256(f"{tenant}|{c.tool}|{c.a['order_id']}|{','.join(ids)}|{c.req}|{c.cur}".encode()).hexdigest()


def s_caps(c):
    _one, hard, gcap, _, cap, day_cap = LIM[c.cur]
    ps = c.case.get("port_state", {})
    mine = own_key(c)
    res = [
        r for r in ps.get("open_reservations", []) if r["customer_id"] in c.weak and r.get("request_ref") != mine
    ]  # the action's OWN reservation is excluded
    foreign = [r for r in ps.get("open_reservations", []) if r.get("request_ref") != mine]
    c.order_cum = (
        int(c.o["refunded_minor"])
        + sum(int(x["amount_minor"]) for x in c.o["other_actions"])
        + sum(int(r["amount_minor"]) for r in res if r.get("order_id") == c.o["order_id"])
        + c.req
    )
    c.ex = executed(c.world, c.weak, c.cur)
    c.cust_cum = sum(x for ag, x, _ in c.ex if ag <= 30 * DAY) + sum(int(r["amount_minor"]) for r in res) + c.req
    if (c.tool == "goodwill" and c.req > gcap) or c.req > hard:
        return "OVER_CAP"
    if c.order_cum > hard:
        return "ORDER_CAP"
    if c.cust_cum > cap:
        return "CUSTOMER_CAP"
    held = sum(
        int(r["amount_minor"]) for r in foreign
    )  # EVERY open reservation but the action's own, the requester's cluster included
    if int(ps.get("store_day_refunded_minor", {}).get(c.cur, "0")) + held + c.req > day_cap:
        return "DAY_CAP"
    return None


def s_key(c):
    if not ID.fullmatch(c.a["order_id"]) or any(not ID.fullmatch(i) for i in c.ids if i != "shipping"):
        return "KEY_INVALID"
    return None


def s_pending(c):
    ps = c.case.get("port_state", {}).get("open_proposals", {})
    if ps.get("cluster", 0) >= 3 or ps.get("sender", 0) >= 3:
        return "PENDING_CAP"
    return None


STEPS = [
    s_sender,
    s_resolution,
    s_fraud,
    s_money,
    s_eligibility,
    s_basis,
    s_lines,
    s_ledger,
    s_authority,
    s_caps,
    s_key,
    s_pending,
]


NET_HITS = 0  # how often the last-resort net below fired; tests/test_reference.py asserts the explicit validation makes it 0


def evaluate(case, world, call):
    """Returns (deny_code, None) or (None, tier); raises Malformed on a broken call envelope or broken port data. Nothing else escapes: the explicit
    `validate_*` calls are the contract, the net below is a last resort that turns a stray KeyError/TypeError/... into Malformed and is counted."""
    global NET_HITS
    try:
        return _evaluate(case, world, call)
    except Malformed:
        raise
    except (KeyError, TypeError, ValueError, OverflowError, AttributeError, IndexError) as e:
        NET_HITS += 1
        raise Malformed(f"unexpected shape: {type(e).__name__}") from e


def _evaluate(case, world, call):
    need(
        isinstance(call, dict) and is_str(call.get("tool")) and call["tool"] in TOOL and isinstance(call.get("args"), dict),
        "bad call envelope",
    )
    validate_case(case)
    validate_world(world)
    world = scope(world, case.get("tenant_id"))
    c = Ctx()
    c.case, c.world, c.t, c.a, c.tool = case, world, case["ticket"], call["args"], TOOL[call["tool"]]
    for step in STEPS:
        deny = step(c)
        if deny:
            return deny, None
    one = LIM[c.cur][0]
    tier = "human" if max(c.req, c.order_cum, c.cust_cum) <= one else "four_eyes"
    repeat = sum(  # a COUNT of executed money actions in the strong cluster, any currency
        1
        for o in c.world["orders"]
        if o["customer_id"] in c.strong
        for ts_ in [f["ts"] for f in o["refunds"]] + [x["ts"] for x in o["other_actions"]]
        if age(ts_) <= 90 * DAY
    )
    addr = c.o["ship_address_changed_at"] and age(c.o["ship_address_changed_at"]) <= 14 * DAY
    evidence = c.a["reason"] in ("damaged", "wrong_item") and c.dage is not None and c.dage > 30 * DAY
    return None, ("four_eyes" if repeat >= 3 or addr or evidence else tier)


def correct_call(case):
    """The call a correct agent would make for an `act` money case, built from the gold's own fields."""
    e = case["expected"]
    tool = {
        "refund": "propose_refund",
        "cancel": "propose_cancel_order",
        "reship": "propose_reship",
        "goodwill": "propose_goodwill_credit",
    }[e["action"]]
    money = {"amount_minor": e["amount_minor"], "currency": e["currency"]}
    args = {"order_id": case["order_ref"], "reason": e["reason"]}
    if tool == "propose_refund":
        args |= {"basis": "line_total", "line_ids": e["line_ids"], "amount": money}
    elif tool == "propose_reship":
        args |= {"line_ids": e["line_ids"], "value": money}
    else:
        args |= {"amount": money}
    return {"tool": tool, "args": args}


def apply_effect(world, case, call):
    """Apply an ALLOWED call to the world (used by the bounded-enumeration property test)."""
    a, tool = call["args"], TOOL[call["tool"]]
    o = next(x for x in world["orders"] if x["order_id"] == a["order_id"])
    amt = int((a.get("amount") or a.get("value"))["amount_minor"])
    stamp = (NOW - timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    if tool == "refund":
        ids = [x["line_id"] for x in o["lines"]] if a["basis"] == "remaining_refundable" else a["line_ids"]
        left = amt
        for ln in o["lines"]:
            if ln["line_id"] in ids:
                part = min(left, int(ln["unit_minor"]) * ln["qty"] - int(ln["refunded_minor"]))
                ln["refunded_minor"] = str(int(ln["refunded_minor"]) + part)
                left -= part
        if left:
            o["shipping_refunded_minor"] = str(int(o["shipping_refunded_minor"]) + left)
        o["refunded_minor"] = str(int(o["refunded_minor"]) + amt)
        o["refunds"].append(
            {
                "refund_id": "rf-x",
                "amount_minor": str(amt),
                "ts": stamp,
                "line_ids": [i for i in ids if int(next(x for x in o["lines"] if x["line_id"] == i)["refunded_minor"]) > 0],
            }
        )
    elif tool == "reship":
        o["other_actions"].append({"kind": "reship", "amount_minor": str(amt), "ts": stamp, "line_ids": a["line_ids"]})
        for ln in o["lines"]:
            if ln["line_id"] in a["line_ids"]:
                ln["compensation"] = "reship"
    elif tool == "goodwill":
        o["other_actions"].append({"kind": "goodwill", "amount_minor": str(amt), "ts": stamp, "line_ids": []})
        o["goodwill_minor"] = str(amt)
    else:
        o["other_actions"].append({"kind": "cancel", "amount_minor": str(amt), "ts": stamp, "line_ids": []})
        o["status"] = "cancelled"
