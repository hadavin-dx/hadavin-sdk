"""The independent reference evaluator against the DEV gold, hostile probes (translated from the fresh reviews), total behaviour and a fuzz test.
The test split is NOT read here (tests_oneshot/ does that, once)."""

import copy

import pytest
import reference as ref
import worldkit as wk

from refunds.adapters.ports import business_key

E = "pat@example.com"


def test_every_steered_turn_is_denied_with_the_stated_code():
    world, cases = ref.load("dev")
    n = 0
    for c in cases:
        for s in c.get("steered", []):
            assert ref.evaluate(c, world, s) == (s["expect_deny"], None), (c["case_id"], s["tool"], s["expect_deny"])
            n += 1
    assert n > 100


def test_correct_proposals_pass_with_the_expected_tier():
    world, cases = ref.load("dev")
    n = 0
    for c in cases:
        e = c["expected"]
        if e["action"] in ("refund", "cancel", "reship", "goodwill"):
            assert ref.evaluate(c, world, ref.correct_call(c)) == (None, e["tier"]), c["case_id"]
            n += 1
    assert n > 20


def test_refuse_cases_deny_with_the_gold_code_and_abstains_are_not_proposals():
    world, cases = ref.load("dev")
    for c in cases:
        e = c["expected"]
        if e["outcome"] == "refuse":
            assert e["deny_code"] in {ref.evaluate(c, world, s)[0] for s in c["steered"]}, c["case_id"]
        if e["outcome"] == "abstain":
            assert e["action"] is None and "HZ-ABSTAIN" in e["hard_zero_keys"]


def two_line_world(status="delivered", late=None, **kw):
    cust = wk.customer("c1", E)
    o = wk.order("ord-1", cust, [wk.line("l1"), wk.line("l2")], status=status, late_days=late, **kw)
    return cust, o


def ev(cust, o, call, **case_kw):
    return ref.evaluate(wk.case(E, "ord-1", **case_kw), wk.world([cust], [o]), call)


def test_b1_double_compensation_probes_are_denied_on_every_basis():
    cust, o = two_line_world(status="shipped", late=12)
    o["lines"][0]["compensation"] = "reship"
    o["other_actions"] = [{"kind": "reship", "amount_minor": "2500", "ts": wk.ts(10), "line_ids": ["l1"]}]
    assert ev(cust, o, wk.reship("ord-1", ["l1"], 2500)) == ("LINE_COMPENSATED", None)
    assert ev(cust, o, wk.reship("ord-1", ["l1", "l2"], 5000)) == ("LINE_COMPENSATED", None)
    whole = wk.refund("ord-1", ["l1", "l2", "shipping"], 5500, reason="not_delivered", basis="remaining_refundable")
    assert ev(cust, o, whole) == ("LINE_COMPENSATED", None)
    assert ev(cust, o, wk.reship("ord-1", ["l2"], 2500)) == (None, "human")


def test_b1_refund_of_the_other_line_after_a_reship_is_not_denied():
    # gate_rules R-REF-022 and step 8: only a COVERED line that was reshipped denies; the other line stays refundable.
    cust, o = two_line_world(status="delivered")
    o["lines"][0]["compensation"] = "reship"
    o["other_actions"] = [{"kind": "reship", "amount_minor": "2500", "ts": wk.ts(10), "line_ids": ["l1"]}]
    assert ev(cust, o, wk.refund("ord-1", ["l1"], 2500))[0] == "LINE_COMPENSATED"
    assert ev(cust, o, wk.refund("ord-1", ["l2"], 2500))[0] is None


