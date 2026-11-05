"""The queue store's interfaces and failure modes after the WP4 reviews: export storage, strict stored JSON, WAL refusal, busy file, file creation,
caller-held transactions, login names, repr, and the rule that nobody but ``workqueue`` and ``queue_schema`` writes queue SQL."""

from __future__ import annotations

import ast
import inspect
import re
import sqlite3
from pathlib import Path

import pytest
from queue_helpers import GOOD_FIELDS, REASON, approve, assertive_all, drop_triggers, new_item, raw_insert, sha

from conftest import ROOT, settings_for_tests
from intake import cli, decisions, queue_schema, workqueue
from intake.codes import ConfigError, Refused
from intake.content_code import content_code

SRC = ROOT / "src" / "intake"


# ---- WAL ------------------------------------------------------------------------------------------------------------------------------------
class _Cursor:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class _Stub:
    """A connection that answers the WAL pragma with a fixed row or error, counting the calls."""

    def __init__(self, answer):
        self.answer, self.calls = answer, 0

    def execute(self, sql):
        self.calls += 1
        if self.calls > 500:
            raise AssertionError("the retry loop has no deadline")
        if isinstance(self.answer, Exception):
            raise self.answer
        return _Cursor((self.answer,))


def test_wal_refused_at_once_when_the_filesystem_answers_another_mode():
    stub = _Stub("delete")  # a share or WSL mount: the pragma returns the old mode, never an error
    with pytest.raises(ConfigError) as e:
        workqueue._enable_wal(stub)
    assert e.value.code == "bad_config" and "wal_unavailable" in e.value.text and stub.calls == 1


def test_wal_retry_has_a_deadline_checked_on_every_pass(monkeypatch):
    """A fake clock moves 0.1 s per reading and sleeping is free, so a loop WITHOUT a deadline reaches the stub's call limit and fails an assertion
    instead of hanging."""
    import types

    now = [0.0]

    def monotonic():
        now[0] += 0.1
        return now[0]

    monkeypatch.setattr(workqueue, "time", types.SimpleNamespace(monotonic=monotonic, sleep=lambda s: None))
    monkeypatch.setattr(workqueue, "WAL_WAIT_S", 0.3)
    stub = _Stub(sqlite3.OperationalError("database is locked"))
    with pytest.raises(ConfigError) as e:
        workqueue._enable_wal(stub)
    assert "wal_unavailable" in e.value.text and 2 <= stub.calls <= 10


def test_wal_other_operational_errors_are_not_retried():
    stub = _Stub(sqlite3.OperationalError("disk I/O error"))
    with pytest.raises(sqlite3.OperationalError):
        workqueue._enable_wal(stub)
    assert stub.calls == 1


def test_wal_accepts_wal_and_a_real_file_ends_in_wal(tmp_path):
    assert workqueue._enable_wal(_Stub("WAL")) is None
    with workqueue.opened(settings_for_tests(tmp_path)) as c:
        assert c.execute("PRAGMA journal_mode").fetchone()[0] == "wal"


# ---- busy file, file creation ---------------------------------------------------------------------------------------------------------------
def test_a_busy_queue_is_refused_db_busy_not_a_traceback(tmp_path):
    s = settings_for_tests(tmp_path)
    with workqueue.opened(s) as holder:
        holder.execute("BEGIN IMMEDIATE")
        other = sqlite3.connect(workqueue.queue_path(s), isolation_level=None)
        other.execute("PRAGMA busy_timeout=0")
        try:
            with pytest.raises(Refused) as e, workqueue.transaction(other):
                pass
            assert e.value.code == "db_busy"
        finally:
            other.close()
        holder.execute("ROLLBACK")


def test_the_queue_file_is_created_empty_before_sqlite_writes_to_it(tmp_path, monkeypatch):
    s = settings_for_tests(tmp_path)
    seen = []
    real = workqueue._precreate

    def spy(path):
        seen.append(path.exists())
        real(path)
        seen.append((path.exists(), path.stat().st_size))

    monkeypatch.setattr(workqueue, "_precreate", spy)
    workqueue.connect(s).close()
    assert seen == [False, (True, 0)]


