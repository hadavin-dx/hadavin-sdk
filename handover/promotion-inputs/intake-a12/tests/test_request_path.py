"""WP2c request path (design B4, errata 69, 70.1, 75.2): the body check in the guard, ``body_unsafe``, the in-extract gate, the keyword-only doubles.
These tests use the test body check; the masking checks themselves are tested with ``mask.BodyCheck``."""

from __future__ import annotations

import ast
import json

import pytest
from model_support import GOOD_FIELDS, calls, fake_settings, fake_with, guarded, plain_check, register, reply, req, rows, sha

from conftest import ROOT, settings_for_tests
from intake import budget, extract, model, reader
from intake.codes import MODEL_ERRORS, ConfigError
from intake.model_fake import FakeBackend

TEXT = "Invoice INV-1 total 1.00"


class Check:
    """A body check with a scripted answer; records what it saw."""

    def __init__(self, document_text, answer=None, raises=None, source_sha=None):
        self.document_text, self.source_sha256 = document_text, source_sha or sha(document_text)
        self.key, self.last_code, self.answer, self.raises, self.bodies = b"", None, answer, raises, []

    def refuse(self, code):
        self.last_code = code

    def __call__(self, body):
        self.bodies.append(body)
        if self.raises:
            raise self.raises
        return self.answer


def test_body_unsafe_is_a_model_error_and_never_falls_back():
    assert "body_unsafe" in MODEL_ERRORS and "body_unsafe" in model.NO_FALLBACK_CODES and not model.fallback_allowed("body_unsafe")


@pytest.mark.parametrize("answer", ["anything", ""])
def test_a_refusing_body_check_costs_nothing(tmp_path, answer):
    s = fake_settings(tmp_path)
    register(s, TEXT)
    c = Check(TEXT, answer=answer)
    r = guarded(s, fake_with(s, TEXT, read=reply())).call(req(TEXT), body_check=c)
    assert r.error == "body_unsafe" and r.cost_micro == 0 and len(c.bodies) == 1
    assert rows(s, "reservations") == 0 and rows(s, "calls") == 0 and budget.total_settled_micro(s) == 0


def test_a_body_check_that_raises_is_body_unsafe_with_no_reservation(tmp_path):
    s = fake_settings(tmp_path)
    register(s, TEXT)
    r = guarded(s, fake_with(s, TEXT, read=reply())).call(req(TEXT), body_check=Check(TEXT, raises=RuntimeError("boom")))
    assert r.error == "body_unsafe" and rows(s, "reservations") == 0


def test_a_config_error_from_the_body_check_passes_through(tmp_path):
    s = fake_settings(tmp_path)
    register(s, TEXT)
    with pytest.raises(ConfigError):
        guarded(s, fake_with(s, TEXT, read=reply())).call(req(TEXT), body_check=Check(TEXT, raises=ConfigError("settle_failed", "x")))


def test_the_body_check_sees_the_exact_bytes_that_are_reserved(tmp_path):
    s = fake_settings(tmp_path)
    register(s, TEXT)
    c = Check(TEXT)
    assert guarded(s, fake_with(s, TEXT, read=reply())).call(req(TEXT), body_check=c).error is None
    assert len(c.bodies) == 1 and json.loads(c.bodies[0]).get("text") == TEXT


def test_body_check_doc_sha_tie(tmp_path):
    """A request whose ``doc_sha`` is not the check's document is refused before the backend builds a body; the check is told why."""
    s = fake_settings(tmp_path)
    register(s, TEXT)
    c = Check(TEXT, source_sha="1" * 64)
    seen = []

    class Spy(FakeBackend):
        def request_body(self, r):
            seen.append(r.tier)
            return super().request_body(r)

    g = guarded(s, Spy(s, {}))
    seen.clear()
    r = g.call(req(TEXT), body_check=c)
    assert r.error == "body_unsafe" and c.last_code == "doc_sha_mismatch" and c.bodies == [] and rows(s, "reservations") == 0
    assert [t for t in seen if t] == []


def test_gate_still_hashes_document_text_not_model_text(tmp_path):
    """The gate hashes ``body_check.document_text``; a model text that is not on the list does not matter, a document that is not on it does."""
    s = fake_settings(tmp_path)
    register(s, TEXT)
    other = "masked: <BANK_1>"
    request = model.ExtractRequest(sha(TEXT), "read", model_text=other)
    ok = guarded(s, fake_with(s, TEXT, read=reply())).call(request, body_check=plain_check(TEXT))
    assert ok.error is None
    bad = guarded(s, fake_with(s, other, read=reply())).call(
        model.ExtractRequest(sha(other), "read", model_text=TEXT), body_check=plain_check(other)
    )
    assert bad.error == "gate"


