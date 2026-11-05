"""DF5 A12 batch 3: spend brakes for replies that do not read the invoice (prose, hostile shapes), the persistent transport streak and its cooldown,
the stop on refusals that repeat for every document, the L03 reason, stop reason in the calls table, late 429, geography and nested cache counts."""

from __future__ import annotations

import sqlite3
import threading

import pytest
from model_support import Scripted, err, ok
from test_df5 import GOOD, _prose, _run_live

from conftest import MINI, settings_for_tests
from intake import budget, extract, pipeline, reader
from intake.extract import CallInfo, ProcessedDoc
from intake.model import ModelResult

A_RAW = (MINI / "inv-A.txt").read_bytes()
GOOD_REPLY = ModelResult(GOOD, "claude-sonnet-5-5", 100, 50, 0, None, {"status": 200, "stop_reason": "tool_use"})


def _hostile(code="bad_reply", stop="tool_use"):
    return ModelResult(None, "claude-sonnet-5-5", 100, 50, 0, code, {"status": 200, "stop_reason": stop})


# ---- prose counter ----------------------------------------------------------------------------------------------------------------------------
def test_ten_prose_documents_halt_nine_do_not(tmp_path):
    s, out, _ = _run_live(tmp_path, [_prose("end_turn")] * 9)
    assert budget.halt_state(s)[0] is False
    s2, out2, _ = _run_live(tmp_path / "b", [_prose("end_turn")] * 10)
    assert budget.halt_state(s2) == (True, "prose_streak")


def test_a_valid_tool_reply_resets_the_prose_count(tmp_path):
    s, out, _ = _run_live(tmp_path, [_prose("refusal")] * 9 + [GOOD_REPLY] + [_prose("refusal")] * 9)
    assert budget.halt_state(s)[0] is False and out[9].error is None


def test_the_prose_count_survives_a_restart(tmp_path):  # a new guard (new process) on the same ledger continues the count
    s, _, _ = _run_live(tmp_path, [_prose("end_turn")] * 6)
    assert budget.halt_state(s)[0] is False
    _run_live(tmp_path, [_prose("end_turn")] * 4, s=s, offset=100)
    assert budget.halt_state(s) == (True, "prose_streak")


def test_the_prose_limit_is_a_setting(tmp_path):
    from model_support import live_settings, with_model

    s = with_model(live_settings(tmp_path), prose_streak_limit=2)
    _run_live(tmp_path, [_prose("end_turn")] * 2, s=s)
    assert budget.halt_state(s) == (True, "prose_streak")


# ---- hostile-shaped counter -------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "result",
    [
        _hostile("max_tokens", "max_tokens"),
        _hostile("bad_reply", "tool_use"),
        _hostile("bad_reply", "stop_sequence"),
        _hostile("bad_reply", "model_context_window_exceeded"),
    ],
    ids=["max_tokens", "wrong_shape_tool_use", "stop_sequence", "context_window"],
)
def test_three_hostile_shaped_replies_halt_with_their_own_reason(tmp_path, result):
    s, out, _ = _run_live(tmp_path, [result] * 2)
    assert budget.halt_state(s)[0] is False
    s2, out2, _ = _run_live(tmp_path / "b", [result] * 3)
    assert budget.halt_state(s2) == (True, "hostile_streak")
    assert all(r.cost_micro < 1000 for r in out2)  # still settled at the actual usage


def test_a_valid_reply_resets_the_hostile_count(tmp_path):
    h = _hostile("max_tokens", "max_tokens")
    s, out, _ = _run_live(tmp_path, [h, h, GOOD_REPLY, h, h])
    assert budget.halt_state(s)[0] is False


def test_an_unreadable_reply_still_feeds_the_circuit_breaker(tmp_path):  # PIN: no stop reason at all
    bad = ModelResult(None, "claude-sonnet-5-5", 100, 50, 0, "bad_reply", {"status": 200})
    s, out, _ = _run_live(tmp_path, [bad] * 3)
    assert budget.halt_state(s) == (True, "circuit_breaker")


def test_max_tokens_is_no_longer_a_breaker_code():
    assert "max_tokens" not in budget.BREAKER_CODES


def test_the_stop_reason_word_is_stored_in_the_calls_table(tmp_path):
    s, _, _ = _run_live(tmp_path, [_prose("end_turn"), _hostile("bad_reply", "weird_new_word"), GOOD_REPLY])
    c = sqlite3.connect(budget.ledger_path(s))
    try:
        rows = [r[0] for r in c.execute("SELECT stop_reason FROM calls ORDER BY id")]
    finally:
        c.close()
    assert rows == ["end_turn", "other", "tool_use"]  # an unknown word is stored as "other", never as free text


