"""The exporter (spec 9, invariant I2): only approved items reach the CSV; the content code is recomputed; the CSV is regenerated from the receipts.
Hostile database states are built with a hand-written SQL on a connection whose triggers were dropped (the exporter's own check must hold without them)."""

from __future__ import annotations

import copy
import csv
import errno
import json
import subprocess
import sys
import textwrap
import threading
from pathlib import Path

import pytest
from queue_helpers import GOOD_FIELDS, REASON, approve, new_item, raw_decision, raw_insert, reject, sha

from intake import codes, csvsink, decisions, exporter, rules, settings, sink_guard, workqueue
from intake.content_code import content_code, record
from intake.content_code import item_row_id as _item_row_id
from intake.sink_guard import COLUMNS


def item_row_id(item):
    return _item_row_id(item, rules.load_policy())


@pytest.fixture
def s(intake_settings):
    return intake_settings


def csv_rows(s):
    p = exporter.csv_path(s)
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.reader(f))


def receipts(s):
    with workqueue.opened(s) as c:
        return [dict(r) for r in c.execute("SELECT * FROM exports ORDER BY rowid")]


def item_state(s, item):
    return workqueue.get(s, item.id).state


def fields(**kw):
    f = copy.deepcopy(GOOD_FIELDS)
    f.update(kw)
    return f


def approved(s, name="inv", f=GOOD_FIELDS, flags=(), reason=None, approver="ap-a"):
    it = new_item(s, name, f, flags)
    approve(s, it, reason, approver)
    return workqueue.get(s, it.id)


def forging(s):
    """A connection with every trigger dropped: someone who can edit the database file (the exporter must still refuse)."""
    conn = workqueue.connect(s)
    for r in conn.execute("SELECT name FROM sqlite_master WHERE type='trigger'").fetchall():
        conn.execute(f'DROP TRIGGER "{r["name"]}"')
    return conn


def forge_approved(s, name, f=GOOD_FIELDS, flags="[]", code=None, decision="approve", fields_json=True):
    conn = forging(s)
    try:
        uid = raw_insert(conn, name, "APPROVED", f if fields_json else None, flags)
        it = workqueue.get_in(conn, name)
        raw_decision(conn, uid, decision, code or content_code(it))
        return it
    finally:
        conn.close()


# ---- the happy path and the shape of one row ----------------------------------------------------------------------------------------------------
def test_export_writes_one_row_with_14_columns_and_sets_exported(s):
    it = approved(s)
    res = exporter.export_row(s, it.id)
    assert res.code == "exported" and res.ok and res.row_id == item_row_id(it)
    got = workqueue.get(s, it.id)
    assert got.state == "EXPORTED" and got.version == it.version + 1
    rows = csv_rows(s)
    assert rows[0] == list(COLUMNS) and len(rows) == 2
    r = dict(zip(COLUMNS, rows[1], strict=True))
    assert r["tenant_id"] == s.tenant_id and r["invoice_no"] == "INV-1001" and r["supplier_name"] == "Acme Ltd"
    assert r["po_ref"] == "" and r["currency"] == "USD" and r["total_minor"] == "3300" and r["line_count"] == "2"
    assert r["flags"] == "" and r["source_sha256"] == it.source_sha256 and r["content_code"] == content_code(it)
    assert r["approved_by"] == "ap-a" and r["row_id"] == res.row_id
    assert len(r["approved_at"]) == 20 and r["approved_at"].endswith("Z") and r["approved_at"][10] == "T"
    (rec,) = receipts(s)
    assert json.loads(rec["row_json"]) == r and rec["content_code"] == content_code(it) and rec["item_uid"] == it.uid


def test_d06_item_with_a_reason_exports_with_its_flag_column(s):
    it = approved(s, "d06", flags=("D06",), reason=REASON)
    assert exporter.export_row(s, it.id).code == "exported"
    assert dict(zip(COLUMNS, csv_rows(s)[1], strict=True))["flags"] == "D06"


def test_receipt_is_inserted_before_the_state_moves(s, monkeypatch):
    it = approved(s)
    seen: list[str] = []
    real = workqueue.connect

    def traced(st):
        c = real(st)
        c.set_trace_callback(lambda q: seen.append(q))
        return c

    monkeypatch.setattr(workqueue, "connect", traced)
    assert exporter.export_row(s, it.id).code == "exported"
    ins = next(i for i, q in enumerate(seen) if q.startswith("INSERT INTO exports"))
    upd = next(i for i, q in enumerate(seen) if "SET state='EXPORTED'" in q)
    assert ins < upd and any(q == "BEGIN IMMEDIATE" for q in seen[:ins])


def test_database_refuses_the_reverse_order_and_a_receipt_without_an_approval(s):
    it = approved(s)
    with workqueue.opened(s) as c:
        with pytest.raises(Exception, match="exported needs an export row"):
            c.execute("UPDATE items SET state='EXPORTED' WHERE uid=?", (it.uid,))  # state first: trigger h
        with pytest.raises(Exception, match="export needs the latest approve"):
            c.execute(
                "INSERT INTO exports (row_id, item_uid, content_code, row_json, at) VALUES ('r', ?, ?, '{}', 'x')", (it.uid, "0" * 64)
            )


