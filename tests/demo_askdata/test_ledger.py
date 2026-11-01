"""The ledger line schema (A-13), append-only writes, torn-tail handling, and the audit reconciliation."""

from __future__ import annotations

import hashlib
import json

import pytest
from askdata import audit as audit_mod
from askdata.audit import AskAudit, local_dir_sink
from askdata.ledger import Budget, LedgerLine, QueryLedger, dump, line_sha256, utc_stamp
from pydantic import ValidationError

H = "a" * 64


def make_line(qid: str = "1" * 32, **over) -> LedgerLine:
    base = {
        "query_id": qid, "ts": "2026-11-01T10:00:00Z", "asker": "claimed:rakesh", "question": "how many?",
        "question_sha256": H, "outcome": "answered", "prompt_sha256": H, "config_hash": H, "catalog_sha256": H,
        "model_id": "m", "route": "sql_generate", "budget": Budget(spent_usd="0.01", cap_usd="8.00"),
    }  # fmt: skip
    return LedgerLine(**(base | over))


def test_a_line_is_sorted_compact_ascii_and_hashed_over_its_exact_bytes():
    line = make_line(question="café ☃")
    raw = dump(line)
    bs = chr(92).encode()
    assert raw.isascii() and bs + b"u00e9" in raw and bs + b"u2603" in raw
    obj = json.loads(raw)
    assert list(obj) == sorted(obj) and obj["schema"] == "askdata.ledger/1"
    assert line_sha256(line) == hashlib.sha256(raw).hexdigest()
    assert json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode() == raw


def test_unknown_keys_bad_hex_and_bad_enums_are_refused():
    with pytest.raises(ValidationError):
        make_line(surprise=1)
    with pytest.raises(ValidationError):
        make_line(question_sha256="XYZ")
    with pytest.raises(ValidationError):
        make_line(outcome="maybe")
    with pytest.raises(ValidationError):
        make_line(ts="yesterday")
    with pytest.raises(ValidationError):
        make_line(qid="short")
    with pytest.raises(ValidationError):
        make_line(alarm=["bad"])


def test_text_fields_are_cleaned_at_write_time():
    esc = chr(27)
    line = make_line(question=f"a{esc}[2Kb{chr(0)}c", asker=f"claimed:{esc}x")
    assert chr(27) not in dump(line).decode() and "\\x00" in line.question


def test_append_returns_the_line_hash_and_reads_back(tmp_path):
    ledger = QueryLedger(tmp_path / "sub" / "ledger.jsonl")
    a, b = make_line("1" * 32), make_line("2" * 32, outcome="abstained", reason_code="ambiguous")
    sha_a, sha_b = ledger.append(a), ledger.append(b)
    res = ledger.read()
    assert [s.line.query_id for s in res.items] == ["1" * 32, "2" * 32] and res.bad == []
    assert [s.sha256 for s in res.items] == [sha_a, sha_b] == [line_sha256(a), line_sha256(b)]


def test_a_torn_tail_is_skipped_and_the_next_append_starts_a_new_line(tmp_path):
    ledger = QueryLedger(tmp_path / "l.jsonl")
    ledger.append(make_line("1" * 32))
    with open(ledger.path, "ab") as f:
        f.write(b'{"asker":"claimed:half')  # a crash mid-append: no newline
    assert [s.number for s in ledger.read().items] == [1] and ledger.read().bad == [2]
    ledger.append(make_line("3" * 32))
    res = ledger.read()
    assert [s.line.query_id for s in res.items] == ["1" * 32, "3" * 32] and res.bad == [2]


def test_garbage_and_non_ascii_lines_are_bad_not_fatal(tmp_path):
    p = tmp_path / "l.jsonl"
    p.write_bytes(b"not json\n" + dump(make_line()) + b"\n" + "é\n".encode() + b"\n")
    res = QueryLedger(p).read()
    assert len(res.items) == 1 and res.bad == [1, 3]


