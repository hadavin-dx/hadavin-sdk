"""Round 7U: tests for the independent r7t review (1 Major, 8 Minor, 5 Nit). Made-up data only, loopback only; no real
service, no spend, no sleep, no real kill (a stop is forced by a hook that raises a BaseException).

Before/after on a plain copy of r7t: see out/R7U/R7U-RESULTS.md. FAILS = fails on the r7t sources. PIN = the r7t code was
already right; the test passes on both and exists to kill a named mutant or to state a rule.

  u1   M1  `created` is never capped; only the open part is (rule, oracle, main-level exit code and message)      FAILS
  u1b  m1  a retry in the same desk process takes back its unknown create (exact); another desk process is an
           over-count in the safe direction (pinned, stated)                                                      FAILS (3), PIN (2)
  u2   m2  counter values: only whole numbers >= 0 (type int); ArithmeticError never a crash                      FAILS
  u3   m3  counter_known and unseen are in the result BEFORE it is written; no "ALL CHECKS HOLD" when
           the counter is unknown or contacts are unaccounted for                                                  FAILS
  u4   m4  the read-back-failed note uses the checked reader and shows open and unknown creates                    FAILS
  u5   m5  a counter that turns unreadable AFTER contacts exist (the case the r7t t9 test 2 does not reach)       PIN
  u7   m7  the mail counter is read with the checked reader: unreadable = not known = F4 fails                    FAILS
  u8   m8  LOCALHOST and the other spellings are accepted by design: a rule, not a promise of a listener          FAILS
  u6   m6  the loopback rule lives in one light module; the two raw-socket fakes import nothing heavy             FAILS
  u9   _settle_create raises; two concurrent puts; a 201 without an id                                           PIN
  n1/n2 docstrings                                                                                               FAILS
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

import pytest
from support import REPO, script_module

rrc = script_module("run_real_check")


class _Killed(BaseException):
    """Stands for a hard kill: not an Exception, so nothing after the raise runs."""


def _stats(path: Path) -> dict[str, int]:
    return json.loads(path.read_text(encoding="utf-8"))


def _crm(rig: Any, tmp_path: Path, label: str = "1") -> tuple[Any, Path]:
    stats = tmp_path / f"desk-rabcdef-{label}.hubspot.json"
    return rig.crm(stats_file=stats), stats


# -- u1 (M1): the counting rule -------------------------------------------------------------------------------------


def _oracle(created: int, accounted: int, open_creates: int, leads: int) -> int:
    """The most contacts that can exist, minus the contacts the list showed. The desk's `created` is a count of 201
    replies and is never capped; each open create may have made one more contact, but a lead makes at most one."""
    most = max(created, min(created + max(0, open_creates), leads))
    return max(0, most - accounted)


@pytest.mark.parametrize("n", [1, 2, 5, 9])
def test_u1_one_more_created_than_leads_is_never_hidden_by_the_cap(n: int) -> None:
    f = rrc.contacts_not_accounted_for
    assert f(n + 1, n, 0, n) == 1  # r7t: min(n+1, n) - n = 0 (blind)
    assert f(n + 2, n, 0, n) == 2
    assert f(n + 1, n, 1, n) == 1  # an open create on top does not add to a count that is already over the book
    assert f(n + 1, 0, 0, n) == n + 1


def test_u1_the_rule_equals_the_oracle_on_every_small_input() -> None:
    f = rrc.contacts_not_accounted_for
    for created in range(0, 8):
        for accounted in range(0, 9):
            for open_creates in range(-1, 8):
                for leads in range(0, 9):
                    assert f(created, accounted, open_creates, leads) == _oracle(
                        created, accounted, open_creates, leads
                    ), (created, accounted, open_creates, leads)


def test_u1_named_values_of_the_rule() -> None:
    f = rrc.contacts_not_accounted_for
    assert f(9, 9, 5, 9) == 0  # an open create retried by the next desk: only 9 leads
    assert f(5, 5, 5, 9) == 4  # the open part is capped by the leads still without a created contact (9 - 5)
    assert f(3, 3, 100, 5) == 2
    assert f(3, 0, 100, 5) == 5
    assert f(10, 0, 0, 9) == 10  # created is not capped
    assert f(8, 8, 1, 9) == 1 and f(8, 9, 1, 9) == 0 and f(8, 8, 0, 9) == 0
    assert f(8, 4, -3, 9) == 4  # a negative open number never lowers the possible number
    assert f(0, 0, 1, None) == 1  # no lead count given: created + open
    assert f(12, 0, 3, None) == 15


def _more_created(monkeypatch: pytest.MonkeyPatch, extra: int) -> None:
    """The HubSpot counter of the real dry run reads `extra` created contacts higher (a contact made twice or one the
    book does not know)."""
    real = rrc.read_counter_files_checked

    def reader(run_dir: Path, suffix: str, tag: str) -> Any:
        read = real(run_dir, suffix, tag)
        if suffix != ".hubspot.json":
            return read
        totals = dict(read.totals)
        totals["created"] += extra
        return rrc.CounterRead(totals, read.files, read.unreadable)

    monkeypatch.setattr(rrc, "read_counter_files_checked", reader)


def _hiding_crm(hidden: int, extra_rows: list[tuple[str, str]] | None = None) -> type:
    class Hiding(rrc.HubspotCrm):
        """A CRM whose LIST shows `hidden` contacts fewer than exist (list lag), and `extra_rows` more."""

        def rows_with_prefix(self, prefix: str) -> list[tuple[str, str]]:
            rows = super().rows_with_prefix(prefix)
            return rows[: len(rows) - hidden] + list(extra_rows or [])

    return Hiding


def test_u1_an_out_of_book_contact_ends_the_run_as_failed(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """One more contact was created than the book has leads: it carries an L id the book does not know, so the read-back
    filter drops it and nothing archives it. r7s said 1; r7t said 0 (exit 0 with a contact left)."""
    monkeypatch.setattr(rrc, "HubspotCrm", _hiding_crm(0, [("L-not-in-the-book", "999")]))
    monkeypatch.setattr(rrc, "floor_checks", lambda *_a, **_k: [])
    _more_created(monkeypatch, 1)
    code = rrc.main(["--dry-fakes", "--assume-yes", "--cleanup"])
    out = capsys.readouterr().out
    assert code == rrc.EXIT_FAILED and "1 contacts may be left" in out, out[-2000:]


def test_u1_a_duplicate_create_under_list_lag_is_counted_whole(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A lead got a second contact (created one too many) and the list hid one contact: two are not accounted for. r7t
    said 1 (the cap cut the created number)."""
    monkeypatch.setattr(rrc, "HubspotCrm", _hiding_crm(1))
    monkeypatch.setattr(rrc, "floor_checks", lambda *_a, **_k: [])
    _more_created(monkeypatch, 1)
    code = rrc.main(["--dry-fakes", "--assume-yes", "--cleanup"])
    out = capsys.readouterr().out
    assert code == rrc.EXIT_FAILED and "2 contacts may be left" in out, out[-2000:]


