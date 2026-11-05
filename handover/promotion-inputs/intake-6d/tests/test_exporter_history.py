"""Historic receipts (errata 36c), result semantics (errata 36d), independence of the layers and the queue-accessor contract (WP5 review majors 1 to 3)."""

from __future__ import annotations

import dataclasses
import json
import sqlite3

import pytest
from queue_helpers import GOOD_FIELDS, REASON, new_item, raw_decision, raw_insert
from test_exporter import approved, csv_rows, fields, forging, item_row_id, item_state, receipts

from intake import codes, content_code, decisions, exporter, flags, sink_guard, textfold, validators, workqueue
from intake.sink_guard import COLUMNS

pytestmark = pytest.mark.filterwarnings("ignore")


@pytest.fixture
def s(intake_settings):
    return intake_settings


def exported_d06(s, name="hist", invoice="INV-H"):
    it = approved(s, name, fields(invoice_no=invoice), flags=("D06",), reason=REASON)
    assert exporter.export_row(s, it.id).ok
    return it


def stays(s, it, rid=None):
    rid = rid or item_row_id(it)
    run = exporter.export_pending(s)
    rows = csv_rows(s)
    assert run.ok and run.skipped == () and [r[0] for r in rows[1:]] == [rid], run
    return rows


# ---- MAJOR 1: a change of today's rules never removes an exported row ------------------------------------------------------------------------------
def test_currency_list_change_after_export_keeps_the_row(s):
    it = exported_d06(s)
    s2 = dataclasses.replace(s, service=dataclasses.replace(s.service, currencies=("EUR",)))
    stays(s2, it)


def test_reason_rule_change_after_export_keeps_the_row(s):
    it = exported_d06(s)
    s2 = dataclasses.replace(s, review=dataclasses.replace(s.review, reason_min_chars=400))
    stays(s2, it)


def test_flag_table_change_after_export_keeps_the_row(s, monkeypatch):
    it = exported_d06(s)
    monkeypatch.setattr(flags, "FLAGS", {k: v for k, v in flags.FLAGS.items() if k != "D06"})  # D06 no longer exists
    stays(s, it)
    assert dict(zip(COLUMNS, csv_rows(s)[1], strict=True))["flags"] == "D06"  # the stored row is written as it was


def test_reject_only_set_change_after_export_keeps_the_row(s, monkeypatch):
    it = exported_d06(s)
    monkeypatch.setattr(flags, "is_reject_only", lambda code: True)
    stays(s, it)


def test_may_approve_and_validators_and_row_id_and_fold_changes_keep_the_row(s, monkeypatch):
    it = exported_d06(s)
    before = exporter.csv_path(s).read_bytes()
    rid = item_row_id(it)
    monkeypatch.setattr(decisions, "may_approve", lambda *a, **k: False)
    monkeypatch.setattr(validators, "validate_record", lambda *a, **k: ["currency"])
    monkeypatch.setattr(content_code, "row_id", lambda *a, **k: "0" * 64)  # a policy change of invoice-number normalisation
    monkeypatch.setattr(textfold, "fold_text", lambda raw, **k: "swapped")
    monkeypatch.setattr(sink_guard, "fold_text", lambda raw, **k: "swapped")
    stays(s, it, rid)
    assert exporter.csv_path(s).read_bytes() == before


def test_a_row_stays_across_every_change_at_once_and_new_exports_still_use_todays_rules(s, monkeypatch):
    old = exported_d06(s)
    s2 = dataclasses.replace(s, service=dataclasses.replace(s.service, currencies=("EUR",)))
    new = approved(s, "newer", fields(invoice_no="INV-NEW"))  # USD, no longer a listed currency in s2
    run = exporter.export_pending(s2)
    assert [r.code for r in run.results] == ["not_approvable"] and run.file == "written"  # the NEW export is judged by today's rules
    assert [r[0] for r in csv_rows(s2)[1:]] == [item_row_id(old)]  # the old row is still there
    assert item_state(s, new) == "APPROVED"


# ---- loud failures --------------------------------------------------------------------------------------------------------------------------------
def tamper_row_json(s, it, mutate):
    conn = forging(s)
    row = json.loads(conn.execute("SELECT row_json FROM exports WHERE item_uid=?", (it.uid,)).fetchone()["row_json"])
    conn.execute("UPDATE exports SET row_json=? WHERE item_uid=?", (mutate(row), it.uid))
    conn.close()