# ---- refusals (each: no receipt, no CSV row, state unchanged) ------------------------------------------------------------------------------------
def assert_nothing_written(s, item=None, state=None):
    assert receipts(s) == []
    p = exporter.csv_path(s)
    assert not p.exists() or len(csv_rows(s)) == 1
    if item is not None:
        assert item_state(s, item) == state


def test_refuses_no_approval(s):
    it = new_item(s, "ready")
    assert exporter.export_row(s, it.id).code == "not_approved"
    assert_nothing_written(s, it, "READY")


def test_refuses_rejected(s):
    it = new_item(s, "rej")
    reject(s, it)
    assert exporter.export_row(s, it.id).code == "not_approved"
    assert_nothing_written(s, it, "REJECTED")


def test_refuses_needs_person_and_received_and_flag_only_items(s):
    flagged = new_item(s, "flag", flags=("D06",))
    rec = workqueue.insert_received(s, "r.txt", sha("r"), "t", s.tenant_id, "r")
    x18 = workqueue.insert_flagged(s, "x.txt", sha("x"), "", s.tenant_id, "x", "X18")
    for i in (flagged, rec, x18):
        assert exporter.export_row(s, i.id).code == "not_approved"
    assert_nothing_written(s)


def test_refuses_after_field_change(s):
    it = approved(s)
    # with the triggers in place the change itself is refused (the first line) ...
    with workqueue.opened(s) as c:
        with pytest.raises(Exception, match="immutable"):
            c.execute("UPDATE items SET fields_json=? WHERE uid=?", (json.dumps(fields(total_minor=999999)), it.uid))
    # ... and with the triggers dropped the exporter recomputes the code and refuses (the second line)
    conn = forging(s)
    conn.execute("UPDATE items SET fields_json=? WHERE uid=?", (json.dumps(fields(total_minor=999999)), it.uid))
    conn.close()
    assert exporter.export_row(s, it.id).code == "approval_mismatch"
    assert_nothing_written(s, it, "APPROVED")


@pytest.mark.parametrize("what", ["flags", "tenant", "sha"])
def test_refuses_after_any_hashed_non_field_change(s, what):
    it = approved(s)
    col, val = {"flags": ("flags_json", '["D06"]'), "tenant": ("tenant_id", "other-tenant"), "sha": ("source_sha256", "f" * 64)}[what]
    conn = forging(s)
    conn.execute(f"UPDATE items SET {col}=? WHERE uid=?", (val, it.uid))
    conn.close()
    assert exporter.export_row(s, it.id).code in ("approval_mismatch", "not_approvable")
    assert_nothing_written(s)


def test_refuses_hand_inserted_approved_reject_only(s):
    # with the triggers in place the insert itself fails ...
    with workqueue.opened(s) as c:
        with pytest.raises(Exception, match="reject_only|decided state"):
            raw_insert(c, "forged", "APPROVED", GOOD_FIELDS, '["D10"]')
    # ... without them the exporter's own may_approve check refuses, for each reject-only code
    for i, code in enumerate(("D10", "X10", "X18", "X28", "L01", "L02")):
        it = forge_approved(s, f"forged{i}", flags=json.dumps([code]))
        assert exporter.export_row(s, it.id).code == "not_approvable", code
    assert_nothing_written(s)


def test_refuses_unknown_flag_and_invalid_record(s):
    it = forge_approved(s, "unk", flags='["ZZ9"]', code="a" * 64)  # content_code itself raises on an unknown flag
    assert exporter.export_row(s, it.id).code == "not_approvable"
    bad = forge_approved(s, "badrec", f={"invoice_no": "INV-9"}, code="b" * 64)  # fails the 6.2 validators
    assert exporter.export_row(s, bad.id).code == "not_approvable"
    neg = forge_approved(s, "neg", f=fields(total_minor=-5))
    assert exporter.export_row(s, neg.id).code == "not_approvable"
    assert_nothing_written(s)


def test_refuses_null_fields(s):
    approved_null = forge_approved(s, "nullf", fields_json=False)  # a hand-inserted APPROVED item with no fields
    assert exporter.export_row(s, approved_null.id).code == "not_approvable"
    x18 = workqueue.insert_flagged(s, "x.txt", sha("x"), "", s.tenant_id, "x", "X18")
    assert exporter.export_row(s, x18.id).code == "not_approved"  # no fields, no row id: straight to not_approved
    assert item_row_id(x18) is None
    assert_nothing_written(s)


def test_d06_without_a_valid_reason_in_the_decision_is_refused(s):
    it = forge_approved(s, "d06noreason", flags='["D06"]')  # decision row has no reason
    assert exporter.export_row(s, it.id).code == "not_approvable"
    assert_nothing_written(s)


