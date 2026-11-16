"""Content code and row id (spec 8): both byte fixtures recomputed with ``python -I``, binding properties, the null-field rule and the row id vector."""

from __future__ import annotations

import copy
import json
import subprocess
import sys

import pytest
from queue_helpers import GOOD_FIELDS, assertive_all

from conftest import MINI, settings_for_tests
from intake import content_code as cc
from intake import rules, workqueue

# the spec values (section 8), written here as literals as well as in the fixture file
SPEC_1 = (
    '{"adjustments":[["VAT",300]],"currency":"USD","flags":["D06"],"invoice_date":"2026-10-01","invoice_no":"INV-1001",'
    '"lines":[["Widget A",2,1250,2500],["Shipping line",1,500,500]],"po_ref":null,"schema_version":1,'
    '"source_sha256":"0000000000000000000000000000000000000000000000000000000000000000","supplier_name":"Acme Ltd",'
    '"tenant_id":"demo-intake","total_minor":3300}'
)
SPEC_1_SHA = "2fd393547c416568a7af7c9ed0df60e4d88ef3cdd34b89eb9e16183caaa0c531"
SPEC_2 = (
    '{"adjustments":[],"currency":null,"flags":["X18"],"invoice_date":null,"invoice_no":null,"lines":[],"po_ref":null,"schema_version":1,'
    '"source_sha256":"1111111111111111111111111111111111111111111111111111111111111111","supplier_name":null,'
    '"tenant_id":"demo-intake","total_minor":null}'
)
SPEC_2_SHA = "fa9bb129b77347b9c137ba15462446bdd1e4b4ddb63e9856cd73b5cf833efe01"
POL = rules.load_policy()
FIX = json.loads((MINI / "content_code_fixtures.json").read_text(encoding="utf-8"))


def item(fields=GOOD_FIELDS, flags=("D06",), sha="0" * 64, tenant="demo-intake", **kw):
    base = dict(
        uid=1, id="x-00000000", source_name="x.txt", source_sha256=sha, tenant_id=tenant, state="NEEDS_PERSON", fields=fields, flags=tuple(flags),
        failing_fields=(), source_text="t", model_id=None, tier=None, prompt_sha256=None, cost_micro=0, version=1, created_at="2026-11-03T00:00:00Z",
    )  # fmt: skip
    base.update(kw)
    return workqueue.Item(**base)


def test_fixture_file_holds_the_spec_values():
    assert [(f["canonical"], f["sha256"]) for f in FIX["fixtures"]] == [(SPEC_1, SPEC_1_SHA), (SPEC_2, SPEC_2_SHA)]


@pytest.mark.parametrize("canonical,digest", [(SPEC_1, SPEC_1_SHA), (SPEC_2, SPEC_2_SHA)])
def test_the_spec_sha256_recomputed_with_python_dash_i(canonical, digest):
    assert json.dumps(json.loads(canonical), sort_keys=True, separators=(",", ":"), ensure_ascii=True) == canonical
    code = "import hashlib,sys;print(hashlib.sha256(sys.argv[1].encode('utf-8')).hexdigest())"
    out = subprocess.run([sys.executable, "-I", "-c", code, canonical], capture_output=True, text=True, timeout=60, check=True)  # noqa: S603
    assert out.stdout.strip() == digest


def test_content_code_matches_fixture_1_and_2():
    one = item()
    assert json.dumps(cc.record(one), sort_keys=True, separators=(",", ":"), ensure_ascii=True) == SPEC_1
    assert cc.content_code(one) == SPEC_1_SHA
    two = item(fields=None, flags=("X18",), sha="1" * 64)
    assert cc.content_code(two) == SPEC_2_SHA


def test_the_record_has_exactly_the_twelve_keys():
    keys = {
        "schema_version", "tenant_id", "source_sha256", "invoice_no", "supplier_name", "po_ref",
        "currency", "invoice_date", "lines", "adjustments", "total_minor", "flags",
    }  # fmt: skip
    assert set(cc.record(item())) == keys and set(cc.record(item(fields=None, flags=("X18",)))) == keys


