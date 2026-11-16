"""Spend guard (money path, spec 5.5): reserve, settle, caps, prices, ledger checks, one send per reservation, import scans.
Each test is written to fail against a stub that skips its check (see the mutation list in the WP1 report)."""

from __future__ import annotations

import ast
import json
import os
import sqlite3
import subprocess
import sys
import threading
from dataclasses import replace
from datetime import timedelta

import pytest
from model_support import (
    GOOD_FIELDS,
    calls,
    fake_settings,
    fake_with,
    guarded,
    live_settings,
    make_queue,
    register,
    reply,
    req,
    rows,
    set_prices,
    set_sentence,
    sha,
    with_model,
)

from conftest import ROOT, key_file
from intake import budget, cli, model
from intake.codes import MODEL_ERRORS, ConfigError, Refused
from intake.model_anthropic import AnthropicBackend
from intake.model_fake import FakeBackend

TEXT = "Invoice INV-1 total 1.00"


def codes_of(fn, *a):
    with pytest.raises(Refused) as ei:
        fn(*a)
    return ei.value.code


def body(n: int = 10, tag: str = "a") -> bytes:
    return (tag * n).encode()


# ---- cap boundary ---------------------------------------------------------------------------------------------------------------------------
def test_boundary_exactly_at_the_cap_passes_and_one_micro_over_refuses(tmp_path):
    s = live_settings(tmp_path, limit=1, sentence_total=1)
    set_prices(s, 1_000_000, 1_000_000)
    ok = with_model(s, overhead_tokens=1_000_000 - 100 - s.model.max_tokens)
    over = with_model(s, overhead_tokens=1_000_000 - 100 - s.model.max_tokens + 1)
    assert codes_of(budget.reserve, over, "e" * 64, "read", body(100)) == "budget_total"
    assert rows(s, "reservations") == 0  # a refusal writes nothing
    assert budget.reserve(ok, "e" * 64, "read", body(100)).micro == 1_000_000


def test_settled_plus_open_plus_worst_case_is_what_counts(tmp_path):
    s = live_settings(tmp_path, limit=1, sentence_total=1)
    set_prices(s, 1_000_000, 1_000_000)
    s = with_model(s, overhead_tokens=0, max_tokens=400_000)  # worst = body + 400000
    r1 = budget.reserve(s, "a" * 64, "read", body(10))  # 400010 open
    r2 = budget.reserve(s, "b" * 64, "read", body(10))  # 800020 open
    assert codes_of(budget.reserve, s, "c" * 64, "read", body(10)) == "budget_total"
    assert budget.settle(r1, (5, 5)) == 10  # settled small: room again (10 + 400010 + 400010 <= 1e6)
    assert budget.reserve(s, "c" * 64, "read", body(10)).micro == 400_010
    assert budget.settle(r2, None) == 400_010


