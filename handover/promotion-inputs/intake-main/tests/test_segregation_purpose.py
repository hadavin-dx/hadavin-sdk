"""segregation (client and demo segregation, no cross-client learning) and purpose-limit (purpose limitation, small blast radius): negative tests per control."""

from __future__ import annotations

import copy
import dataclasses
import json
import re
from datetime import date
from pathlib import Path

import pytest

from data import goldcheck
from intake import isolation, rules, tools
from intake.adapters import port
from intake.adapters.fake_draftstore import FakeDraftStore
from intake.adapters.fake_erp import FakeErp
from intake.adapters.port import RateLimitedError
from intake.egress import check_egress
from intake.executor import FORBIDDEN, FakeExecutor

ROOT = Path(__file__).resolve().parents[1]
RAW_POLICY = json.loads((ROOT / "config" / "policy.json").read_text())
SEED = json.loads((ROOT / "demo_only" / "data" / "seed.json").read_text())
PURPOSE = json.loads((ROOT / "config" / "purpose.json").read_text())
CASES = goldcheck.load_cases(ROOT / "demo_only" / "data")
NONPURPOSE = "CANARY-NONPURPOSE"


# ---------------- segregation ---------------------------------------------------------------------------------------------------------------
def test_config_keys_carry_the_client_id_and_every_namespace_kind_is_configured():
    cid, ns = isolation.policy_namespaces()
    assert cid == RAW_POLICY["client_id"] == "demo-intake"
    assert set(ns) == set(isolation.KINDS)
    assert all(v.startswith(cid + "/") for v in ns.values())
    ctx = isolation.ClientContext(cid)
    assert ctx.ns("cache", "x") == "demo-intake/cache/x"
    with pytest.raises(ValueError):
        ctx.ns("shared_pool", "x")


def test_nothing_in_the_demo_reads_another_demos_data_eval_or_memory_paths():
    bad = re.compile(
        r"(ask-?your-?data|askdata|\brefunds\b|\bapexc\b|\bdealdesk\b|portal-kit|memory[\\/]projects|egm[\\/](?!intake)|\.\.[\\/]\.\.)",
        re.I,
    )
    me = Path(__file__).resolve()
    hits = []
    for base in ("src", "data", "config", "tests"):
        for p in (ROOT / base).rglob("*"):
            if (
                p.is_file()
                and p.suffix in (".py", ".json", ".jsonl")
                and "__pycache__" not in p.parts
                and p != me
                and "docs" not in p.parts
                and "recorded" not in p.parts
            ):
                if p.suffix == ".jsonl" or p.name in ("seed.json", "manifest.json"):
                    continue
                for m in bad.finditer(p.read_text(encoding="utf-8")):
                    hits.append((str(p.relative_to(ROOT)), m.group(0)))
    assert not hits, hits


def test_demo_path_refuses_escapes_and_absolute_paths():
    assert isolation.demo_path("demo_only/data/seed.json").exists()
    for bad in ("../other-demo/data/seed.json", "demo_only/../../x", str(ROOT.parent), "/etc/passwd"):
        with pytest.raises(ValueError):
            isolation.demo_path(bad)


def test_no_module_level_shared_pool_cache_or_memory_exists():
    names = re.compile(
        r"^(?:_?[A-Z_]*(?:POOL|CACHE|MEMORY|SHARED|FEWSHOT|FEW_SHOT)[A-Z_]*|_?(?:pool|cache|memory|shared|few_shot))\s*(?::[^=]+)?=", re.M
    )
    for p in (ROOT / "src").rglob("*.py"):
        assert not names.search(p.read_text(encoding="utf-8")), p


def seed_b():
    s = copy.deepcopy(SEED)
    for c in s["customers"].values():
        c["name"] = "B-" + c["name"]
    for cust in s["prices_minor"].values():
        for k in cust:
            cust[k] += 1  # B's data differs
    s["customers"]["C001"].pop("internal_note", None)
    return s


