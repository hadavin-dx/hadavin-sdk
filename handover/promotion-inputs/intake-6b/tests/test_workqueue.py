"""The work queue (spec 7): connect, insert, compare-and-set results, crash recovery, purge and the two commands that touch the queue."""

from __future__ import annotations

import ast
import os
import shutil
import sqlite3
import subprocess
import sys

import pytest
from queue_helpers import GOOD_FIELDS, approve, assertive_all, drop_triggers, new_item, raw_export, raw_insert, reject, sha

from conftest import settings_for_tests
from intake import cli, queue_schema, workqueue
from intake.codes import Refused


def _triggers(conn):
    return {
        r["name"]: queue_schema.normalise_sql(r["sql"]) for r in conn.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger'")
    }


def test_connect_creates_schema_pragmas_and_all_triggers(tmp_path):
    s = settings_for_tests(tmp_path)
    conn = workqueue.connect(s)
    try:
        assert conn.execute("PRAGMA recursive_triggers").fetchone()[0] == 1
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert conn.execute("PRAGMA busy_timeout").fetchone()[0] >= 5000
        tables = {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"items", "decisions", "exports"} <= tables
        # the stored text equals what we generate: the next open finds nothing to recreate
        assert _triggers(conn) == {k: queue_schema.normalise_sql(v) for k, v in queue_schema.trigger_sql().items()}
    finally:
        conn.close()


def test_connect_makes_the_home_folder(tmp_path):
    s = settings_for_tests(tmp_path)
    shutil.rmtree(s.intake_home)
    workqueue.connect(s).close()
    assert (s.intake_home / "queue.sqlite3").is_file()


def test_connect_restores_a_dropped_or_stray_trigger(tmp_path):
    s = settings_for_tests(tmp_path)
    with workqueue.opened(s) as c:
        drop_triggers(c, "intake_d_items_delete", "intake_e_exports_insert")
        c.execute("CREATE TRIGGER intake_stray BEFORE UPDATE ON items BEGIN SELECT 1; END")
    with workqueue.opened(s) as c:
        assert _triggers(c) == {k: queue_schema.normalise_sql(v) for k, v in queue_schema.trigger_sql().items()}


def test_item_id_duplicate_and_bad_stem(tmp_path):
    s = settings_for_tests(tmp_path)
    a = workqueue.insert_received(s, "a.txt", sha("a"), "t", s.tenant_id, "a")
    assert a.id == "a-" + sha("a")[:8] and a.state == "RECEIVED" and a.version == 1 and a.fields is None and a.flags == ()
    dup = workqueue.insert_received(s, "other-name.txt", sha("a"), "t", s.tenant_id, "other")
    assert dup == workqueue.Duplicate(a.id)
    for bad in ("CON", "con.x", ".hidden", "a b", "x" * 129, ""):
        with pytest.raises(Refused) as e:
            workqueue.insert_received(s, "f.txt", sha("f" + bad), "t", s.tenant_id, bad)
        assert e.value.code == "bad_name"
    assert len(workqueue.list_items(s)) == 1


def test_id_collision_is_refused_not_called_a_duplicate(tmp_path):
    s = settings_for_tests(tmp_path)
    h1, h2 = "ab" * 4 + "0" * 56, "ab" * 4 + "1" * 56
    workqueue.insert_received(s, "a.txt", h1, "t", s.tenant_id, "a")
    with pytest.raises(Refused) as e:
        workqueue.insert_received(s, "a.txt", h2, "t", s.tenant_id, "a")
    assert e.value.code == "id_collision"


def test_insert_state_and_flags_must_agree(tmp_path):
    s = settings_for_tests(tmp_path)
    for kw in ({"state": "NEEDS_PERSON"}, {"flags": ("L02",)}, {"state": "READY"}):
        with pytest.raises(ValueError):
            workqueue.insert_received(s, "a.txt", sha("a"), "t", s.tenant_id, "a", **kw)
    it = workqueue.insert_received(s, "a.txt", sha("a"), "t", s.tenant_id, "a", state="NEEDS_PERSON", flags=("L02",))
    assert it.state == "NEEDS_PERSON" and it.flags == ("L02",)
    with pytest.raises(Exception, match="X99"):  # an unknown flag raises
        workqueue.insert_flagged(s, "b.txt", sha("b"), "t", s.tenant_id, "b", "X99")


