"""WP6 kickoff package 6k (brief-v3 15.1): the shared names, the 17 codes, the code-to-status map, the plain-words table and the additive edits to
closed files (read-only queue connection, ``conn=`` readers, read-only spend readers, ``known_sources``, ``BLANK_LOOKALIKES``, ``read_log_level``,
``preview_rows(conn=)``). Each test is written to fail against an implementation that skips its check (the mutants in ``tools/mutate_src.py --group WP6``)."""

from __future__ import annotations

import ast
import importlib.util
import inspect
import random
import re
import sqlite3
import string
import threading
import time

import pytest
from model_support import live_settings
from queue_helpers import GOOD_FIELDS, drop_triggers, new_item, reject, sha
from test_codes import SRC, used_codes
from test_exporter import approved, fields

from conftest import ROOT, settings_for_tests
from intake import access, budget, codes, decisions, exporter, inbox, review_page, routes, service, settings, workqueue
from intake.codes import ConfigError

pytestmark = pytest.mark.filterwarnings("ignore")

NEW_CODES = (
    "unauthorized login_failed bad_host bad_origin csrf_failed role_denied token_not_allowed bad_request bad_query length_required body_too_large "
    "method_not_allowed not_a_file serve_running port_in_use internal too_many_attempts"
).split()
BANNED = re.compile(r"accuracy|robust|production ready|time saved|hard cap|real ceiling|only made-up files reach", re.I)


# ---- codes, status map, plain words ---------------------------------------------------------------------------------------------------------------
def test_new_codes_listed():
    assert len(NEW_CODES) == 17 and len(set(NEW_CODES)) == 17
    assert [c for c in NEW_CODES if c not in codes.SERVICE_CODES] == []
    assert set(NEW_CODES) <= codes.CODES


def test_status_map_closed():
    assert all(c in codes.CODES for c in service.STATUS), [c for c in service.STATUS if c not in codes.CODES]
    assert all(c in review_page.ERROR_TEXT or c == "budget_halted" for c in service.STATUS)
    assert all(isinstance(v, int) and 400 <= v <= 599 for v in service.STATUS.values())
    # the three sets are disjoint except codes both RAISED by the queue and RETURNED by the exporter
    both = {"db_busy", "state_conflict", "not_approvable"}
    status, internal, outcome = set(service.STATUS), set(service.INTERNAL_OK), set(service.OUTCOME_CODES)
    assert (status & internal) == set() and (internal & outcome) == set() and (status & outcome) == both
    assert service.STATUS["internal"] == 500 and service.STATUS["budget_halted"] == 503 and service.STATUS["bad_host"] == 421
    assert {c for c, v in service.STATUS.items() if v == 500} == {
        "internal"
    }  # every unlisted code answers 500 through the fallback, not a row


def test_error_text_complete_and_clean():
    for c, t in review_page.ERROR_TEXT.items():
        assert isinstance(t, str) and t.strip() and t.isascii() and "\r" not in t and "\n" not in t, c
        assert not BANNED.search(t), c
        assert "<" not in t and "{" not in t.replace("{reason_min_chars}", "").replace("{reason_max_chars}", ""), c
    for c in service.STATUS:  # every code the service can answer has a sentence; a halted spend counter is shown as `halted`
        assert c in review_page.ERROR_TEXT or c == "budget_halted", c
    assert "halted" in review_page.ERROR_TEXT and "internal" in review_page.ERROR_TEXT
    assert set(inbox.REFUSAL_CODES) <= set(review_page.ERROR_TEXT)
    assert review_page.ERROR_TEXT["invalid_reason"].format(reason_min_chars=10, reason_max_chars=200)  # the two numbers come from config


