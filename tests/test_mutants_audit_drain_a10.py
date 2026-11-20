"""Killers for the A10 mutants (tests/audit_drain_a10_mutants.py applies each to src and runs THIS file)."""

from __future__ import annotations

from hadavin_sdk import defaults
from tests.test_audit_drain import _append_fails_for, _event, _ids, _park, _park_in_memory
from tests.test_audit_drain_a10 import _log, _psql


def test_m1_classifier_flipped_a_data_error_is_permanent_and_a_timeout_is_not():
    from hadavin_sdk.audit import chain

    assert chain._is_permanent(_psql("22001")) and chain._is_permanent(_psql("23505"))
    assert not chain._is_permanent(_psql("57014")) and not chain._is_permanent(_psql("40P01"))


def test_m2_limit_dropped_one_tick_drains_at_most_the_batch():
    log, _ = _log(drain_batch=3)
    for i in range(8):
        _park(log, _event(i, event_id=f"evt-{i}"))
    assert log.reconcile() == 3 and len(_ids(log)) == 3


def test_m3_quarantine_dropped_a_fresh_instance_per_tick_renames_the_old_row_and_keeps_it():
    from tests.test_audit_drain_a11 import (
        test_fresh_instance_per_tick_quarantines_an_old_poison_row_and_drains_past_it as t,
    )

    t()


def test_m4_backoff_cap_dropped_no_sleep_exceeds_the_cap(monkeypatch):
    monkeypatch.setattr(defaults, "AUDIT_FLUSH_ATTEMPTS", 10)
    log, sleeps = _log()
    a = _event(1)
    _park_in_memory(log, a)
    _append_fails_for(monkeypatch, log, OSError("down"), a)
    log._flush_pending()
    assert sleeps and max(sleeps) <= defaults.AUDIT_FLUSH_BACKOFF_MAX_S
