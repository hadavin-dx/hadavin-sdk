"""purpose-and-blast-radius rule: purpose limitation and a small blast radius. A negative test per control."""

import copy
import json

import pytest
import reference as ref

from refunds import guards, purposes
from refunds import identities as idn

CANARIES = {
    "internal_memo": "CANARY-NP-MEMO-5d2e",
    "created_at": "CANARY-NP-CREATED-91ab",
    "notes": "CANARY-NP-NOTE-77c0",
    "name": "CANARY-NP-NAME-3f19",
    "ship_name": "CANARY-NP-SHIP-aa42",
    "filename": "CANARY-NP-FILE-0b8d.jpg",
}


def planted_world():
    world, cases = ref.load("dev")
    world = copy.deepcopy(world)
    for o in world["orders"]:
        o["internal_memo"] = CANARIES["internal_memo"]
        o["notes"] = [CANARIES["notes"]]
        o["ship_to"] = {**o["ship_to"], "name": CANARIES["ship_name"]}
    for c in world["customers"]:
        c["created_at"] = CANARIES["created_at"]
        c["name"] = CANARIES["name"]
    return world, copy.deepcopy(cases)


def test_every_field_that_reaches_the_model_has_a_stated_purpose():
    assert purposes.PURPOSE and all(isinstance(v, str) and len(v) > 8 for v in purposes.PURPOSE.values())
    world, cases = ref.load("dev")
    orders = {o["order_id"]: o for o in world["orders"]}
    for c in cases:
        assert set(purposes.model_view(c["ticket"], orders.get(c["order_ref"] or ""))) <= set(purposes.PURPOSE), c["case_id"]


def test_a_canary_in_a_non_purpose_field_never_reaches_the_model_logs_or_outputs():
    world, cases = planted_world()
    orders = {o["order_id"]: o for o in world["orders"]}
    log = guards.ReadLog()
    outputs = []
    for c in cases:
        c["ticket"]["attachments"] = [{**a, "filename": CANARIES["filename"]} for a in c["ticket"]["attachments"]]
        o = orders.get(c["order_ref"] or "")
        view = purposes.model_view(c["ticket"], o)
        log.read(
            "agent_runtime",
            "orders",
            sorted(k for k in view if k.startswith("order.")),
            c["order_ref"] or "none",
            "decide refund eligibility",
            1 if o else 0,
            "2026-10-20T12:00:00Z",
        )
        for s in c.get("steered", []):
            outputs.append(json.dumps(ref.evaluate(c, world, s)))
        outputs.append(json.dumps(view, sort_keys=True))
    blob = json.dumps(outputs) + json.dumps(log.export_for_client())
    for name, can in CANARIES.items():
        assert can not in blob, f"{name} leaked into the model view, an output or the read log"
    assert len(log.entries) == len(cases)


def test_the_agent_is_denied_a_field_outside_its_purpose():
    log = guards.ReadLog()
    for bad in ("order.internal_memo", "customer.created_at", "customer.name", "order.notes", "ticket.attachment_filename"):
        with pytest.raises(PermissionError):
            log.read("agent_runtime", "orders", [bad], "ord-1", "x", 1, "t")


def test_read_log_records_who_what_why_and_row_count_without_pii():
    log = guards.ReadLog()
    log.read(
        "agent_runtime",
        "orders",
        ["order.status", "order.lines"],
        "ord-1022",
        "decide refund eligibility",
        1,
        "2026-10-20T12:00:00Z",
    )
    e = log.export_for_client()[0]
    assert (e["who"], e["port"], e["fields"], e["why"], e["rows"]) == (
        "agent_runtime",
        "orders",
        ["order.lines", "order.status"],
        "decide refund eligibility",
        1,
    )
    assert "ord-1022" not in json.dumps(e) and len(e["ref_sha256"]) == 16


def test_read_only_role_stays_under_the_request_rate_and_connection_caps_in_a_load_test():
    cap = guards.RateCap(max_per_s=50, max_connections=5)
    per_second = {}
    offered = 0
    for t in range(20):  # 20 seconds, 500 offered requests per second = 10x the cap
        for i in range(500):
            offered += 1
            if cap.allow(t + i / 500):
                per_second[int(t + i / 500)] = per_second.get(int(t + i / 500), 0) + 1
    assert offered == 10000 and cap.accepted <= 50 * 20 + 50, "token bucket: sustained rate x duration plus one bucket"
    assert max(per_second.values()) <= 100  # a window can hold the refill plus a bucket, never an unbounded burst
    toks = [cap.acquire() for _ in range(20)]
    assert sum(t is not None for t in toks) == 5
    assert cap.release(toks[0])
    assert cap.acquire() is not None and cap.acquire() is None


def test_a_boundary_burst_cannot_double_the_rate_and_a_backwards_clock_never_refills():
    cap = guards.RateCap(max_per_s=50, max_connections=1)
    first = sum(cap.allow(0.999) for _ in range(50))
    second = sum(cap.allow(1.000) for _ in range(50))
    assert first == 50 and second <= 1, (
        "50 at t=0.999 then 50 at t=1.000 must not all be accepted (a fixed window would allow 100)"
    )
    back = guards.RateCap(max_per_s=5, max_connections=1)
    assert sum(back.allow(10.0) for _ in range(5)) == 5 and not back.allow(9.0), "a backwards clock refills nothing"
    assert back.allow(10.25) and not back.allow(10.25), (
        "and it must not PENALISE the bucket either: 0.25 s of refill at 5/s is one token"
    )
    cap2 = guards.RateCap(max_per_s=5, max_connections=1)
    assert sum(cap2.allow(100.0) for _ in range(5)) == 5 and not cap2.allow(50.0) and not cap2.allow(99.0)