def _raised_codes() -> dict[str, set[str]]:
    """Every code literal raised as Refused, ConfigError or SecretError in the modules of brief-v3 13 (the scanner of ``tests/test_codes.py``)."""
    mods = "access inbox review_page service decisions workqueue budget settings secret_store model extract pipeline invoicecheck exporter".split()
    out: dict[str, set[str]] = {}
    for m in mods:
        tree_src = (SRC / f"{m}.py").read_text(encoding="utf-8")
        for node in ast.walk(ast.parse(tree_src)):
            if isinstance(node, ast.Call):
                fn = node.func
                name = fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else ""
                if (
                    name in codes.CODE_RAISERS
                    and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)
                ):
                    out.setdefault(node.args[0].value, set()).add(m)
    return out


def test_every_raised_code_has_a_place_at_kickoff():
    """The reverse check (m2): a code raised anywhere must be in STATUS, INTERNAL_OK, OUTCOME_CODES, the translation list or the scan refusals. A new
    code anywhere fails this until someone places it. (6d's ``every_raisable_code_mapped`` re-runs it at the integration head.)"""
    translated = set(codes.SECRET_CODES)  # every SecretError code is shown as `not_configured`
    placed = set(service.STATUS) | service.INTERNAL_OK | service.OUTCOME_CODES | translated | set(inbox.REFUSAL_CODES)
    exporter_codes = set(exporter.RESULT_TEXT) | set(exporter.FILE_TEXT)
    assert exporter_codes - {"not_found"} <= placed, exporter_codes - placed
    raised = _raised_codes()
    unplaced = {c: sorted(m) for c, m in raised.items() if c not in placed}
    assert unplaced == {}, unplaced
    assert used_codes("raise Refused('zz_new_code')") == [("zz_new_code", 1)]  # the scanner still sees a literal


# ---- routes ---------------------------------------------------------------------------------------------------------------------------------------
def _row(**kw) -> routes.Route:
    base = {
        "name": "x",
        "method": "GET",
        "path": "/x",
        "roles": frozenset({routes.APPROVER}),
        "app": "work",
        "family": "session",
        "writes": False,
        "fields": (),
        "query": (),
    }
    return routes.Route(**{**base, **kw})


def test_routes_import_validation():
    routes.validate(routes.ROUTE_TABLE)
    good = _row()
    routes.validate((good,))
    bad = {
        "duplicate name": (good, good),
        "dash row that writes": (_row(app="dash", writes=True, method="POST", fields=("csrf",)),),
        "token family on the work listener": (_row(family="token", roles=frozenset({routes.TOKEN_HOLDER})),),
        "token family with a session role": (_row(family="token", app="token", roles=frozenset({routes.APPROVER})),),
        "token listener row of another family": (_row(app="token", family="session"),),
        "login family with a role": (_row(family="login", roles=frozenset({routes.APPROVER})),),
        "session POST without csrf": (_row(method="POST", writes=True, fields=("login",)),),
        "unknown role": (_row(roles=frozenset({"admin"})),),
        "unknown app": (_row(app="mail"),),
        "unknown family": (_row(family="cookie"),),
        "anyone on a session route": (_row(roles=frozenset({routes.ANYONE})),),
        "path without a slash": (_row(path="x"),),
        "a second placeholder": (_row(path="/a/{id}/{other}"),),
        "unsupported method": (_row(method="DELETE"),),
    }
    for why, table in bad.items():
        with pytest.raises(ValueError):
            routes.validate(table)
            raise AssertionError(why)  # reaches here only if validate accepted a bad table: the failure names the case
    routes.validate((_row(roles=frozenset()),))  # an EMPTY role set is allowed in the table: it means nobody (default deny)