# ---- races ----------------------------------------------------------------------------------------------------------------------------------
def test_eight_threads_never_pass_the_cap(tmp_path):
    s = live_settings(tmp_path, limit=1, sentence_total=1)
    set_prices(s, 1_000_000, 1_000_000)
    s = with_model(s, overhead_tokens=0, max_tokens=400_000)
    ok, refused, lock = [], [], threading.Lock()

    def go(i):
        try:
            r = budget.reserve(s, f"{i:064d}", "read", body(10))
            with lock:
                ok.append(r.micro)
        except Refused as e:
            with lock:
                refused.append(e.code)

    ts = [threading.Thread(target=go, args=(i,)) for i in range(8)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert len(ok) == 2 and sum(ok) <= 1_000_000 and refused == ["budget_total"] * 6
    assert rows(s, "reservations") == 2


RACE = (
    "import sys\n"
    "from intake import budget, settings\n"
    "from intake.codes import Refused\n"
    "from dataclasses import replace\n"
    "s = settings.load()\n"
    "s = replace(s, model=replace(s.model, overhead_tokens=0, max_tokens=400000))\n"
    "n = 0\n"
    "for i in range(6):\n"
    "    try:\n"
    "        budget.reserve(s, sys.argv[1] + str(i).zfill(60), 'read', b'0123456789'); n += 1\n"
    "    except Refused:\n"
    "        pass\n"
    "print(n)\n"
)


def test_two_processes_racing_never_pass_the_cap(tmp_path):
    s = live_settings(tmp_path, limit=1, sentence_total=1)
    set_prices(s, 1_000_000, 1_000_000)
    env = {**os.environ, "HADAVIN_LOCAL": str(s.local), "INTAKE_MODEL_BACKEND": "anthropic"}
    ps = [subprocess.Popen([sys.executable, "-c", RACE, tag], env=env, stdout=subprocess.PIPE, text=True) for tag in ("aaaa", "bbbb")]
    got = [int(p.communicate(timeout=120)[0]) for p in ps]
    assert sum(got) == 2 and rows(s, "reservations") == 2


# ---- settle rules ---------------------------------------------------------------------------------------------------------------------------
def test_double_settle_is_refused_and_changes_nothing(tmp_path):
    s = live_settings(tmp_path)
    res = budget.reserve(s, "a" * 64, "read", body())
    c1 = budget.settle(res, (10, 10))
    assert codes_of(budget.settle, res, (1, 1)) == "ledger_inconsistent"
    assert [x[3] for x in calls(s)] == [c1] and rows(s, "calls") == 1


def test_settle_without_reserve_is_refused(tmp_path):
    s = live_settings(tmp_path)
    assert (
        codes_of(budget.Reservation, 1, "a" * 64, "read", 5, 10, "x" * 64, str(budget.ledger_path(s))) == "ledger_inconsistent"
    )  # no mint
    forged = budget.Reservation(99, "a" * 64, "read", 5, 10, "x" * 64, str(budget.ledger_path(s)), budget._MINT)  # noqa: SLF001
    assert codes_of(budget.settle, forged, (1, 1)) == "ledger_inconsistent"
    assert codes_of(budget.settle, "not a reservation", (1, 1)) == "ledger_inconsistent"
    res = budget.reserve(s, "a" * 64, "read", body())
    with sqlite3.connect(budget.ledger_path(s)) as c:
        c.execute("DELETE FROM reservations")
    assert codes_of(budget.settle, res, (1, 1)) == "ledger_inconsistent"
    assert rows(s, "calls") == 0


@pytest.mark.parametrize(
    "usage", [None, (0, 0), (0, 5), (5, 0), (-1, 5), ("5", 5), (True, 5), (1.5, 5), (5,), (1, 2, 3), "12", 7, (10**12, 5), {"a": 1}]
)
def test_usage_zero_or_garbage_settles_at_reserved(tmp_path, usage):
    s = live_settings(tmp_path)
    res = budget.reserve(s, "a" * 64, "read", body())
    assert budget.settle(res, usage) == res.micro
    assert calls(s) == [("read", None, None, res.micro, "settled_at_reserved")]
    assert not budget.is_halted(s)


def test_valid_usage_below_the_reservation_is_the_actual_cost_rounded_up(tmp_path):
    s = live_settings(tmp_path)
    set_prices(s, 333_333, 1)
    res = budget.reserve(s, "a" * 64, "read", body())
    assert budget.settle(res, (1, 1)) == 1  # ceil((333333 + 1) / 1e6) = 1, not 0
    set_prices(s, 1_000_000, 5_000_000)
    r2 = budget.reserve(s, "b" * 64, "read", body())
    assert budget.settle(r2, (3, 7)) == 38  # 3 + 35
    assert [x[4] for x in calls(s)] == ["settled", "settled"]


def test_settle_uses_the_prices_of_the_reservation_not_a_later_file(tmp_path):
    s = live_settings(tmp_path)
    set_prices(s, 1_000_000, 1_000_000)
    res = budget.reserve(s, "a" * 64, "read", body())
    set_prices(s, 1, 1)  # prices.json changes (or goes stale) while the call is running
    assert budget.settle(res, (10, 10)) == 20


def test_settle_above_reserved_settles_actual_halts_and_refuses_the_next_reserve(tmp_path, capsys, monkeypatch):
    s = live_settings(tmp_path)
    set_prices(s, 1_000_000, 1_000_000)
    s = with_model(s, overhead_tokens=0, max_tokens=10)
    res = budget.reserve(s, "a" * 64, "read", body(10))  # worst 20
    assert res.micro == 20
    assert budget.settle(res, (1000, 1000)) == 2000  # actual, not the reserved amount
    assert budget.is_halted(s)
    assert codes_of(budget.reserve, s, "b" * 64, "read", body(10)) == "budget_halted"
    monkeypatch.setenv("HADAVIN_LOCAL", str(s.local))
    monkeypatch.setenv("INTAKE_MODEL_BACKEND", "anthropic")
    assert cli.main(["init", "--clear-halt"]) == 3  # --yes is required
    assert budget.is_halted(s)
    assert cli.main(["init", "--clear-halt", "--yes"]) == 0
    assert not budget.is_halted(s) and budget.reserve(s, "b" * 64, "read", body(10)).micro == 20
    assert budget.total_settled_micro(s) == 2000  # the halt did not erase what was spent


def test_orphan_older_than_600s_settles_at_reserved_at_start_and_a_younger_one_still_counts(tmp_path, monkeypatch):
    s = live_settings(tmp_path, limit=1, sentence_total=1)
    set_prices(s, 1_000_000, 1_000_000)
    s = with_model(s, overhead_tokens=0, max_tokens=400_000)
    now = [1_800_000_000.0]
    monkeypatch.setattr(budget, "clock", lambda: now[0])
    set_prices(s, 1_000_000, 1_000_000, as_of=budget.today().isoformat())
    old = budget.reserve(s, "a" * 64, "read", body(10))  # the process "crashes" here: never sent, never settled
    now[0] += 300
    young = budget.reserve(s, "b" * 64, "read", body(10))
    budget.begin_send(young, body(10))  # crashed after the send started
    assert codes_of(budget.reserve, s, "c" * 64, "read", body(10)) == "budget_total"  # both open ones count against the cap
    now[0] += 400  # old is 700 s, young is 400 s
    assert budget.settle_orphans(s) == 1
    assert calls(s) == [("read", None, None, old.micro, "settled_at_reserved")]
    assert codes_of(budget.reserve, s, "c" * 64, "read", body(10)) == "budget_total"  # young still counts
    now[0] += 300
    monkeypatch.setattr(budget, "min_limit_micro", lambda _s, _b: 0)  # this test is about orphans, not the minimum cap
    assert budget.startup_check(s, FakeBackend(s)) is None  # the start settles it too
    assert [c[4] for c in calls(s)] == ["settled_at_reserved"] * 2
    assert budget.total_settled_micro(s) == old.micro + young.micro
    del young


@pytest.mark.parametrize("code", sorted(MODEL_ERRORS))
def test_every_failure_kind_settles_at_reserved(tmp_path, code):
    s = fake_settings(tmp_path)
    register(s, TEXT)
    b = fake_with(s, TEXT, read=reply(error=code, i=10, o=10))  # even with usage numbers present, a failure costs the reservation
    r = guarded(s, b).call(req(TEXT))
    assert r.error == code and r.fields is None
    (row,) = calls(s)
    assert row[4] == "settled_at_reserved" and row[3] == r.cost_micro > 0
    assert rows(s, "reservations") == 1 and budget.total_settled_micro(s) == r.cost_micro


def test_an_exception_in_send_and_a_bad_result_type_settle_at_reserved(tmp_path):
    s = fake_settings(tmp_path)
    register(s, TEXT)

    class Boom(FakeBackend):
        def send(self, body, reservation):
            budget.begin_send(reservation, body)
            raise RuntimeError("boom")

    r = guarded(s, Boom(s, {})).call(req(TEXT))
    assert r.error == "net" and calls(s)[0][4] == "settled_at_reserved"

    class NoFields(FakeBackend):
        def send(self, body, reservation):
            budget.begin_send(reservation, body)
            return model.ModelResult(None, "m", 5, 5, 0, None)  # no error and no fields is a bad reply, never a success

    r = guarded(s, NoFields(s, {})).call(req(TEXT))
    assert r.error == "bad_reply" and calls(s)[1][4] == "settled_at_reserved"


def test_a_successful_call_costs_the_usage_and_the_guard_computes_cost_micro(tmp_path):
    s = fake_settings(tmp_path)  # test prices: read 1 / 5 US$ per million tokens
    register(s, TEXT)
    r = guarded(s, fake_with(s, TEXT, read=reply(i=246, o=110))).call(req(TEXT))
    assert r.error is None and r.cost_micro == 246 + 550 and r.fields == GOOD_FIELDS
    assert calls(s) == [("read", 246, 110, 796, "settled")]


def test_settle_failed_after_one_retry_is_exit_3(tmp_path, monkeypatch):
    s = live_settings(tmp_path)
    res = budget.reserve(s, "a" * 64, "read", body())
    monkeypatch.setattr(budget, "BUSY_MS", 30)
    hold = sqlite3.connect(budget.ledger_path(s), isolation_level=None)
    hold.execute("BEGIN IMMEDIATE")
    try:
        with pytest.raises(ConfigError) as ei:
            budget.settle(res, (1, 1))
    finally:
        hold.execute("ROLLBACK")
        hold.close()
    assert ei.value.code == "settle_failed"
    assert budget.settle(res, (1, 1)) >= 1  # nothing was half-written: the reservation is still open


# ---- refusals that cost nothing -------------------------------------------------------------------------------------------------------------
def _live_guard(tmp_path):
    s = live_settings(tmp_path)
    register(s, TEXT)
    return s, guarded(s, AnthropicBackend(s))


def test_refusal_costs_nothing_for_gate_key_host_and_consent(tmp_path):
    s, g = _live_guard(tmp_path)
    assert g.call(req("an unlisted text")).error == "gate"  # gate
    # key: the live file has no API key
    key_file(s).write_text("".join(ln for ln in key_file(s).read_text().splitlines(True) if "ANTHROPIC" not in ln), encoding="utf-8")
    assert g.call(req(TEXT)).error == "budget"
    # host: config host differs from the pinned constant
    s2 = with_model(s, api_host="example.invalid")
    assert guarded(s2, AnthropicBackend(s2)).call(req(TEXT)).error == "budget"
    # consent: the literal prefix is gone
    s.owner_sentence_path.write_text("The most the whole demo project may spend is US$100.\n", encoding="utf-8")
    assert guarded(s, AnthropicBackend(s)).call(req(TEXT)).error == "gate"
    assert rows(s, "reservations") == 0 and rows(s, "calls") == 0 and budget.total_settled_micro(s) == 0


def test_committed_config_alone_has_no_prices_and_refuses(tmp_path):
    from intake import settings as cfg

    home = tmp_path / "local"
    s = cfg.load({"HADAVIN_LOCAL": str(home), "INTAKE_MODEL_BACKEND": "fake"})
    assert not s.prices_path.exists()
    budget.init(s)
    assert codes_of(budget.reserve, s, "a" * 64, "read", body()) == "prices_missing"
    assert codes_of(budget.min_limit_micro, s, FakeBackend(s)) == "prices_missing"
    for bad in ("{}", "not json", json.dumps({"prices_micro_usd_per_million_tokens": {"read": {"in": 0, "out": 0}}})):
        s.prices_path.parent.mkdir(parents=True, exist_ok=True)
        s.prices_path.write_text(bad, encoding="utf-8")
        assert codes_of(budget.reserve, s, "a" * 64, "read", body()) == "prices_missing"


def test_stale_and_future_price_dates_refuse_in_a_running_process(tmp_path, monkeypatch):
    s = fake_settings(tmp_path)
    register(s, TEXT)
    g = guarded(s, fake_with(s, TEXT, read=reply()))
    assert g.call(req(TEXT)).error is None
    real = budget.clock()
    monkeypatch.setattr(budget, "clock", lambda: real + 30 * 86400)  # exactly 30 days: still allowed
    assert g.call(req(TEXT)).error is None
    monkeypatch.setattr(budget, "clock", lambda: real + 31 * 86400 + 60)  # a fake clock past 30 days, same process, no restart
    assert codes_of(budget.reserve, s, "a" * 64, "read", body()) == "prices_missing"
    assert g.call(req(TEXT)).error == "budget"
    monkeypatch.setattr(budget, "clock", lambda: real + 31 * 86400 + 120)
    set_prices(s, 1_000_000, 5_000_000, as_of=(budget.today() + timedelta(days=3)).isoformat())  # file date in the future
    assert codes_of(budget.reserve, s, "a" * 64, "read", body()) == "prices_missing"
    assert rows(s, "reservations") == 2  # only the two calls made before the clock moved


def test_prices_file_changes_take_effect_on_the_next_reserve(tmp_path):
    s = fake_settings(tmp_path)
    r1 = budget.reserve(s, "a" * 64, "read", body())
    set_prices(s, 2_000_000, 10_000_000)
    r2 = budget.reserve(s, "b" * 64, "read", body())
    assert r2.micro > r1.micro
    s.prices_path.unlink()
    assert codes_of(budget.reserve, s, "c" * 64, "read", body()) == "prices_missing"


# ---- owner sentence, provider limit, effective cap -------------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "quote",
    [
        "0",
        "$5",
        "LIMIT SET 0",
        "LIMIT SET $5",
        "LIMIT SET 05",
        "limit set 5",
        "PREPAID",
        "LIMIT SET 100000",
        "LIMIT SET 5 now",
        "",
        "foo",
        "LIMIT  SET 5",
    ],
)
def test_confirm_limit_bad_forms_are_refused(tmp_path, quote, monkeypatch):
    s = live_settings(tmp_path, limit=None)
    with pytest.raises(ConfigError) as ei:
        budget.confirm_limit(s, quote)
    assert ei.value.code == "bad_config" and budget.provider_limit_micro(s) is None
    monkeypatch.setenv("HADAVIN_LOCAL", str(s.local))
    monkeypatch.setenv("INTAKE_MODEL_BACKEND", "anthropic")
    assert cli.main(["confirm-limit", "--quote", quote]) == 3