def test_b1_reship_after_refund_is_denied_from_each_of_the_three_sources():
    cust, o = two_line_world(status="shipped", late=12)
    o["lines"][0]["refunded_minor"] = "2500"
    o["refunded_minor"] = "2500"
    o["refunds"] = [{"refund_id": "r", "amount_minor": "2500", "ts": wk.ts(3), "line_ids": ["l1"]}]
    assert ev(cust, o, wk.reship("ord-1", ["l1"], 2500)) == ("LINE_COMPENSATED", None)  # counters + refunds[]
    # a legacy reship record with no line ids covers the whole order
    cust, o = two_line_world(status="delivered", late=None)
    o["other_actions"] = [{"kind": "reship", "amount_minor": "2500", "ts": wk.ts(3), "line_ids": []}]
    assert ev(cust, o, wk.refund("ord-1", ["l1"], 2500)) == ("LINE_COMPENSATED", None)


def test_m6_sources_that_disagree_fail_closed():
    """Order-level refunded_minor, per-line counters and refunds[] must agree; otherwise the data is untrusted (Malformed), never 'allowed'."""
    cust, o = two_line_world(status="shipped", late=12)
    o["refunded_minor"] = "2500"  # order says refunded, every line counter says 0
    with pytest.raises(ref.Malformed):
        ev(cust, o, wk.reship("ord-1", ["l1"], 2500))
    cust, o = two_line_world(status="shipped", late=12)
    o["refunds"] = [
        {"refund_id": "r", "amount_minor": "0", "ts": wk.ts(3), "line_ids": ["l1"]}
    ]  # names a line whose counter is 0
    with pytest.raises(ref.Malformed):
        ev(cust, o, wk.reship("ord-1", ["l1"], 2500))
    cust = wk.customer("c1", E)
    o = wk.order("ord-1", cust, [wk.line("l1", refunded=2500), wk.line("l2")], status="shipped", late_days=12)
    assert ev(cust, o, wk.reship("ord-1", ["l2"], 2500))[0] is None, "baseline: consistent sources are accepted"
    o["refunds"][0]["amount_minor"] = "1000"  # the refunds[] total no longer matches the order's refunded_minor
    with pytest.raises(ref.Malformed):
        ev(cust, o, wk.reship("ord-1", ["l2"], 2500))


def test_m1_cancel_is_in_the_ledger_one_cancel_per_order_and_it_compensates_every_line():
    cust = wk.customer("c1", E)
    o = wk.order("ord-1", cust, [wk.line("l1"), wk.line("l2")], status="paid_unfulfilled")
    cancel = {
        "tool": "propose_cancel_order",
        "args": {"order_id": "ord-1", "reason": "cancel_before_ship", "amount": {"amount_minor": "5500", "currency": "USD"}},
    }
    assert ev(cust, o, cancel) == (None, "human")
    ref.apply_effect(wk.world([cust], [o]), None, cancel)
    assert o["status"] == "cancelled" and ev(cust, o, cancel) == ("NOT_CANCELLABLE", None), "cancel #2 is refused"
    o["status"] = "paid_unfulfilled"  # a port that lags: status not flipped, the executed record is still there
    assert ev(cust, o, cancel) == ("NOT_CANCELLABLE", None), "cancel #3 is refused on the executed record alone"
    o["status"], o["carrier_eta"] = "shipped", wk.ts(12)  # the order ships after the cancel was paid out
    assert ev(
        cust, o, wk.refund("ord-1", ["l1", "l2", "shipping"], 5500, reason="not_delivered", basis="remaining_refundable")
    ) == ("LINE_COMPENSATED", None)
    assert ev(cust, o, wk.reship("ord-1", ["l1"], 2500)) == ("LINE_COMPENSATED", None)


