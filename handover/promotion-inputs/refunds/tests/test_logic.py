"""Pure-logic tests with HAND-WRITTEN literal expectations (nothing here derives its expected values from refunds.config)."""

import importlib.util
import inspect
import json
import re
from datetime import timedelta
from pathlib import Path

import pytest

from refunds import config, hashing, identity, textnorm, tools, verdict
from refunds.adapters import ports
from refunds.adapters.ports import KeyInvalid, business_key
from refunds.config import GateInputError, cap_decision, eligibility, required_tier
from refunds.money import MoneyError, parse_minor

ROOT = Path(__file__).resolve().parents[1]
DAY = 86400
# independent literal limits: (one_approver_max, hard_cap, goodwill_cap, goodwill_amount, customer_30d_cap, store_day_cap)
LIT = {
    "USD": (7500, 50000, 2500, 1500, 30000, 250000),
    "GBP": (6000, 40000, 2000, 1200, 24000, 200000),
    "CAD": (10000, 65000, 3500, 2000, 40000, 325000),
    "AUD": (11000, 75000, 3800, 2200, 45000, 375000),
}


def lit_decide(cur, req, order_cum, cust_cum, floor=None, kind="refund"):
    """Independent literal evaluator for step 10 (caps) and step 13 (tier)."""
    one, hard, gcap, _, cap, _ = LIT[cur]
    if (kind == "goodwill" and req > gcap) or req > hard:
        return "OVER_CAP"
    if order_cum > hard:
        return "ORDER_CAP"
    if cust_cum > cap:
        return "CUSTOMER_CAP"
    t = "human" if max(req, order_cum, cust_cum) <= one else "four_eyes"
    return "four_eyes" if floor == "four_eyes" else t


def test_limits_match_literals_and_cap_is_below_hard_cap():
    for cur, lim in config.LIMITS.items():
        assert (
            lim.one_approver_max,
            lim.hard_cap,
            lim.goodwill_cap,
            lim.goodwill_amount,
            lim.customer_30d_cap,
            lim.store_day_cap,
        ) == LIT[cur]
        assert lim.customer_30d_cap < lim.hard_cap, "else CUSTOMER_CAP is unreachable behind OVER_CAP"


@pytest.mark.parametrize(
    "cur,req,oc,cc,floor,want",
    [
        ("USD", 7500, 7500, 7500, None, "human"),
        ("USD", 7501, 7501, 7501, None, "four_eyes"),
        ("USD", 7499, 7499, 14998, None, "four_eyes"),
        ("USD", 7499, 7499, 29996, None, "four_eyes"),
        ("USD", 7499, 7499, 37495, None, "CUSTOMER_CAP"),
        ("USD", 30000, 30000, 30000, None, "four_eyes"),
        ("USD", 30001, 30001, 30001, None, "CUSTOMER_CAP"),
        ("USD", 50000, 50000, 1, None, "ORDER_CAP" if False else None),
        ("USD", 50001, 50001, 1, None, "OVER_CAP"),
        ("USD", 3000, 7600, 3000, None, "four_eyes"),
        ("USD", 1000, 1000, 1000, "four_eyes", "four_eyes"),
        ("USD", 29000, 58000, 29000, None, "ORDER_CAP"),
        ("USD", 29000, 50000, 29000, None, "four_eyes"),
        ("USD", 29000, 50001, 29000, None, "ORDER_CAP"),
        ("GBP", 6000, 6000, 6000, None, "human"),
        ("GBP", 6001, 6001, 6001, None, "four_eyes"),
        ("GBP", 24001, 24001, 24001, None, "CUSTOMER_CAP"),
        ("GBP", 21000, 42000, 21000, None, "ORDER_CAP"),
        ("CAD", 10000, 10000, 10000, None, "human"),
        ("CAD", 40000, 40000, 40000, None, "four_eyes"),
        ("AUD", 11001, 11001, 11001, None, "four_eyes"),
        ("AUD", 75001, 75001, 75001, None, "OVER_CAP"),
        ("AUD", 75000, 75000, 1, None, None),
    ],
)
def test_cumulative_tier_and_caps_literal_table(cur, req, oc, cc, floor, want):
    if (
        want is None
    ):  # exactly at the hard cap with an unsaturated cluster: the cap decision itself passes (the boundary is >, not >=)
        assert cap_decision(cur, req, oc, cc) is None
        return
    assert lit_decide(cur, req, oc, cc, floor) == want
    if want in ("human", "four_eyes"):
        assert cap_decision(cur, req, oc, cc) is None and required_tier(cur, req, oc, cc, "refund", floor) == want
    else:  # a denied request has no tier: 'blocked' is never a tier
        assert cap_decision(cur, req, oc, cc) == want
        with pytest.raises(GateInputError):
            required_tier(cur, req, oc, cc)