# -- u1b (m1): a create that ended unknown and was retried -----------------------------------------------------------
#
# Rule: a lead makes at most one contact. Inside ONE desk process the adapter remembers the leads whose create ended
# unknown: a later 201 for the same lead proves the earlier create stored nothing, so it takes the unknown back in the
# same write; a second unknown for the same lead is not counted again; a 409 keeps the unknown (that contact exists).
# Across desk processes (the crash drill restarts the desk) the counters carry no lead ids, so a retry in another
# process stays an over-count by one: the safe direction (a false alarm, never a miss), pinned below.


def _fail_first_requests(monkeypatch: pytest.MonkeyPatch, times: int, *, store: bool) -> list[int]:
    from lead_desk.crm_hubspot import CrmError, HubspotCrm

    real = HubspotCrm._once
    calls: list[int] = []

    def once(self: Any, method: str, path: str, obj: Any, deadline: float, key: str) -> Any:
        calls.append(1)
        if len(calls) <= times:
            if store:
                real(self, method, path, obj, deadline, key)  # HubSpot made the contact, the reply is lost
            raise CrmError("connection dropped")
        return real(self, method, path, obj, deadline, key)

    monkeypatch.setattr(HubspotCrm, "_once", once)
    return calls


def test_u1b_a_create_that_ended_unknown_and_was_retried_with_a_201_is_counted_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from test_crm_hubspot import REC, Rig

    from lead_desk.crm_hubspot import CrmError

    rig = Rig(tmp_path)
    try:
        crm, stats = _crm(rig, tmp_path)
        _fail_first_requests(monkeypatch, 1, store=False)
        with pytest.raises(CrmError):
            crm.put("L-1", REC)
        assert (_stats(stats)["create_unknown"], _stats(stats)["created"]) == (1, 0)
        assert crm.put("L-1", REC) == "PUT"
        written = _stats(stats)
        assert (written["created"], written["create_unknown"], written["create_open"]) == (1, 0, 0), written
        assert len(rig.state.contacts) == 1
        assert rrc.contacts_not_accounted_for(written["created"], 1, written["create_unknown"], 1) == 0
    finally:
        rig.stop()


