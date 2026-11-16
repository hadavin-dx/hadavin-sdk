"""Data gate (spec 5.4): only files whose send_text hash is on the made-up list reach the model. Read at the entry of every tier call."""

from __future__ import annotations

import hashlib

import pytest
from model_support import calls, fake_settings, fake_with, guarded, live_settings, plain_check, register, reply, req, rows, sha

from intake import budget, model
from intake.codes import Refused
from intake.model_anthropic import AnthropicBackend
from intake.model_fake import FakeBackend

TEXT = "Invoice INV-1 total 1.00 é"


def listf(s):
    return s.intake_home / "synthetic_hashes.txt"


def test_unlisted_hash_refused(tmp_path):
    s = fake_settings(tmp_path)
    register(s, TEXT)
    g = guarded(s, fake_with(s, "other", read=reply()))
    r = g.call(req("other"), body_check=plain_check("other"))
    assert r.error == "gate" and r.fields is None and r.cost_micro == 0
    with pytest.raises(Refused) as ei:
        model.gate_check(s, "other")
    assert ei.value.code == "not_on_list"
    assert rows(s, "reservations") == 0  # a refusal costs nothing


@pytest.mark.parametrize("content", [None, "", "   \n\t \n\n", "\n"])
def test_empty_list_refuses(tmp_path, content):
    s = fake_settings(tmp_path)
    if content is None:
        listf(s).unlink()
    else:
        listf(s).write_text(content, encoding="utf-8")
    assert model.listed_hashes(s) == frozenset()
    with pytest.raises(Refused) as ei:
        model.gate_check(s, TEXT)
    assert ei.value.code == "real_file_refused"
    g = guarded(s, fake_with(s, TEXT, read=reply()))
    assert g.call(req(TEXT), body_check=plain_check(TEXT)).error == "gate" and rows(s, "reservations") == 0 and rows(s, "calls") == 0


def test_list_lines_tolerate_blank_lines_and_whitespace_and_match_utf8_sha256(tmp_path):
    s = fake_settings(tmp_path)
    listf(s).write_text("\n  " + sha(TEXT) + "  \r\n\n", encoding="utf-8")
    model.gate_check(s, TEXT)  # no exception
    assert sha(TEXT) == hashlib.sha256(TEXT.encode("utf-8")).hexdigest()
    with pytest.raises(Refused):
        model.gate_check(s, TEXT + " ")  # one byte more is another hash


def test_check_and_send_same_bytes(tmp_path):
    """The gate hashes the document text; the backend builds the body from the model text, which here is that same string (no masking yet)."""
    s = fake_settings(tmp_path)
    register(s, TEXT)
    seen = []

    class Spy(FakeBackend):
        def request_body(self, r):
            seen.append(r.model_text)
            return super().request_body(r)

    g = guarded(s, Spy(s, {f"{sha(TEXT)}:read": reply()}))
    seen.clear()  # the constructor builds the maximum-size documents for the start check
    assert g.call(req(TEXT), body_check=plain_check(TEXT)).error is None
    seen[:] = [t for t in seen if len(t) < 1000]  # (the minimum check also builds the maximum-size documents)
    assert seen == [TEXT] and sha(seen[0]) in model.listed_hashes(s)
    seen.clear()  # a text that differs by one character from a listed one never reaches the backend
    assert (
        g.call(req(TEXT.replace("1.00", "1.01")), body_check=plain_check(TEXT.replace("1.00", "1.01"))).error == "gate"
        and [t for t in seen if len(t) < 1000] == []
    )


def test_stop_by_emptying_list_takes_effect(tmp_path):
    """Emptying the list stops the very next call without a restart, including a fallback call after the read call ran."""
    s = fake_settings(tmp_path)
    register(s, TEXT)
    g = guarded(s, fake_with(s, TEXT, read=reply("timeout"), fallback=reply()))
    assert g.call(req(TEXT, "read"), body_check=plain_check(TEXT)).error == "timeout"
    n = rows(s, "calls")
    listf(s).write_text("", encoding="utf-8")  # STOP
    r = g.call(req(TEXT, "fallback"), body_check=plain_check(TEXT))
    assert r.error == "gate" and rows(s, "calls") == n and rows(s, "reservations") == n  # nothing reserved, nothing sent
    register(s, TEXT)  # RESUME
    assert g.call(req(TEXT, "fallback"), body_check=plain_check(TEXT)).error is None


def test_a_gate_refusal_in_the_fallback_tier_does_not_call_the_backend(tmp_path):
    s = fake_settings(tmp_path)
    register(s, TEXT)
    sent = []

    class Spy(FakeBackend):
        def send(self, body, res):
            sent.append(res.tier)
            return super().send(body, res)

    g = guarded(s, Spy(s, {f"{sha(TEXT)}:read": reply("http_5xx"), f"{sha(TEXT)}:fallback": reply()}))
    first = g.call(req(TEXT, "read"), body_check=plain_check(TEXT))
    assert first.error == "http_5xx" and model.fallback_allowed(first.error)
    listf(s).write_text("\n", encoding="utf-8")
    assert g.call(req(TEXT, "fallback"), body_check=plain_check(TEXT)).error == "gate" and sent == ["read"]
    assert calls(s)[0][4] == "settled_at_reserved" and len(calls(s)) == 1


def test_the_gate_costs_nothing_with_a_live_backend_too(tmp_path):
    s = live_settings(tmp_path)  # the list holds the mini hashes only
    g = guarded(s, AnthropicBackend(s))
    assert g.call(req("not listed"), body_check=plain_check("not listed")).error == "gate"
    assert budget.total_settled_micro(s) == 0 and rows(s, "reservations") == 0