def test_precreate_uses_the_owner_only_mode(tmp_path, monkeypatch):
    modes = []
    real_open = workqueue.os.open
    monkeypatch.setattr(workqueue.os, "open", lambda p, flags, mode=0o777: (modes.append(mode), real_open(p, flags, mode))[1])
    workqueue._precreate(tmp_path / "q.sqlite3")
    assert modes == [0o600]


def test_the_home_folder_is_made_owner_only(tmp_path, monkeypatch):
    s = settings_for_tests(tmp_path)
    import shutil

    shutil.rmtree(s.intake_home)
    calls = []
    real = Path.mkdir
    monkeypatch.setattr(
        Path, "mkdir", lambda self, mode=0o777, parents=False, exist_ok=False: (calls.append(mode), real(self, mode, parents, exist_ok))[1]
    )
    workqueue.connect(s).close()
    assert 0o700 in calls


# ---- schema: a dropped table is not silently rebuilt ----------------------------------------------------------------------------------------
@pytest.mark.parametrize("table", ["decisions", "purges", "exports", "meta"])
def test_a_dropped_table_is_refused_not_recreated(table, tmp_path):
    s = settings_for_tests(tmp_path)
    with workqueue.opened(s) as c:
        c.execute(f"DROP TABLE {table}")
    with pytest.raises(ConfigError) as e:
        workqueue.connect(s)
    assert e.value.code == "bad_config"


def test_a_stray_trigger_whose_name_holds_a_quote_is_dropped(tmp_path):
    s = settings_for_tests(tmp_path)
    with workqueue.opened(s) as c:
        c.execute('CREATE TRIGGER "we""ird" BEFORE UPDATE ON items BEGIN SELECT 1; END')
    with workqueue.opened(s) as c:
        names = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}
    assert names == set(queue_schema.trigger_sql())


# ---- export storage (what WP5 calls instead of hand-written SQL) ---------------------------------------------------------------------------
def _approved(s, name="a", **kw):
    it = new_item(s, name, **kw)
    approve(s, it, REASON if kw.get("flags") else None)
    return workqueue.get(s, it.id)


def _export(s, item, row_id="row-1", code=None, version=None, conn=None):
    code = code or content_code(item)
    with workqueue.opened(s) as c, workqueue.transaction(c):
        return workqueue.record_export(c, item, row_id, code, '{"row":1}', item.version if version is None else version)


def test_record_export_writes_the_receipt_then_bumps_the_version(tmp_path):
    s = settings_for_tests(tmp_path)
    it = _approved(s)
    ex = _export(s, it)
    got = workqueue.get(s, it.id)
    assert got.state == "EXPORTED" and got.version == it.version + 1
    with workqueue.opened(s) as c:
        assert workqueue.get_export(c, it.uid) == workqueue.exports_in_order(c)[0] == workqueue.export_by_row_id(c, "row-1")
        assert (ex.row_id, ex.item_uid, ex.content_code) == ("row-1", it.uid, content_code(it)) and ex.seq == 1
        assert workqueue.get_by_uid(c, it.uid).id == it.id and workqueue.get_by_uid(c, 9999) is None
        assert workqueue.get_export(c, 9999) is None and workqueue.export_by_row_id(c, "nope") is None


