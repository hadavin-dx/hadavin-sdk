"""WP2c wiring in ``extract_parsed`` (design B4 and B5): the order of steps, the self-check codes that reach ``ProcessedDoc.selfcheck``, restore on the
returned record, and the AST rule that only ``extract.py`` builds ``mask.BodyCheck``. The model here is a scripted stand-in."""

from __future__ import annotations

import ast
import copy

import pytest
from model_support import register
from test_extract import A_RAW, GOOD, Scripted, err, ok

from conftest import ROOT, settings_for_tests
from intake import extract, mask, reader, selfcheck_codes
from intake.codes import ConfigError

KEY = bytes(range(32))
TEXT_ADD = "Contact: jo@acme.example.com\n"


@pytest.fixture
def s(tmp_path):
    return settings_for_tests(tmp_path)


def doc_with_email(s):
    raw = A_RAW + TEXT_ADD.encode()
    p = reader.read("inv-E.txt", raw)
    register(s, p.text)
    return p


def reply_with(**changes):
    f = copy.deepcopy(GOOD)
    f.update(changes)
    return f


def test_clean_invoice_masks_once_per_request_and_restores_nothing(s):
    m = Scripted(ok(GOOD))
    d = extract.extract_parsed(reader.read("inv-A.txt", A_RAW), m, s, key=KEY, streak=None)
    assert d.fields == GOOD and d.selfcheck is None and d.key == KEY and d.document_text and d.spans
    assert m.calls[0].model_text == mask.mask(d.document_text, KEY).text != d.document_text
    assert d.mask_summary["restored"] == 0


def test_a_mark_copied_by_the_ai_is_put_back_into_a_description(s):
    p = doc_with_email(s)
    marked = mask.mask(p.text, KEY)
    mark = next(sp.placeholder for sp in marked.spans if sp.kind == "EMAIL")
    f = copy.deepcopy(GOOD)
    f["lines"][0]["description"] = f"{f['lines'][0]['description']} {mark}"
    d = extract.extract_parsed(p, Scripted(ok(f)), s, key=KEY, streak=None)
    assert d.selfcheck is None and d.mask_summary["restored"] == 1
    # the restored description is not a phrase of the invoice (the AI added the mark to it), so grounding on the ORIGINAL text refuses the line
    assert d.fields is None and d.failing_fields == ("lines",)


def test_the_returned_record_is_judged_on_the_original_text(s):
    f = reply_with(total_minor=999999)
    m = Scripted(ok(f))
    d = extract.extract_parsed(reader.read("inv-A.txt", A_RAW), m, s, key=KEY, streak=None)
    assert (
        d.fields is None and d.failing_fields and d.selfcheck is None and [c.tier for c in d.calls] == ["read"]
    )  # DF5: a quality failure makes no second call


@pytest.mark.parametrize("field_name", ["invoice_no", "supplier_name"])
def test_a_bank_mark_in_a_plain_field_is_hidden_value_in_field_and_costs_the_call(s, field_name):
    p = reader.read("inv-A.txt", A_RAW)
    mark = next(sp.placeholder for sp in mask.mask(p.text, KEY).spans if sp.kind == "IBAN")
    m = Scripted(ok(reply_with(**{field_name: mark}), cost=7))
    d = extract.extract_parsed(p, m, s, key=KEY, streak=None)
    assert d.fields is None and d.selfcheck == "hidden_value_in_field" and d.cost_micro == 7 and len(m.calls) == 1
    assert selfcheck_codes.FLAG_OF["hidden_value_in_field"] == "M01"


def test_a_forged_mark_is_m02_one_call_no_fallback(s):
    m = Scripted(ok(reply_with(invoice_no="<BANK_9>"), cost=5))
    d = extract.extract_parsed(reader.read("inv-A.txt", A_RAW), m, s, key=KEY, streak=None)
    assert d.selfcheck == "forged_mark" and d.cost_micro == 5 and len(m.calls) == 1 and selfcheck_codes.FLAG_OF["forged_mark"] == "M02"


def test_a_mark_like_text_is_held_back_before_any_call(s):
    p = reader.read("inv-M.txt", A_RAW + b"Ref <BANK_1>\n")
    register(s, p.text)
    m = Scripted(None)
    d = extract.extract_parsed(p, m, s, key=KEY, streak=None)
    assert d.selfcheck == "mark_like_text" and m.calls == [] and d.cost_micro == 0 and d.fields is None


def test_a_long_line_is_held_back_before_any_call(s):
    p = reader.read("inv-L.txt", A_RAW + b"x" * 2001 + b"\n")
    register(s, p.text)
    m = Scripted(None)
    d = extract.extract_parsed(p, m, s, key=KEY, streak=None)
    assert d.selfcheck == "mask_too_large" and m.calls == []


def test_a_sink_that_cannot_write_means_no_call(s):
    class Sink:
        def mask_done(self, masked, key, document_text):
            raise OSError("no")

    m = Scripted(None)
    try:
        d = extract.extract_parsed(reader.read("inv-A.txt", A_RAW), m, s, tracer=Sink(), key=KEY, streak=None)
    except OSError:
        pytest.fail("the sink failure escaped instead of becoming mask_failed")
    assert d.selfcheck == "mask_failed" and m.calls == []