def test_route_table_is_the_brief_table():
    got = [(r.name, r.method, r.path, r.app, r.family, sorted(r.roles), r.writes, r.fields, r.query) for r in routes.ROUTE_TABLE]
    assert [g[0] for g in got] == [
        "login",
        "login_post",
        "home",
        "item",
        "decide",
        "export",
        "export_run",
        "overview",
        "logout",
        "healthz",
        "scan",
    ]
    by = {g[0]: g for g in got}
    assert by["decide"][8] == () and by["decide"][7] == ("csrf", "decision", "reason", "content_code", "version")
    assert (
        by["home"][8] == ("sort", "dir", "state")
        and by["export_run"][7] == ("csrf", "passphrase")
        and by["login_post"][7] == ("csrf", "login", "passphrase")
    )
    assert by["scan"][3:6] == ("token", "token", ["token_holder"]) and by["scan"][7] == () and by["healthz"][3] == "token"
    assert (
        routes.APPS == ("work", "dash", "token")
        and routes.FAMILIES == ("login", "session", "token")
        and routes.ROLES == ("approver", "viewer", "dash")
    )
    for r in routes.ROUTE_TABLE:
        assert r.writes == (r.method == "POST")
        assert routes.route(r.name) is r
    with pytest.raises(ValueError):
        routes.route("nope")


def test_match_is_exact_and_per_listener():
    iid = "inv-a-1a2b3c4d"
    assert routes.match("work", "GET", "/")[0].name == "home"
    assert routes.match("work", "GET", f"/item/{iid}") == (routes.route("item"), {"id": iid})
    assert routes.match("work", "POST", f"/item/{iid}/decide")[1] == {"id": iid}
    assert routes.match("token", "POST", "/events/scan")[0].name == "scan"
    assert routes.match("work", "POST", "/events/scan") is None  # a path of another listener is a 404 here
    assert routes.match("token", "GET", "/") is None and routes.match("dash", "GET", "/") is None
    assert routes.match("work", "POST", "/") == "method" and routes.match("work", "GET", "/logout") == "method"
    assert routes.match("work", "GET", "/export")[0].name == "export" and routes.match("work", "POST", "/export")[0].name == "export_run"
    for path in (
        "/item/%69nv-a-1a2b3c4d",
        "/%2e",
        "/item/x",
        "/item/inv-a-1A2B3C4D",
        f"/item/{iid}/",
        "/login/",
        "//",
        "/item/inv/a-1a2b3c4d",
        "",
    ):
        assert routes.match("work", "GET", path) is None, path


def test_allowed_is_default_deny():
    assert routes.allowed("GET", "/", routes.APPROVER) and routes.allowed("GET", "/", routes.VIEWER)
    assert not routes.allowed("GET", "/", None) and not routes.allowed("GET", "/", "admin") and not routes.allowed("GET", "/", 1)
    assert routes.allowed("GET", "/login", None)  # open row
    assert not routes.allowed("GET", "/nope", routes.APPROVER) and not routes.allowed("DELETE", "/", routes.APPROVER)
    assert not routes.allowed("POST", "/export", routes.VIEWER) and routes.allowed("POST", "/export", routes.APPROVER)
    assert not routes.allowed("GET", "/healthz", routes.TOKEN_HOLDER) and not routes.allowed(
        "POST", "/events/scan", routes.APPROVER
    )  # not on the work listener


def test_item_id_re_matches_workqueue():
    rnd = random.Random(20261104)
    alphabet = string.ascii_letters + string.digits + "._-"
    for _ in range(200):
        n = rnd.randint(1, 128)
        stem = rnd.choice(string.ascii_letters + string.digits) + "".join(rnd.choice(alphabet) for _ in range(n - 1))
        iid = workqueue.item_id(stem, sha(stem))
        assert re.fullmatch(routes.ITEM_ID_RE, iid), iid
    for bad in (
        "",
        "-1a2b3c4d",
        "a-1a2b3c4",
        "a-1a2b3c4d5",
        "a-1A2B3C4D",
        "a b-1a2b3c4d",
        "a/b-1a2b3c4d",
        "a" * 129 + "-1a2b3c4d",
        "é-1a2b3c4d",
    ):
        assert not re.fullmatch(routes.ITEM_ID_RE, bad), bad
    cfg = settings.read_config()["service"]["name_regex"]
    assert cfg == "^" + routes.STEM_RE + "$"  # `serve` refuses to start when these differ (brief-v3 12.1 step 1b)


