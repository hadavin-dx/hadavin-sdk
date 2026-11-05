"""Sign-in, sessions, expiry, throttle, login CSRF and role checks (brief-v3 4.2, 6). Security path: no review-round cap. The lead gave these bodies to
package 6d (6a is the inbox scan in this build). Every secret compare goes through ``equal_secret``; no ``==`` on a passphrase, token, CSRF or
pre-session value (AST test ``compare_digest_only``)."""

from __future__ import annotations

import hashlib
import re
import secrets
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace

from . import secret_store, workqueue
from .codes import SecretError
from .routes import ANYONE, APPROVER, ROLES, TOKEN_HOLDER, Route
from .settings import Settings

LIMIT_SESSION_IDLE_S = 1800
LIMIT_SESSION_ABS_S = 28800  # W-7, M2
LIMIT_PRE_SESSIONS = 64
LIMIT_PRE_SESSION_S = 600  # W-6
THROTTLE_FAILURES = 5
THROTTLE_WINDOW_S = 60
THROTTLE_GAP_S = 1  # W-5
LIMIT_PASSPHRASE_CHARS = 1024
COOKIE_SESSION = "__Host-intake_session"
COOKIE_PRE = "__Host-intake_pre"  # W-4, W-6
_ID_RE = re.compile(r"[A-Za-z0-9_-]{43}")  # secrets.token_urlsafe(32)
_HOST_DOCKER = "host.docker.internal"


@dataclass(frozen=True)
class Clocks:
    """Both clocks, always together (M-B). Product code uses ``Clocks()``; only tests pass others."""

    mono: Callable[[], float] = time.monotonic  # may pause while the laptop sleeps
    wall: Callable[[], float] = time.time  # keeps running across sleep; can jump

    def stamp(self) -> Stamp:
        return Stamp(self.mono(), self.wall())


@dataclass(frozen=True)
class Stamp:
    """One point in time on both clocks."""

    mono: float
    wall: float


def age_over(start: Stamp, now: Stamp, limit_s: float) -> bool:
    """THE expiry rule: True when ``now.mono - start.mono > limit_s``, OR ``now.wall - start.wall > limit_s``, OR ``now.wall < start.wall``."""
    return now.mono - start.mono > limit_s or now.wall - start.wall > limit_s or now.wall < start.wall


@dataclass(frozen=True)
class Login:
    name: str
    role: str
    secret_name: str


def _validate_logins(logins: tuple[Login, ...]) -> None:
    seen: set[str] = set()
    for lg in logins:
        if not workqueue.ACTOR_RE.fullmatch(lg.name) or lg.name.casefold() in workqueue.RESERVED_ACTORS:
            raise ValueError("bad login name")
        if lg.role not in ROLES or lg.secret_name not in secret_store.NAMES or lg.name.casefold() in seen:
            raise ValueError("bad login")
        seen.add(lg.name.casefold())


LOGINS: tuple[Login, ...] = (Login("ap-a", APPROVER, secret_store.APPROVER_PASSPHRASE),)
_validate_logins(LOGINS)


@dataclass(frozen=True)
class Session:
    sid: str = field(repr=False)
    login_name: str
    role: str
    csrf: str = field(repr=False)
    created: Stamp
    last_touch: Stamp