def test_confirm_limit_good_forms_store_the_quote_and_a_later_one_replaces_it(tmp_path, capsys, monkeypatch):
    s = live_settings(tmp_path, limit=None)
    assert budget.confirm_limit(s, "LIMIT SET 25") == 25 and budget.provider_limit_micro(s) == 25_000_000
    assert budget.confirm_limit(s, "PREPAID 7\n") == 7 and budget.provider_limit_micro(s) == 7_000_000
    with sqlite3.connect(budget.ledger_path(s)) as c:
        assert dict(c.execute("SELECT k,v FROM meta"))["provider_quote"] == "PREPAID 7"
    monkeypatch.setenv("HADAVIN_LOCAL", str(s.local))
    monkeypatch.setenv("INTAKE_MODEL_BACKEND", "anthropic")
    assert cli.main(["confirm-limit", "--quote", "LIMIT SET 9"]) == 0
    assert capsys.readouterr().out.strip() == "provider_limit: recorded 9"


def test_effective_cap_is_the_minimum_of_the_owner_total_and_the_provider_limit(tmp_path):
    s = live_settings(tmp_path, limit=30, sentence_total=100)
    with sqlite3.connect(budget.ledger_path(s)) as c:
        assert budget.effective_cap(c, s) == 30_000_000
    set_sentence(s, 10)
    with sqlite3.connect(budget.ledger_path(s)) as c:
        assert budget.effective_cap(c, s) == 10_000_000
        assert budget.current_cap(s) == 10_000_000


