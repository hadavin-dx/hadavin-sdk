"""Sign-in, sessions, decide and export over real sockets (package 6d, brief-v3 6, 11, 15.5). Security, approval and money paths."""

from __future__ import annotations

import ast
import sqlite3
import threading
import time
from urllib.parse import urlencode

import pytest
from queue_helpers import GOOD_FIELDS, approve, new_item
from service_helpers import (
    NAV,
    FakeScanner,
    build,
    cookie_of,
    csrf_in,
    form_post,
    get,
    login_form,
    make_viewer,
    raw,
    sign_in,
    start_service,
    txt,
)

from conftest import ROOT, fake_secret_values
from intake import access, budget, decisions, exporter, model, review_page, workqueue
from intake.content_code import content_code


@pytest.fixture
def env(tmp_path, monkeypatch):
    e = start_service(tmp_path, monkeypatch)
    yield e
    e.close()


PASS = "pass" + "P" * 30
T = review_page.ERROR_TEXT


def login(env, fields=None, *, cookies=None, extra=None):
    _, pre, tok = login_form(env)
    f = {"csrf": tok, "login": "ap-a", "passphrase": PASS}
    f.update(fields or {})
    return form_post(env, "/login", f, cookies=f"{access.COOKIE_PRE}={pre}" if cookies is None else cookies, extra=extra)


# ---- sign-in ---------------------------------------------------------------------------------------------------------------------------------
def test_login_success_sets_cookie_and_redirects(env):
    r = login(env)
    assert r.status == 303 and r.h("Location") == ["/"]
    sess = [v for v in r.h("Set-Cookie") if v.startswith(access.COOKIE_SESSION + "=")]
    assert (
        len(sess) == 1
        and sess[0].endswith("; Secure; HttpOnly; SameSite=Strict; Path=/")
        and "Domain" not in sess[0]
        and "Max-Age" not in sess[0]
    )
    assert any(v.startswith(access.COOKIE_PRE + "=;") and "Max-Age=0" in v for v in r.h("Set-Cookie"))
    assert not any("Clear-Site-Data" in k for k, _ in r.headers)
    assert (
        get(
            env,
            "work",
            "/",
            {"Cookie": cookie_of(r, access.COOKIE_SESSION) and f"{access.COOKIE_SESSION}={cookie_of(r, access.COOKIE_SESSION)}"},
        ).status
        == 200
    )


def test_wrong_passphrase_refused(env):
    r = login(env, {"passphrase": "wrong-pass-xyz"})
    assert r.status == 401 and T["login_failed"] in r.text
    assert cookie_of(r, access.COOKIE_SESSION) is None  # login_failure_keeps_no_session
    assert cookie_of(r, access.COOKIE_PRE)  # the 401 page carries a fresh pre-session
    assert "wrong-pass-xyz" not in r.text
    assert login(env, {"login": "system"}).status == 401 and login(env, {"login": "nobody"}).status == 401
    for name in ("system", "nobody"):  # no name oracle: the same sentence for a reserved name and an unknown one
        assert T["login_failed"] in login(env, {"login": name}).text


def test_csrf_required(env):
    cookie, csrf = sign_in(env)
    for fields in ({"csrf": "wrong"}, {"csrf": ""}):
        r = form_post(env, "/logout", fields, cookies=cookie)
        assert r.status == 403 and T["csrf_failed"] in r.text
    assert get(env, "work", "/", {"Cookie": cookie}).status == 200  # a refused logout did not end the session
    for path, fields in (
        ("/export", {"csrf": "x", "passphrase": PASS}),
        ("/item/inv-a-1a2b3c4d/decide", {"csrf": "x", "decision": "reject", "reason": "", "content_code": "0" * 64, "version": "1"}),
    ):
        assert form_post(env, path, fields, cookies=cookie).status == 403


def test_login_csrf_required(env):
    _, pre, tok = login_form(env)
    other = access.PreSessions().issue()
    for cookies, token in (
        ("", tok),
        (f"{access.COOKIE_PRE}={pre}", ""),
        (f"{access.COOKIE_PRE}={pre}", other[1]),
        (f"{access.COOKIE_PRE}={other[0]}", tok),
    ):
        r = form_post(env, "/login", {"csrf": token, "login": "ap-a", "passphrase": PASS}, cookies=cookies)
        assert r.status == 403 and T["csrf_failed"] in r.text and cookie_of(r, access.COOKIE_SESSION) is None
        assert csrf_in(r) and cookie_of(r, access.COOKIE_PRE)  # and a fresh form
        _, pre, tok = login_form(env)