def test_u1b_a_retry_that_ends_unknown_again_is_not_counted_twice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from test_crm_hubspot import REC, Rig

    from lead_desk.crm_hubspot import CrmError

    rig = Rig(tmp_path)
    try:
        crm, stats = _crm(rig, tmp_path)
        _fail_first_requests(monkeypatch, 2, store=False)
        for _ in range(2):
            with pytest.raises(CrmError):
                crm.put("L-1", REC)
        assert _stats(stats)["create_unknown"] == 1, _stats(stats)  # one lead: at most one contact
        crm.put("L-2", {**REC, "email": "second@example.test"})  # another lead is its own count
        assert _stats(stats)["created"] == 1 and _stats(stats)["create_unknown"] == 1
    finally:
        rig.stop()


def test_u1b_an_unknown_create_that_did_store_and_is_then_met_by_a_409_keeps_one_possible_contact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from test_crm_hubspot import REC, Rig

    from lead_desk.crm_hubspot import CrmError

    rig = Rig(tmp_path)
    try:
        crm, stats = _crm(rig, tmp_path)
        _fail_first_requests(monkeypatch, 1, store=True)
        with pytest.raises(CrmError):
            crm.put("L-1", REC)
        assert crm.put("L-1", REC) == "ALREADY_PRESENT"
        written = _stats(stats)
        assert (written["created"], written["conflicts"], written["create_unknown"]) == (0, 1, 1), written
        assert len(rig.state.contacts) == 1
        assert rrc.contacts_not_accounted_for(0, 0, 1, 1) == 1  # the list hides it: reported
        assert rrc.contacts_not_accounted_for(0, 1, 1, 1) == 0  # the list shows it: no false alarm
    finally:
        rig.stop()


def test_u1b_a_201_after_an_unknown_of_another_lead_takes_nothing_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from test_crm_hubspot import REC, Rig

    from lead_desk.crm_hubspot import CrmError

    rig = Rig(tmp_path)
    try:
        crm, stats = _crm(rig, tmp_path)
        _fail_first_requests(monkeypatch, 1, store=True)
        with pytest.raises(CrmError):
            crm.put("L-1", REC)
        crm.put("L-2", {**REC, "email": "second@example.test"})
        written = _stats(stats)
        assert (written["created"], written["create_unknown"]) == (1, 1), written  # L-1 may exist, L-2 was made
    finally:
        rig.stop()


def test_u1b_a_retry_in_another_desk_process_is_an_over_count_in_the_safe_direction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """PIN of the stated residual: the counters carry no lead ids, so desk 2 cannot take back desk 1's unknown. One
    lead made one contact; the sum says created 1 + unknown 1 for a book of 2 leads. The run reports 1 possible
    contact too many (a false alarm that a person checks in HubSpot in a minute), never one too few."""
    from test_crm_hubspot import REC, Rig

    from lead_desk.crm_hubspot import CrmError

    rig = Rig(tmp_path)
    try:
        crm1, stats1 = _crm(rig, tmp_path, "1")
        crm2, stats2 = _crm(rig, tmp_path, "2")
        _fail_first_requests(monkeypatch, 1, store=False)
        with pytest.raises(CrmError):
            crm1.put("L-1", REC)
        crm2.put("L-1", REC)
        read = rrc.read_counter_files_checked(tmp_path, ".hubspot.json", "rabcdef")
        assert (read.totals["created"], read.totals["create_unknown"]) == (1, 1), read.totals
        assert len(rig.state.contacts) == 1
        # 2 leads in the book, one of them never got a contact: the over-count shows
        assert rrc.contacts_not_accounted_for(1, 1, 1, 2) == 1
        assert rrc.contacts_not_accounted_for(1, 1, 1, 1) == 0  # every lead has its contact: the cap absorbs it
    finally:
        rig.stop()