def test_insert_flagged_makes_a_needs_person_item_without_fields(tmp_path):
    s = settings_for_tests(tmp_path)
    it = workqueue.insert_flagged(s, "scan.pdf", sha("p"), "", s.tenant_id, "scan", "X18")
    assert (it.state, it.flags, it.fields, it.source_text) == ("NEEDS_PERSON", ("X18",), None, "")
    assert isinstance(workqueue.insert_flagged(s, "scan.pdf", sha("p"), "", s.tenant_id, "scan", "X18"), workqueue.Duplicate)


def test_set_result_ready_then_a_second_result_is_refused(tmp_path):
    s = settings_for_tests(tmp_path)
    it = workqueue.insert_received(s, "a.txt", sha("a"), "t", s.tenant_id, "a")
    done = workqueue.set_result(
        s,
        it.uid,
        "READY",
        fields=GOOD_FIELDS,
        flags=[],
        failing_fields=[],
        model_id="m",
        tier="read",
        prompt_sha256="p" * 64,
        cost_micro=1234,
    )
    assert (done.state, done.version, done.cost_micro, done.fields, done.model_id, done.tier) == (
        "READY",
        2,
        1234,
        GOOD_FIELDS,
        "m",
        "read",
    )
    with pytest.raises(Refused) as e:
        workqueue.set_result(
            s,
            it.uid,
            "NEEDS_PERSON",
            fields=None,
            flags=["L02"],
            failing_fields=[],
            model_id=None,
            tier=None,
            prompt_sha256=None,
            cost_micro=0,
        )
    assert e.value.code == "state_conflict"
    assert workqueue.get(s, it.id).state == "READY" and workqueue.get(s, it.id).version == 2


def test_set_result_needs_person_sorts_flags_and_keeps_failing_fields(tmp_path):
    s = settings_for_tests(tmp_path)
    it = workqueue.insert_received(s, "a.txt", sha("a"), "t", s.tenant_id, "a")
    done = workqueue.set_result(
        s,
        it.uid,
        "NEEDS_PERSON",
        fields=None,
        flags=["X10", "D06", "X10"],
        failing_fields=["total_minor"],
        model_id="m",
        tier="fallback",
        prompt_sha256="p" * 64,
        cost_micro=9,
    )
    assert done.flags == ("D06", "X10") and done.failing_fields == ("total_minor",)


@pytest.mark.parametrize(
    "state,fields,flags",
    [
        ("READY", GOOD_FIELDS, ["D06"]),
        ("NEEDS_PERSON", GOOD_FIELDS, []),
        ("READY", None, []),
        ("APPROVED", GOOD_FIELDS, []),
        ("RECEIVED", None, []),
    ],
)
def test_set_result_rejects_an_inconsistent_state(tmp_path, state, fields, flags):
    s = settings_for_tests(tmp_path)
    it = workqueue.insert_received(s, "a.txt", sha("a"), "t", s.tenant_id, "a")
    with pytest.raises(ValueError):
        workqueue.set_result(
            s, it.uid, state, fields=fields, flags=flags, failing_fields=[], model_id=None, tier=None, prompt_sha256=None, cost_micro=0
        )
    assert workqueue.get(s, it.id).state == "RECEIVED"


def test_get_and_list_filter_and_order(tmp_path):
    s = settings_for_tests(tmp_path)
    a, b = new_item(s, "a"), new_item(s, "b", flags=["D06"])
    assert workqueue.get(s, "nope") is None
    assert [i.id for i in workqueue.list_items(s)] == [a.id, b.id]
    assert [i.id for i in workqueue.list_items(s, "NEEDS_PERSON")] == [b.id]
    assert workqueue.list_items(s, "EXPORTED") == []


