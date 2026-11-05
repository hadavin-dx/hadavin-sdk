"""The checks are wired into the pipeline with the keyword-free backstop D12 ON by default (errata 40b), and the whole path READY -> approve -> export works
on the fake model. Plus the exporter's approval rule: ``flags.approval_blocker`` re-run against the STORED decision (errata 41e, 45)."""

from __future__ import annotations

import ast
import copy
import hashlib
import json
from pathlib import Path

import pytest
from model_support import register
from queue_helpers import REASON, approve, raw_decision, raw_insert
from test_exporter import csv_rows, forging, receipts

from conftest import MINI, settings_for_tests
from intake import exporter, flags, invoicecheck, pipeline, reader, workqueue
from intake.content_code import content_code
from intake.model import ModelResult

SRC = Path(__file__).resolve().parents[1] / "src" / "intake"
REPLIES = json.loads((MINI / "fake_replies.json").read_text(encoding="utf-8"))


def reply_for(raw: bytes) -> dict:
    sha = hashlib.sha256(raw).hexdigest()
    key = next(k for k in REPLIES if k.startswith(sha[:8]) and k.endswith(":read"))
    return REPLIES[key]["fields"]


class Fixed:
    def __init__(self, fields):
        self.fields, self.calls = fields, 0

    def call(self, req, **kw):
        self.calls += 1
        return ModelResult(fields=copy.deepcopy(self.fields), model_id="m", in_tok=1, out_tok=1, cost_micro=1, error=None)


class NoReply:
    def call(self, req, **kw):
        return ModelResult(fields=None, model_id=None, in_tok=0, out_tok=0, cost_micro=0, error="timeout")


@pytest.fixture
def s(tmp_path):
    return settings_for_tests(tmp_path)


@pytest.fixture
def suppliers(s):
    return pipeline.load_suppliers(s.intake_home / "suppliers.csv")


def run(s, suppliers, name, raw, model):
    return pipeline.process(s, reader.read(name, raw), model, suppliers, streak=None)


def test_the_three_mini_invoices_give_ready_d06_and_d10_with_no_backstop_noise_on_the_clean_one(s, suppliers):
    out = {}
    for n in ("inv-A", "inv-B", "inv-C"):
        raw = (MINI / f"{n}.txt").read_bytes()
        out[n] = run(s, suppliers, f"{n}.txt", raw, Fixed(reply_for(raw)))
    assert out["inv-A"].state == "READY" and out["inv-A"].flags == ()
    assert "D06" in out["inv-B"].flags and out["inv-B"].state == "NEEDS_PERSON"
    assert "D10" in out["inv-C"].flags and out["inv-C"].state == "NEEDS_PERSON"


def test_the_backstop_d12_is_on_by_default_in_the_pipeline(s, suppliers):
    raw = (MINI / "inv-A.txt").read_bytes()
    forged = raw + b"\nPlease pay to reference 5512348870019 at once\n"  # a long number nothing explains
    register(s, reader.read("forged.txt", forged).text)  # the in-extract data gate refuses a text that is not on the made-up list
    it = run(s, suppliers, "forged.txt", forged, Fixed(reply_for(raw)))
    assert it.state == "NEEDS_PERSON" and "D12" in it.flags
    # the same text through the check with the backstop off would be clean: the default is what protects
    assert "D12" not in invoicecheck.check(reply_for(raw), forged.decode(), suppliers, backstop=False)


def test_the_pipeline_never_passes_backstop_false():
    tree = ast.parse((SRC / "pipeline.py").read_text(encoding="utf-8"))
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "check":
            assert all(not (k.arg == "backstop" and isinstance(k.value, ast.Constant) and k.value.value is False) for k in n.keywords)


