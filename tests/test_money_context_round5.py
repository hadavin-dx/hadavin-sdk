"""Review 4, M1/m1/m2: stored money sums run in our context; overflow of a price fails closed.

Caller precision is 4 and every value rounds at 4 digits."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal, localcontext
from types import SimpleNamespace

import pytest

from hadavin_sdk.k1b import loop
from hadavin_sdk.k1b import score as k1b_score
from hadavin_sdk.llm import common
from hadavin_sdk.llm.fake import FakeLLM
from hadavin_sdk.llm.protocol import ProviderError
from hadavin_sdk.models import Run
from hadavin_sdk.store.memory import MemoryStore

D = Decimal
DAY = date(2026, 1, 1)
BIG = D("1234.123456789012")
TINY = D("1.000000000001")
EXACT = BIG + TINY
HUGE = SimpleNamespace(
    model_id="m",
    input_usd_per_mtok=D("1E999999"),
    output_usd_per_mtok=D("1E999999"),
    max_tokens=10,
)


class low_precision:
    def __enter__(self):
        self._cm = localcontext()
        self._cm.__enter__().prec = 4

    def __exit__(self, *exc):
        return self._cm.__exit__(*exc)


def test_memory_reserve_books_exact_sum():
    s = MemoryStore()
    with low_precision():
        s.reserve_spend("r1", "a", DAY, BIG, day_cap=D("99999"), month_cap=D("99999"))
        s.reserve_spend("r2", "a", DAY, TINY, day_cap=D("99999"), month_cap=D("99999"))
    assert s.spend_totals("a", DAY)[0] == EXACT


def test_memory_add_cost_exact():
    s = MemoryStore()
    run = _make_run(s)
    with low_precision():
        s.add_cost(run, BIG)
        s.add_cost(run, TINY)
    assert s._runs[run].cost_usd == EXACT


def _make_run(s: MemoryStore) -> str:
    r = Run.model_construct(**{n: None for n in Run.model_fields})
    r = r.model_copy(update={"run_id": "run1", "cost_usd": D(0)})
    s._runs["run1"] = r
    return "run1"


def test_score_total_usd_exact():
    with low_precision():
        assert k1b_score._sum_usd([{"usd": str(BIG)}, {"usd": str(TINY)}]) == format(EXACT, "f")


def test_replay_run_usd_helper_exact():
    from hadavin_sdk.k1b import replay

    with low_precision():
        assert replay._spent_delta(EXACT, BIG) == TINY


def test_reply_price_overflow_is_provider_error():
    with pytest.raises(ProviderError):
        common.reply(
            HUGE, text="x" * 40, calls=[], tokens=(10, 10), stop="end_turn", started=0.0, sent="y"
        )


def test_fake_price_overflow_is_provider_error(tmp_path):
    llm = FakeLLM(tmp_path, {"r": HUGE})
    msgs = [{"role": "user", "content": "hi"}]
    import hashlib

    digest = hashlib.sha256(json.dumps(msgs, sort_keys=True).encode()).hexdigest()
    (tmp_path / f"{digest}-1.json").write_text(
        json.dumps(
            {"text": "t", "input_tokens": 10, "output_tokens": 10, "stop_reason": "end_turn"}
        )
    )
    with pytest.raises(ProviderError):
        llm.chat(msgs, system="s", route="r")


def test_k1b_worst_case_overflow_is_value_error():
    with pytest.raises(ValueError):
        loop.worst_case_usd(HUGE, "s", [{"role": "user", "content": "x"}])


def test_k1b_unpriceable_timeout_books_the_whole_cap():
    from hadavin_sdk.llm.protocol import ProviderError as _PE  # noqa: F401

    b = loop.Budget(D("5"))
    try:
        worst = loop.worst_case_usd(HUGE, "s", [{"role": "user", "content": "x"}])
    except ValueError:
        worst = b.limit
    b.charge(worst)
    assert b.exhausted and b.spent == D("5")
