"""Review round 5: src/ checks against the oracle (differential), bank bypass families, rows after TOTAL, total functions (fuzz), CRLF/BOM, false hand-back rate, order X27,
stats wording, doc facts generated from code."""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import pytest

from data import gen, goldcheck
from intake import checks, cpbounds
from intake.adapters.fake_draftstore import FakeDraftStore
from intake.adapters.fake_erp import FakeErp
from intake.adapters.fake_ledger import InboundLedger
from intake.egress import check_egress
from intake.rules import load_policy, norm_invoice_no

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "demo_only" / "data"
SEED = json.loads((DATA / "seed.json").read_text())
CASES = goldcheck.load_cases(DATA)
BY_ID = {c["case_id"]: c for c in CASES}
SUP = {s["id"]: s for s in SEED["suppliers"]}
INVOICES = [c for c in CASES if c["kind"] == "supplier_invoice"]
ORDERS = [c for c in CASES if c["kind"] == "order"]
POL = load_policy()
DOCS_MD = {p.name: p.read_text(encoding="utf-8") for p in ROOT.glob("*.md")} | {
    "demo_script.md": (ROOT / "demo_only" / "demo_script.md").read_text(encoding="utf-8")
}


def on_file(c) -> str:
    po = SEED["purchase_orders"].get(c["facts"]["po_ref"])
    return SUP[po["supplier"] if po else "S01"]["bank"]


def inv_text(sid="S01", pos=0):
    c = next(
        x
        for x in INVOICES
        if x["expected"]["verdict"] == "matched"
        and SEED["purchase_orders"][x["facts"]["po_ref"]]["supplier"] == sid
        and "ABN" not in goldcheck.case_text(x)
    )
    return c, goldcheck.case_text(c)


# ---- differential: src/ against the oracle ------------------------------------------------------------------------------------------
def test_src_and_oracle_agree_on_structure_and_bank_for_every_invoice_in_the_gold_set():
    for c in INVOICES:
        text = goldcheck.case_text(c)
        s, o = checks.parse_invoice(text), goldcheck.parse_invoice_strict(text)
        assert s.ok == o["ok"], c["case_id"]
        if s.ok:
            assert s.rows == o["rows"], c["case_id"]
            for sid in SUP:  # against every supplier's account, so both the clean and the dirty direction are exercised
                assert checks.bank_clean(SUP[sid]["bank"], text) == goldcheck.bank_clean(SUP[sid]["bank"], text), (c["case_id"], sid)


def test_src_checks_reproduce_the_gold_d10_and_x27_labels_without_the_oracle():
    for c in INVOICES:
        text = goldcheck.case_text(c)
        e = set(c["expected"]["exceptions"])
        p = checks.parse_invoice(text)
        if e & {"X12", "X26", "X28", "D11"}:
            continue  # decided before the structure
        if "X27" in e:
            assert not p.ok, c["case_id"]
        elif p.ok and "D04" not in e:
            kw = any(re.search(k, text.lower()) for k in goldcheck.BANK["keyword_patterns"])
            d10 = (not checks.bank_clean(on_file(c), text)) or kw
            assert d10 == ("D10" in e), c["case_id"]
            if "D06" not in e:
                assert all(a == q * cst for _, q, cst, a in p.rows), c["case_id"]


def test_src_sku_and_unit_checks_agree_with_the_oracle_on_every_parsed_email_line():
    erp = FakeErp(SEED)
    n = 0
    for c in ORDERS:
        if c["source"]["format"] != "email":
            continue
        cust = goldcheck.registered(SEED, c["input"]["sender"])
        if cust is None:
            continue
        text = goldcheck.case_text(c)
        items, bad = checks.parse_email_items(text)
        o = goldcheck.parse_order(text, "email")
        assert [(i["ref"], i["qty"], i["unit"]) for i in items] == [(x["ref"], x["qty"], x["unit"]) for x in o["lines"]], c["case_id"]
        assert bool(bad) == bool(o["unparsed"]), c["case_id"]
        for it in items:
            skus = checks.check_sku(erp, cust["id"], it["ref"])
            assert skus == goldcheck.resolve_skus(SEED, cust, it["ref"]), c["case_id"]
            if len(skus) == 1:
                n += 1
                try:
                    qb, fac = checks.convert_units(erp, cust["id"], skus[0], it["qty"], it["unit"])
                    ok = True
                except checks.LineError:
                    ok = False
                uname, ofac = goldcheck.unit_name_factor(SEED, cust, skus[0], it["unit"])
                oracle_ok = (
                    goldcheck.QTY_OK.fullmatch(it["qty"]) is not None
                    and ofac is not None
                    and not (
                        "," in it["qty"]
                        and (uname == "kg" or SEED["skus"][skus[0]]["base_uom"] == "kg" and uname == SEED["skus"][skus[0]]["base_uom"])
                    )
                    and int(it["qty"].replace(",", "")) * ofac <= POL.max_qty_base
                )  # noqa: E501
                assert ok == oracle_ok, (c["case_id"], it)
                if ok:
                    assert (qb, fac) == (int(it["qty"].replace(",", "")) * ofac, ofac)
    assert n > 100