def test_refuses_when_the_latest_decision_is_not_this_approval(s):
    it = approved(s)
    conn = forging(s)
    raw_decision(conn, it.uid, "reject", content_code(it))  # a later reject row
    conn.close()
    assert exporter.export_row(s, it.id).code == "approval_mismatch"
    it2 = approved(s, "inv2", fields(invoice_no="INV-2"))
    conn = forging(s)
    raw_decision(conn, it2.uid, "approve", "0" * 64)  # a later approve with another code
    conn.close()
    assert exporter.export_row(s, it2.id).code == "approval_mismatch"
    it3 = forge_approved(s, "nodec")
    conn = forging(s)
    conn.execute("DELETE FROM decisions WHERE item_uid=?", (it3.uid,))  # approved with no decision at all
    conn.close()
    assert exporter.export_row(s, it3.id).code == "approval_mismatch"
    assert_nothing_written(s)


def test_a_forged_decision_code_is_never_trusted(s):
    it = forge_approved(s, "forgedcode", code="a" * 64)  # decision carries a code that is not the item's
    assert exporter.export_row(s, it.id).code == "approval_mismatch"
    assert_nothing_written(s)


def test_row_id_conflict(s):
    first = approved(s, "first")
    assert exporter.export_row(s, first.id).code == "exported"
    second = approved(
        s, "second", fields(total_minor=4000, adjustments=[{"label": "VAT", "amount_minor": 1000}])
    )  # same supplier and invoice no
    assert item_row_id(second) == item_row_id(first) and content_code(second) != content_code(first)
    res = exporter.export_row(s, second.id)
    assert res.code == "row_id_conflict" and res.row_id == item_row_id(first)
    assert item_state(s, second) == "APPROVED" and len(receipts(s)) == 1 and len(csv_rows(s)) == 2


def test_row_id_conflict_on_a_revised_invoice_number_and_case(s):
    first = approved(s, "a1", fields(invoice_no="INV-1001", supplier_name="Acme Ltd"))
    exporter.export_row(s, first.id)
    other = approved(s, "a2", fields(invoice_no="inv-1001", supplier_name="  ACME   LTD ", total_minor=5))
    assert exporter.export_row(s, other.id).code == "row_id_conflict"


def test_already_exported_is_a_success_without_a_second_row(s):
    it = approved(s)
    assert exporter.export_row(s, it.id).code == "exported"
    again = exporter.export_row(s, it.id)
    assert again.code == "already_exported" and again.ok and len(receipts(s)) == 1 and len(csv_rows(s)) == 2


def test_exported_item_with_a_forged_receipt_code_is_not_a_success(s):
    it = approved(s)
    exporter.export_row(s, it.id)
    conn = forging(s)
    conn.execute("UPDATE exports SET content_code=? WHERE item_uid=?", ("0" * 64, it.uid))
    conn.close()
    assert exporter.export_row(s, it.id).code == "row_id_conflict"  # spec 9: another content code under this row id


def test_not_found(s):
    assert exporter.export_row(s, "nope-00000000").code == "not_found"


# ---- kill switch (errata 30) ---------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("how", ["true", "raises", "missing"])
def test_kill_switch_wins_for_any_item_and_an_unreadable_policy_counts_as_engaged(s, monkeypatch, how):
    it = approved(s)

    def read():
        if how == "raises":
            raise OSError("policy unreadable")
        return how == "true"

    if how == "missing":
        monkeypatch.setattr(settings, "_raw_policy", lambda: {})
    else:
        monkeypatch.setattr(settings, "read_kill_switch", read)
    assert exporter.export_row(s, it.id).code == "kill_switch"
    assert exporter.export_row(s, "nope").code == "kill_switch"  # first, for any item, even an unknown one
    run = exporter.export_pending(s)
    assert run.file == "kill_switch" and run.results[0].code == "kill_switch"
    assert_nothing_written(s, it, "APPROVED")


def test_kill_switch_engaged_after_the_receipt_leaves_the_file_stale_but_the_item_exported(s, monkeypatch):
    it = approved(s)
    calls = iter([False, True, True, True])
    monkeypatch.setattr(settings, "read_kill_switch", lambda: next(calls))
    res = exporter.export_row(s, it.id)
    assert res.code == "exported" and res.exported and res.file == "kill_switch" and not res.ok
    assert item_state(s, it) == "EXPORTED" and len(receipts(s)) == 1
    assert not exporter.csv_path(s).exists()
    monkeypatch.setattr(settings, "read_kill_switch", lambda: False)
    assert exporter.export_pending(s).file == "written" and len(csv_rows(s)) == 2