def test_provider_limit_missing_refuses(tmp_path):
    s = live_settings(tmp_path, limit=None)
    assert codes_of(budget.reserve, s, "a" * 64, "read", body()) == "provider_limit_missing"


def test_lowering_the_owner_sentence_from_100_to_5_refuses_the_next_reserve_in_the_same_process(tmp_path):
    s = live_settings(tmp_path, limit=100, sentence_total=100)
    set_prices(s, 1_000_000, 1_000_000)
    s = with_model(s, overhead_tokens=0, max_tokens=3_000_000)  # worst ~ US$3
    first = budget.reserve(s, "a" * 64, "read", body(10))
    assert first.micro > 3_000_000
    set_sentence(s, 5)  # the owner lowers the sentence while the process runs
    assert codes_of(budget.reserve, s, "b" * 64, "read", body(10)) == "budget_total"
    set_sentence(s, 100)
    assert budget.reserve(s, "b" * 64, "read", body(10))


@pytest.mark.parametrize(
    "text",
    [
        "",
        "YES: send made-up invoices to the Anthropic AI service.",  # the consent alone
        "The most the whole demo project may spend is US$100.",  # the number part alone: cap ok, consent missing
        "The most the whole demo project may spend is US$100. The most the whole demo project may spend is US$50.",  # two matches
        "The most the whole demo project may spend is US$0.",
        "The most the whole demo project may spend is US$100000.",
        "the most the whole demo project may spend is us$100.",
    ],
)
def test_owner_sentence_forms_that_do_not_count(tmp_path, text):
    s = live_settings(tmp_path)
    s.owner_sentence_path.write_text(text, encoding="utf-8")
    assert not budget.consent_recorded(s)
    assert codes_of(budget.current_cap, s) == "owner_sentence_missing"
    assert codes_of(budget.reserve, s, "a" * 64, "read", body()) == "owner_sentence_missing"
    s.owner_sentence_path.unlink()
    assert codes_of(budget.current_cap, s) == "owner_sentence_missing"


