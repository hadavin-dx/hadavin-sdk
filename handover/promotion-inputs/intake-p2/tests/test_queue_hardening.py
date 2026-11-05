"""WP4 review round 2: schema version, a decision's savepoint, reserved names, replayed results, unknown stored flags, the cost sum, AST pins (probe calls,
sqlite aliases), directory mode, and row id vectors."""

from __future__ import annotations

import ast
import json
import sqlite3
import unicodedata
from pathlib import Path

import pytest
from queue_helpers import GOOD_FIELDS, REASON, approve, assertive_all, drop_triggers, new_item

from conftest import ROOT, settings_for_tests
from intake import content_code as cc
from intake import decisions, queue_schema, rules, workqueue
from intake.codes import ConfigError, Refused
from intake.content_code import content_code

SRC = ROOT / "src" / "intake"


def refused(fn, *a, **k) -> str:
    with pytest.raises(Refused) as e:
        fn(*a, **k)
    return e.value.code


# ---- M-A: the schema version ---------------------------------------------------------------------------------------------------------------------
def test_a_new_queue_file_carries_the_schema_version(tmp_path):
    with workqueue.opened(settings_for_tests(tmp_path)) as c:
        assert [tuple(r) for r in c.execute("SELECT k, v FROM meta")] == [("schema_version", queue_schema.SCHEMA_VERSION)]


@pytest.mark.parametrize("damage", ["UPDATE meta SET v = '9'", "UPDATE meta SET v = ''", "DELETE FROM meta"])
def test_a_queue_file_with_another_or_no_schema_version_is_refused(damage, tmp_path):
    s = settings_for_tests(tmp_path)
    with workqueue.opened(s) as c:
        drop_triggers(c)
        c.execute(damage)
    with pytest.raises(ConfigError) as e:
        workqueue.connect(s)
    assert e.value.code == "bad_config" and "schema version" in e.value.text


def test_the_version_row_cannot_be_changed_through_the_triggers(tmp_path):
    with workqueue.opened(settings_for_tests(tmp_path)) as c:
        for sql in ("UPDATE meta SET v = '9'", "DELETE FROM meta", "INSERT OR REPLACE INTO meta (k, v) VALUES ('schema_version', '9')"):
            with pytest.raises(sqlite3.IntegrityError, match="append-only"):
                c.execute(sql)


def test_a_missing_version_row_is_not_silently_added_to_an_existing_file(tmp_path):
    s = settings_for_tests(tmp_path)
    with workqueue.opened(s) as c:
        drop_triggers(c)
        c.execute("DELETE FROM meta")
    for _ in range(2):  # twice: the first refusal must not have repaired the file
        with pytest.raises(ConfigError):
            workqueue.connect(s)


# ---- M-B: a refused decision leaves nothing behind, even when the caller commits ------------------------------------------------------------------
def test_a_caller_that_swallows_the_refusal_and_commits_leaves_no_orphan_decision(tmp_path):
    s = settings_for_tests(tmp_path)
    it = new_item(s)
    with workqueue.opened(s) as c:
        with workqueue.transaction(c):  # commits at the end of the block
            try:
                decisions.decide(s, it.id, "approve", "ap-a", None, content_code(it), it.version + 1, conn=c)
            except Refused as e:
                assert e.code == "stale_content"  # swallowed on purpose: a loop over many items would do this
    with workqueue.opened(s) as c:
        assert c.execute("SELECT COUNT(*) FROM decisions").fetchone()[0] == 0
    got = workqueue.get(s, it.id)
    assert got.state == "READY" and got.version == it.version
    assert approve(s, got).decision == "approve"  # and a later, valid approve works


def test_the_savepoint_is_released_after_success_and_after_failure(tmp_path):
    s = settings_for_tests(tmp_path)
    a, b = new_item(s, "a"), new_item(s, "b")
    with workqueue.opened(s) as c, workqueue.transaction(c):
        with pytest.raises(Refused):
            decisions.decide(s, a.id, "approve", "ap-a", None, content_code(a), a.version + 1, conn=c)
        decisions.decide(s, b.id, "approve", "ap-a", None, content_code(b), b.version, conn=c)
        with pytest.raises(sqlite3.OperationalError, match="no such savepoint"):
            c.execute("ROLLBACK TO apply_decision")  # nothing is left open
    assert workqueue.get(s, b.id).state == "APPROVED" and workqueue.get(s, a.id).state == "READY"