# ---- B1: bank-detail bypass families ---------------------------------------------------------------------------------------------------
FAMILIES = [
    "Acct 87654321.00", "Ref 87,654,321.00", "Acct " + "".join(chr(0x660 + int(d)) for d in "87654321"), "Acct " + "".join(chr(0x966 + int(d)) for d in "87654321"),
    "Acct 8765.4321", "Pay to 87.65.43.21", "Acct 8765/4321", "Acct 8765\t4321", "Acct 8765  4321", "Acct 8765\n4321", "ref 8765432", "Acct %38%37%36%35%34%33%32%31",
    "QWNjdCA4NzY1NDMyMQ==", "Please remit via pay@evil.example.net", "Pay online at https://pay.evil.example.net/inv", "Send to bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq",
    "Cheques payable to the PO Box below", "Our ref 20261102", "pay at evil.example.net/x", "Acct 8765_4321", "Acct 8765-4321", "Acct 8765 . 4321",
]  # fmt: skip


@pytest.mark.parametrize("extra", FAMILIES)
def test_every_bank_bypass_family_is_d10_in_src_and_oracle_even_with_the_real_account_present(extra):
    _, text = inv_text("S01")
    dirty = text.replace("Item   Qty", extra + "\nItem   Qty", 1)
    on = SUP["S01"]["bank"]
    kw = any(re.search(k, dirty.lower()) for k in goldcheck.BANK["keyword_patterns"])
    assert checks.bank_clean(on, text) and goldcheck.bank_clean(on, text)  # the clean original passes
    assert (not checks.bank_clean(on, dirty)) or kw
    assert (not goldcheck.bank_clean(on, dirty)) or kw


def test_benign_forms_stay_clean_so_the_check_is_not_a_blanket_hand_back():
    _, text = inv_text("S01")
    on = SUP["S01"]["bank"]
    for ok in (
        "ABN 51 824 753 556",
        "Tel +61 2 9999 8888",
        "Fax: +44 (0) 20 7946 0958",
        "Our ref 20261",
        "Delivery note GRN 4471",
        "VAT: GB123456789012",
        "Date: 2026-11-02",
    ):
        dirty = text.replace("Item   Qty", ok + "\nItem   Qty", 1)
        assert checks.bank_clean(on, dirty) and goldcheck.bank_clean(on, dirty), ok
    assert checks.bank_clean(on, text.replace(on, on.lower())) and checks.bank_clean(
        on, text.replace(on, " ".join(on[i : i + 4] for i in range(0, len(on), 4)))
    )


def test_gold_has_every_bypass_family_and_both_splits_have_each_main_family():
    texts = {c["case_id"]: goldcheck.case_text(c) for c in INVOICES if "D10" in c["expected"]["exceptions"]}
    for needle in (
        "Acct 87654321.00",
        "Ref 87,654,321.00",
        chr(0x668),
        chr(0x96E),
        "Acct 8765.4321",
        "87.65.43.21",
        "Acct 8765/4321",
        "Acct 8765\t4321",
        "Acct 8765  4321",
        "Acct 8765\n4321",
        "ref 8765432",
        "QWNjdCA4NzY1NDMyMQ==",
        "pay@evil.example.net",
        "https://pay.evil",
        "bc1q",
        "Cheques payable",
    ):
        hits = [i for i, t in texts.items() if needle in t]
        assert hits, needle
    for needle in ("Acct 87654321.00", "ref 8765432", "pay@evil.example.net"):
        assert {BY_ID[i]["split"] for i, t in texts.items() if needle in t} == {"dev", "test"}, needle


