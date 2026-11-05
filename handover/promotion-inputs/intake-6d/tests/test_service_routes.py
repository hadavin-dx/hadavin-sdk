"""The service over real sockets (package 6d, brief-v3 15.5): request parsing and limits, headers on every response, listeners, deadlines, token routes,
code mapping. Servers bind 127.0.0.21 / .22 and 127.0.0.1 on port 0; limits are shrunk so no test sleeps more than 2 s."""

from __future__ import annotations

import ast
import http.client
import io
import random
import socket
import sys
import threading
import time

import pytest
from service_helpers import (
    NAV,
    STYLE,
    FakeScanner,
    Resp,
    build,
    fast_limits,
    form_post,
    get,
    make_viewer,
    raw,
    sign_in,
    start_service,
)

from conftest import ROOT
from intake import review_page, routes, service
from intake.codes import ConfigError, Refused


@pytest.fixture
def env(tmp_path, monkeypatch):
    e = start_service(tmp_path, monkeypatch)
    yield e
    e.close()


def tok(env):
    return {"X-Hadavin-Token": env.secret("HADAVIN_WEBHOOK_SECRET")}


def scan(env, headers=None, body=None, **kw):
    addr = env.token
    h = {**tok(env), **(headers or {})}
    return raw(addr, build("POST", "/events/scan", f"{addr[0]}:{addr[1]}", h, body if body is not None else b"", **kw))


FULL_WORK = ("Content-Security-Policy", "Referrer-Policy", "X-Content-Type-Options", "Cache-Control", "Cross-Origin-Opener-Policy",
             "Cross-Origin-Resource-Policy", "Permissions-Policy", "X-Frame-Options", "Server")  # fmt: skip
FULL_TOKEN = (
    "Content-Security-Policy",
    "Referrer-Policy",
    "X-Content-Type-Options",
    "Cache-Control",
    "Cross-Origin-Resource-Policy",
    "Server",
)


def assert_headers(r: Resp, app: str):
    for h in FULL_TOKEN if app == "token" else FULL_WORK:
        assert r.first(h), (h, r.status)
    assert r.first("X-Content-Type-Options") == "nosniff" and r.first("Cache-Control") == "no-store" and r.first("Server") == "intake"
    assert r.first("Referrer-Policy") == ("no-referrer" if app == "token" else "same-origin")
    assert r.first("Content-Security-Policy") == (
        service.CSP_JSON if app == "token" else service.CSP_WORK_FORMAT.format(style_hash="sha256-" + STYLE)
    )
    for line in (r.first("Content-Type") or "",):
        assert "charset=utf-8" in line or r.status == 303
    for k, v in r.headers:
        assert "\r" not in k + v and "\n" not in k + v


# ---- token routes --------------------------------------------------------------------------------------------------------------------------
def test_scan_route_token_only(env):
    r = scan(env)
    assert r.status == 200 and r.first("Content-Type").startswith("application/json")
    assert set(__import__("json").loads(r.body)) == {"examined", "new", "refused", "duplicates", "remaining"}
    for h in ({}, {"X-Hadavin-Token": "wrong" * 10}, {"X-Hadavin-Token": ""}):
        addr = env.token
        r = raw(addr, build("POST", "/events/scan", f"{addr[0]}:{addr[1]}", h, b""))
        assert r.status == 401 and b"unauthorized" in r.body, h
    addr = env.token  # two token headers
    data = build("POST", "/events/scan", f"{addr[0]}:{addr[1]}", {**tok(env)}, b"").replace(
        b"\r\n\r\n", b"\r\n" + b"X-Hadavin-Token: " + tok(env)["X-Hadavin-Token"].encode() + b"\r\n\r\n", 1
    )
    assert raw(addr, data).status == 401
    assert FakeScanner.calls == 1  # only the first request scanned
    r = get(env, "token", "/healthz", tok(env))
    assert r.status == 200 and b"ok" in r.body
    assert get(env, "token", "/healthz").status == 401


def test_session_route_rejects_token(env):
    cookie, _ = sign_in(env)
    r = get(env, "work", "/", {"Cookie": cookie, **tok(env)})
    assert r.status == 403 and r.text.count("service key is not accepted") == 1
    assert get(env, "work", "/login", {**NAV, **tok(env)}).status == 403


def test_token_route_rejects_session(env):
    cookie, _ = sign_in(env)
    assert get(env, "token", "/healthz", {"Cookie": cookie}).status == 401
    assert scan(env, headers={"X-Hadavin-Token": "x" * 40, "Cookie": cookie}).status == 401  # a cookie never stands in for the token


def test_route_on_wrong_listener(env):
    cookie, _ = sign_in(env)
    assert get(env, "work", "/healthz", {"Cookie": cookie}).status == 404
    assert get(env, "token", "/login", NAV).status == 404
    assert get(env, "token", "/", tok(env)).status == 404
    assert get(env, "dash", "/healthz", tok(env)).status == 404
    r = form_post(env, "/events/scan", {}, cookies=cookie)
    assert r.status == 404


def test_dash_listener_skeleton(env):
    for p in ("/", "/login", "/healthz", "/events/scan", "/anything"):
        r = get(env, "dash", p)
        assert r.status == 404, p
        assert_headers(r, "dash")
    h, p = env.dash
    assert get(env, "dash", "/", host=f"{h}:{p + 1}").status == 421


def test_cookie_not_shared_across_listeners(env):
    cookie, _ = sign_in(env)
    assert get(env, "dash", "/", {"Cookie": cookie}).status == 404
    assert get(env, "token", "/healthz", {"Cookie": cookie}).status == 401
    assert get(env, "work", "/", {"Cookie": cookie}).status == 200