def test_no_identity_can_change_a_schema_a_permission_a_credential_or_bulk_delete():
    for action in ("schema.change", "permission.change", "credential.change", "bulk_delete"):
        assert action in idn.ACTIONS
        assert not any(idn.authorize(i, action) for i in idn.IDENTITIES), action


def test_egress_allows_only_the_verified_customer_and_blocks_unlisted_links_attachments_and_bank_details():
    p, v = "pat@example.com", "pat@example.com"
    assert guards.egress_check("Hello Pat, your refund request is pending review.", p, v) == []
    assert guards.egress_check("hi", "attacker@example.com", v) == ["RECIPIENT_NOT_VERIFIED_CUSTOMER"]
    assert guards.egress_check("hi", p, None) == ["RECIPIENT_NOT_VERIFIED_CUSTOMER"]
    assert "UNLISTED_LINK" in guards.egress_check("see https://evil.example.net/x", p, v)
    assert (
        guards.egress_check(
            "see https://help.example.com/returns.", p, v, allowed_links=frozenset({"https://help.example.com/returns"})
        )
        == []
    )
    assert "UNLISTED_ADDRESS" in guards.egress_check("write to boss@example.com", p, v)
    assert "UNLISTED_ATTACHMENT" in guards.egress_check("hi", p, v, attachments=("report.pdf",))
    assert "BANK_PATTERN" in guards.egress_check("send it to GB00FAKE00000000000000", p, v)
    assert "BANK_PATTERN" in guards.egress_check("send it to GB82\u200bWEST12345698765432", p, v), (
        "a zero-width character cannot split an account number"
    )
    assert guards.egress_check("hi", "pat+x@example.com", v) == ["RECIPIENT_NOT_VERIFIED_CUSTOMER"], (
        "alias folding never authorises a recipient"
    )
    assert "UNLISTED_LINK" in guards.egress_check("pay at evil.example/pay", p, v), (
        "a bare domain is caught, not only a URL with a scheme"
    )
    assert "UNLISTED_LINK" in guards.egress_check("see ht\u200btps://evil.example/x", p, v), (
        "a zero-width character cannot split a link"
    )
    assert "UNLISTED_LINK" in guards.egress_check("see www.evil.example", p, v)
    assert guards.egress_check("see help.example.com/returns", p, v, allowed_hosts=frozenset({"help.example.com"})) == []


def test_data_stays_in_the_agreed_region():
    assert (
        guards.region_ok("eu-west-x", frozenset({"eu-west-x"}))
        and not guards.region_ok("us-east-x", frozenset({"eu-west-x"}))
        and not guards.region_ok("eu-west-x", frozenset())
    )


def test_egress_folds_ideographic_dots_and_defanged_hosts_and_pins_the_homoglyph_gap():
    p = "pat@example.com"
    for spelled in (
        "pay at evil\u3002example/pay",
        "see evil[.]example",
        "go to evil dot example",
        "visit evil(dot)example/x",
        "evil\uff0eexample",
    ):
        assert "UNLISTED_LINK" in guards.egress_check(spelled, p, p), spelled
    assert guards.egress_check("Thanks. Dot matrix printers are loud.", p, p) == []
    # a Cyrillic look-alike HOST is a Unicode (IDN) host: unlisted, so it is caught (review 10 M3); look-alike letters in prose words are still not folded
    assert guards.egress_check("see еvil.example/pay", p, p) == ["UNLISTED_LINK"]


def test_egress_catches_a_spaced_iban_a_bare_ipv4_and_a_spaced_domain_and_pins_what_it_does_not_cover():
    p = "pat@example.com"
    assert "BANK_PATTERN" in guards.egress_check("pay GB29 NWBK 6016 1331 9268 19 today", p, p)
    assert "BANK_PATTERN" in guards.egress_check("pay gb29-nwbk-6016-1331-9268-19 today", p, p)
    assert "UNLISTED_LINK" in guards.egress_check("send it to 203.0.113.5/pay", p, p)
    assert "UNLISTED_LINK" in guards.egress_check("send it to 203.0.113.5", p, p)
    assert guards.egress_check("send it to 203.0.113.5", p, p, allowed_hosts=frozenset({"203.0.113.5"})) == []
    assert "UNLISTED_LINK" in guards.egress_check("go to evil . example now", p, p)
    # NOT covered (stated in guards.py): pinned so a fix has to change these on purpose
    assert "UNLISTED_LINK" in guards.egress_check("go to evil.  example now", p, p), "two spaces are collapsed first, then joined"
    assert "UNLISTED_LINK" in guards.egress_check("go to evil. example now", p, p), "one space and a lowercase word is"
    assert guards.egress_check("Your order total was 12.50 and the ticket number is 4521. Thanks.", p, p) == []