# ---- the batch (POST /export) -------------------------------------------------------------------------------------------------------------------
def test_pending_exports_only_approved_in_creation_order(s):
    a = approved(s, "a", fields(invoice_no="INV-A"))
    new_item(s, "ready", fields(invoice_no="INV-R"))
    rej = new_item(s, "rej", fields(invoice_no="INV-X"))
    reject(s, rej)
    c = approved(s, "c", fields(invoice_no="INV-C"))
    b = approved(s, "b", fields(invoice_no="INV-B"))
    assert exporter.preview(s) == [a.id, c.id, b.id]
    run = exporter.export_pending(s)
    assert [r.code for r in run.results] == ["exported"] * 3 and run.file == "written" and run.skipped == ()
    rows = csv_rows(s)
    assert [r[2] for r in rows[1:]] == ["INV-A", "INV-C", "INV-B"]
    assert {item_state(s, x) for x in (a, b, c)} == {"EXPORTED"} and item_state(s, rej) == "REJECTED"
    assert exporter.preview(s) == []


def test_item_level_refusal_is_listed_and_the_loop_goes_on(s):
    good1 = approved(s, "g1", fields(invoice_no="INV-1"))
    forge_approved(s, "badfwd", flags='["D10"]')
    good2 = approved(s, "g2", fields(invoice_no="INV-2"))
    run = exporter.export_pending(s)
    # the forged row has an old created_at, so it is tried first; the refusal does not stop the two good ones behind it
    assert [r.code for r in run.results] == ["not_approvable", "exported", "exported"] and run.file == "written"
    assert good1.id and good2.id
    assert [r[2] for r in csv_rows(s)[1:]] == ["INV-1", "INV-2"]


def test_nothing_pending_still_regenerates_the_file(s):
    it = approved(s)
    exporter.export_row(s, it.id)
    exporter.csv_path(s).unlink()
    run = exporter.export_pending(s)
    assert run.results == () and run.file == "written" and len(csv_rows(s)) == 2
    exporter.csv_path(s).write_bytes(b"")  # a zero-byte file is simply regenerated
    exporter.export_pending(s)
    assert len(csv_rows(s)) == 2


def test_empty_queue_writes_a_header_only_file(s):
    run = exporter.export_pending(s)
    assert run.file == "written" and csv_rows(s) == [list(COLUMNS)]


# ---- crash and kill -------------------------------------------------------------------------------------------------------------------------------
def test_rerun_after_kill_does_not_duplicate(s, monkeypatch):
    it = approved(s)

    def crash(path, rows):
        raise KeyboardInterrupt("killed between the receipt and the file")

    monkeypatch.setattr(csvsink, "regenerate", crash)
    with pytest.raises(KeyboardInterrupt):
        exporter.export_row(s, it.id)
    assert item_state(s, it) == "EXPORTED" and len(receipts(s)) == 1 and not exporter.csv_path(s).exists()
    monkeypatch.undo()
    run = exporter.export_pending(s)  # the retry repairs the file; it adds no second receipt
    assert run.results == () and run.file == "written"
    rows = csv_rows(s)
    assert len(rows) == 2 and sum(1 for r in rows if r[0] == receipts(s)[0]["row_id"]) == 1
    assert exporter.export_row(s, it.id).code == "already_exported" and len(csv_rows(s)) == 2 and len(receipts(s)) == 1


def test_sink_locked_keeps_the_item_exported_and_the_next_export_repairs_the_file(s, monkeypatch):
    it = approved(s)

    def deny(a, b):
        raise OSError(errno.EBUSY, "open in another program")

    monkeypatch.setattr(csvsink.os, "replace", deny)
    res = exporter.export_row(s, it.id)
    assert res.code == "exported" and res.exported and res.file == "sink_locked" and not res.ok and res.row_id == item_row_id(it)
    assert item_state(s, it) == "EXPORTED"
    assert not exporter.csv_path(s).exists() and not list(exporter.csv_path(s).parent.glob("*.tmp"))
    monkeypatch.undo()
    assert exporter.export_pending(s).file == "written" and len(csv_rows(s)) == 2


def test_kill_during_regeneration_leaves_the_old_file_whole(s, tmp_path):
    it1 = approved(s, "k1", fields(invoice_no="INV-K1"))
    exporter.export_row(s, it1.id)
    before = exporter.csv_path(s).read_bytes()
    it2 = approved(s, "k2", fields(invoice_no="INV-K2"))
    script = textwrap.dedent(
        """
        import os, sys
        from pathlib import Path
        sys.path.insert(0, sys.argv[1])
        from intake import csvsink, exporter, settings
        s = settings.load({"HADAVIN_LOCAL": sys.argv[2], "INTAKE_MODEL_BACKEND": "fake"})
        csvsink.os.replace = lambda a, b: os._exit(9)  # the process dies right before the swap
        exporter.export_row(s, sys.argv[3])
        """
    )
    src = str(Path(__file__).resolve().parents[1] / "src")
    r = subprocess.run([sys.executable, "-I", "-c", script, src, str(s.local), it2.id], capture_output=True, timeout=120)  # noqa: S603
    assert r.returncode == 9
    assert exporter.csv_path(s).read_bytes() == before  # old file whole (a leftover .tmp is harmless)
    assert item_state(s, it2) == "EXPORTED" and len(receipts(s)) == 2
    run = exporter.export_pending(s)
    assert run.file == "written" and [r[2] for r in csv_rows(s)[1:]] == ["INV-K1", "INV-K2"]