def test_host_per_listener(env):
    wh, wp = env.work
    for bad in (
        f"localhost:{wp}",
        f"[::1]:{wp}",
        f"0.0.0.0:{wp}",
        f"127.0.0.22:{wp}",
        f"{wh}.:{wp}",
        f"{wh}:{wp + 1}",
        wh,
        f"{wh} :{wp}",
        f"{wh}:{wp}	1",
        f"{wh}:{wp},{wh}:{wp}",
        "evil.example",
    ):
        r = raw(env.work, build("GET", "/login", bad, NAV))
        assert r.status == 421 and b"own address" in r.body, bad
        assert_headers(r, "work")
    assert raw(env.work, build("GET", "/login", "x", NAV, drop=("Host",))).status == 421  # no Host
    two = build("GET", "/login", f"{wh}:{wp}", NAV).replace(b"\r\n\r\n", f"\r\nHost: {wh}:{wp}\r\n\r\n".encode(), 1)
    assert raw(env.work, two).status == 421
    th, tp = env.token
    assert raw(env.token, build("GET", "/healthz", f"host.docker.internal:{tp}", tok(env))).status == 200
    assert raw(env.token, build("GET", "/healthz", f"localhost:{tp}", tok(env))).status == 421
    assert raw(env.work, build("GET", "/login", f"host.docker.internal:{wp}", NAV)).status == 421


# ---- parsing --------------------------------------------------------------------------------------------------------------------------------
def test_content_length_strict(env):
    wh, wp = env.work
    base = {"Origin": f"http://{wh}:{wp}", "Sec-Fetch-Site": "same-origin", "Content-Type": "application/x-www-form-urlencoded"}
    cookie, csrf = sign_in(env)
    bad_values = ["+5", "-1", "5 5", "5,5", "0x5", "1e1", "", "123456", "\u0665".encode().decode("latin-1")]
    for v in bad_values:
        data = build("POST", "/logout", f"{wh}:{wp}", {**base, "Cookie": cookie, "Content-Length": v}, b"")
        assert raw(env.work, data).status == 400, repr(v)
    dup = build("POST", "/logout", f"{wh}:{wp}", {**base, "Cookie": cookie}, b"csrf=x").replace(
        b"\r\n\r\n", b"\r\nContent-Length: 6\r\n\r\n", 1
    )
    assert raw(env.work, dup).status == 400
    # a VALID form (right csrf, signed in): without the Transfer-Encoding rule this would be a normal logout (303), so only that rule can give 400
    te = build("POST", "/logout", f"{wh}:{wp}", {**base, "Cookie": cookie, "Transfer-Encoding": "chunked"}, f"csrf={csrf}".encode())
    assert raw(env.work, te).status == 400
    te_token = build("POST", "/events/scan", f"{env.token[0]}:{env.token[1]}", {**tok(env), "Transfer-Encoding": "chunked"}, b"")
    assert raw(env.token, te_token).status == 400
    # body cap: exactly the cap is read (and then fails the form rule), one more is 413
    ok = build("POST", "/logout", f"{wh}:{wp}", {**base, "Cookie": cookie}, b"a" * service.LIMIT_BODY_WORK)
    assert raw(env.work, ok).status == 400
    big = build("POST", "/logout", f"{wh}:{wp}", {**base, "Cookie": cookie}, b"a" * (service.LIMIT_BODY_WORK + 1))
    assert raw(env.work, big).status == 413
    assert scan(env, body=b"a" * service.LIMIT_BODY_TOKEN).status == 200
    assert scan(env, body=b"a" * (service.LIMIT_BODY_TOKEN + 1)).status == 413
    get_with_body = build("GET", "/login", f"{wh}:{wp}", {**NAV, "Content-Length": "3"}, b"abc")
    assert raw(env.work, get_with_body).status == 400


def test_request_target_forms(env):
    wh, wp = env.work
    host = f"{wh}:{wp}"
    for target, status in [
        (f"http://{host}/login", 400),
        ("*", 400),
        ("//evil.example/", 400),
        (host, 400),
        ("/%2e%2e/login", 404),
        ("/login%20", 404),
        ("/login/", 404),
        ("/\\evil.example", 404),
        ("/login#frag", 404),
        ("/item/%41", 404),
        ("/item/x", 404),
        ("/?evil=1", 422),
        ("/?sort=a&sort=b", 422),
        ("/?a", 422),
        ("/login?x=1", 422),
    ]:
        r = raw(env.work, f"GET {target} HTTP/1.1\r\nHost: {host}\r\n\r\n".encode())
        assert r.status == status, (target, r.status)
    assert raw(env.work, f"GET /a b HTTP/1.1\r\nHost: {host}\r\n\r\n".encode()).status == 400
    assert raw(env.work, f"GET /login\tx HTTP/1.1\r\nHost: {host}\r\n\r\n".encode()).status == 400
    assert raw(env.work, f"GET /login HTTP/1.1\nHost: {host}\n\n".encode()).status == 400  # bare LF line ends are refused


def test_no_upgrade(env):
    wh, wp = env.work
    r = raw(env.work, build("GET", "/login", f"{wh}:{wp}", {**NAV, "Upgrade": "websocket", "Connection": "Upgrade"}))
    assert r.status == 400


