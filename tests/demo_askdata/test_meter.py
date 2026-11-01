"""The shared cost meter and the kill switch (A-03)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from askdata.fixtures import ROUTE
from askdata.meter import KillSwitch, Meter, MeterError, OverBudget, worst_case_usd

T0 = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)


def make(tmp_path, *, now=T0, **kw) -> Meter:
    m = Meter(tmp_path / "meter.json", clock=lambda: now, **kw)
    Meter.create(m.path, total_cap="10.00", reserve="1.00", demo_cap="8.00", now=now)
    return m


def test_worst_case_is_input_estimate_plus_max_tokens_at_the_output_rate():
    # 300 chars -> 100 tokens at $2/M, 1024 max tokens at $10/M
    assert worst_case_usd(ROUTE, 300) == (Decimal(100) * 2 + Decimal(1024) * 10) / 1_000_000


def test_charge_adds_up_and_survives_a_reread(tmp_path):
    m = make(tmp_path)
    m.charge(Decimal("0.013"))
    m.charge(Decimal("0.0045"))
    assert Meter(m.path).snapshot()["askdata_spent"] == Decimal("0.0175")
    assert json.loads(m.path.read_text())["spent"]["replay_check"] == "0"


def test_demo_cap_blocks_when_spent_plus_worst_case_exceeds_it(tmp_path):
    m = make(tmp_path)
    m.charge(Decimal("7.99"))
    m.check(Decimal("0.01"), live=False)
    with pytest.raises(OverBudget) as e:
        m.check(Decimal("0.0100001"), live=False)
    assert e.value.which == "demo_cap"


def test_the_shared_cap_keeps_the_reserve_unspent(tmp_path):
    m = make(tmp_path)
    m.set_external(Decimal("1.50"))
    path = json.loads(m.path.read_text())
    path["spent"]["replay_check"] = "0.40"
    m.path.write_text(json.dumps(path))
    # 10.00 - 1.00 reserve - 0.40 - 1.50 = 7.10 shared room
    m.check(Decimal("7.10"), live=False)
    with pytest.raises(OverBudget) as e:
        m.check(Decimal("7.11"), live=False)
    assert e.value.which == "shared_cap" and m.snapshot()["shared_room"] == Decimal("7.10")


def test_a_live_step_refuses_a_stale_external_figure(tmp_path):
    m = make(tmp_path, now=T0, max_external_age=timedelta(hours=24))
    later = Meter(
        m.path, clock=lambda: T0 + timedelta(hours=25), max_external_age=timedelta(hours=24)
    )
    later.check(Decimal("0.01"), live=False)  # a free (fake) step does not care
    with pytest.raises(OverBudget) as e:
        later.check(Decimal("0.01"), live=True)
    assert e.value.which == "external_stale"
    later.set_external(Decimal(0))
    later.check(Decimal("0.01"), live=True)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "{",
        "[]",
        '{"total_cap": "x"}',
        '{"total_cap":"10","reserve":"1","demo_cap":"8","spent":{},"external_usd":"0","external_updated_at":"now"}',
    ],
)
def test_a_broken_meter_file_fails_closed(tmp_path, text):
    p = tmp_path / "m.json"
    p.write_text(text)
    with pytest.raises(MeterError):
        Meter(p).check(Decimal("0.01"))


def test_a_missing_file_fails_closed(tmp_path):
    with pytest.raises(MeterError):
        Meter(tmp_path / "none.json").snapshot()


def test_negative_amounts_are_refused(tmp_path):
    with pytest.raises(MeterError):
        make(tmp_path).charge(Decimal(-1))


def test_a_stale_lock_file_is_broken_and_a_live_one_times_out(tmp_path):
    import os

    m = make(tmp_path, lock_wait_s=0.2)
    lock = m.path.with_name(m.path.name + ".lock")
    lock.write_text("x")
    with pytest.raises(MeterError, match="busy"):
        m.charge(Decimal("0.01"))
    os.utime(lock, (1, 1))  # a crashed holder, long ago
    m.charge(Decimal("0.01"))
    assert not lock.exists()


def test_remaining_is_the_smaller_of_the_two_rooms(tmp_path):
    m = make(tmp_path)
    m.charge(Decimal(2))
    assert m.remaining() == Decimal(6)
    m.set_external(Decimal(5))
    assert m.remaining() == Decimal(2)  # 10 - 1 - 2 - 5


def test_kill_switch_is_a_flag_file(tmp_path):
    k = KillSwitch(tmp_path / "d" / "off.flag")
    assert not k.is_on()
    k.on()
    assert k.is_on()
    k.off()
    k.off()
    assert not k.is_on()