# -- u2 (m2): counter values ------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    ["1e999", "-1", "0.9", "1.0", "true", "false", '"5"', "null", "[1]", "{}", "1" + "0" * 5000],
    ids=lambda v: v[:12],
)
def test_u2_a_counter_value_that_is_not_a_whole_number_from_zero_is_unreadable(tmp_path: Path, value: str) -> None:
    (tmp_path / "desk-raaaaaa-1.hubspot.json").write_text('{"created": ' + value + "}", encoding="utf-8")
    read = rrc.read_counter_files_checked(tmp_path, ".hubspot.json", "raaaaaa")
    assert (read.files, read.unreadable) == (1, 1) and not rrc.counter_is_known(read)
    assert read.totals == {}  # the file is taken whole or not at all


def test_u2_whole_numbers_from_zero_are_read(tmp_path: Path) -> None:
    (tmp_path / "desk-raaaaaa-1.hubspot.json").write_text('{"created": 0, "calls": 3, "big": 12345678901234567890}')
    read = rrc.read_counter_files_checked(tmp_path, ".hubspot.json", "raaaaaa")
    assert read.totals == {"created": 0, "calls": 3, "big": 12345678901234567890}
    assert (read.files, read.unreadable) == (1, 0) and rrc.counter_is_known(read)


def test_u2_one_bad_value_makes_the_whole_file_unreadable_and_adds_nothing(tmp_path: Path) -> None:
    (tmp_path / "desk-raaaaaa-1.hubspot.json").write_text('{"calls": 3, "created": -2}', encoding="utf-8")
    (tmp_path / "desk-raaaaaa-2.hubspot.json").write_text('{"calls": 4, "created": 2}', encoding="utf-8")
    read = rrc.read_counter_files_checked(tmp_path, ".hubspot.json", "raaaaaa")
    assert (read.totals, read.files, read.unreadable) == ({"calls": 4, "created": 2}, 2, 1)
    assert not rrc.counter_is_known(read)


@pytest.mark.parametrize("error", [OverflowError("x"), ZeroDivisionError("x"), ArithmeticError("x")], ids=repr)
def test_u2_an_arithmetic_error_while_reading_is_an_unreadable_file_never_a_crash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: ArithmeticError
) -> None:
    (tmp_path / "desk-raaaaaa-1.hubspot.json").write_text('{"created": 1}', encoding="utf-8")

    def raising(*_a: Any, **_k: Any) -> Any:
        raise error

    monkeypatch.setattr(rrc, "load_json_file", raising)
    read = rrc.read_counter_files_checked(tmp_path, ".hubspot.json", "raaaaaa")
    assert (read.files, read.unreadable) == (1, 1)


# -- u3 (m3): the saved result and the table say the same as the exit code --------------------------------------------