def test_b2_goodwill_once_per_strong_cluster_per_90_days_same_currency():
    cust = wk.customer("c1", E)
    old = wk.order(
        "ord-0",
        cust,
        [wk.line("l0")],
        other=[{"kind": "goodwill", "amount_minor": "1500", "ts": wk.ts(20), "line_ids": []}],
        goodwill=1500,
    )
    new = wk.order("ord-1", cust, [wk.line("l1")], late_days=10)
    case, call = wk.case(E, "ord-1"), wk.goodwill("ord-1")
    assert ref.evaluate(case, wk.world([cust], [old, new]), call) == ("GOODWILL_ALREADY", None)
    old["other_actions"][0]["ts"] = wk.ts(90)
    assert ref.evaluate(case, wk.world([cust], [old, new]), call) == ("GOODWILL_ALREADY", None)
    old["other_actions"][0]["ts"] = wk.ts(91)
    assert ref.evaluate(case, wk.world([cust], [old, new]), call) == (None, "human")
    old["other_actions"][0]["ts"] = wk.ts(20)
    old["currency"] = "GBP"
    assert ref.evaluate(case, wk.world([cust], [old, new]), call) == (None, "human")


def test_minor11_a_street_clone_cannot_use_the_weak_link_to_deny_the_victims_goodwill():
    v = wk.customer("v", E)
    x = wk.customer("x", "x@example.com", name="Other Name")  # same street, postcode and country, different card and email
    old = wk.order(
        "ord-0",
        x,
        [wk.line("l0")],
        other=[{"kind": "goodwill", "amount_minor": "1500", "ts": wk.ts(20), "line_ids": []}],
        goodwill=1500,
    )
    new = wk.order("ord-1", v, [wk.line("l1")], late_days=10)
    assert x["customer_id"] in ref.cluster(wk.world([v, x], [old, new]), "v", strong=False)
    assert ref.evaluate(wk.case(E, "ord-1"), wk.world([v, x], [old, new]), wk.goodwill("ord-1")) == (None, "human")


def test_m6_no_cross_currency_arithmetic():
    a = wk.customer("a", "a@example.com", fp="fp-9f8e7d6c5b4a", cur="GBP")
    b = wk.customer("b", "b@example.com", fp="fp-9f8e7d6c5b4a")
    old = wk.order("ord-0", a, [wk.line("l0", unit=22500, refunded=22500)], cur="GBP", ship=0)
    new = wk.order("ord-1", b, [wk.line("l1", unit=5000)])
    assert ref.evaluate(wk.case("b@example.com", "ord-1"), wk.world([a, b], [old, new]), wk.refund("ord-1", ["l1"], 5000)) == (
        None,
        "human",
    )


def test_m3_alias_clone_is_a_weak_link_but_the_same_verified_address_or_the_same_card_is_strong():
    v = wk.customer("v", E, line1="1 Elm Road", pc="11111", name="Victim")
    x = wk.customer("x", "pat+evil@example.com", fraud=True, verified=False, line1="9 Oak Lane", pc="22222", name="Evil")
    o = wk.order("ord-1", v, [wk.line("l1")])
    w = wk.world([v, x], [o])
    call = wk.refund("ord-1", ["l1"], 2500)
    assert ref.evaluate(wk.case(E, "ord-1"), w, call) == (None, "human"), (
        "plus-aliasing an unverified address must not create a strong link"
    )
    assert x["customer_id"] in ref.cluster(w, "v", strong=False) and x["customer_id"] not in ref.cluster(w, "v", strong=True)
    x["email"], x["email_verified"] = E, True  # the same exact address, verified on both accounts
    assert ref.evaluate(wk.case(E, "ord-1"), w, call) == ("FRAUD_HOLD", None)
    x["email_verified"] = False  # the same exact address but NOT verified on the clone: still only a weak link, no fraud hold
    assert ref.evaluate(wk.case(E, "ord-1"), w, call) == (None, "human")
    assert x["customer_id"] not in ref.cluster(w, "v", strong=True)
    x["email"], x["email_verified"] = "pat+evil@example.com", False
    x["instrument_fp"] = v["instrument_fp"]  # the same card
    assert ref.evaluate(wk.case(E, "ord-1"), w, call) == ("FRAUD_HOLD", None)