def test_record_export_refusals(tmp_path):
    s = settings_for_tests(tmp_path)
    a, b = _approved(s, "a"), _approved(s, "b")
    with pytest.raises(Refused) as e:
        _export(s, a, version=a.version + 5)  # the version moved: compare-and-set miss
    assert e.value.code == "stale_content"
    with workqueue.opened(s) as c:
        assert (
            workqueue.get_export(c, a.uid) is None and workqueue.get_by_uid(c, a.uid).state == "APPROVED"
        )  # the receipt rolled back with it
    with pytest.raises(Refused) as e:
        _export(s, a, code="0" * 64)  # a content code that is not the latest approve's
    assert e.value.code == "state_conflict"
    _export(s, a, row_id="same-row")
    with pytest.raises(Refused) as e:
        _export(s, b, row_id="same-row")
    assert e.value.code == "row_id_conflict"
    with workqueue.opened(s) as c, pytest.raises(Refused) as e, workqueue.transaction(c):
        workqueue.record_export(c, workqueue.get_by_uid(c, a.uid), "other-row", content_code(a), "{}", a.version + 1)
    assert e.value.code in ("already_exported", "state_conflict")
    ready = new_item(s, "r")
    with pytest.raises(Refused) as e:
        _export(s, ready)  # not approved
    assert e.value.code == "state_conflict"


def test_record_export_and_conn_arguments_need_a_transaction(tmp_path):
    s = settings_for_tests(tmp_path)
    it = _approved(s)
    with workqueue.opened(s) as c:
        with pytest.raises(ValueError):
            workqueue.record_export(c, it, "r", content_code(it), "{}", it.version)
        rd = new_item(s, "rd")
        with pytest.raises(ValueError):
            decisions.decide(s, rd.id, "approve", "ap-a", None, content_code(rd), rd.version, conn=c)
        with pytest.raises(ValueError):
            workqueue.purge(s, rd.id, conn=c)
        assert workqueue.get(s, rd.id).state == "READY"


def test_a_refused_decision_with_conn_is_undone_only_if_the_caller_rolls_back(tmp_path):
    s = settings_for_tests(tmp_path)
    it = new_item(s)
    with workqueue.opened(s) as c:
        with pytest.raises(Refused):
            with workqueue.transaction(c):
                decisions.decide(s, it.id, "approve", "ap-a", None, content_code(it), it.version + 1, conn=c)
        assert (
            c.execute("SELECT COUNT(*) FROM decisions").fetchone()[0] == 0
        )  # the Refused propagated, the caller's transaction rolled back
    assert workqueue.get(s, it.id).state == "READY"


# ---- no hand-written queue SQL outside workqueue and queue_schema ---------------------------------------------------------------------------
_SQL = re.compile(
    r"\b(INSERT\s+(OR\s+\w+\s+)?INTO|UPDATE\s+(items|decisions|exports|purges|item_mask_map|item_keys|item_trace)|DELETE\s+FROM|FROM\s+(items|decisions|exports|purges|item_mask_map|item_keys|item_trace))\b",
    re.I,
)
_QUEUE_OWNERS = {"workqueue.py", "queue_schema.py"}


def sql_strings(source: str) -> list[str]:
    return [
        n.value for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Constant) and isinstance(n.value, str) and _SQL.search(n.value)
    ]


# ALLOWLIST (one reasoned line, reviewed by the lead): budget.py is the spend ledger (WP1). It writes ONLY its own tables (meta, reservations, calls) and
# has ONE read-only statement over the queue, the ledger-vs-items cost check (spec 5.5: `SELECT COALESCE(SUM(cost_micro),0) FROM items`). Any other SQL
# string in budget.py that touches a queue table fails this test.
_LEDGER_TABLES = re.compile(r"\b(?:INSERT\s+(?:OR\s+\w+\s+)?INTO|UPDATE|DELETE\s+FROM|FROM)\s+(meta|reservations|calls)\b", re.I)
_ALLOWED_QUEUE_READ = "SELECT COALESCE(SUM(cost_micro),0) FROM items"
_QUEUE_TABLES = re.compile(r"\b(?:items|decisions|exports|purges|item_mask_map|item_keys|item_trace)\b", re.I)