def test_recover_received_after_a_real_crash(tmp_path):
    """A process dies after the insert and before the result (``os._exit``): the next start makes the item NEEDS_PERSON with L02."""
    s = settings_for_tests(tmp_path)
    code = (
        "import os\n"
        "from intake import settings, workqueue\n"
        "s = settings.load()\n"
        f"workqueue.insert_received(s, 'c.txt', '{sha('c')}', 'text', s.tenant_id, 'c')\n"
        "os._exit(7)\n"
    )
    env = {**os.environ, "HADAVIN_LOCAL": str(s.local), "INTAKE_MODEL_BACKEND": "fake"}
    r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, timeout=120)  # noqa: S603
    assert r.returncode == 7, r.stderr[-300:]
    assert workqueue.list_items(s)[0].state == "RECEIVED"
    new_item(s, "ready-one")  # an item that has a result is left alone
    ids = workqueue.recover_received(s, serve_lock_held=lambda: True)
    assert ids == ["c-" + sha("c")[:8]]
    got = workqueue.get(s, ids[0])
    assert (got.state, got.flags, got.fields, got.version) == ("NEEDS_PERSON", ("L02",), None, 2)
    assert workqueue.recover_received(s, serve_lock_held=lambda: True) == []  # idempotent
    with pytest.raises(Refused):  # the late result of the dead run cannot overwrite it
        workqueue.set_result(
            s,
            got.uid,
            "READY",
            fields=GOOD_FIELDS,
            flags=[],
            failing_fields=[],
            model_id="m",
            tier="read",
            prompt_sha256="p" * 64,
            cost_micro=0,
        )


def test_purge_allowed_states_keep_decisions_and_refuse_unknown(tmp_path):
    s = settings_for_tests(tmp_path)
    rec = workqueue.insert_received(s, "r.txt", sha("r"), "t", s.tenant_id, "r")
    ready, np_, rej = new_item(s, "ready"), new_item(s, "np", flags=["D06"]), new_item(s, "rej")
    reject(s, rej)
    for it in (rec, ready, np_, rej):
        workqueue.purge(s, it.id)
        assert workqueue.get(s, it.id) is None
    with workqueue.opened(s) as c:
        assert c.execute("SELECT COUNT(*) FROM decisions").fetchone()[0] == 1  # decisions are never removed
    with pytest.raises(Refused) as e:
        workqueue.purge(s, "gone-12345678")
    assert e.value.code == "not_found"


def test_purge_refuses_approved(tmp_path):
    s = settings_for_tests(tmp_path)
    it = new_item(s, "a")
    approve(s, it)
    with pytest.raises(Refused) as e:
        workqueue.purge(s, it.id)
    assert e.value.code == "purge_refused"
    assert workqueue.get(s, it.id).state == "APPROVED"


def test_purge_refuses_an_item_that_has_an_export_row(tmp_path):
    """Not reachable through the API for a READY item, so the guard trigger is removed on one connection to build the situation."""
    s = settings_for_tests(tmp_path)
    it = new_item(s, "a")
    with workqueue.opened(s) as c:
        drop_triggers(c, "intake_e_exports_insert")
        raw_export(c, it.uid)
    with pytest.raises(Refused) as e:
        workqueue.purge(s, it.id)
    assert e.value.code == "purge_refused"


def test_cli_init_creates_the_queue_and_purge_needs_yes(tmp_path, monkeypatch, capsys):
    s = settings_for_tests(tmp_path)
    monkeypatch.setenv("HADAVIN_LOCAL", str(s.local))
    monkeypatch.setenv("INTAKE_MODEL_BACKEND", "fake")
    assert cli.main(["init"]) == 0
    assert (s.intake_home / "queue.sqlite3").is_file()
    assert cli.main(["init"]) == 0  # idempotent
    it = new_item(s, "a")
    with pytest.raises(SystemExit) as e:
        cli.main(["purge", it.id])
    assert e.value.code == 3 and workqueue.get(s, it.id) is not None  # no --yes: nothing happens
    assert cli.main(["purge", "unknown-id", "--yes"]) == 3
    assert cli.main(["purge", it.id, "--yes"]) == 0 and workqueue.get(s, it.id) is None
    capsys.readouterr()
    ap = new_item(s, "b")
    approve(s, ap)
    assert cli.main(["purge", ap.id, "--yes"]) == 2
    assert "purge_refused" in capsys.readouterr().err