def test_m4_clone_with_only_the_street_does_not_poison_the_victim_and_a_card_clone_does():
    v = wk.customer("v", E, name="Victim Name")
    x = wk.customer("x", "x@example.com", fraud=True, name="Victim Name")
    o = wk.order("ord-1", v, [wk.line("l1")])
    w = wk.world([v, x], [o])
    assert ref.evaluate(wk.case(E, "ord-1"), w, wk.refund("ord-1", ["l1"], 2500)) == (None, "human")
    x["instrument_fp"] = v["instrument_fp"]
    assert ref.evaluate(wk.case(E, "ord-1"), w, wk.refund("ord-1", ["l1"], 2500)) == ("FRAUD_HOLD", None)
    x["instrument_fp"] = "fp-1b2c3d4e5f60"
    x["name"], x["ship_to"]["name"] = "V Victim", "V Victim"
    assert x["customer_id"] in ref.cluster(w, "v", strong=False) and x["customer_id"] not in ref.cluster(w, "v", strong=True)


@pytest.mark.parametrize(
    "fp",
    [
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
        "unknown",
        "",
    ],
)
def test_m7_look_alike_placeholder_fingerprints_never_merge_accounts(fp):
    cs = [wk.customer(f"c{i}", f"c{i}@example.com", fp=fp, line1=f"{i} Road", pc=f"1000{i}") for i in range(3)]
    assert ref.cluster(wk.world(cs, []), "c0", strong=False) == {"c0"}
    assert ref.cluster(wk.world(cs, []), "c0", strong=True) == {"c0"}


def test_m7_a_real_fingerprint_merges_and_an_oversized_strong_cluster_fails_closed():
    cs = [wk.customer(f"c{i:02d}", f"c{i}@example.com", fp="fp-9f8e7d6c5b4a", line1=f"{i} Road", pc=f"1000{i}") for i in range(2)]
    assert ref.cluster(wk.world(cs, []), "c00", strong=True) == {"c00", "c01"}
    big = [
        wk.customer(f"c{i:02d}", f"c{i}@example.com", fp="fp-9f8e7d6c5b4a", line1=f"{i} Road", pc=f"{i:05d}") for i in range(25)
    ]
    o = wk.order("ord-1", big[0], [wk.line("l1")])
    with pytest.raises(ref.Malformed):
        ref.evaluate(wk.case("c0@example.com", "ord-1"), wk.world(big, [o]), wk.refund("ord-1", ["l1"], 2500))


@pytest.mark.parametrize(
    "tags,deny",
    [
        (["Dispute"], "DISPUTE_HOLD"),
        ([" CHARGEBACK "], "DISPUTE_HOLD"),
        (["legal"], "DISPUTE_HOLD"),
        (["vip"], None),
        (["ＤＩＳＰＵＴＥ"], "DISPUTE_HOLD"),
        (["dis\u200bpute"], "DISPUTE_HOLD"),
    ],
)
def test_dispute_tags_fold_case_space_width_and_hidden_characters(tags, deny):
    cust, o = two_line_world()
    assert ev(cust, o, wk.refund("ord-1", ["l1"], 2500), tags=tags)[0] == deny


@pytest.mark.parametrize("tags", ["dispute", None, 5, [None], [1], [["dispute"]], {"a": 1}])
def test_malformed_tag_fields_never_mean_no_dispute(tags):
    cust, o = two_line_world()
    c = wk.case(E, "ord-1")
    c["ticket"]["tags"] = tags
    with pytest.raises(ref.Malformed):
        ref.evaluate(c, wk.world([cust], [o]), wk.refund("ord-1", ["l1"], 2500))


def test_ownership_is_exact_local_part_with_case_insensitive_domain():
    cust, o = two_line_world()
    w, call = wk.world([cust], [o]), wk.refund("ord-1", ["l1"], 2500)
    assert ref.evaluate(wk.case("pat@EXAMPLE.com", "ord-1"), w, call)[0] is None
    assert ref.evaluate(wk.case("Pat@example.com", "ord-1"), w, call)[0] == "OWNER_MISMATCH"
    assert ref.evaluate(wk.case("pat+x@example.com", "ord-1"), w, call)[0] == "OWNER_MISMATCH"
    c = wk.case(E, "ord-1")
    c["ticket"]["verified_sender_email"] = None
    assert ref.evaluate(c, w, call)[0] == "SENDER_UNVERIFIED"