def foreign_sql(file_name: str, source: str) -> list[str]:
    out = []
    for s in sql_strings(source):
        if file_name == "budget.py" and (
            _ALLOWED_QUEUE_READ in s or (_LEDGER_TABLES.search(s) and not _QUEUE_TABLES.search(_LEDGER_TABLES.sub("", s)))
        ):
            continue
        out.append(s[:60])
    return out


def test_only_workqueue_and_queue_schema_write_queue_sql():
    bad = []
    for f in sorted(SRC.rglob("*.py")):
        if (
            f.name in _QUEUE_OWNERS or "core_copy" in f.parts or f.name == "fake_ledger.py"
        ):  # fake_ledger: the existing in-memory order-flow ledger
            continue
        bad += [(f.name, s) for s in foreign_sql(f.name, f.read_text(encoding="utf-8"))]
    assert not bad, bad


def test_the_budget_allowlist_admits_only_the_ledger_tables_and_the_one_items_read():
    ok = "INSERT INTO meta(k,v) VALUES (?,?)"
    assert not foreign_sql("budget.py", f"q = {ok!r}")
    assert not foreign_sql("budget.py", f"q = {_ALLOWED_QUEUE_READ!r}")
    for stmt in (
        "INSERT INTO exports VALUES (1)",
        "UPDATE items SET state = 'x'",
        "DELETE FROM decisions",
        "SELECT * FROM items",
        "INSERT INTO calls SELECT * FROM items",
    ):
        assert foreign_sql("budget.py", f"q = {stmt!r}"), stmt
    assert foreign_sql("decisions.py", f"q = {ok!r}")  # the allowance is for budget.py only


def test_the_sql_scan_sees_each_statement_kind():
    for stmt in (
        "INSERT INTO exports VALUES (1)",
        "update items set x=1",
        "SELECT * FROM exports",
        "DELETE FROM items",
        "INSERT OR REPLACE INTO decisions (a) VALUES (1)",
    ):
        assert sql_strings(f"q = {stmt!r}"), stmt
    assert not sql_strings("q = 'SELECT 1'")


# ---- strict stored JSON ---------------------------------------------------------------------------------------------------------------------
POISON = {
    "nan": ("fields_json", '{"total_minor": NaN}'),
    "duplicate_key": ("fields_json", '{"a": 1, "a": 2}'),
    "fields_is_a_list": ("fields_json", "[1, 2]"),
    "surrogate": ("fields_json", '{"a": "\\ud800"}'),
    "flags_not_json": ("flags_json", "[not json"),
    "flags_not_a_list": ("flags_json", '{"a": 1}'),
    "flags_not_strings": ("flags_json", "[1, 2]"),
    "failing_not_a_list": ("failing_fields_json", '"x"'),
    "deep": ("fields_json", "[" * 5000 + "]" * 5000),
}


@pytest.mark.parametrize("name", sorted(POISON))
def test_a_poisoned_row_is_a_stored_data_error_and_does_not_hide_the_others(name, tmp_path):
    s = settings_for_tests(tmp_path)
    good = new_item(s, "good")
    col, val = POISON[name]
    with workqueue.opened(s) as c:
        drop_triggers(c)
        raw_insert(c, "bad", "RECEIVED")
        c.execute(f"UPDATE items SET {col} = ? WHERE id = 'bad'", (val,))
    with pytest.raises(Refused) as e:
        workqueue.get(s, "bad")
    assert e.value.code == "stored_data_bad" and val[:10] not in e.value.text
    assert [i.id for i in workqueue.list_items(s)] == [good.id]
    assert workqueue.list_items(s, "RECEIVED") == []
    assert workqueue.unreadable_ids(s) == ["bad"]
    with pytest.raises(Refused):  # a decision on it is refused, never a traceback
        decisions.decide(s, "bad", "reject", "ap-a", REASON, "0" * 64, 1)