def _url_names(source: str) -> list[str]:
    return [
        n.args[0].value
        for n in ast.walk(ast.parse(source))
        if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "url" and n.args and isinstance(n.args[0], ast.Constant)
    ]


def test_url_name_scan_sees_calls():
    assert _url_names("a = url('home')\nb = url('x', id=1)\nc = other('y')") == ["home", "x"]


def test_ui_names_still_resolve():
    """Every ``ui.url(name)`` call in ``ui.py`` names a row of the table (``ui.py`` comes from the portal branch; until it is merged there is none)."""
    spec = importlib.util.find_spec("intake.ui")
    if spec is None or spec.origin is None:
        pytest.skip("ui.py is not on this branch yet (portal P1 merge, brief-v3 W-0)")
    names = _url_names(open(spec.origin, encoding="utf-8").read())
    assert names and [n for n in names if n not in {r.name for r in routes.ROUTE_TABLE}] == []


# ---- skeleton names (so the sub-builders cannot drift) ---------------------------------------------------------------------------------------------
def test_skeleton_names_and_signatures():
    want = {
        access: "Clocks Stamp age_over Login LOGINS Session Denied NotConfigured Throttled equal_secret match_login check_step_up Throttle SessionStore "
        "PreSessions cookie_value set_cookie clear_cookie host_ok origin_ok csrf_ok allowed require_role".split(),
        inbox: "Refusal NewItem ScanResult REFUSAL_CODES inbox_dir read_plain_file scan_deadline_s Scanner".split(),
        review_page: "ERROR_TEXT SpendReading session_view banners queue_view invoice_view export_view".split(),
        service: "HOST_TOKEN HOST_WORK HOST_DASH PRODUCT_HOSTS Limits PRODUCT_LIMITS STATUS INTERNAL_OK OUTCOME_CODES CSP_JSON Request Reply HANDLERS "
        "csp_for IntakeServer Handler send log_line scan_running serve".split(),
    }
    for mod, names in want.items():
        assert [n for n in names if not hasattr(mod, n)] == [], (mod.__name__, names)
    assert list(inspect.signature(access.SessionStore.get).parameters) == ["self", "sid", "touch"]
    assert inspect.signature(access.SessionStore.get).parameters["touch"].kind is inspect.Parameter.KEYWORD_ONLY
    assert list(inspect.signature(inbox.read_plain_file).parameters) == ["path", "cap", "dir_fd"]
    assert list(inspect.signature(service.serve).parameters) == ["s", "hosts", "limits"]
    assert list(inspect.signature(access.origin_ok).parameters) == ["origin_values", "sec_fetch_site", "port", "work_host"]
    assert (service.HOST_TOKEN, service.HOST_WORK, service.HOST_DASH) == ("127.0.0.1", "127.0.0.11", "127.0.0.12")
    assert [access.LIMIT_SESSION_IDLE_S, access.LIMIT_SESSION_ABS_S, access.LIMIT_PRE_SESSIONS, access.LIMIT_PRE_SESSION_S] == [
        1800,
        28800,
        64,
        600,
    ]
    assert service.PRODUCT_LIMITS.scan_s is None and service.PRODUCT_LIMITS.read_s == 15 and service.PRODUCT_LIMITS.conn_work == 16
    assert len(access.LOGINS) == 1 and (access.LOGINS[0].name, access.LOGINS[0].role) == ("ap-a", "approver")
    assert access.Denied("role_denied").code == "role_denied"
    assert "sid" not in repr(access.Session("SECRETSID", "ap-a", "approver", "SECRETCSRF", access.Stamp(0, 0), access.Stamp(0, 0)))
    assert "SECRETCSRF" not in repr(access.Session("SECRETSID", "ap-a", "approver", "SECRETCSRF", access.Stamp(0, 0), access.Stamp(0, 0)))
    assert dict(service.HANDLERS) == {}  # 6d fills it