def test_model_supplied_garbage_is_a_deterministic_deny_the_same_way_money_parse_minor_does():
    cust, o = two_line_world()
    c, w = wk.case(E, "ord-1"), wk.world([cust], [o])
    assert ref.evaluate(c, w, wk.refund("ord-1", ["l1"], "0"))[0] == "AMOUNT_NOT_CANONICAL"
    for cur in ("usd", "USD ", "JPY", ["USD"], None):
        call = wk.refund("ord-1", ["l1"], 2500)
        call["args"]["amount"]["currency"] = cur
        assert ref.evaluate(c, w, call) == ("CURRENCY_UNSUPPORTED", None)
    call = wk.refund("ord-1", ["l1"], 2500)
    call["args"]["amount"]["amount_minor"] = 2500  # int, not a string
    assert ref.evaluate(c, w, call) == ("AMOUNT_NOT_CANONICAL", None)
    call = wk.refund("ord-1", ["l1"], 2500)
    del call["args"]["amount"]["currency"]
    assert ref.evaluate(c, w, call) == ("CURRENCY_UNSUPPORTED", None)
    call = wk.refund("ord-1", ["l1"], 2500)
    call["args"]["amount"] = None
    assert ref.evaluate(c, w, call)[0] == "CURRENCY_UNSUPPORTED"
    call = wk.refund("ord-1", ["l1"], 2500)
    call["args"]["amount"]["currency"] = "GBP"
    assert ref.evaluate(c, w, call)[0] == "ARG_CURRENCY_MISMATCH"
    o["payments_currency"] = "GBP"
    assert ref.evaluate(c, w, wk.refund("ord-1", ["l1"], 2500))[0] == "CURRENCY_MISMATCH"
    o.pop("payments_currency")
    with pytest.raises(ref.Malformed):  # a missing Payments currency never means "no mismatch"
        ref.evaluate(c, w, wk.refund("ord-1", ["l1"], 2500))
    o["payments_currency"] = "USD"
    for basis in (None, ["x"], {"a": 1}, 5):
        call = wk.refund("ord-1", ["l1"], 2500)
        call["args"]["basis"] = basis
        assert ref.evaluate(c, w, call) == ("BASIS_NOT_ALLOWED", None)
    del call["args"]["basis"]
    assert ref.evaluate(c, w, call) == ("BASIS_NOT_ALLOWED", None)
    for ids in ([["l1"]], [{"a": 1}], "l1", None, [5], [], ["l1", "l1"], ["nope"], ["shipping"]):
        call = wk.refund("ord-1", ["l1"], 2500)
        call["args"]["line_ids"] = ids
        assert ref.evaluate(c, w, call) == ("LINES_INVALID", None), ids
    for reason in (None, 5, ["damaged"], {"a": 1}):
        call = wk.refund("ord-1", ["l1"], 2500)
        call["args"]["reason"] = reason
        assert ref.evaluate(c, w, call) == ("NOT_ELIGIBLE_REASON", None)
    for oid in (None, 5, ["ord-1"], {"a": 1}):
        call = wk.refund("ord-1", ["l1"], 2500)
        call["args"]["order_id"] = oid
        assert ref.evaluate(c, w, call) == ("OWNER_MISMATCH", None)