def test_a_stale_tmp_file_from_a_kill_is_overwritten(s):
    it = approved(s)
    (exporter.csv_path(s).parent).mkdir(parents=True, exist_ok=True)
    (exporter.csv_path(s).parent / "invoices.csv.abc123.tmp").write_bytes(b"=garbage\x00\xff")
    exporter.export_row(s, it.id)
    assert len(csv_rows(s)) == 2 and not list(exporter.csv_path(s).parent.glob("*.tmp"))


# ---- the CSV is regenerated from the receipts, never trusted --------------------------------------------------------------------------------------
def test_a_hand_edited_csv_is_overwritten_by_the_next_export(s):
    it = approved(s)
    exporter.export_row(s, it.id)
    good = exporter.csv_path(s).read_bytes()
    exporter.csv_path(s).write_bytes(good + b'"x","y","=cmd|calc","z"\n')  # an extra, unapproved row added by hand
    run = exporter.export_pending(s)
    assert run.file == "written" and exporter.csv_path(s).read_bytes() == good
    exporter.csv_path(s).write_bytes(b"garbage")
    exporter.export_pending(s)
    assert exporter.csv_path(s).read_bytes() == good


def test_a_tampered_receipt_is_skipped_and_never_reaches_the_file(s):
    a = approved(s, "ta", fields(invoice_no="INV-TA"))
    b = approved(s, "tb", fields(invoice_no="INV-TB"))
    exporter.export_pending(s)
    conn = forging(s)
    row = json.loads(conn.execute("SELECT row_json FROM exports WHERE item_uid=?", (a.uid,)).fetchone()["row_json"])
    row["supplier_name"] = "=cmd|' /C calc'!A0"
    conn.execute("UPDATE exports SET row_json=? WHERE item_uid=?", (json.dumps(row), a.uid))
    conn.close()
    run = exporter.export_pending(s)
    rows = csv_rows(s)
    assert run.skipped == (item_row_id(a),) and [r[2] for r in rows[1:]] == ["INV-TB"]
    assert all("calc" not in c for r in rows for c in r)
    assert item_row_id(b) in [r[0] for r in rows]


def test_a_receipt_for_an_item_that_was_never_approved_never_reaches_the_file(s):
    ready = new_item(s, "never", fields(invoice_no="INV-NEVER"))
    rej = new_item(s, "rejected", fields(invoice_no="INV-REJ"))
    reject(s, rej)
    conn = forging(s)
    for it in (ready, rej):
        rid = item_row_id(it)
        conn.execute(
            "INSERT INTO exports (row_id, item_uid, content_code, row_json, at) VALUES (?, ?, ?, ?, 'x')",
            (rid, it.uid, content_code(it), json.dumps(dict.fromkeys(COLUMNS, "x"))),
        )
    conn.close()
    run = exporter.export_pending(s)
    assert len(run.skipped) == 2 and csv_rows(s) == [list(COLUMNS)]  # I2: nothing but approved, exported items


def test_a_receipt_for_a_later_field_change_or_an_unapproved_state_is_skipped(s):
    it = approved(s)
    exporter.export_row(s, it.id)
    conn = forging(s)
    conn.execute("UPDATE items SET fields_json=? WHERE uid=?", (json.dumps(fields(total_minor=777)), it.uid))
    conn.close()
    run = exporter.export_pending(s)
    assert run.skipped == (item_row_id(it),) and csv_rows(s) == [list(COLUMNS)]
    conn = forging(s)
    conn.execute("UPDATE items SET fields_json=?, state='REJECTED' WHERE uid=?", (json.dumps(GOOD_FIELDS), it.uid))
    conn.close()
    assert exporter.export_pending(s).skipped == (item_row_id(it),) and csv_rows(s) == [list(COLUMNS)]


# ---- the cell guard inside the real flow ---------------------------------------------------------------------------------------------------------
def test_hostile_values_and_a_hostile_approver_are_guarded_in_the_file_but_not_in_the_code(s):
    f = fields(supplier_name="=1+1", invoice_no="@SUM(A1)", po_ref="-Acme", invoice_date="+1")
    it = approved(s, "hostile", f)
    conn = forging(s)  # the login rule refuses such a name; a forged decision row is the only way in, and the guard must still hold
    conn.execute("UPDATE decisions SET approver=? WHERE item_uid=?", ("=cmd|' /C calc'!A0", it.uid))
    conn.close()
    code_before = content_code(it)
    assert exporter.export_row(s, it.id).code == "exported"
    r = dict(zip(COLUMNS, csv_rows(s)[1], strict=True))
    assert r["supplier_name"] == "'=1+1" and r["invoice_no"] == "'@SUM(A1)" and r["po_ref"] == "'-Acme" and r["invoice_date"] == "'+1"
    assert r["approved_by"] == "'=cmd|' /C calc'!A0"
    assert content_code(workqueue.get(s, it.id)) == code_before  # the guard changes only the written text