def test_owner_sentence_forms_that_count(tmp_path):
    s = live_settings(tmp_path)
    full = "YES: send made-up invoices to the Anthropic AI service. The most the whole demo project may spend is US$42."
    for variant in (
        full,
        full + "\n",
        "\n  " + full + "  \r\n",
        "YES: send made-up invoices to the Anthropic AI service.\nThe most the whole demo project may spend is US$42.",
    ):
        s.owner_sentence_path.write_text(variant, encoding="utf-8")
        assert budget.consent_recorded(s) and budget.current_cap(s) == 42_000_000
    s.owner_sentence_path.write_text(full + " " + full, encoding="utf-8")  # the consent prefix twice
    assert not budget.consent_recorded(s)


def test_fake_backend_needs_no_sentence_and_no_limit_and_uses_the_fake_cap(tmp_path):
    s = fake_settings(tmp_path)
    s.owner_sentence_path.unlink()
    assert budget.current_cap(s) == s.model.fake_total_cap_micro == 100_000_000
    assert budget.reserve(s, "a" * 64, "read", body())


# ---- ledger checks --------------------------------------------------------------------------------------------------------------------------
def test_ledger_missing_refuses_and_nothing_is_created(tmp_path):
    s = live_settings(tmp_path)
    budget.ledger_path(s).unlink()
    assert codes_of(budget.reserve, s, "a" * 64, "read", body()) == "ledger_missing"
    register(s, TEXT)
    g = guarded(s, FakeBackend(s, {}))
    assert g.deferred == "ledger_missing" and g.call(req(TEXT)).error == "budget"
    assert not budget.ledger_path(s).exists()


def test_ledger_total_below_the_queue_costs_refuses(tmp_path):
    s = live_settings(tmp_path)
    make_queue(s, [300, 400])
    assert codes_of(budget.reserve, s, "a" * 64, "read", body()) == "ledger_inconsistent"
    assert codes_of(budget.startup_check, s, FakeBackend(s)) == "ledger_inconsistent"
    with pytest.raises(Refused) as ei:
        guarded(s, FakeBackend(s, {}))
    assert ei.value.code == "ledger_inconsistent"
    # settle spend equal to the queue sum: consistent again (equality passes)
    with sqlite3.connect(budget.ledger_path(s)) as c:
        c.execute("INSERT INTO calls(ts,cost_micro,status) VALUES(0,700,'settled')")
    assert budget.reserve(s, "a" * 64, "read", body())