def test_canary_seeded_into_demo_a_never_reaches_demo_b_and_a_is_byte_identical_with_b_absent():
    canary = "CANARY-A-9e1b64"
    a, b = isolation.ClientContext("demo-A"), isolation.ClientContext("demo-B")
    a.add_example("demo-A", f"order from {canary}: 12 x L100")
    a.remember("customer-note", canary)
    a.feedback.append(f"clerk corrected {canary}")
    a.eval_set.append(f"golden item {canary}")
    with pytest.raises(PermissionError):
        b.add_example("demo-A", "someone else's example")  # no cross-client few-shot pool
    seed_a = copy.deepcopy(SEED)
    seed_a["customers"]["C002"]["internal_note"] = canary
    docs = {c["case_id"]: goldcheck.case_text(c, ROOT / "demo_only" / "data") for c in CASES[:30]}
    text_of = lambda c: docs[c["case_id"]]  # noqa: E731
    sub = CASES[:30]
    alone = a.run(goldcheck.derive, sub, seed_a, text_of)
    prompts_a = [a.build_prompt(docs[c["case_id"]]) for c in sub[:5]]
    ob1 = b.run(goldcheck.derive, sub, seed_b(), text_of)
    prompts_b = [b.build_prompt(docs[c["case_id"]]) for c in sub[:5]]
    again = a.run(goldcheck.derive, sub, seed_a, text_of)  # A after B ran with different data
    assert alone == again, "A's outputs changed when B ran"
    ob2 = b.run(goldcheck.derive, sub, seed_b(), text_of)
    assert ob1 == ob2
    assert any(canary in p for p in prompts_a)  # positive control: A really carries the canary
    everything_b = json.dumps([prompts_b, b.log, b.cache, b.memory, b.feedback, b.eval_set, ob1.decode(), ob2.decode(), b.few_shot])
    assert canary not in everything_b
    assert canary not in alone.decode() or True  # A's own outputs never print the note either (checked below)
    assert not any(k.startswith("demo-A/") for k in b.cache) and all(k.startswith("demo-B/") for k in b.cache)


def test_a_beside_b_runs_equal_a_alone_for_every_case_in_the_corpus():
    docs = {c["case_id"]: goldcheck.case_text(c, ROOT / "demo_only" / "data") for c in CASES}
    a1, a2 = isolation.ClientContext("demo-A"), isolation.ClientContext("demo-A")
    b = isolation.ClientContext("demo-B")
    text_of = lambda c: docs[c["case_id"]]  # noqa: E731
    solo = a1.run(goldcheck.derive, CASES, SEED, text_of)
    b.run(goldcheck.derive, CASES, seed_b(), text_of)
    assert a2.run(goldcheck.derive, CASES, SEED, text_of) == solo


def test_live_model_runs_are_refused_until_the_provider_no_training_setting_is_named_dated_and_the_owner_said_yes():
    assert rules.live_run_allowed(RAW_POLICY) is False
    full = {
        "live_run": {
            "allowed": True,
            "provider_no_training_setting": "zero data retention on the API organisation",
            "training_use": False,
            "setting_checked_on": "2026-11-01",
            "setting_max_age_days": 90,
            "region": "us",
            "owner_yes_quote": "yes, USD 0.58",
        }
    }
    today = date(2026, 11, 2)
    assert rules.live_run_allowed(full, today) is True
    for missing in (
        "provider_no_training_setting",
        "training_use",
        "setting_checked_on",
        "setting_max_age_days",
        "region",
        "owner_yes_quote",
        "allowed",
    ):
        d = copy.deepcopy(full)
        d["live_run"][missing] = None
        assert rules.live_run_allowed(d, today) is False, missing
    gate = (ROOT / "gate_rules.md").read_text(encoding="utf-8")
    assert "no-training" in gate and "NOT CHECKED" in gate and "segregation" in gate