def test_skeleton_bodies_are_stubs_until_their_package():
    with pytest.raises(NotImplementedError):
        access.equal_secret("a", "a")
    with pytest.raises(NotImplementedError):
        service.csp_for("work", routes.route("home"))


def test_cli_serve_and_trace_are_stubs(tmp_path, monkeypatch, capsys):
    from intake import cli

    settings_for_tests(tmp_path)
    monkeypatch.setenv("HADAVIN_LOCAL", str(tmp_path / "local"))
    assert cli.main(["serve"]) == 3
    err = capsys.readouterr().err
    assert "bad_config" in err and "not built" in err and "Traceback" not in err
    assert cli.main(["trace", "inv-a-1a2b3c4d"]) == 3
    assert "not built" in capsys.readouterr().err
    assert cli.main(["trace", "inv-a-1a2b3c4d", "--show-masked-request"]) == 3


# ---- the additive edits to closed files -----------------------------------------------------------------------------------------------------------
def _queue(tmp_path, n=2):
    s = settings_for_tests(tmp_path)
    items = [new_item(s, f"inv{i}") for i in range(n)]
    return s, items


def test_connect_readonly_cannot_write(tmp_path):
    s, items = _queue(tmp_path)
    conn = workqueue.connect_readonly(s)
    try:
        assert conn.execute("SELECT count(*) FROM items").fetchone()[0] == 2
        for sql in (
            "INSERT INTO meta (k, v) VALUES ('x', 'y')",
            "UPDATE items SET state = 'REJECTED'",
            "DELETE FROM items",
            "CREATE TABLE zzz (a)",
            "DROP TABLE items",
            "PRAGMA user_version = 7",
            "PRAGMA journal_mode = DELETE",
        ):
            with pytest.raises(sqlite3.Error):
                conn.execute(sql)
        conn.execute("BEGIN IMMEDIATE")  # accepted by SQLite on a read-only connection, but nothing can be written inside it
        with pytest.raises(sqlite3.Error):
            conn.execute("UPDATE items SET state = state")
        conn.execute("ROLLBACK")
    finally:
        conn.close()
    with workqueue.opened(s) as w:  # nothing changed
        assert w.execute("SELECT count(*) FROM items").fetchone()[0] == 2
        assert w.execute("PRAGMA user_version").fetchone()[0] == 0
        assert str(w.execute("PRAGMA journal_mode").fetchone()[0]).lower() == "wal"
    # a version mismatch is `bad_config` (the file is not trusted)
    with workqueue.opened(s) as w:
        drop_triggers(w)
        w.execute("UPDATE meta SET v = '9' WHERE k = 'schema_version'")
    with pytest.raises(ConfigError) as ei:
        workqueue.connect_readonly(s)
    assert ei.value.code == "bad_config"


def test_connect_readonly_refuses_non_wal(tmp_path):
    s, _ = _queue(tmp_path, 1)
    w = workqueue.connect(s)
    w.execute("PRAGMA journal_mode=DELETE")
    w.close()
    with pytest.raises(ConfigError) as ei:
        workqueue.connect_readonly(s)
    assert ei.value.code == "bad_config" and "WAL" in ei.value.text
    workqueue.connect(s).close()  # a normal open puts the file back to WAL
    workqueue.connect_readonly(s).close()