@pytest.mark.parametrize(
    "mutate",
    [
        lambda row: json.dumps(dict(row, supplier_name="Evil Ltd")),
        lambda row: json.dumps({k: v for k, v in row.items() if k != "approved_by"}),
        lambda row: json.dumps(dict(row, extra="x")),
        lambda row: json.dumps(row)[:-1] + ', "supplier_name": "Dup"}',  # duplicate key
        lambda row: json.dumps(row)[:-1]
        + ", "
        + json.dumps("supplier_name")
        + ": "
        + json.dumps(row["supplier_name"])
        + "}",  # duplicate key, SAME value: only the strict seam refuses it
        lambda row: json.dumps(row).replace('"line_count": "2"', '"line_count": NaN'),  # NaN
        lambda row: "[1, 2]",
        lambda row: "not json",
    ],
)
def test_a_receipt_that_fails_integrity_is_skipped_and_reported_loudly(s, mutate):
    it = approved(s, "tamper")
    exporter.export_row(s, it.id)
    tamper_row_json(s, it, mutate)
    res = exporter.export_row(s, it.id)  # already_exported: the row will NOT land in the file, so this is not ok
    assert res.code == "already_exported" and res.exported and not res.ok and res.skipped == (item_row_id(it),)
    run = exporter.export_pending(s)
    assert run.skipped == (item_row_id(it),) and not run.ok and csv_rows(s) == [list(COLUMNS)]
    other = approved(s, "second", fields(invoice_no="INV-2"))
    res2 = exporter.export_row(s, other.id)
    assert res2.exported and res2.file == "written" and res2.skipped == (item_row_id(it),) and not res2.ok  # loud on every export


def test_an_error_that_is_not_a_verification_failure_propagates(s, monkeypatch):
    it = approved(s)
    exporter.export_row(s, it.id)

    def boom(conn):
        raise RuntimeError("programming error")

    monkeypatch.setattr(workqueue, "exports_in_order", boom)
    with pytest.raises(RuntimeError):
        exporter.export_pending(s)


# ---- MAJOR 3: result semantics ------------------------------------------------------------------------------------------------------------------------
def test_result_separates_the_item_from_the_file_and_has_plain_text(s):
    it = approved(s)
    res = exporter.export_row(s, it.id)
    assert (res.code, res.exported, res.file, res.skipped, res.ok) == ("exported", True, "written", (), True) and res.text == "exported"
    again = exporter.export_row(s, it.id)
    assert (again.code, again.exported, again.file, again.ok) == ("already_exported", True, None, True)
    refused = exporter.export_row(s, "nope")
    assert (refused.exported, refused.ok, refused.file) == (False, False, None) and refused.text == "no such item"
    for code in exporter.RESULT_TEXT:
        assert code in codes.CODES
    assert set(exporter.FILE_TEXT) == {"written", "sink_locked", "sink_error", "kill_switch", "db_error"}


def test_an_approved_item_that_already_has_a_receipt_is_not_a_success(s):
    it = approved(s)
    exporter.export_row(s, it.id)
    conn = forging(s)
    conn.execute("UPDATE items SET state='APPROVED' WHERE uid=?", (it.uid,))  # inconsistent: APPROVED with a receipt
    conn.close()
    res = exporter.export_row(s, it.id)
    assert res.code == "approval_mismatch" and not res.exported and not res.ok


def test_database_failures_are_returned_as_codes_not_raised(s, monkeypatch):
    it = approved(s)

    def locked(st):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(workqueue, "connect", locked)
    res = exporter.export_row(s, it.id)
    assert res.code == "db_busy" and not res.exported and not res.ok
    run = exporter.export_pending(s)
    assert run.file == "db_error" and run.results[0].code == "db_busy" and not run.ok

    def broken(st):
        raise sqlite3.DatabaseError("file is not a database")

    monkeypatch.setattr(workqueue, "connect", broken)
    assert exporter.export_row(s, it.id).code == "db_error"
    assert exporter.regenerate_file(s)[0] == "db_error"


def test_sink_error_is_reported_apart_from_sink_locked(s, monkeypatch):
    import errno

    it = approved(s)

    def full(src, dst):
        raise OSError(errno.ENOSPC, "disk full")

    monkeypatch.setattr(exporter.csvsink.os, "replace", full)
    res = exporter.export_row(s, it.id)
    assert res.exported and res.file == "sink_error" and not res.ok and not list(exporter.csv_path(s).parent.glob("*.tmp"))


# ---- MAJOR 4: the layers are independent (stub the rules the exporter calls and show it still refuses) -----------------------------------------------
def test_exporter_refuses_with_may_approve_and_validators_stubbed_open(s, monkeypatch, request):
    forged = []
    for i, (flag, f) in enumerate((('["D10"]', GOOD_FIELDS), ('["X10"]', GOOD_FIELDS), ("[]", None))):
        conn = forging(s)
        uid = raw_insert(conn, f"st{i}", "APPROVED", f, flag)
        it = workqueue.get_in(conn, f"st{i}")
        raw_decision(conn, uid, "approve", content_code.content_code(it))
        conn.close()
        forged.append(it)
    bad_total = forging(s)  # a record the validators would refuse, with a negative total (the sink guard is the last line)
    uid = raw_insert(bad_total, "negtotal", "APPROVED", fields(total_minor=-5), "[]")
    neg = workqueue.get_in(bad_total, "negtotal")
    raw_decision(bad_total, uid, "approve", content_code.content_code(neg))
    bad_total.close()
    forged.append(neg)
    monkeypatch.setattr(decisions, "may_approve", lambda *a, **k: True)
    monkeypatch.setattr(validators, "validate_record", lambda *a, **k: [])
    for it in forged:
        assert exporter.export_row(s, it.id).code == "not_approvable", it.id
    assert receipts(s) == []