# ---- schema verification, recovery guard, purge record, accessors, files, opening scan -------------------------------------------------------------
def test_connect_restores_a_same_name_trigger_with_a_different_body(tmp_path):
    s = settings_for_tests(tmp_path)
    with workqueue.opened(s) as c:
        c.execute("DROP TRIGGER intake_b_immutable")
        c.execute("CREATE TRIGGER intake_b_immutable BEFORE UPDATE ON items BEGIN SELECT 1; END")  # same name, harmless body
    with workqueue.opened(s) as c:
        assert _triggers(c) == {k: queue_schema.normalise_sql(v) for k, v in queue_schema.trigger_sql().items()}
        raw = c.execute("SELECT sql FROM sqlite_master WHERE name = 'intake_b_immutable'").fetchone()[0]
        assert "OLD.state <> 'RECEIVED'" in raw


@pytest.mark.parametrize("table", ["items", "decisions", "exports", "purges", "meta"])
def test_connect_refuses_a_table_whose_definition_was_changed(table, tmp_path):
    """``CREATE TABLE IF NOT EXISTS`` would keep a tampered table: the stored definition is compared with the wanted one."""
    from intake.codes import ConfigError

    s = settings_for_tests(tmp_path)
    with workqueue.opened(s) as c:
        c.execute(f"ALTER TABLE {table} ADD COLUMN extra TEXT")  # any change to the stored definition
    with pytest.raises(ConfigError) as e:
        workqueue.connect(s)
    assert e.value.code == "bad_config"


def test_connect_refuses_a_table_missing_its_check_constraint(tmp_path):
    from intake.codes import ConfigError

    s = settings_for_tests(tmp_path)
    with workqueue.opened(s) as c:
        c.execute("DROP TABLE decisions")
        c.execute(
            "CREATE TABLE decisions (seq INTEGER PRIMARY KEY AUTOINCREMENT, item_uid INTEGER NOT NULL, decision TEXT NOT NULL, approver TEXT NOT NULL, reason TEXT, content_code TEXT NOT NULL, at TEXT NOT NULL)"
        )
    with pytest.raises(ConfigError):
        workqueue.connect(s)


def test_recover_received_needs_the_serve_lock(tmp_path):
    s = settings_for_tests(tmp_path)
    workqueue.insert_received(s, "r.txt", sha("r"), "t", s.tenant_id, "r")
    for bad in (lambda: False, lambda: None, lambda: 1, None, True):
        with pytest.raises(Refused) as e:
            workqueue.recover_received(s, serve_lock_held=bad)
        assert e.value.code == "state_conflict"
    with pytest.raises(TypeError):
        workqueue.recover_received(s)  # no default: the caller must say how it knows
    assert workqueue.list_items(s)[0].state == "RECEIVED"
    assert workqueue.recover_received(s, serve_lock_held=lambda: True) == ["r-" + sha("r")[:8]]


def test_purge_writes_one_audit_row_without_text_and_it_is_append_only(tmp_path):
    s = settings_for_tests(tmp_path)
    it = new_item(s, "a")
    workqueue.purge(s, it.id, by="lead")
    with workqueue.opened(s) as c:
        rows = [dict(r) for r in c.execute("SELECT * FROM purges")]
        assert len(rows) == 1 and rows[0]["item_id"] == it.id and rows[0]["purged_by"] == "lead" and rows[0]["state"] == "READY"
        assert "invoice text" not in str(rows)
        with pytest.raises(Exception, match="append-only"):
            c.execute("DELETE FROM purges")
    with pytest.raises(Refused):
        workqueue.purge(s, it.id)  # unknown now: no second audit row
    with workqueue.opened(s) as c:
        assert c.execute("SELECT COUNT(*) FROM purges").fetchone()[0] == 1