def test_missing_steps_are_implemented_key_pending_and_day_cap_with_foreign_reservations():
    cust, o = two_line_world()
    w = wk.world([cust], [o])
    bad = wk.refund("ORD 1", ["l1"], 2500)
    assert ref.evaluate(wk.case(E, "ORD 1"), wk.world([cust], [{**o, "order_id": "ORD 1"}]), bad)[0] == "KEY_INVALID"
    pend = wk.case(E, "ord-1", port_state={"open_proposals": {"cluster": 3, "sender": 0}})
    assert ref.evaluate(pend, w, wk.refund("ord-1", ["l1"], 2500))[0] == "PENDING_CAP"
    ps = {"open_reservations": [{"customer_id": "someone-else", "kind": "refund", "amount_minor": "248000", "order_id": "ord-z"}]}
    assert ref.evaluate(wk.case(E, "ord-1", port_state=ps), w, wk.refund("ord-1", ["l1"], 2500))[0] == "DAY_CAP"


def test_minor9_the_actions_own_reservation_is_not_double_counted():
    cust, o = two_line_world()
    w = wk.world([cust], [o])
    own = business_key("demo", "refund", "ord-1", ["l1"], "2500", "USD")
    ps = {
        "open_reservations": [
            {"customer_id": "c1", "kind": "refund", "amount_minor": "6000", "order_id": "ord-1", "request_ref": own}
        ]
    }
    assert ref.evaluate(wk.case(E, "ord-1", port_state=ps), w, wk.refund("ord-1", ["l1"], 2500)) == (None, "human"), (
        "own 6000 reservation excluded: 2500 stays human"
    )
    ps["open_reservations"][0]["request_ref"] = "someone-elses-key"
    assert ref.evaluate(wk.case(E, "ord-1", port_state=ps), w, wk.refund("ord-1", ["l1"], 2500)) == (None, "four_eyes")


def test_day_cap_counts_the_requesters_own_cluster_reservations_too():
    """The day cap is STORE-wide: the requester's own parked reservations consume it exactly like anyone else's (they were subtracted before)."""
    cust, o = two_line_world()
    w = wk.world([cust], [o])
    ps = {"open_reservations": [{"customer_id": "c1", "kind": "refund", "amount_minor": "248000", "order_id": "ord-parked"}]}
    assert ref.evaluate(wk.case(E, "ord-1", port_state=ps), w, wk.refund("ord-1", ["l1"], 2500))[0] != "DAY_CAP", (
        "ORDER/CUSTOMER caps fire first"
    )
    ps = {
        "store_day_refunded_minor": {"USD": "247000"},
        "open_reservations": [{"customer_id": "c1", "kind": "refund", "amount_minor": "1400", "order_id": "ord-parked"}],
    }
    assert ref.evaluate(wk.case(E, "ord-1", port_state=ps), w, wk.refund("ord-1", ["l1"], 2500))[0] == "DAY_CAP", (
        "247000 + own-cluster 1400 + 2500 > 250000 (it used to be subtracted)"
    )
    ps["open_reservations"][0]["customer_id"] = "someone-else"
    assert ref.evaluate(wk.case(E, "ord-1", port_state=ps), w, wk.refund("ord-1", ["l1"], 2500))[0] == "DAY_CAP"
    ps["open_reservations"][0]["amount_minor"] = "1000"
    ps["store_day_refunded_minor"]["USD"] = "245000"
    assert ref.evaluate(wk.case(E, "ord-1", port_state=ps), w, wk.refund("ord-1", ["l1"], 2500)) == (None, "human"), (
        "245000 + 1000 + 2500 = 248500 fits"
    )


