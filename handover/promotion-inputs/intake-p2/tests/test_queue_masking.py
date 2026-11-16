"""WP2c P3: the mask map, the per-item key and the trace in the queue (design B3, errata 72): schema version 2, accessors, purge, caller limits.

The trigger scenarios themselves live in ``test_triggers.py``; here are the behaviours around them."""

from __future__ import annotations

import ast
import sqlite3
from pathlib import Path

import pytest
from queue_helpers import approve, drop_triggers, new_item, raw_insert, sha

from conftest import settings_for_tests
from intake import phrases, queue_schema, selfcheck_codes, workqueue
from intake.codes import ConfigError, Refused
from intake.selfcheck_codes import SelfCheckFailed

SRC = Path(__file__).resolve().parent.parent / "src" / "intake"
TEXT = "Pay to account 12345678 now. Mail jo@acme.example.com"
KEY = bytes(range(32))


def _received(s, name="m1", text=TEXT):
    it = workqueue.insert_received(s, f"{name}.txt", sha(name), text, s.tenant_id, name)
    assert isinstance(it, workqueue.Item)
    return it


def _span(text, needle, ph, kind, key=KEY, at=None):
    i = text.index(needle) if at is None else at
    return workqueue.MaskSpan(ph, kind, i, i + len(needle), workqueue._fp(key, needle), "t-1")


def _row(step="mask", result="pass", reason="", counts=None, fps=()):
    return workqueue.TraceRow(step, "2026-11-04T00:00:00Z", counts or {}, fps, result, reason)


def _store(s, it, key=KEY):
    spans = [
        _span(it.source_text, "12345678", "<BANK_1>", "BANK", key),
        _span(it.source_text, "jo@acme.example.com", "<EMAIL_1>", "EMAIL", key),
    ]
    workqueue.store_mask(s, it.uid, it.source_text, key, spans)
    return spans


# ---- version and old files ---------------------------------------------------------------------------------------------------------------------
def test_schema_version_is_two_and_a_new_file_carries_the_new_tables(tmp_path):
    assert queue_schema.SCHEMA_VERSION == "2"
    with workqueue.opened(settings_for_tests(tmp_path)) as c:
        names = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"item_mask_map", "item_keys", "item_trace"} <= names
    assert len(queue_schema.trigger_sql()) == 40  # 27 before WP2c plus the 12 new ones plus the meta insert-exists trigger (erratum 91)


def test_a_version_one_file_is_refused_with_bad_config(tmp_path):
    s = settings_for_tests(tmp_path)
    with workqueue.opened(s) as c:  # build a v1 file: no new tables, no new triggers, version '1'
        drop_triggers(c)
        for t in ("item_mask_map", "item_keys", "item_trace"):
            c.execute(f"DROP TABLE {t}")
        c.execute("UPDATE meta SET v = '1'")
    with pytest.raises(ConfigError) as e:
        workqueue.connect(s)
    assert e.value.code == "bad_config"


# ---- store_mask ----------------------------------------------------------------------------------------------------------------------------------
def test_store_and_restore_round_trip_with_none_versus_empty(tmp_path):
    s = settings_for_tests(tmp_path)
    it = _received(s)
    assert workqueue.restore_map(s, it.id) is None and workqueue.item_key(s, it.id) is None  # never masked
    _store(s, it)
    assert dict(workqueue.restore_map(s, it.id)) == {"<BANK_1>": "12345678", "<EMAIL_1>": "jo@acme.example.com"}
    assert workqueue.item_key(s, it.id) == KEY
    assert workqueue.restore_map(s, "no-such-item") is None
    empty = _received(s, "m2", "nothing hidden here")
    workqueue.store_mask(s, empty.uid, empty.source_text, KEY, [])
    assert dict(workqueue.restore_map(s, empty.id)) == {}  # masked, zero spans: empty, not None


def test_one_mark_may_have_several_spans_of_the_same_text(tmp_path):
    s = settings_for_tests(tmp_path)
    text = "acct 12345678 and again 12345678"
    it = _received(s, "m3", text)
    spans = [_span(text, "12345678", "<BANK_1>", "BANK", at=5), _span(text, "12345678", "<BANK_1>", "BANK", at=24)]
    workqueue.store_mask(s, it.uid, text, KEY, spans)
    assert dict(workqueue.restore_map(s, it.id)) == {"<BANK_1>": "12345678"}
    assert [x[2] for x in workqueue.all_spans_for_scan(s)] == ["12345678"]