def test_methods(env):
    wh, wp = env.work
    for m in ("HEAD", "PUT", "DELETE", "TRACE", "OPTIONS", "CONNECT", "PATCH"):
        r = raw(env.work, build(m, "/", f"{wh}:{wp}"))
        assert r.status == 405, m
        assert_headers(r, "work")
    r = raw(env.work, build("FOO", "/", f"{wh}:{wp}"))
    assert r.status == 501
    assert b"FOO" not in r.body
    assert get(env, "work", "/logout").status == 405  # the path exists, with POST only
    assert get(env, "token", "/events/scan", tok(env)).status == 405
    assert get(env, "work", "/login", NAV).status == 200
    assert raw(env.work, build("POST", "/healthz", f"{wh}:{wp}", {}, b"")).status == 404  # healthz belongs to the token listener
    assert raw(env.work, build("POST", "/export", f"{wh}:{wp}", {}, b"")).status == 401  # the path exists with POST: needs a session first


def test_stdlib_errors_use_our_writer(env):
    wh, wp = env.work
    host = f"{wh}:{wp}"
    many = "".join(f"X-H{i}: v\r\n" for i in range(41))
    cases = {
        400: b"GARBAGE\r\n\r\n",
        414: b"GET /" + b"a" * 3000 + b" HTTP/1.1\r\n\r\n",
        431: f"GET /login HTTP/1.1\r\nHost: {host}\r\n{many}\r\n".encode(),
        501: f"FOO /login HTTP/1.1\r\nHost: {host}\r\n\r\n".encode(),
        505: f"GET /login HTTP/2.0\r\nHost: {host}\r\n\r\n".encode(),
    }
    for want, data in cases.items():
        r = raw(env.work, data)
        assert r.status == want, (want, r.status)
        assert_headers(r, "work")
        assert b"GARBAGE" not in r.body and b"aaaa" not in r.body and b"X-H" not in r.body and b"FOO" not in r.body
    long_hdr = f"GET /login HTTP/1.1\r\nHost: {host}\r\nX: {'a' * 5000}\r\n\r\n".encode()
    assert raw(env.work, long_hdr).status == 431


def test_form_content_type_variants(env):
    cookie, csrf = sign_in(env)
    for ct, ok in [
        ("application/x-www-form-urlencoded", True),
        ("application/x-www-form-urlencoded; charset=utf-8", True),
        ("Application/X-WWW-Form-Urlencoded ;charset=UTF-8", True),
        ("text/plain", False),
        ("multipart/form-data; boundary=x", False),
        ("application/x-www-form-urlencoded; charset=latin-1", False),
        ("application/x-www-form-urlencoded; boundary=x", False),
        ("application/json", False),
    ]:
        r = form_post(env, "/logout", {"csrf": "x"}, cookies=cookie, extra={"Content-Type": ct})
        assert (r.status == 403) is ok and (ok or r.status == 400), (ct, r.status)  # ok = got past the type rule to the CSRF check
    wh, wp = env.work
    no_ct = build(
        "POST", "/logout", f"{wh}:{wp}", {"Origin": f"http://{wh}:{wp}", "Sec-Fetch-Site": "same-origin", "Cookie": cookie}, b"csrf=x"
    )
    assert raw(env.work, no_ct).status == 400


def test_form_strict_parsing_and_fields(env):
    cookie, csrf = sign_in(env)
    wh, wp = env.work
    base = {
        "Origin": f"http://{wh}:{wp}",
        "Sec-Fetch-Site": "same-origin",
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": cookie,
    }

    def post(body: bytes):
        return raw(env.work, build("POST", "/logout", f"{wh}:{wp}", base, body)).status

    assert post(f"csrf={csrf}&junk".encode()) == 400  # a piece without "=" is not silently dropped
    assert post(f"csrf={csrf}&approver=ap-a".encode()) == 400  # approver_field_refused: identity comes from the session only
    assert post(f"csrf={csrf}&csrf={csrf}".encode()) == 400  # repeated
    assert post(f"csrf={csrf}&".encode()) == 400  # an empty piece is not silently skipped
    assert post(b"") == 400  # missing
    assert post(b"csrf=%ff") == 400  # not UTF-8
    assert post(f"csrf={csrf}".encode()) == 303


def test_body_too_large_413_seen_by_client(env):
    wh, wp = env.work
    cookie, _ = sign_in(env)
    c = http.client.HTTPConnection(wh, wp, timeout=5)
    c.request("POST", "/logout", body=b"a" * 9000, headers={"Cookie": cookie, "Origin": f"http://{wh}:{wp}", "Sec-Fetch-Site": "same-origin",
                                                          "Content-Type": "application/x-www-form-urlencoded"})  # fmt: skip
    r = c.getresponse()
    assert r.status == 413
    r.read()
    c.close()
    th, tp = env.token
    c = http.client.HTTPConnection(th, tp, timeout=5)
    c.request("POST", "/events/scan", body=b"a" * 5000, headers=tok(env))
    assert c.getresponse().status == 413
    c.close()


def test_token_post_without_length_is_empty(env):
    r = scan(env)  # build() adds Content-Length: 0 for b"": send it with NO length at all
    addr = env.token
    data = f"POST /events/scan HTTP/1.1\r\nHost: {addr[0]}:{addr[1]}\r\nX-Hadavin-Token: {tok(env)['X-Hadavin-Token']}\r\n\r\n".encode()
    r = raw(addr, data)
    assert r.status == 200
    wh, wp = env.work
    cookie, csrf = sign_in(env)
    h = {
        "Origin": f"http://{wh}:{wp}",
        "Sec-Fetch-Site": "same-origin",
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": cookie,
    }
    r = raw(env.work, build("POST", "/logout", f"{wh}:{wp}", h))
    assert r.status == 411


def test_fixture_wall_clock_never_steps_back(env, monkeypatch):
    """The service fixture must survive a container clock step (evidence 6d-5): its wall clock follows time.time but never goes backwards."""
    wall = env.run.shared.sessions._clocks.wall
    assert env.run.shared.pre._clocks.wall is not time.time
    monkeypatch.setattr(time, "time", lambda: 4_000_000_000.0)  # far above the real time, so a clock that ignores time.time cannot match
    assert wall() == 4_000_000_000.0
    monkeypatch.setattr(time, "time", lambda: 3_999_999_995.0)  # the clock steps back 5 s
    assert wall() == 4_000_000_000.0


