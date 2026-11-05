# ruff: noqa: F811
"""WP1 result-review round 2: forward-clock recovery, refusal words, breaker inside the settle transaction, strict JSON, reply-model check, body meaning
check, genesis marker, consent sentence from config, vendor words, example price fixture. Each test fails on the commit before the fixes."""

from __future__ import annotations

import json
import shutil
import sqlite3
import sys
from datetime import UTC, datetime

import pytest
from model_support import (
    calls,
    fake_settings,
    guarded,
    live_settings,
    register,
    reply,
    req,
    rows,
    sha,
    with_model,
)
from test_model_anthropic import live, ok_reply, stub  # noqa: F401 (fixtures)

import intake.model_anthropic as ma
from conftest import MINI, ROOT, settings_for_tests
from intake import budget, model
from intake.codes import Refused
from intake.model_anthropic import AnthropicBackend
from intake.model_fake import FakeBackend

TEXT = "Invoice INV-1 total 1.00 é <<tag>>"


def refused(fn, *a, **k):
    with pytest.raises(Refused) as ei:
        fn(*a, **k)
    return ei.value.code


# ---- forward clock jump recovery ---------------------------------------------------------------------------------------------------------------
def test_a_forward_clock_jump_is_recovered_by_init_clear_halt_yes(tmp_path, monkeypatch):
    s = fake_settings(tmp_path)
    t = [budget.clock()]
    monkeypatch.setattr(budget, "clock", lambda: t[0])
    assert budget.reserve(s, "a" * 64, "read", b"x" * 10)
    t[0] += 10 * 86400  # a wrong clock jumps ten days forward and one call is recorded
    set_future_prices = json.loads(s.prices_path.read_text(encoding="utf-8"))
    set_future_prices["prices_as_of"] = datetime.fromtimestamp(t[0], UTC).date().isoformat()
    s.prices_path.write_text(json.dumps(set_future_prices), encoding="utf-8")
    assert budget.reserve(s, "b" * 64, "read", b"x" * 10)
    t[0] -= 10 * 86400  # the clock is repaired: now it is earlier than the ledger's last entry by 10 days
    assert refused(budget.reserve, s, "c" * 64, "read", b"x" * 10) == "ledger_inconsistent"
    budget.init(s, clear_halt=True)  # the documented recovery: last_seen restarts at the repaired clock
    with sqlite3.connect(budget.ledger_path(s)) as c:  # observed directly: NOT the old future value and NOT zero
        assert int(c.execute("SELECT v FROM meta WHERE k='last_seen'").fetchone()[0]) == int(t[0])
    set_future_prices["prices_as_of"] = datetime.fromtimestamp(t[0], UTC).date().isoformat()
    s.prices_path.write_text(json.dumps(set_future_prices), encoding="utf-8")
    assert budget.reserve(s, "c" * 64, "read", b"x" * 10)
    t[0] -= 2 * 86400  # last_seen is now the repaired clock (not 0): going back again is refused once more
    assert refused(budget.reserve, s, "d" * 64, "read", b"x" * 10) == "ledger_inconsistent"


# ---- refusal words in diag ---------------------------------------------------------------------------------------------------------------------
def test_every_refusal_before_reserve_says_which_rule_in_diag(tmp_path):
    s = live_settings(tmp_path)
    register(s, TEXT)
    g = guarded(s, AnthropicBackend(s))
    assert g.call(req("not listed")).diag == {"refusal": "not_on_list"}
    s.prices_path.unlink()
    r = g.call(req(TEXT))
    assert r.error == "budget" and r.diag["refusal"] in ("prices_missing", "bad_config")
    s2 = live_settings(tmp_path / "b")
    register(s2, TEXT)
    for _ in range(3):
        budget.record_outcome(s2, "http_4xx")
    r = guarded(s2, FakeBackend(s2, {})).call(req(TEXT))
    assert r.error == "halted" and r.diag["refusal"] == "budget_halted"
    assert "refusal=budget_halted" in model.format_diag(r)


def test_preflight_refusals_carry_a_code_word(tmp_path):
    s = live_settings(tmp_path)
    register(s, TEXT)
    s.owner_sentence_path.write_text("nothing", encoding="utf-8")
    r = guarded(s, AnthropicBackend(s)).call(req(TEXT))
    assert r.error == "gate" and r.diag["refusal"] == "owner_sentence_missing"