def test_store_mask_is_idempotent_and_refuses_anything_different(tmp_path):
    s = settings_for_tests(tmp_path)
    it = _received(s)
    spans = _store(s, it)
    workqueue.store_mask(s, it.uid, it.source_text, KEY, list(reversed(spans)))  # same key, same spans: no-op
    for key, sp in ((bytes(32), spans), (KEY, spans[:1]), (KEY, [])):
        with pytest.raises(SelfCheckFailed) as e:
            workqueue.store_mask(s, it.uid, it.source_text, key, sp)
        assert e.value.code == "mask_failed"


def test_store_mask_refuses_a_text_whose_hash_differs_or_a_bad_span(tmp_path):
    s = settings_for_tests(tmp_path)
    it = _received(s)
    good = _span(TEXT, "12345678", "<BANK_1>", "BANK")
    for text, spans, key in (
        (TEXT + " ", [good], KEY),  # another text than the stored one
        (TEXT, [workqueue.MaskSpan("<BANK_1>", "BANK", 0, 4, workqueue._fp(KEY, "Pay "), "t-1")], bytes(32)),  # fingerprint of another key
        (TEXT, [workqueue.MaskSpan("<BANK_1>", "BANK", 10, len(TEXT) + 5, "abcdef01", "t-1")], KEY),  # past the end
        (TEXT, [good], b"short"),
    ):
        with pytest.raises(SelfCheckFailed):
            workqueue.store_mask(s, it.uid, text, key, spans)
    assert workqueue.item_key(s, it.id) is None  # nothing was written by any refusal


def test_store_mask_refuses_a_decided_item(tmp_path):
    s = settings_for_tests(tmp_path)
    it = new_item(s)
    with pytest.raises(SelfCheckFailed):
        workqueue.store_mask(s, it.uid, it.source_text, KEY, [])


@pytest.mark.parametrize("bad", [("bad mark", "BANK", 0, 3, "abcdef01"), ("<BANK_1>", "NOPE", 0, 3, "abcdef01"), ("<BANK_1>", "BANK", 3, 3, "abcdef01"),
                                 ("<BANK_1>", "BANK", 0, 3, "ABCDEF01"), ("<BANK_1>", "BANK", -1, 3, "abcdef01")])  # fmt: skip
def test_a_mask_span_with_a_bad_field_is_refused(bad):
    with pytest.raises(ValueError):
        workqueue.MaskSpan(*bad, "t-1")


def test_a_tampered_span_is_caught_by_restore_map(tmp_path):
    s = settings_for_tests(tmp_path)
    it = _received(s)
    _store(s, it)
    with workqueue.opened(s) as c:
        drop_triggers(c)
        c.execute("UPDATE item_mask_map SET span_start = span_start + 1, span_end = span_end + 1 WHERE placeholder = '<BANK_1>'")
    with pytest.raises(Refused) as e:
        workqueue.restore_map(s, it.id)
    assert e.value.code == "stored_data_bad"


# ---- add_trace / trace_rows -----------------------------------------------------------------------------------------------------------------
def test_trace_rows_come_back_in_order_with_derived_rows_last(tmp_path):
    s = settings_for_tests(tmp_path)
    it = _received(s, "t1")
    assert workqueue.add_trace(s, it.uid, _row("received", "info", counts={"bytes": 5}))
    assert workqueue.add_trace(s, it.uid, _row("mask", "pass", fps=(("<BANK_1>", "abcdef01"),)))
    done = workqueue.set_result(
        s,
        it.uid,
        "READY",
        fields=__import__("queue_helpers").GOOD_FIELDS,
        flags=[],
        model_id="m",
        tier="read",
        prompt_sha256="p" * 64,
        cost_micro=0,
    )
    approve(s, done)
    rows = workqueue.trace_rows(s, it.id)
    assert [r.step for r in rows] == ["received", "mask", "decision"]
    assert rows[0].counts == {"bytes": 5} and rows[1].fingerprints == (("<BANK_1>", "abcdef01"),)
    assert rows[2].reason_plain == phrases.phrases()["approved"] and rows[2].result == "pass"
    assert workqueue.trace_rows(s, "no-such-item") == []