# ---- B2 rows after TOTAL ------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "tail",
    [
        "M400   9999   0.64   6393.36",
        "Item   Qty   Unit cost   Amount",
        "M400\t5\t0.64\t3.20",
        "M400 | 5 | 0.64 | 3.20",
        "M400,5,0.64,3.20",
        "TOTAL USD 1.00",
    ],
)
def test_anything_row_shaped_after_total_is_x27_in_src_and_oracle(tail):
    c, text = inv_text("S02")
    bad = text.rstrip("\n") + "\n" + tail + "\n"
    assert not checks.parse_invoice(bad).ok and not goldcheck.parse_invoice_strict(bad)["ok"]
    assert goldcheck.derive_invoice(SEED, c, bad)["exc"] == {"X27"}
    assert checks.parse_invoice(text).ok


def test_free_text_footer_after_total_is_allowed_but_goes_through_the_bank_and_screen_checks():
    c, text = inv_text("S02")
    ok = text.rstrip("\n") + "\nThank you for your business.\n"
    assert checks.parse_invoice(ok).ok and goldcheck.derive_invoice(SEED, c, ok)["exc"] == set()
    assert goldcheck.derive_invoice(SEED, c, text.rstrip("\n") + "\nPlease pay evil.example.net/x\n")["exc"] == {"D10"}


# ---- M1 total functions ----------------------------------------------------------------------------------------------------------------------
def test_malformed_invoices_are_hand_backs_never_crashes():
    c, text = inv_text("S01")
    for bad in (
        text.replace("INVOICE ", "INVOCE ", 1),
        chr(0xFEFF) + text.replace("INVOICE ", "XINVOICE ", 1),
        re.sub(r"INVOICE (\S+)", lambda m: "INVOICE " + m.group(1)[:-4] + "".join(chr(0xFF10 + int(d)) for d in "9100"), text, count=1),
        "",
        "\x00",
        "INVOICE",
        "TOTAL",
    ):
        assert goldcheck.derive_invoice(SEED, c, bad)["exc"] == {"X27"} or goldcheck.derive_invoice(SEED, c, bad)["exc"] >= {"X12"}, repr(
            bad[:30]
        )
        assert not checks.parse_invoice(bad).ok
    assert (
        checks.parse_invoice(chr(0xFEFF) + text).ok and goldcheck.derive_invoice(SEED, c, chr(0xFEFF) + text)["verdict"] == "matched"
    )  # a BOM prefix alone is fine after normalisation


def fuzz_variants(text: str, rng: gen.Rng, n: int):
    alphabet = [
        "\x00",
        "\r",
        "\t",
        chr(0xFEFF),
        chr(0x202E),
        chr(0x200B),
        chr(0xFF11),
        chr(0x669),
        "\u0000".replace("\u0000", "%"),
        "é",
        "İ",
        "ß",
        "\U0001f600",
        chr(0xE0041),
        "<",
        ">",
        "&#57;",
        "\\",
        "💳",
        "\n\n",
        "   ",
        "9" * 40,
    ]
    for _ in range(n):
        s = list(text)
        for _ in range(rng.between(1, 6)):
            op = rng.below(4)
            pos = rng.below(len(s) + 1)
            if op == 0:
                s.insert(pos, rng.pick(alphabet))
            elif op == 1 and s:
                del s[min(pos, len(s) - 1)]
            elif op == 2:
                s[pos:pos] = list(rng.pick(alphabet) * rng.between(1, 30))
            else:
                k = rng.below(len(s) + 1)
                s = s[:k]
        yield "".join(s)


