"""More access rules: tests adopted from the independent build of access.py (the comparison file of the second access build, section B) and the part A review
of package 6d. Adopted: reserved/unknown-name reads, missing and malformed secrets, no cause on NotConfigured, length cap, leading whitespace, extended login
validation, equal_secret edge cases, throttle below the limit and in flight, exact-limit expiry, both-direction sleep, last_touch after a poll, cookie grammar and
names, exact cookie strings, host and origin extra forms, the real route table, require_role with a foreign role, either-clock pre-session expiry, oldest-first
cap, end_all keeping other logins, repr hiding, and the sweep of expired sessions. Not adopted: nothing was found wrong; a few 6a cases duplicate tests already
in test_access.py (absolute expiry steps, cookie flags)."""

from __future__ import annotations

import ast

import pytest
from test_access import AP, HOSTS, FakeClocks, must_admit

from conftest import ROOT, settings_for_tests
from intake import access, routes, secret_store


def _spy(monkeypatch):
    log = {"compare": 0, "read": 0}
    real_c, real_g = access.secrets.compare_digest, access.secret_store.get
    monkeypatch.setattr(access.secrets, "compare_digest", lambda a, b: log.__setitem__("compare", log["compare"] + 1) or real_c(a, b))
    monkeypatch.setattr(access.secret_store, "get", lambda *a, **k: log.__setitem__("read", log["read"] + 1) or real_g(*a, **k))
    return log


def test_every_name_does_one_compare_and_one_read(tmp_path, monkeypatch):
    s = settings_for_tests(tmp_path)
    good = "pass" + "P" * 30
    log = _spy(monkeypatch)
    for name in ("ap-a", "system", "SYSTEM", "cli", "nobody", ""):
        log.update(compare=0, read=0)
        got = access.match_login(s, name, good)
        assert (got is not None) == (name == "ap-a")  # even the right passphrase for a reserved name is refused
        assert (log["compare"], log["read"]) == (1, 1), name


def test_missing_secret_is_503_for_every_name_not_only_the_real_one(tmp_path):
    s = settings_for_tests(tmp_path)
    secret_store.secrets_path(s.local).write_text("OTHER=x\n", encoding="utf-8")
    for name in ("ap-a", "nobody", "system", "CLI"):
        with pytest.raises(access.NotConfigured):
            access.match_login(s, name, "whatever")  # no name oracle on the configuration state
    sess = access.SessionStore(FakeClocks().clocks()).create(AP)
    with pytest.raises(access.NotConfigured):
        access.check_step_up(s, sess, "whatever")


def test_malformed_secret_is_not_configured_and_carries_no_detail(tmp_path):
    s = settings_for_tests(tmp_path)
    path = secret_store.secrets_path(s.local)
    path.write_text("HADAVIN_APPROVER_PASSPHRASE=short\n", encoding="utf-8")  # shorter than the 24-character minimum
    with pytest.raises(access.NotConfigured) as e:
        access.match_login(s, "ap-a", "short")
    assert e.value.__cause__ is None and e.value.args == () and "HADAVIN" not in repr(e.value)


def test_an_over_long_passphrase_is_refused_even_if_it_equals_the_secret(tmp_path):
    s = settings_for_tests(tmp_path)
    long_secret = "L" * (access.LIMIT_PASSPHRASE_CHARS + 1)
    secret_store.secrets_path(s.local).write_text(f"HADAVIN_APPROVER_PASSPHRASE={long_secret}\n", encoding="utf-8")
    assert access.match_login(s, "ap-a", long_secret) is None  # over the cap it is never accepted
    sess = access.SessionStore(FakeClocks().clocks()).create(AP)
    assert access.check_step_up(s, sess, long_secret) is False
    short = "S" * access.LIMIT_PASSPHRASE_CHARS
    secret_store.secrets_path(s.local).write_text(f"HADAVIN_APPROVER_PASSPHRASE={short}\n", encoding="utf-8")
    assert access.match_login(s, "ap-a", short) == AP  # exactly at the cap it is accepted


def test_a_missing_secret_answers_the_same_for_every_passphrase(tmp_path):
    s = settings_for_tests(tmp_path)
    secret_store.secrets_path(s.local).write_text("OTHER=x\n", encoding="utf-8")
    sess = access.SessionStore(FakeClocks().clocks()).create(AP)
    for pw in ("", " ", "x" * (access.LIMIT_PASSPHRASE_CHARS + 1), "normal-passphrase-of-some-length"):
        with pytest.raises(access.NotConfigured):
            access.match_login(s, "ap-a", pw)  # 503 for an empty and an over-long one too, not a 401 that tells them apart
        with pytest.raises(access.NotConfigured):
            access.check_step_up(s, sess, pw)