def test_login_retry_after_failure_works(env):
    r = login(env, {"passphrase": "wrong"})
    assert r.status == 401
    pre, tok = cookie_of(r, access.COOKIE_PRE), csrf_in(r)
    r2 = form_post(env, "/login", {"csrf": tok, "login": "ap-a", "passphrase": PASS}, cookies=f"{access.COOKIE_PRE}={pre}")
    assert r2.status == 303 and cookie_of(r2, access.COOKIE_SESSION)


def test_login_two_tabs(env):
    _, pre_a, tok_a = login_form(env)  # tab A loads first
    _, pre_b, tok_b = login_form(env)  # tab B loads last: the browser now holds B's cookie
    r = form_post(env, "/login", {"csrf": tok_b, "login": "ap-a", "passphrase": PASS}, cookies=f"{access.COOKIE_PRE}={pre_b}")
    assert r.status == 303
    r = form_post(
        env, "/login", {"csrf": tok_a, "login": "ap-a", "passphrase": PASS}, cookies=f"{access.COOKIE_PRE}={pre_b}"
    )  # A submits with B's (spent) cookie
    assert r.status == 403 and T["csrf_failed"] in r.text
    r = form_post(
        env,
        "/login",
        {"csrf": csrf_in(r), "login": "ap-a", "passphrase": PASS},
        cookies=f"{access.COOKIE_PRE}={cookie_of(r, access.COOKIE_PRE)}",
    )
    assert r.status == 303  # A signs in on its second submit


def test_login_429_page_has_fresh_form(env):
    last = None
    for _ in range(access.THROTTLE_FAILURES):
        last = login(env, {"passphrase": "wrong"})
        assert last.status == 401
    r = login(env, {"passphrase": PASS})  # right passphrase, but too soon after the failures: not checked, 429, no sleeping server
    assert r.status == 429 and r.first("Retry-After") == "1" and T["too_many_attempts"] in r.text
    assert csrf_in(r) and cookie_of(r, access.COOKIE_PRE) and cookie_of(r, access.COOKIE_SESSION) is None
    time.sleep(1.1)
    r2 = form_post(
        env,
        "/login",
        {"csrf": csrf_in(r), "login": "ap-a", "passphrase": PASS},
        cookies=f"{access.COOKIE_PRE}={cookie_of(r, access.COOKIE_PRE)}",
    )
    assert r2.status == 303


def test_login_csrf_checked_after_throttle(env, monkeypatch):
    for _ in range(access.THROTTLE_FAILURES):
        login(env, {"passphrase": "wrong"})
    calls = []
    real = access.PreSessions.redeem
    monkeypatch.setattr(access.PreSessions, "redeem", lambda self, a, b: calls.append(1) or real(self, a, b))
    assert form_post(env, "/login", {"csrf": "x", "login": "ap-a", "passphrase": "x"}).status == 429
    assert calls == []  # while throttled the pre-session is never touched


def test_login_get_needs_navigation(env):
    pre = env.run.shared.pre
    n0 = len(pre._by_id)
    for h in (
        {"Sec-Fetch-Mode": "no-cors", "Sec-Fetch-Dest": "image"},
        {"Sec-Fetch-Mode": "cors", "Sec-Fetch-Dest": "empty"},
        {"Sec-Fetch-Mode": "navigate", "Sec-Fetch-Dest": "image"},
        {},
    ):
        r = get(env, "work", "/login", h)
        assert r.status == 403 and cookie_of(r, access.COOKIE_PRE) is None
    assert len(pre._by_id) == n0
    assert get(env, "work", "/login", NAV).status == 200 and len(pre._by_id) == n0 + 1
    for site in ("cross-site", "same-site", "bogus", ""):  # a page on another site (a popup flood) must not create pre-sessions
        r = get(env, "work", "/login", {**NAV, "Sec-Fetch-Site": site})
        assert r.status == 403 and cookie_of(r, access.COOKIE_PRE) is None, site
    assert len(pre._by_id) == n0 + 1
    assert get(env, "work", "/login", {**NAV, "Sec-Fetch-Site": "same-origin"}).status == 200  # a redirect inside the app


