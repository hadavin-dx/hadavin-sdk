"""The contract between the queue (P3) and the trace log (P7): ``extract.QueueSink`` stores the spans and the key, stores trace rows and answers False when the
queue refuses a row. Uses the real queue, the real ``TraceRow`` and the real mask kernel; the Tracer itself is P7's and is tested there."""

from __future__ import annotations

import pytest
from model_support import register
from queue_helpers import approve, new_item, sha
from test_extract import A_RAW, GOOD, Scripted, ok

from conftest import settings_for_tests
from intake import extract, mask, reader, workqueue
from intake.selfcheck_codes import SelfCheckFailed

KEY = bytes(range(32))
AT = "2026-11-04T00:00:00Z"


@pytest.fixture
def s(tmp_path):
    return settings_for_tests(tmp_path)


def received(s, text):
    p = reader.read("inv-A.txt", text.encode("utf-8"))
    it = workqueue.insert_received(s, "inv-A.txt", p.source_sha256, p.text, s.tenant_id, "inv-A")
    assert isinstance(it, workqueue.Item)
    return it, p


class TracerLike:
    """Just enough of a Tracer for ``extract_parsed``: hands the call to the sink with the document text, as the real one does."""

    def __init__(self, sink):
        self.sink = sink

    def mask_done(self, masked, key, document_text):
        assert document_text
        self.sink.mask_done(masked, key)


def test_mask_done_stores_spans_and_key_so_the_marks_restore(s):
    it, p = received(s, A_RAW.decode())
    sink = extract.QueueSink(s, it.uid, it.source_text)
    masked = mask.mask(it.source_text, KEY)
    sink.mask_done(masked, KEY)
    assert workqueue.item_key(s, it.id) == KEY
    rm = workqueue.restore_map(s, it.id)
    assert rm and all(it.source_text[sp.start : sp.end] == rm[sp.placeholder] for sp in masked.spans)


def test_mask_done_with_a_wrong_text_is_mask_failed(s):
    it, _ = received(s, A_RAW.decode())
    sink = extract.QueueSink(s, it.uid, it.source_text + "x")
    with pytest.raises(SelfCheckFailed) as e:
        sink.mask_done(mask.mask(it.source_text, KEY), KEY)
    assert e.value.code == "mask_failed"


def test_extract_with_the_real_sink_stores_then_calls_and_a_failing_sink_means_no_call(s):
    it, p = received(s, A_RAW.decode())
    m = Scripted(ok(GOOD))
    d = extract.extract_parsed(p, m, s, tracer=TracerLike(extract.QueueSink(s, it.uid, it.source_text)), key=KEY, streak=None)
    assert d.selfcheck is None and d.fields == GOOD and workqueue.item_key(s, it.id) == KEY
    it2, p2 = received(s, A_RAW.decode() + "Ref 77\n")
    register(s, p2.text)
    bad = extract.QueueSink(s, it2.uid, it2.source_text + "x")  # stores nothing: the hash differs
    m2 = Scripted(None)
    d2 = extract.extract_parsed(p2, m2, s, tracer=TracerLike(bad), key=KEY, streak=None)
    assert d2.selfcheck == "mask_failed" and m2.calls == [] and d2.cost_micro == 0


def test_row_stores_a_trace_row_and_maps_the_result_words(s):
    it, _ = received(s, "x")
    sink = extract.QueueSink(s, it.uid, "x")
    assert sink.row("mask", AT, {"digit8": 1}, (("<BANK_1>", "ab12cd34"),), "pass", "") is True
    assert sink.row("restore", AT, {}, (), "MISMATCH", "") is True
    assert sink.row("restore", AT, {}, (), "same", "") is True
    assert sink.row("data_gate", AT, {}, (), "refused", "") is True
    stored = [r.result for r in workqueue.trace_rows(s, it.id)]
    assert stored == ["pass", "fail", "pass", "fail"]


@pytest.mark.parametrize("result", ["bogus", "", None])
def test_an_unknown_result_word_is_a_refused_row(s, result):
    it, _ = received(s, "x")
    assert extract.QueueSink(s, it.uid, "x").row("mask", AT, {}, (), result, "") is False
    assert workqueue.trace_rows(s, it.id) == []


def test_a_row_outside_the_closed_vocabulary_is_refused_not_raised(s):
    it, _ = received(s, "x")
    sink = extract.QueueSink(s, it.uid, "x")
    assert sink.row("not_a_step", AT, {}, (), "pass", "") is False
    assert sink.row("mask", AT, {"not_a_count": 1}, (), "pass", "") is False
    assert sink.row("mask", AT, {}, (), "pass", "free text that is not a phrase") is False
    assert workqueue.trace_rows(s, it.id) == []


def test_a_decided_item_takes_no_row_and_the_sink_says_false(s):
    it = new_item(s, "dec")
    sink = extract.QueueSink(s, it.uid, it.source_text)
    assert sink.row("mask", AT, {}, (), "pass", "") is True
    approve(s, it)
    assert sink.row("selfcheck_e", AT, {}, (), "pass", "") is False
    assert [r.step for r in workqueue.trace_rows(s, it.id) if r.step == "mask"] == ["mask"]


def test_an_unknown_item_is_a_refused_row(s):
    assert extract.QueueSink(s, 99999, "x").row("mask", AT, {}, (), "pass", "") is False
    assert sha("x")  # keeps the helper import honest


def test_fingerprint_names_follow_erratum_97_and_pass_through_unchanged(s):
    """The sink never renames: the Tracer names the pairs BODY_1 (request body), TEXT_1 (read text), FP_1 (check b); a name that is not mark-shaped is refused."""
    it, _ = received(s, "x")
    sink = extract.QueueSink(s, it.uid, "x")
    pairs = (("BODY_1", "0a1b2c3d"), ("TEXT_1", "4e5f6a7b"), ("FP_1", "8c9d0e1f"))
    assert sink.row("request", AT, {}, pairs, "info", "") is True
    assert sink.row("request", AT, {}, (("body", "0a1b2c3d"),), "info", "") is False
    (row,) = [r for r in workqueue.trace_rows(s, it.id) if r.step == "request"]
    assert tuple(row.fingerprints) == pairs