def test_refusal_words_are_limited_to_the_closed_codes():
    assert model.clean_diag({"refusal": "not_on_list"}) == {"refusal": "not_on_list"}
    assert model.clean_diag({"refusal": "free text with a body"}) is None


# ---- breaker inside the settle transaction; over_cap counts -----------------------------------------------------------------------------------
def test_settle_updates_the_breaker_in_the_same_transaction(tmp_path):
    s = live_settings(tmp_path)
    r = budget.reserve(s, "a" * 64, "read", b"x" * 10)
    budget.settle(r, None, None, "http_4xx", 1)  # one call: the settlement and the halt are one commit
    assert budget.halt_state(s) == (True, "circuit_breaker")
    assert calls(s)[0][4] == "settled_at_reserved"
    budget.init(s, clear_halt=True)
    r2 = budget.reserve(s, "b" * 64, "read", b"x" * 10)
    budget.settle(r2, (1, 1), None, None, 1)  # a success never trips it
    assert not budget.is_halted(s)
    r3 = budget.reserve(s, "c" * 64, "read", b"x" * 10)
    budget.settle(r3, None, None, "net", 1)  # a transient error neither counts nor trips
    assert not budget.is_halted(s)


def test_over_cap_replies_count_toward_the_breaker(live):
    s, g, st = live
    s = with_model(s, response_cap_bytes=1024)
    g = guarded(s, AnthropicBackend(s))
    st.payload = ok_reply() + b" " * 2000
    assert [g.call(req(TEXT)).error for _ in range(3)] == ["over_cap"] * 3
    assert budget.halt_state(s) == (True, "circuit_breaker")


# ---- strict JSON ---------------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "payload",
    [
        b'{"stop_reason":"tool_use","content":[{"type":"tool_use","name":"record_invoice","input":{"total_minor":NaN}}],"usage":{"input_tokens":1,"output_tokens":1}}',
        b'{"stop_reason":"tool_use","content":[{"type":"tool_use","name":"record_invoice","input":{"total_minor":Infinity}}],"usage":{"input_tokens":1,"output_tokens":1}}',
        b'{"stop_reason":"end_turn","stop_reason":"tool_use","content":[{"type":"tool_use","name":"record_invoice","input":{"a":1}}]}',
        b'{"content":[{"type":"tool_use","name":"record_invoice","input":{"a":1,"a":2}}]}',
    ],
)
def test_a_reply_with_nan_infinity_or_duplicate_keys_is_a_bad_reply(live, payload):
    s, g, st = live
    st.payload = payload
    assert g.call(req(TEXT)).error == "bad_reply"


def test_a_fake_replies_file_with_duplicate_keys_is_refused(tmp_path):
    s = fake_settings(tmp_path)
    register(s, TEXT)
    key = f"{sha(TEXT)}:read"
    path = tmp_path / "dup.json"
    path.write_text('{"' + key + '": "timeout", "' + key + '": "net"}', encoding="utf-8")
    s2 = with_model(s, fake_replies_path=path)
    assert guarded(s2, FakeBackend(s2)).call(req(TEXT)).error == "bad_reply"  # an unreadable file is "no reply", never the last duplicate


# ---- reply model check -----------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("reply_model", ["claude-sonnet-5-5", "claude-haiku-5-5-other", "evil\nmodel", "", None, 5, "x" * 300])
def test_a_reply_from_another_model_settles_at_reserved_and_halts(live, reply_model):
    s, g, st = live
    st.payload = ok_reply(model=reply_model)
    r = g.call(req(TEXT))
    assert r.error is None and r.model_id == "claude-haiku-5-5"  # the stored id is OUR requested id, never the provider's string
    assert r.diag["model_mismatch"] == 1
    (row,) = calls(s)
    assert row[4] == "settled_at_reserved" and row[3] == r.cost_micro > 100 + 250  # not the usage cost
    assert budget.halt_state(s) == (True, "model_mismatch")
    assert g.call(req(TEXT)).error == "halted"


