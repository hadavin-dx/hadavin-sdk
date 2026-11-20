"""Step F-store, ORDER 020 minors m2, m3, m5 and the release command's dispatch. No database.

m2 settle checks the agent. m3 the stuck age is clamped. m5 `Budget` validates its limit and refuses a zero
reserve at the cap like the PostgreSQL store. The command `release-expired` is its own subcommand: it never reaches
`limits.reset` (which would clear the kill switch)."""

from __future__ import annotations

import argparse
import math
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from hadavin_sdk import cli, defaults
from hadavin_sdk.limits import Budget, Limits, SpendRefused
from hadavin_sdk.models import new_id
from hadavin_sdk.runtime import tick
from hadavin_sdk.store.memory import MemoryStore
from hadavin_sdk.store.protocol import MAX_EXPIRY_AGE_S, NotFound, check_expiry_age

D = Decimal
DAY = date(2025, 1, 31)


# --- m2: settle checks the agent -----------------------------------------------------------------------------------


def _reserved(store, agent="agent-a"):
    rid = new_id("res")
    store.reserve_spend(rid, agent, DAY, D("1.00"), day_cap=D(10), month_cap=D(10))
    return rid


def test_settle_of_another_agents_reservation_is_not_found_and_changes_nothing():
    store = MemoryStore()
    rid = _reserved(store)
    with pytest.raises(NotFound):
        store.settle_spend(rid, D("0"), agent_id="agent-b")
    row, applied = store.settle_spend(rid, D("0.25"), agent_id="agent-a")
    assert applied and row.settled_usd == D("0.25")


def test_settle_without_an_agent_keeps_working():
    store = MemoryStore()
    assert store.settle_spend(_reserved(store), D("0.5"))[1] is True


def test_limits_settle_for_passes_the_agent_on():
    store = MemoryStore()
    rid = _reserved(store)
    limits = Limits.__new__(Limits)
    limits.store = store
    with pytest.raises(NotFound):
        limits.settle_for("agent-b", rid, D("0"))
    assert limits.settle_for("agent-a", rid, D("0.5")) == 0


def test_budget_settle_of_another_agents_reservation_is_not_found():
    budget = Budget(D(10))
    rid = budget.reserve("agent-a", D(1))
    with pytest.raises(NotFound):
        budget.settle_for("agent-b", rid, D(0))
    assert budget.settle_for("agent-a", rid, D("0.5")) == 0
    assert budget.spent == D("0.5")


# --- m3: the stuck age is clamped ----------------------------------------------------------------------------------


def _app(max_steps, timeout=60, attempts=1):
    agents = {"a": SimpleNamespace(max_steps=max_steps)}
    llm = SimpleNamespace(call_timeout_s=timeout, max_attempts=attempts)
    return SimpleNamespace(
        registry=SimpleNamespace(agents=agents),
        config=SimpleNamespace(backends=SimpleNamespace(llm=llm)),
    )


@pytest.mark.parametrize(
    "app",
    [
        _app(10**9),  # far above 10**7 seconds
        _app(1, timeout=math.inf),
        _app(1, timeout=math.nan),
        _app(1, timeout=1e300),
    ],
    ids=["huge steps", "infinite", "nan", "1e300"],
)
def test_a_stuck_age_that_is_too_large_or_not_a_number_is_clamped_and_the_store_accepts_it(app):
    age = tick.reservation_expire_s(app)
    assert age == MAX_EXPIRY_AGE_S and type(age) is int
    assert check_expiry_age(age) == age
    assert MemoryStore().expire_spend_reservations(age) == 0


def test_a_normal_stuck_age_is_not_changed_by_the_clamp():
    assert tick.reservation_expire_s(_app(1)) == defaults.RESERVATION_EXPIRE_S
    assert tick.reservation_expire_s(_app(200, 60, 2)) == 200 * 60 * 2 + 60


# --- m5: Budget ----------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "limit", [float("nan"), 1.0, 1, "1", None, D("NaN"), D("Infinity"), D("-1"), True]
)
def test_budget_refuses_a_limit_the_store_would_refuse(limit):
    with pytest.raises(ValueError):
        Budget(limit)


def test_budget_accepts_a_zero_limit_and_then_refuses_everything_like_the_store():
    budget = Budget(D(0))
    with pytest.raises(SpendRefused) as e:
        budget.reserve("a", D(0))
    assert e.value.reason == "usd_cap"


def test_a_zero_reserve_at_exactly_the_cap_is_refused_like_postgres():
    budget = Budget(D(1))
    budget.reserve("a", D(1))  # exactly the cap is allowed (usd + amt <= cap)
    with pytest.raises(SpendRefused) as e:
        budget.reserve("a", D(0))  # at the cap even a zero amount refuses (usd < cap)
    assert e.value.reason == "usd_cap"


def test_a_zero_reserve_below_the_cap_still_works():
    budget = Budget(D(1))
    budget.reserve("a", D("0.5"))
    assert budget.reserve("a", D(0))


# --- the command is its own subcommand -----------------------------------------------------------------------------