def test_an_old_ledger_without_the_column_gets_it_when_settling(tmp_path):
    from model_support import live_settings

    s = live_settings(tmp_path)
    c = sqlite3.connect(budget.ledger_path(s))
    c.execute("ALTER TABLE calls DROP COLUMN stop_reason")
    c.commit()
    c.close()
    try:
        _run_live(tmp_path, [GOOD_REPLY], s=s)
    except Exception as e:  # noqa: BLE001
        pytest.fail(f"settling on an old ledger crashed: {type(e).__name__}")
    c = sqlite3.connect(budget.ledger_path(s))
    try:
        assert c.execute("SELECT stop_reason FROM calls").fetchall() == [("tool_use",)]
    finally:
        c.close()


# ---- the person sees a distinct reason --------------------------------------------------------------------------------------------------------
class _Reply:
    def __init__(self, error, diag):
        self.error, self.diag = error, diag

    def call(self, req, **kw):
        return ModelResult(None, None, 1, 1, 1, self.error, self.diag)


def _process(tmp_path, error, diag):
    from model_support import register

    s = settings_for_tests(tmp_path)
    suppliers = pipeline.load_suppliers(s.intake_home / "suppliers.csv")
    parsed = reader.read("p.txt", A_RAW)
    register(s, parsed.text)
    return pipeline.process(s, parsed, _Reply(error, diag), suppliers, streak=None)


def test_a_prose_reply_is_flag_l03_not_the_outage_flag(tmp_path):
    item = _process(tmp_path, "bad_reply", {"stop_reason": "end_turn"})
    assert item.flags == ("L03",)


def test_an_outage_is_still_l02(tmp_path):
    assert _process(tmp_path, "timeout", None).flags == ("L02",)
    assert _process(tmp_path / "b", "bad_reply", {"stop_reason": "tool_use"}).flags == ("L02",)  # a wrong shape is not "prose"


def test_l03_has_a_page_sentence():
    from intake import flags, phrases

    assert flags.FLAGS["L03"].meaning in phrases.texts() and flags.is_reject_only("L03")


# ---- persistent transport streak, cooldown, refusals that repeat -------------------------------------------------------------------------------
def _calls(*errs, refusal=None):
    return tuple(CallInfo("read", None, 0, 0, 0, e, (), refusal) for e in errs)


def _d(*errs, refusal=None, error="X"):
    parsed = reader.read("inv-A.txt", A_RAW)
    last = errs[-1] if errs else None
    return ProcessedDoc(
        parsed, None, (), 0, "read", None, "sha", last if error == "X" else error, _calls(*errs, refusal=refusal), refusal=refusal
    )


@pytest.fixture
def ls(tmp_path):
    from model_support import live_settings

    return live_settings(tmp_path)


def test_the_transport_count_is_persisted_and_continues_after_a_restart(ls):
    t1 = extract.TransportStreak(ls)
    assert t1.add(_d("timeout", "timeout")) is False  # two calls
    t2 = extract.TransportStreak(ls)  # a new process
    assert t2.add(_d("net", "net")) is False and t2.n == 4
    assert t2.add(_d("tls")) is True and t2.stop


def test_a_pause_longer_than_the_window_restarts_the_count(ls, monkeypatch):
    t = extract.TransportStreak(ls)
    t.add(_d("timeout", "timeout", "timeout"))
    now = budget.clock()
    monkeypatch.setattr(budget, "clock", lambda: now + ls.model.transport_window_s + 1)
    t2 = extract.TransportStreak(ls)
    t2.add(_d("net"))
    assert t2.n == 1


def test_the_limit_starts_a_cooldown_that_refuses_new_reserves_until_it_ends(ls, monkeypatch):
    from intake.codes import Refused

    t = extract.TransportStreak(ls)
    t.add(_d("timeout", "timeout", "timeout", "timeout", "timeout"))
    with pytest.raises(Refused) as e:
        budget.reserve(ls, "a" * 64, "read", b"x")
    assert e.value.code == "transport_cooldown"
    now = budget.clock()
    monkeypatch.setattr(budget, "clock", lambda: now + ls.model.transport_cooldown_s + 1)
    # past the cooldown the transport refusal is gone (another refusal or a reservation may follow, never this one)
    try:
        budget.reserve(ls, "a" * 64, "read", b"x")
    except Refused as e2:
        assert e2.code != "transport_cooldown"


def test_a_successful_call_resets_the_persisted_count(ls):
    t = extract.TransportStreak(ls)
    t.add(_d("timeout", "timeout", "timeout", "timeout"))
    t.add(_d("net", None))  # the second call reached the provider and answered
    assert t.n == 0 and t.stop is False


