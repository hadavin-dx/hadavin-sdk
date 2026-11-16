"""Identity table (least privilege), tenant isolation (tenant isolation), purpose/blast radius (blast radius), segregation (segregation) and typed errors."""

import copy
import inspect
import json

import pytest
from engine_kit import BOOK, CRM, MATRIX, POLICY, STD, Kit, mk_deal
from properties_rng import Mini

from dealdesk import desk as desk_mod
from dealdesk import executor as ex_mod
from dealdesk import gate_rules as g
from dealdesk import guards, identities, lockcheck, purposes, world
from dealdesk.errors import CrossTenantAccess, DealDeskError, Malformed, NotPermitted
from dealdesk.store import AuditChain, TenantStore


# ---------------------------------------------------------------- identities
def test_every_identity_is_denied_every_action_it_does_not_hold():
    n = 0
    for who, held in identities.IDENTITIES.items():
        for action in identities.ACTIONS:
            if action in held:
                identities.authorize(who, action)
            else:
                with pytest.raises(NotPermitted):
                    identities.authorize(who, action)
                n += 1
    assert n > 200
    with pytest.raises(NotPermitted):
        identities.authorize("nobody", "crm.read")
    with pytest.raises(NotPermitted):
        identities.authorize("agent_runtime", "*")
    with pytest.raises(NotPermitted):
        identities.authorize(None, "crm.read")


def test_separation_invariants_and_no_wildcards():
    t = identities.IDENTITIES
    for who, acts in t.items():
        assert all("*" not in a for a in acts) and acts <= set(identities.ACTIONS)
        assert not ({"decision.record", "quote.commit"} <= acts), who  # no identity both approves and executes
        assert not ({"quote.propose", "decision.record"} <= acts) and not ({"quote.draft", "quote.commit"} <= acts), who
        for a in acts:
            assert (who, a) in identities.JUSTIFICATION, (who, a)
    for forbidden in (
        "decision.record",
        "quote.commit",
        "quote.void_commit",
        "quote.draft",
        "killswitch.set",
        "schema.migrate",
        "ledger.write",
        "breakglass.use",
    ):
        assert forbidden not in t["agent_runtime"]
    assert t["breakglass_dormant"] == frozenset()
    assert {"kill_switch_operator", "migrations", "ci_deploy", "breakglass_dormant", "audit_reader", "scheduler"} <= set(t)


def test_every_public_operation_declares_its_required_action():
    missing = []
    for cls in (desk_mod.Desk, ex_mod.Executor, world.ReadOnlyPorts):
        for name, fn in inspect.getmembers(cls, inspect.isfunction):
            if not name.startswith("_") and getattr(fn, "required_action", None) is None:
                missing.append(f"{cls.__name__}.{name}")
    assert missing == []


def test_ports_have_no_write_method_and_each_read_is_identity_checked():
    names = [n for n, _ in inspect.getmembers(world.ReadOnlyPorts, inspect.isfunction) if not n.startswith("_")]
    assert names and not [n for n in names if n.startswith(("put", "set", "update", "delete", "write", "create", "add"))]
    k = Kit(deals=[mk_deal("deal-7001", "acct-7001", "Zephyr Works")])
    for who in ("requester_rep", "approver_commercial", "ci_deploy"):
        with pytest.raises(NotPermitted):
            k.desk.ports.get_deal(who, "deal-7001")
    d = k.desk.ports.get_deal("agent_runtime", "deal-7001")
    d["owner_rep"] = "evil"  # a copy: the world is unchanged
    assert k.world.deals["deal-7001"]["owner_rep"] == "p-ae-01"


# ---------------------------------------------------------------- tenant isolation (tenant isolation)
def _tenant_kit(tenant, canary):
    d = mk_deal("deal-0001", "acct-0001", f"Shared Name {canary}")  # SAME ids and similar names in every tenant
    d["notes"] = canary
    return Kit(tenant=tenant, deals=[d])