def test_unicode_newlines_and_a_huge_cell_round_trip(s):
    big = "Acme " + "x" * 58  # po_ref cap is 64 (validators)
    f = fields(supplier_name="M" + chr(0xFC) + "ller GmbH " + chr(0x4E2D) + chr(0x6587), invoice_no="INV-U", po_ref=big)
    it = approved(s, "uni", f)
    assert exporter.export_row(s, it.id).code == "exported"
    r = dict(zip(COLUMNS, csv_rows(s)[1], strict=True))
    assert r["supplier_name"] == f["supplier_name"] and r["po_ref"] == big
    nl = new_item(s, "nl", fields(invoice_no="INV-NL", supplier_name="Two" + chr(10) + "Line" + chr(9) + "Co"))
    with pytest.raises(codes.Refused) as e:  # a line break in a value is refused upstream (validators); the sink would also replace it
        approve(s, nl)
    assert e.value.code == "not_approvable"


def test_nul_in_a_value_cannot_even_be_read_back_and_is_never_exported(s):
    conn = forging(s)
    uid = raw_insert(conn, "nul", "APPROVED", fields(invoice_no="INV-NUL", supplier_name="A" + chr(0) + "B"), "[]")
    raw_decision(conn, uid, "approve", "a" * 64)
    conn.close()
    assert exporter.export_row(s, "nul").code == "stored_data_bad"  # the queue refuses to read it
    assert_nothing_written(s)