def test_release_expired_is_not_an_action_of_limits(capsys):
    with pytest.raises(SystemExit) as e:
        cli.main(["limits", "release-expired", "--by", "x"])
    assert e.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_the_command_is_dispatched_to_its_own_function_and_never_reaches_limits_reset(monkeypatch):
    seen = []
    monkeypatch.setattr(cli, "load_config", lambda: SimpleNamespace(environment="pilot"))
    monkeypatch.setattr(
        cli, "release_expired_cmd", lambda cfg, agent, day, by: seen.append((agent, day, by)) or 7
    )

    def boom(*a, **k):  # the reset path: any call here would clear the kill switch
        raise AssertionError("limits.reset reached")

    monkeypatch.setattr(Limits, "reset", boom)
    monkeypatch.setattr(cli, "kill_switch", boom)
    argv = ["release-expired", "agent-a", "--day", "2025-01-31", "--by", "user:op"]
    assert cli.main(argv) == 7
    assert seen == [("agent-a", DAY, "user:op")]


def test_a_bad_day_is_refused_by_the_parser(capsys):
    with pytest.raises(SystemExit):
        cli.main(["release-expired", "a", "--day", "31-01-2025", "--by", "x"])
    assert "not a date" in capsys.readouterr().err
    with pytest.raises(argparse.ArgumentTypeError):
        cli._day("2025-13-01")


def _cfg(kind="postgres", **store):
    s = SimpleNamespace(kind=kind, dsn_secret_name="pg-dsn", purge_dsn_secret_name=None, **store)  # noqa: S106
    s.model_copy = lambda update: SimpleNamespace(**{**vars(s), **update})
    return SimpleNamespace(backends=SimpleNamespace(store=s, audit=None, secrets=None))


def test_the_command_refuses_before_any_connection(monkeypatch, capsys):
    def no_connection(*a, **k):
        raise AssertionError("a connection was built")

    monkeypatch.setattr(cli, "make", no_connection)
    assert cli.release_expired_cmd(_cfg("memory"), "a", DAY, "u") == 2
    assert cli.release_expired_cmd(_cfg(), "a", DAY, "u") == 2  # no release_credential_ref
    assert "release role" in capsys.readouterr().err
    same = _cfg(release_credential_ref="pg-dsn")
    assert cli.release_expired_cmd(same, "a", DAY, "u") == 2
    reset = _cfg(release_credential_ref="r", reset_credential_ref="r")
    assert cli.release_expired_cmd(reset, "a", DAY, "u") == 2


def test_the_agreed_settle_signature_is_unchanged():
    import inspect

    for owner in (Limits, Budget):
        assert list(inspect.signature(owner.settle).parameters) == [
            "self",
            "reservation_id",
            "actual_usd",
        ]


# --- review 3 minors -------------------------------------------------------------------------------------------


def test_the_release_ref_is_compared_in_canonical_form(monkeypatch, capsys):
    monkeypatch.setattr(
        cli, "make", lambda *a, **k: (_ for _ in ()).throw(AssertionError("connected"))
    )
    assert cli.release_expired_cmd(_cfg(release_credential_ref="PG.DSN"), "a", DAY, "u") == 2
    assert "same secret" in capsys.readouterr().err
    folded = _cfg(release_credential_ref="R-X", reset_credential_ref="r_x")
    assert cli.release_expired_cmd(folded, "a", DAY, "u") == 2


def test_a_tool_secret_that_folds_to_the_release_ref_stops_the_start():
    from hadavin_sdk import app as app_mod

    src = Path(app_mod.__file__).read_text()
    assert "release_credential_ref" in src and "canonical_secret_name" in src


def test_the_outcome_failing_after_commit_exits_5_and_names_the_intent(monkeypatch, capsys):
    from hadavin_sdk.store.protocol import SpendRelease

    done = SpendRelease(
        agent_id="a",
        day=DAY,
        reservations=1,
        released_usd=Decimal(1),
        day_usd=Decimal(0),
        month_usd=Decimal(0),
        applied_usd=Decimal(1),
        intent_id="evt-dangling-1",
        outcome_audited=False,
    )
    store = SimpleNamespace(release_expired_spend=lambda *a: done)
    monkeypatch.setattr(cli.platform_secrets, "check", lambda *a, **k: None)
    monkeypatch.setattr(cli, "make", lambda kind, *a, **k: store if kind == "store" else object())
    assert cli.release_expired_cmd(_cfg(release_credential_ref="rel"), "a", DAY, "u") == 5
    assert "evt-dangling-1" in capsys.readouterr().err


def test_limits_settle_works_with_a_store_that_has_the_old_signature():
    calls = []

    class Old:
        def settle_spend(self, reservation_id, actual_usd):
            calls.append((reservation_id, actual_usd))
            return (
                SimpleNamespace(
                    settled_usd=actual_usd, reserved_usd=actual_usd, run_id=None, agent_id="a"
                ),
                True,
            )

    limits = Limits.__new__(Limits)
    limits.store = Old()
    assert limits.settle("r1", Decimal(1)) == 0
    assert calls == [("r1", Decimal(1))]


def test_a_nan_stuck_age_after_the_first_agent_is_clamped(monkeypatch):
    ages = iter([5.0, float("nan")])
    app = SimpleNamespace(registry=SimpleNamespace(agents={"a": 1, "b": 2}))
    monkeypatch.setattr(tick, "stuck_after_s", lambda _app, _a: next(ages))
    assert tick.reservation_expire_s(app) == MAX_EXPIRY_AGE_S
