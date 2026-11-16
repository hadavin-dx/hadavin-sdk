"""Sign-in, sessions, clocks, throttle, login CSRF and role rules (brief-v3 15.2). Security path. Clocks are injected: no test sleeps."""

from __future__ import annotations

import ast
import time

import pytest

from conftest import ROOT, settings_for_tests
from intake import access, routes, secret_store, workqueue


class FakeClocks:
    def __init__(self):
        self.m, self.w = 1000.0, 1_700_000_000.0

    def clocks(self):
        return access.Clocks(lambda: self.m, lambda: self.w)

    def advance(self, secs, wall=True):
        self.m += secs
        if wall:
            self.w += secs


AP = access.LOGINS[0]


def must_admit(t):
    """An admit that has to pass: a throttle that bites too early is an assertion failure (not a stray exception)."""
    try:
        t.admit()
    except access.Throttled:
        raise AssertionError("throttled before the limit") from None


def test_logins_validated_at_import():
    for bad in (
        access.Login("system", "approver", "HADAVIN_APPROVER_PASSPHRASE"),
        access.Login("CLI", "approver", "HADAVIN_APPROVER_PASSPHRASE"),
        access.Login("a b", "approver", "HADAVIN_APPROVER_PASSPHRASE"),
        access.Login("ap-a", "root", "HADAVIN_APPROVER_PASSPHRASE"),
        access.Login("ap-a", "approver", "NOT_A_SECRET"),
    ):
        with pytest.raises(ValueError):
            access._validate_logins((bad,))
    with pytest.raises(ValueError):
        access._validate_logins((AP, AP))
    access._validate_logins(access.LOGINS)


def test_equal_secret_behaviour():
    assert access.equal_secret("abc", "abc")
    assert not access.equal_secret("abc", "abd")
    assert not access.equal_secret("abc", "abcd") and not access.equal_secret("abcd", "abc")  # different lengths
    assert not access.equal_secret("", "") and not access.equal_secret("x", "") and not access.equal_secret("", "x")


def test_passphrase_match_and_reread(tmp_path):
    s = settings_for_tests(tmp_path)
    good = "pass" + "P" * 30
    assert access.match_login(s, "ap-a", good) == AP
    assert access.match_login(s, "ap-a", good + " \r\n") == AP  # trailing whitespace is stripped
    assert access.match_login(s, "ap-a", "x" * 2000) is None  # over the cap: refused without a compare
    assert access.match_login(s, "ap-a", "wrong") is None
    path = secret_store.secrets_path(s.local)
    path.write_text(path.read_text().replace(good, "pass" + "Q" * 30), encoding="utf-8")
    assert access.match_login(s, "ap-a", good) is None  # re-read on every call: the old value no longer matches
    assert access.match_login(s, "ap-a", "pass" + "Q" * 30) == AP


def test_passphrase_missing_is_not_configured(tmp_path):
    s = settings_for_tests(tmp_path)
    secret_store.secrets_path(s.local).write_text("OTHER=x\n", encoding="utf-8")
    with pytest.raises(access.NotConfigured):
        access.match_login(s, "ap-a", "whatever")


def test_reserved_and_unknown_names_same_answer(tmp_path, monkeypatch):
    s = settings_for_tests(tmp_path)
    seen = []
    real = access.secrets.compare_digest
    monkeypatch.setattr(access.secrets, "compare_digest", lambda a, b: seen.append(1) or real(a, b))
    for name in ("system", "CLI", "cli", "nobody", ""):
        seen.clear()
        assert access.match_login(s, name, "pass" + "P" * 30) is None
        assert seen, name  # the dummy compare ran: the same work as a real name


def test_step_up_uses_the_logins_own_passphrase(tmp_path):
    s = settings_for_tests(tmp_path)
    sess = access.SessionStore(FakeClocks().clocks()).create(AP)
    assert access.check_step_up(s, sess, "pass" + "P" * 30)
    assert not access.check_step_up(s, sess, "nope")
    ghost = access.Session("x" * 43, "ghost", "approver", "c", sess.created, sess.last_touch)
    assert not access.check_step_up(s, ghost, "pass" + "P" * 30)