def test_database_triggers_refuse_when_the_exporter_checks_are_stubbed_open(s, monkeypatch):
    # second line: with every Python rule stubbed open, trigger e still refuses a receipt for a latest REJECT decision
    it = approved(s)
    conn = forging(s)
    raw_decision(conn, it.uid, "reject", content_code.content_code(it))
    conn.close()
    real = exporter._eligible
    monkeypatch.setattr(
        exporter,
        "_eligible",
        lambda st, c, item: (
            workqueue.Decision(1, item.uid, "approve", "ap-a", None, content_code.content_code(item), "2026-11-03T00:00:00Z"),
            item_row_id(item),
            content_code.content_code(item),
        ),
    )
    assert exporter.export_row(s, it.id).code == "state_conflict" and receipts(s) == [] and real
    assert item_state(s, it) == "APPROVED"


# ---- MAJOR 2: the accessor contract (WP4 must meet it; this adapter is deleted at the rebase) --------------------------------------------------------
def test_accessor_return_types_and_order(s):
    a = approved(s, "a", fields(invoice_no="INV-A"))
    c = approved(s, "c", fields(invoice_no="INV-C"))
    new_item(s, "ready", fields(invoice_no="INV-R"))
    with workqueue.opened(s) as conn:
        d = workqueue.latest_decision(conn, a.uid)
        assert isinstance(d, workqueue.Decision) and d.decision == "approve" and d.item_uid == a.uid
        assert workqueue.latest_decision(conn, 99999) is None
        pend = workqueue.approved_unexported(conn)
        assert (
            isinstance(pend, list) and all(isinstance(i, workqueue.Item) for i in pend) and [i.id for i in pend] == [a.id, c.id]
        )  # oldest first
        assert isinstance(workqueue.get_by_uid(conn, a.uid), workqueue.Item) and workqueue.get_by_uid(conn, 99999) is None
    exporter.export_row(s, c.id)
    exporter.export_row(s, a.id)
    with workqueue.opened(s) as conn:
        recs = workqueue.exports_in_order(conn)
        assert all(isinstance(r, workqueue.Export) for r in recs) and [r.item_uid for r in recs] == [
            c.uid,
            a.uid,
        ]  # insertion order, ascending
        assert [r.seq for r in recs] == sorted(r.seq for r in recs)
        assert workqueue.approved_unexported(conn) == []
    raw = workqueue.Decision
    assert [f.name for f in dataclasses.fields(raw)] == ["seq", "item_uid", "decision", "approver", "reason", "content_code", "at"]


def test_latest_decision_is_the_highest_seq(s):
    it = approved(s)
    conn = forging(s)
    raw_decision(conn, it.uid, "reject", "c" * 64)
    conn.close()
    with workqueue.opened(s) as conn:
        assert workqueue.latest_decision(conn, it.uid).decision == "reject"


# ---- preview rows -------------------------------------------------------------------------------------------------------------------------------------
def test_preview_rows_show_the_row_or_the_refusal_and_write_nothing(s):
    ok = approved(s, "okay", fields(invoice_no="=1+1"))
    conn = forging(s)
    uid = raw_insert(conn, "bad", "APPROVED", GOOD_FIELDS, '["D10"]')
    raw_decision(conn, uid, "approve", "d" * 64)
    conn.close()
    rows = {p.item_id: p for p in exporter.preview_rows(s)}
    assert rows[ok.id].refusal is None and rows[ok.id].row["invoice_no"] == "'=1+1" and rows[ok.id].row["row_id"] == item_row_id(ok)
    assert rows["bad"].row is None and rows["bad"].refusal == "not_approvable"
    assert receipts(s) == [] and not exporter.csv_path(s).exists() and item_state(s, ok) == "APPROVED"


# ---- the caps are WP0 validators (errata 36a); the exporter relies on them and the guard cap is the last line ------------------------------------
def test_validators_cap_the_hashed_text_fields():
    for key, n in (("invoice_no", 65), ("po_ref", 65), ("supplier_name", 201), ("invoice_date", 33)):
        assert validators.validate_record(fields(**{key: "x" * n}), ["USD"]) == [key]