def test_a_refused_purge_leaves_no_audit_row(tmp_path):
    s = settings_for_tests(tmp_path)
    it = new_item(s, "a")
    approve(s, it)
    with pytest.raises(Refused):
        workqueue.purge(s, it.id)
    with workqueue.opened(s) as c:
        assert c.execute("SELECT COUNT(*) FROM purges").fetchone()[0] == 0


def test_purge_inside_a_caller_transaction_is_undone_by_the_callers_rollback(tmp_path):
    s = settings_for_tests(tmp_path)
    it = new_item(s, "a")
    with workqueue.opened(s) as c:
        with pytest.raises(RuntimeError):
            with workqueue.transaction(c):
                workqueue.purge(s, it.id, conn=c)
                raise RuntimeError("x")
    assert workqueue.get(s, it.id) is not None


def test_accessors_latest_decision_approved_unexported_and_exports_in_order(tmp_path):
    from queue_helpers import REASON

    from intake.content_code import content_code

    s = settings_for_tests(tmp_path)
    a, b, c_ = new_item(s, "a"), new_item(s, "b"), new_item(s, "c")
    with workqueue.opened(s) as c:
        assert (
            workqueue.latest_decision(c, a.uid) is None and workqueue.approved_unexported(c) == [] and workqueue.exports_in_order(c) == []
        )
    approve(s, c_)
    approve(s, a)
    reject(s, b)
    with workqueue.opened(s) as c:
        assert workqueue.latest_decision(c, b.uid).decision == "reject" and workqueue.latest_decision(c, a.uid).decision == "approve"
        assert [i.id for i in workqueue.approved_unexported(c)] == [a.id, c_.id]  # created_at order, not decision order
        with workqueue.transaction(c):  # export c first, then a: the receipts are listed in seq order
            for it in (c_, a):
                raw_export(c, it.uid, "row-" + it.id, content_code(it))
                c.execute("UPDATE items SET state='EXPORTED', version=version+1 WHERE uid=?", (it.uid,))
        assert [e.item_uid for e in workqueue.exports_in_order(c)] == [c_.uid, a.uid]
        assert [e.seq for e in workqueue.exports_in_order(c)] == sorted(e.seq for e in workqueue.exports_in_order(c))
        assert workqueue.approved_unexported(c) == []
    assert REASON


def test_a_second_export_row_for_one_item_is_refused(tmp_path):
    from intake.content_code import content_code

    s = settings_for_tests(tmp_path)
    it = new_item(s, "a")
    approve(s, it)
    with workqueue.opened(s) as c:
        raw_export(c, it.uid, "row-1", content_code(it))
        with pytest.raises(Exception, match="UNIQUE|already|export needs|append-only"):
            raw_export(c, it.uid, "row-2", content_code(it))


def test_queue_files_state_reports_the_mode(tmp_path):
    s = settings_for_tests(tmp_path)
    assert workqueue.queue_files_state(s) == "absent"
    workqueue.connect(s).close()
    if os.name == "nt":
        assert workqueue.queue_files_state(s) == "n/a (windows)"
    else:
        import stat

        assert workqueue.queue_files_state(s) == "ok"
        assert stat.S_IMODE(workqueue.queue_path(s).stat().st_mode) == 0o600
        workqueue.queue_path(s).chmod(0o644)
        assert workqueue.queue_files_state(s) == "mode_too_open"


def test_check_prints_the_queue_files_line_and_fails_on_open_modes(tmp_path, monkeypatch, capsys):
    s = settings_for_tests(tmp_path)
    workqueue.connect(s).close()
    monkeypatch.setenv("HADAVIN_LOCAL", str(s.local))
    monkeypatch.setenv("INTAKE_MODEL_BACKEND", "fake")
    rc = cli.main(["check"])
    out = capsys.readouterr().out
    assert "queue_files: " in out and rc == 0