def test_goodwill_above_the_goodwill_cap_is_a_deny_not_a_tier():  # review M8
    assert (
        cap_decision("USD", 2501, 2501, 2501, "goodwill") == "OVER_CAP"
        and cap_decision("USD", 2500, 2500, 2500, "goodwill") is None
    )
    with pytest.raises(GateInputError):
        required_tier("USD", 2600, 2600, 2600, "goodwill")
    assert required_tier("USD", 1500, 1500, 1500, "goodwill") == "human"


def test_input_guards_fail_closed_with_a_typed_error():  # review m9
    for bad in ((0, 1, 1), (-5, 1, 1), (1, 0, 1), (1, 1, -1), (True, 1, 1), (1.5, 1, 1), ("5", 1, 1)):
        with pytest.raises(GateInputError) as ei:
            cap_decision("USD", *bad)
        assert ei.value.code == "AMOUNT_NOT_POSITIVE"
    for cur in ("JPY", None, ["USD"], "usd"):
        with pytest.raises(GateInputError) as ei:
            cap_decision(cur, 1, 1, 1)
        assert ei.value.code == "CURRENCY_UNSUPPORTED"


def test_split_refunds_sequence_eleven_times_7499():
    cum, got = 0, []
    for _ in range(11):
        cum += 7499
        got.append(lit_decide("USD", 7499, 7499, cum))
    assert got == ["human"] + ["four_eyes"] * 3 + ["CUSTOMER_CAP"] * 7
    sc = {s["scenario_id"]: s for s in json.loads((ROOT / "demo_only/data/rule_scenarios.json").read_text())}
    assert sc["SC-01"]["expected"] == got and sc["SC-09"]["cases"][3]["expected_granted"] == 4