def test_a_backend_cannot_return_body_unsafe_after_reserve(tmp_path):
    s = fake_settings(tmp_path)
    register(s, TEXT)

    class Liar(FakeBackend):
        def send(self, body, reservation):
            budget.begin_send(reservation, body)
            return model.ModelResult(None, "fake-x", 0, 0, 0, "body_unsafe")

    r = guarded(s, Liar(s, {})).call(req(TEXT), body_check=plain_check(TEXT))
    assert r.error == "bad_reply" and calls(s)[0][4] == "settled_at_reserved"


@pytest.mark.parametrize("value", ["body_unsafe", {"error": "body_unsafe"}, {"error": "body_unsafe", "fields": GOOD_FIELDS}])
def test_fake_backend_cannot_reply_body_unsafe(tmp_path, value):
    s = fake_settings(tmp_path)
    register(s, TEXT)
    r = guarded(s, fake_with(s, TEXT, read=value)).call(req(TEXT), body_check=plain_check(TEXT))
    assert r.error == "bad_reply"


def test_fake_body_carries_masked_text(tmp_path):
    b = FakeBackend(fake_settings(tmp_path))
    d = json.loads(b.request_body(model.ExtractRequest(sha(TEXT), "read", model_text="<EMAIL_1> é")))
    assert d == {"fake": True, "doc_sha": sha(TEXT), "tier": "read", "text": "<EMAIL_1> é"}


def test_extract_request_hides_its_text_in_repr():
    assert "secret" not in repr(model.ExtractRequest("0" * 64, "read", model_text="secret"))


# ---- the in-extract gate -----------------------------------------------------------------------------------------------------------------------
class Never:
    def __init__(self):
        self.n = 0

    def call(self, req, **kw):
        self.n += 1
        raise AssertionError("the model must not be called")


def test_gate_refusal_shape_unchanged(tmp_path):
    """A text that is not on the list is refused inside ``extract_parsed``: the same ProcessedDoc the guard's refusal gave, with no model call."""
    s = settings_for_tests(tmp_path)
    m = Never()
    d = extract.extract_parsed(reader.read("x.txt", b"Invoice INV-9 not listed\n"), m, s, streak=None)
    assert m.n == 0
    assert (d.fields, d.failing_fields, d.cost_micro, d.tier, d.model_id, d.error) == (None, (), 0, "read", None, "gate")
    assert d.calls == (extract.CallInfo("read", None, 0, 0, 0, "gate", (), "not_on_list"),) and d.refusal == "not_on_list"
    d1 = extract.extract_parsed(reader.read("x.txt", b"Invoice INV-9 not listed\n"), m, s, tiers=("read",), streak=None)
    assert d1.tier == "read" and d1.error == "gate"


def test_flagged_files_are_not_gated_and_not_sent(tmp_path):
    s = settings_for_tests(tmp_path)
    m = Never()
    d = extract.extract_parsed(reader.read("x.txt", b"a\x00b"), m, s, streak=None)
    assert m.n == 0 and d.parsed.flag is not None and d.error is None and d.calls == ()


# ---- AST rules ---------------------------------------------------------------------------------------------------------------------------------
def _py(*parts):
    return sorted((ROOT.joinpath(*parts)).rglob("*.py"))


def test_doubles_accept_keywords():
    """Every test double with ``def call(self, req ...)`` accepts ``**kw``, because the real guard takes ``body_check`` by keyword."""
    bad = []
    for p in _py("tests"):
        for node in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(node, ast.FunctionDef) and node.name == "call" and [a.arg for a in node.args.args][:2] == ["self", "req"]:
                if node.args.kwarg is None:
                    bad.append(f"{p.name}:{node.lineno}")
    assert bad == []


def test_extract_request_is_built_only_where_the_design_allows():
    for p in _py("src", "intake"):
        if p.name not in {"extract.py", "budget.py", "tracelog.py"}:  # tracelog rebuilds the request on purpose (masked_request)
            assert "ExtractRequest(" not in p.read_text(encoding="utf-8"), p.name


def test_plain_check_is_defined_and_used_only_under_tests():
    for p in _py("src", "intake"):
        assert "plain_check" not in p.read_text(encoding="utf-8"), p.name


def test_model_call_needs_the_body_check_keyword():
    import inspect

    p = inspect.signature(model.GuardedModel.call).parameters["body_check"]
    assert p.kind is inspect.Parameter.KEYWORD_ONLY and p.default is inspect.Parameter.empty