def test_the_sink_sees_the_masked_result_and_the_key(s):
    seen = []

    class Sink:
        def mask_done(self, masked, key, document_text):
            seen.append((masked, key))

    extract.extract_parsed(reader.read("inv-A.txt", A_RAW), Scripted(ok(GOOD)), s, tracer=Sink(), key=KEY, streak=None)
    assert len(seen) == 1 and seen[0][1] == KEY and seen[0][0].spans


@pytest.mark.parametrize("code", ["body_has_original", "mask_failed", "mask_residual", "doc_sha_mismatch"])
def test_body_unsafe_carries_last_code(s, code):
    class Refusing:
        def call(self, req, **kw):
            kw["body_check"].refuse(code)
            return err("body_unsafe")

    d = extract.extract_parsed(reader.read("inv-A.txt", A_RAW), Refusing(), s, key=KEY, streak=None)
    assert d.selfcheck == code and d.error == "body_unsafe" and d.fields is None and d.cost_micro == 0 and len(d.calls) == 1


def test_body_unsafe_without_a_code_is_mask_failed_and_gives_m01_not_l02(s):
    class Refusing:
        def call(self, req, **kw):
            return err("body_unsafe")

    d = extract.extract_parsed(reader.read("inv-A.txt", A_RAW), Refusing(), s, key=KEY, streak=None)
    assert d.selfcheck == "mask_failed" and selfcheck_codes.FLAG_OF[d.selfcheck] == "M01"


def test_settle_failed_still_leaves_extract(s):
    class Boom:
        def call(self, req, **kw):
            raise ConfigError("settle_failed", "x")

    with pytest.raises(ConfigError):
        extract.extract_parsed(reader.read("inv-A.txt", A_RAW), Boom(), s, key=KEY, streak=None)


def test_reader_flagged_file_is_not_masked_or_keyed(s):
    d = extract.extract_parsed(reader.read("x.txt", b"a\x00b"), Scripted(None), s, streak=None)
    assert d.selfcheck is None and d.spans == () and d.key is None


def test_a_fresh_key_is_made_when_none_is_given_and_returned(s):
    d = extract.extract_parsed(reader.read("inv-A.txt", A_RAW), Scripted(ok(GOOD)), s, streak=None)
    assert isinstance(d.key, bytes) and len(d.key) == 32
    e = extract.extract_parsed(reader.read("inv-A.txt", A_RAW), Scripted(ok(GOOD)), s, streak=None)
    assert e.key != d.key


def test_mask_body_check_is_built_only_in_extract_py():
    for p in sorted((ROOT / "src" / "intake").glob("*.py")):
        if p.name not in {"extract.py", "mask.py"}:
            assert "BodyCheck(" not in p.read_text(encoding="utf-8").replace("class BodyCheck(Protocol)", ""), p.name
    tree = ast.parse((ROOT / "src" / "intake" / "extract.py").read_text(encoding="utf-8"))
    built = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "BodyCheck"]
    assert len(built) == 1


def test_judge_gets_the_restored_record_and_the_original_text(s, monkeypatch):
    """(d) runs on the record with the values put back and on the ORIGINAL text, never on the masked one; what it passes is what the caller gets."""
    p = doc_with_email(s)
    mark = next(sp.placeholder for sp in mask.mask(p.text, KEY).spans if sp.kind == "EMAIL")
    f = copy.deepcopy(GOOD)
    f["lines"][0]["description"] = f"Mail {mark}"
    seen = []
    monkeypatch.setattr(extract, "judge", lambda fields, text, cur: (seen.append((fields, text)), ())[1])
    d = extract.extract_parsed(p, Scripted(ok(f)), s, key=KEY, streak=None)
    assert seen[0][1] == p.text and seen[0][0]["lines"][0]["description"] == "Mail jo@acme.example.com"
    assert d.fields["lines"][0]["description"] == "Mail jo@acme.example.com"


def test_checks_a3_and_a2_run_before_any_call(s, monkeypatch):
    from intake.selfcheck_codes import SelfCheckFailed

    def refuse(masked):
        raise SelfCheckFailed("mask_residual")

    monkeypatch.setattr(mask, "check_model_text", refuse)
    m = Scripted(None)
    d = extract.extract_parsed(reader.read("inv-A.txt", A_RAW), m, s, key=KEY, streak=None)
    assert d.selfcheck == "mask_residual" and m.calls == [] and d.cost_micro == 0


def test_repr_of_a_processed_doc_holds_no_invoice_text_or_record(s):
    p = doc_with_email(s)
    d = extract.extract_parsed(p, Scripted(ok(GOOD)), s, key=KEY, streak=None)
    text = repr(d)
    assert "jo@acme.example.com" not in text and "Acme Ltd" not in text and "INV-1001" not in text and p.text[:40] not in text