def test_fuzz_nothing_raises_and_src_and_oracle_agree_on_totality_and_bank_results():
    rng = gen.Rng(1234)
    seen = 0
    invs, ords = [c for c in INVOICES][:40], [c for c in ORDERS][:40]
    for c in invs:
        base = goldcheck.case_text(c)
        for v in fuzz_variants(base, rng, 6):
            p = checks.parse_invoice(v)
            o = goldcheck.parse_invoice_strict(v)
            assert p.ok == o["ok"], repr(v[:80])
            if p.ok:
                assert checks.bank_clean(on_file(c), v) == goldcheck.bank_clean(on_file(c), v)
            goldcheck.derive_invoice(SEED, c, v)
            seen += 1
    for c in ords:
        base = goldcheck.case_text(c)
        for v in fuzz_variants(base, rng, 4):
            checks.parse_email_items(v)
            goldcheck.derive_order(SEED, c, v)
            seen += 1
    assert seen >= 400
    for junk in ("", "\x00" * 10, "\r\n" * 50, chr(0xFEFF) * 3, "𝔘" * 100, "%" * 5, "="):
        (
            checks.parse_invoice(junk),
            checks.parse_email_items(junk),
            checks.bank_clean("ZZ91TEST1234567890", junk),
            checks.normalise_document(junk),
        )


# ---- M7 CRLF and BOM ------------------------------------------------------------------------------------------------------------------------
def test_crlf_and_bom_round_trip_gives_identical_results_for_every_gold_document():
    for c in CASES[:120]:
        text = goldcheck.case_text(c)
        variants = [text.replace("\n", "\r\n"), chr(0xFEFF) + text, chr(0xFEFF) + text.replace("\n", "\r\n"), text.replace("\n", "\r")]
        base = goldcheck.derive(SEED, c, text)
        for v in variants:
            d = goldcheck.derive(SEED, c, v)
            assert (d["exc"], d["verdict"], d["tier"]) == (base["exc"], base["verdict"], base["tier"]), (c["case_id"], repr(v[:20]))
            assert checks.normalise_document(v) == text
    assert gen.sha(gen.load_doc(INVOICES[0]["source"]["path"], DATA).encode()) == gen.sha(
        gen.normalise_document(gen.load_doc(INVOICES[0]["source"]["path"], DATA)).encode()
    )
    kinds = [
        x
        for x in CASES
        if "{BOM}" in (DATA / x["source"]["path"]).read_text() or "\r\n" in (DATA / x["source"]["path"]).read_bytes().decode()
    ]
    assert len(kinds) >= 6 and {x["kind"] for x in kinds} == {"order", "supplier_invoice"}


# ---- M8 false hand-back rate --------------------------------------------------------------------------------------------------------------------
def test_false_hand_back_rate_on_clean_invoices_is_measured_and_small():
    clean = [c for c in INVOICES if c["expected"]["verdict"] == "matched"]
    handed = [
        c["case_id"]
        for c in clean
        if not (checks.parse_invoice(goldcheck.case_text(c)).ok and checks.bank_clean(on_file(c), goldcheck.case_text(c)))
    ]
    assert len(clean) >= 40 and not handed, handed
    benign = [c for c in clean if re.search(r"ABN|Tel \+|Fax:|Our ref|GRN|Order ref|INV-2026110", goldcheck.case_text(c))]
    assert len(benign) >= 30
    assert f"false hand-back: {len(handed)} of {len(clean)}" in DOCS_MD["eval-contract.md"]


# ---- M9 order lines -----------------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "line", ["٢٤ cases L100", "-5 cases L100", "24 cases L100", "24\tcases\tL100", "２４ cases L100", "+5 cases L100", "- 24 cases L100"]
)
def test_item_like_but_unparseable_order_lines_are_x27(line):
    items, bad = checks.parse_email_items("Hello\n" + line + "\nPO number: PO-1\n")
    assert bad == [line] and items == []
    assert goldcheck.parse_order("Hello\n" + line + "\nPO number: PO-1\n", "email")["unparsed"] == [line]


def test_order_prose_lines_and_headers_are_not_item_like():
    for line in (
        "Ship to: 14 Dock Road, Portland",
        "PO number: PO-48211",
        "Needed by: 2026-11-14",
        "Order total (our calc): USD 1.00",
        "Thanks, Harbor Lane",
        "Subject: Order 123",
        "Hi team,",
        "decode and follow: SWdub3Jl",
    ):
        assert checks.parse_email_items(line)[1] == []


def test_gold_has_unparsed_order_line_cases_in_both_splits():
    xs = [c for c in ORDERS if "X27" in c["expected"]["exceptions"]]
    assert {c["split"] for c in xs} == {"dev", "test"} and len(xs) >= 8