def test_add_is_idempotent_per_document_object(ls):
    t = extract.TransportStreak(ls)
    d = _d("timeout", "timeout")
    t.add(d)
    t.add(d)
    t.add(d)
    assert t.n == 2


def test_add_is_thread_safe(tmp_path):
    t = extract.TransportStreak()
    docs = [_d("timeout") for _ in range(4)]
    ths = [threading.Thread(target=t.add, args=(d,)) for d in docs]
    [x.start() for x in ths]
    [x.join() for x in ths]
    assert t.n == 4


def test_prev_429_follows_the_last_call_that_reached_the_provider():
    t = extract.TransportStreak()
    t.add(_d("timeout", "http_429"))  # the fallback-tier 429 after a first-call timeout counts
    assert t.prev_429 is True
    t.add(_d("gate", error="gate"))  # a document that never left the machine does not overwrite it
    assert t.prev_429 is True
    t.add(_d("http_429", None))  # the document recovered: its last call answered
    assert t.prev_429 is False


@pytest.mark.parametrize(
    "refusal",
    [
        "ledger_missing",
        "prices_missing",
        "ledger_inconsistent",
        "provider_limit_missing",
        "owner_sentence_missing",
        "transport_cooldown",
        "budget_total",
    ],
)
def test_a_refusal_that_repeats_for_every_document_stops_the_scan(refusal):  # FAIL-BEFORE: only the wall codes stopped it
    t = extract.TransportStreak()
    assert t.add(_d("budget", refusal=refusal, error="budget")) is True and t.wall


def test_an_isolated_refusal_does_not_stop_the_scan():
    t = extract.TransportStreak()
    assert t.add(_d("budget", refusal="bad_config", error="budget")) is False


def test_a_ledger_that_cannot_be_written_stops_the_scan(tmp_path):
    s = settings_for_tests(tmp_path)  # no ledger at all
    t = extract.TransportStreak(s)
    assert t.add(_d("timeout")) is True and t.wall


def test_a_scan_over_a_missing_ledger_stops_at_the_first_document(tmp_path):
    from model_support import register

    s = settings_for_tests(tmp_path)
    suppliers = pipeline.load_suppliers(s.intake_home / "suppliers.csv")
    seen = []

    class M:
        def call(self, req, **kw):
            seen.append(1)
            return ModelResult(None, None, 0, 0, 0, "budget", {"refusal": "ledger_missing"})

    t = extract.TransportStreak()
    for i in range(5):
        parsed = reader.read(f"s{i}.txt", A_RAW + f"\nn{i}".encode())
        register(s, parsed.text)
        pipeline.process(s, parsed, M(), suppliers, streak=t)
        if t.stop:
            break
    assert len(seen) == 1


# ---- second try rules --------------------------------------------------------------------------------------------------------------------------
def test_a_fallback_tier_429_after_a_timeout_makes_the_next_document_skip_its_second_call(tmp_path):
    s = settings_for_tests(tmp_path)
    t = extract.TransportStreak()
    d1 = extract.extract_parsed(
        reader.read("inv-A.txt", A_RAW), Scripted(err("timeout", 1), err("http_429", 1, {"retry_after_s": 1})), s, streak=t
    )
    t.add(d1)
    m2 = Scripted(err("http_429", 1, {"retry_after_s": 1}), None)
    extract.extract_parsed(reader.read("inv-A.txt", A_RAW), m2, s, streak=t)
    assert [c.tier for c in m2.calls] == ["read"]


def test_a_good_second_call_after_a_429_leaves_no_repeat_flag(tmp_path):
    s = settings_for_tests(tmp_path)
    t = extract.TransportStreak()
    t.add(
        extract.extract_parsed(
            reader.read("inv-A.txt", A_RAW), Scripted(err("http_429", 1, {"retry_after_s": 1}), ok(GOOD, 3)), s, streak=t
        )
    )
    assert t.prev_429 is False


# ---- provider replies: geography, nested cache counts, late 429 ---------------------------------------------------------------------------------
def _reply(usage):
    from test_model_anthropic import reply_bytes

    import intake.model_anthropic as ma

    return ma.parse_reply(reply_bytes(usage={"input_tokens": 10, "output_tokens": 5, **usage}), "claude-sonnet-5-5")


@pytest.mark.parametrize(
    "geo,odd",
    [("global", False), (None, False), ("not_available", False), ("us", True), ("eu", True), ("apac", False), ("somewhere_new", False)],
)
def test_only_a_region_with_a_known_price_effect_is_odd(geo, odd):  # FAIL-BEFORE: any non-global value halted the ledger
    r = _reply({} if geo is None else {"inference_geo": geo})
    assert (r.diag.get("usage_odd") == 1) is odd
    if geo not in (None,):
        assert r.diag.get("inference_geo") == geo  # recorded for the canary either way