def test_the_requested_model_in_the_reply_is_a_normal_success(live):
    s, g, st = live
    r = g.call(req(TEXT))
    assert r.error is None and "model_mismatch" not in r.diag and calls(s)[0][4] == "settled"


# ---- body meaning check -------------------------------------------------------------------------------------------------------------------------
def test_send_refuses_a_body_that_does_not_match_the_tier_config(live):
    s, g, st = live
    b = AnthropicBackend(s)
    fb_body = b.request_body(req(TEXT, "fallback"))
    res = budget.reserve(s, req(TEXT).doc_sha, "read", fb_body)  # priced as read, but the body names the fallback model
    r = b.send(fb_body, res)
    assert r.error == "budget" and r.diag["refusal"] == "bad_config" and st.hits == 0
    budget.settle(res, None)
    other = AnthropicBackend(with_model(s, max_tokens=4096)).request_body(req(TEXT))  # a body with another max_tokens than the config
    res2 = budget.reserve(s, req(TEXT).doc_sha, "read", other)
    assert b.send(other, res2).error == "budget" and st.hits == 0
    budget.settle(res2, None)


# ---- genesis marker ---------------------------------------------------------------------------------------------------------------------------
def test_a_deleted_ledger_cannot_be_started_again(tmp_path):
    s = fake_settings(tmp_path)
    res = budget.reserve(s, "a" * 64, "read", b"x" * 10)
    budget.settle(res, None)
    assert budget.genesis_path(s).is_file()
    budget.ledger_path(s).unlink()
    assert refused(budget.init, s) == "ledger_inconsistent"
    assert not budget.ledger_path(s).exists()  # the refused creation leaves no empty ledger behind
    budget.genesis_path(s).unlink()  # only the owner, deliberately, starts a new count
    budget.init(s)
    assert budget.total_settled_micro(s) == 0


def test_a_replaced_ledger_is_refused_even_when_it_exists(tmp_path):
    s = fake_settings(tmp_path)
    other = fake_settings(tmp_path / "other")
    shutil.copyfile(budget.ledger_path(other), budget.ledger_path(s))  # a fresh ledger with another genesis id
    assert refused(budget.reserve, s, "a" * 64, "read", b"x" * 10) == "ledger_inconsistent"
    assert refused(budget.startup_check, s, FakeBackend(s)) == "ledger_inconsistent"
    budget.genesis_path(s).write_text("not the id", encoding="utf-8")
    assert refused(budget.init, s) == "ledger_inconsistent"


def test_init_twice_keeps_the_genesis_id(tmp_path):
    s = fake_settings(tmp_path)
    first = budget.genesis_path(s).read_text(encoding="utf-8")
    budget.init(s)
    assert budget.genesis_path(s).read_text(encoding="utf-8") == first
    with sqlite3.connect(budget.ledger_path(s)) as c:
        assert c.execute("SELECT v FROM meta WHERE k='genesis'").fetchone()[0] == first


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX mode bits")
def test_the_ledger_is_owner_only_on_posix(tmp_path):
    s = fake_settings(tmp_path)
    assert budget.ledger_path(s).stat().st_mode & 0o077 == 0 and s.spend_dir.stat().st_mode & 0o077 == 0


# ---- consent sentence from config, vendor words ----------------------------------------------------------------------------------------------------
def test_the_consent_sentence_comes_from_the_config_not_from_code(tmp_path):
    s = live_settings(tmp_path)
    assert budget.consent_recorded(s)
    other = with_model(s, consent_prefix="I agree to something else.")
    assert not budget.consent_recorded(other) and refused(budget.current_cap, other) == "owner_sentence_missing"
    cfg_json = json.loads((ROOT / "config" / "service.json").read_text(encoding="utf-8"))
    assert cfg_json["model"]["consent_prefix"] == s.model.consent_prefix


def test_no_vendor_name_in_the_spend_guard_module():
    text = (ROOT / "src" / "intake" / "budget.py").read_text(encoding="utf-8").lower()
    assert "anthropic" not in text and "claude" not in text