def test_a_missing_queue_file_or_items_table_counts_as_zero(tmp_path):
    s = live_settings(tmp_path)
    assert budget.queue_cost_micro(s) == 0  # no file
    make_queue(s, None, table=False)  # a file with no items table (normal in Milestone 1)
    assert budget.queue_cost_micro(s) == 0
    assert budget.reserve(s, "a" * 64, "read", body())


def test_init_twice_does_not_reset_and_a_deleted_ledger_next_to_a_costed_queue_is_refused(tmp_path):
    s = live_settings(tmp_path)
    res = budget.reserve(s, "a" * 64, "read", body())
    budget.settle(res, (10, 10))
    before = budget.total_settled_micro(s)
    budget.init(s)
    budget.init(s)
    assert budget.total_settled_micro(s) == before == 60 and budget.provider_limit_micro(s) == 100_000_000
    # fresh ledger with costed items
    s2 = live_settings(tmp_path / "other", limit=None)
    budget.ledger_path(s2).unlink()
    make_queue(s2, [500])
    assert codes_of(budget.init, s2) == "ledger_inconsistent"
    assert codes_of(budget.confirm_limit, s2, "LIMIT SET 5") == "ledger_inconsistent"


def test_a_busy_ledger_refuses_instead_of_calling(tmp_path, monkeypatch):
    s = fake_settings(tmp_path)
    register(s, TEXT)
    g = guarded(s, fake_with(s, TEXT, read=reply()))
    monkeypatch.setattr(budget, "BUSY_MS", 30)
    hold = sqlite3.connect(budget.ledger_path(s), isolation_level=None)
    hold.execute("BEGIN IMMEDIATE")
    try:
        assert codes_of(budget.reserve, s, "a" * 64, "read", body()) == "ledger_missing"
        assert g.call(req(TEXT)).error == "budget"
    finally:
        hold.execute("ROLLBACK")
        hold.close()
    assert rows(s, "reservations") == 0 and g.call(req(TEXT)).error is None


def test_the_ledger_uses_synchronous_full_and_immediate_transactions(tmp_path):
    src = (ROOT / "src" / "intake" / "budget.py").read_text(encoding="utf-8")
    assert "PRAGMA synchronous=FULL" in src and "BEGIN IMMEDIATE" in src and "isolation_level=None" in src


# ---- startup check --------------------------------------------------------------------------------------------------------------------------
def test_startup_check_refuses_below_the_minimum_and_equality_passes(tmp_path, monkeypatch):
    s = live_settings(tmp_path, limit=50, sentence_total=100)  # cap 50 US$
    b = FakeBackend(s)
    monkeypatch.setattr(budget, "min_limit_micro", lambda _s, _b: 50_000_000)  # equality
    assert budget.startup_check(s, b) is None
    monkeypatch.setattr(budget, "min_limit_micro", lambda _s, _b: 50_000_001)  # one micro over
    assert codes_of(budget.startup_check, s, b) == "cap_too_small_for_worst_case"
    with pytest.raises(Refused) as ei:  # the constructor runs it once
        guarded(s, b)
    assert ei.value.code == "cap_too_small_for_worst_case"
    monkeypatch.setattr(budget, "min_limit_micro", lambda _s, _b: 50_000_000)
    assert guarded(s, b).deferred is None


def test_the_constructor_defers_when_the_sentence_limit_or_prices_are_missing(tmp_path):
    s = live_settings(tmp_path)
    s.owner_sentence_path.unlink()
    g = guarded(s, FakeBackend(s, {}))
    assert g.deferred == "owner_sentence_missing"
    register(s, TEXT)
    assert g.call(req(TEXT)).error == "budget" and rows(s, "reservations") == 0
    s2 = live_settings(tmp_path / "b", limit=None)
    assert guarded(s2, FakeBackend(s2, {})).deferred == "provider_limit_missing"
    s3 = live_settings(tmp_path / "c")
    s3.prices_path.unlink()
    assert guarded(s3, FakeBackend(s3, {})).deferred == "prices_missing"


def test_min_limit_is_eighteen_times_the_worst_case_of_the_maximum_document(tmp_path):
    s = live_settings(tmp_path)
    b = AnthropicBackend(s)
    p = budget.current_prices(s)
    big = chr(0x10FFFF) * 20000
    esc = chr(1) * 20000
    n_big, n_esc = (len(b.request_body(req(t, "read"))) for t in (big, esc))
    assert n_esc > n_big  # the escaped control characters make the larger body (6 bytes each against 4)
    expect = 0
    for tier in ("read", "fallback"):
        n = max(len(b.request_body(req(t, tier))) for t in (big, esc))
        expect += -(
            -(
                (n + s.model.overhead_tokens) * (p.read_in if tier == "read" else p.fallback_in)
                + s.model.max_tokens * (p.read_out if tier == "read" else p.fallback_out)
            )
            // 1_000_000
        )
    assert budget.min_limit_micro(s, b) == 18 * expect > 0
    set_prices(s, 2_000_000, 10_000_000, 4_000_000, 20_000_000)
    assert budget.min_limit_micro(s, b) > 18 * expect  # prices are re-read on every call