def test_throttle_429_no_sleep():
    fc = FakeClocks()
    t = access.Throttle(fc.clocks())
    for _ in range(access.THROTTLE_FAILURES):
        must_admit(t)
        t.failed()
        fc.advance(0.01)
    t0 = time.perf_counter()
    with pytest.raises(access.Throttled):
        t.admit()  # failures filled the window and the last checked attempt was under a second ago
    assert time.perf_counter() - t0 < 0.05
    fc.advance(1.0)
    must_admit(t)  # one attempt per second is checked: never a lock-out
    t.failed()
    fc.advance(0.5)
    with pytest.raises(access.Throttled):
        t.admit()
    fc.advance(61)
    must_admit(t)  # the failures aged out of the window


def test_no_lockout_after_failures():
    fc = FakeClocks()
    t = access.Throttle(fc.clocks())
    for _ in range(100):
        try:
            t.admit()
            t.failed()
        except access.Throttled:
            pass
        fc.advance(0.05)
    fc.advance(1.0)
    must_admit(t)  # the right passphrase gets checked within a second of the last wrong one


def test_step_up_counts_in_throttle():
    # the service passes ONE Throttle to the sign-in and to the export step-up: a failure recorded by either fills the same window
    fc = FakeClocks()
    t = access.Throttle(fc.clocks())
    for _ in range(access.THROTTLE_FAILURES):
        must_admit(t)
        t.failed()
    with pytest.raises(access.Throttled):
        t.admit()


def test_session_ids_fresh_and_strong():
    st = access.SessionStore(FakeClocks().clocks())
    a, b = st.create(AP), st.create(AP)
    assert a.sid != b.sid and a.csrf != b.csrf and a.sid != a.csrf
    assert len(a.sid) == 43 and access._ID_RE.fullmatch(a.sid)


def test_session_rotation_and_client_sid_never_adopted():
    st = access.SessionStore(FakeClocks().clocks())
    old = st.create(AP)
    new = st.create(AP, replacing=old.sid)
    assert st.get(old.sid, touch=False) is None and st.get(new.sid, touch=False) is not None
    assert st.get("A" * 43, touch=True) is None  # a client-chosen id is never adopted
    assert new.sid != "A" * 43


def test_create_refuses_reserved_names():
    st = access.SessionStore(FakeClocks().clocks())
    for n in ("system", "Cli"):
        with pytest.raises(ValueError):
            st.create(access.Login(n, "approver", "HADAVIN_APPROVER_PASSPHRASE"))


def test_session_idle_expiry():
    fc = FakeClocks()
    st = access.SessionStore(fc.clocks())
    sess = st.create(AP)
    fc.advance(access.LIMIT_SESSION_IDLE_S - 1)
    assert st.get(sess.sid, touch=True)
    fc.advance(access.LIMIT_SESSION_IDLE_S - 1)
    assert st.get(sess.sid, touch=True)  # touching kept it alive
    fc.advance(access.LIMIT_SESSION_IDLE_S + 1)
    assert st.get(sess.sid, touch=True) is None and st.get(sess.sid, touch=False) is None  # idle: and the entry was deleted


def test_session_absolute_expiry():
    fc = FakeClocks()
    st = access.SessionStore(fc.clocks())
    sess = st.create(AP)
    for _ in range(28):  # 28000 s, each step well under the idle limit: kept busy
        fc.advance(1000)
        assert st.get(sess.sid, touch=True)
    fc.advance(1000)  # 29000 s since sign-in, but only 1000 s idle: only the absolute limit can end it
    assert st.get(sess.sid, touch=True) is None