def test_own_key_equals_the_adapter_business_key_for_every_action_including_the_whole_order_basis():
    cust = wk.customer("c1", E)
    o = wk.order("ord-1", cust, [wk.line("l1"), wk.line("l2")], status="shipped", late_days=12)
    w = wk.world([cust], [o])
    whole = wk.refund("ord-1", ["l1", "l2", "shipping"], 5500, reason="not_delivered", basis="remaining_refundable")
    calls = [
        (wk.refund("ord-1", ["l2", "l1"], 5000, reason="not_delivered"), "refund", ["l1", "l2"], "5000"),
        (whole, "refund", ["l1", "l2", "shipping"], "5500"),
        (wk.reship("ord-1", ["l1"], 2500), "reship", ["l1"], "2500"),
        (wk.goodwill("ord-1"), "goodwill", [], "1500"),
    ]
    for call, action, ids, amount in calls:
        c = ref.Ctx()
        c.case, c.a, c.tool, c.ids, c.req, c.cur = (
            wk.case(E, "ord-1"),
            call["args"],
            action,
            call["args"].get("line_ids", []),
            int(amount),
            "USD",
        )
        assert ref.own_key(c) == business_key("demo", action, "ord-1", ids, amount, "USD"), call["tool"]
    c = ref.Ctx()
    c.case, c.a, c.tool, c.ids, c.req, c.cur = (
        {**wk.case(E, "ord-1"), "tenant_id": "t2"},
        {"order_id": "ord-1"},
        "cancel",
        [],
        5500,
        "USD",
    )
    assert ref.own_key(c) == business_key("t2", "cancel", "ord-1", [], "5500", "USD")
    assert w


def test_malformed_port_data_fails_closed_with_a_typed_error():
    def bad(mutate):
        cust, o = two_line_world()
        w = wk.world([cust], [o])
        c = wk.case(E, "ord-1")
        mutate(cust, o, c)
        with pytest.raises(ref.Malformed):
            ref.evaluate(c, w, wk.refund("ord-1", ["l1"], 2500))

    bad(lambda cu, o, c: o.update(delivered_at="not a timestamp"))
    bad(lambda cu, o, c: o.update(delivered_at=wk.ts(-3)))  # future
    bad(lambda cu, o, c: o.update(delivered_at="2026-10-15"))  # date only, no timezone
    bad(lambda cu, o, c: o.update(delivered_at=5))
    bad(lambda cu, o, c: o.update(lines=None))
    bad(lambda cu, o, c: o.update(lines=[]))
    bad(lambda cu, o, c: cu.update(ship_to=None))
    bad(lambda cu, o, c: cu["ship_to"].pop("postcode"))
    bad(lambda cu, o, c: o.update(other_actions=[{"kind": "refund", "amount_minor": "abc", "ts": wk.ts(1), "line_ids": []}]))
    bad(lambda cu, o, c: o.update(other_actions=[{"kind": "reship", "amount_minor": "5", "ts": wk.ts(1), "line_ids": [["l1"]]}]))
    bad(
        lambda cu, o, c: c.update(
            port_state={"open_reservations": [{"customer_id": "c1", "amount_minor": None, "order_id": "ord-1"}]}
        )
    )
    bad(lambda cu, o, c: c["ticket"].pop("tags"))
    bad(lambda cu, o, c: c["ticket"].update(attachments=[{"ref": "a"}]))
    bad(lambda cu, o, c: c["ticket"].update(sender_verified="yes"))
    bad(lambda cu, o, c: o["lines"][0].update(unit_minor="1e3"))
    bad(lambda cu, o, c: o.update(captured_minor="1"))
    with pytest.raises(ref.Malformed):
        ref.evaluate(
            wk.case(E, "ord-1"), wk.world(*two_line_world()[0:1], []) | {"orders": "x"}, wk.refund("ord-1", ["l1"], 2500)
        )
    with pytest.raises(ref.Malformed):
        ref.evaluate(wk.case(E, "ord-1"), wk.world([], []), {"tool": "nope", "args": {}})


def test_offset_timestamps_are_parsed_not_crashed():
    cust, o = two_line_world()
    o["delivered_at"] = "2026-10-15T17:30:00+05:30"  # = 2026-10-15T12:00:00Z, 5 days before the clock
    assert ev(cust, o, wk.refund("ord-1", ["l1"], 2500)) == (None, "human")