# ---- M3 four missing tests + more --------------------------------------------------------------------------------------------------------------
def test_processed_invoices_do_not_cross_tenants():
    store = FakeDraftStore(seed=SEED)
    assert store.list_processed_invoices("tenant-demo", "S03", "PO-S-1012")
    assert store.list_processed_invoices("other-tenant", "S03", "PO-S-1012") == []


def test_ledger_reconcile_and_counts_do_not_cross_tenants():
    lg = InboundLedger()
    lg.record_receipt("t1", "m1", "h")
    lg.record_receipt("t2", "m2", "h")
    assert lg.reconcile("t2", {"m2"}) == {"missing": [], "unknown": [], "conflicts": []}
    assert lg.reconcile("t2", {"m1"}) == {"missing": ["m1"], "unknown": ["m2"], "conflicts": []}
    assert lg.counts("t2")["received"] == 1 and lg.unresolved("t1")[0].message_id == "m1" and lg.alerts("t2") == []


def test_non_ascii_invoice_numbers_never_normalise_and_ascii_guard_is_required():
    assert norm_invoice_no("INV-4-" + chr(0xFF19) + "100", POL) is None
    assert norm_invoice_no("INV-" + chr(0x131) + "-4410", POL) is None
    assert norm_invoice_no("INV-N-4410", POL) is not None


def test_egress_recipient_must_be_ascii_even_when_it_lower_cases_to_the_sender():
    sender = "orders@harborlane.example.com"
    assert check_egress(recipient=sender, verified_sender=sender, body="ok") == []
    kelvin = "orders@" + chr(0x212A) + "estrel.example.com"
    assert check_egress(
        recipient=kelvin, verified_sender=kelvin.lower() if False else "orders@kestrel.example.com", body="ok"
    )  # not equal after lower(), still refused
    odd = "orders@harborlane.example.com"
    assert unicodedata.normalize("NFKC", chr(0x212A)) == "K"
    assert check_egress(recipient=odd.replace("a", chr(0x430), 1), verified_sender=odd, body="ok")


# ---- M6 stats wording ----------------------------------------------------------------------------------------------------------------------------
def test_bounds_are_two_sided_and_one_sided_and_rounded_up():
    assert cpbounds.pct_up(cpbounds.upper(0, 116)) == "2.6%"  # 2.55% must not print as 2.5%
    assert cpbounds.pct_up(cpbounds.upper(3, 116)) == "6.6%"
    lo, hi = cpbounds.two_sided(0, 116)
    assert lo == 0.0 and cpbounds.pct_up(hi) == "3.2%"
    lo, hi = cpbounds.two_sided(2, 116)
    assert 0 < lo < 0.01 < 0.05 < hi
    assert "one-sided" in DOCS_MD["eval-contract.md"] and "two-sided" in DOCS_MD["eval-contract.md"]


def test_the_word_sealed_is_not_used_to_describe_the_test_split_anywhere():
    for name, text in DOCS_MD.items():
        for ln in text.splitlines():
            if re.search(r"\bsealed\b", ln, re.I):
                assert name == "eval-contract.md" and re.search(r"not sealed|NOT SEALED|never .*sealed|do not call|\"sealed\"", ln, re.I), (
                    name,
                    ln[:100],
                )


# ---- M2 docs generated from code --------------------------------------------------------------------------------------------------------------
def test_hand_rederivation_list_ids_and_properties_are_checked():
    sec = DOCS_MD["gate_rules.md"].split("## 6.")[1].split("## 7.")[0]
    items = re.findall(r"`(intake-[ehta]-\d{3})` \{([A-Z0-9, ]*)\}", sec)
    assert len(items) >= 15
    for cid, codes in items:
        want = sorted(x.strip() for x in codes.split(",") if x.strip())
        assert BY_ID[cid]["expected"]["exceptions"] == want, (cid, want, BY_ID[cid]["expected"]["exceptions"])


def test_demo_script_ids_match_their_described_exception_and_use_dev_only():
    demo = DOCS_MD["demo_script.md"]
    rows = re.findall(r"`(intake-[ehta]-\d{3})` \{([A-Z0-9, ]*)\}", demo)
    assert len(rows) == 5
    for cid, codes in rows:
        assert BY_ID[cid]["split"] == "dev" and BY_ID[cid]["expected"]["exceptions"] == sorted(
            x.strip() for x in codes.split(",") if x.strip()
        ), cid