def test_colliding_ids_and_names_across_six_tenants_never_cross():
    kits = {f"t-{i}": _tenant_kit(f"t-{i}", f"CANARY{i}ZZ") for i in range(6)}
    qids = {}
    for t, k in kits.items():
        r = k.propose("deal-0001", {"discount_bps": 1500})
        assert r["status"] == "created"
        qids[t] = r["quote_id"]
        k.desk.request_approval("agent_runtime", r["quote_id"])
        k.decide(k.open_approval(r["quote_id"]), "p-sm-01")
        k.desk.draft_quote("draft_writer", r["quote_id"])
    assert len(set(qids.values())) == 6  # quote ids carry the tenant even though deal ids collide
    for t, k in kits.items():
        blob = json.dumps(k.store.all_items(), sort_keys=True)
        for other in kits:
            if other != t:
                assert f"CANARY{other[2:]}ZZ" not in blob, (t, other)
                assert all(f"/{other}/" not in key for key in k.store.all_items())
        for name in k.store.names("quotes"):
            assert name == qids[t]
    a, b = kits["t-0"], kits["t-1"]
    with pytest.raises(CrossTenantAccess):
        a.store.get_raw(b.store.key("quotes", qids["t-1"]))
    with pytest.raises(CrossTenantAccess):
        a.store.get_raw(f"dealdesk/t-0/../t-1/quotes/{qids['t-1']}")


def test_missing_malformed_or_foreign_tenant_fails_closed():
    for bad in (None, "", "T-A", "a/b", "a" * 50, 5, "..", "t a"):
        with pytest.raises(Malformed):
            TenantStore(bad)
    k = Kit(deals=[mk_deal("deal-7001", "acct-7001", "Zephyr Works")])
    with pytest.raises(Malformed):
        k.store.key("quotes", "../x")
    with pytest.raises(Malformed):
        k.store.key("not-a-kind", "x")
    other_world = Kit(tenant="t-b", deals=[mk_deal("deal-7001", "acct-7001", "Zephyr Works")]).world
    with pytest.raises(CrossTenantAccess):
        desk_mod.Desk(other_world, k.store, k.clock, k.keys)
    foreign = mk_deal("deal-9", "acct-9", "Foreign")
    foreign["tenant_id"] = "t-z"
    with pytest.raises(CrossTenantAccess):
        world.World("t-a", {"deal-9": foreign}, BOOK, [], MATRIX, POLICY)


def test_property_many_tenants_random_interleaving_keep_canaries_apart():
    r = Mini(369)
    kits = [_tenant_kit(f"t-{i}", f"CAN{i}Q") for i in range(8)]
    for _ in range(60):
        k = kits[r.n(8)]
        k.propose("deal-0001", {"discount_bps": 1000 + 100 * r.n(5)})
    for i, k in enumerate(kits):
        blob = json.dumps(k.store.all_items())
        assert all(f"CAN{j}Q" not in blob for j in range(8) if j != i)


def test_audit_chain_detects_tampering_and_is_per_tenant():
    k = _tenant_kit("t-a", "C1")
    k.propose("deal-0001", {"discount_bps": 1500})
    assert k.desk.audit.verify()
    ev = k.store.get("audit", "00000000")
    ev["tier"] = "none"
    k.store.put("audit", "00000000", ev)
    assert not k.desk.audit.verify()
    assert AuditChain(TenantStore("t-b")).verify()


# ---------------------------------------------------------------- purpose limitation and blast radius (blast radius)
def test_model_view_contains_only_purposed_fields_and_never_cost_floor_notes_arr_tier():
    deal = copy.deepcopy(CRM[0])
    deal["notes"] = "NOTECANARY"
    deal["arr_minor"] = "7391337"
    deal["customer_tier"] = "tiercanary"
    req = {
        "text": "hello",
        "attachments": [{"name": "a.pdf", "text": "ATTCANARY"}],
        "thread": ["THREADCANARY"],
        "sender": "x@example.com",
    }
    v = purposes.model_view(req, deal, BOOK)
    assert set(v) <= set(purposes.PURPOSE) and all(purposes.PURPOSE[k] for k in v)
    blob = json.dumps(v)
    cogs = str(BOOK["plans"][deal["plan"]][deal["currency"]]["cogs_seat"])
    for banned in (
        "NOTECANARY",
        "THREADCANARY",
        "x@example.com",
        deal["owner_rep"],
        "7391337",
        "floor_bps",
        "cogs",
        f'"{cogs}"',
        "tiercanary",
    ):
        assert banned not in blob, banned