def test_add_trace_returns_false_and_writes_nothing_for_approved(tmp_path):
    s = settings_for_tests(tmp_path)
    it = new_item(s, "t2")
    assert workqueue.add_trace(s, it.uid, _row("mask")) is True  # READY takes rows
    approve(s, it)
    assert workqueue.add_trace(s, it.uid, _row("selfcheck_e")) is False
    with workqueue.opened(s) as c:
        assert c.execute("SELECT count(*) FROM item_trace").fetchone()[0] == 1


def test_trace_rows_are_allowed_for_ready_needs_person_and_rejected_not_for_approved_or_exported(tmp_path):
    s = settings_for_tests(tmp_path)
    with workqueue.opened(s) as c:
        drop_triggers(c)
        ids = {
            st: raw_insert(c, f"s-{st}", st, {} if st != "RECEIVED" else None)
            for st in ("RECEIVED", "READY", "NEEDS_PERSON", "REJECTED", "APPROVED", "EXPORTED")
        }
    for st, uid in ids.items():
        assert workqueue.add_trace(s, uid, _row()) is (st not in ("APPROVED", "EXPORTED"))
    # the trigger is the second line: a statement that bypasses add_trace is refused
    with workqueue.opened(s) as c, pytest.raises(sqlite3.IntegrityError, match="after a decision"):
        c.execute("INSERT INTO item_trace (item_uid, step, at, result) VALUES (?, 'mask', 'z', 'pass')", (ids["APPROVED"],))


def test_add_trace_for_an_unknown_item_is_refused(tmp_path):
    with pytest.raises(Refused) as e:
        workqueue.add_trace(settings_for_tests(tmp_path), 999, _row())
    assert e.value.code == "not_found"


def test_trace_row_reason_must_be_a_phrase_and_the_vocabulary_is_closed():
    assert _row(reason=phrases.phrases()["mask_failed"]).reason_plain
    assert _row(reason=phrases.phrases()["bank_ok"]).reason_plain  # the template text with placeholders is what is stored
    for kw in (
        {"reason": "the account number is 12345678"},
        {"step": "not_a_step"},
        {"step": "run"},  # log-only
        {"result": "boom"},
        {"counts": {"not_a_count": 1}},
        {"counts": {"bytes": "5"}},
        {"counts": {"bytes": True}},
        {"fps": (("<BANK_1>", "ABCDEF01"),)},
        {"fps": (("12345678", "abcdef01"),)},
        {"fps": (("<BANK_1>",),)},
    ):
        with pytest.raises(ValueError):
            _row(**kw)
    with pytest.raises(ValueError):
        workqueue.TraceRow("mask", "not a time")


def test_add_trace_refuses_derived_steps_and_non_rows(tmp_path):
    s = settings_for_tests(tmp_path)
    it = _received(s)
    with pytest.raises(ValueError):
        workqueue.add_trace(s, it.uid, _row("decision"))
    with pytest.raises(ValueError):
        workqueue.add_trace(s, it.uid, {"step": "mask"})  # type: ignore[arg-type]


def test_selfcheck_reason_is_the_code_of_the_latest_failed_row(tmp_path):
    s = settings_for_tests(tmp_path)
    it = _received(s)
    assert workqueue.selfcheck_reason(s, it.id) is None
    workqueue.add_trace(s, it.uid, _row("selfcheck_a", "fail", phrases.phrases()["mask_residual"]))
    workqueue.add_trace(s, it.uid, _row("selfcheck_e", "pass"))
    assert workqueue.selfcheck_reason(s, it.id) == "mask_residual"
    workqueue.add_trace(s, it.uid, _row("selfcheck_b", "fail", phrases.phrases()["forged_mark"]))
    assert workqueue.selfcheck_reason(s, it.id) == "forged_mark"


def test_every_plain_sentence_of_a_self_check_code_is_unique(tmp_path):
    texts = list(selfcheck_codes.PLAIN.values())
    assert len(texts) == len(set(texts))  # selfcheck_reason maps a stored sentence back to its code