def test_worst_case_formula():
    from datetime import date

    from intake.settings import Prices

    p = Prices(500_000, 2_500_000, 2_000_000, 10_000_000, date(2026, 11, 3), "v")
    assert budget.worst_case(p, "read", 1000, 2048, 2000) == -(-(3000 * 500_000 + 2048 * 2_500_000) // 1_000_000) == 6620
    assert budget.worst_case(p, "fallback", 1000, 2048, 2000) == (3000 * 2_000_000 + 2048 * 10_000_000) // 1_000_000 + 0 == 26480
    assert codes_of(budget.worst_case, p, "other", 1, 1, 1) == "bad_config"


# ---- one send per reservation ---------------------------------------------------------------------------------------------------------------
def _sendable(tmp_path):
    s = fake_settings(tmp_path)
    b = FakeBackend(s, {})
    rq = req(TEXT)
    bd = b.request_body(rq)
    return s, b, rq, bd, budget.reserve(s, rq.doc_sha, "read", bd)


def test_send_requires_a_reservation(tmp_path):
    s, b, rq, bd, res = _sendable(tmp_path)
    for bad in (None, "x", {"id": 1}):
        with pytest.raises(Refused):
            b.send(bd, bad)
    forged = budget.Reservation(res.id + 5, res.doc_sha, "read", res.micro, res.body_len, res.body_sha, res.ledger, budget._MINT)  # noqa: SLF001
    with pytest.raises(Refused):
        b.send(bd, forged)
    assert sqlite3.connect(budget.ledger_path(s)).execute("SELECT state FROM reservations").fetchall() == [("open",)]


def test_second_send_is_refused(tmp_path):
    s, b, rq, bd, res = _sendable(tmp_path)
    b.send(bd, res)
    with pytest.raises(Refused):
        b.send(bd, res)
    budget.settle(res, None)
    with pytest.raises(Refused):
        b.send(bd, res)  # settled: refused too


def test_a_different_body_of_equal_size_is_refused(tmp_path):
    s, b, rq, bd, res = _sendable(tmp_path)
    other = bytes(reversed(bd))
    assert len(other) == len(bd) and other != bd
    with pytest.raises(Refused):
        b.send(other, res)
    b.send(bd, res)  # the priced body still goes (the refusal did not burn the reservation)


def test_an_oversize_body_is_refused(tmp_path):
    s, b, rq, bd, res = _sendable(tmp_path)
    for big in (bd + b" ", bd * 3, b"x" * 100_000):
        with pytest.raises(Refused):
            b.send(big, res)


def test_a_tier_or_document_mismatch_is_refused(tmp_path):
    s, b, rq, bd, res = _sendable(tmp_path)
    bd_fb = b.request_body(req(TEXT, "fallback"))
    with pytest.raises(Refused):
        b.send(bd_fb, res)  # the fallback body on the read reservation
    with pytest.raises(Refused):
        b.send(bd, replace(res, tier="fallback"))  # the object says fallback, the ledger says read
    with pytest.raises(Refused):
        b.send(bd, replace(res, doc_sha="f" * 64))
    with pytest.raises(Refused):
        b.send(bd, replace(res, micro=1))
    with pytest.raises(Refused):
        b.send(b.request_body(req("another text")), res)  # another document's body
    b.send(bd, res)


def test_every_backend_send_calls_begin_send_first(tmp_path, monkeypatch):
    for fname, cls in (("model_fake.py", "FakeBackend"), ("model_anthropic.py", "AnthropicBackend")):
        tree = ast.parse((ROOT / "src" / "intake" / fname).read_text(encoding="utf-8"))
        send = next(
            n
            for c in tree.body
            if isinstance(c, ast.ClassDef) and c.name == cls
            for n in c.body
            if isinstance(n, ast.FunctionDef) and n.name == "send"
        )
        first = next(st for st in send.body if not (isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant)))  # skip a docstring
        assert isinstance(first, ast.Expr) and isinstance(first.value, ast.Call)
        assert ast.unparse(first.value.func) == "budget.begin_send"

    class StopError(Exception):
        pass

    def boom(*a, **k):
        raise StopError

    s = live_settings(tmp_path)
    monkeypatch.setattr(budget, "begin_send", boom)
    import intake.model_anthropic as ma

    monkeypatch.setattr(ma.AnthropicBackend, "_exchange", lambda *a, **k: pytest.fail("network before begin_send"))
    monkeypatch.setattr(ma.secret_store, "get", lambda *a, **k: pytest.fail("key read before begin_send"))
    for backend in (FakeBackend(s, {}), AnthropicBackend(s)):
        with pytest.raises(StopError):
            backend.send(b"x", object())