@pytest.mark.parametrize(
    "field_change",
    [
        lambda f: f.update(invoice_no="INV" + chr(0xD800)),  # lone surrogate
        lambda f: f.update(total_minor=float("nan")),
        lambda f: f.update(total_minor=float("inf")),
        lambda f: f.update(extra={"a": [[[[1]]]]}),  # unknown field, nested
        lambda f: f.update(lines=[{"description": "x", "qty": 1, "unit_cost_minor": 1, "amount_minor": 1, "x": 1}]),
    ],
)
def test_set_result_stores_a_hostile_record_as_a_flagged_result_without_fields(field_change, tmp_path):
    import copy

    s = settings_for_tests(tmp_path)
    it = workqueue.insert_received(s, "a.txt", sha("a"), "t", s.tenant_id, "a")
    f = copy.deepcopy(GOOD_FIELDS)
    field_change(f)
    got = workqueue.set_result(
        s, it.uid, "READY", fields=f, flags=[], failing_fields=[], model_id="m", tier="read", prompt_sha256=None, cost_micro=0
    )
    assert got.state == "NEEDS_PERSON" and "X10" in got.flags and got.fields is None and got.failing_fields


def test_the_roundtrip_check_catches_a_value_the_validators_would_pass(tmp_path, monkeypatch):
    """Class check: whatever the validators say, a record that does not survive a strict-JSON round trip is not stored."""
    s = settings_for_tests(tmp_path)
    it = workqueue.insert_received(s, "a.txt", sha("a"), "t", s.tenant_id, "a")
    monkeypatch.setattr(workqueue.validators, "validate_record", lambda f, c=None: [])
    bad = dict(GOOD_FIELDS, total_minor=float("nan"))
    got = workqueue.set_result(
        s, it.uid, "READY", fields=bad, flags=[], failing_fields=[], model_id=None, tier=None, prompt_sha256=None, cost_micro=0
    )
    assert got.state == "NEEDS_PERSON" and got.failing_fields == ("record",) and got.fields is None


# ---- signatures, repr, tenant, login names --------------------------------------------------------------------------------------------------
def test_set_result_takes_everything_after_state_by_keyword(tmp_path):
    s = settings_for_tests(tmp_path)
    it = workqueue.insert_received(s, "a.txt", sha("a"), "t", s.tenant_id, "a")
    with pytest.raises(TypeError):
        workqueue.set_result(s, it.uid, "READY", GOOD_FIELDS, [], [], "m", "read", None, 0)
    params = inspect.signature(workqueue.set_result).parameters
    assert [n for n, p in params.items() if p.kind is p.KEYWORD_ONLY] == [
        "fields", "flags", "failing_fields", "model_id", "tier", "prompt_sha256", "cost_micro"
    ]  # fmt: skip


def test_a_tenant_that_is_not_the_deployments_is_refused(tmp_path):
    s = settings_for_tests(tmp_path)
    with pytest.raises(ValueError):
        workqueue.insert_received(s, "a.txt", sha("a"), "t", "someone-else", "a")
    with pytest.raises(ValueError):
        workqueue.insert_flagged(s, "a.pdf", sha("p"), "", "someone-else", "p", "X18")
    assert workqueue.list_items(s) == []


def test_repr_never_prints_the_invoice_text_or_the_values(tmp_path):
    s = settings_for_tests(tmp_path)
    it = new_item(s)
    with workqueue.opened(s) as c:
        approve(s, it)
        text = repr(workqueue.get_in(c, it.id)) + repr(workqueue.latest_decision(c, it.uid))
    assert "invoice text" not in text and "Acme" not in text and "INV-1001" not in text


def test_public_names_are_listed_and_documented():
    for name in workqueue.__all__:
        obj = getattr(workqueue, name)
        assert obj is not None
        if inspect.isfunction(obj):
            assert (obj.__doc__ or "").strip(), name
    for fn in (workqueue.scope, workqueue.get_in, workqueue.transaction, workqueue.connect, workqueue.opened, workqueue.record_export):
        assert (fn.__doc__ or "").strip()
    exported = {
        n for n, o in vars(workqueue).items() if inspect.isfunction(o) and not n.startswith("_") and o.__module__ == workqueue.__name__
    }
    assert exported <= set(workqueue.__all__), exported - set(workqueue.__all__)