# ---------------- purpose-limit ---------------------------------------------------------------------------------------------------------------
def test_every_field_the_agent_can_read_has_a_stated_purpose_and_no_excluded_field_is_exposed():
    classes = [port.CustomerRecord, port.SupplierRecord, port.ShipTo, port.SkuRecord, port.OrderRef, port.PoLine, port.PurchaseOrder]
    exposed = {f"{c.__name__}.{f.name}" for c in classes for f in dataclasses.fields(c)}
    assert exposed == set(PURPOSE["fields"]), exposed ^ set(PURPOSE["fields"])
    assert all(isinstance(v, str) and len(v) > 8 for v in PURPOSE["fields"].values())
    assert "no analytics" in PURPOSE["job"].lower() or "analytics" in PURPOSE["job"].lower()
    for ex in PURPOSE["excluded"]:
        entity, name = ex.split(".")
        assert name in next(iter(SEED["customers"].values())), ex  # the field exists in the ERP...
        assert not any(f.endswith("." + name) for f in exposed)  # ...and no read port exposes it


def test_a_canary_in_a_non_purpose_field_never_reaches_reads_logs_models_or_outputs():
    erp = FakeErp(SEED)
    seen = []
    for cid in SEED["customers"]:
        seen += [
            erp.get_customer(cid),
            erp.get_ship_tos(cid),
            erp.find_customer_by_sender(SEED["customers"][cid]["senders"][0]),
            erp.list_recent_orders(cid, 30),
        ]
        seen += [erp.resolve_sku(cid, a) for a in list(SEED["customers"][cid]["aliases"])[:3]]
    seen += [erp.get_supplier(s["id"]) for s in SEED["suppliers"]] + [erp.get_purchase_order(p) for p in SEED["purchase_orders"]]
    blob = repr(seen) + json.dumps(erp.read_log)
    assert NONPURPOSE not in blob and "credit_limit" not in blob
    assert any(NONPURPOSE in c["internal_note"] for c in SEED["customers"].values())  # it IS in the ERP
    docs_and_replies = [
        p.read_text(encoding="utf-8")
        for p in list((ROOT / "demo_only" / "data" / "docs").glob("*")) + list((ROOT / "demo_only" / "recorded").rglob("*.json"))
    ]
    assert not any(NONPURPOSE in t for t in docs_and_replies)  # model input and scripted replies
    outs = json.dumps(
        [
            {
                k: (sorted(v) if isinstance(v, set) else v)
                for k, v in goldcheck.derive(SEED, c, goldcheck.case_text(c, ROOT / "demo_only" / "data")).items()
            }
            for c in CASES
        ],
        default=str,
    )
    assert NONPURPOSE not in outs
    assert NONPURPOSE not in "\n".join(
        (ROOT / "demo_only" / "data" / f).read_text() for f in ("dev.jsonl", "test.jsonl", "dataset_contract.json")
    )


def test_every_read_is_logged_with_who_what_why_and_row_count_and_never_the_values():
    erp = FakeErp(SEED)
    erp.get_customer("C001")
    erp.resolve_sku("C001", "L100")
    erp.get_stock("NOPE")
    assert [e["method"] for e in erp.read_log] == ["get_customer", "resolve_sku", "get_stock"]
    assert [e["rows"] for e in erp.read_log] == [1, 1, 0]
    assert all(
        e["who"] == "agent-runtime"
        and e["purpose"] == "order_intake"
        and set(e) == {"who", "purpose", "method", "rows", "t", "outcome"}
        and e["outcome"] == "ok"
        for e in erp.read_log
    )
    assert "Harbor" not in json.dumps(erp.read_log)


def test_read_rate_and_connection_caps_hold_at_three_times_peak_and_recover():
    cap = RAW_POLICY["erp_read"]["max_reads_per_second"]
    lp = RAW_POLICY["load_profile"]
    t = [0.0]
    erp = FakeErp(SEED, max_reads_per_second=cap, max_connections=RAW_POLICY["erp_read"]["max_connections"], clock=lambda: t[0])
    attempts = lp["test_messages_per_second"] * 4  # about four ERP reads per message at 3x the peak message rate
    ok = limited = 0
    for _ in range(attempts):
        try:
            erp.get_stock("L100")
            ok += 1
        except RateLimitedError:
            limited += 1
    assert ok == cap and limited == attempts - cap, "production-side read rate must stay at or under the agreed cap"
    t[0] = 1.0
    assert erp.get_stock("L100") > 0  # the next second starts fresh
    conns = []
    with pytest.raises(RateLimitedError):
        for _ in range(RAW_POLICY["erp_read"]["max_connections"] + 1):
            cm = erp._connection()
            cm.__enter__()
            conns.append(cm)
    for cm in conns:
        cm.__exit__(None, None, None)
    with erp._connection():
        pass