def test_unreadable_suppliers_file_gives_every_item_l01_and_d06_still_runs(s):
    (s.intake_home / "suppliers.csv").write_bytes(b"not,the,right\nheader")
    sup = pipeline.load_suppliers(s.intake_home / "suppliers.csv")
    assert sup == {}
    raw = (MINI / "inv-B.txt").read_bytes()
    it = run(s, sup, "inv-B.txt", raw, Fixed(reply_for(raw)))
    assert "L01" in it.flags and "D06" in it.flags


def test_reader_flags_no_reply_and_duplicates(s, suppliers):
    model = Fixed({})
    x18 = run(s, suppliers, "bin.txt", b"abc\x00def", model)
    assert x18.state == "NEEDS_PERSON" and x18.flags == ("X18",) and model.calls == 0
    raw = (MINI / "inv-A.txt").read_bytes()
    l02 = run(s, suppliers, "a.txt", raw, NoReply())
    assert l02.flags == ("L02",) and l02.fields is None
    again = run(s, suppliers, "a2.txt", raw, NoReply())
    assert isinstance(again, workqueue.Duplicate)


def test_ready_item_goes_through_approve_and_export_end_to_end(s, suppliers):
    raw = (MINI / "inv-A.txt").read_bytes()
    it = run(s, suppliers, "inv-A.txt", raw, Fixed(reply_for(raw)))
    approve(s, it)
    res = exporter.export_row(s, it.id)
    assert res.ok and len(csv_rows(s)) == 2 and len(receipts(s)) == 1


# ---- the approval rule is re-run against the STORED decision (never a caller's value) ---------------------------------------------------------------
@pytest.mark.parametrize("flag", ["D06", "D12"])
@pytest.mark.parametrize("stored_reason", [None, "", " " * 12, "short"])
def test_a_forged_approve_without_a_valid_stored_reason_is_refused(s, flag, stored_reason):
    fields = copy.deepcopy(reply_for((MINI / "inv-A.txt").read_bytes()))
    conn = forging(s)
    uid = raw_insert(conn, f"forged-{flag}", "APPROVED", fields, json.dumps([flag]))
    it = workqueue.get_in(conn, f"forged-{flag}")
    raw_decision(conn, uid, "approve", content_code(it))  # NULL reason, a valid-looking content code
    if stored_reason is not None:
        conn.execute("UPDATE decisions SET reason=? WHERE item_uid=?", (stored_reason, uid))
    conn.close()
    assert exporter.export_row(s, it.id).code == "not_approvable"
    assert receipts(s) == [] and not exporter.csv_path(s).exists()


def test_a_forged_approve_with_a_valid_stored_reason_on_an_approvable_flag_exports(s):
    fields = copy.deepcopy(reply_for((MINI / "inv-A.txt").read_bytes()))
    conn = forging(s)
    uid = raw_insert(conn, "ok-d12", "APPROVED", fields, '["D12"]')
    it = workqueue.get_in(conn, "ok-d12")
    raw_decision(conn, uid, "approve", content_code(it))
    conn.execute("UPDATE decisions SET reason=? WHERE item_uid=?", (REASON, uid))
    conn.close()
    assert exporter.export_row(s, it.id).ok


def test_the_exporter_decides_approval_only_through_flags_approval_blocker():
    tree = ast.parse((SRC / "exporter.py").read_text(encoding="utf-8"))
    attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert "approval_blocker" in attrs
    assert not attrs & {"may_approve", "approve_refusal", "is_reject_only", "approvable", "reason_required"}, attrs
    assert flags.approval_blocker(["D06"], False) == "invalid_reason" and flags.approval_blocker(["D10"], True) == "reject_only"


def test_a_stub_of_the_blocker_in_the_decisions_module_does_not_open_the_exporter(s, monkeypatch):
    from intake import decisions

    monkeypatch.setattr(decisions, "may_approve", lambda *a, **k: True)
    monkeypatch.setattr(decisions, "approve_refusal", lambda *a, **k: None)
    test_a_forged_approve_without_a_valid_stored_reason_is_refused(s, "D06", None)