def test_a_real_backward_wall_step_ends_the_session(env):
    """Spec M-B (kept on purpose, no tolerance): if the wall clock goes back, every session is treated as expired. Not a bug: see README, Sessions."""
    from service_helpers import use_fake_clocks

    fc = use_fake_clocks(env)
    cookie, _ = sign_in(env)
    assert get(env, "work", "/", {"Cookie": cookie, **NAV}).status == 200
    fc.w -= 5  # the wall clock steps back 5 s; the monotonic clock does not
    r = get(env, "work", "/", {"Cookie": cookie, **NAV})
    assert r.status == 303 and "/login" in (r.first("Location") or "")


def test_check_order(env):
    wh, wp = env.work
    host = f"{wh}:{wp}"
    cookie, csrf = sign_in(env)
    vcookie, vcsrf = make_viewer(env)
    text = review_page.ERROR_TEXT
    # 4 Host before everything (even a wrong path and a token header)
    assert raw(env.work, build("GET", "/nope", "evil", {"X-Hadavin-Token": "x"})).status == 421
    # 5 upgrade, 6 route, 7 query
    assert raw(env.work, build("GET", "/nope", host, {"Upgrade": "x"})).status == 400
    assert raw(env.work, build("GET", "/nope", host)).status == 404
    assert (
        raw(env.work, build("GET", "/?evil=1", host, {"X-Hadavin-Token": "x"})).status == 422
    )  # the query rule comes before the token rule
    # 8 token: before the body rules
    th, tp = env.token
    assert raw(env.token, build("POST", "/events/scan", f"{th}:{tp}", {"Transfer-Encoding": "chunked"}, b"")).status == 401
    # 9 token header on a work route before the session
    assert raw(env.work, build("GET", "/", host, {"X-Hadavin-Token": "x"})).status == 403
    assert raw(env.work, build("GET", "/", host)).status == 303
    # 9 session before 10 origin
    assert form_post(env, "/logout", {"csrf": "x"}, extra={"Origin": "http://evil.example"}).status == 401
    # 10 origin before the body rules
    r = form_post(env, "/logout", {"csrf": csrf}, cookies=cookie, extra={"Origin": "http://evil.example", "Transfer-Encoding": "chunked"})
    assert r.status == 403 and text["bad_origin"] in r.text
    # 12 CSRF before 13 role
    r = form_post(
        env,
        "/item/inv-a-1a2b3c4d/decide",
        {"csrf": "bad", "decision": "approve", "reason": "", "content_code": "0" * 64, "version": "1"},
        cookies=vcookie,
    )
    assert r.status == 403 and text["csrf_failed"] in r.text
    r = form_post(
        env,
        "/item/inv-a-1a2b3c4d/decide",
        {"csrf": vcsrf, "decision": "approve", "reason": "", "content_code": "0" * 64, "version": "1"},
        cookies=vcookie,
    )
    assert r.status == 403 and text["role_denied"] in r.text
    # each request below breaks TWO rules at once; the earlier rule of the spec order must be the one that answers
    ok = {
        "Origin": f"http://{wh}:{wp}",
        "Sec-Fetch-Site": "same-origin",
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": cookie,
    }
    # 1 Origin (10) before 411 (no Content-Length on a work POST) (11)
    r = raw(env.work, build("POST", "/logout", host, {**ok, "Origin": "http://evil.example"}))
    assert r.status == 403 and text["bad_origin"] in r.text
    # 2 Origin (10) before 413 (body too large) (11)
    r = raw(env.work, build("POST", "/logout", host, {**ok, "Origin": "http://evil.example"}, b"a" * (service.LIMIT_BODY_WORK + 1)))
    assert r.status == 403 and text["bad_origin"] in r.text
    # 3 413 (11) before the form rules (13): a too-large body that is also not a form (wrong Content-Type)
    r = raw(env.work, build("POST", "/logout", host, {**ok, "Content-Type": "text/plain"}, b"a" * (service.LIMIT_BODY_WORK + 1)))
    assert r.status == 413
    # 4 the query rule (7) before the token rule (8), on the token listener too (a wrong token AND an unknown query)
    r = raw(env.token, build("GET", "/healthz?evil=1", f"{th}:{tp}", {"X-Hadavin-Token": "wrong"}))
    assert r.status == 422
    # 5 upgrade (5) before route (6) before query (7): an unknown path with an unknown query is 404 only without the Upgrade header
    assert raw(env.work, build("GET", "/nope?evil=1", host, {"Upgrade": "x"})).status == 400
    assert raw(env.work, build("GET", "/nope?evil=1", host)).status == 404


# ---- headers ---------------------------------------------------------------------------------------------------------------------------------
def test_csp_per_app(env):
    w = get(env, "work", "/login", NAV)
    t = get(env, "token", "/healthz", tok(env))
    assert w.first("Content-Security-Policy") == service.CSP_WORK_FORMAT.format(style_hash="sha256-" + STYLE)
    assert t.first("Content-Security-Policy") == service.CSP_JSON == "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    for csp in (w.first("Content-Security-Policy"), t.first("Content-Security-Policy")):
        assert "unsafe-" not in csp and " * " not in csp and "script-src" not in csp
    assert "style-src 'sha256-" in w.first("Content-Security-Policy") and "'self'" not in w.first("Content-Security-Policy").replace(
        "form-action 'self'", ""
    )