def test_preflight_runs_in_the_guard_before_reserve_not_in_send(tmp_path):
    s = live_settings(tmp_path)
    register(s, TEXT)
    order = []

    class Spy(FakeBackend):
        def preflight(self):
            order.append("preflight")
            return None

        def request_body(self, r):
            if r.send_text == TEXT:  # (the minimum check also builds the maximum-size bodies on every call)
                order.append("body")
            return super().request_body(r)

        def send(self, bd, res):
            order.append("send")
            return super().send(bd, res)

    g = guarded(s, Spy(s, {f"{sha(TEXT)}:read": reply()}))
    order.clear()
    assert g.call(req(TEXT)).error is None and order == ["preflight", "body", "send"]


# ---- import scans (a convention check over our own files) -----------------------------------------------------------------------------------
def scan_py(files: dict[str, str]) -> dict[str, list[str]]:
    """Findings per rule for ``{relative path: source}``."""
    out: dict[str, list[str]] = {"guardedmodel": [], "anthropic": [], "host": []}
    for rel, src in files.items():
        base = rel.rsplit("/", 1)[-1]
        tree = ast.parse(src)
        for n in ast.walk(tree):
            names: list[str] = []
            if isinstance(n, ast.ImportFrom):
                names = [a.name for a in n.names] + [n.module or ""]
            elif isinstance(n, ast.Import):
                names = [a.name for a in n.names]
            elif isinstance(n, ast.Attribute):
                names = [n.attr]
            if any(x == "GuardedModel" for x in names) and base not in ("model.py", "pipeline.py", "cli.py"):
                out["guardedmodel"].append(rel)
            if any(x.rsplit(".", 1)[-1] == "model_anthropic" for x in names) and base != "model.py":
                out["anthropic"].append(rel)
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and "api.anthropic.com" in n.value and base != "model_anthropic.py":
                out["host"].append(rel)
    return out


def our_py_files() -> dict[str, str]:
    files = {}
    for top in ("src", "tools", "demo_only"):
        for p in (ROOT / top).rglob("*.py") if (ROOT / top).is_dir() else []:
            files[p.relative_to(ROOT).as_posix()] = p.read_text(encoding="utf-8")
    return files


def test_only_pipeline_and_cli_import_guardedmodel():
    assert scan_py(our_py_files())["guardedmodel"] == []
    assert scan_py({"src/intake/extract.py": "from .model import GuardedModel\n"})["guardedmodel"]  # the scan sees a violation
    assert scan_py({"tools/x.py": "import intake.model as m\nm.GuardedModel(1)\n"})["guardedmodel"]
    assert not scan_py({"src/intake/pipeline.py": "from .model import GuardedModel\n"})["guardedmodel"]


def test_only_model_factory_imports_model_anthropic():
    assert scan_py(our_py_files())["anthropic"] == []
    assert scan_py({"src/intake/pipeline.py": "from .model_anthropic import AnthropicBackend\n"})["anthropic"]
    assert scan_py({"src/intake/cli.py": "from . import model_anthropic\n"})["anthropic"]
    assert scan_py({"tools/x.py": "import intake.model_anthropic\n"})["anthropic"]
    assert not scan_py({"src/intake/model.py": "from .model_anthropic import AnthropicBackend\n"})["anthropic"]


def test_api_host_literal_only_in_model_anthropic():
    assert scan_py(our_py_files())["host"] == []
    assert scan_py({"src/intake/settings.py": 'H = "api.anthropic.com"\n'})["host"]
    assert not scan_py({"src/intake/model_anthropic.py": 'H = "api.anthropic.com"\n'})["host"]
    allowed = json.loads((ROOT / "config" / "service.json").read_text(encoding="utf-8"))["model"]["api_host"]
    assert allowed == "api.anthropic.com"  # the config carries it too (the only non-Python home)


def test_the_vendor_modules_are_not_imported_by_the_fake_path():
    # the fake backend never imports the network modules (the factory imports model_anthropic lazily)
    src = (ROOT / "src" / "intake" / "model_fake.py").read_text(encoding="utf-8")
    assert "urllib" not in src and "ssl" not in src and "model_anthropic" not in src
    assert "import model_anthropic" not in (ROOT / "src" / "intake" / "model.py").read_text(encoding="utf-8").split("def backend_for")[0]


def test_only_the_model_module_calls_the_guard_internals():
    # reserve and settle are called only by the guard (model.py) and budget.py itself; backends call begin_send only
    for p in (ROOT / "src" / "intake").glob("*.py"):
        if p.name in ("budget.py", "model.py"):
            continue
        t = p.read_text(encoding="utf-8")
        assert "budget.reserve(" not in t and "budget.settle(" not in t, p.name
