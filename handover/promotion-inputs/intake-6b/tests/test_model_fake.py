"""Model port and fake backend: closed error set, fallback table, key format, stand-in body, guard-computed cost."""

from __future__ import annotations

import hashlib
import json

import pytest
from model_support import GOOD_FIELDS, fake_settings, fake_with, guarded, register, reply, req, sha

from intake import budget, model
from intake.codes import MODEL_ERRORS
from intake.model_fake import FakeBackend
from intake.reader import normalise_for_model

TEXT = "Invoice INV-1 total 1.00"


def test_model_result_accepts_only_the_closed_error_set():
    for code in MODEL_ERRORS:
        assert model.ModelResult(None, None, 0, 0, 0, code).error == code
    with pytest.raises(ValueError):
        model.ModelResult(None, None, 0, 0, 0, "redirect")
    assert len(MODEL_ERRORS) == 12


@pytest.mark.parametrize("code", ["timeout", "net", "tls", "http_429", "http_5xx", "over_cap", "max_tokens", "bad_reply"])
def test_fallback_table_calls_the_fallback_tier_after(code):
    assert model.fallback_allowed(code)


@pytest.mark.parametrize("code", ["gate", "budget", "halted", "http_4xx", None])
def test_fallback_table_does_not_call_the_fallback_tier_after(code):
    assert not model.fallback_allowed(code)  # None = a reply returned: the caller decides on validation and grounding


def test_the_two_tables_cover_the_whole_closed_set():
    assert model.FALLBACK_CODES | model.NO_FALLBACK_CODES == MODEL_ERRORS and not model.FALLBACK_CODES & model.NO_FALLBACK_CODES


def test_stand_in_body_differs_per_document_and_tier(tmp_path):
    s = fake_settings(tmp_path)
    b = FakeBackend(s)
    bodies = {b.request_body(req(t, tier)) for t in (TEXT, "other") for tier in ("read", "fallback")}
    assert len(bodies) == 4
    d = json.loads(b.request_body(req(TEXT, "fallback")))
    assert d["doc_sha"] == sha(TEXT) and d["tier"] == "fallback"
    assert b.preflight() is None


def test_replies_are_keyed_by_doc_sha_and_tier_name_from_the_fixture_file(tmp_path):
    s = fake_settings(tmp_path)
    keys = list(json.loads(s.model.fake_replies_path.read_text(encoding="utf-8")))
    assert keys and all(k.endswith((":read", ":fallback")) and len(k.split(":")[0]) == 64 for k in keys)
    inv = s.model.fake_replies_path.parent / "inv-A.txt"
    raw = inv.read_bytes()
    g = guarded(s, FakeBackend(s))
    r = g.call(model.ExtractRequest(normalise_for_model(raw), hashlib.sha256(raw).hexdigest(), "read"))
    assert r.error is None and r.fields["invoice_no"] == "INV-1001" and r.model_id


def test_an_unknown_key_and_a_junk_value_are_bad_reply(tmp_path):
    s = fake_settings(tmp_path)
    register(s, TEXT)
    for value in ({}, "not-a-code", 5, {"fields": {}, "error": "weird"}):
        r = guarded(s, fake_with(s, TEXT, read=value)).call(req(TEXT))
        assert r.error == "bad_reply"
    assert guarded(s, FakeBackend(s, {})).call(req(TEXT)).error == "bad_reply"  # key missing


def test_error_code_string_replies_map_to_the_error(tmp_path):
    s = fake_settings(tmp_path)
    register(s, TEXT)
    assert guarded(s, fake_with(s, TEXT, read="http_429")).call(req(TEXT)).error == "http_429"


def test_the_guard_applies_to_the_fake_backend_prices_budget_and_gate(tmp_path):
    s = fake_settings(tmp_path)
    register(s, TEXT)
    g = guarded(s, fake_with(s, TEXT, read=reply()))
    assert g.call(req(TEXT)).cost_micro == 100 + 250  # test prices: read US$1 in, US$5 out per million
    s.prices_path.unlink()
    assert g.call(req(TEXT)).error == "budget"  # a missing price table refuses even with the fake backend
    assert budget.total_settled_micro(s) == 350 and g.call(req("x")).error == "gate"


def test_the_result_fields_are_returned_as_the_backend_gave_them(tmp_path):
    s = fake_settings(tmp_path)
    register(s, TEXT)
    r = guarded(s, fake_with(s, TEXT, read=reply())).call(req(TEXT))
    assert r.fields == GOOD_FIELDS and r.in_tok == 100 and r.out_tok == 50 and r.model_id == "fake-x"