# ---- minors --------------------------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("name", ["system", "cli", "SYSTEM", "Cli"])
def test_reserved_names_cannot_decide(name, tmp_path):
    s = settings_for_tests(tmp_path)
    it = new_item(s)
    assert refused(approve, s, it, None, name) == "bad_decision"
    assert workqueue.get(s, it.id).state == "READY"


def test_a_replayed_result_on_a_processed_item_is_refused_and_keeps_the_version(tmp_path):
    s = settings_for_tests(tmp_path)
    it = new_item(s, "a")  # READY
    again = lambda: workqueue.set_result(  # noqa: E731
        s,
        it.uid,
        "READY",
        fields=GOOD_FIELDS,
        flags=[],
        failing_fields=[],
        model_id="model-x",
        tier="read",
        prompt_sha256="p" * 64,
        cost_micro=0,
    )
    assert refused(again) == "state_conflict"
    assert workqueue.get(s, it.id).version == it.version  # an open review form stays valid
    np_ = new_item(s, "b", flags=["D06"])
    assert (
        refused(
            workqueue.set_result,
            s, np_.uid, "NEEDS_PERSON", fields=GOOD_FIELDS, flags=["D06"], failing_fields=[], model_id="model-x", tier="read", prompt_sha256="p" * 64, cost_micro=0,
        )
        == "state_conflict"
    )  # fmt: skip
    assert workqueue.get(s, np_.id).version == np_.version


def test_an_unknown_stored_flag_can_be_rejected_never_approved_and_never_crashes(tmp_path):
    s = settings_for_tests(tmp_path)
    it = new_item(s, "u", flags=["D06"])
    with workqueue.opened(s) as c:
        drop_triggers(c, "intake_b_immutable")
        c.execute("UPDATE items SET flags_json = ? WHERE uid = ?", ('["ZZ9"]', it.uid))
    odd = workqueue.get(s, it.id)
    assert odd.flags == ("ZZ9",)
    assert isinstance(content_code(odd), str)
    assert refused(approve, s, odd, REASON) == "not_approvable"
    assert decisions.decide(s, odd.id, "reject", "ap-a", REASON, content_code(odd), odd.version).decision == "reject"


def test_sum_cost_micro_adds_every_item_and_follows_a_purge(tmp_path):
    s = settings_for_tests(tmp_path)
    assert workqueue.sum_cost_micro(s) == 0
    a, _ = new_item(s, "a", cost=5), new_item(s, "b", cost=7)
    assert workqueue.sum_cost_micro(s) == 12
    workqueue.purge(s, a.id)
    assert workqueue.sum_cost_micro(s) == 7


def test_an_existing_intake_folder_with_loose_bits_is_tightened(tmp_path, monkeypatch):
    s = settings_for_tests(tmp_path)
    calls = []
    monkeypatch.setattr(Path, "chmod", lambda self, mode: calls.append((self.name, mode)))
    monkeypatch.setattr(workqueue.os, "name", "posix")
    workqueue._restrict_files(s)  # on Windows the stat reports loose bits, as a POSIX folder at 0755 would
    assert (s.intake_home.name, 0o700) in calls


# ---- AST pins ------------------------------------------------------------------------------------------------------------------------------------
_PROBE_ATTRS = {"exists", "stat", "lstat", "is_file", "is_dir", "samefile"}
_PROBE_FUNCTIONS = {"_precreate", "queue_files_state", "_restrict_files"}


def _enclosing(tree: ast.AST) -> dict[ast.AST, str]:
    out: dict[ast.AST, str] = {}
    for fn in ast.walk(tree):
        if isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef):
            for n in ast.walk(fn):
                out[n] = fn.name
    return out


def probe_findings(source: str) -> list[str]:
    """Every path probe (exists, stat, ..., os.open) must sit in one of the three allowed functions and be rooted in ``queue_path(s)`` or
    ``s.intake_home`` (directly, through a name assigned from them, or the parameter that is always called with ``queue_path(s)``)."""
    tree = ast.parse(source)
    where = _enclosing(tree)
    rooted_names = {"path"}  # _precreate(path): checked below against its call sites
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            text = ast.unparse(n.value)
            if "s.intake_home" in text or "queue_path(s)" in text:
                rooted_names.add(n.targets[0].id)
    bad = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        is_probe = isinstance(f, ast.Attribute) and (f.attr in _PROBE_ATTRS or (f.attr == "open" and ast.unparse(f.value) == "os"))
        if not is_probe:
            continue
        recv = n.args[0] if f.attr == "open" else f.value
        text = ast.unparse(recv)
        rooted = "queue_path(s)" in text or "s.intake_home" in text or (isinstance(recv, ast.Name) and recv.id in rooted_names)
        if where.get(n) not in _PROBE_FUNCTIONS or not rooted:
            bad.append(f"line {n.lineno}: {ast.unparse(n)[:60]}")
    for n in ast.walk(tree):  # the parameter of _precreate is trusted only because every call passes queue_path(s)
        if (
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id == "_precreate"
            and [ast.unparse(a) for a in n.args] != ["queue_path(s)"]
        ):
            bad.append(f"line {n.lineno}: _precreate called with something else")
    return bad