def test_read_log_refuses_unpurposed_fields_and_hashes_refs():
    log = guards.ReadLog()
    log.read("agent_runtime", "crm", ["deal.plan", "deal.seats"], "deal-0001", "propose", 1, "2026-11-09T09:00:00Z")
    assert "deal-0001" not in json.dumps(log.export_for_client())
    with pytest.raises(PermissionError):
        log.read("agent_runtime", "crm", ["deal.cogs_seat"], "x", "p", 1, "t")
    with pytest.raises(PermissionError):
        log.read("agent_runtime", "crm", ["deal.notes"], "x", "p", 1, "t")


def test_rate_cap_token_bucket_connection_cap_and_backwards_clock():
    rc = guards.RateCap(max_per_s=5, max_connections=2)
    assert sum(rc.allow(0.0) for _ in range(20)) == 5
    assert [rc.allow(0.5) for _ in range(3)] == [True, True, False]  # half a second refills 2.5 tokens
    rc2 = guards.RateCap(5, 2)
    assert (
        sum(rc2.allow(0.999) for _ in range(50)) == 5 and sum(rc2.allow(1.0) for _ in range(50)) == 0
    )  # no boundary double burst
    assert rc2.allow(0.0) is False  # a backwards clock never refills
    assert rc.connect() and rc.connect() and not rc.connect()
    rc.disconnect()
    assert rc.connect()


def test_egress_blocks_unlisted_recipient_links_domains_addresses_and_bank_patterns():
    ok = guards.egress_check("Your quote draft is ready for review.", "p-ae-01@example.com", "p-ae-01@example.com")
    assert ok == []
    bad = guards.egress_check("see https://evil.example/pay or pay at evil.example/pay, mail boss@evil.example, IBAN GB82WEST12345698765432",
                              "other@example.com", "p-ae-01@example.com", attachments=("x.exe",))  # fmt: skip
    assert {"RECIPIENT_NOT_REQUESTER", "UNLISTED_LINK", "UNLISTED_ADDRESS", "BANK_PATTERN", "UNLISTED_ATTACHMENT"} <= set(bad)
    assert "UNLISTED_LINK" in guards.egress_check("ht\u200btps://evil.example/x", "a@example.com", "a@example.com")
    assert "UNLISTED_LINK" in guards.egress_check("evil.example/pay", "a@example.com", "a@example.com")


def test_lock_requires_a_dated_boolean_no_training_setting():
    good = {"provider_no_training": {"setting": "zero-retention, no training", "training_use": False, "checked_on": "2026-11-01"}}
    assert lockcheck.live_run_allowed(good, "2026-11-09", 30)[0]
    assert (
        lockcheck.live_run_allowed(good, "2026-12-01", 30)[0] and not lockcheck.live_run_allowed(good, "2026-12-02", 30)[0]
    )  # 30 days inclusive, 31 stale
    assert (
        lockcheck.live_run_allowed(good, "2026-11-01", 30)[0] and not lockcheck.live_run_allowed(good, "2026-10-31", 30)[0]
    )  # same day ok, future not
    cases = [None, {}, {"provider_no_training": None}, {"provider_no_training": {"setting": "x", "checked_on": "9999-99-99", "training_use": False}},
             {"provider_no_training": {"setting": "training ENABLED", "checked_on": "2020-01-01", "training_use": True}},
             {"provider_no_training": {**good["provider_no_training"], "checked_on": "2027-01-01"}},
             {"provider_no_training": {**good["provider_no_training"], "checked_on": "2026-01-01"}},
             {"provider_no_training": {**good["provider_no_training"], "training_use": "false"}},
             {"provider_no_training": {**good["provider_no_training"], "extra": 1}}]  # fmt: skip
    assert not any(lockcheck.live_run_allowed(c, "2026-11-09", 30)[0] for c in cases)
    shipped = json.loads(
        (__import__("pathlib").Path(__file__).resolve().parent.parent / "demo_only/eval/lock.template.json").read_text(
            encoding="utf-8"
        )
    )
    assert not lockcheck.live_run_allowed(shipped, "2026-11-09", 30)[0]


# ---------------------------------------------------------------- typed errors (fuzz): nothing but a verdict or a DealDeskError escapes
JUNK = [None, True, 1.5, -1, 0, 10**30, "", " ", "x" * 300, [], {}, [None], {"a": 1}, chr(0x202E), "../x", ["a", ["b"]]]