def test_style_hash_matches_ui(env):
    from intake import ui

    csp = get(env, "work", "/login", NAV).first("Content-Security-Policy")
    assert f"style-src 'sha256-{ui.STYLE_SHA256}';" in csp


def test_headers_on_every_response(env):
    wh, wp = env.work
    host = f"{wh}:{wp}"
    cookie, csrf = sign_in(env)
    cases = [
        (raw(env.work, build("GET", "/login", host, NAV)), 200),
        (raw(env.work, build("GET", "/", host)), 303),
        (raw(env.work, b"GARBAGE\r\n\r\n"), 400),
        (raw(env.work, build("POST", "/export", host, {}, b"")), 401),
        (raw(env.work, build("GET", "/", host, {"X-Hadavin-Token": "x"})), 403),
        (raw(env.work, build("GET", "/nope", host)), 404),
        (raw(env.work, build("PUT", "/", host)), 405),
        (
            raw(
                env.work,
                build(
                    "POST",
                    "/logout",
                    host,
                    {
                        "Origin": f"http://{host}",
                        "Sec-Fetch-Site": "same-origin",
                        "Cookie": cookie,
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                ),
            ),
            411,
        ),  # fmt: skip
        (
            raw(
                env.work,
                build(
                    "POST",
                    "/logout",
                    host,
                    {
                        "Origin": f"http://{host}",
                        "Sec-Fetch-Site": "same-origin",
                        "Cookie": cookie,
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    b"a" * 9000,
                ),
            ),
            413,
        ),  # fmt: skip
        (raw(env.work, b"GET /" + b"a" * 3000 + b" HTTP/1.1\r\n\r\n"), 414),
        (raw(env.work, build("GET", "/", "evil")), 421),
        (raw(env.work, build("GET", "/?x=1", host)), 422),
        (raw(env.work, f"FOO / HTTP/1.1\r\nHost: {host}\r\n\r\n".encode()), 501),
        (raw(env.work, f"GET / HTTP/2.0\r\nHost: {host}\r\n\r\n".encode()), 505),
    ]
    for r, want in cases:
        assert r.status == want, (want, r.status)
        assert_headers(r, "work")
        assert r.first("Cross-Origin-Embedder-Policy") == "require-corp"
    for _ in range(7):  # 429: the sign-in throttle
        r = form_post(env, "/login", {"csrf": "x", "login": "ap-a", "passphrase": "wrong"})
    assert r.status in (401, 403, 429)
    for r in (raw(env.token, b"GARBAGE\r\n\r\n"), get(env, "token", "/healthz"), get(env, "token", "/nope", tok(env))):
        assert r.status in (400, 401, 404)
        assert_headers(r, "token")


def test_referrer_policy_per_response(env):
    assert get(env, "work", "/login", NAV).first("Referrer-Policy") == "same-origin"
    assert get(env, "token", "/healthz", tok(env)).first("Referrer-Policy") == "no-referrer"
    assert get(env, "dash", "/").first("Referrer-Policy") == "same-origin"


class _FakeHandler:
    def __init__(self, server):
        self.server, self.wfile, self.ctx, self.route = server, io.BytesIO(), {}, None


def test_header_crlf(env):
    srv = env.run.servers["work"]
    for name, value in [
        ("X", "a\r\nSet-Cookie: evil=1"),
        ("X", "a\nb"),
        ("X", "a\rb"),
        ("X", "a\x00b"),
        ("X\r\nY", "v"),
        ("X\x00", "v"),
        ("X\n", "v"),
    ]:
        h = _FakeHandler(srv)
        with pytest.raises(ValueError):
            service.send(h, 200, b"", "text/html; charset=utf-8", ((name, value),))
        assert h.wfile.getvalue() == b""  # nothing was written
    rnd = random.Random(7)
    for _ in range(200):  # fuzz: any CR, LF or NUL anywhere is refused, anything else is written
        v = "".join(rnd.choice("ab \t\r\n\x00;=") for _ in range(rnd.randint(0, 12)))
        h = _FakeHandler(srv)
        bad = any(c in v for c in "\r\n\x00")
        try:
            service.send(h, 200, b"", "text/plain", (("X-T", v),))
            assert not bad
        except ValueError:
            assert bad


def test_send_encodes_lone_surrogate(env):
    h = _FakeHandler(env.run.servers["work"])
    service.send(h, 200, "a\ud800b", "text/html; charset=utf-8", ())
    assert h.wfile.getvalue().endswith(b"a?b")


def test_log_injection(env, capsys):
    wh, wp = env.work
    host = f"{wh}:{wp}"
    evil = ["\x1b[31mred", "\u202eevil", "a\rb", "a\nb", "%0d%0a", "\u0000"]
    for e in evil:
        raw(env.work, f"GET /{e} HTTP/1.1\r\nHost: {host}\r\n\r\n".encode("utf-8", "replace"))
        raw(env.work, f"GET /?{e}=1 HTTP/1.1\r\nHost: {host}\r\n\r\n".encode("utf-8", "replace"))
        raw(
            env.work,
            f"GET /login HTTP/1.1\r\nHost: {host}\r\nX-Request-Id: {e}\r\nSec-Fetch-Mode: navigate\r\nSec-Fetch-Dest: document\r\nSec-Fetch-Site: none\r\n\r\n".encode(
                "utf-8", "replace"
            ),
        )
    raw(env.work, build("GET", "/login", host, {**NAV, "X-Request-Id": "abc-123_OK"}))
    raw(env.work, build("GET", "/login", host, {**NAV, "X-Request-Id": "a" * 60}))
    time.sleep(0.2)
    err = capsys.readouterr().err
    assert (
        "\x1b" not in err
        and "\u202e" not in err
        and "\x00" not in err
        and "%0d" not in err
        and "red" not in err.replace("rid=", "").replace("status", "")
    )
    for line in err.splitlines():
        if line.startswith("intake "):
            assert line.count("\r") == 0 and " app=" in line and " rid=" in line
    assert "rid=abc-123_OK" in err and "rid=" + "a" * 32 + " " in err and "a" * 33 not in err
    assert "/nope" not in err and "evil" not in err


def test_no_open_redirect(env):
    wh, wp = env.work
    host = f"{wh}:{wp}"
    paths = [
        "//evil.example",
        "/\\evil.example",
        "/%2f%2fevil.example",
        "http:evil",
        "/\t/evil.example",
        "/\n/evil.example",
        "/login?next=//evil.example",
        "/ /evil",
    ]
    for p in paths:
        r = raw(env.work, f"GET {p} HTTP/1.1\r\nHost: {host}\r\n\r\n".encode("latin-1", "replace"))
        assert r.status in (400, 404, 422), (p, r.status)
        assert not r.h("Location"), p
    r = raw(env.work, build("GET", "/", host))
    assert r.status == 303 and r.h("Location") == ["/login"]


# ---- limits, deadlines ---------------------------------------------------------------------------------------------------------------------
def _slow_start(tmp_path, monkeypatch, **lim):
    return start_service(tmp_path, monkeypatch, limits=fast_limits(**lim))


def _wait_closed(sock, limit):
    """Seconds until the server closed or shut the connection (EOF or reset), or None if still open after ``limit``."""
    t0 = time.monotonic()
    sock.settimeout(0.1)
    while time.monotonic() - t0 < limit:
        try:
            if sock.recv(1024) == b"":
                return time.monotonic() - t0
        except TimeoutError:
            continue
        except OSError:
            return time.monotonic() - t0
    return None


def test_request_deadline(tmp_path, monkeypatch):
    e = _slow_start(tmp_path, monkeypatch, read_s=1, conn_work=1)
    try:
        c = socket.create_connection(e.work)
        c.sendall(b"GET /login HTTP/1.1\r\n")
        t0 = time.monotonic()
        closed = None
        while time.monotonic() - t0 < 2.5 and closed is None:
            try:
                c.sendall(b"X")  # one byte every 0.3 s: a drip client
            except OSError:
                closed = time.monotonic() - t0
                break
            time.sleep(0.3)
            c.settimeout(0.01)
            try:
                if c.recv(10) == b"":
                    closed = time.monotonic() - t0
            except TimeoutError:
                pass
            except OSError:
                closed = time.monotonic() - t0
        assert closed is not None and closed < 1.8, closed
        c.close()
        assert get(e, "work", "/login", NAV).status == 200  # the slot was released (cap 1)
    finally:
        e.close()


def test_drip_body(tmp_path, monkeypatch):
    e = _slow_start(tmp_path, monkeypatch, read_s=1)
    try:
        wh, wp = e.work
        c = socket.create_connection(e.work)
        c.sendall(
            build(
                "POST",
                "/logout",
                f"{wh}:{wp}",
                {
                    "Origin": f"http://{wh}:{wp}",
                    "Sec-Fetch-Site": "same-origin",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Content-Length": "100",
                },
            )
        )
        t0 = time.monotonic()
        closed = None
        while time.monotonic() - t0 < 2.5 and closed is None:
            try:
                c.sendall(b"a")
            except OSError:
                closed = time.monotonic() - t0
                break
            time.sleep(0.3)
            c.settimeout(0.01)
            try:
                if c.recv(10) == b"":
                    closed = time.monotonic() - t0
            except TimeoutError:
                pass
            except OSError:
                closed = time.monotonic() - t0
        assert closed is not None and closed < 1.8, closed
        c.close()
    finally:
        e.close()


def test_connection_cap_per_listener(tmp_path, monkeypatch):
    e = _slow_start(tmp_path, monkeypatch, conn_work=2, conn_dash=2, conn_token=1)
    held = []
    try:
        for _ in range(2):
            held.append(socket.create_connection(e.dash))
        extra = socket.create_connection(e.dash)  # the third is closed at once
        assert _wait_closed(extra, 1.5) is not None
        extra.close()
        cookie, _ = sign_in(e)  # the work listener still answers while the dash cap is full
        assert get(e, "work", "/", {"Cookie": cookie}).status == 200
        for _ in range(2):
            held.append(socket.create_connection(e.work))
        extra = socket.create_connection(e.work)
        assert _wait_closed(extra, 1.5) is not None
        extra.close()
        assert scan(e).status == 200  # the token scan still answers while the work cap is full
    finally:
        for c in held:
            c.close()
        e.close()


def test_processing_deadline(tmp_path, monkeypatch):
    e = _slow_start(tmp_path, monkeypatch, handle_s=0.5)
    done = threading.Event()

    def slow(req):
        time.sleep(1.0)
        done.set()  # the side effect of the route still happens after the socket was shut down
        return service.Reply(200, b"late", "text/plain")

    monkeypatch.setattr(service, "HANDLERS", {**service.HANDLERS, "home": slow})
    try:
        cookie, _ = sign_in(e)
        wh, wp = e.work
        c = socket.create_connection(e.work)
        c.sendall(build("GET", "/", f"{wh}:{wp}", {"Cookie": cookie}))
        t0 = time.monotonic()
        data = b""
        c.settimeout(2.0)
        try:
            while True:
                chunk = c.recv(1024)
                if not chunk:
                    break
                data += chunk
        except OSError:
            pass
        assert time.monotonic() - t0 < 0.95 and data == b""  # shut down at ~0.5 s with no reply
        c.close()
        assert done.wait(2.0)
    finally:
        e.close()


def test_scan_deadline_applies(tmp_path, monkeypatch):
    e = _slow_start(tmp_path, monkeypatch, scan_s=0.5, handle_s=30)
    try:
        FakeScanner.delay = 1.0
        t0 = time.monotonic()
        addr = e.token
        c = socket.create_connection(addr)
        c.sendall(build("POST", "/events/scan", f"{addr[0]}:{addr[1]}", tok(e), b""))
        c.settimeout(2.0)
        data = b""
        try:
            while True:
                chunk = c.recv(1024)
                if not chunk:
                    break
                data += chunk
        except OSError:
            pass
        assert data == b"" and time.monotonic() - t0 < 0.95
        c.close()
        time.sleep(0.8)
        assert FakeScanner.calls == 1 and FakeScanner.done == 1  # the scan itself finished in the handler thread
    finally:
        e.close()


def test_scan_gets_scan_bound_not_handle_bound(tmp_path, monkeypatch):
    e = _slow_start(tmp_path, monkeypatch, scan_s=2, handle_s=0.2)
    try:
        FakeScanner.delay = 0.5
        assert scan(e).status == 200  # 0.5 s of scanning is over the 0.2 s handle bound but inside the 2 s scan bound
    finally:
        e.close()


def test_watchdog_shutdown_only():
    tree = ast.parse((ROOT / "src" / "intake" / "service.py").read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_watchdog")
    attrs = [n.attr for n in ast.walk(fn) if isinstance(n, ast.Attribute)]
    assert "shutdown" in attrs and "close" not in attrs and "detach" not in attrs


def test_scan_survives_closed_socket(tmp_path, monkeypatch):
    e = _slow_start(tmp_path, monkeypatch)
    try:
        FakeScanner.delay = 0.5
        addr = e.token
        c = socket.create_connection(addr)
        c.sendall(build("POST", "/events/scan", f"{addr[0]}:{addr[1]}", tok(e), b""))
        time.sleep(0.1)
        c.close()  # the client (n8n) gave up while the scan runs
        t0 = time.monotonic()
        while FakeScanner.done < 1 and time.monotonic() - t0 < 2:
            time.sleep(0.05)
        assert FakeScanner.calls == 1 and FakeScanner.done == 1
        assert scan(e).status == 200  # the service is still fine
    finally:
        e.close()


# ---- code mapping --------------------------------------------------------------------------------------------------------------------------
def test_unknown_code_is_internal(env, monkeypatch):
    cookie, _ = sign_in(env)

    def boom(req):
        raise Refused("not_a_real_code", "planted text C:\\secret\\path")

    monkeypatch.setattr(service, "HANDLERS", {**service.HANDLERS, "home": boom})
    r = get(env, "work", "/", {"Cookie": cookie})
    assert r.status == 500 and b"not_a_real_code" not in r.body and b"planted" not in r.body and b"secret" not in r.body
    assert review_page.ERROR_TEXT["internal"] in r.text


def test_config_error_text_never_shown(env, monkeypatch):
    cookie, _ = sign_in(env)
    for exc in (
        ConfigError("bad_config", "path C:\\Users\\x\\secret"),
        Refused("ledger_inconsistent", "planted"),
        RuntimeError("planted runtime text"),
    ):
        monkeypatch.setattr(service, "HANDLERS", {**service.HANDLERS, "home": lambda req, exc=exc: (_ for _ in ()).throw(exc)})
        r = get(env, "work", "/", {"Cookie": cookie})
        assert (
            r.status == 500
            and b"planted" not in r.body
            and b"Users" not in r.body
            and b"bad_config" not in r.body
            and b"ledger_inconsistent" not in r.body
        )


def test_status_and_code_translations():
    from intake import access
    from intake.codes import SecretError

    assert service.status_and_code(SecretError("key_short", "x")) == (503, "not_configured")
    assert service.status_and_code(access.NotConfigured()) == (503, "not_configured")
    assert service.status_and_code(access.Throttled()) == (429, "too_many_attempts")
    assert service.status_and_code(access.Denied("csrf_failed")) == (403, "csrf_failed")
    assert service.status_and_code(__import__("sqlite3").OperationalError("database is locked")) == (503, "db_busy")
    assert service.status_and_code(__import__("sqlite3").DatabaseError("malformed")) == (500, "internal")
    assert service.status_and_code(Refused("budget_halted", "x")) == (503, "budget_halted")


def test_every_raisable_code_mapped():
    import test_wp6_kickoff as k

    k.test_every_raised_code_has_a_place_at_kickoff()


def test_handle_error_no_traceback(env, capsys):
    srv = env.run.servers["work"]
    try:
        raise RuntimeError("planted traceback text")
    except RuntimeError:
        srv.handle_error(None, ("127.0.0.1", 1))
    err = capsys.readouterr().err
    assert "Traceback" not in err and "planted" not in err and err.count("\n") == 1 and "code=internal" in err


def test_dispatch_touch_rule(env, monkeypatch):
    from service_helpers import use_fake_clocks

    fc = use_fake_clocks(env)
    cookie, _ = sign_in(env)
    sid = cookie.split("=", 1)[1]
    store = env.run.shared.sessions
    t0 = store._by_sid[sid].last_touch
    monkeypatch.setattr(service, "JSON_ROUTES", frozenset({"overview"}))
    monkeypatch.setattr(
        service, "HANDLERS", {**service.HANDLERS, "overview": lambda r: service.Reply(200, b"{}", "application/json; charset=utf-8")}
    )
    fc.advance(5)
    assert get(env, "work", "/overview", {"Cookie": cookie}).status == 200
    assert store._by_sid[sid].last_touch == t0  # a JSON route never refreshes the idle time
    assert get(env, "work", "/", {"Cookie": cookie}).status == 200
    assert store._by_sid[sid].last_touch.mono == t0.mono + 5  # an HTML page does


def test_routes_have_roles_on_the_listener(env, monkeypatch):
    import re

    nobody = routes.Route("nobody", "GET", "/nobody", frozenset(), "work", "session")
    monkeypatch.setattr(routes, "_PATTERNS", routes._PATTERNS + ((re.compile("/nobody"), nobody),))
    monkeypatch.setattr(service, "HANDLERS", {**service.HANDLERS, "nobody": lambda r: service.Reply(200, b"x", "text/plain")})
    for cookie in (sign_in(env)[0], make_viewer(env)[0]):
        assert get(env, "work", "/nobody", {"Cookie": cookie}).status == 403  # default deny: an empty role set serves nobody
    assert get(env, "work", "/nobody").status == 303  # no session: sign in first
    rows = {r.name for r in routes.ROUTE_TABLE}
    assert rows - set(service.HANDLERS) == {"overview"}
    assert get(env, "work", "/overview", {"Cookie": sign_in(env)[0]}).status == 404  # until P2a adds the page


def test_viewer_refused_every_post_except_logout(env):
    vcookie, vcsrf = make_viewer(env)
    item = "inv-a-1a2b3c4d"
    r = form_post(
        env,
        f"/item/{item}/decide",
        {"csrf": vcsrf, "decision": "approve", "reason": "", "content_code": "0" * 64, "version": "1"},
        cookies=vcookie,
    )
    assert r.status == 403
    assert form_post(env, "/export", {"csrf": vcsrf, "passphrase": "x"}, cookies=vcookie).status == 403
    assert get(env, "work", "/export", {"Cookie": vcookie}).status == 403  # viewer_refused_export_page (M-C)
    assert form_post(env, "/logout", {"csrf": vcsrf}, cookies=vcookie).status == 303


def test_no_stub_left():
    for p in (ROOT / "src" / "intake").glob("*.py"):
        if p.name not in ("service.py", "access.py", "routes.py"):
            continue  # inbox.py, review_page.py and cli.py (trace) belong to other packages; the integration head checks every file
        tree = ast.parse(p.read_text(encoding="utf-8"))
        assert not [
            n
            for n in ast.walk(tree)
            if isinstance(n, ast.Raise) and isinstance(n.exc, (ast.Name, ast.Call)) and "NotImplementedError" in ast.dump(n)
        ], p.name


def test_product_entry_fixed_ast():
    # serve() is called with no hosts= / limits= in product code (cli.py); only tests and the attack harness pass them
    for p in (ROOT / "src" / "intake").glob("*.py"):
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            if (
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute)
                and n.func.attr in ("serve", "start")
                and getattr(n.func.value, "id", "") == "service"
            ):
                assert not n.keywords, (p.name, n.lineno)


def test_listeners_loopback_only(env):
    assert {a: sv.server_address[0] for a, sv in env.run.servers.items()} == {
        "token": "127.0.0.1",
        "work": "127.0.0.21",
        "dash": "127.0.0.22",
    }
    if sys.platform == "win32":
        assert service.IntakeServer.allow_reuse_address is False
    src = (ROOT / "src" / "intake" / "service.py").read_text(encoding="utf-8")
    assert "0.0.0.0" not in src and "getfqdn" not in src.replace("never socket.getfqdn", "")
    assert service.PRODUCT_HOSTS == {"token": "127.0.0.1", "work": "127.0.0.11", "dash": "127.0.0.12"}


def test_settle_failed_from_any_handler_stops_the_service(env, monkeypatch):
    cookie, _ = sign_in(env)
    monkeypatch.setattr(
        service, "HANDLERS", {**service.HANDLERS, "home": lambda r: (_ for _ in ()).throw(ConfigError("settle_failed", "x"))}
    )
    r = get(env, "work", "/", {"Cookie": cookie})
    assert r.status == 503 and env.run.shared.stop.wait(2) and env.run.shared.fatal.is_set()


def test_no_broad_catch_in_the_service():
    tree = ast.parse((ROOT / "src" / "intake" / "service.py").read_text(encoding="utf-8"))
    bad = []
    for n in ast.walk(tree):
        if isinstance(n, ast.ExceptHandler) and getattr(n.type, "id", "") in ("Exception", "BaseException"):
            if not (n.type.id == "BaseException" and isinstance(n.body[-1], ast.Raise)):  # a cleanup that re-raises is fine
                bad.append(n.lineno)
    assert not bad, bad


def test_early_errors_and_413_drain_the_body(env, monkeypatch):
    """Closing a socket with unread data can reset the connection and the client loses the reply (m6); a real client on this laptop does not always
    lose it, so the test checks that the drain runs and consumes the declared body (up to the cap)."""
    seen = []
    real = service.Handler._drain

    def spy(self):
        before = self._body_read
        real(self)
        seen.append((self._declared, before, self._body_read))

    monkeypatch.setattr(service.Handler, "_drain", spy)
    cookie, _ = sign_in(env)
    wh, wp = env.work
    h = {
        "Origin": f"http://{wh}:{wp}",
        "Sec-Fetch-Site": "same-origin",
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": cookie,
    }
    assert raw(env.work, build("POST", "/logout", f"{wh}:{wp}", h, b"a" * 9000)).status == 413
    assert raw(env.work, build("POST", "/export", f"{wh}:{wp}", {k: v for k, v in h.items() if k != "Cookie"}, b"a" * 100)).status == 401
    assert seen == [(9000, False, True), (100, False, True)]