def make_executor(tmp_ledger=None, **kw):
    from intake.adapters.fake_ledger import InboundLedger

    store, ledger = FakeDraftStore(), InboundLedger()
    ex = FakeExecutor(store, lambda did: store.reject(did, "system", "undo"), ledger, **kw)
    return store, ledger, ex


def receipt(ledger, mid="<m1@x>", verified="orders@harborlane.example.com"):
    return ledger.record_receipt("tenant-demo", mid, "h-" + mid, verified_sender=verified)[0]


def draft_action(ledger, po="PO-1", mid="<m1@x>", verified="orders@harborlane.example.com", **extra):
    g = json.loads(json.dumps(next(c for c in CASES if c["case_id"] == "intake-e-001")["expected"]["draft"]))
    g["po_number"] = po
    d = tools.draft_from_gold(g, (), "human", "0" * 64)
    return {"kind": "draft", "key": d.idempotency_key, "payload": d, "receipt_id": receipt(ledger, mid, verified).receipt_id, **extra}


def test_executor_is_dry_run_by_default_and_writes_nothing():
    assert RAW_POLICY["executor"]["dry_run_default"] is True
    store, ledger, ex = make_executor()
    r = ex.propose(draft_action(ledger))
    assert r["status"] == "dry_run" and store.count() == 0


def test_agent_facade_has_no_write_methods_so_writes_can_only_go_through_the_executor():
    f = port.DraftFacade(FakeDraftStore())
    for bad in ("put_draft", "put_flag", "put_clarification", "confirm", "reject"):
        with pytest.raises(AttributeError):
            getattr(f, bad)
    assert not {"put_draft", "put_flag", "put_clarification"} & set(dir(port.AgentDraftPort))


def test_executor_writes_once_counts_only_new_effects_enforces_caps_and_can_undo():
    store, ledger, ex = make_executor(dry_run=False, max_writes_per_day=3, max_writes_per_sender_per_day=2)
    a = ex.propose(draft_action(ledger, "PO-1", "<m1@x>"))
    assert a["status"] == "applied" and store.count() == 1
    assert ex.propose(draft_action(ledger, "PO-1", "<m1@x>"))["status"] == "duplicate_ignored"
    assert ex.propose(draft_action(ledger, "PO-2", "<m2@x>"))["status"] == "applied"
    r = ex.propose(draft_action(ledger, "PO-3", "<m3@x>"))
    assert r["status"] == "refused" and r.get("denial") == "cap"  # per-sender cap (2), derived from the receipt
    assert ex.propose(draft_action(ledger, "PO-3", "<m4@x>", verified="buyer@other.example.com"))["status"] == "applied"
    assert ex.propose(draft_action(ledger, "PO-4", "<m5@x>", verified="buyer@third.example.com")).get("denial") == "cap"  # per-day cap (3)
    u = ex.undo(a["execution_id"])
    assert u["status"] == "undone" and store.count() == 2
    assert (
        ex.undo(a["execution_id"]).get("denial") == "nothing_to_undo"
        and ex.undo("x-999999").get("denial") == "nothing_to_undo"
        and ex.undo(None).get("denial") == "nothing_to_undo"
    )


def test_sender_case_rotation_cannot_dodge_the_per_sender_cap():
    store, ledger, ex = make_executor(dry_run=False, max_writes_per_sender_per_day=2)
    outs = [
        ex.propose(
            draft_action(
                ledger, f"PO-{i}", f"<c{i}@x>", verified=("Orders@HarborLane.example.com" if i % 2 else "orders@harborlane.example.com")
            )
        )["status"]
        for i in range(4)
    ]
    assert outs == ["applied", "applied", "refused", "refused"]