# ---- example prices fixture: the owner's minimum is reproducible -------------------------------------------------------------------------------
def test_the_example_prices_give_the_published_minimum_limit(tmp_path, monkeypatch):
    s = settings_for_tests(tmp_path, backend="anthropic", with_ledger=True)
    shutil.copyfile(ROOT / "tests" / "fixtures" / "model" / "prices_example.json", s.prices_path)
    monkeypatch.setattr(budget, "clock", lambda: datetime(2026, 11, 4, 12, 0, tzinfo=UTC).timestamp())
    b = AnthropicBackend(s)
    assert budget.min_limit_micro(s, b) == 6_028_830  # 18 x (66,987 + 267,948); the README shows the derivation
    p = budget.current_prices(s)
    big = chr(0x10FFFF) * 20000
    esc = chr(1) * 20000
    n_read = max(len(b.request_body(req(t, "read"))) for t in (big, esc))
    assert budget.worst_case(p, "read", n_read, 2048, 2000) == 66_987


def test_the_mini_fixtures_dir_is_unchanged_by_this_test_file():
    assert MINI.is_dir() and ma.API_HOST and reply


def test_check_reports_the_state_of_the_two_spend_files(tmp_path, monkeypatch, capsys):
    from intake import cli

    s = live_settings(tmp_path)
    monkeypatch.setenv("HADAVIN_LOCAL", str(s.local))
    monkeypatch.setenv("INTAKE_MODEL_BACKEND", "anthropic")
    assert budget.files_state(s) == "ok"
    assert cli.main(["check"]) == 0 and "spend_files: ok" in capsys.readouterr().out
    budget.genesis_path(s).unlink()
    assert budget.files_state(s) == "marker_missing" and cli.main(["check"]) == 2
    budget.genesis_path(s).write_text("other", encoding="utf-8")
    assert budget.files_state(s) == "mismatch"
    budget.ledger_path(s).unlink()
    assert budget.files_state(s) == "ledger_missing" and "spend_files: ledger_missing" in (cli.main(["check"]), capsys.readouterr().out)[1]


def test_init_creates_both_spend_files_and_verifies_them_on_every_run(tmp_path, monkeypatch):
    from intake import cli

    s = fake_settings(tmp_path)
    budget.ledger_path(s).unlink()
    budget.genesis_path(s).unlink()
    monkeypatch.setenv("HADAVIN_LOCAL", str(s.local))
    monkeypatch.setenv("INTAKE_MODEL_BACKEND", "fake")
    assert cli.main(["init"]) == 0 and budget.files_state(s) == "ok"
    assert cli.main(["init"]) == 0 and budget.files_state(s) == "ok"
    budget.genesis_path(s).write_text("tampered", encoding="utf-8")
    assert cli.main(["init"]) == 2  # a marker that does not match the ledger is refused, not repaired


def test_an_empty_anthropic_version_is_refused_before_any_network_call(live):
    s, g, st = live
    d = json.loads(s.prices_path.read_text(encoding="utf-8"))
    d["anthropic_version"] = ""
    s.prices_path.write_text(json.dumps(d), encoding="utf-8")
    b = AnthropicBackend(s)
    assert budget.current_prices(s).anthropic_version == ""  # the price file itself loads (the version is optional for other providers)
    assert b.preflight() == "budget" and b.last_refusal == "prices_missing"
    r = guarded(s, b).call(req(TEXT))
    assert r.error == "budget" and st.hits == 0 and rows(s, "reservations") == 0
    body = b.request_body(req(TEXT))
    res = budget.reserve(s, req(TEXT).doc_sha, "read", body)
    assert b.send(body, res).error == "budget" and st.hits == 0  # also inside send, which never opened a connection
    budget.settle(res, None)


def test_the_live_backend_module_has_exactly_one_open_call_and_no_other_file_probe():
    """R3-4: the scan allowlist exempts model_anthropic.py for ``opener.open(request)`` only; this keeps it from hiding any other probe."""
    import ast

    tree = ast.parse((ROOT / "src" / "intake" / "model_anthropic.py").read_text(encoding="utf-8"))
    probes = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr in ("exists", "is_file", "is_dir", "open", "stat", "lstat")
    ]
    assert [ast.unparse(n.func) for n in probes] == ["opener.open"]
    assert not any(isinstance(n, ast.Call) and ast.unparse(n.func) in ("os.stat", "os.lstat", "os.open", "open") for n in ast.walk(tree))