# ---- concurrency ------------------------------------------------------------------------------------------------------------------------------------
def test_eight_threads_exporting_one_item_write_one_receipt_and_one_row(s):
    it = approved(s)
    out: list[str] = []
    gate = threading.Barrier(8)

    def go():
        gate.wait()
        out.append(exporter.export_row(s, it.id).code)

    ts = [threading.Thread(target=go) for _ in range(8)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert out.count("exported") == 1 and set(out) <= {"exported", "already_exported"}
    assert len(receipts(s)) == 1 and len(csv_rows(s)) == 2


def test_two_processes_exporting_the_same_item_write_one_receipt(s):
    it = approved(s)
    script = textwrap.dedent(
        """
        import sys
        sys.path.insert(0, sys.argv[1])
        from intake import exporter, settings
        s = settings.load({"HADAVIN_LOCAL": sys.argv[2], "INTAKE_MODEL_BACKEND": "fake"})
        print(exporter.export_row(s, sys.argv[3]).code)
        """
    )
    src = str(Path(__file__).resolve().parents[1] / "src")
    procs = [subprocess.Popen([sys.executable, "-I", "-c", script, src, str(s.local), it.id], stdout=subprocess.PIPE) for _ in range(3)]  # noqa: S603
    outs = [p.communicate(timeout=120)[0].decode().strip() for p in procs]
    assert all(p.returncode == 0 for p in procs) and outs.count("exported") == 1, outs
    assert set(outs) == {"exported", "already_exported"} and len(receipts(s)) == 1 and len(csv_rows(s)) == 2


# ---- columns, codes ---------------------------------------------------------------------------------------------------------------------------------
def test_every_exported_column_is_hashed_or_listed_exempt(s):
    assert tuple(exporter.EXEMPT_FROM_HASH) == ("row_id", "line_count", "content_code", "approved_by", "approved_at")
    it = new_item(s, "cols", fields(po_ref="PO-1"), flags=("D06",))
    base = content_code(it)
    mutate = {
        "tenant_id": lambda i: {"tenant_id": "other"},
        "invoice_no": lambda i: {"fields": fields(po_ref="PO-1", invoice_no="INV-X")},
        "supplier_name": lambda i: {"fields": fields(po_ref="PO-1", supplier_name="Other Ltd")},
        "po_ref": lambda i: {"fields": fields(po_ref="PO-2")},
        "currency": lambda i: {"fields": fields(po_ref="PO-1", currency="GBP")},
        "invoice_date": lambda i: {"fields": fields(po_ref="PO-1", invoice_date="2026-10-02")},
        "total_minor": lambda i: {"fields": fields(po_ref="PO-1", total_minor=1)},
        "flags": lambda i: {"flags": ("D06", "L01")},
        "source_sha256": lambda i: {"source_sha256": "e" * 64},
    }
    import dataclasses

    hashed = [c for c in COLUMNS if c not in exporter.EXEMPT_FROM_HASH]
    assert sorted(hashed) == sorted(mutate)
    for col in hashed:
        changed = dataclasses.replace(it, **mutate[col](it))
        assert content_code(changed) != base, col
    # the exempt columns are not in the hashed record (line_count is derived from the hashed lines)
    assert set(record(it)) >= {
        "tenant_id",
        "source_sha256",
        "invoice_no",
        "supplier_name",
        "po_ref",
        "currency",
        "invoice_date",
        "total_minor",
        "flags",
    }
    assert not (set(exporter.EXEMPT_FROM_HASH) & set(record(it)))


def test_columns_match_the_spec_and_the_result_codes_are_listed():
    assert (
        list(COLUMNS)
        == (
            "row_id tenant_id invoice_no supplier_name po_ref currency invoice_date total_minor line_count flags source_sha256 content_code "
            "approved_by approved_at"
        ).split()
    )
    for code in (
        "exported",
        "already_exported",
        "not_found",
        "kill_switch",
        "not_approved",
        "not_approvable",
        "approval_mismatch",
        "row_id_conflict",
        "sink_locked",
    ):
        assert code in codes.CODES
    assert sink_guard.COLUMNS == COLUMNS
    assert decisions  # imported for the decision rows of the tests above


# ---- the exporter's OWN checks, with the database triggers switched off (the triggers are the second line, not the first) ------------------
@pytest.fixture
def no_triggers(monkeypatch):
    real = workqueue._ensure_schema

    def no_triggers_schema(conn):
        real(conn)  # the real schema check, then every trigger is dropped on this connection
        for r in conn.execute("SELECT name FROM sqlite_master WHERE type='trigger'").fetchall():
            conn.execute(f'DROP TRIGGER "{r["name"]}"')

    monkeypatch.setattr(workqueue, "_ensure_schema", no_triggers_schema)


def test_exporter_checks_hold_without_any_trigger(s, no_triggers):
    # latest decision is a reject carrying the SAME code
    it = approved(s)
    conn = workqueue.connect(s)
    raw_decision(conn, it.uid, "reject", content_code(it))
    conn.close()
    assert exporter.export_row(s, it.id).code == "approval_mismatch"
    # latest decision is an approve with ANOTHER code
    it2 = approved(s, "inv2", fields(invoice_no="INV-2"))
    conn = workqueue.connect(s)
    raw_decision(conn, it2.uid, "approve", "0" * 64)
    conn.close()
    assert exporter.export_row(s, it2.id).code == "approval_mismatch"
    # the item fields changed after the approval (nothing refuses the UPDATE here)
    it3 = approved(s, "inv3", fields(invoice_no="INV-3"))
    conn = workqueue.connect(s)
    conn.execute("UPDATE items SET fields_json=? WHERE uid=?", (json.dumps(fields(invoice_no="INV-3", total_minor=1)), it3.uid))
    conn.close()
    assert exporter.export_row(s, it3.id).code == "approval_mismatch"
    # hand-inserted APPROVED items: reject-only flag, no fields
    for i, (flags, fj) in enumerate((('["D10"]', True), ("[]", False))):
        conn = workqueue.connect(s)
        uid = raw_insert(conn, f"h{i}", "APPROVED", GOOD_FIELDS if fj else None, flags)
        h = workqueue.get_in(conn, f"h{i}")
        raw_decision(conn, uid, "approve", content_code(h))
        conn.close()
        assert exporter.export_row(s, h.id).code == "not_approvable"
    assert receipts(s) == []  # not one receipt: I2 held with no database help
    assert not exporter.csv_path(s).exists() or len(csv_rows(s)) == 1


def test_row_id_conflict_without_a_unique_constraint_help(s, no_triggers):
    first = approved(s, "first")
    exporter.export_row(s, first.id)
    second = approved(s, "second", fields(total_minor=4000, adjustments=[{"label": "VAT", "amount_minor": 1000}]))
    assert exporter.export_row(s, second.id).code == "row_id_conflict"
    assert len(receipts(s)) == 1


def test_an_integrity_error_from_a_trigger_is_a_refusal_and_writes_nothing(s, monkeypatch):
    it = approved(s)
    conn = forging(s)
    raw_decision(conn, it.uid, "reject", content_code(it))  # latest decision is a reject
    conn.close()
    real = exporter._eligible

    def lying(st, c, item):  # the exporter's own check is bypassed: trigger e must refuse the receipt
        got = real(st, c, item)
        if isinstance(got, exporter.ExportResult):
            return (
                workqueue.Decision(1, item.uid, "approve", "ap-a", None, content_code(item), "2026-11-03T00:00:00Z"),
                item_row_id(item),
                content_code(item),
            )
        return got

    monkeypatch.setattr(exporter, "_eligible", lying)
    res = exporter.export_row(s, it.id)
    assert res.code == "state_conflict"
    assert receipts(s) == [] and item_state(s, it) == "APPROVED"


def test_a_nul_in_a_forged_approver_name_is_refused_at_export_not_written(s):
    it = approved(s, "nulappr")
    conn = forging(s)
    conn.execute("UPDATE decisions SET approver=? WHERE item_uid=?", ("ap-a" + chr(0) + "x", it.uid))
    conn.close()
    assert exporter.export_row(s, it.id).code == "not_approvable"
    assert_nothing_written(s, it, "APPROVED")


def test_exports_are_serialised_inside_the_process(s, monkeypatch):
    items = [approved(s, f"p{i}", fields(invoice_no=f"INV-P{i}")) for i in range(4)]
    state = {"now": 0, "max": 0}
    real = csvsink.regenerate

    def slow(path, rows):
        state["now"] += 1
        state["max"] = max(state["max"], state["now"])
        import time

        time.sleep(0.15)
        try:
            return real(path, rows)
        finally:
            state["now"] -= 1

    monkeypatch.setattr(csvsink, "regenerate", slow)
    ts = [threading.Thread(target=exporter.export_row, args=(s, i.id)) for i in items]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert state["max"] == 1 and len(receipts(s)) == 4 and len(csv_rows(s)) == 5


# ---- a tampered decisions or receipts row never reaches the file ---------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "how", ["later_approve_other_code", "later_reject_same_code", "receipt_code_only", "state_reverted", "receipt_row_id"]
)
def test_regeneration_skips_a_receipt_whose_decision_or_code_was_tampered(s, how):
    keep = approved(s, "keep", fields(invoice_no="INV-KEEP"))
    it = approved(s, "tamper", fields(invoice_no="INV-T"))
    exporter.export_pending(s)
    assert len(csv_rows(s)) == 3
    conn = forging(s)
    if how == "later_approve_other_code":
        raw_decision(conn, it.uid, "approve", "9" * 64)
    elif how == "later_reject_same_code":
        raw_decision(conn, it.uid, "reject", content_code(it))
    elif how == "receipt_code_only":
        conn.execute("UPDATE exports SET content_code=? WHERE item_uid=?", ("9" * 64, it.uid))
    elif how == "state_reverted":
        conn.execute("UPDATE items SET state='APPROVED' WHERE uid=?", (it.uid,))
    elif how == "receipt_row_id":
        conn.execute("UPDATE exports SET row_id=? WHERE item_uid=?", ("8" * 64, it.uid))
    conn.close()
    run = exporter.export_pending(s)
    assert len(run.skipped) == 1, how
    assert [r[2] for r in csv_rows(s)[1:]] == ["INV-KEEP"] and keep.id