def test_connect_readonly_on_wal_queue(tmp_path):
    s, items = _queue(tmp_path)
    writer = workqueue.connect(s)
    try:
        writer.execute("BEGIN IMMEDIATE")  # another connection holds the write lock
        writer.execute("UPDATE items SET state = state")  # a write is pending in the transaction
        t0 = time.monotonic()
        conn = workqueue.connect_readonly(s)
        try:
            assert [i.id for i in workqueue.list_items(s, conn=conn)] == [i.id for i in items]
            assert workqueue.get(s, items[0].id, conn=conn).id == items[0].id
        finally:
            conn.close()
        assert time.monotonic() - t0 < 2  # the reader neither waited for the writer nor timed out
        writer.execute("ROLLBACK")
    finally:
        writer.close()
    # the read-only open works with no other connection open as well (the -wal and -shm files may be gone)
    conn = workqueue.connect_readonly(s)
    conn.close()


def test_connect_readonly_missing_file_creates_nothing(tmp_path):
    s = settings_for_tests(tmp_path)
    before = sorted(p.name for p in s.intake_home.rglob("*"))
    with pytest.raises((OSError, sqlite3.Error)):
        workqueue.connect_readonly(s)
    assert sorted(p.name for p in s.intake_home.rglob("*")) == before and not workqueue.queue_path(s).exists()
    # also when the folder itself is missing
    s2 = settings_for_tests(tmp_path / "other")
    import shutil

    shutil.rmtree(s2.intake_home)
    with pytest.raises((OSError, sqlite3.Error)):
        workqueue.connect_readonly(s2)
    assert not s2.intake_home.exists()