def test_every_passphrase_does_one_read_and_one_compare(tmp_path, monkeypatch):
    s = settings_for_tests(tmp_path)
    log = _spy(monkeypatch)
    sess = access.SessionStore(FakeClocks().clocks()).create(AP)
    for pw in ("", "   ", "x" * (access.LIMIT_PASSPHRASE_CHARS + 1), "pass" + "P" * 30, "wrong"):
        log.update(compare=0, read=0)
        access.match_login(s, "ap-a", pw)
        assert (log["compare"], log["read"]) == (1, 1), repr(pw[:5])
        log.update(compare=0, read=0)
        access.check_step_up(s, sess, pw)
        assert (log["compare"], log["read"]) == (1, 1), repr(pw[:5])


def test_the_failure_window_is_sixty_seconds():
    for age, throttled in ((30, True), (60, True), (60.5, False), (61, False)):
        fc = FakeClocks()
        t = access.Throttle(fc.clocks())
        for _ in range(access.THROTTLE_FAILURES):
            must_admit(t)
            t.failed()
        fc.advance(age)
        must_admit(t)  # a long time since the last check: always allowed
        t.passed()
        if throttled:
            with pytest.raises(access.Throttled):
                t.admit()  # straight away again: the failures still count inside the window
        else:
            must_admit(t)  # the failures aged out: no second check is refused


def test_failures_are_trimmed_when_recorded_too():
    fc = FakeClocks()
    t = access.Throttle(fc.clocks())
    for _ in range(access.THROTTLE_FAILURES):
        must_admit(t)
        t.failed()
    fc.advance(access.THROTTLE_WINDOW_S + 1)
    t.failed()  # recording one failure trims the old five (no admit in between: admit trims too)
    assert len(t._failures) == 1


def test_an_old_session_is_swept_at_create_by_the_absolute_limit_too():
    fc = FakeClocks()
    st = access.SessionStore(fc.clocks())
    old = st.create(AP)
    for _ in range(28):  # kept busy: never idle for long
        fc.advance(1000)
        assert st.get(old.sid, touch=True)
    fc.advance(1000)  # 29000 s since sign-in, 1000 s idle: only the absolute limit applies
    st.create(AP)
    assert old.sid not in st._by_sid


def test_only_trailing_space_cr_lf_are_stripped(tmp_path):
    s = settings_for_tests(tmp_path)
    good = "pass" + "P" * 30
    assert access.match_login(s, "ap-a", good + "\r\n  ") == AP
    for bad in (" " + good, "\t" + good, good + "\t", good + "\x00"):
        assert access.match_login(s, "ap-a", bad) is None, repr(bad)


def test_logins_validation_extended():
    for name in ("", "-x", "Cli", "SYSTEM", "a" * 65, "a b"):
        with pytest.raises(ValueError):
            access._validate_logins((access.Login(name, "approver", "HADAVIN_APPROVER_PASSPHRASE"),))
    with pytest.raises(ValueError):
        access._validate_logins((AP, access.Login("AP-A", "viewer", "HADAVIN_APPROVER_PASSPHRASE")))  # a duplicate in another case
    st = access.SessionStore(FakeClocks().clocks())
    for n in ("system", "SYSTEM", "cli"):
        with pytest.raises(ValueError):
            st.create(access.Login(n, "approver", "HADAVIN_APPROVER_PASSPHRASE"))


def test_equal_secret_edges():
    assert access.equal_secret("abc", "abc") is True and access.equal_secret("abc", "abd") is False
    assert access.equal_secret("x" * 5000, "x") is False and access.equal_secret("é" * 30, "é" * 30) is True
    assert access.equal_secret("a\ud800b", "a\ud800b") is True  # a lone surrogate does not raise
    assert access.equal_secret(None, "x") is False and access.equal_secret("x", None) is False


def test_four_failures_never_throttle_and_the_fifth_does_within_the_gap():
    fc = FakeClocks()
    t = access.Throttle(fc.clocks())
    for _ in range(access.THROTTLE_FAILURES - 1):
        for _ in range(10):
            must_admit(t)
            t.passed()
        must_admit(t)
        t.failed()
    for _ in range(10):
        must_admit(t)  # four failures: free
        t.passed()
    must_admit(t)
    t.failed()  # the fifth
    with pytest.raises(access.Throttled):
        t.admit()
    fc.advance(access.THROTTLE_GAP_S)
    must_admit(t)  # exactly one second later it is checked again
    t.passed()