def test_a_missing_file_reads_empty(tmp_path):
    assert QueryLedger(tmp_path / "nope.jsonl").read().items == []


# ------------------------------------------------------------------------------------------------ audit


def _one(tmp_path, with_intent=True):
    ledger, sink = QueryLedger(tmp_path / "l.jsonl"), local_dir_sink(tmp_path / "audit")
    audit = AskAudit(sink, principal="claimed:t")
    qid = "9" * 32
    ids = [audit.intent(qid, question_sha256=H, sql_sha256=H)] if with_intent else []
    from askdata.ledger import Attempt

    line = make_line(
        qid,
        attempts=[
            Attempt(n=1, schema_ok=True, executed=True, intent_event_id=ids[0] if ids else None)
        ],
        intent_event_ids=ids,
    )
    sha = ledger.append(line)
    audit.outcome(qid, question_sha256=H, decision="answered", ledger_sha256=sha, sql_sha256=H)
    return ledger, sink, sha, qid


def test_verify_counts_match_and_never_says_chain(tmp_path):
    ledger, sink, *_ = _one(tmp_path)
    rep = audit_mod.verify(ledger, sink)
    assert rep.ok and (rep.events_ok, rep.events_total, rep.lines_ok, rep.lines_total) == (
        2,
        2,
        1,
        1,
    )
    text = rep.text()
    assert text.startswith("local integrity check: 2 of 2 events and 1 of 1 ledger lines match")
    assert "rewriting both" in text and "chain" not in text.lower() and "intact" not in text.lower()


def test_verify_finds_an_edited_ledger_line(tmp_path):
    ledger, sink, *_ = _one(tmp_path)
    ledger.path.write_bytes(ledger.path.read_bytes().replace(b"how many?", b"how much?"))
    rep = audit_mod.verify(ledger, sink)
    assert (
        not rep.ok
        and rep.lines_ok == 0
        and any("differs from its outcome" in p for p in rep.problems)
    )


def test_verify_finds_an_edited_event_object(tmp_path):
    ledger, sink, *_ = _one(tmp_path)
    obj = next((tmp_path / "audit" / "objects").glob("*.json"))
    obj.write_bytes(obj.read_bytes().replace(b"claimed:t", b"claimed:u"))
    rep = audit_mod.verify(ledger, sink)
    assert not rep.ok and rep.events_ok < rep.events_total


def test_verify_finds_a_line_with_no_outcome_event_and_an_outcome_with_no_line(tmp_path):
    ledger, sink, *_ = _one(tmp_path)
    ledger.append(make_line("7" * 32))
    audit = AskAudit(sink, principal="claimed:t")
    audit.outcome("8" * 32, question_sha256=H, decision="answered", ledger_sha256=H)
    probs = " | ".join(audit_mod.verify(ledger, sink).problems)
    assert "has no outcome event" in probs and "has no ledger line" in probs


def test_verify_finds_an_executed_attempt_without_an_intent_event(tmp_path):
    ledger, sink, *_ = _one(tmp_path, with_intent=False)
    # the attempt says executed but names no intent event
    assert any("without an intent event" in p for p in audit_mod.verify(ledger, sink).problems)


def test_verify_finds_an_orphan_intent(tmp_path):
    ledger, sink, *_ = _one(tmp_path)
    AskAudit(sink, principal="claimed:t").intent("5" * 32, question_sha256=H, sql_sha256=H)
    assert any("not in any ledger line" in p for p in audit_mod.verify(ledger, sink).problems)


def test_the_utc_stamp_shape():
    assert utc_stamp().endswith("Z") and len(utc_stamp()) == 20


def test_verify_reports_an_unreadable_event_object_instead_of_crashing(tmp_path):
    ledger, sink, *_ = _one(tmp_path)
    next((tmp_path / "audit" / "objects").glob("*.json")).write_bytes(b"{not json")
    rep = audit_mod.verify(ledger, sink)
    assert not rep.ok and any("could not be read" in p for p in rep.problems)