def test_poll_does_not_refresh_idle():
    fc = FakeClocks()
    st = access.SessionStore(fc.clocks())
    sess = st.create(AP)
    for _ in range(5):
        fc.advance(access.LIMIT_SESSION_IDLE_S // 3)
        if st.get(sess.sid, touch=False) is None:
            break
    assert st.get(sess.sid, touch=False) is None  # five polls never kept it alive


def test_session_expires_across_sleep():
    fc = FakeClocks()
    st = access.SessionStore(fc.clocks())
    sess = st.create(AP)
    fc.w += 12 * 3600  # the lid was closed: the monotonic clock is frozen, the wall clock moved on
    assert st.get(sess.sid, touch=True) is None


def test_wall_clock_backwards_expires():
    fc = FakeClocks()
    st = access.SessionStore(fc.clocks())
    sess = st.create(AP)
    fc.m += 10
    fc.w -= 1
    assert st.get(sess.sid, touch=True) is None


def test_age_over_rule():
    a = access.Stamp(0.0, 100.0)
    assert not access.age_over(a, access.Stamp(5, 105), 10)
    assert access.age_over(a, access.Stamp(11, 105), 10)  # monotonic alone
    assert access.age_over(a, access.Stamp(5, 111), 10)  # wall alone
    assert access.age_over(a, access.Stamp(5, 99.9), 10)  # wall moved backwards


def test_pre_session_issue_always_new_and_one_use():
    pre = access.PreSessions(FakeClocks().clocks())
    a, b = pre.issue(), pre.issue()
    assert a[0] != b[0] and a[1] != b[1]
    assert pre.redeem(a[0], a[1]) is True
    assert pre.redeem(a[0], a[1]) is False  # one use
    assert pre.redeem(b[0], "wrong") is False
    assert pre.redeem(b[0], b[1]) is False  # a failed attempt also deleted it
    c = pre.issue()
    assert pre.redeem(c[0], b[1]) is False  # a token of another pre-session
    assert pre.redeem(None, "x") is False and pre.redeem("x", None) is False


def test_pre_session_map_capped_and_expires():
    fc = FakeClocks()
    pre = access.PreSessions(fc.clocks())
    first = pre.issue()
    for _ in range(access.LIMIT_PRE_SESSIONS):
        pre.issue()
    assert len(pre._by_id) == access.LIMIT_PRE_SESSIONS
    assert pre.redeem(*first) is False  # the oldest went when the map was full
    exp = pre.issue()
    fc.advance(access.LIMIT_PRE_SESSION_S + 1)
    assert pre.redeem(*exp) is False  # expired
    fresh = pre.issue()
    assert len(pre._by_id) == 1 and pre.redeem(*fresh)  # expired entries go first


def test_csrf_bound_to_session_and_valid_in_two_tabs():
    st = access.SessionStore(FakeClocks().clocks())
    a, b = st.create(AP), st.create(AP)
    assert access.csrf_ok(a, a.csrf) and not access.csrf_ok(a, b.csrf) and not access.csrf_ok(a, None) and not access.csrf_ok(a, "")
    assert access.csrf_ok(a, a.csrf)  # valid again in a second tab of the same session


def test_logout_ends_all_sessions_of_login():
    st = access.SessionStore(FakeClocks().clocks())
    a, b = st.create(AP), st.create(AP)
    st.end_all("ap-a")
    assert st.get(a.sid, touch=False) is None and st.get(b.sid, touch=False) is None


def test_cookie_value_exactly_one_and_grammar():
    v = "A" * 43
    assert access.cookie_value(f"x=1; {access.COOKIE_SESSION}={v}", access.COOKIE_SESSION) == v
    assert access.cookie_value(f"{access.COOKIE_SESSION}={v}; {access.COOKIE_SESSION}={v}", access.COOKIE_SESSION) is None
    assert access.cookie_value(f"{access.COOKIE_SESSION}={'A' * 42}", access.COOKIE_SESSION) is None
    assert access.cookie_value(f'{access.COOKIE_SESSION}="{v}"', access.COOKIE_SESSION) is None
    assert access.cookie_value("garbage", access.COOKIE_SESSION) is None and access.cookie_value(None, "x") is None


def test_cookie_flags():
    v = "B" * 43
    c = access.set_cookie(access.COOKIE_SESSION, v)
    assert c == f"__Host-intake_session={v}; Secure; HttpOnly; SameSite=Strict; Path=/"
    assert "Domain" not in c and "Max-Age" not in c
    assert access.set_cookie(access.COOKIE_PRE, v, max_age=600).endswith("; Max-Age=600")
    cl = access.clear_cookie(access.COOKIE_SESSION)
    assert (
        cl.startswith("__Host-intake_session=;") and "Max-Age=0" in cl and "Secure" in cl and "HttpOnly" in cl and "SameSite=Strict" in cl
    )
    assert "Clear-Site-Data" not in cl
    with pytest.raises(ValueError):
        access.set_cookie("x", "a;b")


HOSTS = {"token": "127.0.0.1", "work": "127.0.0.11", "dash": "127.0.0.12"}


@pytest.mark.parametrize(
    "app,values,ok",
    [
        ("work", ["127.0.0.11:8750"], True),
        ("work", ["localhost:8750"], False),
        ("work", ["[::1]:8750"], False),
        ("work", ["0.0.0.0:8750"], False),
        ("work", ["127.0.0.12:8750"], False),
        ("work", ["example.com:8750"], False),
        ("work", [], False),
        ("work", ["127.0.0.11:8750", "127.0.0.11:8750"], False),
        ("work", [" 127.0.0.11:8750"], False),
        ("work", ["127.0.0.11:8750 "], False),
        ("work", ["127.0.0.11:8750,127.0.0.11:8750"], False),
        ("work", ["127.0.0.11.:8750"], False),
        ("work", ["127.0.0.11:8751"], False),
        ("work", ["127.0.0.11"], False),
        ("work", ["host.docker.internal:8750"], False),
        ("dash", ["127.0.0.12:8750"], True),
        ("dash", ["127.0.0.11:8750"], False),
        ("token", ["127.0.0.1:8750"], True),
        ("token", ["host.docker.internal:8750"], True),
        ("token", ["HOST.Docker.Internal:8750"], True),
        ("token", ["localhost:8750"], False),
        ("token", ["host.docker.internal:8751"], False),
    ],
)
def test_host_per_listener_unit(app, values, ok):
    assert access.host_ok(app, values, 8750, HOSTS) is ok


def test_origin_rules():
    good = "http://127.0.0.11:8750"

    def f(o, sf):
        return access.origin_ok(o, sf, 8750, "127.0.0.11")

    assert f([good], ["same-origin"])
    for o in (
        [],
        ["null"],
        ["https://127.0.0.11:8750"],
        ["http://127.0.0.11:8750.evil"],
        ["http://127.0.0.11:8751"],
        [good, good],
        ["http://localhost:8750"],
    ):
        assert not f(o, ["same-origin"]), o
    for sf in ([], ["same-site"], ["cross-site"], ["none"], ["same-origin", "same-origin"], ["Same-Origin"]):
        assert not f([good], sf), sf


def test_allowed_default_deny_and_require_role():
    st = access.SessionStore(FakeClocks().clocks())
    ap = st.create(AP)
    vw = st.create(access.Login("vw-1", "viewer", "HADAVIN_APPROVER_PASSPHRASE"))
    nobody = routes.Route("x", "GET", "/x", frozenset(), "work", "session")
    assert not access.allowed(nobody, ap) and not access.allowed(nobody, vw) and not access.allowed(nobody, None)
    assert not access.allowed(routes.route("home"), None) and access.allowed(routes.route("home"), vw)
    assert access.allowed(routes.route("login"), None)
    assert not access.allowed(routes.route("scan"), ap)  # a token row is never a session row
    assert access.allowed(routes.route("decide"), ap) and not access.allowed(routes.route("decide"), vw)
    access.require_role(ap, "approver")
    for who in (vw, None):
        with pytest.raises(access.Denied) as e:
            access.require_role(who, "approver")
        assert e.value.code == "role_denied"


def test_session_store_threads():
    import threading

    st = access.SessionStore()
    out = []

    def work():
        for _ in range(50):
            s = st.create(AP)
            out.append(st.get(s.sid, touch=True) is not None)
            st.end(s.sid)

    ts = [threading.Thread(target=work) for _ in range(8)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert len(out) == 400 and all(out) and not st._by_sid


def test_repr_hides_secrets():
    sess = access.SessionStore(FakeClocks().clocks()).create(AP)
    assert sess.sid not in repr(sess) and sess.csrf not in repr(sess)


def test_compare_digest_only_ast():
    # no ``==`` / ``!=`` between a passphrase, token, CSRF or pre-session value and anything but a short public literal in access.py or service.py
    secret_words = {"passphrase", "token", "csrf", "expected", "given", "pre_id", "stored", "tok"}
    for path in ("src/intake/access.py", "src/intake/service.py"):
        tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            if isinstance(n, ast.Compare) and any(isinstance(o, (ast.Eq, ast.NotEq)) for o in n.ops):
                names = {x.id for x in ast.walk(n) if isinstance(x, ast.Name)} | {
                    x.attr for x in ast.walk(n) if isinstance(x, ast.Attribute)
                }
                assert not (names & secret_words), (path, n.lineno, names & secret_words)


def test_session_clocks_fixed_ast():
    # product code builds SessionStore/PreSessions/Throttle/Clocks with no argument; only tests pass fakes
    for p in (ROOT / "src" / "intake").glob("*.py"):
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, (ast.Name, ast.Attribute)):
                nm = n.func.id if isinstance(n.func, ast.Name) else n.func.attr
                if nm in ("SessionStore", "PreSessions", "Throttle", "Clocks"):
                    assert not n.args and not n.keywords, (p.name, n.lineno)


def test_actor_grammar_matches_workqueue():
    assert workqueue.ACTOR_RE.fullmatch("ap-a")