def test_workqueue_probes_paths_only_in_the_three_allowed_functions_on_its_own_files():
    assert probe_findings((SRC / "workqueue.py").read_text(encoding="utf-8")) == []


@pytest.mark.parametrize(
    "snippet",
    [
        "def f(s):\n    return Path('x').exists()",  # a probe of an unrelated path
        "def _precreate(path):\n    pass\ndef g(s):\n    _precreate(Path('x'))",  # a call site with another argument
        "def helper(s):\n    return queue_path(s).exists()",  # right path, wrong function
        "def queue_files_state(s):\n    return open_this.stat()",  # allowed function, unrelated receiver
        "def _precreate(path):\n    os.open(other, 0)",
    ],
)
def test_the_probe_pin_catches_a_probe_outside_its_allowance(snippet):
    assert probe_findings(snippet)


def sqlite_openers(source: str) -> list[int]:
    """Line numbers of calls that open a sqlite connection by any spelling: ``sqlite3.connect``, ``sqlite3.Connection``, through ``import sqlite3 as x``,
    or through ``from sqlite3 import connect / Connection [as y]``."""
    tree = ast.parse(source)
    modules, names = set(), set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            modules |= {a.asname or a.name for a in n.names if a.name == "sqlite3"}
        if isinstance(n, ast.ImportFrom) and n.module == "sqlite3":
            names |= {a.asname or a.name for a in n.names if a.name in ("connect", "Connection")}
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            if (
                isinstance(f, ast.Attribute)
                and f.attr in ("connect", "Connection")
                and isinstance(f.value, ast.Name)
                and f.value.id in modules
            ):
                out.append(n.lineno)
            if isinstance(f, ast.Name) and f.id in names:
                out.append(n.lineno)
    return out


@pytest.mark.parametrize(
    "snippet",
    [
        "import sqlite3\nsqlite3.connect('x')",
        "import sqlite3 as sq\nsq.connect('x')",
        "import sqlite3\nsqlite3.Connection('x')",
        "from sqlite3 import connect\nconnect('x')",
        "from sqlite3 import Connection as C\nC('x')",
    ],
)
def test_the_opener_scan_sees_every_spelling(snippet):
    assert sqlite_openers(snippet)


def test_the_opener_scan_ignores_other_connect_calls():
    assert not sqlite_openers("import sqlite3\nworkqueue.connect(s)\nsock.connect(a)")


def test_only_workqueue_and_the_spend_ledger_open_sqlite_connections():
    allowed = {"workqueue.py", "budget.py", "fake_ledger.py"}  # fake_ledger: the existing in-memory order-flow ledger
    bad = [
        (f.name, n)
        for f in sorted(SRC.rglob("*.py"))
        if f.name not in allowed and "core_copy" not in f.parts
        for n in sqlite_openers(f.read_text(encoding="utf-8"))
    ]
    assert not bad, bad


# ---- row id vectors ------------------------------------------------------------------------------------------------------------------------------
VECTORS = json.loads((ROOT / "tests" / "fixtures" / "content_code" / "row_id_vectors.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("v", VECTORS["vectors"], ids=[v["name"] for v in VECTORS["vectors"]])
def test_row_id_matches_the_pinned_vector(v):
    got = cc.row_id(v["tenant_id"], v["supplier_name"], v["invoice_no"], rules.load_policy())
    assert got == v["row_id"], (
        f"row id changed (vectors computed with Unicode {VECTORS['unicode_version']}, this Python has {unicodedata.unidata_version}); "
        "a change in the fold would split or merge exported invoices"
    )


def test_the_look_alike_vectors_agree_with_each_other_where_they_should():
    by = {v["name"]: v["row_id"] for v in VECTORS["vectors"]}
    for same in (
        "revision suffix",
        "spaces and case",
        "fullwidth invoice",
        "cyrillic I first",
        "greek iota",
        "zero-width space",
        "cyrillic A in supplier",
    ):
        assert by[same] == by["ascii"], same
    assert by["other tenant"] != by["ascii"] and by["cjk invoice (still not ASCII after the fold)"] != by["ascii"]


assertive_all(globals())