def test_fuzz_evaluate_inputs_fail_with_typed_errors_only():
    deal = {"plan": "business", "currency": "USD", "seats": 40, "customer_tier": "mid", "request_type": "new", "arr_minor": "0"}
    n = 0
    for field in list(deal):
        for j in JUNK:
            try:
                g.evaluate({**deal, field: j}, BOOK, MATRIX, {**STD})
            except DealDeskError:
                n += 1
            except KeyError as e:
                pytest.fail(f"raw KeyError for deal.{field}={j!r}: {e}")
    for field in list(STD):
        for j in JUNK:
            try:
                g.evaluate(deal, BOOK, MATRIX, {**STD, field: j})
            except DealDeskError:
                n += 1
    for bad in (None, [], "x", {}, {"plan": "business"}):
        with pytest.raises(DealDeskError):
            g.evaluate(bad, BOOK, MATRIX, STD)
        with pytest.raises(DealDeskError):
            g.evaluate(deal, BOOK, MATRIX, bad)
    assert n > 60


def test_fuzz_engine_entry_points_fail_with_typed_errors_only():
    k = Kit(deals=[mk_deal("deal-7001", "acct-7001", "Zephyr Works")])
    for j in JUNK:
        for call in (lambda j=j: k.desk.propose("agent_runtime", j, "deal-7001", STD, []), lambda j=j: k.desk.propose("agent_runtime", "p-ae-01", j, STD, []),
                     lambda j=j: k.desk.propose("agent_runtime", "p-ae-01", "deal-7001", j, []), lambda j=j: k.desk.propose("agent_runtime", "p-ae-01", "deal-7001", STD, j),
                     lambda j=j: k.desk.status("agent_runtime", j), lambda j=j: k.desk.request_approval("agent_runtime", j),
                     lambda j=j: k.desk.draft_quote("draft_writer", j), lambda j=j: k.ex.commit("commit_executor", j),
                     lambda j=j: k.ex.void_commit("commit_executor", j, "x"), lambda j=j: k.desk.edit_quote("agent_runtime", j, terms=STD)):  # fmt: skip
            try:
                call()
            except DealDeskError:
                pass
            except Exception as e:  # noqa: BLE001
                pytest.fail(f"{type(e).__name__} escaped for {j!r}: {e}")
        assert k.desk.record_decision("approver_commercial", j, "p-sm-01") == {"status": "decision_not_accepted"}
    a_q = k.propose("deal-7001", {"discount_bps": 1500})["quote_id"]
    k.desk.request_approval("agent_runtime", a_q)
    good = k.signed(k.open_approval(a_q), "p-sm-01")
    for field in good:  # every signed field (ts and kid included) is bound by the signature: any junk value is refused
        for j in JUNK:
            if j == good[field]:
                continue
            assert k.desk.record_decision("approver_commercial", {**good, field: j}, "p-sm-01") == {
                "status": "decision_not_accepted"
            }, (
                field,
                j,
            )


def test_every_port_read_is_logged_with_who_what_why_rows_and_never_carries_notes():
    deal = mk_deal("deal-7001", "acct-7001", "Zephyr Works")
    deal["notes"] = "NOTECANARY"
    k = Kit(deals=[deal])
    q = k.propose("deal-7001", {"discount_bps": 1500})["quote_id"]
    k.desk.request_approval("agent_runtime", q)
    k.decide(k.open_approval(q), "p-sm-01")
    log = k.desk.ports.log.export_for_client()
    assert {e["port"] for e in log} == {"crm", "billing", "identity"} and all(
        e["who"] in ("agent_runtime", "decision_service") and e["why"] and e["rows"] >= 1 and e["at"] for e in log
    )
    blob = json.dumps(log)
    assert "NOTECANARY" not in blob and "deal.notes" not in blob and "deal-7001" not in blob  # refs are hashed
    assert all(f in purposes.PURPOSE or f in purposes.CODE_PURPOSE for e in log for f in e["fields"])
    assert "notes" not in k.desk.ports.get_deal("agent_runtime", "deal-7001")
    assert any(e["port"] == "crm" and "deal.owner_rep" in e["fields"] for e in log)
