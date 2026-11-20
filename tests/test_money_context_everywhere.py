"""Review 3, M1/m1/m2: every money sum and product runs in our own Decimal context, not the caller's.

Each test lowers the caller's precision to 4 and uses a value that rounds at 4 digits."""

from __future__ import annotations

import decimal
from datetime import date
from decimal import Decimal, localcontext
from types import SimpleNamespace

from hadavin_sdk import defaults
from hadavin_sdk.config import Route
from hadavin_sdk.k1b import loop
from hadavin_sdk.k1b.report import render_replay_report
from hadavin_sdk.limits import Budget, Limits
from hadavin_sdk.store.memory import MemoryStore

D = Decimal
DAY = date(2026, 1, 1)
BIG = D("1234.123456789012")
TINY = D("1.000000000001")
EXACT = BIG + TINY  # 1235.123456789013


class low_precision:
    def __enter__(self):
        self._cm = localcontext()
        self._cm.__enter__().prec = 4

    def __exit__(self, *exc):
        return self._cm.__exit__(*exc)


def test_k1b_worst_case_usd():
    r = Route(
        model_id="m",
        input_usd_per_mtok="123456.123456",
        output_usd_per_mtok="999999.999999",
        max_tokens=4093,
    )
    exact = loop.worst_case_usd(r, "s", [{"role": "user", "content": "x"}])
    with low_precision():
        low = loop.worst_case_usd(r, "s", [{"role": "user", "content": "x"}])
    assert low == exact and exact > D("4094.3")


def test_memory_add_spend():
    s = MemoryStore()
    with low_precision():
        s.add_spend("a", DAY, BIG)
        assert s.add_spend("a", DAY, TINY) == (EXACT, EXACT)


def test_memory_spend_totals():
    s = MemoryStore()
    s.add_spend("a", DAY, BIG)
    s.add_spend("a", date(2026, 1, 2), TINY)
    with low_precision():
        assert s.spend_totals("a", DAY) == (BIG, EXACT)


def test_memory_month_total_and_reserve_arithmetic():
    s = MemoryStore()
    s.add_spend("a", DAY, BIG)
    s.add_spend("a", date(2026, 1, 2), TINY)
    with low_precision():
        assert s._month_total("a", DAY) == EXACT
        # booked + usd must be compared exactly: 1234.123456789012 + 0.000000000001 > cap 1234.123456789012
        import pytest

        from hadavin_sdk.store.protocol import SpendCapExceeded

        with pytest.raises(SpendCapExceeded):
            s.reserve_spend("r1", "a", DAY, D("0.000000000001"), day_cap=BIG, month_cap=D("9999"))


def test_memory_settle_spend_booking():
    s = MemoryStore()
    s.add_spend("a", DAY, D(0))
    s.reserve_spend("r1", "a", DAY, BIG, day_cap=D("99999"), month_cap=D("99999"))
    with low_precision():
        s.settle_spend("r1", EXACT)
    assert s.spend_totals("a", DAY)[0] == EXACT


def test_budget_spent_sum_and_settle_overshoot():
    b = Budget(D("999999"))
    b.charge(BIG)
    b.charge(TINY)
    with low_precision():
        assert b.spent == EXACT
    b2 = Budget(D("999999"))
    rid = b2.reserve("a", BIG)
    with low_precision():
        assert b2.settle_for("a", rid, EXACT) == TINY


def test_limits_settle_overshoot():
    reg = SimpleNamespace(
        agents={
            "a": SimpleNamespace(budget_usd=SimpleNamespace(daily=D("9999"), monthly=D("9999")))
        }
    )

    class Sink:
        def write_intent(self, e):
            pass

        def write_outcome(self, e):
            pass

    lim = Limits(MemoryStore(), Sink(), reg)
    rid = lim.reserve("a", BIG)
    with low_precision():
        assert lim.settle(rid, EXACT) == TINY


def test_evals_cost_sum_and_division(cfg_dir):
    from hadavin_sdk import evals
    from tests.test_k1a_pass_k import RIGHT, ScriptedLLM, _doc, _registry, _reply

    reg = _registry(cfg_dir, [{"id": "a", "input_ref": "golden-01.txt", "expected": RIGHT}])
    llm = ScriptedLLM(
        {_doc(cfg_dir, "golden-01.txt"): [_reply(RIGHT, str(BIG)), _reply(RIGHT, str(TINY))]}
    )
    with low_precision():
        run = evals.gate(reg, llm, "test-agent", k=2)
    assert run.cost_per_task_usd == EXACT / 2


def test_k1b_report_cost_sum():
    counts = dict.fromkeys(
        ("ok", "unreadable", "error", "timeout", "capped", "uncited_conversions", "hard_check_a"), 0
    )
    runs = [
        {
            "run_index": i,
            "counts": counts,
            "usd": str(v),
            "model_id": "m",
            "sdk_version": "0.0.0",
            "config_hash": "c",
            "bundle_set_sha256": "b",
        }
        for i, v in ((1, BIG), (2, TINY))
    ]
    with low_precision():
        text = render_replay_report(runs, "done")
    assert f"Cost: USD {EXACT}." in text


def test_money_context_is_pinned_not_inherited(monkeypatch):
    """m1: a host that edited decimal.DefaultContext cannot change our rounding, traps, Emin or Emax."""
    ctx = defaults.money_context()
    assert ctx.prec == defaults.MONEY_DECIMAL_PRECISION
    assert ctx.rounding == decimal.ROUND_HALF_EVEN
    assert (ctx.Emin, ctx.Emax) == (-999999, 999999)
    enabled = {k for k, v in ctx.traps.items() if v}
    assert enabled == {decimal.InvalidOperation, decimal.DivisionByZero, decimal.Overflow}
    monkeypatch.setattr(decimal.DefaultContext, "rounding", decimal.ROUND_DOWN)
    monkeypatch.setattr(decimal.DefaultContext, "Emax", 5)
    monkeypatch.setitem(decimal.DefaultContext.traps, decimal.Inexact, True)
    ctx = defaults.money_context()
    assert ctx.rounding == decimal.ROUND_HALF_EVEN and ctx.Emax == 999999
    assert not ctx.traps[decimal.Inexact]


def test_unknown_model_route_is_escaped_in_the_registry_refusal(cfg_dir):
    import pytest

    from hadavin_sdk.config import load_config
    from hadavin_sdk.errors import ConfigError
    from hadavin_sdk.registry import load_registry

    p = cfg_dir / "agents.yaml"
    p.write_text(p.read_text().replace("model_route: default", 'model_route: "evil\\nforged: x"'))
    with pytest.raises(ConfigError) as caught:
        load_registry(load_config(cfg_dir))
    assert "evil\nforged" not in str(caught.value)
    assert "evil\\nforged" in str(caught.value)