def _is_sqlite_connect(node) -> bool:
    f = node.func
    return isinstance(f, ast.Attribute) and f.attr == "connect" and isinstance(f.value, ast.Name) and f.value.id in ("sqlite3", "sqlite")


def test_the_queue_is_opened_only_through_connect():
    """``sqlite3.connect`` appears only in workqueue.py (the queue) and budget.py (the spend ledger, WP1): a connection opened elsewhere would lack
    ``recursive_triggers``, the busy timeout and the trigger check."""
    from pathlib import Path

    src = Path(__file__).resolve().parents[1] / "src" / "intake"
    allowed = {"workqueue.py", "budget.py", "fake_ledger.py"}  # fake_ledger: the existing in-memory order-flow ledger, a different database
    bad = []
    for f in sorted(src.rglob("*.py")):
        if f.name in allowed or "core_copy" in f.parts:
            continue
        for node in ast.walk(ast.parse(f.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call) and _is_sqlite_connect(node):
                bad.append((f.name, node.lineno))
            if isinstance(node, ast.ImportFrom) and node.module == "sqlite3" and any(a.name == "connect" for a in node.names):
                bad.append((f.name, node.lineno))
    assert not bad, bad


def test_the_scan_finds_a_connect_call_in_a_snippet():
    import ast

    assert any(
        isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "connect"
        for n in ast.walk(ast.parse("import sqlite3\nsqlite3.connect('x')"))
    )


# ---- transaction behaviour, accessor order, file modes -------------------------------------------------------------------------------------------
class _FlakyCommit:
    """A connection whose COMMIT fails (disk error), to prove the transaction is rolled back and the connection is usable again."""

    def __init__(self, conn):
        self.conn = conn

    @property
    def in_transaction(self):
        return self.conn.in_transaction

    def execute(self, sql, *a):
        if sql == "COMMIT":
            raise sqlite3.OperationalError("disk I/O error")
        return self.conn.execute(sql, *a)


def test_transaction_rolls_back_on_an_exception_and_on_a_failing_commit(tmp_path):
    s = settings_for_tests(tmp_path)
    with workqueue.opened(s) as c:
        with pytest.raises(RuntimeError):
            with workqueue.transaction(c):
                raw_insert(c, "x1", "RECEIVED")
                raise RuntimeError("boom")
        assert not c.in_transaction and c.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 0
        with pytest.raises(sqlite3.OperationalError, match="disk I/O"):
            with workqueue.transaction(_FlakyCommit(c)):
                raw_insert(c, "x2", "RECEIVED")
        assert not c.in_transaction and c.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 0
        with workqueue.transaction(c):  # the connection is usable again
            raw_insert(c, "x3", "RECEIVED")
        assert c.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 1


def test_latest_decision_is_the_highest_seq_not_the_first(tmp_path):
    from queue_helpers import raw_decision, raw_insert

    s = settings_for_tests(tmp_path)
    with workqueue.opened(s) as c:
        drop_triggers(c)
        uid = raw_insert(c, "two", "READY", GOOD_FIELDS)
        raw_decision(c, uid, "approve")
        raw_decision(c, uid, "reject")
        assert workqueue.latest_decision(c, uid).decision == "reject"


def test_queue_files_are_restricted_to_the_owner_on_posix(tmp_path, monkeypatch):
    """The Windows run cannot see mode bits, so the call is checked: with ``os.name`` patched to posix, ``chmod(0o600)`` is made on each queue file."""
    from pathlib import Path

    s = settings_for_tests(tmp_path)
    workqueue.connect(s).close()
    calls = []
    monkeypatch.setattr(Path, "chmod", lambda self, mode: calls.append((self.name, mode)))
    monkeypatch.setattr(workqueue.os, "name", "posix")
    workqueue._restrict_files(s)
    assert ("queue.sqlite3", 0o600) in calls and all(m in (0o600, 0o700) for _, m in calls)


assertive_all(globals())