def test_public_functions_are_typed():
    from intake import content_code as cc

    for fn in (
        workqueue.insert_received, workqueue.insert_flagged, workqueue.set_result, workqueue.apply_decision, workqueue.record_export,
        decisions.decide, cc.content_code, cc.record, cc.row_id, cc.item_row_id,
    ):  # fmt: skip
        sig = inspect.signature(fn)
        untyped = [n for n, p in sig.parameters.items() if p.annotation is inspect.Parameter.empty]
        assert not untyped and sig.return_annotation is not inspect.Signature.empty, (fn.__name__, untyped)


def test_purge_by_is_a_login_name_and_defaults_to_the_os_user(tmp_path, monkeypatch):
    s = settings_for_tests(tmp_path)
    a, b, c_ = new_item(s, "a"), new_item(s, "b"), new_item(s, "c")
    for bad in ("", "a b", "x" * 65, "-a", "a;b", None.__class__):
        with pytest.raises(ValueError):
            workqueue.purge(s, a.id, by=bad)
    assert workqueue.get(s, a.id) is not None
    workqueue.purge(s, a.id)
    monkeypatch.setattr(workqueue.getpass, "getuser", lambda: "We ird\\user!")
    workqueue.purge(s, b.id)
    monkeypatch.setattr(workqueue.getpass, "getuser", lambda: "")
    workqueue.purge(s, c_.id)
    with workqueue.opened(s) as c:
        who = [r[0] for r in c.execute("SELECT purged_by FROM purges ORDER BY seq")]
    assert all(workqueue.ACTOR_RE.fullmatch(w) for w in who) and who[1] == "We_ird_user_" and who[2] == "unknown"


def test_check_fails_and_says_so_when_the_queue_files_are_open(tmp_path, monkeypatch, capsys):
    s = settings_for_tests(tmp_path)
    workqueue.connect(s).close()
    monkeypatch.setenv("HADAVIN_LOCAL", str(s.local))
    monkeypatch.setenv("INTAKE_MODEL_BACKEND", "fake")
    monkeypatch.setattr(workqueue, "queue_files_state", lambda _s: "mode_too_open")
    assert cli.main(["check"]) == 2
    assert "queue_files: mode_too_open" in capsys.readouterr().out


# ---- the stored text is hashed at insert, frozen, and verified on read ---------------------------------------------------------------------------
def test_the_normalised_text_hash_is_stored_and_differs_from_the_raw_bytes_hash(tmp_path):
    import hashlib

    s = settings_for_tests(tmp_path)
    text = "Invoice INV-1001\ncaf" + chr(0xE9)
    raw_sha = hashlib.sha256(
        (text.replace("\n", "\r\n")).encode("utf-8")
    ).hexdigest()  # the file had CRLF: the raw hash is not the text hash
    it = workqueue.insert_received(s, "a.txt", raw_sha, text, s.tenant_id, "a")
    assert it.source_sha256 == raw_sha
    with workqueue.opened(s) as c:
        stored = c.execute("SELECT text_sha256 FROM items WHERE uid = ?", (it.uid,)).fetchone()[0]
    assert stored == hashlib.sha256(text.encode("utf-8")).hexdigest() != raw_sha == workqueue.get(s, it.id).source_sha256
    assert workqueue.text_hash("") == hashlib.sha256(b"").hexdigest()


def test_an_x18_item_with_empty_text_reads_back(tmp_path):
    s = settings_for_tests(tmp_path)
    it = workqueue.insert_flagged(s, "a.pdf", sha("pdf"), "", s.tenant_id, "pdf", "X18")
    assert workqueue.get(s, it.id).source_text == ""