def _no_connect(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("workqueue.connect was called: the reader did not use the connection it was given")

    monkeypatch.setattr(workqueue, "connect", boom)


def test_readers_use_given_conn(tmp_path, monkeypatch):
    s, items = _queue(tmp_path, 3)
    reject(s, items[2])
    ids = [i.id for i in items]
    ro = workqueue.connect_readonly(s)
    try:
        _no_connect(monkeypatch)
        assert [i.id for i in workqueue.list_items(s, conn=ro)] == ids
        assert [i.id for i in workqueue.list_items(s, "REJECTED", conn=ro)] == [ids[2]]
        assert workqueue.get(s, ids[1], conn=ro).id == ids[1] and workqueue.get(s, "nope-00000000", conn=ro) is None
        assert workqueue.unreadable_ids(s, conn=ro) == []
        assert workqueue.known_sources(s, conn=ro) == frozenset(sha(f"inv{i}") for i in range(3))
        # the default (no conn) still opens its own connection: the old behaviour is unchanged
        with pytest.raises(AssertionError):
            workqueue.list_items(s)
        for call in (workqueue.get, workqueue.unreadable_ids, workqueue.known_sources):
            with pytest.raises(AssertionError):
                call(s, ids[0]) if call is workqueue.get else call(s)
    finally:
        ro.close()


def test_list_items_on_readonly_conn(tmp_path):
    s, items = _queue(tmp_path, 3)
    bad = workqueue.insert_received(s, "bad.txt", sha("bad"), "text", s.tenant_id, "bad")
    with workqueue.opened(s) as w:  # break the stored JSON of one row
        drop_triggers(w)
        w.execute("UPDATE items SET flags_json = 'not json' WHERE uid = ?", (bad.uid,))
    ro = workqueue.connect_readonly(s)
    try:
        assert [i.id for i in workqueue.list_items(s, conn=ro)] == [i.id for i in items]  # the damaged row is left out
        assert workqueue.unreadable_ids(s, conn=ro) == [bad.id] == workqueue.unreadable_ids(s)
        assert [i.id for i in workqueue.list_items(s, conn=ro)] == [i.id for i in workqueue.list_items(s)]
    finally:
        ro.close()


def test_known_sources_lists_every_hash(tmp_path):
    s, items = _queue(tmp_path, 3)
    reject(s, items[0])
    approved(s, "appr", fields(invoice_no="A-1"))
    flagged = workqueue.insert_flagged(s, "x.pdf", sha("flagged"), "t", s.tenant_id, "x", "X18")
    got = workqueue.known_sources(s)
    with workqueue.opened(s) as w:
        all_rows = {r[0] for r in w.execute("SELECT source_sha256 FROM items")}
    assert got == frozenset(all_rows) and len(got) == 5 and sha("flagged") in got and isinstance(got, frozenset)
    assert flagged.state == "NEEDS_PERSON"  # rejected, flagged and approved items all count: a duplicate takes no new slot
    empty = settings_for_tests(tmp_path / "empty")
    assert workqueue.known_sources(empty) == frozenset()


def test_preview_rows_on_readonly_conn(tmp_path, monkeypatch):
    s = settings_for_tests(tmp_path)
    ok = approved(s, "okay", fields(invoice_no="=1+1"))
    approved(s, "second", fields(invoice_no="B-2"))
    own = exporter.preview_rows(s)
    ro = workqueue.connect_readonly(s)
    try:
        _no_connect(monkeypatch)
        via = exporter.preview_rows(s, conn=ro)
        assert via == own and len(via) == 2 and {p.item_id for p in via} >= {ok.id}
        assert not exporter.csv_path(s).exists()
        with pytest.raises(AssertionError):
            exporter.preview_rows(s)  # without conn it opens its own, as before
    finally:
        ro.close()
    assert [p.row["invoice_no"] for p in own if p.item_id == ok.id] == ["'=1+1"]


def test_total_settled_readonly_matches_ledger(tmp_path, monkeypatch):
    s = live_settings(tmp_path)
    assert budget.total_settled_readonly(s) == budget.total_settled_micro(s) == 0
    for i in range(3):
        res = budget.reserve(s, "a" * 64, "read", f"body{i}".encode())
        budget.settle(res, (10 + i, 10))
    total = budget.total_settled_micro(s)
    assert total > 0 and budget.total_settled_readonly(s) == total
    monkeypatch.setattr(budget, "BUSY_MS", 50)
    writer = sqlite3.connect(budget.ledger_path(s), isolation_level=None)
    try:
        writer.execute("BEGIN IMMEDIATE")  # a settle in progress holds the write lock: a page read still answers
        assert budget.total_settled_readonly(s) == total
        writer.execute("ROLLBACK")
    finally:
        writer.close()
    held = sqlite3.connect(budget.ledger_path(s), isolation_level=None)
    try:
        held.execute("BEGIN EXCLUSIVE")  # a locked ledger: the reader gives up fast with None, never raises
        t0 = time.monotonic()
        assert budget.total_settled_readonly(s) is None and time.monotonic() - t0 < 3
        held.execute("ROLLBACK")
    finally:
        held.close()
    budget.ledger_path(s).write_bytes(b"this is not a database" * 50)
    assert budget.total_settled_readonly(s) is None  # unreadable
    budget.ledger_path(s).unlink()
    assert budget.total_settled_readonly(s) is None  # missing: and nothing is created
    assert not budget.ledger_path(s).exists()


def test_page_reads_never_block_settle(tmp_path):
    s = live_settings(tmp_path)
    settled: list[int] = []
    errors: list[str] = []
    stop = threading.Event()
    reads = [0]

    def reader():
        for _ in range(200):
            v = budget.total_settled_readonly(s)
            if v is None:
                errors.append("a reader got None while the ledger was healthy")
                return
            reads[0] += 1
            if stop.is_set():
                break

    threads = [threading.Thread(target=reader) for _ in range(8)]
    for t in threads:
        t.start()
    try:
        for i in range(20):
            res = budget.reserve(s, "b" * 64, "read", f"body{i}".encode())
            settled.append(budget.settle(res, (10, 10)))  # `settle_failed` would raise ConfigError here
    finally:
        stop.set()
        for t in threads:
            t.join(timeout=60)
    assert errors == [] and len(settled) == 20 and reads[0] > 0
    assert budget.total_settled_readonly(s) == budget.total_settled_micro(s) == sum(settled)


def test_halt_state_readonly_states(tmp_path, monkeypatch):
    s = live_settings(tmp_path)
    p = budget.ledger_path(s)

    def meta(sql, *a):
        c = sqlite3.connect(p, isolation_level=None)
        try:
            c.execute(sql, a)
        finally:
            c.close()

    assert budget.halt_state_readonly(s) == (False, "")  # a healthy, not halted ledger
    meta("UPDATE meta SET v = '1' WHERE k = 'halted'")
    meta("INSERT INTO meta (k, v) VALUES ('halt_reason', ?) ON CONFLICT(k) DO UPDATE SET v = excluded.v", "estimate too low")
    assert budget.halt_state_readonly(s) == (True, "estimate too low")
    assert budget.halt_state(s) == budget.halt_state_readonly(s)  # the older reader agrees where it is right
    meta("UPDATE meta SET v = '0' WHERE k = 'halted'")
    assert budget.halt_state_readonly(s) == (False, "")
    meta("UPDATE meta SET v = '2' WHERE k = 'halted'")
    assert budget.halt_state_readonly(s) is None  # any other value is unreadable, not "not halted"
    meta("UPDATE meta SET v = '' WHERE k = 'halted'")
    assert budget.halt_state_readonly(s) is None
    meta("DELETE FROM meta WHERE k = 'halted'")
    assert (
        budget.halt_state_readonly(s) is None and budget.halt_state(s)[0] is False
    )  # key absent: `halt_state` says "not halted", this does not
    monkeypatch.setattr(budget, "BUSY_MS", 50)
    held = sqlite3.connect(p, isolation_level=None)
    try:
        held.execute("BEGIN EXCLUSIVE")
        assert budget.halt_state_readonly(s) is None  # locked
        held.execute("ROLLBACK")
    finally:
        held.close()
    p.write_bytes(b"corrupt" * 100)
    assert budget.halt_state_readonly(s) is None  # a database error
    p.unlink()
    assert budget.halt_state_readonly(s) is None and budget.halt_state(s) == (False, "")  # a missing file
    assert not p.exists()


def test_blank_lookalikes_public_alias():
    assert decisions.BLANK_LOOKALIKES is decisions._BLANK_LOOKALIKES  # noqa: SLF001 (the alias must be the same object)
    assert decisions.BLANK_LOOKALIKES == frozenset(chr(c) for c in (0x115F, 0x1160, 0x2800, 0x3164, 0xFFA0))


def test_read_log_level():
    assert settings.read_log_level({}) == "normal" and settings.read_log_level({"INTAKE_LOG": ""}) == "normal"
    assert settings.read_log_level({"INTAKE_LOG": "normal"}) == "normal" and settings.read_log_level({"INTAKE_LOG": "verbose"}) == "verbose"
    for bad in ("debug", "Verbose", "VERBOSE", " verbose", "1", "true", "verbose\n"):
        with pytest.raises(ConfigError) as ei:
            settings.read_log_level({"INTAKE_LOG": bad})
        assert ei.value.code == "bad_config"
    assert settings.read_log_level({"OTHER": "verbose"}) == "normal"  # only the literal key counts


def test_read_log_level_reads_the_process_environment(monkeypatch):
    monkeypatch.setenv("INTAKE_LOG", "verbose")
    assert settings.read_log_level() == "verbose"
    monkeypatch.delenv("INTAKE_LOG")
    assert settings.read_log_level() == "normal"


def test_secret_scope_allows_only_the_literal_log_key():
    import test_secret_scope as t

    assert "INTAKE_LOG" in t.ENV_VAR_KEYS_OK["src/intake/settings.py"]
    src = (ROOT / "src" / "intake" / "settings.py").read_text(encoding="utf-8")
    assert t.scan_capabilities(src, "src/intake/settings.py") == []
    assert t.scan_capabilities(src.replace('"INTAKE_LOG"', '"INTAKE_OTHER"'), "src/intake/settings.py")  # any other name is flagged
    assert GOOD_FIELDS  # (keeps the shared helper import used)