def test_an_item_read_back_from_the_database_has_the_same_code(tmp_path):
    s = settings_for_tests(tmp_path)
    it = workqueue.insert_received(s, "x.txt", "0" * 64, "t", "demo-intake", "x")
    done = workqueue.set_result(
        s,
        it.uid,
        "NEEDS_PERSON",
        fields=GOOD_FIELDS,
        flags=["D06"],
        failing_fields=[],
        model_id="m",
        tier="read",
        prompt_sha256="p" * 64,
        cost_micro=0,
    )
    assert cc.content_code(done) == SPEC_1_SHA


def _variants():
    def f(**ch):
        d = copy.deepcopy(GOOD_FIELDS)
        d.update(ch)
        return {"fields": d}

    def line(i, k, v):
        d = copy.deepcopy(GOOD_FIELDS)
        d["lines"][i][k] = v
        return {"fields": d}

    def adj(i, k, v):
        d = copy.deepcopy(GOOD_FIELDS)
        d["adjustments"][i][k] = v
        return {"fields": d}

    return {
        "tenant_id": {"tenant": "other"},
        "source_sha256": {"sha": "2" * 64},
        "invoice_no": f(invoice_no="INV-1002"),
        "supplier_name": f(supplier_name="Acme Ltd."),
        "po_ref": f(po_ref="PO-1"),
        "currency": f(currency="GBP"),
        "invoice_date": f(invoice_date="2026-10-02"),
        "invoice_date_null": f(invoice_date=None),
        "total_minor": f(total_minor=3301),
        "line_description": line(0, "description", "Widget B"),
        "line_qty": line(0, "qty", 3),
        "line_unit": line(0, "unit_cost_minor", 1251),
        "line_amount": line(0, "amount_minor", 2501),
        "line_removed": {"fields": {**GOOD_FIELDS, "lines": GOOD_FIELDS["lines"][:1]}},
        "line_order": {"fields": {**GOOD_FIELDS, "lines": GOOD_FIELDS["lines"][::-1]}},
        "adjustment_label": adj(0, "label", "Tax"),
        "adjustment_amount": adj(0, "amount_minor", 301),
        "adjustment_removed": f(adjustments=[]),
        "flags": {"flags": ("D06", "L01")},
        "flags_none": {"flags": ()},
    }


@pytest.mark.parametrize("name", sorted(_variants()))
def test_the_code_changes_when_any_hashed_field_changes(name):
    changed = cc.content_code(item(**_variants()[name]))
    assert changed != SPEC_1_SHA and changed != cc.content_code(item())


def test_the_code_ignores_what_is_not_hashed_and_the_flag_order():
    base = cc.content_code(item())
    assert (
        cc.content_code(item(state="READY", version=9, cost_micro=77, id="zzz", uid=5, model_id="m", tier="read", failing_fields=("x",)))
        == base
    )
    assert cc.content_code(item(flags=("D06",), source_text="other text")) == base
    assert cc.content_code(item(flags=("L01", "D06"))) == cc.content_code(item(flags=("D06", "L01")))


def test_the_code_hashes_the_unguarded_text():
    """The CSV cell guard (WP5) changes only the exported text; here: the code reads the raw value, not a folded or prefixed one."""
    guarded = copy.deepcopy(GOOD_FIELDS)
    guarded["supplier_name"] = "'" + guarded["supplier_name"]
    assert cc.content_code(item(fields=guarded)) != SPEC_1_SHA
    assert "'" not in json.dumps(cc.record(item()))


def test_null_field_items_use_null_scalars_and_empty_lists_and_have_a_code():
    r = cc.record(item(fields=None, flags=("X18",), sha="1" * 64))
    assert [r[k] for k in ("invoice_no", "supplier_name", "po_ref", "currency", "invoice_date", "total_minor")] == [None] * 6
    assert r["lines"] == [] and r["adjustments"] == [] and r["flags"] == ["X18"] and r["source_sha256"] == "1" * 64