@pytest.mark.parametrize("change", ["text", "hash"])
def test_a_text_that_does_not_match_its_stored_hash_is_a_stored_data_error(change, tmp_path):
    s = settings_for_tests(tmp_path)
    good = new_item(s, "good")
    it = new_item(s, "bad")
    with workqueue.opened(s) as c:
        drop_triggers(c, "intake_b_immutable")  # forge the damage under the guard that would stop it
        col, val = ("source_text", "changed after storing") if change == "text" else ("text_sha256", "0" * 64)
        c.execute(f"UPDATE items SET {col} = ? WHERE uid = ?", (val, it.uid))
    with pytest.raises(Refused) as e:
        workqueue.get(s, it.id)
    assert e.value.code == "stored_data_bad"
    assert [i.id for i in workqueue.list_items(s)] == [good.id] and workqueue.unreadable_ids(s) == [it.id]
    with pytest.raises(Refused):
        decisions.decide(s, it.id, "reject", "ap-a", REASON, "0" * 64, 1)  # a damaged item cannot be decided


# ---- layers that the API cannot reach separately: code layer on a forged connection, trigger layer by statement ---------------------------------------
def test_decide_on_a_received_item_is_refused_by_the_code_even_with_the_triggers_gone(tmp_path):
    """``decide(conn=...)`` runs on the caller's connection, so the triggers can be dropped on it: the code's own check must still answer."""
    s = settings_for_tests(tmp_path)
    rec = workqueue.insert_received(s, "r.txt", sha("r"), "t", s.tenant_id, "r")
    with workqueue.opened(s) as c:
        drop_triggers(c)
        c.execute("BEGIN IMMEDIATE")
        with pytest.raises(Refused) as e:
            decisions.decide(s, rec.id, "reject", "ap-a", REASON, content_code(rec), rec.version, conn=c)
        c.execute("ROLLBACK")
    assert e.value.code == "state_conflict" and "no result" in e.value.text


def test_record_export_refuses_a_second_receipt_by_code_even_with_the_triggers_gone(tmp_path):
    s = settings_for_tests(tmp_path)
    it = _approved(s)
    with workqueue.opened(s) as c:
        drop_triggers(c)
        c.execute("BEGIN IMMEDIATE")
        workqueue.record_export(c, workqueue.get_by_uid(c, it.uid), "row-1", content_code(it), "{}", it.version)
        again = workqueue.get_by_uid(c, it.uid)
        with pytest.raises(Refused) as e:
            workqueue.record_export(c, again, "row-2", content_code(it), "{}", again.version)
        c.execute("ROLLBACK")
    assert e.value.code == "already_exported"


def test_approved_unexported_leaves_out_an_item_that_already_has_a_receipt(tmp_path):
    """A forged state (APPROVED with a receipt, which a crash cannot produce because the two writes are one transaction): the list must still exclude it."""
    s = settings_for_tests(tmp_path)
    it = _approved(s)
    with workqueue.opened(s) as c:
        drop_triggers(c)
        c.execute(
            "INSERT INTO exports (row_id, item_uid, content_code, row_json, at) VALUES ('r', ?, ?, '{}', 'z')", (it.uid, content_code(it))
        )
        assert workqueue.approved_unexported(c) == []


def test_set_result_without_its_state_check_would_still_be_stopped_by_the_triggers(tmp_path):
    """``set_result`` opens its own connection (which restores the triggers), so its ``state = 'RECEIVED'`` check cannot be tested alone. This is the
    UNOBSERVABLE proof: the same UPDATE WITHOUT that check, run on a READY item, is refused by trigger (b) and, separately, by trigger (f); with neither
    trigger it succeeds."""
    from queue_helpers import only_triggers

    sql = (
        "UPDATE items SET state='NEEDS_PERSON', fields_json=NULL, flags_json='[\"L02\"]', failing_fields_json='[]', model_id=NULL, tier=NULL, "
        "prompt_sha256=NULL, cost_micro=0, version=version+1 WHERE uid=1"
    )
    for trig, msg in (("intake_b_immutable", "immutable"), ("intake_f_transitions", "state move")):
        with workqueue.opened(settings_for_tests(tmp_path / trig)) as c:
            raw_insert(c, "x", "READY", GOOD_FIELDS)
            only_triggers(c, trig)
            with pytest.raises(sqlite3.IntegrityError, match=msg):
                c.execute(sql)
    with workqueue.opened(settings_for_tests(tmp_path / "none")) as c:
        raw_insert(c, "x", "READY", GOOD_FIELDS)
        drop_triggers(c)
        c.execute(sql)


