"""The WP0 fixtures under tests/fixtures/mini: byte rules, the content-code byte fixtures (recomputed here), fake replies keyed by raw hash and tier,
and the committed config/attribute rules the fixtures rely on."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata

from conftest import MINI, ROOT, mini_hashes
from intake import rules, validators

CC = json.loads((MINI / "content_code_fixtures.json").read_text(encoding="utf-8"))
REPLIES = json.loads((MINI / "fake_replies.json").read_text(encoding="utf-8"))
DOCS = ["inv-A.txt", "inv-B.txt", "inv-C.txt", "calibration-25.txt"]


def test_documents_are_lf_ascii_plain_text_with_valid_names():
    from intake import settings

    rx = json.loads((ROOT / "config" / "service.json").read_text(encoding="utf-8"))["service"]["name_regex"]
    for n in DOCS:
        b = (MINI / n).read_bytes()
        assert b"\r" not in b and b"\x00" not in b and b.isascii() and b.endswith(b"\n") and len(b) < 200000
        assert settings.is_name_allowed(n, rx)
        assert unicodedata.normalize("NFC", b.decode()) == b.decode()
    for p in MINI.iterdir():
        assert b"\r" not in p.read_bytes(), p.name  # a test asserts no CR in fixture bytes
        assert p.suffix in {".txt", ".json", ".csv"}


def test_attributes_keep_fixtures_untouched_and_line_one_is_unchanged():
    lines = (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
    assert lines[0] == "* text=auto eol=lf"
    assert "tests/fixtures/** -text" in lines and "demo_only/layouts/** -text" in lines
    assert lines.index("tests/fixtures/** -text") > 0


def test_three_layouts_and_a_25_line_calibration_invoice():
    a, b, c, cal = ((MINI / n).read_text() for n in DOCS)
    assert "IBAN" in a and "$12.50" in a  # LAY1: columns, IBAN
    assert re.search(r"sort code 00-00-00 account 00012345", b)  # LAY2: prose, sort code and account
    assert "|" in c and "Routing 111222333 Account 999999999" in c  # LAY3: pipe table, routing and account
    assert len(REPLIES[_key("calibration-25.txt", "fallback")]["fields"]["lines"]) == 25
    assert len(re.findall(r"^Part \d\d bracket", cal, re.M)) == 25


def test_suppliers_csv():
    rows = list(csv.reader((MINI / "suppliers.csv").read_text(encoding="utf-8").splitlines()))
    assert rows[0] == ["supplier_name", "bank_detail"] and len(rows) == 5
    assert {r[0] for r in rows[1:]} == {"Acme Ltd", "Birch Supplies Limited", "Cedar Industrial Inc", "Dunmore Trading Co"}


def _key(name: str, tier: str) -> str:
    return f"{hashlib.sha256((MINI / name).read_bytes()).hexdigest()}:{tier}"


def test_fake_replies_are_keyed_doc_sha_colon_tier_and_valid():
    assert all(re.fullmatch(r"[0-9a-f]{64}:(read|fallback)", k) for k in REPLIES)
    for n in DOCS[:3]:
        assert _key(n, "read") in REPLIES
    assert REPLIES[_key("calibration-25.txt", "read")] == "timeout"  # an error code value
    for k, val in REPLIES.items():
        if isinstance(val, str):
            continue
        assert set(val) == {"fields", "model_id", "in_tok", "out_tok", "cost_micro", "error"} and val["error"] is None
        assert validators.validate_record(val["fields"]) == [], k
        assert val["model_id"] not in ("read", "fallback")  # the tier name is the key, never the model id


def test_every_fake_reply_value_is_found_in_its_document():
    for n in DOCS:
        text = (MINI / n).read_text()
        for tier in ("read", "fallback"):
            val = REPLIES.get(_key(n, tier))
            if not isinstance(val, dict):
                continue
            f = val["fields"]
            assert f["invoice_no"] in text and f["supplier_name"] in text
            assert all(line["description"] in text for line in f["lines"])


def test_d06_and_d10_cases_are_what_the_names_say():
    def f(n):
        return REPLIES[_key(n, "read")]["fields"]

    def total(x):
        return sum(ln["amount_minor"] for ln in x["lines"]) + sum(a["amount_minor"] for a in x["adjustments"])

    assert total(f("inv-A.txt")) == f("inv-A.txt")["total_minor"]  # clean
    assert total(f("inv-B.txt")) != f("inv-B.txt")["total_minor"]  # D06: wrong total
    assert total(f("inv-C.txt")) == f("inv-C.txt")["total_minor"]
    for x in (f("inv-A.txt"), f("inv-B.txt"), f("inv-C.txt")):
        assert all(ln["amount_minor"] == ln["qty"] * ln["unit_cost_minor"] for ln in x["lines"])
    cal = REPLIES[_key("calibration-25.txt", "fallback")]["fields"]
    assert total(cal) == cal["total_minor"] and all(ln["amount_minor"] == ln["qty"] * ln["unit_cost_minor"] for ln in cal["lines"])
    sup = {r["supplier_name"]: r["bank_detail"] for r in csv.DictReader((MINI / "suppliers.csv").open(encoding="utf-8"))}
    assert (
        "999999999" not in sup["Cedar Industrial Inc"] and "111222333" in sup["Cedar Industrial Inc"]
    )  # LAY3: changed account, same routing


def test_content_code_fixtures_are_recomputed_not_trusted():
    expected = {
        "invoice_with_flag": "2fd393547c416568a7af7c9ed0df60e4d88ef3cdd34b89eb9e16183caaa0c531",
        "item_without_fields": "fa9bb129b77347b9c137ba15462446bdd1e4b4ddb63e9856cd73b5cf833efe01",
    }
    for fx in CC["fixtures"]:
        s = fx["canonical"]
        assert hashlib.sha256(s.encode("utf-8")).hexdigest() == fx["sha256"] == expected[fx["name"]]
        assert json.dumps(json.loads(s), sort_keys=True, separators=(",", ":"), ensure_ascii=True) == s
        assert len(json.loads(s)) == 12  # exactly the twelve keys of the content code
    from intake import tools

    assert (
        tools.canonical_json(json.loads(CC["fixtures"][0]["canonical"])) == CC["fixtures"][0]["canonical"]
    )  # the existing helper gives the same bytes


def test_row_id_vector():
    v = CC["row_id_vector"]
    pol = rules.load_policy()
    sk = " ".join(unicodedata.normalize("NFKC", v["supplier_name"]).casefold().split())
    ik = rules.norm_invoice_no(v["invoice_no"], pol)
    assert (sk, ik) == (v["supplier_key"], v["invoice_key"])
    assert hashlib.sha256("\x1f".join([v["tenant_id"], sk, ik]).encode("utf-8")).hexdigest() == v["row_id"]
    assert v["tenant_id"] == "demo-intake"


def test_mini_hashes_are_four_distinct_normalised_hashes():
    h = mini_hashes()
    assert len(h) == 4 == len(set(h)) and all(re.fullmatch(r"[0-9a-f]{64}", x) for x in h)