def test_login_not_configured_503(env):
    from intake import secret_store

    path = secret_store.secrets_path(env.s.local)
    path.write_text(path.read_text().replace("HADAVIN_APPROVER_PASSPHRASE", "OTHER_NAME"), encoding="utf-8")
    r = login(env)
    assert r.status == 503 and T["not_configured"] in r.text and csrf_in(r)


def test_bad_origin_refused(env):
    cookie, csrf = sign_in(env)
    wh, wp = env.work
    good = f"http://{wh}:{wp}"
    cases = [
        {"Origin": "null"},
        {"Origin": "http://evil.example"},
        {"Origin": good + ".evil"},
        {"Origin": "https://" + good[7:]},
        {"Sec-Fetch-Site": "same-site"},
        {"Sec-Fetch-Site": "cross-site"},
        {"Sec-Fetch-Site": "none"},
    ]
    for extra in cases:
        r = form_post(env, "/logout", {"csrf": csrf}, cookies=cookie, extra=extra)
        assert r.status == 403 and T["bad_origin"] in r.text, extra
    base = {"Content-Type": "application/x-www-form-urlencoded", "Cookie": cookie}
    body = urlencode({"csrf": csrf}).encode()
    for h in (
        {"Sec-Fetch-Site": "same-origin"},
        {"Origin": good},
        {"Referer": good + "/", "Sec-Fetch-Site": "same-origin"},
    ):  # missing Origin, missing site, Referer only
        assert raw(env.work, build("POST", "/logout", f"{wh}:{wp}", {**base, **h}, body)).status == 403
    assert get(env, "work", "/", {"Cookie": cookie}).status == 200
    r = login(env, extra={"Origin": "null"})  # the sign-in form is checked too, before the throttle
    assert r.status == 403 and T["bad_origin"] in r.text
    assert len(env.run.shared.throttle._failures) == 0


def test_bad_host_refused(env):
    wh, wp = env.work
    r = raw(env.work, build("POST", "/login", f"localhost:{wp}", {}, b""))
    assert r.status == 421 and T["bad_host"] in r.text


def test_wrong_listener_cookie_and_logout_then_old_cookie_redirects(env):
    cookie, csrf = sign_in(env)
    r = form_post(env, "/logout", {"csrf": csrf}, cookies=cookie)
    assert r.status == 303 and r.h("Location") == ["/login"]
    assert any("Max-Age=0" in v and v.startswith(access.COOKIE_SESSION + "=;") for v in r.h("Set-Cookie"))
    r = get(env, "work", "/", {"Cookie": cookie})
    assert r.status == 303 and r.h("Location") == ["/login"]
    assert form_post(env, "/logout", {"csrf": csrf}, cookies=cookie).status == 401


def test_logout_ends_every_session_of_the_login(env):
    c1, k1 = sign_in(env)
    c2, k2 = sign_in(env)
    assert form_post(env, "/logout", {"csrf": k1}, cookies=c1).status == 303
    assert get(env, "work", "/", {"Cookie": c2}).status == 303


def test_session_rotation_over_http(env):
    old, _ = sign_in(env)
    _, pre, tok = login_form(env)
    r = form_post(env, "/login", {"csrf": tok, "login": "ap-a", "passphrase": PASS}, cookies=f"{access.COOKIE_PRE}={pre}; {old}")
    assert r.status == 303
    assert get(env, "work", "/", {"Cookie": old}).status == 303  # the presented session ended at sign-in
    new = f"{access.COOKIE_SESSION}={cookie_of(r, access.COOKIE_SESSION)}"
    assert new != old and get(env, "work", "/", {"Cookie": new}).status == 200


def test_two_tabs_session_csrf(env):
    cookie, csrf = sign_in(env)
    for _ in range(2):  # the same session token works in every tab
        r = form_post(env, "/export", {"csrf": csrf, "passphrase": "wrong"}, cookies=cookie)
        assert r.status == 401


# ---- decide ----------------------------------------------------------------------------------------------------------------------------------
def decide_fields(item, decision="approve", reason="", **kw):
    f = {"decision": decision, "reason": reason, "content_code": content_code(item), "version": str(item.version)}
    f.update(kw)
    return f


def post_decide(env, cookie, csrf, item_id, fields):
    return form_post(env, f"/item/{item_id}/decide", {"csrf": csrf, **fields}, cookies=cookie)