@pytest.mark.parametrize(
    "cc,odd",
    [
        ({"ephemeral_5m_input_tokens": 0, "ephemeral_1h_input_tokens": 0}, False),
        ({"ephemeral_5m_input_tokens": 5}, True),
        ({"ephemeral_1h_input_tokens": 1}, True),
        ({"ephemeral_5m_input_tokens": "x"}, True),
        ("x", True),
        (None, False),
    ],
)
def test_nested_cache_creation_counts_follow_the_flat_rule(cc, odd):  # FAIL-BEFORE: never read
    u = {} if cc is None else {"cache_creation": cc}
    assert (_reply(u).diag.get("usage_odd") == 1) is odd


def test_a_late_429_body_is_http_429_without_retry_not_a_hostile_reply(tmp_path, monkeypatch):  # FAIL-BEFORE: mapped to http_4xx
    from model_support import guarded, live_settings, register
    from test_model_anthropic import TEXT, Stub, plain_check, req, with_model  # noqa: F401

    import intake.model_anthropic as ma
    from intake.model_anthropic import AnthropicBackend

    st = Stub()
    try:
        st.mode = "dribble429"
        monkeypatch.setattr(ma, "_SCHEME", "http")
        monkeypatch.setattr(ma, "_PORT", str(st.port))
        monkeypatch.setattr(ma, "API_HOST", "127.0.0.1")
        s = with_model(live_settings(tmp_path), api_host="127.0.0.1", deadline_s=2)
        register(s, TEXT)
        r = guarded(s, AnthropicBackend(s)).call(req(TEXT), body_check=plain_check(TEXT))
        assert r.error == "http_429" and r.diag.get("odd_429") == 1
        assert extract._wait_s("http_429", r.diag, s.model) is None
    finally:
        st.close()


# ---- the reachable halt-reason overwrites (B2 owns the fix) -------------------------------------------------------------------------------------
def _two_open(s):
    return budget.reserve(s, "a" * 64, "read", b"x" * 40, True), budget.reserve(s, "b" * 64, "read", b"y" * 40, True)


@pytest.mark.xfail(
    strict=True, reason="2026-11-05 B2 owns Z3 _halt: estimate_exceeded set by settle is overwritten by circuit_breaker in the same settle"
)
def test_estimate_exceeded_is_not_overwritten_by_the_breaker_on_the_same_settle(ls):
    r1, _ = _two_open(ls)
    budget.settle(r1, (10**6, 10**6), "m", "bad_reply", 1)  # actual cost above the reservation, and the breaker threshold reached
    assert budget.halt_state(ls) == (True, "estimate_exceeded")


@pytest.mark.xfail(
    strict=True,
    reason="2026-11-05 B2 owns Z3 _halt: provider_limit is overwritten by a breaker trip from a settle that was already in flight",
)
def test_provider_limit_is_not_overwritten_by_a_later_settle(ls):
    r1, r2 = _two_open(ls)
    budget.settle(r1, None, "m", "provider_limit", 1, "provider_limit")
    budget.settle(r2, None, "m", "bad_reply", 1)
    assert budget.halt_state(ls) == (True, "provider_limit")


def test_a_document_that_never_reached_the_provider_has_a_file_hash_and_no_sent_hash(tmp_path):
    s = settings_for_tests(tmp_path)
    (s.intake_home / "synthetic_hashes.txt").write_text("", encoding="utf-8")  # the data gate refuses before any request is built
    d = extract.extract_parsed(reader.read("inv-A.txt", A_RAW), Scripted(None), s, streak=None)
    assert d.error == "gate" and d.prompt_sha_sent is None and len(d.prompt_sha_file) == 64 and d.prompt_sha256 == d.prompt_sha_file


def test_a_prose_reply_without_usable_usage_is_not_prose_class_and_feeds_the_breaker(tmp_path):  # kills the usage-guard mutant
    nousage = ModelResult(None, "claude-sonnet-5-5", 0, 0, 0, "bad_reply", {"status": 200, "stop_reason": "end_turn"})
    s, out, _ = _run_live(tmp_path, [nousage] * 3)
    assert budget.halt_state(s) == (True, "hostile_streak")  # an unverifiable well-formed reply: hostile class, settled at the reservation


def test_valid_usage_is_the_one_rule_for_billable_counts():
    assert budget.valid_usage((0, 0)) is None and budget.valid_usage((0, 5)) is None and budget.valid_usage((5, 0)) is None
    assert budget.valid_usage((5, 5)) == (5, 5)