class Denied(Exception):  # noqa: N818 (name fixed by the brief)
    """A refused request; ``code`` is one of ``role_denied``, ``csrf_failed``, ``bad_origin``, ``token_not_allowed``."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class NotConfigured(Exception):  # noqa: N818 (name fixed by the brief)
    """A needed secret is missing or malformed: 503 ``not_configured``."""


class Throttled(Exception):  # noqa: N818 (name fixed by the brief)
    """429 ``too_many_attempts`` with ``Retry-After: 1``."""


def _digest(v: str) -> bytes:
    return hashlib.sha256(v.encode("utf-8", "surrogatepass")).digest()


def equal_secret(given: str, expected: str) -> bool:
    """THE constant-time compare (errata 51.4): False at once if either is empty; else ``secrets.compare_digest`` of the two SHA-256 digests."""
    if not isinstance(given, str) or not isinstance(expected, str) or not given or not expected:
        return False
    return secrets.compare_digest(_digest(given), _digest(expected))


_DUMMY = _digest("dummy-passphrase-for-unknown-names")


def _clean_passphrase(v: str) -> str | None:
    """Trailing ASCII spaces, CR and LF are stripped (no valid value ends in whitespace); over the length cap = None (refused without a compare)."""
    if not isinstance(v, str) or len(v) > LIMIT_PASSPHRASE_CHARS:
        return None
    return v.rstrip(" \r\n")


def _expected(s: Settings, login: Login) -> str:
    try:
        return secret_store.get(login.secret_name, local=s.local)  # re-read on every attempt, dropped after the compare
    except SecretError:
        raise NotConfigured from None


def match_login(s: Settings, name: str, passphrase: str) -> Login | None:
    """The caller has already called ``Throttle.admit``. Every call does the same work whatever the name and the passphrase (a known, unknown or reserved
    name; a normal, empty or over-long passphrase): ONE read of the secret (a missing secret is ``NotConfigured`` for all of them) and ONE digest compare."""
    given = _clean_passphrase(passphrase)  # None = over the length cap
    login = next((lg for lg in LOGINS if isinstance(name, str) and lg.name == name), None)
    real = login is not None and name.casefold() not in workqueue.RESERVED_ACTORS
    expected = _expected(s, login if real else LOGINS[0])
    same = secrets.compare_digest(_digest(given or ""), _digest(expected) if real else _DUMMY)
    return login if real and same and given and expected else None


def check_step_up(s: Settings, session: Session, passphrase: str) -> bool:
    """W-17: the signed-in login's own passphrase, same work as ``match_login`` (one read, one compare); the caller admits through the same ``Throttle``
    first."""
    given = _clean_passphrase(passphrase)
    login = next((lg for lg in LOGINS if lg.name == session.login_name), None)
    expected = _expected(s, login or LOGINS[0])
    same = secrets.compare_digest(_digest(given or ""), _digest(expected))
    return bool(login and same and given and expected)


class Throttle:
    """One per server; monotonic clock only (a pause while asleep only makes it stricter)."""

    def __init__(self, clocks: Clocks = Clocks()) -> None:  # noqa: B008 (a frozen value)
        self._clock = clocks.mono
        self._lock = threading.Lock()
        self._failures: list[float] = []
        self._last_checked: float | None = None
        self._in_flight = 0  # attempts admitted and not yet settled by ``failed`` or ``passed``

    def _trim(self, now: float) -> None:
        self._failures = [t for t in self._failures if now - t <= THROTTLE_WINDOW_S]

    def admit(self) -> None:
        """Raises ``Throttled`` when failures plus attempts still being checked reach ``THROTTLE_FAILURES`` within ``THROTTLE_WINDOW_S`` and the last
        checked attempt was under ``THROTTLE_GAP_S`` ago; never sleeps. An admitted attempt holds a slot until the caller settles it with ``failed`` or
        ``passed``, so parallel wrong guesses cannot all slip in before the first failure is recorded. (Brief 4.2 says "more than", section 6 says
        "after 5": the stricter reading is used.)"""
        with self._lock:
            now = self._clock()
            self._trim(now)
            if (
                len(self._failures) + self._in_flight >= THROTTLE_FAILURES
                and self._last_checked is not None
                and now - self._last_checked < THROTTLE_GAP_S
            ):
                raise Throttled
            self._last_checked = now
            self._in_flight += 1

    def failed(self) -> None:
        """The admitted attempt was a wrong guess."""
        with self._lock:
            self._in_flight = max(0, self._in_flight - 1)
            self._trim(self._clock())
            self._failures.append(self._clock())

    def passed(self) -> None:
        """The admitted attempt was not a wrong guess (right passphrase, or it stopped before the passphrase was compared)."""
        with self._lock:
            self._in_flight = max(0, self._in_flight - 1)


class SessionStore:
    """One per server."""

    def __init__(self, clocks: Clocks = Clocks()) -> None:  # noqa: B008 (a frozen value)
        self._clocks = clocks
        self._lock = threading.Lock()
        self._by_sid: dict[str, Session] = {}

    def create(self, login: Login, *, replacing: str | None = None) -> Session:
        if not workqueue.ACTOR_RE.fullmatch(login.name) or login.name.casefold() in workqueue.RESERVED_ACTORS or login.role not in ROLES:
            raise ValueError("refused login")
        sid, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        with self._lock:
            # taken UNDER the lock: stamps of different threads are then ordered, so a fresh session is never "from the future"
            now = self._clocks.stamp()
            sess = Session(sid, login.name, login.role, csrf, now, now)
            for k in [
                k
                for k, v in self._by_sid.items()
                if age_over(v.last_touch, now, LIMIT_SESSION_IDLE_S) or age_over(v.created, now, LIMIT_SESSION_ABS_S)
            ]:
                del self._by_sid[k]  # expired sessions are swept, not kept until somebody looks them up
            if replacing is not None:
                self._by_sid.pop(replacing, None)  # rotation: the presented session ends at sign-in
            self._by_sid[sess.sid] = sess
        return sess

    def get(self, sid: str | None, *, touch: bool) -> Session | None:
        if not isinstance(sid, str) or not _ID_RE.fullmatch(sid):
            return None
        with self._lock:
            now = self._clocks.stamp()  # under the lock (see create)
            sess = self._by_sid.get(sid)
            if sess is None:
                return None
            if age_over(sess.last_touch, now, LIMIT_SESSION_IDLE_S) or age_over(sess.created, now, LIMIT_SESSION_ABS_S):
                del self._by_sid[sid]
                return None
            if touch:
                sess = replace(sess, last_touch=now)
                self._by_sid[sid] = sess
            return sess

    def end(self, sid: str | None) -> None:
        with self._lock:
            if isinstance(sid, str):
                self._by_sid.pop(sid, None)

    def end_all(self, login_name: str) -> None:
        with self._lock:
            for k in [k for k, v in self._by_sid.items() if v.login_name == login_name]:
                del self._by_sid[k]


class PreSessions:
    """Login CSRF (W-6, M-A)."""

    def __init__(self, clocks: Clocks = Clocks()) -> None:  # noqa: B008 (a frozen value)
        self._clocks = clocks
        self._lock = threading.Lock()
        self._by_id: dict[str, tuple[str, Stamp]] = {}  # insertion order = oldest first

    def issue(self) -> tuple[str, str]:
        """A NEW (pre-session id for the cookie, login CSRF token for the form) on every call. At most ``LIMIT_PRE_SESSIONS`` entries: expired ones go
        first, then the oldest."""
        pre_id, token = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        with self._lock:
            now = self._clocks.stamp()  # under the lock (see SessionStore.create)
            for k in [k for k, (_, st) in self._by_id.items() if age_over(st, now, LIMIT_PRE_SESSION_S)]:
                del self._by_id[k]
            while len(self._by_id) >= LIMIT_PRE_SESSIONS:
                del self._by_id[next(iter(self._by_id))]
            self._by_id[pre_id] = (token, now)
        return pre_id, token

    def redeem(self, pre_id: str | None, token: str | None) -> bool:
        """One use: the entry is deleted whatever the result."""
        if not isinstance(pre_id, str):
            return False
        with self._lock:
            entry = self._by_id.pop(pre_id, None)
        if entry is None or not isinstance(token, str):
            return False
        stored, st = entry
        if age_over(st, self._clocks.stamp(), LIMIT_PRE_SESSION_S):
            return False
        return equal_secret(token, stored)


def cookie_value(header: str | None, name: str) -> str | None:
    """Exactly one cookie of that name with a value of the id grammar, else None; a malformed header is None."""
    if not isinstance(header, str) or not header.isascii():
        return None
    found: list[str] = []
    for part in header.split(";"):
        part = part.strip()
        if not part:
            continue
        k, sep, v = part.partition("=")
        if not sep or not k:
            return None
        if k == name:
            found.append(v)
    return found[0] if len(found) == 1 and _ID_RE.fullmatch(found[0]) else None


def _attrs(max_age: int | None) -> str:
    return "; Secure; HttpOnly; SameSite=Strict; Path=/" + ("" if max_age is None else f"; Max-Age={max_age}")


def set_cookie(name: str, value: str, *, max_age: int | None = None) -> str:
    if name not in (COOKIE_SESSION, COOKIE_PRE) or not _ID_RE.fullmatch(value):
        raise ValueError("cookie name or value outside the grammar")
    return f"{name}={value}" + _attrs(max_age)


def clear_cookie(name: str) -> str:
    if name not in (COOKIE_SESSION, COOKIE_PRE):
        raise ValueError("cookie name outside the grammar")
    return f"{name}=" + _attrs(0)


def host_ok(app: str, host_values: list[str], port: int, hosts: Mapping[str, str]) -> bool:
    """Exactly one Host header, equal to an allowed string of this listener (token: also ``host.docker.internal:<port>``, name case-insensitive)."""
    if len(host_values) != 1 or app not in hosts:
        return False
    v = host_values[0]
    if v == f"{hosts[app]}:{port}":
        return True
    return app == "token" and v.lower() == f"{_HOST_DOCKER}:{port}"


def origin_ok(origin_values: list[str], sec_fetch_site: list[str], port: int, work_host: str) -> bool:
    """W-8: exactly one Origin equal to ``http://<work_host>:<port>`` AND exactly one Sec-Fetch-Site equal to ``same-origin``."""
    return (
        len(origin_values) == 1
        and origin_values[0] == f"http://{work_host}:{port}"
        and len(sec_fetch_site) == 1
        and sec_fetch_site[0] == "same-origin"
    )


def csrf_ok(session: Session, token: str | None) -> bool:
    return isinstance(token, str) and equal_secret(token, session.csrf)


def allowed(route: Route, session: Session | None) -> bool:
    """Default deny: empty roles, a token row and a missing session are all refused here."""
    if not route.roles or TOKEN_HOLDER in route.roles:
        return False  # no roles = nobody; a row that lists the token holder is never opened by a session
    if ANYONE in route.roles:
        return True
    if session is None or session.role not in ROLES:
        return False
    return session.role in route.roles


def require_role(session: Session | None, role: str) -> None:
    """Raises ``Denied("role_denied")``."""
    if session is None or role not in ROLES or session.role != role:
        raise Denied("role_denied")