def decision_rows(env):
    c = workqueue.connect_readonly(env.s)
    try:
        return c.execute("SELECT approver, decision FROM decisions").fetchall()
    finally:
        c.close()


def test_decide_approve_ready_and_records_login_name(env):
    cookie, csrf = sign_in(env)
    it = new_item(env.s, "inv1")
    r = post_decide(env, cookie, csrf, it.id, decide_fields(it))
    assert r.status == 200 and "approved" in r.text.lower()
    assert [tuple(x) for x in decision_rows(env)] == [("ap-a", "approve")]
    assert workqueue.get(env.s, it.id).state == "APPROVED"
    r = post_decide(env, cookie, csrf, it.id, decide_fields(it, approver="mallory"))  # approver_field_refused
    assert r.status == 400
    assert len(decision_rows(env)) == 1


def test_decide_reject_needs_reason(env):
    cookie, csrf = sign_in(env)
    it = new_item(env.s, "inv1")
    r = post_decide(env, cookie, csrf, it.id, decide_fields(it, "reject", ""))
    assert r.status == 409 and txt(env.s, "invalid_reason") in r.text
    r = post_decide(env, cookie, csrf, it.id, decide_fields(it, "reject", "checked against the purchase order"))
    assert r.status == 200 and "rejected" in r.text.lower()
    assert post_decide(env, cookie, csrf, it.id, decide_fields(it, "maybe")).status == 400
    assert post_decide(env, cookie, csrf, "inv-zz-1a2b3c4d", decide_fields(it)).status == 404


def test_decide_race(env, capfd):
    cookie, csrf = sign_in(env)
    it = new_item(env.s, "inv1")
    out = []
    gate = threading.Barrier(8)

    def go():
        gate.wait()
        out.append(post_decide(env, cookie, csrf, it.id, decide_fields(it)).status)

    ts = [threading.Thread(target=go) for _ in range(8)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert sorted(out) == [200] + [409] * 7, out
    log = capfd.readouterr().err
    assert (
        log.count("route=decide status=409") == 7 and log.count("code=already_decided") == 7
    )  # exactly that code, never db_busy or stale_content
    assert len(decision_rows(env)) == 1


@pytest.mark.parametrize("flag", ["D10", "X10", "X18", "L02", "ZZ99"])
def test_decide_direct_post_reject_only(env, flag):
    cookie, csrf = sign_in(env)
    if flag == "ZZ99":  # a flag code the table does not know, stored directly (the API refuses to write one)
        it = new_item(env.s, "inv1", flags=("D06",))
        from queue_helpers import drop_triggers

        with workqueue.opened(env.s) as c:
            drop_triggers(c, "intake_b_immutable")
            c.execute("UPDATE items SET flags_json = ? WHERE uid = ?", ('["ZZ99"]', it.uid))
        it = workqueue.get(env.s, it.id)
    else:
        it = new_item(env.s, "inv1", flags=(flag,))
    r = post_decide(env, cookie, csrf, it.id, decide_fields(it, "approve", "I checked this invoice by hand"))
    assert r.status == 409 and (txt(env.s, "reject_only") in r.text or txt(env.s, "not_approvable") in r.text), r.text
    assert decision_rows(env) == [] and workqueue.get(env.s, it.id).state == "NEEDS_PERSON"


def test_decide_version_unicode_digits(env):
    cookie, csrf = sign_in(env)
    it = new_item(env.s, "inv1")
    for v in (chr(0x661), "99999999999999999999", "-1", "1.0", " 1", "", "1" * 10, "０"):
        assert post_decide(env, cookie, csrf, it.id, decide_fields(it, version=v)).status == 400, repr(v)
    assert decision_rows(env) == []


def test_decide_bad_content_code_shape(env):
    cookie, csrf = sign_in(env)
    it = new_item(env.s, "inv1")
    for c in (content_code(it).upper(), content_code(it)[:63], content_code(it) + "0", "", "g" * 64):
        assert post_decide(env, cookie, csrf, it.id, decide_fields(it, content_code=c)).status == 400, c
    assert decision_rows(env) == []


def test_decide_stale_code_and_version_409(env):
    cookie, csrf = sign_in(env)
    it = new_item(env.s, "inv1")
    r = post_decide(env, cookie, csrf, it.id, decide_fields(it, content_code="0" * 64))
    assert r.status == 409 and txt(env.s, "stale_content") in r.text
    r = post_decide(env, cookie, csrf, it.id, decide_fields(it, version=str(it.version + 5)))
    assert r.status == 409 and txt(env.s, "stale_content") in r.text
    assert decision_rows(env) == []


def test_decide_received_item_409(env):
    cookie, csrf = sign_in(env)
    rec = workqueue.insert_received(env.s, "r.txt", "e" * 64, "text", env.s.tenant_id, "r")
    r = post_decide(
        env, cookie, csrf, rec.id, {"decision": "reject", "reason": "x" * 12, "content_code": "0" * 64, "version": str(rec.version)}
    )
    assert r.status == 409


def test_only_service_decides_ast():
    callers = []
    for p in (ROOT / "src" / "intake").glob("*.py"):
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if (
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute)
                and n.func.attr == "decide"
                and getattr(n.func.value, "id", "").startswith("decisions")
            ):
                callers.append((p.name, n))
    assert {c[0] for c in callers} == {"service.py"}
    (call,) = [n for name, n in callers]
    approver = call.args[3]
    assert (
        isinstance(approver, ast.Attribute)
        and approver.attr == "login_name"
        and isinstance(approver.value, ast.Attribute)
        and approver.value.attr == "session"
    )