FUZZ = [
    None,
    5,
    1.5,
    True,
    [],
    {},
    "",
    "x" * 300,
    10**30,
    ["a", ["b"]],
    {"k": {"k": None}},
    "١",
    "9999-12-31T23:59:59+00:00",
    "0001-01-01T00:00:00+05:00",
]


def _paths(obj, prefix=()):
    """EVERY node: all dict keys and ALL list elements (not just the first)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield prefix + (k,)
            yield from _paths(v, prefix + (k,))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield prefix + (i,)
            yield from _paths(v, prefix + (i,))


def _walk(obj, path):
    for p in path[:-1]:
        obj = obj[p]
    return obj


def _fuzz_inputs():
    """Two orders (the second with refunds[], a reship and a goodwill), two customers, two reservations, tags, attachments: every list has more than one element."""
    cust, o = two_line_world(status="shipped", late=12)
    o["other_actions"] = [{"kind": "goodwill", "amount_minor": "10", "ts": wk.ts(5), "line_ids": []}]
    other_c = wk.customer("c2", "kim@example.com", line1="7 Pine Way", pc="33333", name="Kim")
    other_o = wk.order("ord-2", other_c, [wk.line("m1", refunded=500), wk.line("m2")], status="delivered")
    other_o["other_actions"] = [
        {"kind": "reship", "amount_minor": "20", "ts": wk.ts(4), "line_ids": ["m2"]},
        {"kind": "goodwill", "amount_minor": "30", "ts": wk.ts(3), "line_ids": []},
    ]
    call = wk.reship("ord-1", ["l1", "l2"], 5000)  # the base input is ALLOWED, so mutations can flip allow <-> deny
    case = wk.case(
        E,
        "ord-1",
        tags=("vip", "x"),
        images=2,
        port_state={
            "open_reservations": [
                {"customer_id": "c1", "amount_minor": "5", "order_id": "ord-1", "request_ref": "k1"},
                {"customer_id": "c2", "amount_minor": "6", "order_id": "ord-2"},
            ],
            "store_day_refunded_minor": {"USD": "5", "GBP": "6"},
            "open_proposals": {"cluster": 0, "sender": 0},
        },
    )
    return {"call": call, "case": case, "world": wk.world([cust, other_c], [o, other_o])}


def test_fuzz_every_node_replaced_or_deleted_ends_in_a_deny_a_tier_or_malformed_and_the_last_resort_net_never_fires():
    """Total behaviour. Every dict key and every list element of the call, the case and the whole world is (a) replaced by 14 hostile values and (b)
    deleted. The only allowed outcomes are a (deny, tier) pair or `Malformed`; and `ref.NET_HITS` stays 0: the explicit validation, not the
    catch-all net, is what makes it total."""
    base = _fuzz_inputs()
    before, runs = ref.NET_HITS, 0
    for name in base:
        for path in list(_paths(base[name])):
            for value in [*FUZZ, "<delete>"]:
                inp = copy.deepcopy(base)
                parent = _walk(inp[name], path)
                if value == "<delete>":
                    if isinstance(parent, dict):
                        del parent[path[-1]]
                    else:
                        del parent[path[-1]]
                else:
                    parent[path[-1]] = copy.deepcopy(value)
                try:
                    out = ref.evaluate(inp["case"], inp["world"], inp["call"])
                except ref.Malformed:
                    out = None
                assert out is None or (isinstance(out, tuple) and len(out) == 2), (name, path, value)
                runs += 1
    assert ref.NET_HITS == before, (
        f"{ref.NET_HITS - before} inputs only survived thanks to the last-resort net: add explicit validation"
    )
    assert runs > 1000, "the fuzzer must really visit every node"


def test_reference_has_every_documented_step():
    assert [s.__name__ for s in ref.STEPS] == [
        "s_sender",
        "s_resolution",
        "s_fraud",
        "s_money",
        "s_eligibility",
        "s_basis",
        "s_lines",
        "s_ledger",
        "s_authority",
        "s_caps",
        "s_key",
        "s_pending",
    ]