def test_parallel_attempts_reserve_a_slot_before_the_first_failure_is_recorded():
    fc = FakeClocks()
    t = access.Throttle(fc.clocks())
    admitted = 0
    throttled = 0
    for _ in range(16):  # sixteen guesses in flight at once: none has failed yet
        try:
            t.admit()
            admitted += 1
        except access.Throttled:
            throttled += 1
    assert admitted == access.THROTTLE_FAILURES and throttled == 16 - access.THROTTLE_FAILURES
    for _ in range(admitted):
        t.passed()
    must_admit(t)  # slots given back: not locked out


def test_exactly_at_the_limit_is_still_valid():
    fc = FakeClocks()
    st = access.SessionStore(fc.clocks())
    sess = st.create(AP)
    fc.advance(access.LIMIT_SESSION_IDLE_S)
    assert st.get(sess.sid, touch=False)  # "over" the limit expires, "at" it does not
    fc.advance(1)
    assert st.get(sess.sid, touch=False) is None
    a = access.Stamp(0.0, 100.0)
    assert not access.age_over(a, access.Stamp(10, 100), 10) and not access.age_over(a, access.Stamp(0, 110), 10)


def test_poll_leaves_last_touch_and_a_touch_sets_it():
    fc = FakeClocks()
    st = access.SessionStore(fc.clocks())
    sess = st.create(AP)
    fc.advance(100)
    assert st.get(sess.sid, touch=False).last_touch == sess.last_touch
    got = st.get(sess.sid, touch=True)
    assert got.last_touch.mono == fc.m and got.created == sess.created


def test_sleep_expires_in_both_directions():
    fc = FakeClocks()
    st = access.SessionStore(fc.clocks())
    sess = st.create(AP)
    fc.m += access.LIMIT_SESSION_IDLE_S + 1  # the wall clock stood still (it was set back to where it was)
    assert st.get(sess.sid, touch=True) is None


def test_expired_sessions_are_swept_at_create():
    fc = FakeClocks()
    st = access.SessionStore(fc.clocks())
    old = st.create(AP)
    fc.advance(access.LIMIT_SESSION_IDLE_S + 5)
    st.create(AP)
    assert old.sid not in st._by_sid


def test_end_all_keeps_the_sessions_of_other_logins():
    st = access.SessionStore(FakeClocks().clocks())
    a = st.create(AP)
    v = st.create(access.Login("vw-1", "viewer", "HADAVIN_APPROVER_PASSPHRASE"))
    st.end_all("ap-a")
    st.end(None)
    st.end("nope")
    assert st.get(a.sid, touch=False) is None and st.get(v.sid, touch=False) is not None


def test_pre_session_expires_on_either_clock_alone():
    for which in ("m", "w"):
        fc = FakeClocks()
        pre = access.PreSessions(fc.clocks())
        ok = pre.issue()
        setattr(fc, which, getattr(fc, which) + access.LIMIT_PRE_SESSION_S)
        assert pre.redeem(*ok) is True  # exactly at the limit
        late = pre.issue()
        setattr(fc, which, getattr(fc, which) + access.LIMIT_PRE_SESSION_S + 1)
        assert pre.redeem(*late) is False, which


def test_a_full_map_drops_the_oldest_first():
    pre = access.PreSessions(FakeClocks().clocks())
    first = [pre.issue() for _ in range(access.LIMIT_PRE_SESSIONS)]
    pre.issue()
    assert pre.redeem(*first[0]) is False and pre.redeem(*first[1]) is True


def test_cookie_value_variants():
    v, w = "A" * 43, "B" * 43
    n = access.COOKIE_SESSION
    assert access.cookie_value(f"{n}={v}; {n}={w}", n) is None  # two different values
    assert access.cookie_value(f"x{n}={v}; {n}x={v}", n) is None  # names that only contain it
    assert access.cookie_value(f"{access.COOKIE_PRE}={v}", n) is None
    assert access.cookie_value(f"{n}={v}; =x", n) is None and access.cookie_value(f"{n}={v}; junk", n) is None
    assert access.cookie_value(f"{n}={v}; é=1", n) is None and access.cookie_value("", n) is None
    assert access.cookie_value(f"{n}={v}", n) == v