def test_only_service_exports_ast():
    for p in (ROOT / "src" / "intake").glob("*.py"):
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
                if n.func.attr in ("export_pending", "export_row", "regenerate_file") and p.name not in ("service.py", "exporter.py"):
                    pytest.fail(f"{p.name}:{n.lineno}")
                if n.func.attr == "record_export":
                    assert p.name in ("exporter.py", "workqueue.py"), p.name


# ---- export ----------------------------------------------------------------------------------------------------------------------------------
def csv_text(env):
    p = exporter.csv_path(env.s)
    return p.read_text(encoding="utf-8") if p.exists() else ""


def export_count(env) -> int:
    c = workqueue.connect_readonly(env.s)
    try:
        return c.execute("SELECT COUNT(*) FROM exports").fetchone()[0]
    finally:
        c.close()


def approved(env, name="inv1", **kw):
    it = new_item(env.s, name, **kw)
    approve(env.s, it)
    return it


def test_export_preview_and_write(env):
    cookie, csrf = sign_in(env)
    it = approved(env)
    assert get(env, "work", "/export", {"Cookie": cookie}).status == 200
    assert csv_text(env) == ""  # the preview writes nothing
    r = form_post(env, "/export", {"csrf": csrf, "passphrase": PASS}, cookies=cookie)
    assert r.status == 200 and exporter.FILE_TEXT["written"] in r.text
    assert export_count(env) == 1 and workqueue.get(env.s, it.id).state == "EXPORTED"
    assert csv_text(env).count("INV-1001") == 1


def test_export_step_up(env):
    cookie, csrf = sign_in(env)
    approved(env)
    r = form_post(env, "/export", {"csrf": csrf, "passphrase": "wrong-pass-xyz"}, cookies=cookie)
    assert r.status == 401 and txt(env.s, "login_failed") in r.text and csv_text(env) == ""
    assert get(env, "work", "/", {"Cookie": cookie}).status == 200  # the session stays
    r = form_post(env, "/export", {"csrf": csrf, "passphrase": PASS}, cookies=cookie)
    assert r.status == 200 and "INV-1001" in csv_text(env)


def test_export_step_up_throttled(env):
    cookie, csrf = sign_in(env)
    approved(env)
    for _ in range(access.THROTTLE_FAILURES):
        assert form_post(env, "/export", {"csrf": csrf, "passphrase": "wrong"}, cookies=cookie).status == 401
    r = form_post(env, "/export", {"csrf": csrf, "passphrase": PASS}, cookies=cookie)
    assert r.status == 429 and r.first("Retry-After") == "1" and csv_text(env) == ""  # the sign-in and the step-up share one throttle
    assert login(env).status == 429