def test_row_id_vector():
    v = FIX["row_id_vector"]
    assert cc.row_id(v["tenant_id"], v["supplier_name"], v["invoice_no"], POL) == v["row_id"]
    import hashlib

    assert hashlib.sha256("\u001f".join((v["tenant_id"], v["supplier_key"], v["invoice_key"])).encode()).hexdigest() == v["row_id"]
    assert v["invoice_key"] == "1NV1001" and v["supplier_key"] == "acme ltd"
    assert cc.item_row_id(item(), POL) == v["row_id"]


def test_row_id_normalisation():
    base = cc.row_id("t", "Acme Ltd", "INV-1001", POL)
    assert cc.row_id("t", "  ACME   ltd ", "inv-1001", POL) == base
    assert cc.row_id("t", "Acme Ltd", "INV-1001-REV", POL) == base  # the revision suffix maps to the same row id (spec 7)
    assert cc.row_id("t", "Ａcme Ltd", "INV-1001", POL) == base  # NFKC: a fullwidth letter
    assert cc.row_id("t", "Acme Ltd", "INV-1002", POL) != base and cc.row_id("u", "Acme Ltd", "INV-1001", POL) != base
    non_ascii = cc.row_id("t", "Acme Ltd", "Réf 7", POL)  # None from norm_invoice_no: casefolded, whitespace-collapsed text
    assert non_ascii == cc.row_id("t", "Acme Ltd", " réf   7 ", POL) != base


def test_item_without_fields_has_no_row_id():
    assert cc.item_row_id(item(fields=None, flags=("X18",)), POL) is None


def test_row_id_folds_a_fullwidth_invoice_number_like_the_ascii_one():
    base = cc.row_id("t", "Acme Ltd", "INV-1001", POL)
    assert cc.row_id("t", "Acme Ltd", "".join(chr(ord(c) + 0xFEE0) if c.isalnum() else c for c in "INV-1001"), POL) == base


@pytest.mark.parametrize(
    "fields",
    [
        {},
        {"lines": "x"},
        {"lines": [1, None, "a", {"qty": 1}], "adjustments": [3, {"label": "x"}]},
        {"adjustments": {"a": 1}},
        ["x"],
        "text",
        5,
    ],
)
def test_record_never_raises_on_a_malformed_stored_record(fields):
    r = cc.record(item(fields=fields, flags=("X10",)))
    assert len(r) == 12 and isinstance(cc.content_code(item(fields=fields, flags=("X10",))), str)


@pytest.mark.parametrize(
    "twin",
    [
        chr(0x406) + "NV-1001",  # Cyrillic I at position 0
        "INV-1001".replace("I", chr(0x399)),  # Greek capital iota
        "INV-1001".replace("V", chr(0x474)),  # Cyrillic izhitsa
        "INV-1001" + chr(0x200B),  # zero-width space
    ],
)
def test_row_id_folds_look_alike_invoice_numbers_to_the_same_id(twin):
    assert cc.row_id("t", "Acme Ltd", twin, POL) == cc.row_id("t", "Acme Ltd", "INV-1001", POL)


def test_row_id_folds_look_alike_suppliers_and_keeps_tenants_apart():
    base = cc.row_id("t", "Acme Ltd", "INV-1001", POL)
    assert cc.row_id("t", chr(0x410) + "cme Ltd", "INV-1001", POL) == base  # Cyrillic A
    assert cc.row_id("t", "Acme Ltd", "INV-1001", POL) != cc.row_id("u", "Acme Ltd", "INV-1001", POL)
    assert cc.row_id("t", "Acme Inc", "INV-1001", POL) != base


def test_item_row_id_never_raises_on_a_malformed_stored_record():
    for fields in (
        {},
        {"supplier_name": "A"},
        {"supplier_name": 5, "invoice_no": "x"},
        {"supplier_name": "A", "invoice_no": None},
        ["x"],
        "t",
    ):
        assert cc.item_row_id(item(fields=fields, flags=("X10",)), POL) is None


def test_row_id_cyrillic_a_at_position_zero_matches_the_latin_a():
    assert cc.row_id("t", "Acme Ltd", chr(0x410) + "BC-1001", POL) == cc.row_id("t", "Acme Ltd", "ABC-1001", POL)


assertive_all(globals())
