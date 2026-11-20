"""Killers for the A10 mutants (tests/audit_drain_a10_mutants.py applies each to src and runs THIS file)."""

from __future__ import annotations

import pytest

from hadavin_sdk import defaults
from tests.test_audit_drain import _append_fails_for, _event, _ids, _park, _park_in_memory, _refuse
from tests.test_audit_drain_a10 import _ids_in_outbox, _log, _psql


def test_m1_classifier_flipped_a_data_error_is_permanent_and_a_timeout_is_not():
    from hadavin_sdk.audit import chain

    assert chain._is_permanent(_psql("22001")) and chain._is_permanent(_psql("23505"))
    assert not chain._is_permanent(_psql("57014")) and not chain._is_permanent(_psql("40P01"))


def test_m2_limit_dropped_one_tick_drains_at_most_the_batch():
    log, _ = _log(drain_batch=3)
    for i in range(8):
        _park(log, _event(i, event_id=f"evt-{i}"))
    assert log.reconcile() == 3 and len(_ids(log)) == 3


def test_m3_quarantine_dropped_the_row_is_renamed_after_n_ticks_and_kept():
    log, _ = _log()
    bad = _event(0, event_id="evt-bad")
    _park(log, bad)
    _refuse(log, bad)
    for _ in range(defaults.AUDIT_QUARANTINE_AFTER_TICKS):
        with pytest.raises(RuntimeError):
            log.reconcile()
    assert _ids_in_outbox(log) == ["poison:evt-bad"]


def test_m4_backoff_cap_dropped_no_sleep_exceeds_the_cap(monkeypatch):
    monkeypatch.setattr(defaults, "AUDIT_FLUSH_ATTEMPTS", 10)
    log, sleeps = _log()
    a = _event(1)
    _park_in_memory(log, a)
    _append_fails_for(monkeypatch, log, OSError("down"), a)
    log._flush_pending()
    assert sleeps and max(sleeps) <= defaults.AUDIT_FLUSH_BACKOFF_MAX_S