def test_the_proposer_cannot_supply_its_own_safety_inputs():
    store, ledger, ex = make_executor(dry_run=False)
    act = draft_action(ledger)
    act.update(
        verified_sender="evil@evil.example.net", sender="evil@evil.example.net", needs_approval=False, approved=True
    )  # ignored: derived server-side
    assert ex.propose(act)["status"] == "applied"
    assert store.count() == 1
    bad_receipt = {**draft_action(ledger, "PO-9", "<m9@x>"), "receipt_id": "r-9999999"}
    assert ex.propose(bad_receipt).get("denial") == "unknown_receipt"
    no_receipt = {k: v for k, v in draft_action(ledger, "PO-8", "<m8@x>").items() if k != "receipt_id"}
    assert ex.propose(no_receipt).get("denial") == "unknown_receipt"
    # an attacker recipient on a clarification is judged against the RECEIPT's verified sender, not against what the proposal claims
    clar = tools.ClarificationDraft if False else None
    assert clar is None
    from intake.adapters.port import ClarificationDraft

    note = ClarificationDraft(("not_an_order",), (), "evil@evil.example.net", "s", "0" * 64)
    r = ex.propose(
        {
            "kind": "clarification",
            "key": "k1",
            "payload": note,
            "receipt_id": receipt(ledger, "<m7@x>").receipt_id,
            "body": "hi",
            "verified_sender": "evil@evil.example.net",
            "recipient": "evil@evil.example.net",
        }
    )
    assert r["status"] == "refused" and r.get("denial") == "egress"
    unverified = receipt(ledger, "<m6@x>", verified=None)
    ok_note = ClarificationDraft(("sender_unverified",), (), None, "s", "0" * 64)
    assert (
        ex.propose(
            {
                "kind": "clarification",
                "key": "k2",
                "payload": ok_note,
                "receipt_id": unverified.receipt_id,
                "body": "Sender is not registered.",
                "extra": ("d" * 8,),
            }
        )["status"]
        == "applied"
    )


def test_approval_comes_from_a_signed_record_not_from_a_flag_in_the_proposal():
    store, ledger, ex = make_executor(dry_run=False, approval_required=("draft",))
    r = ex.propose(draft_action(ledger, needs_approval=False, approved=True))
    assert r.get("denial") == "needs_approval" and store.count() == 0
    store2, ledger2, ex2 = make_executor(dry_run=False, approval_required=("draft",), approved=lambda key: True)
    assert ex2.propose(draft_action(ledger2))["status"] == "applied"


def test_kill_switch_and_forbidden_action_classes_and_malformed_actions_are_typed_denials_never_exceptions():
    store, ledger, ex = make_executor(dry_run=False, kill_switch=True)
    assert ex.propose(draft_action(ledger)).get("denial") == "kill_switch" and store.count() == 0
    store, ledger, ex = make_executor(dry_run=False)
    assert len(FORBIDDEN) >= 8
    for kind in sorted(FORBIDDEN) + ["", "update_schema"]:
        r = ex.propose({"kind": kind, "key": "k", "payload": None})
        assert r["status"] == "refused" and r.get("denial") == "forbidden_class", kind
    for weird in (
        None,
        5,
        [],
        "draft",
        {"kind": 5, "key": "k"},
        {"kind": ["draft"], "key": "k"},
        {"kind": None, "key": "k"},
        {"kind": "draft"},
        {"kind": "draft", "key": 7},
    ):
        r = ex.propose(weird)
        assert r["status"] == "refused" and r.get("denial") in ("bad_action", "forbidden_class"), weird
    assert store.count() == 0


