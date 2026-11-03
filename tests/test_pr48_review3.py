"""PR #48 result review 3 (M1-M3, N1, N2, N5, N6, N7): each test fails on the code the review read (d801b03)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import BaseModel

from hadavin_sdk import extract as extract_mod
from hadavin_sdk.llm import gemini
from hadavin_sdk.llm.metered import MeteredLLM
from hadavin_sdk.llm.protocol import (
    ProviderError,
    ProviderExhausted,
    QuotaReached,
    SpendLimitReached,
)
from hadavin_sdk.llm.resilient import CircuitBreaker, ResilientLLM
from hadavin_sdk.llm.retry import with_retry
from hadavin_sdk.models import KillSwitch, Reply
from hadavin_sdk.store.memory import MemoryStore
from hadavin_sdk.store.protocol import StoreUnavailable
from tests.test_core_hardening_review import _doc, _Raises, build
from tests.test_core_hardening_round2 import (  # noqa: F401 - fixtures are used by name
    DAY,
    ROUTES,
    Stub,
    _limits,
    _pg_store,
    clock,
    roles,
)

D = Decimal


# --- M1: every driver error is StoreUnavailable, class name only ------------------------------------------------------


def test_m1_a_driver_error_that_is_not_operational_is_store_unavailable_by_class_name(roles, clock):  # noqa: F811
    store = _pg_store(roles.runtime)
    try:
        lim = _limits(store, max_run="5")
        with pytest.raises(StoreUnavailable) as e:
            lim.prune_runs()  # the runtime role may not DELETE: InsufficientPrivilege
        assert "InsufficientPrivilege" in str(e.value)
        assert "permission denied" not in str(e.value).lower()
        # A value the driver refuses (a NUL in text): DataError, whose text could quote the value.
        with pytest.raises(StoreUnavailable) as e2:
            store.reserve_spend("a" + chr(0) + "SECRET-VALUE", DAY, D("0.1"), D(1), D(1))
        assert "DataError" in str(e2.value) and "SECRET-VALUE" not in str(e2.value)
    finally:
        store.close()


# --- M2: an exhausted provider may have billed: the worst case stays booked -------------------------------------------


def test_m2_the_loop_keeps_the_worst_case_when_the_provider_is_exhausted(cfg_dir):
    rt, cfg = build(cfg_dir)
    rt.llm = _Raises(ProviderExhausted("read timed out after the request was sent"))
    run = rt.handle("test-agent", "svc:test-agent", _doc(cfg, "chat.txt"))
    assert run.reason_code == "provider_exhausted"
    assert rt.store.spend_totals("test-agent", run.created_at.date())[0] > 0


def test_m2_the_loop_still_releases_a_refused_request_and_names_a_quota(cfg_dir):
    rt, cfg = build(cfg_dir)
    rt.llm = _Raises(QuotaReached("per-day quota"))
    run = rt.handle("test-agent", "svc:test-agent", _doc(cfg, "chat.txt"))
    assert run.reason_code == "provider_quota"
    assert rt.store.spend_totals("test-agent", run.created_at.date()) == (0, 0)


def test_m2_metered_llm_keeps_the_worst_case_on_exhaustion_and_releases_a_refusal(clock):  # noqa: F811
    store = MemoryStore()
    lim = _limits(store, daily="1")
    with pytest.raises(ProviderExhausted):
        MeteredLLM(Stub(ProviderExhausted("5xx after retries")), lim, "a", ROUTES).chat(
            [], system="", route="r"
        )
    booked = store.spend_totals("a", DAY)[0]
    assert booked > 0
    with pytest.raises(ProviderError):
        MeteredLLM(Stub(ProviderError("bad request")), lim, "a", ROUTES).chat(
            [], system="", route="r"
        )
    assert store.spend_totals("a", DAY)[0] == booked  # the refusal released its own booking only


# --- M3: the spend reason is sticky for the whole failure streak ------------------------------------------------------


def test_m3_a_mixed_streak_that_includes_a_spend_limit_opens_for_spend():
    t = [0.0]
    br = CircuitBreaker(failures=5, reset_after_s=30.0, clock=lambda: t[0])
    for spend in (True, True, True, True, False):
        br.failure(br.allow(), spend=spend)
    assert br.open_for_spend

    unmetered = Stub(Reply(text="from fallback", model_id="m"))
    llm = ResilientLLM(Stub(SpendLimitReached("cap")), unmetered, CircuitBreaker(2, 30.0))
    llm.primary = Stub(SpendLimitReached("cap"))
    with pytest.raises(SpendLimitReached):
        llm.chat([], system="", route="r")  # a spend failure, not served by the unmetered fallback
    llm.primary = Stub(ProviderExhausted("down"))
    llm.chat(
        [], system="", route="r"
    )  # an outage failure: the circuit opens and this call is served
    assert unmetered.n == 1
    with pytest.raises(
        SpendLimitReached
    ):  # open for spend (sticky): the unmetered fallback is not used
        llm.chat([], system="", route="r")
    assert unmetered.n == 1


def test_m3_the_streak_flag_resets_when_the_circuit_closes():
    t = [0.0]
    br = CircuitBreaker(failures=2, reset_after_s=10.0, clock=lambda: t[0])
    br.failure(br.allow(), spend=True)
    br.success(br.allow())  # closed streak ends
    for _ in range(2):
        br.failure(br.allow(), spend=False)
    assert not br.open_for_spend


# --- N1 / N2 ----------------------------------------------------------------------------------------------------------


def test_n1_safe_errors_names_no_value_for_a_plain_exception():
    assert extract_mod.safe_errors(ValueError("CANARY"), set()) == "reply is invalid"
    assert "CANARY" not in extract_mod.safe_errors(ValueError("CANARY"), {"title"})


def test_n2_valid_repr_does_not_show_the_raw_model_text():
    class Rec(BaseModel):
        title: str

    reply = Reply(text='{"title": "t"} CANARY-DOCUMENT-QUOTE', model_id="m")
    assert "CANARY-DOCUMENT-QUOTE" not in repr(extract_mod.Valid(Rec(title="t"), [reply]))


# --- N5: a per-day quota is a QuotaReached (still a SpendLimitReached for the breaker) -----------------------------


def test_n5_gemini_per_day_quota_raises_quota_reached():
    assert issubclass(QuotaReached, SpendLimitReached)
    assert gemini.GeminiLLM.spend_error is QuotaReached

    def call():
        raise RuntimeError("429 per day")

    with pytest.raises(QuotaReached):
        with_retry(
            call,
            label="gemini",
            max_attempts=3,
            sleep=lambda s: None,
            retryable=lambda e: True,
            spend_limit=lambda e: True,
            spend_error=QuotaReached,
        )
    with pytest.raises(SpendLimitReached) as e:  # the default stays the money cap
        with_retry(
            call, label="x", max_attempts=3, sleep=lambda s: None, spend_limit=lambda e: True
        )
    assert not isinstance(e.value, QuotaReached)


# --- N6: a refused reservation leaves no counter rows -----------------------------------------------------------------


def _rows(dsn, agent):
    import psycopg

    with psycopg.connect(dsn) as db:
        return db.execute(
            "SELECT (SELECT count(*) FROM spend WHERE agent_id = %s),"
            " (SELECT count(*) FROM spend_month WHERE agent_id = %s)",
            (agent, agent),
        ).fetchone()


def test_n6_a_refused_reservation_commits_no_zero_counter_rows(roles, clock):  # noqa: F811
    store = _pg_store(roles.runtime)
    try:
        lim = _limits(store, daily="0.01", max_run="5")
        from hadavin_sdk.limits import OverBudget

        with pytest.raises(OverBudget):
            lim.reserve("a", D("0.50"), run_id="r-refused")  # over the daily cap
        assert _rows(roles.owner, "a") == (0, 0)
        assert _rows(roles.owner, "r-refused") == (0, 0)
        store.set_kill_switch(KillSwitch(on=True, by="t"))
        with pytest.raises(OverBudget):
            lim.reserve("a", D("0.001"), run_id="r-ks")
        assert _rows(roles.owner, "a") == (0, 0)
        store.set_kill_switch(KillSwitch(on=False, by="t"))
        lim.reserve("a", D("0.001"), run_id="r-ok")  # a booking still writes its rows
        assert _rows(roles.owner, "a") == (1, 1)
    finally:
        store.close()


# --- N7: a settle failure after a good reply does not lose the reply --------------------------------------------------


def test_n7_metered_llm_returns_the_reply_when_settle_fails(clock):  # noqa: F811
    store = MemoryStore()
    lim = _limits(store, daily="1")

    def boom(*a, **k):
        raise OSError("store down")

    lim.settle = boom
    reply = Reply(text="ok", model_id="m", cost_usd=D("0.002"))
    out = MeteredLLM(Stub(reply), lim, "a", ROUTES).chat([], system="", route="r")
    assert out is reply
    assert store.spend_totals("a", DAY)[0] > 0  # the worst case stays booked


# --- B1: the secrets scan of a pull request covers only that pull request's commits ----------------------------------


def test_b1_ci_gitleaks_scans_the_pr_range_and_the_full_history_only_off_pull_requests():
    from pathlib import Path

    ci = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    step = ci[
        ci.index("name: Secrets (gitleaks") : ci.index("name: Vulnerabilities, misconfigurations")
    ]
    assert "--log-opts=" in step, "gitleaks must be given an explicit range"
    assert "PR_BASE_SHA}..${PR_HEAD_SHA" in step and "github.event.pull_request.base.sha" in step
    assert '"$EVENT_NAME" = "pull_request"' in step
    assert "--full-history HEAD" in step  # push to main and the weekly schedule
    assert "--all" not in step, "every fetched branch (other pull requests) must not be scanned"
    assert "schedule:" in ci and "push:" in ci