def _capture_results(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Record every payload handed to write_result at the moment it is handed over (the file holds exactly this)."""
    real = rrc.write_result
    seen: list[dict[str, Any]] = []

    def spy(out: Path, payload: dict[str, Any]) -> bool:
        seen.append(json.loads(json.dumps(payload, default=str)))
        return real(out, payload)

    monkeypatch.setattr(rrc, "write_result", spy)
    return seen


def _hide_hubspot_counter(monkeypatch: pytest.MonkeyPatch) -> None:
    real = rrc.read_counter_files_checked

    def reader(run_dir: Path, suffix: str, tag: str) -> Any:
        return rrc.CounterRead({}, 0, 0) if suffix == ".hubspot.json" else real(run_dir, suffix, tag)

    monkeypatch.setattr(rrc, "read_counter_files_checked", reader)


def test_u3_a_counter_that_is_not_known_is_in_the_result_and_the_result_is_not_ok(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    seen = _capture_results(monkeypatch)
    _hide_hubspot_counter(monkeypatch)
    code = rrc.main(["--dry-fakes", "--assume-yes", "--cleanup"])
    out = capsys.readouterr().out
    assert code == rrc.EXIT_FAILED, out[-1500:]
    (payload,) = seen
    assert payload["summary"]["counter_known"] is False and payload["summary"]["unseen_contacts"] == 0
    assert payload["checks"]["ok"] is False  # r7t: True here (the file said ok with an unknown counter)
    assert any(c["id"] == "F7" and c["ok"] is False for c in payload["checks"]["checks"])
    assert "ALL CHECKS HOLD" not in out and "AT LEAST ONE CHECK FAILED" in out, out[-2500:]


def test_u3_contacts_not_accounted_for_are_in_the_result_and_the_result_is_not_ok(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    seen = _capture_results(monkeypatch)
    monkeypatch.setattr(rrc, "HubspotCrm", _hiding_crm(1))
    _more_created(monkeypatch, 0)
    code = rrc.main(["--dry-fakes", "--assume-yes", "--cleanup"])
    out = capsys.readouterr().out
    (payload,) = seen
    assert code == rrc.EXIT_FAILED, out[-1500:]
    assert payload["summary"]["counter_known"] is True and payload["summary"]["unseen_contacts"] == 1, payload[
        "summary"
    ]
    assert payload["checks"]["ok"] is False and "ALL CHECKS HOLD" not in out, out[-2500:]


def test_u3_a_clean_run_says_so_in_the_result_and_the_table(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    seen = _capture_results(monkeypatch)
    code = rrc.main(["--dry-fakes", "--assume-yes", "--cleanup"])
    out = capsys.readouterr().out
    (payload,) = seen
    assert code == 0, out[-1500:]
    assert payload["summary"]["counter_known"] is True and payload["summary"]["unseen_contacts"] == 0
    assert payload["checks"]["ok"] is True and "ALL CHECKS HOLD" in out
    assert any(c["id"] == "F7" and c["ok"] is True for c in payload["checks"]["checks"])


def test_u3_the_counter_check_names_no_number_that_is_not_a_count() -> None:
    ok = rrc.counter_check(True, 0, {"created": 3, "create_open": 0, "create_unknown": 0})
    assert ok["id"] == "F7" and ok["ok"] is True and ok["offender_count"] == 0
    for known, unseen in [(False, 0), (True, 1), (False, 2)]:
        bad = rrc.counter_check(known, unseen, {})
        assert bad["ok"] is False, (known, unseen)
    assert "unknown" in rrc.counter_check(False, 0, {})["detail"]
    assert "1" in rrc.counter_check(True, 1, {"created": 3})["detail"]


# -- u4 (m4): the read-back-failed note -------------------------------------------------------------------------------


def _readback_stops(monkeypatch: pytest.MonkeyPatch) -> None:
    class Stops(rrc.HubspotCrm):
        def rows_with_prefix(self, prefix: str) -> list[tuple[str, str]]:
            raise rrc.CrmError("the read-back stopped")

    monkeypatch.setattr(rrc, "HubspotCrm", Stops)


def _counter_totals(monkeypatch: pytest.MonkeyPatch, **more: int) -> None:
    real = rrc.read_counter_files_checked

    def reader(run_dir: Path, suffix: str, tag: str) -> Any:
        read = real(run_dir, suffix, tag)
        if suffix != ".hubspot.json":
            return read
        return rrc.CounterRead({**read.totals, **more}, read.files, read.unreadable)

    monkeypatch.setattr(rrc, "read_counter_files_checked", reader)


def test_u4_the_readback_note_shows_the_open_and_unknown_creates(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    seen = _capture_results(monkeypatch)
    _readback_stops(monkeypatch)
    _counter_totals(monkeypatch, create_open=1, create_unknown=2)
    code = rrc.main(["--dry-fakes", "--assume-yes", "--cleanup"])
    out = capsys.readouterr().out
    assert code == rrc.EXIT_FAILED
    note = seen[-1]["note"]
    assert "1 create requests were still open and 2 ended with an unknown outcome" in note, note
    assert note in out


def test_u4_the_readback_note_does_not_name_a_number_when_the_counter_is_not_known(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    seen = _capture_results(monkeypatch)
    _readback_stops(monkeypatch)
    real = rrc.read_counter_files_checked

    def reader(run_dir: Path, suffix: str, tag: str) -> Any:
        read = real(run_dir, suffix, tag)
        if suffix != ".hubspot.json":
            return read
        return rrc.CounterRead({**read.totals, "created": 5}, read.files, read.unreadable + 1)  # one file failed

    monkeypatch.setattr(rrc, "read_counter_files_checked", reader)
    code = rrc.main(["--dry-fakes", "--assume-yes", "--cleanup"])
    capsys.readouterr()
    assert code == rrc.EXIT_FAILED
    note = seen[-1]["note"]
    assert "an unknown number of" in note and "created 5" not in note and " 5 contacts" not in note, note


# -- u5 (m5): the counter file turns unreadable AFTER the contacts exist ------------------------------------------------


def test_u5_a_counter_that_is_unreadable_while_contacts_exist_and_one_is_hidden_ends_as_failed(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The real desk processes wrote real contacts and a real counter; the counter file is then cut in half (a hard
    stop in a write on a system with no atomic replace, a full disk) and the list hides one contact (floor F3 silent).
    The run must end failed and say the counter cannot be trusted. (PIN: r7t already fails closed here.)"""
    monkeypatch.setattr(rrc, "HubspotCrm", _hiding_crm(1))
    monkeypatch.setattr(rrc, "floor_checks", lambda *_a, **_k: [])
    real = rrc.read_counter_files_checked

    def reader(run_dir: Path, suffix: str, tag: str) -> Any:
        if suffix == ".hubspot.json":
            for p in sorted(run_dir.glob(f"desk-{tag}-*{suffix}")):
                p.write_text(p.read_text(encoding="utf-8")[:12], encoding="utf-8")
        return real(run_dir, suffix, tag)

    monkeypatch.setattr(rrc, "read_counter_files_checked", reader)
    code = rrc.main(["--dry-fakes", "--assume-yes", "--cleanup"])
    out = capsys.readouterr().out
    assert code == rrc.EXIT_FAILED and "counter cannot be trusted" in out, out[-2000:]


# -- u7 (m7): the mail counter ------------------------------------------------------------------------------------------


def _smtp_reader(monkeypatch: pytest.MonkeyPatch, *, files: int | None = None, unreadable: int | None = None) -> None:
    real = rrc.read_counter_files_checked

    def reader(run_dir: Path, suffix: str, tag: str) -> Any:
        read = real(run_dir, suffix, tag)
        if suffix != ".smtp.json":
            return read
        return rrc.CounterRead(
            read.totals,
            read.files if files is None else files,
            read.unreadable if unreadable is None else unreadable,
        )

    monkeypatch.setattr(rrc, "read_counter_files_checked", reader)


def test_u7_an_unreadable_mail_counter_file_is_not_a_smaller_number_it_is_not_known(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """One of the desks' mail counter files cannot be read; the other gave a number. r7t used the partial sum and F4
    could hold with a mail missing from it; r7u: the desk's mail count is not known and F4 fails."""
    seen = _capture_results(monkeypatch)
    _smtp_reader(monkeypatch, unreadable=1)
    code = rrc.main(["--dry-fakes", "--assume-yes", "--cleanup"])
    out = capsys.readouterr().out
    (payload,) = seen
    assert code == rrc.EXIT_FAILED, out[-1500:]
    f4 = next(c for c in payload["checks"]["checks"] if c["id"] == "F4")
    assert f4["ok"] is False
    assert payload["summary"]["smtp_counter_known"] is False
    assert payload["summary"]["mails_sent_by_the_desk_total"] is None


def test_u7_a_missing_mail_counter_file_fails_the_floor(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    seen = _capture_results(monkeypatch)
    real = rrc.read_counter_files_checked

    def reader(run_dir: Path, suffix: str, tag: str) -> Any:
        return rrc.CounterRead({}, 0, 0) if suffix == ".smtp.json" else real(run_dir, suffix, tag)

    monkeypatch.setattr(rrc, "read_counter_files_checked", reader)
    code = rrc.main(["--dry-fakes", "--assume-yes", "--cleanup"])
    capsys.readouterr()
    assert code == rrc.EXIT_FAILED
    assert next(c for c in seen[0]["checks"]["checks"] if c["id"] == "F4")["ok"] is False
    assert seen[0]["summary"]["smtp_counter_known"] is False


def test_u7_a_readable_mail_counter_is_known(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    seen = _capture_results(monkeypatch)
    code = rrc.main(["--dry-fakes", "--assume-yes", "--cleanup"])
    capsys.readouterr()
    assert code == 0 and seen[0]["summary"]["smtp_counter_known"] is True
    assert isinstance(seen[0]["summary"]["mails_sent_by_the_desk_total"], int)


def test_u7_the_mail_counter_rule() -> None:
    f = rrc.smtp_counter_known
    assert f(rrc.CounterRead({"sent": 0, "attempts": 0}, 1, 0)) is True
    assert f(rrc.CounterRead({"attempts": 3}, 1, 0)) is False  # no number of sent mails
    assert f(rrc.CounterRead({"sent": 3}, 0, 0)) is False  # no file
    assert f(rrc.CounterRead({"sent": 3}, 2, 1)) is False  # one file unreadable


# -- u8 (m8): the rule says "this computer", not "a listener will start" ------------------------------------------------


def test_u8_the_loopback_rule_accepts_these_spellings_by_design_and_says_it_does_not_promise_a_listener() -> None:
    from lead_desk import loopback

    for host in ("LOCALHOST", "localhost", "127.0.0.1", "[::1]", "::1", "::ffff:127.0.0.1"):
        assert loopback.is_loopback_host(host) is True, host
    for host in ("0.0.0.0", "::", "", "example.com", "[::", "::1%eth0", "192.0.2.1"):
        assert loopback.is_loopback_host(host) is False, host
    doc = loopback.__doc__ or ""
    assert "by design" in doc and "LOCALHOST" in doc and "does not" in doc and "listen" in doc, doc


# -- u6 (m6): one light module ------------------------------------------------------------------------------------------


LIGHT = REPO / "src" / "lead_desk" / "loopback.py"
HEAVY = ("lead_desk.config", "scripts.http_guard", "tools.refusing_args", "lead_desk.constants", "lead_desk.envnum")


def test_u6_the_light_module_imports_only_the_standard_library() -> None:
    tree = ast.parse(LIGHT.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            names.add((node.module or "").split(".")[0])
    assert names <= {"__future__", "ipaddress"}, names


def test_u6_the_two_raw_socket_fakes_import_nothing_heavy_in_a_fresh_interpreter() -> None:
    code = (
        "import sys\n"
        f"sys.path[:0] = [{str(REPO / 'src')!r}, {str(REPO)!r}]\n"
        "import demo_only.fake_imap, demo_only.fake_smtp_tls\n"
        f"heavy = [m for m in {list(HEAVY)!r} if m in sys.modules]\n"
        "print('HEAVY=' + ','.join(heavy))\n"
        "print('LIGHT=' + str('lead_desk.loopback' in sys.modules))\n"
    )
    done = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, timeout=60, check=False)
    assert done.returncode == 0, done.stderr[-1500:]
    assert "HEAVY=\n" in done.stdout + "\n" and "LIGHT=True" in done.stdout, done.stdout


def test_u6_the_light_module_alone_on_the_path_imports() -> None:
    """Only the folder of the module on the path: it must not need any other file of the repository."""
    code = (
        "import sys, importlib.util\n"
        f"spec = importlib.util.spec_from_file_location('loopback', {str(LIGHT)!r})\n"
        "m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)\n"
        "assert m.require_loopback_host('127.0.0.1') == '127.0.0.1'\n"
        "print('OK')\n"
    )
    done = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, timeout=60, check=False)
    assert done.returncode == 0 and "OK" in done.stdout, done.stderr[-1500:]


def test_u6_there_is_one_rule_and_one_text() -> None:
    from demo_only import bad_request
    from lead_desk import config, loopback
    from tools import refusing_args

    assert config.is_loopback_host is loopback.is_loopback_host
    assert bad_request.require_loopback_host is loopback.require_loopback_host
    assert refusing_args.LOOPBACK_HOST_TEXT is loopback.LOOPBACK_HOST_TEXT
    for bad in (None, 5, b"127.0.0.1", "", "0.0.0.0"):
        with pytest.raises(ValueError, match=loopback.LOOPBACK_HOST_TEXT):
            loopback.require_loopback_host(bad)


# -- u9: gaps the review named in the new tests of r7t ------------------------------------------------------------------


def test_u9_a_put_whose_settle_raises_leaves_the_create_open_which_is_the_safe_side(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from test_crm_hubspot import REC, Rig

    from lead_desk.crm_hubspot import HubspotCrm

    rig = Rig(tmp_path)
    try:
        crm, stats = _crm(rig, tmp_path)

        def boom(self: Any, outcome: str | None) -> None:
            raise RuntimeError("settle failed")

        monkeypatch.setattr(HubspotCrm, "_settle_create", boom)
        with pytest.raises(RuntimeError, match="settle failed"):
            crm.put("L-1", REC)
        written = _stats(stats)
        assert (written["created"], written["create_open"]) == (0, 1), written
        assert len(rig.state.contacts) == 1
        assert rrc.contacts_not_accounted_for(0, 0, 1, 1) == 1  # still reported when the list hides it
        assert rrc.contacts_not_accounted_for(0, 1, 1, 1) == 0
    finally:
        rig.stop()


def test_u9_two_puts_at_the_same_time_are_two_open_creates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from test_crm_hubspot import REC, Rig

    from lead_desk.crm_hubspot import HubspotCrm

    rig = Rig(tmp_path)
    try:
        crm, stats = _crm(rig, tmp_path)
        entered = threading.Barrier(3, timeout=20)  # two puts and this test
        go = threading.Event()
        real = HubspotCrm._once

        def once(self: Any, method: str, path: str, obj: Any, deadline: float, key: str) -> Any:
            entered.wait()  # both creates have been written as open before either request leaves
            assert go.wait(20)
            return real(self, method, path, obj, deadline, key)

        monkeypatch.setattr(HubspotCrm, "_once", once)
        errors: list[BaseException] = []

        def put(n: int) -> None:
            try:
                crm.put(f"L-{n}", {**REC, "email": f"p{n}@example.test"})
            except BaseException as e:  # noqa: BLE001  (handed to the test thread)
                errors.append(e)

        threads = [threading.Thread(target=put, args=(n,)) for n in (1, 2)]
        for t in threads:
            t.start()
        entered.wait()
        try:
            assert _stats(stats)["create_open"] == 2, _stats(stats)
        finally:
            go.set()
            for t in threads:
                t.join(20)
        assert not errors, errors
        done = _stats(stats)
        assert (done["created"], done["create_open"]) == (2, 0), done
    finally:
        rig.stop()


def test_u9_a_201_without_an_id_is_an_unknown_create(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from test_crm_hubspot import REC, Rig

    from lead_desk.crm_hubspot import CrmError, HubspotCrm, _Reply

    rig = Rig(tmp_path)
    try:
        crm, stats = _crm(rig, tmp_path)
        real = HubspotCrm._once

        def once(self: Any, method: str, path: str, obj: Any, deadline: float, key: str) -> Any:
            real(self, method, path, obj, deadline, key)  # HubSpot made the contact
            return _Reply(201, {}, None)  # and answered 201 with no id

        monkeypatch.setattr(HubspotCrm, "_once", once)
        with pytest.raises(CrmError):
            crm.put("L-1", REC)
        written = _stats(stats)
        assert (written["created"], written["create_open"], written["create_unknown"]) == (0, 0, 1), written
    finally:
        rig.stop()


# -- n1, n2: the texts ------------------------------------------------------------------------------------------------


def test_n1_the_counters_file_text_does_not_say_that_no_test_checks_atomicity() -> None:
    from lead_desk import run_stats

    doc = run_stats.__doc__ or ""
    assert "no test checks atomicity" not in doc
    assert "write_stats_strict" in doc and "create_open" in doc and "tests/test_r7t_findings.py" in doc, doc


def test_n2_the_hubspot_adapter_text_names_the_create_counters_and_the_refusal() -> None:
    from lead_desk import crm_hubspot

    doc = crm_hubspot.__doc__ or ""
    for word in ("create_open", "create_unknown", "CrmCounterUnwritable"):
        assert word in doc, word