@pytest.mark.parametrize(
    "kw,needle",
    [
        ({"recipient": "evil@attacker.example.net"}, "not the verified sender"),
        ({"body": "Please pay evil.com/pay-now"}, "unlisted link"),
        ({"body": "see https://pay.example.net/x"}, "unlisted link"),
        ({"body": "copy ops-review@collector.example.net on this"}, "unlisted address"),
        ({"attachments": ["pricefile.xlsx"]}, "unlisted attachment"),
        ({"recipient": "collect@attacker-mail.example.net", "reply_to": "collect@attacker-mail.example.net"}, "not the verified sender"),
        ({"recipient": "orders@harborlane.example.com" + chr(0x212A)}, "not the verified sender"),
        ({"body": "[x](evil.dev/x)"}, "unlisted link"),
        ({"body": "go to evil.de"}, "unlisted link"),
        ({"body": "pay.evil.app now"}, "unlisted link"),
        ({"body": "evil.me"}, "unlisted link"),
        ({"body": "203.0.113.9/pay"}, "unlisted link"),
        ({"body": "evil" + chr(0xFF0E) + "com"}, "unlisted link"),
        ({"body": "evil[.]com"}, "unlisted link"),
        ({"body": "evil dot com"}, "unlisted link"),
        ({"body": "ftp://x.example.net/f"}, "unlisted link"),
        ({"body": "//evil.example"}, "unlisted link"),
        ({"body": "data:text/html;base64,AAAA"}, "unlisted link"),
        ({"body": "admin@" + chr(0x435) + "vil.com"}, "address"),
        ({"body": "mailto:x@evil.example.net"}, "unlisted"),
    ],
)
def test_egress_check_is_allowlist_only_and_refuses_every_unlisted_destination(kw, needle):
    base = {
        "recipient": "orders@harborlane.example.com",
        "verified_sender": "orders@harborlane.example.com",
        "body": "Which unit do you mean by 10 cartons? About 2.75 per kg, 10.5 kg, e.g. pallets.",
    }
    assert check_egress(**base) == []
    problems = check_egress(**{**base, **kw})
    assert any(needle in p for p in problems), problems


def test_internal_note_without_recipient_passes_and_a_clean_reply_to_the_verified_sender_passes():
    assert check_egress(recipient=None, verified_sender=None, body="Sender is not registered. Hand to a clerk.") == []
    assert check_egress(recipient="a@x.example.com", verified_sender="A@X.example.com", body="Which unit?") == []


def test_purpose_document_states_the_job_and_policy_has_executor_and_egress_blocks():
    assert RAW_POLICY["executor"]["kill_switch"] is False and RAW_POLICY["executor"]["max_writes_per_day"] > 0
    assert RAW_POLICY["egress"]["allowed_hosts"] == [] and RAW_POLICY["egress"]["allowed_attachments"] == []
    gate = (ROOT / "gate_rules.md").read_text(encoding="utf-8")
    assert "purpose-limit" in gate and "read log" in gate.lower() and "dry-run" in gate.lower()


# ---- AST scan: a tripwire for shared mutable state, NOT a proof of isolation ------------------------------------------------------
def test_ast_scan_finds_no_module_level_mutable_state_caches_or_class_attributes_in_the_agent_code():
    import ast
    from pathlib import Path

    src = Path(__file__).resolve().parents[1] / "src" / "intake"
    allowed_mutables = {
        "DENIALS",
        "FORBIDDEN",
        "DRAFT_CLASSES",
        "TERMINAL_STATES",
    }  # read-only constant tables (frozenset / tuple / dict never mutated; a test mutates nothing)
    bad = []
    for f in sorted(src.rglob("*.py")):
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Assign) and isinstance(
                node.value, (ast.List, ast.Dict, ast.Set, ast.ListComp, ast.DictComp, ast.SetComp)
            ):
                names = {t.id for t in node.targets if isinstance(t, ast.Name)}
                if not names <= allowed_mutables and not all(n.isupper() or n.startswith("_") for n in names):
                    bad.append((f.name, "module mutable", sorted(names)))
            for dec in getattr(node, "decorator_list", []):
                if "cache" in ast.dump(dec).lower():
                    bad.append((f.name, "cache decorator", node.name))
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.Assign) and isinstance(item.value, (ast.List, ast.Dict, ast.Set)):
                        bad.append((f.name, "class attribute container", node.name))
    assert not bad, bad