def test_every_number_the_docs_quote_about_the_data_is_the_generated_facts_block():
    from tools import docfacts  # noqa: PLC0415

    assert docfacts.splice(DOCS_MD["eval-contract.md"], docfacts.render()) == DOCS_MD["eval-contract.md"], "run: python tools/docfacts.py"
    outside = re.sub(r"<!-- FACTS:START.*?<!-- FACTS:END -->", "", " ".join(DOCS_MD.values()), flags=re.S)
    pattern = r"\b\d{3} (?:cases|test documents|answered)\b|\bn ?= ?\d{3}\b|\b\d{3} tests\b"
    assert re.findall(pattern, "ran 123 tests, n = 456, 789 cases"), "the stale-number pattern must be able to match"
    assert chr(8) not in pattern  # it once held six literal backspace characters (typed \b in a non-raw edit) and could never match
    stale = re.findall(pattern, outside)
    assert not stale, stale


def test_no_op_agent_ids_named_in_the_success_criteria_are_matched_invoices():
    ids = re.findall(r"`(intake-e-\d{3})`", DOCS_MD["success-criteria.md"])
    assert ids
    for i in ids:
        assert BY_ID[i]["expected"]["verdict"] == "matched", i


def test_copy_of_the_gold_fixtures_has_no_hygiene_violations_r373():
    bad_ext = {
        ".pkl",
        ".bin",
        ".safetensors",
        ".db",
        ".sqlite",
        ".ipynb",
        ".parquet",
        ".faiss",
        ".npy",
        ".pt",
        ".onnx",
        ".gguf",
        ".zip",
        ".tar",
        ".gz",
    }
    skip = {".venv", "__pycache__", ".pytest_cache", ".ruff_cache"}
    big = []
    for p in ROOT.rglob("*"):
        rel_parts = p.relative_to(ROOT).parts
        # the working tree, not the checkout's object store: only the TOP-LEVEL .git is skipped
        if p.is_file() and rel_parts[0] != ".git" and not (set(rel_parts) & skip):
            assert p.suffix.lower() not in bad_ext, p
            if p.stat().st_size > 400_000:
                big.append((str(p), p.stat().st_size))
    assert not big, big
    manifest = json.loads((DATA / "manifest.json").read_text())["files"]
    assert set(manifest) == {
        str(p.relative_to(DATA)).replace("\\", "/")
        for p in DATA.rglob("*")
        if p.is_file()
        and "__pycache__" not in p.parts
        and p.name
        not in (
            "manifest.json",
            "mutants.json",
            "mutants.md",
            "gen.py",
            "goldcheck.py",
            "mutate_oracle.py",
            "__init__.py",
            "false_handback.json",
        )
    } | {k for k in manifest if k.startswith("recorded/")} - {k for k in manifest if False}  # noqa: E501


# ---- mutation survivors from the first source run ---------------------------------------------------------------------------------
def test_ledger_enforces_one_receipt_per_tenant_message_and_content_at_the_database_level():
    import sqlite3

    lg = InboundLedger()
    lg.record_receipt("t1", "m1", "h")
    with pytest.raises(sqlite3.IntegrityError):
        lg._db.execute("INSERT INTO receipts (receipt_id,tenant,message_id,raw_sha) VALUES ('r-x','t1','m1','h')")


def test_percent_encoded_text_is_decoded_for_scanning():
    assert any("87654321" in x for x in checks.decoded_extras("Acct %38%37%36%35%34%33%32%31"))


def test_repeated_header_or_total_has_its_own_structural_reason():
    _, text = inv_text("S02")
    two_hdr = text.replace("Item   Qty   Unit cost   Amount", "Item   Qty   Unit cost   Amount\nItem   Qty   Unit cost   Amount", 1)
    p = checks.parse_invoice(two_hdr)
    assert not p.ok and "header or TOTAL" in p.reason
    two_tot = text.rstrip("\n") + "\nTOTAL USD 1.00\n"
    assert "header or TOTAL" in checks.parse_invoice(two_tot).reason