def test_integrity_only_a_fully_consistent_rewrite_is_not_judged_by_todays_rules(s):
    # errata 36c: item, decision, receipt and row all agree, so integrity holds; today's reject-only rule is NOT applied to a historic receipt
    # (a database editor can do this; the receipts are the record. New exports are still judged by today's rules: see the refusal tests)
    it = approved(s)
    exporter.export_row(s, it.id)
    conn = forging(s)
    conn.execute("UPDATE items SET flags_json='[\"D10\"]' WHERE uid=?", (it.uid,))
    forged = workqueue.get_in(conn, it.id)
    code = content_code(forged)
    dec = workqueue.Decision(0, it.uid, "approve", "ap-a", None, code, "2026-11-03T00:00:00Z")
    row = sink_guard.guard_row(exporter.build_row(forged, dec, item_row_id(forged), code))
    raw_decision(conn, it.uid, "approve", code)
    conn.execute("UPDATE exports SET content_code=?, row_json=? WHERE item_uid=?", (code, json.dumps(row), it.uid))
    got = conn.execute(
        "SELECT decision, content_code, at, approver FROM decisions WHERE item_uid=? ORDER BY seq DESC LIMIT 1", (it.uid,)
    ).fetchone()
    conn.execute("UPDATE exports SET row_json=? WHERE item_uid=?", (json.dumps(dict(row, approved_at=got["at"])), it.uid))
    conn.close()
    run = exporter.export_pending(s)
    assert run.skipped == () and len(csv_rows(s)) == 2


def test_kill_switch_stops_the_batch_at_once(s, monkeypatch):
    for i in range(3):
        approved(s, f"k{i}", fields(invoice_no=f"INV-K{i}"))
    calls = iter([False, False, True, True, True, True, True])  # pending check, item 1 ok, item 2 refused: the loop must stop there
    monkeypatch.setattr(settings, "read_kill_switch", lambda: next(calls))
    run = exporter.export_pending(s)
    assert [r.code for r in run.results] == ["exported", "kill_switch"] and run.file == "kill_switch"
    monkeypatch.setattr(settings, "read_kill_switch", lambda: False)
    assert len(exporter.export_pending(s).results) == 2  # the two left over are exported later
    assert len(csv_rows(s)) == 4


def test_kill_switch_engaged_before_the_batch_tries_nothing(s, monkeypatch):
    approved(s, "a", fields(invoice_no="INV-A"))
    approved(s, "b", fields(invoice_no="INV-B"))
    monkeypatch.setattr(settings, "read_kill_switch", lambda: True)
    run = exporter.export_pending(s)
    assert len(run.results) == 1 and run.results[0].code == "kill_switch" and run.file == "kill_switch"


def test_flags_column_is_sorted_and_pipe_joined(s):
    import dataclasses

    it = approved(s)
    dec = workqueue.Decision(1, it.uid, "approve", "ap-a", None, "c" * 64, "2026-11-03T00:00:00Z")
    row = exporter.build_row(dataclasses.replace(it, flags=("L01", "D06")), dec, "r" * 64, "c" * 64)
    assert row["flags"] == "D06|L01"
    assert exporter.build_row(dataclasses.replace(it, flags=()), dec, "r" * 64, "c" * 64)["flags"] == ""