# ---- purge -----------------------------------------------------------------------------------------------------------------------------------------
def test_purge_deletes_spans_and_key_keeps_trace_and_a_rescan_starts_clean(tmp_path):
    s = settings_for_tests(tmp_path)
    it = _received(s)
    _store(s, it)
    workqueue.add_trace(s, it.uid, _row("mask"))
    workqueue.purge(s, it.id, by="op-a")
    with workqueue.opened(s) as c:
        assert c.execute("SELECT count(*) FROM item_mask_map").fetchone()[0] == 0
        assert c.execute("SELECT count(*) FROM item_keys").fetchone()[0] == 0
        assert c.execute("SELECT count(*) FROM item_trace").fetchone()[0] == 1  # trace rows stay: fingerprints and counts only
    again = _received(s)  # the same bytes come back as a new item with a new uid and no key
    assert again.uid != it.uid and workqueue.item_key(s, again.id) is None


# ---- insert-or-replace refusals through the real API connection -----------------------------------------------------------------------------
def test_insert_or_replace_cannot_rewrite_a_span_the_key_or_a_trace_row(tmp_path):
    s = settings_for_tests(tmp_path)
    it = _received(s)
    _store(s, it)
    workqueue.add_trace(s, it.uid, _row("mask"))
    with workqueue.opened(s) as c:
        for sql, params in (
            ("INSERT OR REPLACE INTO item_mask_map VALUES (?, '<BANK_1>', 'BANK', 15, 23, 'abcdef01', 'x')", (it.uid,)),
            ("INSERT OR REPLACE INTO item_keys VALUES (?, ?)", (it.uid, "b" * 64)),
            ("INSERT OR REPLACE INTO item_trace (seq, item_uid, step, at, result) VALUES (1, ?, 'mask', 'z', 'fail')", (it.uid,)),
        ):
            with pytest.raises(sqlite3.IntegrityError):
                c.execute(sql, params)


# ---- who may call what: AST tests ----------------------------------------------------------------------------------------------------------------
def _files():
    return [f for f in sorted(SRC.rglob("*.py")) if "core_copy" not in f.parts]


def _callers(name: str) -> set[str]:
    out = set()
    for f in _files():
        for n in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if isinstance(n, ast.Call) and (
                (isinstance(n.func, ast.Attribute) and n.func.attr == name) or (isinstance(n.func, ast.Name) and n.func.id == name)
            ):
                out.add(f.name)
    return out


def test_restore_map_is_called_only_from_the_review_page():
    assert _callers("restore_map") <= {"workqueue.py", "review_page.py"}


def test_all_spans_for_scan_is_called_only_from_logscan():
    assert _callers("all_spans_for_scan") <= {"workqueue.py", "logscan.py"}


def source_text_reads(source: str) -> list[str]:
    """Reads of ``source_text`` in one module: a plain attribute, ``getattr(x, "source_text")``, and ``asdict``/``astuple`` (which expose every field)."""
    found = []
    for n in ast.walk(ast.parse(source)):
        if isinstance(n, ast.Attribute) and n.attr == "source_text":
            found.append(f"attribute line {n.lineno}")
        if isinstance(n, ast.Call):
            fn = n.func
            name = fn.attr if isinstance(fn, ast.Attribute) else fn.id if isinstance(fn, ast.Name) else ""
            if name == "getattr" and len(n.args) >= 2 and isinstance(n.args[1], ast.Constant) and n.args[1].value == "source_text":
                found.append(f"getattr line {n.lineno}")
            if name in ("asdict", "astuple"):
                found.append(f"{name} line {n.lineno}")
    return found


def test_source_text_and_masked_request_callers():
    homes = {"workqueue.py", "tracelog.py", "review_page.py"}  # design B3's reader list; a further reader needs the lead's yes
    bad = []
    for f in _files():
        if f.name not in homes:
            bad += [(f.name, x) for x in source_text_reads(f.read_text(encoding="utf-8"))]
    assert not bad, bad
    assert _callers("masked_request") <= {"tracelog.py", "cli.py", "routes.py"}