def test_cookie_names_and_values_are_closed():
    for bad in ("", "a" * 42, "a" * 44, "a b" + "c" * 40, "a=" + "c" * 41, "a\n" + "c" * 41):
        with pytest.raises(ValueError):
            access.set_cookie(access.COOKIE_SESSION, bad)
    with pytest.raises(ValueError):
        access.set_cookie("other", "A" * 43)
    with pytest.raises(ValueError):
        access.clear_cookie("other")
    v = "C" * 43
    assert (
        access.set_cookie(access.COOKIE_PRE, v, max_age=600)
        == f"__Host-intake_pre={v}; Secure; HttpOnly; SameSite=Strict; Path=/; Max-Age=600"
    )
    assert access.clear_cookie(access.COOKIE_PRE) == "__Host-intake_pre=; Secure; HttpOnly; SameSite=Strict; Path=/; Max-Age=0"


@pytest.mark.parametrize(
    "app,value,ok",
    [
        ("work", "127.0.0.11:08750", False),
        ("work", "127.0.0.11:8750:1", False),
        ("work", "127.0.0.11:8750\x00", False),
        ("work", "LOCALHOST:8750", False),
        ("work", "", False),
        ("dash", "127.0.0.1:8750", False),
        ("token", "127.0.0.12:8750", False),
        ("nope", "127.0.0.11:8750", False),
    ],
)
def test_host_extra_forms(app, value, ok):
    assert access.host_ok(app, [value], 8750, HOSTS) is ok


def test_origin_extra_forms():
    good = "http://127.0.0.11:8750"

    def f(o, sf):
        return access.origin_ok(o, sf, 8750, "127.0.0.11")

    for o in ([good + "/"], ["HTTP://127.0.0.11:8750"], ["http://127.0.0.12:8750"], [good, "null"]):
        assert not f(o, ["same-origin"]), o
    assert not f([good], ["same-origin", "cross-site"])


def test_allowed_over_the_real_route_table():
    st = access.SessionStore(FakeClocks().clocks())
    ap = st.create(AP)
    vw = st.create(access.Login("vw-1", "viewer", "HADAVIN_APPROVER_PASSPHRASE"))
    odd = access.Session("z" * 43, "ap-a", "root", "c", ap.created, ap.last_touch)
    for r in routes.ROUTE_TABLE:
        want_ap = r.family != "token"
        assert access.allowed(r, ap) is want_ap, r.name
        assert access.allowed(r, vw) is (r.family == "login" or (r.family == "session" and "viewer" in r.roles)), r.name
        assert access.allowed(r, None) is (r.family == "login"), r.name
        assert access.allowed(r, odd) is (r.family == "login"), r.name
    mixed = routes.Route("m", "GET", "/m", frozenset({routes.APPROVER, routes.TOKEN_HOLDER}), "work", "session")
    assert not access.allowed(mixed, ap)  # a row that lists the token holder is never opened by a session
    with pytest.raises(access.Denied):
        access.require_role(ap, "root")
    with pytest.raises(access.Denied):
        access.require_role(ap, "")


def test_repr_hides_more():
    assert "pass" + "P" * 30 not in repr(access.Throttle()) + repr(AP) + repr(access.Denied("role_denied"))


def test_watched_names_in_the_compare_scan():
    secret_words = {"sid", "secret", "passphrase", "token", "csrf", "expected", "given", "pre_id", "stored"}
    for path in ("src/intake/access.py", "src/intake/service.py"):
        for n in ast.walk(ast.parse((ROOT / path).read_text(encoding="utf-8"))):
            if isinstance(n, ast.Compare) and any(isinstance(o, (ast.Eq, ast.NotEq)) for o in n.ops):
                names = {x.id for x in ast.walk(n) if isinstance(x, ast.Name)}
                assert not (names & secret_words), (path, n.lineno)


def test_stamps_are_taken_under_the_lock():
    """A stamp taken before the lock can be OLDER than one another thread stored a moment earlier; the sweep would then read a fresh session as coming
    from the future (wall clock moved backwards) and end it. Every stamp that SessionStore.create/get and PreSessions.issue compare with stored ones is
    taken while the lock is held (PreSessions.redeem stamps outside its lock: it compares with one entry it already removed, so that is harmless)."""
    seen = []
    holder = {}

    def tick():
        seen.append(holder["store"]._lock.locked())
        return 1.0

    clocks = access.Clocks(tick, tick)
    holder["store"] = sessions = access.SessionStore(clocks)
    sess = sessions.create(AP)
    sessions.get(sess.sid, touch=True)
    sessions.get(sess.sid, touch=False)
    holder["store"] = pre = access.PreSessions(clocks)
    pre.issue()
    assert len(seen) >= 8 and all(seen), seen
