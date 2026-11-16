# ruff: noqa: F811
"""WP1 result-review round 1: diagnostic side channel, extra_body, circuit breaker, cap source from the backend, model-id/price binding,
minimum check on every call, clock set back, orphan safety, certificate environment, scheme, gate edge cases. Each test fails on the commit before the fixes."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from datetime import timedelta
from json import dumps as _dumps
from pathlib import Path

import pytest
from model_support import (
    GOOD_FIELDS,
    calls,
    fake_settings,
    fake_with,
    guarded,
    live_settings,
    plain_check,
    register,
    reply,
    req,
    rows,
    set_prices,
    set_sentence,
    sha,
    with_model,
)
from test_model_anthropic import Stub, live, ok_reply, stub  # noqa: F401 (fixtures)

import intake.model_anthropic as ma
from conftest import ROOT, fake_secret_values
from intake import budget, cli, model
from intake import settings as cfg
from intake.codes import ConfigError, Refused
from intake.model_anthropic import AnthropicBackend
from intake.model_fake import FakeBackend

TEXT = "Invoice INV-1 total 1.00 é <<tag>>"
KEY = fake_secret_values()["ANTHROPIC_API_KEY"]


def refused_config(fn, *a, **k):
    with pytest.raises(ConfigError) as ei:
        fn(*a, **k)
    return ei.value.code


def refused(fn, *a, **k):
    with pytest.raises(Refused) as ei:
        fn(*a, **k)
    return ei.value.code


# ---- M1: sanitised diagnostic side channel -------------------------------------------------------------------------------------------------
def test_max_tokens_diag_carries_stop_reason_usage_status_and_elapsed(live):
    s, g, st = live
    st.payload = ok_reply(stop_reason="max_tokens", usage={"input_tokens": 321, "output_tokens": 2048})
    r = g.call(req(TEXT), body_check=plain_check(TEXT))
    assert r.error == "max_tokens" and r.cost_micro > 0  # settled at reserved
    assert r.diag["stop_reason"] == "max_tokens" and (r.diag["in_tok"], r.diag["out_tok"]) == (321, 2048) and r.diag["status"] == 200
    assert isinstance(r.diag["elapsed_ms"], int)
    line = model.format_diag(r)
    assert "stop_reason=max_tokens" in line and "out_tok=2048" in line and "error=max_tokens" in line


def test_4xx_diag_keeps_only_the_error_type_word_never_the_body(live):
    s, g, st = live
    st.status, st.payload = 400, json.dumps({"error": {"type": "invalid_request_error", "message": "PRIVATE-BODY-TEXT " + KEY}}).encode()
    r = g.call(req(TEXT), body_check=plain_check(TEXT))
    assert r.error == "http_4xx" and r.diag["status"] == 400 and r.diag["error_type"] == "invalid_request_error"
    out = model.format_diag(r) + repr(r)
    assert "PRIVATE-BODY-TEXT" not in out and KEY not in out
    assert "error_type=invalid_request_error" in model.format_diag(r)


@pytest.mark.parametrize("etype", ["Bad Type!", "x" * 200, "has space", "UPPER", 5, None, ["a"]])
def test_4xx_error_type_that_is_not_a_plain_word_is_dropped(live, etype):
    s, g, st = live
    st.status, st.payload = 401, json.dumps({"error": {"type": etype}}).encode()
    r = g.call(req(TEXT), body_check=plain_check(TEXT))
    assert r.error == "http_4xx" and "error_type" not in r.diag and r.diag["status"] == 401


def test_5xx_and_429_diag_has_status_only(live):
    s, g, st = live
    st.status, st.payload = 503, json.dumps({"error": {"type": "overloaded_error"}}).encode()
    r = g.call(req(TEXT), body_check=plain_check(TEXT))
    assert r.error == "http_5xx" and r.diag["status"] == 503 and "error_type" not in r.diag


def test_success_and_bad_reply_diag(live):
    s, g, st = live
    r = g.call(req(TEXT), body_check=plain_check(TEXT))
    assert r.error is None and (r.diag["in_tok"], r.diag["out_tok"], r.diag["status"], r.diag["stop_reason"]) == (100, 50, 200, "tool_use")
    st.payload = ok_reply(content=[{"type": "text", "text": "hello"}], stop_reason="end_turn")
    r2 = g.call(req(TEXT), body_check=plain_check(TEXT))
    assert r2.error == "bad_reply" and r2.diag["stop_reason"] == "end_turn"


def test_clean_diag_drops_everything_but_the_allowed_keys_and_shapes():
    d = model.clean_diag(
        {"status": 400, "body": "SECRET", "stop_reason": "end_turn", "error_type": "x y", "in_tok": True, "elapsed_ms": -1, "out_tok": 5}
    )
    assert d == {"status": 400, "stop_reason": "end_turn", "out_tok": 5}
    assert model.clean_diag("x") is None and model.clean_diag({}) is None
    r = model.ModelResult(None, "evil id with spaces\n" + KEY, 0, 0, 0, "net", {"status": 1})
    assert KEY not in model.format_diag(r) and "model_id=n/a" in model.format_diag(r)


def test_the_fake_backend_results_have_no_diag_by_default(tmp_path):
    s = fake_settings(tmp_path)
    register(s, TEXT)
    assert guarded(s, fake_with(s, TEXT, read=reply())).call(req(TEXT), body_check=plain_check(TEXT)).diag is None


# ---- M2: model.extra_body ------------------------------------------------------------------------------------------------------------------
def _parse(extra):
    data = cfg.read_config()
    data["model"]["extra_body"] = extra
    return cfg._parse_config(data, ROOT)  # noqa: SLF001


def _per_tier(read=None, fallback=None):
    return {"read": {} if read is None else read, "fallback": {} if fallback is None else fallback}


def _parse_ok(extra):
    try:
        return _parse(extra)[0].extra_body
    except ConfigError:
        return "refused"


def _refused(extra) -> bool:
    try:
        _parse(extra)
    except ConfigError:
        return True
    except Exception:  # noqa: BLE001 (a crash is not a refusal: the caller's assertion then fails by value)
        return False
    return False


def test_settings_only_checks_that_extra_body_is_a_small_json_object_per_tier():
    assert _parse_ok(_per_tier({"anything": 1})) == _per_tier({"anything": 1})  # which keys are valid is the backend's rule
    assert _parse_ok(_per_tier()) == _per_tier()
    for bad in ([], "x", None, _per_tier({"k": "x" * 600}), {"read": []}, {"read": {}}, {"read": {}, "fallback": [], "extra": {}}):
        assert _refused(bad), bad
    assert _refused(_per_tier({"thinking": {"v": float("nan")}}))


def test_old_flat_extra_body_refused():
    for flat in ({}, {"thinking": {"type": "disabled"}}, {"anything": 1}):
        assert _refused(flat), flat


def test_extra_body_512_per_tier():
    ok = {"k": "x" * 480}  # 512 bytes serialised is the per-tier bound, not a bound on the pair
    assert len(_dumps(ok)) <= 512
    assert _parse_ok(_per_tier(ok, ok)) == _per_tier(ok, ok)
    assert _refused(_per_tier(ok, {"k": "x" * 520}))
    assert _refused(_per_tier({"k": "x" * 520}, ok))


GOOD_EXTRA = [{}, {"thinking": {"type": "between_tools"}}]  # for claude-sonnet-5-5 (the model of both tiers in the demo config)
BAD_EXTRA = [
    {"effort": "low"},
    {"output_config": {"effort": "low"}},
    {"temperature": 0},
    {"temperature": 1},
    {"top_p": 0.9},
    {"top_k": 5},
    {"inference_geo": "us"},
    {"model": "evil"},
    {"max_tokens": 5},
    {"tools": []},
    {"tool_choice": {"type": "tool", "name": "record_invoice"}},
    {"thinking": {"type": "adaptive"}},
    {"thinking": {"type": "disabled"}},  # HTTP 400 on Sonnet 5.5: the provider names between_tools instead
    {"thinking": {"type": "enabled", "budget_tokens": 1024}},
    {"thinking": {"type": "between_tools", "display": "omitted"}},  # between_tools takes no other field
    {"thinking": {"type": "between_tools", "budget_tokens": 2000}},
    {"thinking": {"type": "enabled"}},
    {"thinking": "between_tools"},
    {"thinking": {"type": "between_tools"}, "effort": "low"},
    {"thinking": {}},
]


@pytest.mark.parametrize("extra", GOOD_EXTRA)
@pytest.mark.parametrize("tier", ["read", "fallback"])
def test_extra_body_shapes_that_are_proven_are_accepted(tmp_path, extra, tier):
    s0 = live_settings(tmp_path)
    s = with_model(s0, extra_body={**s0.model.extra_body, tier: extra})
    try:
        got = json.loads(AnthropicBackend(s).request_body(req(TEXT, tier))).get("thinking")
    except ConfigError:
        got = "refused"
    assert got == extra.get("thinking")


@pytest.mark.parametrize("extra", BAD_EXTRA)
@pytest.mark.parametrize("tier", ["read", "fallback"])
def test_extra_body_keys_and_values_that_are_not_proven_are_refused_at_construction(tmp_path, extra, tier):
    s0 = live_settings(tmp_path)
    s = with_model(s0, extra_body={**s0.model.extra_body, tier: extra})
    assert refused_config(AnthropicBackend, s) == "bad_config"


def _allowed(model_id, extra) -> bool:
    try:
        ma.validate_extra_body(model_id, extra)
    except (ConfigError, TypeError):  # TypeError: the old function took (extra, max_tokens)
        return False
    return True


def test_the_extra_body_allowlist_is_keyed_by_model_id_not_by_tier():
    assert _allowed("claude-sonnet-5-5", {"thinking": {"type": "between_tools"}})
    assert _allowed("claude-haiku-5-5", {"thinking": {"type": "disabled"}})
    for model_id, extra in (
        ("claude-haiku-5-5", {"thinking": {"type": "between_tools"}}),  # between_tools is Sonnet-only
        ("claude-sonnet-5-5", {"thinking": {"type": "disabled"}}),
        ("claude-opus-5-5", {"thinking": {"type": "disabled"}}),  # Opus 5.5 cannot turn thinking off
        ("claude-opus-5-5", {"thinking": {"type": "between_tools"}}),
        ("unknown-model", {"thinking": {"type": "between_tools"}}),
    ):
        assert not _allowed(model_id, extra), (model_id, extra)
    assert _allowed("claude-opus-5-5", {}) and _allowed("unknown-model", {})


def test_extra_body_is_checked_again_at_the_point_of_use(tmp_path):
    s = live_settings(tmp_path)
    b = AnthropicBackend(s)
    b._s = with_model(s, extra_body=_per_tier({"thinking": {"type": "disabled"}}))  # noqa: SLF001 (settings swapped after construction)
    try:
        b.request_body(req(TEXT))
        raised = False
    except ConfigError:
        raised = True
    assert raised


def test_extra_body_is_part_of_the_priced_body(tmp_path):
    s = live_settings(tmp_path)
    with_tb = AnthropicBackend(s).request_body(req(TEXT))
    s2 = with_model(s, extra_body=_per_tier())
    plain = AnthropicBackend(s2).request_body(req(TEXT))
    assert len(with_tb) > len(plain)
    assert budget.reserve(s, "b" * 64, "read", with_tb).micro >= budget.reserve(s2, "a" * 64, "read", plain).micro


def test_the_request_shape_passes_a_stub_that_validates_it(live):
    s, g, st = live
    st.validate = True
    assert g.call(req(TEXT), body_check=plain_check(TEXT)).error is None  # the shipped body shape is accepted by the validating stub
    s2 = with_model(s, extra_body=_per_tier())
    assert guarded(s2, AnthropicBackend(s2)).call(req(TEXT), body_check=plain_check(TEXT)).error is None
    assert st.check_shape(b"{}") is False
    forced = json.loads(AnthropicBackend(s).request_body(req(TEXT)))
    forced["tool_choice"] = {"type": "tool", "name": "record_invoice"}
    assert st.check_shape(json.dumps(forced).encode()) is False  # what the old code sent: HTTP 400 on Sonnet 5.5


def test_the_committed_config_has_the_new_keys():
    m = cfg.read_config()["model"]
    assert m["extra_body"] == {"read": {"thinking": {"type": "between_tools"}}, "fallback": {"thinking": {"type": "between_tools"}}}
    assert m["consent_prefix"].startswith("YES: ") and m["breaker_failures"] == 3 and "send_temperature" not in m
    assert (m["tiers"]["read"], m["tiers"]["fallback"]) == ("claude-sonnet-5-5", "claude-sonnet-5-5")
    assert (m["fallback_wait_s"], m["fallback_wait_max_s"], m["strict_tool"]) == (2, 10, False)
    assert m["approved_read_models"] == ["claude-sonnet-5-5"] and m["display_names"] == {"claude-sonnet-5-5": "Claude Sonnet 5.5"}


# ---- M3: circuit breaker -------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("kind", ["http_4xx", "bad_reply", "max_tokens"])
def test_three_systematic_failures_in_a_row_halt_the_guard_and_no_fourth_request_is_sent(live, kind):
    s, g, st = live
    if kind == "http_4xx":
        st.status, st.payload = 400, b"{}"
    elif kind == "bad_reply":
        st.payload = b"not json"
    else:
        st.payload = ok_reply(stop_reason="max_tokens")
    assert [g.call(req(TEXT), body_check=plain_check(TEXT)).error for _ in range(3)] == [kind] * 3
    assert budget.is_halted(s) and budget.halt_state(s) == (True, "hostile_streak" if kind == "max_tokens" else "circuit_breaker")
    r = g.call(req(TEXT), body_check=plain_check(TEXT))
    assert r.error == "halted" and st.hits == 3  # the fourth call never reached the network
    assert rows(s, "reservations") == 3


def test_a_success_resets_the_streak_and_transient_errors_neither_count_nor_reset(live):
    s, g, st = live
    st.payload = b"not json"
    assert [g.call(req(TEXT), body_check=plain_check(TEXT)).error for _ in range(2)] == ["bad_reply"] * 2
    st.status, st.payload = 503, b"{}"
    assert g.call(req(TEXT), body_check=plain_check(TEXT)).error == "http_5xx"  # neither counted nor resetting
    st.status, st.payload = 200, b"not json"
    assert g.call(req(TEXT), body_check=plain_check(TEXT)).error == "bad_reply" and budget.is_halted(
        s
    )  # the third systematic failure, the 503 in between did not reset
    budget.init(s, clear_halt=True)
    assert not budget.is_halted(s)
    st.payload = ok_reply()
    assert g.call(req(TEXT), body_check=plain_check(TEXT)).error is None
    st.payload = b"not json"
    assert [g.call(req(TEXT), body_check=plain_check(TEXT)).error for _ in range(2)] == ["bad_reply"] * 2
    st.payload = ok_reply()
    assert g.call(req(TEXT), body_check=plain_check(TEXT)).error is None  # a success after two failures resets
    st.payload = b"not json"
    assert [g.call(req(TEXT), body_check=plain_check(TEXT)).error for _ in range(2)] == ["bad_reply"] * 2 and not budget.is_halted(s)


def test_the_breaker_threshold_is_configurable_and_the_halt_needs_clear_halt_yes(live, monkeypatch):
    s, g, st = live
    s = with_model(s, breaker_failures=1)
    g = guarded(s, AnthropicBackend(s))
    st.status, st.payload = 401, b"{}"
    assert (
        g.call(req(TEXT), body_check=plain_check(TEXT)).error == "http_4xx"
        and g.call(req(TEXT), body_check=plain_check(TEXT)).error == "halted"
    )
    monkeypatch.setenv("HADAVIN_LOCAL", str(s.local))
    monkeypatch.setenv("INTAKE_MODEL_BACKEND", "anthropic")
    assert cli.main(["init", "--clear-halt"]) == 3 and budget.is_halted(s)
    assert cli.main(["init", "--clear-halt", "--yes"]) == 0 and not budget.is_halted(s)
    assert budget.halt_state(s)[0] is False


def test_the_breaker_does_not_apply_to_the_fake_backend(tmp_path):
    s = fake_settings(tmp_path)
    register(s, TEXT)
    g = guarded(s, fake_with(s, TEXT, read=reply("bad_reply")))
    assert [g.call(req(TEXT), body_check=plain_check(TEXT)).error for _ in range(6)] == ["bad_reply"] * 6 and not budget.is_halted(s)


def test_check_reports_the_halt_and_fails(tmp_path, monkeypatch, capsys):
    s = live_settings(tmp_path)
    for _ in range(3):
        budget.record_outcome(s, "http_4xx")
    monkeypatch.setenv("HADAVIN_LOCAL", str(s.local))
    monkeypatch.setenv("INTAKE_MODEL_BACKEND", "anthropic")
    assert cli.main(["check"]) == 2
    assert "halted: yes (circuit_breaker)" in capsys.readouterr().out


# ---- M4: the cap source comes from the backend ---------------------------------------------------------------------------------------------
def test_a_live_backend_under_fake_settings_is_refused_everywhere(tmp_path):
    s = fake_settings(tmp_path)
    assert refused(AnthropicBackend, s) == "bad_config"

    class LiveFake(FakeBackend):
        live = True

    assert refused(guarded, s, LiveFake(s, {})) == "bad_config"


def test_the_reserve_takes_the_cap_source_from_the_backend_flag(tmp_path):
    s = fake_settings(tmp_path)
    s.owner_sentence_path.unlink()
    assert budget.reserve(s, "a" * 64, "read", b"x" * 10).micro > 0  # fake cap: no sentence needed
    assert refused(budget.reserve, s, "b" * 64, "read", b"x" * 10, True) == "owner_sentence_missing"  # live flag from the backend: strict


def test_fake_on_a_real_folder_is_refused_by_the_guard_constructor_not_only_the_factory(tmp_path, monkeypatch):
    s = fake_settings(tmp_path)
    monkeypatch.setattr(cfg, "under_temp_folder", lambda _p: False)
    assert refused(guarded, s, FakeBackend(s, {})) == "fake_on_real_folder"


# ---- M5: model ids bound to the prices -----------------------------------------------------------------------------------------------------
def _edit_prices(s, **changes):
    d = json.loads(s.prices_path.read_text(encoding="utf-8"))
    for k, v in changes.items():
        if v is None:
            d.pop(k, None)
        else:
            d[k] = v
    s.prices_path.write_text(json.dumps(d), encoding="utf-8")


@pytest.mark.parametrize(
    "ids",
    [
        None,
        {},
        {"read": "claude-haiku-5-5"},
        {"read": "claude-sonnet-5-5", "fallback": "claude-haiku-5-5"},
        {"read": "claude-haiku-5-5", "fallback": "other"},
        {"read": 1, "fallback": 2},
    ],
)
def test_prices_for_other_models_or_without_model_ids_refuse(tmp_path, ids):
    s = fake_settings(tmp_path)
    register(s, TEXT)
    g = guarded(s, fake_with(s, TEXT, read=reply()))
    assert g.call(req(TEXT), body_check=plain_check(TEXT)).error is None
    _edit_prices(s, model_ids=ids)
    assert refused(budget.current_prices, s) == "prices_missing"
    assert refused(budget.reserve, s, "a" * 64, "read", b"x" * 10) == "prices_missing"
    assert g.call(req(TEXT), body_check=plain_check(TEXT)).error == "budget"


def test_a_tier_change_in_the_config_without_new_prices_refuses(tmp_path):
    s = fake_settings(tmp_path)
    s2 = with_model(s, tier_read="claude-opus-5-5")
    assert refused(budget.current_prices, s2) == "prices_missing"


def test_check_says_why_the_prices_are_refused_and_when_they_are_from(tmp_path, monkeypatch, capsys):
    s = fake_settings(tmp_path)
    monkeypatch.setenv("HADAVIN_LOCAL", str(s.local))
    monkeypatch.setenv("INTAKE_MODEL_BACKEND", "fake")
    _edit_prices(s, prices_as_of=(budget.today() - timedelta(days=45)).isoformat())
    assert cli.main(["check"]) == 2
    out = capsys.readouterr().out
    assert (
        "prices: missing" in out
        and "prices_problem: prices_as_of is in the future or older than 30 days" in out
        and "prices_as_of: n/a" in out
    )


# ---- minor fixes ---------------------------------------------------------------------------------------------------------------------------
def test_a_text_with_a_lone_surrogate_is_a_gate_refusal_not_an_exception(tmp_path):
    s = fake_settings(tmp_path)
    bad_text = "bad " + chr(0xD800) + " text"
    assert refused(model.gate_check, s, bad_text) == "not_on_list"
    g = guarded(s, FakeBackend(s, {}))
    bad = model.ExtractRequest("0" * 64, "read", model_text=bad_text)  # (the helper req() hashes with utf-8 too, so build it by hand)
    assert g.call(bad, body_check=plain_check(bad_text, "0" * 64)).error == "gate" and rows(s, "reservations") == 0


def test_a_junk_only_list_is_empty_like_check_sees_it(tmp_path):
    s = fake_settings(tmp_path)
    (s.intake_home / "synthetic_hashes.txt").write_text("not a hash\n" + "A" * 64 + "\n", encoding="utf-8")
    assert refused(model.gate_check, s, TEXT) == "real_file_refused"


def test_a_deferred_start_does_not_skip_the_minimum_check(tmp_path):
    s = live_settings(tmp_path)
    s.owner_sentence_path.unlink()

    class Sized(FakeBackend):  # a live-sized body (the real request body) so the 18x figure is the real one
        live = True

        def request_body(self, r):
            return AnthropicBackend(s).request_body(r)

    g = guarded(s, Sized(s, {f"{sha(TEXT)}:read": reply()}))
    assert g.deferred == "owner_sentence_missing"
    register(s, TEXT)
    set_sentence(s, 1)  # now a sentence exists, but US$1 is below the 18x worst case
    budget.confirm_limit(s, "LIMIT SET 1")
    r = g.call(req(TEXT), body_check=plain_check(TEXT))
    assert r.error == "budget" and rows(s, "reservations") == 0
    assert refused(budget.minimum_check, s, Sized(s, {})) == "cap_too_small_for_worst_case"
    set_sentence(s, 100)
    budget.confirm_limit(s, "LIMIT SET 100")
    assert g.call(req(TEXT), body_check=plain_check(TEXT)).error is None


def test_the_largest_text_comes_from_the_masked_cap_and_the_minimum_follows_it(tmp_path, monkeypatch):
    """Since WP2c the bound is the masked-text cap (a mark can be longer than the value it hides), which is not below the policy document cap."""
    from intake import mask

    s = live_settings(tmp_path)
    assert cfg.read_policy_value("max_document_chars") == 20000 and mask.MASKED_MAX_CHARS >= 20000
    b = AnthropicBackend(s)
    full = budget.min_limit_micro(s, b)
    monkeypatch.setattr(mask, "MASKED_MAX_CHARS", 10000)
    assert budget.min_limit_micro(s, b) < full


def test_the_call_deadline_is_capped_at_half_the_orphan_age():
    assert cfg.ORPHAN_AGE_S == 600 and budget.ORPHAN_AGE_S == 600
    ok = cfg.read_config()
    ok["model"]["deadline_s"] = 300
    assert cfg._parse_config(ok, ROOT)[0].deadline_s == 300  # noqa: SLF001
    ok["model"]["deadline_s"] = 301
    with pytest.raises(ConfigError):
        cfg._parse_config(ok, ROOT)  # noqa: SLF001


def test_an_orphan_sweep_never_settles_a_reservation_of_a_call_that_can_still_be_running(tmp_path, monkeypatch):
    s = live_settings(tmp_path)
    s = with_model(s, deadline_s=300)
    now = [1_800_000_000.0]
    monkeypatch.setattr(budget, "clock", lambda: now[0])
    set_prices(s, 1_000_000, 5_000_000, as_of=budget.today().isoformat())
    res = budget.reserve(s, "a" * 64, "read", b"x" * 10)
    budget.begin_send(res, b"x" * 10)
    now[0] += 604  # older than the orphan age but not older than twice the deadline + 5
    assert budget.settle_orphans(s) == 0
    now[0] += 3
    assert budget.settle_orphans(s) == 1
    assert refused(budget.settle, res, (1, 1)) == "ledger_inconsistent"  # the late settle of the swept call is refused, never doubled


def test_a_refused_settle_inside_the_guard_does_not_escape_call(tmp_path):
    s = fake_settings(tmp_path)
    register(s, TEXT)

    class Sweeper(FakeBackend):
        def send(self, body, res):
            out = super().send(body, res)
            budget.settle(res, None)  # something else settled this reservation while the call ran
            return out

    r = guarded(s, Sweeper(s, {f"{sha(TEXT)}:read": reply()})).call(req(TEXT), body_check=plain_check(TEXT))
    assert r.error is None and r.cost_micro > 0
    assert len(calls(s)) == 1  # counted once, at the reserved amount


def test_a_clock_set_back_by_more_than_a_day_is_refused(tmp_path, monkeypatch):
    s = fake_settings(tmp_path)
    t = [budget.clock()]
    monkeypatch.setattr(budget, "clock", lambda: t[0])
    assert budget.reserve(s, "a" * 64, "read", b"x" * 10)
    t[0] -= 3600  # an hour back is tolerated
    assert budget.reserve(s, "b" * 64, "read", b"x" * 10)
    t[0] -= 2 * 86400  # two days back (to make stale prices look fresh)
    assert refused(budget.reserve, s, "c" * 64, "read", b"x" * 10) == "ledger_inconsistent"
    assert refused(budget.startup_check, s, FakeBackend(s)) == "ledger_inconsistent"
    t[0] += 3 * 86400
    assert budget.reserve(s, "d" * 64, "read", b"x" * 10)


def test_plain_http_is_refused_to_a_remote_host_but_loopback_is_allowed(tmp_path, monkeypatch):
    s = live_settings(tmp_path)
    s = with_model(s, api_host="example.com")
    monkeypatch.setattr(ma, "API_HOST", "example.com")
    monkeypatch.setattr(ma, "_SCHEME", "http")
    assert AnthropicBackend(s).preflight() == "budget"  # the key would travel in clear text
    monkeypatch.setattr(ma, "_SCHEME", "https")
    assert AnthropicBackend(s).preflight() is None
    s2 = with_model(s, api_host="127.0.0.1")
    monkeypatch.setattr(ma, "API_HOST", "127.0.0.1")
    monkeypatch.setattr(ma, "_SCHEME", "http")
    assert AnthropicBackend(s2).preflight() is None


@pytest.mark.parametrize("var", ["SSL_CERT_FILE", "SSL_CERT_DIR", "SSLKEYLOGFILE", "OPENSSL_CONF"])
def test_a_certificate_store_override_in_the_environment_is_refused(tmp_path, monkeypatch, var):
    s = live_settings(tmp_path)
    b = AnthropicBackend(s)
    assert b.preflight() is None
    monkeypatch.setenv(var, str(tmp_path))
    assert b.preflight() == "budget"
    register(s, TEXT)
    assert guarded(s, b).call(req(TEXT), body_check=plain_check(TEXT)).error == "budget" and rows(s, "reservations") == 0
    body = b.request_body(req(TEXT))
    res = budget.reserve(s, req(TEXT).doc_sha, "read", body)
    assert b.send(body, res).error == "budget"  # also checked again inside send
    budget.settle(res, None)


def test_the_prompt_file_is_pinned_byte_for_byte():
    p = ROOT / "src" / "intake" / "prompts" / "extract_v1.txt"
    assert hashlib.sha256(p.read_bytes()).hexdigest() == "59ac5c94b89d1e6678f3ffdf90ec372398b78994ddce60a138e706c7a7da0714"
    assert b"\r" not in p.read_bytes()


def test_ledger_texts_and_the_documented_columns(tmp_path):
    s = fake_settings(tmp_path)
    budget.ledger_path(s).unlink()
    with pytest.raises(Refused) as ei:
        budget.reserve(s, "a" * 64, "read", b"x")
    assert "intake check" in ei.value.text
    s = fake_settings(tmp_path / "b")
    c = sqlite3.connect(budget.ledger_path(s))
    try:
        cols = [r[1] for r in c.execute("PRAGMA table_info(reservations)")]
    finally:
        c.close()
    assert {"in_price", "out_price", "body_sha", "body_len"} <= set(cols)
    assert "in_price" in (budget.__doc__ or "") and "SUM(cost_micro)" in (budget.__doc__ or "")


def test_the_fake_backend_prints_no_minimum_in_check(tmp_path, monkeypatch, capsys):
    s = fake_settings(tmp_path)
    monkeypatch.setenv("HADAVIN_LOCAL", str(s.local))
    monkeypatch.setenv("INTAKE_MODEL_BACKEND", "fake")
    assert cli.main(["check"]) == 0
    assert "min_limit_usd: n/a (fake)" in capsys.readouterr().out


def test_unused_imports_are_used():
    assert GOOD_FIELDS and time and Path and Stub