@pytest.mark.parametrize(
    "src",
    [
        "x = item.source_text\n",
        "import dataclasses\ny = dataclasses.asdict(item)\n",
        "from dataclasses import astuple\nastuple(item)\n",
        "getattr(item, 'source_text')\n",
    ],
)
def test_the_reader_scan_catches_each_form(src):
    assert source_text_reads(src)
    assert source_text_reads("x = 1\n") == []


def test_queue_schema_and_workqueue_pass_bandit_at_medium():
    """Bandit B608 (string-built SQL) is a gate in the evidence run; the trigger text is joined from constants, never formatted into a SQL sentence."""
    bandit = pytest.importorskip("bandit")
    assert bandit
    import subprocess
    import sys

    done = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "bandit", "-q", "-ll", str(SRC / "queue_schema.py"), str(SRC / "workqueue.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert done.returncode == 0, done.stdout[-800:]


# ---- review 1 fixes: immutable rows, damaged rows, one snapshot, uid reuse, bare references, phrase cache ----------------------------------------
def test_a_trace_row_is_immutable_and_copies_its_counts():
    src = {"bytes": 5}
    row = _row(counts=src)
    src["bytes"] = 99
    src["not_a_count"] = 1
    assert row.counts == {"bytes": 5}
    with pytest.raises(TypeError):
        row.counts["bytes"] = 1  # type: ignore[index]
    with pytest.raises(AttributeError):
        row.step = "state"  # type: ignore[misc]
    assert row == _row(counts={"bytes": 5}) and row != _row(counts={"bytes": 6})


def test_add_trace_validates_again_the_values_it_writes(tmp_path):
    s = settings_for_tests(tmp_path)
    it = _received(s)

    class Liar(workqueue.TraceRow):
        counts = property(lambda self: {"not_a_count": 1})

    with pytest.raises(ValueError):
        workqueue.add_trace(s, it.uid, Liar("mask", "2026-11-04T00:00:00Z"))
    with workqueue.opened(s) as c:
        assert c.execute("SELECT count(*) FROM item_trace").fetchone()[0] == 0


@pytest.mark.parametrize(
    "kw", [{"fingerprints": None}, {"counts": 5}, {"counts": [("bytes", 1)]}, {"fingerprints": "abcd"}, {"fingerprints": [None]}]
)
def test_a_trace_row_with_a_wrong_container_raises_value_error_not_type_error(kw):
    with pytest.raises(ValueError):
        workqueue.TraceRow("mask", "2026-11-04T00:00:00Z", **kw)


def test_a_damaged_key_row_is_stored_data_bad_and_a_damaged_span_row_is_mask_failed(tmp_path):
    s = settings_for_tests(tmp_path)
    it = _received(s)
    _store(s, it)
    with workqueue.opened(s) as c:
        drop_triggers(c)
        c.execute("UPDATE item_keys SET fp_key = ?", ("z" * 64,))
    for fn in (workqueue.item_key, workqueue.restore_map):
        with pytest.raises(Refused) as e:
            fn(s, it.id)
        assert e.value.code == "stored_data_bad"
    other = _received(s, "m9", "other text")
    workqueue.store_mask(s, other.uid, other.source_text, KEY, [])
    with workqueue.opened(s) as c:
        drop_triggers(c)
        c.execute("INSERT INTO item_mask_map VALUES (?, 'bad mark', 'BANK', 0, 3, 'abcdef01', 'd')", (other.uid,))
    with pytest.raises(SelfCheckFailed) as e2:
        workqueue.store_mask(s, other.uid, other.source_text, KEY, [])
    assert e2.value.code == "mask_failed"
    with pytest.raises(Refused):
        workqueue.restore_map(s, other.id)


def test_restore_map_reads_one_snapshot_even_if_the_item_is_purged_midway(tmp_path, monkeypatch):
    s = settings_for_tests(tmp_path)
    it = _received(s)
    _store(s, it)
    real = workqueue._read_spans

    def purge_then_read(c, uid):
        workqueue.purge(s, it.id, by="op-a")  # another connection removes the item between the statements of the reader
        return real(c, uid)

    monkeypatch.setattr(workqueue, "_read_spans", purge_then_read)
    assert dict(workqueue.restore_map(s, it.id)) == {"<BANK_1>": "12345678", "<EMAIL_1>": "jo@acme.example.com"}


def test_trace_rows_survive_a_purge_and_a_raw_insert_that_reuses_the_uid_re_attaches_them(tmp_path):
    """The actual behaviour, pinned: trace rows stay after a purge; SQL does not stop a raw INSERT with the old uid, so the old rows show up under the
    new item. Nothing in the code does that (uid is AUTOINCREMENT and every insert goes through ``insert_received``)."""
    s = settings_for_tests(tmp_path)
    it = _received(s, "u1")
    workqueue.add_trace(s, it.uid, _row("mask", "pass"))
    workqueue.purge(s, it.id, by="op-a")
    assert workqueue.trace_rows(s, it.id) == []  # an item that does not exist shows no rows
    with workqueue.opened(s) as c:
        c.execute(
            "INSERT INTO items (uid, id, source_name, source_sha256, tenant_id, state, created_at) VALUES (?, 'u2', 'u2.txt', ?, ?, 'RECEIVED', 'z')",
            (it.uid, sha("u2"), s.tenant_id),
        )
    assert [r.step for r in workqueue.trace_rows(s, "u2")] == ["mask"]
    # insert_received never reuses a uid
    assert _received(s, "u3").uid > it.uid


def _refs_in(source: str, name: str) -> bool:
    """True when the module text mentions ``name`` as a call, a bare reference (``partial``, an alias, a stored function), an import or a string for
    ``getattr``. Ceiling, stated plainly: exact names only; it does not see a computed name (``getattr(x, "restore_" + "map")``), ``vars(...)``, a star
    import, ``importlib`` with a dotted string, or another file with the same base name. Two names for one file in different folders count as one."""
    return any(
        (isinstance(n, ast.Name) and n.id == name)
        or (isinstance(n, ast.Attribute) and n.attr == name)
        or (isinstance(n, ast.alias) and n.name == name)
        or (isinstance(n, ast.Constant) and n.value == name)
        for n in ast.walk(ast.parse(source))
    )


def _references(name: str) -> set[str]:
    """The base names of the product modules that mention ``name`` in any form ``_refs_in`` sees."""
    return {f.name for f in _files() if _refs_in(f.read_text(encoding="utf-8"), name)}


def test_the_restricted_readers_are_not_referenced_in_any_form_outside_their_callers():
    assert _references("restore_map") <= {"workqueue.py", "review_page.py"}
    assert _references("all_spans_for_scan") <= {"workqueue.py", "logscan.py"}
    assert _references("item_key") <= {
        "workqueue.py",
        "pipeline.py",
        "tracelog.py",
    }  # the stored key: the retry of an item and the masked request


def test_the_reference_scan_catches_every_form_it_claims_and_states_its_ceiling():
    for src in (
        "wq.restore_map(s, i)\n",
        "f = wq.restore_map\n",
        "functools.partial(wq.restore_map, s)\n",
        "from wq import restore_map as r\n",
        "getattr(wq, 'restore_map')\n",
    ):
        assert _refs_in(src, "restore_map"), src
    assert not _refs_in("x = 1\n", "restore_map")
    for src in (
        "getattr(wq, 'restore_' + 'map')\n",
        "vars(wq)['rest' 'ore']\n",
        "from wq import *\n",
    ):  # the stated ceiling: these are NOT seen
        assert not _refs_in(src, "restore_map"), src


def test_add_trace_writes_the_values_it_checked_not_a_second_read(tmp_path):
    s = settings_for_tests(tmp_path)
    it = _received(s)

    class Twice(workqueue.TraceRow):
        reads = {"counts": 0, "reason": 0}

        @property
        def counts(self):  # type: ignore[override]
            Twice.reads["counts"] += 1
            return {"bytes": 1} if Twice.reads["counts"] == 1 else {"not_a_count": 1}

        @property
        def reason_plain(self):  # type: ignore[override]
            Twice.reads["reason"] += 1
            return "" if Twice.reads["reason"] == 1 else "the account number is 12345678"

    assert workqueue.add_trace(s, it.uid, Twice("mask", "2026-11-04T00:00:00Z")) is True
    with workqueue.opened(s) as c:
        row = c.execute("SELECT counts_json, reason_plain FROM item_trace").fetchone()
    assert tuple(row) == ('{"bytes":1}', "")  # the first answers, the checked ones


@pytest.mark.parametrize("bad", [b"a" * 64, "A" * 64, "g" * 64])
def test_a_stored_key_that_is_not_lower_case_hex_is_stored_data_bad(bad, tmp_path):
    s = settings_for_tests(tmp_path)
    it = _received(s)
    _store(s, it)
    with workqueue.opened(s) as c:
        drop_triggers(c)
        c.execute("UPDATE item_keys SET fp_key = ?", (bad,))
    for fn in (workqueue.item_key, workqueue.restore_map):
        with pytest.raises(Refused) as e:
            fn(s, it.id)
        assert e.value.code == "stored_data_bad"


def test_insert_or_replace_cannot_rewrite_the_schema_version_even_without_recursive_triggers(tmp_path):
    with workqueue.opened(settings_for_tests(tmp_path)) as c:
        c.execute("PRAGMA recursive_triggers=OFF")  # erratum 91: the insert trigger itself refuses, the delete trigger is not needed
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            c.execute("INSERT OR REPLACE INTO meta (k, v) VALUES ('schema_version', '9')")


def test_all_spans_for_scan_returns_item_uid_mark_and_the_slice_of_the_stored_text(tmp_path):
    s = settings_for_tests(tmp_path)
    it = _received(s)
    spans = _store(s, it)
    got = workqueue.all_spans_for_scan(s)
    assert got == [
        (it.uid, sp.placeholder, it.source_text[sp.span_start : sp.span_end]) for sp in sorted(spans, key=lambda x: x.span_start)
    ]


class _Liar(str):
    """A str that says it equals anything: it would pass a membership test."""

    def __eq__(self, other):
        return True

    def __hash__(self):
        return 0


@pytest.mark.parametrize(
    "kw",
    [
        {"step": _Liar("bogus")},
        {"result": _Liar("bogus")},
        {"at": _Liar("not a time")},
        {"reason_plain": _Liar("the account number is 12345678")},
        {"counts": {_Liar("bogus"): 1}},
        {"fingerprints": ((_Liar("not a mark"), "abcdef01"),)},
        {"fingerprints": (("<BANK_1>", _Liar("zzzzzzzz")),)},
    ],
)
def test_a_str_subclass_cannot_slip_past_the_vocabulary_check(kw):
    args = {"step": "mask", "at": "2026-11-04T00:00:00Z", **kw}
    with pytest.raises(ValueError):
        workqueue.TraceRow(**args)


def test_add_trace_writes_the_first_answer_of_every_property_not_a_later_one(tmp_path):
    s = settings_for_tests(tmp_path)
    it = _received(s)
    reads: dict[str, int] = {}

    def once(name, first, later):
        def getter(self):
            reads[name] = reads.get(name, 0) + 1
            return first if reads[name] == 1 else later

        return property(getter)

    class Twice(workqueue.TraceRow):
        step = once("step", "mask", "bogus")
        at = once("at", "2026-11-04T00:00:00Z", "not a time")
        result = once("result", "pass", "bogus")
        fingerprints = once("fps", (("<BANK_1>", "abcdef01"),), (("12345678", "zz"),))

    assert workqueue.add_trace(s, it.uid, Twice("mask", "2026-11-04T00:00:00Z")) is True
    with workqueue.opened(s) as c:
        row = c.execute("SELECT step, at, result, fingerprints_json FROM item_trace").fetchone()
    assert tuple(row) == ("mask", "2026-11-04T00:00:00Z", "pass", '[["<BANK_1>","abcdef01"]]')


def test_all_spans_for_scan_skips_a_span_that_runs_past_its_text(tmp_path):
    s = settings_for_tests(tmp_path)
    it = _received(s)
    _store(s, it)
    with workqueue.opened(s) as c:
        drop_triggers(c)
        c.execute("UPDATE item_mask_map SET span_end = ? WHERE placeholder = '<EMAIL_1>'", (len(it.source_text) + 40,))
    assert [x[1] for x in workqueue.all_spans_for_scan(s)] == ["<BANK_1>"]  # the damaged one is skipped, not returned cut short