def test_export_race(env):
    cookie, csrf = sign_in(env)
    approved(env)
    out = []
    gate = threading.Barrier(2)

    def go():
        gate.wait()
        r = form_post(env, "/export", {"csrf": csrf, "passphrase": PASS}, cookies=cookie)
        out.append(r)

    ts = [threading.Thread(target=go) for _ in range(2)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert sorted(r.status for r in out) in ([200, 200], [200, 409])  # the second may find the list already written (409 export_changed)
    assert any(exporter.FILE_TEXT["written"] in r.text for r in out)  # one run wrote the file
    assert export_count(env) == 1  # exactly one run exported the row (one receipt)
    assert csv_text(env).count("INV-1001") == 1
    c = workqueue.connect_readonly(env.s)
    try:
        assert c.execute("SELECT COUNT(*) FROM exports").fetchone()[0] == 1
    finally:
        c.close()


def test_export_formula_cells(env):
    cookie, csrf = sign_in(env)
    fields = dict(__import__("queue_helpers").GOOD_FIELDS)
    fields["supplier_name"] = "=HYPERLINK(1)"
    approved(env, fields=fields)
    form_post(env, "/export", {"csrf": csrf, "passphrase": PASS}, cookies=cookie)
    text = csv_text(env)
    assert "'=HYPERLINK(1)" in text and ",=HYPERLINK" not in text and '"=HYPERLINK' not in text


def test_export_kill_switch_shown(env, monkeypatch):
    cookie, csrf = sign_in(env)
    approved(env)
    monkeypatch.setattr(exporter, "_engaged", lambda: True)
    before = csv_text(env)
    r = form_post(env, "/export", {"csrf": csrf, "passphrase": PASS}, cookies=cookie)
    assert (
        r.status == 200 and exporter.FILE_TEXT["kill_switch"] in r.text and csv_text(env) == before
    )  # the long sentence, not a short word
    assert export_count(env) == 0


def test_export_nothing_pending_regenerates(env):
    cookie, csrf = sign_in(env)
    approved(env)
    form_post(env, "/export", {"csrf": csrf, "passphrase": PASS}, cookies=cookie)
    exporter.csv_path(env.s).unlink()
    r = form_post(env, "/export", {"csrf": csrf, "passphrase": PASS}, cookies=cookie)
    assert r.status == 200 and "INV-1001" in csv_text(env)  # the file is rewritten from the receipts


def test_viewer_refused_export_page_and_no_values(env):
    vcookie, vcsrf = make_viewer(env)
    approved(env)
    r = get(env, "work", "/export", {"Cookie": vcookie})
    assert r.status == 403 and "INV-1001" not in r.text and "Acme" not in r.text
    assert form_post(env, "/export", {"csrf": vcsrf, "passphrase": PASS}, cookies=vcookie).status == 403


# ---- GET pages, hygiene ----------------------------------------------------------------------------------------------------------------------
def test_gets_have_no_side_effects(env, monkeypatch):
    cookie, _ = sign_in(env)
    it = new_item(env.s, "inv1")
    spied = []
    for mod, names in (
        (exporter, ("export_pending", "export_row", "regenerate_file")),
        (decisions, ("decide",)),
        (budget, ("reserve", "settle")),
        (workqueue, ("insert_received", "insert_flagged", "set_result", "purge", "apply_decision", "record_export")),
    ):
        for n in names:
            real = getattr(mod, n)
            monkeypatch.setattr(mod, n, lambda *a, _n=n, _r=real, **k: (spied.append(_n), _r(*a, **k))[1])
    before = csv_text(env)
    for p in ("/", f"/item/{it.id}", "/export", "/login"):
        assert get(env, "work", p, {"Cookie": cookie, **NAV}).status == 200, p
    assert spied == [] and csv_text(env) == before


def test_gets_use_readonly_connection_ast():
    src = ast.parse((ROOT / "src" / "intake" / "service.py").read_text(encoding="utf-8"))
    banned = {"connect", "opened", "get", "scope", "transaction"}
    for fn in [
        n for n in ast.walk(src) if isinstance(n, ast.FunctionDef) and n.name in ("h_home", "h_item", "h_export", "h_login", "h_healthz")
    ]:
        for n in ast.walk(fn):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and getattr(n.func.value, "id", "") == "workqueue":
                assert n.func.attr not in banned, (fn.name, n.func.attr)
    rp = ast.parse((ROOT / "src" / "intake" / "review_page.py").read_text(encoding="utf-8"))
    for n in ast.walk(rp):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and getattr(n.func.value, "id", "") == "workqueue":
            assert n.func.attr not in {"connect", "opened"}, n.lineno


def test_get_on_missing_queue_creates_nothing(env):
    # the queue file exists after `serve` started; remove it so a GET that opened a write-capable connection would recreate it
    cookie, _ = sign_in(env)
    for p in env.s.intake_home.glob("queue.sqlite3*"):
        p.unlink()
    before = sorted(p.name for p in env.s.intake_home.rglob("*"))
    for p in ("/", "/item/inv-a-1a2b3c4d", "/export"):
        get(env, "work", p, {"Cookie": cookie})
    assert (
        sorted(p.name for p in env.s.intake_home.rglob("*")) == before
    )  # no GET created a file (6c's tests prove the view builders themselves)


def test_guarded_model_built_once(tmp_path, monkeypatch):
    calls = []
    real = model.build_guarded
    monkeypatch.setattr(model, "build_guarded", lambda s=None: calls.append(1) or real(s))
    e = start_service(tmp_path, monkeypatch)
    try:
        sign_in(e)
        get(e, "work", "/")
        assert len(calls) == 1
    finally:
        e.close()


def test_secrets_hygiene_service(tmp_path, monkeypatch, capfd):
    e = start_service(tmp_path, monkeypatch)
    try:
        vals = fake_secret_values()
        tokh = {"X-Hadavin-Token": vals["HADAVIN_WEBHOOK_SECRET"]}
        bodies = []
        cookie, csrf = sign_in(e)
        for app, path, h in (
            ("work", "/", {"Cookie": cookie}),
            ("work", "/export", {"Cookie": cookie}),
            ("work", "/login", NAV),
            ("work", "/nope", {}),
            ("dash", "/", {}),
            ("token", "/healthz", tokh),
            ("token", "/healthz", {}),
            ("token", "/nope", tokh),
        ):
            bodies.append(get(e, app, path, h))
        bodies.append(login(e, {"passphrase": "typed-wrong-xyz"}))
        bodies.append(form_post(e, "/export", {"csrf": csrf, "passphrase": "typed-wrong-xyz"}, cookies=cookie))
        for r in bodies:
            blob = r.text + repr(r.headers)
            for name, v in vals.items():
                assert v not in blob, name
            assert "typed-wrong-xyz" not in blob
        out = capfd.readouterr()
        for v in [*vals.values(), "typed-wrong-xyz", cookie.split("=", 1)[1], csrf]:
            assert v not in out.out + out.err
    finally:
        e.close()


def test_page_text_has_no_banned_words():
    banned = ("hard cap", "real ceiling", "accuracy", "robust")
    assert not [w for w in banned if any(w in t.lower() for t in T.values())]


def test_scan_reply_shapes(env):
    from intake.codes import Refused

    addr = env.token
    h = {"X-Hadavin-Token": fake_secret_values()["HADAVIN_WEBHOOK_SECRET"]}

    def scan():
        return raw(addr, build("POST", "/events/scan", f"{addr[0]}:{addr[1]}", h, b""))

    FakeScanner.script = [Refused("budget_halted", "model_mismatch hidden reason"), Refused("ledger_missing", "x"), None]
    r = scan()
    assert (
        r.status == 503 and r.text == '{"error": "halted"}' and "model_mismatch" not in r.text
    )  # scan_halted_503: the reason is never shown
    r = scan()
    assert r.status == 503 and r.text == '{"error": "ledger_missing"}'  # scan_spend_unreadable_503
    r = scan()
    assert r.status == 200 and r.text == '{"busy": true}'  # scan_busy_200
    FakeScanner.script = [Refused("not_a_real_code", "planted")]
    r = scan()
    assert r.status == 500 and r.text == '{"error": "internal"}'


def test_settle_failed_503_then_stop(env):
    from intake.codes import ConfigError

    addr = env.token
    h = {"X-Hadavin-Token": fake_secret_values()["HADAVIN_WEBHOOK_SECRET"]}
    FakeScanner.script = [ConfigError("settle_failed", "x")]
    r = raw(addr, build("POST", "/events/scan", f"{addr[0]}:{addr[1]}", h, b""))
    assert r.status == 503 and r.text == '{"error": "settle_failed"}'
    assert env.run.shared.stop.wait(2) and env.run.shared.fatal.is_set()
    for app, path in (("work", "/login"), ("dash", "/"), ("token", "/healthz")):
        a = getattr(env, app)
        rr = raw(a, build("GET", path, f"{a[0]}:{a[1]}", {**NAV, **h}))
        assert rr.status == 503, app  # every later request on every listener answers 503


# ---- errata 102: the export writes only what was previewed -----------------------------------------------------------------------------------------
def test_export_with_the_token_the_page_carried_writes(env):
    cookie, csrf = sign_in(env)
    approved(env)
    token = review_page.export_token(env.s)
    assert len(token) == 64
    r = form_post(env, "/export", {"csrf": csrf, "passphrase": PASS, "preview": token}, cookies=cookie)
    assert r.status == 200 and export_count(env) == 1


def test_an_invoice_approved_after_the_page_was_opened_is_not_written(env, capfd):
    cookie, csrf = sign_in(env)
    approved(env, "inv1")
    seen = review_page.export_token(env.s)  # the page was opened with one invoice in the list
    approved(env, "inv2", fields={**GOOD_FIELDS, "invoice_no": "INV-2002"})  # a second one is approved before the person presses Write
    r = form_post(env, "/export", {"csrf": csrf, "passphrase": PASS, "preview": seen}, cookies=cookie)
    assert r.status == 409 and txt(env.s, "export_changed") in r.text
    assert export_count(env) == 0 and csv_text(env) == ""  # nothing was written, not even the invoice that was on the page
    assert "code=export_changed" in capfd.readouterr().err  # and the log line says why
    r = form_post(env, "/export", {"csrf": csrf, "passphrase": PASS, "preview": review_page.export_token(env.s)}, cookies=cookie)
    assert r.status == 200 and export_count(env) == 2  # the slot was given back: the person opens the page again and writes both


def test_the_step_up_comes_before_the_token_check(env):
    cookie, csrf = sign_in(env)
    approved(env, "inv1")
    seen = review_page.export_token(env.s)
    approved(env, "inv2", fields={**GOOD_FIELDS, "invoice_no": "INV-2002"})
    r = form_post(env, "/export", {"csrf": csrf, "passphrase": "wrong-pass-xyz", "preview": seen}, cookies=cookie)
    assert r.status == 401  # a wrong passphrase is answered first (and counted), whatever the token says
    assert len(env.run.shared.throttle._failures) == 1


def test_a_missing_malformed_or_stale_preview_writes_nothing(env):
    cookie, csrf = sign_in(env)
    approved(env)
    good = review_page.export_token(env.s)
    for bad in ("", good[:63], good + "0", good.upper(), "g" * 64, " " + good[1:], "0" * 64, chr(233) * 64):
        r = form_post(env, "/export", {"csrf": csrf, "passphrase": PASS, "preview": bad}, cookies=cookie)
        assert r.status == 409 and txt(env.s, "export_changed") in r.text, repr(bad)
    wh, wp = env.work
    no_field = urlencode({"csrf": csrf, "passphrase": PASS}).encode()
    h = {
        "Origin": f"http://{wh}:{wp}",
        "Sec-Fetch-Site": "same-origin",
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": cookie,
    }
    r = raw(env.work, build("POST", "/export", f"{wh}:{wp}", h, no_field))
    assert r.status == 409 and txt(env.s, "export_changed") in r.text  # no token at all: refused too
    assert export_count(env) == 0 and csv_text(env) == ""  # not one invoice was written
    assert len(env.run.shared.throttle._failures) == 0  # the passphrase was right each time: no guess was counted


def test_a_token_that_cannot_be_computed_writes_nothing(env, monkeypatch):
    cookie, csrf = sign_in(env)
    approved(env)
    good = review_page.export_token(env.s)

    def broken(s):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(review_page, "export_token", broken)
    r = form_post(env, "/export", {"csrf": csrf, "passphrase": PASS, "preview": good}, cookies=cookie)
    assert r.status == 409 and export_count(env) == 0


def test_a_coding_error_in_the_token_step_is_a_500_not_a_reload_loop(env, monkeypatch):
    cookie, csrf = sign_in(env)
    approved(env)
    good = review_page.export_token(env.s)

    def broken(s):
        raise TypeError("a bug, not a busy database")

    monkeypatch.setattr(review_page, "export_token", broken)
    r = form_post(env, "/export", {"csrf": csrf, "passphrase": PASS, "preview": good}, cookies=cookie)
    assert r.status == 500 and export_count(env) == 0  # nothing written, and the person is not told to "reload" for ever