def _gen():
    spec = importlib.util.spec_from_file_location("refunds_gen", ROOT / "demo_only/data/gen.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_cluster_cumulative_uses_30_day_window_other_actions_aliases_and_one_currency():
    g = _gen()
    w = g.World(g.Rng(1), 0)
    a = w.customer("USD", name="Ann One", email="ann@example.com", fp="fp-a1b2c3d4e5f6")
    b = w.customer(
        "USD", name="Ann Two", email="ANN+promo@Example.com", fp="fp-b1c2d3e4f5a6", email_verified=False
    )  # weak alias of a
    d = w.customer("USD", name="Dee", email="dee@example.com", fp="fp-a1b2c3d4e5f6")  # shares a's card (strong)
    z = w.customer("USD", name="Zed", email="zed@example.com", fp="fp-9f8e7d6c5b4a")  # unrelated
    plan = [(a, 29 * DAY + 23 * 3600, 100), (a, 30 * DAY, 200), (b, 30 * DAY + 1, 400), (d, 5 * DAY, 800), (z, 1 * DAY, 1600)]
    for cust, age, amt in plan:
        o = w.order(cust, "delivered", 1, shipping=0, unit=(amt, amt), refunded=amt)
        o["refunds"][0]["ts"] = (g.NOW - timedelta(seconds=age)).strftime(g.FMT)
    w.other_action(a, "reship", 700, 10)  # executed reship counts (timestamped, inside the window)
    w.other_action(a, "goodwill", 1000, 31)  # executed goodwill 31 days ago does not
    assert g.cust30(w, a["customer_id"], "USD") == 100 + 200 + 800 + 700
    assert g.cust30(w, b["customer_id"], "USD") == g.cust30(w, a["customer_id"], "USD"), (
        "the alias account is in the exposure cluster (weak link)"
    )
    assert g.cust30(w, z["customer_id"], "USD") == 1600
    assert g.cust30(w, a["customer_id"], "GBP") == 0, "another currency is a separate bucket"
    assert g.cust30(w, a["customer_id"], "USD") + 700 + 50 == 2550  # executed + open reservation + this request


@pytest.mark.parametrize(
    "args,want",
    [
        (("refund", "damaged", "delivered", 5 * DAY, None, 1), None),
        (("refund", "damaged", "delivered", 5 * DAY, None, 0), "EVIDENCE_MISSING"),
        (("refund", "damaged", "delivered", 45 * DAY, None, 1), None),
        (("refund", "damaged", "delivered", 90 * DAY, None, 1), None),
        (("refund", "damaged", "delivered", 90 * DAY + 1, None, 1), "OUTSIDE_WINDOW"),
        (("refund", "damaged", "delivered", 99 * DAY, None, 1), "OUTSIDE_WINDOW"),
        (("refund", "damaged", "shipped", None, None, 1), "NOT_ELIGIBLE_REASON"),
        (("refund", "damaged", "paid_unfulfilled", None, None, 1), "NOT_ELIGIBLE_REASON"),
        (("refund", "wrong_item", "delivered", 5 * DAY, None, 0), "EVIDENCE_MISSING"),
        (("refund", "changed_mind", "delivered", 30 * DAY, None, 0), None),
        (("refund", "changed_mind", "delivered", 30 * DAY + 1, None, 0), "OUTSIDE_WINDOW"),
        (("refund", "changed_mind", "delivered", None, None, 0), "NOT_ELIGIBLE_REASON"),
        (("refund", "changed_mind", "shipped", None, None, 0), "NOT_ELIGIBLE_REASON"),
        (("refund", "not_delivered", "shipped", None, 7 * DAY, 0), "NOT_LATE_ENOUGH"),
        (("refund", "not_delivered", "shipped", None, 7 * DAY + 1, 0), None),
        (("refund", "not_delivered", "delivered", 3 * DAY, 9 * DAY, 0), "NOT_ELIGIBLE_REASON"),
        (("refund", "not_delivered", "shipped", None, None, 0), "NOT_LATE_ENOUGH"),
        (("refund", "other", "delivered", 3 * DAY, None, 1), "NOT_ELIGIBLE_REASON"),
        (("cancel", "cancel_before_ship", "paid_unfulfilled", None, None, 0), None),
        (("cancel", "other", "paid_unfulfilled", None, None, 0), "NOT_CANCELLABLE"),
        (("cancel", "cancel_before_ship", "shipped", None, None, 0), "NOT_CANCELLABLE"),
        (("reship", "not_delivered", "shipped", None, 8 * DAY, 0), None),
        (("reship", "not_delivered", "delivered", 2 * DAY, 8 * DAY, 0), "NOT_ELIGIBLE_REASON"),
        (("reship", "not_delivered", "shipped", None, 7 * DAY, 0), "NOT_LATE_ENOUGH"),
        (("reship", "damaged", "shipped", None, 9 * DAY, 0), "NOT_ELIGIBLE_REASON"),
        (("goodwill", "late_delivery", "delivered", 2 * DAY, 8 * DAY, 0), None),
        (("goodwill", "late_delivery", "shipped", None, 8 * DAY, 0), None),
        (("goodwill", "late_delivery", "paid_unfulfilled", None, 8 * DAY, 0), "NOT_ELIGIBLE_REASON"),
        (("goodwill", "late_delivery", "delivered", 2 * DAY, 7 * DAY, 0), "NOT_LATE_ENOUGH"),
        (("goodwill", "service_failure", "delivered", 2 * DAY, 9 * DAY, 0), "NOT_ELIGIBLE_REASON"),
    ],
)
def test_eligibility_matrix_literal(args, want):
    assert eligibility(*args) == want


def test_evidence_floor_and_floor_for():
    assert config.evidence_floor("damaged", 30 * DAY) is None and config.evidence_floor("damaged", 30 * DAY + 1) == "four_eyes"
    assert config.evidence_floor("wrong_item", 31 * DAY) == "four_eyes" and config.evidence_floor("wrong_item", None) is None
    assert config.evidence_floor("changed_mind", 80 * DAY) is None
    assert config.floor_for(3, None, "x", None) == "four_eyes" and config.floor_for(2, None, "x", None) is None
    assert config.floor_for(0, 14 * DAY, "x", None) == "four_eyes" and config.floor_for(0, 14 * DAY + 1, "x", None) is None
    assert config.floor_for(0, None, "damaged", 31 * DAY) == "four_eyes"


@pytest.mark.parametrize(
    "tool,reason,basis,prior,ok",
    [
        ("refund", "damaged", "line_total", 0, True),
        ("refund", "damaged", "remaining_refundable", 0, False),
        ("refund", "changed_mind", "remaining_refundable", 0, False),
        ("refund", "not_delivered", "remaining_refundable", 0, True),
        ("refund", "not_delivered", "remaining_refundable", 1, False),
        ("refund", "not_delivered", "line_total", 0, False),
        ("refund", "other", "line_total", 0, False),
        ("cancel", "cancel_before_ship", "remaining_refundable", 0, True),
        ("reship", "not_delivered", "lines_value", 0, True),
        ("goodwill", "late_delivery", "goodwill_config", 0, True),
        ("goodwill", "late_delivery", "line_total", 0, False),
    ],
)
def test_basis_matrix_literal(tool, reason, basis, prior, ok):
    assert config.basis_allowed(tool, reason, basis, prior) is ok


def test_owner_default_constants_are_pinned():
    """The OWNER DEFAULTS, as literals. A changed default must be a deliberate edit of this test. This is a change detector by design; it says nothing
    about whether any logic uses the constants correctly (the next test does, symbolically)."""
    assert (config.APPROVAL_TTL_S, config.EXPOSURE_WINDOW_S, config.SETTLE_DELAY_S, config.SWEEP_INTERVAL_S, config.UNKNOWN_ESCALATION_S) == (
        86400, 30 * DAY, 120, 300, 14400,
    )  # fmt: skip
    assert (
        config.MAX_PENDING_PER_CUSTOMER,
        config.MAX_PENDING_PER_SENDER,
        config.UNAPPROVED_SHARE_DEN,
        config.DENY_RATE_PER_SENDER_HOUR,
    ) == (3, 3, 4, 5)
    assert (
        config.GOODWILL_WINDOW_S, config.REPEAT_REFUND_COUNT, config.REPEAT_WINDOW_S, config.ADDRESS_CHANGE_SIGNAL_S, config.REJECTED_COOLDOWN_S, config.MAX_RETRIES,
    ) == (90 * DAY, 3, 90 * DAY, 14 * DAY, 3600, 2)  # fmt: skip
    assert config.APPROVER_MATRIX == {"human": ["support_lead"], "four_eyes": ["support_lead", "finance_approver"]}


def test_helper_boundaries_follow_their_own_constants_exactly():
    """Behaviour at the edge, written symbolically so it catches a flipped comparison whatever the constant is."""
    c = config
    assert (
        c.in_exposure_window(c.EXPOSURE_WINDOW_S)
        and not c.in_exposure_window(c.EXPOSURE_WINDOW_S + 1)
        and c.in_exposure_window(0)
    )
    m1, m2 = c.MAX_PENDING_PER_CUSTOMER, c.MAX_PENDING_PER_SENDER
    assert c.pending_cap_decision(m1 - 1, m2 - 1) is None
    assert (
        c.pending_cap_decision(m1, 0) == "PENDING_CAP"
        and c.pending_cap_decision(0, m2) == "PENDING_CAP"
        and c.pending_cap_decision(m1 + 1, 0) == "PENDING_CAP"
    )
    share = c.LIMITS["USD"].store_day_cap // c.UNAPPROVED_SHARE_DEN
    assert c.unapproved_share_ok(share - 500, 500, "USD") is True and c.unapproved_share_ok(share - 500, 501, "USD") is False
    assert c.unapproved_share_ok(0, share, "USD") is True and c.unapproved_share_ok(0, share + 1, "USD") is False
    assert c.unapproved_share_ok(0, c.LIMITS["USD"].store_day_cap // 2, "USD") is False, (
        "the share is a fraction of the day cap, not a half"
    )
    gap = c.SETTLE_DELAY_S
    assert (
        c.release_unknown_ok([]) is False
        and c.release_unknown_ok([100]) is False
        and c.release_unknown_ok([100, 100 + gap - 1]) is False
    )
    assert c.release_unknown_ok([100, 100 + gap]) is True and c.release_unknown_ok([100, 101, 100 + gap + 50]) is True
    assert c.release_unknown_ok([100 + gap, 100]) is True, "order of the confirmations does not matter"
    e = c.UNKNOWN_ESCALATION_S
    assert c.escalation_due(e) is False and c.escalation_due(e + 1) is True and c.escalation_due(0) is False
    sw = c.SWEEP_INTERVAL_S
    assert c.sweep_due(sw - 1) is False and c.sweep_due(sw) is True
    d = c.DENY_RATE_PER_SENDER_HOUR
    assert c.deny_rate_exceeded(d) is False and c.deny_rate_exceeded(d + 1) is True
    cd = c.REJECTED_COOLDOWN_S
    assert c.cooldown_active(cd) is True and c.cooldown_active(cd + 1) is False and c.cooldown_active(0) is True
    gw = c.GOODWILL_WINDOW_S
    assert (
        c.goodwill_cluster_blocked([gw]) is True
        and c.goodwill_cluster_blocked([gw + 1]) is False
        and c.goodwill_cluster_blocked([]) is False
    )
    assert c.goodwill_cluster_blocked([gw + 1, 5]) is True, "any executed goodwill inside the window blocks"


def test_sc25_goodwill_window_table_is_executable():
    sc = {s["scenario_id"]: s for s in json.loads((ROOT / "demo_only/data/rule_scenarios.json").read_text())}
    for row in sc["SC-25"]["table"]:
        ages = [d * DAY for d in row["executed_goodwill_age_days"]] if row["currency_same"] else []
        assert ("GOODWILL_ALREADY" if config.goodwill_cluster_blocked(ages) else "allow") == row["expect"], row
    assert config.goodwill_cluster_blocked([90 * DAY]) and not config.goodwill_cluster_blocked([90 * DAY + 1])


def test_dispute_tags_fold_case_width_and_hidden_characters_and_malformed_fields_fail_closed():
    assert (
        config.is_dispute(["Dispute"])
        and config.is_dispute([" CHARGEBACK "])
        and config.is_dispute(["x", "Legal"])
        and not config.is_dispute(["vip", "other"])
    )
    assert (
        config.is_dispute(["\uff24\uff29\uff33\uff30\uff35\uff34\uff25"])
        and config.is_dispute(["dis\u200bpute"])
        and not config.is_dispute([])
    )
    for bad in ("dispute", None, 5, [None], [1], [["dispute"]], {"a": 1}):
        with pytest.raises(GateInputError) as ei:
            config.is_dispute(bad)
        assert ei.value.code == "TAGS_MALFORMED"


def test_ttl_and_day_bucket():
    assert config.is_expired(DAY, 0) is False and config.is_expired(DAY + 1, 0) is True
    assert config.day_bucket("2026-10-20T23:59:59Z") == "2026-10-20"


def test_deny_rule_table_is_complete_and_one_to_one():
    codes = set(tools.DenyCode.__args__)
    assert codes == set(config.DENY_RULE)
    rules = set(re.findall(r"^\| (R-REF-\d{3}) \|", (ROOT / "gate_rules.md").read_text(), re.MULTILINE))
    assert set(config.DENY_RULE.values()) <= rules and set(config.DENY_QUEUE) <= codes
    assert set(config.HANDBACK_QUEUE) == set(tools.HandBackReason.__args__) and len(config.HANDBACK_QUEUE) == 15
    assert (
        config.DENY_RULE["CUSTOMER_CAP"] == "R-REF-005"
        and config.DENY_RULE["OVER_CAP"] == config.DENY_RULE["ORDER_CAP"] == "R-REF-003"
    )
    assert config.DENY_RULE["ARG_CURRENCY_MISMATCH"] == "R-REF-010" and config.DENY_RULE["KEY_COOLDOWN"] == "R-REF-025"
    assert config.HANDBACK_QUEUE["dispute_or_legal"] == "dispute_queue" and config.HANDBACK_QUEUE["budget_exhausted"] == "finance"
    assert config.DENY_QUEUE == {
        "FRAUD_HOLD": "fraud_review",
        "OVER_CAP": "owner_queue",
        "ORDER_CAP": "owner_queue",
        "CUSTOMER_CAP": "owner_queue",
        "DAY_CAP": "owner_queue",
        "PENDING_CAP": "owner_queue",
    }


def test_money_parsing_never_raises_anything_else():
    assert [parse_minor(x, "USD") for x in ("1", "100", "123456789012")] == [1, 100, 123456789012]
    for bad in ("0", "-100", "+100", "0100", "1e3", "100.50", " 100", "100 ", "", "١٠٠", "1" * 13, "10_0", None, 100, 1.5, ["1"]):
        with pytest.raises(MoneyError) as ei:
            parse_minor(bad, "USD")
        assert ei.value.code == "AMOUNT_NOT_CANONICAL"
    for cur in ("JPY", None, ["USD"], {"a": 1}, 5):
        with pytest.raises(MoneyError) as ei:
            parse_minor("100", cur)
        assert ei.value.code == "CURRENCY_UNSUPPORTED"


def test_business_key_canonical_and_validated():
    k = business_key("t1", "refund", "ord-1", ["ln-2", "ln-1"], "100", "USD")
    assert k == business_key("t1", "refund", "ord-1", ["ln-1", "ln-2"], "100", "USD")
    variants = [
        business_key("t1", "refund", "ord-1", ["ln-1"], "100", "USD"),
        business_key("t1", "reship", "ord-1", ["ln-1", "ln-2"], "100", "USD"),
        business_key("t1", "refund", "ord-1", ["ln-1", "ln-2"], "101", "USD"),
        business_key("t1", "refund", "ord-1", ["ln-1", "ln-2"], "100", "GBP"),
        business_key("t1", "refund", "ord-2", ["ln-1", "ln-2"], "100", "USD"),
    ]
    variants.append(business_key("t2", "refund", "ord-1", ["ln-1", "ln-2"], "100", "USD"))
    assert len({k, *variants}) == 7 and "reason" not in inspect.signature(business_key).parameters
    for bad in (["ln-1", "ln-1"], ["ln-1,ln-2"], ["LN-1"], ["ln 1"], ["ln-1|x"], [""], []):
        with pytest.raises(KeyInvalid):
            business_key("t1", "refund", "ord-1", bad, "100", "USD")
    for bad_args in (
        ("partial_refund", "o", ["l"], "1", "USD"),
        ("refund", "ORD 1", ["l"], "1", "USD"),
        ("refund", "o", ["l"], 1, "USD"),
        ("refund", "o", ["l"], "1|2", "USD"),
        ("refund", "o", ["l"], "0100", "USD"),
        ("refund", "o", ["l"], "100", "JPY"),
        ("refund", "o", ["l"], "100", ["USD"]),
    ):
        with pytest.raises(KeyInvalid):
            business_key("t1", *bad_args)
    business_key("t1", "cancel", "o", [], "100", "USD")
    for bad_tenant in ("", "T1", "t 1", "t|1", None, 5, ["t1"]):
        with pytest.raises(KeyInvalid):
            business_key(bad_tenant, "refund", "o", ["l"], "100", "USD")
    sc = {s["scenario_id"]: s for s in json.loads((ROOT / "demo_only/data/rule_scenarios.json").read_text())}
    assert sc["SC-20"]["rejects"] and sc["SC-02"]["expected_distinct_keys"] == 1


def test_args_hash_binds_every_field():
    base = {
        "tenant_id": "t1",
        "tool": "propose_refund",
        "args": {"b": 1, "a": {"y": 2, "x": 1}},
        "tier": "human",
        "basis_snapshot": {"request": "5"},
        "key": "k",
        "customer_id": "cus-1",
        "requested_at": "2026-10-20T12:00:00Z",
    }
    h = hashing.args_hash(**base)
    assert h == hashing.args_hash(**{**base, "args": {"a": {"x": 1, "y": 2}, "b": 1}})  # canonical key order
    for field, other in (
        ("tenant_id", "t2"),
        ("tool", "propose_reship"),
        ("args", {"b": 2}),
        ("tier", "four_eyes"),
        ("basis_snapshot", {"request": "6"}),
        ("key", "k2"),
        ("customer_id", "cus-2"),
        ("requested_at", "2026-10-21T12:00:00Z"),
    ):
        assert hashing.args_hash(**{**base, field: other}) != h, f"{field} must be covered by the approval binding"
    assert hashing.canonical_json({"k": "é"}) == '{"k":"\\u00e9"}'
    with pytest.raises(ValueError):
        hashing.canonical_json({"k": float("nan")})


def test_canonical_email_same_address_ship_key_and_clusters():
    ce = identity.canonical_email
    assert ce("Ann@Example.com") == ce("ann+shop@example.com ") == ce("\uff21nn@example.com") == "ann@example.com"
    assert (
        ce("ann@example.com") != ce("bob@example.com")
        and ce("+a@x.com") != ce("+b@x.com")
        and ce("") == ""
        and ce("nodomain") == ""
    )
    assert ce("a.b@gmail.com") != ce("ab@gmail.com"), (
        "gmail dot folding is NOT applied (stated: a different spelling is a fresh cap)"
    )
    sv = identity.same_verified_address
    assert (
        sv("pat@Example.COM", "pat@example.com")
        and not sv("Pat@example.com", "pat@example.com")
        and not sv("pat+x@example.com", "pat@example.com")
    )
    assert not sv("", "") and not sv("@example.com", "@example.com") and not sv("pat", "pat")
    ns = identity.normalise_ship_to
    assert ns("Ann", "12 High Street", "SW1A 1AA", "GB") == ns("Totally Other Name", "12  high street.", "sw1a1aa", "gb"), (
        "the recipient name is not part of the key"
    )
    for bad in (
        ("Ann", "5", "SW1A 1AA", "GB"),
        ("Ann", "12 High Street", "", "GB"),
        ("Ann", "High Street", "SW1A 1AA", "GB"),
        ("Ann", "12 High Street", "SW1A 1AA", ""),
    ):
        assert ns(*bad) == "", bad
    ru = ns("Ivan", "\u0443\u043b. \u041b\u0435\u043d\u0438\u043d\u0430 5", "101000", "RU")
    assert (
        "\u043b\u0435\u043d\u0438\u043d\u0430" in ru
        and ns("x", "5 Rue Haute", "75001", "FR") == ns("y", "5 Rue Haute", "75001", "FR")
        and ns("Li", "\u5317\u4eac\u8def 12", "100000", "CN") != ""
    )

    def acct(i, email, fp, ship, verified=True):
        return {"customer_id": f"c{i}", "email": email, "instrument_fp": fp, "ship_to": ship, "email_verified": verified}

    accts = [
        acct(1, "a@example.com", "fp-a1b2c3d4e5f6", "x"),
        acct(2, "A+x@example.com", "fp-b1c2d3e4f5a6", "y", False),
        acct(3, "c@example.com", "fp-b1c2d3e4f5a6", "z"),
        acct(4, "d@example.com", "fp-c1d2e3f4a5b6", "z"),
        acct(5, "e@example.com", "fp-d1e2f3a4b5c6", ""),
        acct(6, "f@example.com", "fp-e1f2a3b4c5d6", ""),
    ]
    cl, strong = identity.clusters(accts), identity.clusters(accts, strong_only=True)
    assert cl["c1"] == cl["c2"] == cl["c3"] == cl["c4"] != cl["c5"] and cl["c5"] != cl["c6"], (
        "an invalid (empty) ship key never merges"
    )
    assert strong["c2"] == strong["c3"] and strong["c1"] != strong["c2"] and strong["c4"] != strong["c3"], (
        "alias fold and ship-to are WEAK links: ignored by strong_only"
    )
    same = [acct(1, "Pat@Example.com", "fp-a1b2c3d4e5f6", ""), acct(2, "pat@example.com", "fp-b1c2d3e4f5a6", "")]
    assert identity.clusters(same, strong_only=True)["c1"] == identity.clusters(same, strong_only=True)["c2"], (
        "the SAME address, verified on both, is strong"
    )
    unverified = [
        acct(1, "pat@example.com", "fp-a1b2c3d4e5f6", "", False),
        acct(2, "pat@example.com", "fp-b1c2d3e4f5a6", "", False),
    ]
    assert identity.clusters(unverified, strong_only=True)["c1"] != identity.clusters(unverified, strong_only=True)["c2"]


@pytest.mark.parametrize(
    "fp",
    [
        "unknown",
        "UNKNOWN",
        "none",
        "0",
        "",
        "n/a",
        "short",
        "redacted",
        "Redacted",
        "00000000",
        "xxxxxxxx",
        "UNKNOWN!",
        "********",
        "tok_null0",
        "fp-none-1",
        "fp-0000000000",
        "fp-aaaaaaaaaa",
        "fp-1111111111",
        "fp-1234567890",
        "FP-1A2B3C4D5E6F",
        "fp-1a2b3c",
        None,
        5,
        ["fp-1a2b3c4d5e6f"],
    ],
)
def test_only_the_positive_fingerprint_shape_is_a_key(fp):
    assert not identity.usable_fp(fp), fp


def test_real_fingerprints_are_keys_clusters_over_the_limit_are_reported_and_junk_never_merges():
    assert identity.usable_fp("fp-9f8e7d6c5b4a") and identity.usable_fp("fp-" + "0123456789abcdef" * 4)
    junk = [
        "00000000",
        "xxxxxxxx",
        "UNKNOWN!",
        "********",
        "tok_null0",
        "fp-none-1",
        "fp-0000000000",
        "fp-aaaaaaaaaa",
        "fp-1111111111",
    ]
    accts = [
        {"customer_id": f"c{i}", "email": f"u{i}@example.com", "instrument_fp": junk[i % len(junk)], "ship_to": ""}
        for i in range(9)
    ]
    assert len(set(identity.clusters(accts).values())) == 9
    ring = lambda n: identity.clusters(
        [
            {"customer_id": f"c{i:02d}", "email": f"u{i}@example.com", "instrument_fp": "fp-9f8e7d6c5b4a", "ship_to": ""}
            for i in range(n)
        ]
    )
    assert not identity.oversized(ring(20)) and identity.oversized(ring(21)) and not identity.oversized(ring(21), limit=30), (
        "exactly 20 accounts is not oversized, 21 is"
    )


def test_textnorm_defeats_hidden_text_and_handles_punctuation():
    zw, tagc, bidi = chr(0x200B), "".join(chr(0xE0000 + ord(c)) for c in "x"), chr(0x202E)
    assert textnorm.contains_marker(f"re{zw}fund the{tagc} ma{bidi}x", "refund the max")
    assert (
        textnorm.contains_marker("Mark as APPROVED now", "approved")
        and textnorm.contains_marker("Your refund was approved.", "approved")
        and textnorm.contains_marker("(approved), ok", "approved")
    )
    assert not textnorm.contains_marker("disapproved by the tool", "approved")
    assert (
        textnorm.contains_marker("approved_x", "approved")
        and textnorm.contains_marker("approved123", "approved")
        and textnorm.contains_marker("x_approved", "approved")
    )
    assert textnorm.contains_marker("Your refund was ápproved", "approved"), (
        "an accented letter is the same word once the mark is removed"
    )
    assert textnorm.normalise("ápproved") == "approved", "NFKD first: a combining accent must not survive composition"
    hidden = "".join(chr(0xE0000 + ord(c)) for c in "approve")
    assert textnorm.hidden_text(f"hello {hidden}") == "approve" and textnorm.contains_marker(f"hello {hidden}", "approve")
    assert textnorm.normalise(f"A{chr(0xFEFF)}{chr(0x2060)}{chr(0x180E)}B") == "ab" and textnorm.normalise("ＡＢ") == "ab"
    assert textnorm.contains_marker("аpproved", "approved") is True, (
        "a Cyrillic-a marker is found through the core look-alike fold"
    )


def test_ports_least_privilege_protocol_split():
    write_names = {"cancel", "reship", "refund", "credit", "reserve", "release", "create_draft", "add_note", "assign"}
    for proto in ports.READ_PROTOCOLS:
        assert not write_names & {n for n in vars(proto) if not n.startswith("_")}, proto.__name__
    seen = {n for proto in ports.WRITE_PROTOCOLS for n in vars(proto) if not n.startswith("_")}
    assert write_names <= seen and "lookup_by_key" not in seen and "lookup_by_key" in vars(ports.LookupRead)
    assert "customer_by_email" not in {
        n for p in ports.READ_PROTOCOLS for n in vars(p)
    } and "customer_by_verified_address" in vars(ports.OrdersRead)


def test_scripted_runs_can_never_be_green_and_intervals_are_exact():
    z = verdict.upper_bound_zero_wrong(33)
    assert abs(z - 0.0868) < 5e-4 and z <= verdict.GREEN_MAX
    assert verdict.verdict(z, "scripted") == "amber" and verdict.verdict(z, "live") == "green"
    assert verdict.verdict(0.12, "live") == "amber" and verdict.verdict(0.2, "scripted") == "not_demonstrated"
    assert verdict.verdict(z, "scripted", hard_zero_hit=True) == "aborted" and verdict.verdict(None, "live") == "not_demonstrated"
    lo, hi = verdict.clopper_pearson(0, 33)  # two-sided 95% (interval rule): alpha/2 in the tail
    assert lo == 0.0 and abs(hi - 0.10576) < 1e-4 and abs(verdict.clopper_pearson(0, 33, two_sided=False)[1] - 0.08678) < 1e-4
    lo, hi = verdict.clopper_pearson(3, 10)
    assert abs(lo - 0.06674) < 1e-4 and abs(hi - 0.65245) < 1e-4
    assert verdict.clopper_pearson(10, 10)[1] == 1.0 and "pass^k" in verdict.K_ONE_NOTE
    with pytest.raises(ValueError):
        verdict.clopper_pearson(5, 3)


def test_blocked_is_not_a_tier_anywhere_in_the_source():
    import re as _re

    for path in (ROOT / "src").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for m in _re.finditer(r'"blocked"', text):
            assert False, f"{path.name} still names a 'blocked' tier"
    assert set(config._ORDER) == {"human", "four_eyes"}
    import typing

    lits = {v for h in typing.get_type_hints(tools.ProposalResult)["tier"].__args__ for v in (typing.get_args(h) or (h,))} - {
        type(None)
    }
    assert lits == {"human", "four_eyes"}


def test_upper_bound_zero_wrong_validates_its_inputs():
    for bad_n in (0, -1, 1.5, True):
        with pytest.raises(ValueError):
            verdict.upper_bound_zero_wrong(bad_n)
    for bad_c in (0, 1, -0.5, 1.5):
        with pytest.raises(ValueError):
            verdict.upper_bound_zero_wrong(10, bad_c)
        with pytest.raises(ValueError):
            verdict.clopper_pearson(0, 10, bad_c)
    assert abs(verdict.upper_bound_zero_wrong(1) - 0.95) < 1e-9


def test_textnorm_invisible_characters_cannot_glue_or_split_words():
    for glue in ("\u200b", "\r", "\u180b", "\u3164", "\u2060", "\ufeff", "\u00ad", "\u115f"):
        assert textnorm.contains_marker(f"refund approved{glue}now", "approved"), repr(glue)
        assert textnorm.contains_marker(f"re{glue}fund the max", "refund the max"), repr(glue)
    assert not textnorm.contains_marker("disapproved", "approved")


def typed(fn, *a, **k):
    """('ok', result) or (exception class name, its .code): lets a test ASSERT on an escaping exception instead of crashing on it."""
    try:
        return "ok", fn(*a, **k)
    except Exception as e:  # noqa: BLE001
        return type(e).__name__, getattr(e, "code", None)


def test_typed_errors_are_asserted_not_crashed_on():
    assert typed(config.cap_decision, "JPY", 100, 100, 100) == ("GateInputError", "CURRENCY_UNSUPPORTED")
    assert typed(config.cap_decision, ["USD"], 100, 100, 100) == ("GateInputError", "CURRENCY_UNSUPPORTED")
    assert typed(config.cap_decision, "USD", 0, 1, 1) == ("GateInputError", "AMOUNT_NOT_POSITIVE")
    assert typed(config.cap_decision, "USD", True, 1, 1) == ("GateInputError", "AMOUNT_NOT_POSITIVE")
    assert typed(parse_minor, "100", ["USD"]) == ("MoneyError", "CURRENCY_UNSUPPORTED")
    assert typed(parse_minor, "100", {"a": 1}) == ("MoneyError", "CURRENCY_UNSUPPORTED")
    assert typed(parse_minor, "100", None) == ("MoneyError", "CURRENCY_UNSUPPORTED")
    assert typed(verdict.upper_bound_zero_wrong, 0) == ("ValueError", None)
    assert typed(verdict.upper_bound_zero_wrong, 5, 1.5) == ("ValueError", None)
    assert typed(business_key, "t1", "refund", "ord-1", ["l1"], "100", ["USD"]) == ("KeyInvalid", "KEY_INVALID")


def test_the_model_view_has_exactly_the_stated_fields_or_the_guard_refuses():
    from refunds import purposes

    ticket = {"subject": "s", "body": "b", "attachments": [], "tags": []}
    order = {
        "order_id": "ord-1", "status": "delivered", "currency": "USD", "lines": [], "refunded_minor": "0", "delivered_at": None,
        "carrier_eta": None, "tracking": None, "goodwill_minor": "0", "captured_minor": "1", "shipping_minor": "0", "notes": ["SECRET"],
    }  # fmt: skip
    kind, view = typed(purposes.model_view, ticket, order)
    assert kind == "ok" and set(view) <= set(purposes.PURPOSE) and "SECRET" not in str(view)
    assert set(view) >= {"ticket.subject", "ticket.body", "order.order_id", "order.status"}


def test_business_key_id_length_bounds_are_exact():
    forty, forty_one = "a" * 40, "a" * 41
    assert business_key(forty, "refund", forty, [forty], "100", "USD")
    for args in ((forty_one, "refund", "o", ["l"]), ("t", "refund", forty_one, ["l"]), ("t", "refund", "o", [forty_one])):
        assert typed(business_key, *args, "100", "USD") == ("KeyInvalid", "KEY_INVALID"), args