# ---- approval is decided in ONE place (errata 41e) ----------------------------------------------------------------------------------------------------
_APPROVAL_HELPERS = {"is_reject_only", "approvable", "reason_required"}  # flags.py internals that decide whether an item may be approved


def _called_names(source: str) -> set[str]:
    out = set()
    for n in ast.walk(ast.parse(source)):
        if isinstance(n, ast.Call):
            f = n.func
            out.add(f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else "")
    return out


def test_approval_is_decided_only_by_flags_approval_blocker():
    """No module but flags.py calls the approval internals; only decisions.py (and the exporter, WP5) calls ``approval_blocker``; nobody else compares
    a record's flags with the codes that block or need a reason."""
    users, internals, literals = set(), [], []
    codes = {"D06", "D10", "D12", "L01", "L02", "M01", "M02", "X10", "X18", "X28"}
    for f in sorted(SRC.rglob("*.py")):
        if "core_copy" in f.parts or f.name == "flags.py":
            continue
        src = f.read_text(encoding="utf-8")
        names = _called_names(src)
        if "approval_blocker" in names:
            users.add(f.name)
        internals += [(f.name, n) for n in sorted(names & _APPROVAL_HELPERS)]
        if f.name in (
            "decisions.py",
            "content_code.py",
            "exporter.py",
        ):  # workqueue.py only SETS flags (L02 on recovery, X10 on a bad record)
            literals += [(f.name, n.value) for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Constant) and n.value in codes]
    assert users <= {"decisions.py", "exporter.py"} and "decisions.py" in users, users
    assert not internals, internals
    assert not literals, literals  # decisions, the content code and the exporter never test for a particular flag code


def test_the_approval_scan_catches_a_second_decision_path():
    assert _called_names("flags.is_reject_only(c)") & _APPROVAL_HELPERS == {"is_reject_only"}
    assert "approval_blocker" in _called_names("x = flagtable.approval_blocker(f, ok)")


# ---- the clock seam (errata 41c) -----------------------------------------------------------------------------------------------------------------
def test_the_queue_clock_can_be_fixed_only_with_the_fake_backend_and_is_restorable(tmp_path):
    from datetime import UTC, datetime, timedelta, timezone

    s = settings_for_tests(tmp_path)
    live = settings_for_tests(tmp_path / "live", backend="anthropic")
    when = datetime(2026, 11, 3, 10, 0, 5, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    try:
        with pytest.raises(Refused) as e:
            workqueue.set_fixed_clock(live, when)
        assert e.value.code == "bad_config"
        with pytest.raises(ValueError):
            workqueue.set_fixed_clock(s, datetime(2026, 1, 1))  # no timezone
        workqueue.set_fixed_clock(s, when)
        assert workqueue.now_utc() == "2026-11-03T04:30:05Z"
        it = new_item(s)
        assert it.created_at == "2026-11-03T04:30:05Z"
        approve(s, it)
        with workqueue.opened(s) as c:
            assert workqueue.latest_decision(c, it.uid).at == "2026-11-03T04:30:05Z"
    finally:
        workqueue.reset_clock()
    assert abs(datetime.now(UTC) - datetime.strptime(workqueue.now_utc(), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)) < timedelta(seconds=5)


assertive_all(globals())
