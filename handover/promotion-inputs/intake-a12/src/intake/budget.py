"""Spend guard (money path, spec 5.5). Our spend counter, not the provider's bill: it counts our estimates, and the limit at the provider is a separate,
second stop that this program cannot see.

Ledger ``HADAVIN_LOCAL/spend/spend.sqlite3`` (outside the repo): explicit ``BEGIN IMMEDIATE``, ``synchronous=FULL``, busy or locked = a refusal.
All money is integer micro-USD. Every call that passed ``reserve`` settles; nothing is released. The project total comes from the owner's sentence
(``current_cap`` re-reads ``owner_sentence.txt`` on every call; never cached) and prices are re-read from ``prices.json`` on every reserve
(``current_prices``; never cached). ``clock`` is the one time source (tests replace it).

Ledger shape for readers (WP6 footer, WP8 report): ``calls(cost_micro, status settled|settled_at_reserved, ...)`` holds every settled cost; the total spent is
``SELECT SUM(cost_micro) FROM calls``; ``reservations`` also carries ``in_price`` and ``out_price`` (the prices of that reservation, micro-USD per million
tokens: settle reads them from the row); ``meta`` holds ``halted``, ``halt_reason``, ``fail_streak``, ``last_seen``, ``cap_effective_micro`` (log copy),
``provider_limit_micro`` and ``provider_quote``. The worst-case bound assumes output <= ``max_tokens`` PLUS whatever ``model.extra_body`` allows: with
a model that thinks, the thinking tokens may count against ``max_tokens`` (the API's rule, NOT CHECKED here); a settle above the reservation halts."""

from __future__ import annotations

import hashlib
import re
import sqlite3
import sys
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path

from . import settings as cfg
from .codes import ConfigError, Refused

TIERS = ("read", "fallback")
CAP_RE = re.compile(r"The most the whole demo project may spend is US\$([1-9][0-9]{0,4})\.")
QUOTE_RE = re.compile(r"(LIMIT SET|PREPAID) ([1-9][0-9]{0,4})")
ORPHAN_AGE_S = cfg.ORPHAN_AGE_S  # 600 s; settings caps the call deadline at half of it, so a live call is never an orphan
BUSY_MS = 5000
MIN_FACTOR = 18  # the 6-document run, the video run and one re-run, each counted as 6 documents (a deliberate upper bound)
BREAKER_CODES = frozenset(
    {"http_4xx", "bad_reply", "over_cap"}
)  # systematic failures counted by the circuit breaker (an unreadable reply, a wrong request)
STOP_PROSE = "stop_prose"  # sentinel outcome: a well-formed reply that did not call the tool (own counter ``prose_streak``)
HOSTILE_SHAPE = (
    "hostile_shape"  # sentinel outcome: max_tokens, a wrong-shape tool call or an unlisted stop reason (own counter ``hostile_streak``)
)
PROSE_LIMIT, HOSTILE_LIMIT = 10, 3  # defaults; ``model.prose_streak_limit`` and ``model.hostile_streak_limit`` replace them
KNOWN_STOPS = frozenset(
    {"end_turn", "max_tokens", "stop_sequence", "tool_use", "refusal", "pause_turn", "model_context_window_exceeded"}
)  # closed list for the calls table
CLOCK_BACK_S = 86400  # a clock this much earlier than the ledger's last entry is refused
MAX_TOKENS_SEEN = 10**9  # a usage count above this is garbage, not a measurement
DEFERRED = frozenset({"owner_sentence_missing", "provider_limit_missing", "prices_missing"})
_MINT = object()

_SCHEMA = (
    "CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT)",
    "CREATE TABLE IF NOT EXISTS reservations(id INTEGER PRIMARY KEY AUTOINCREMENT, doc_sha TEXT NOT NULL, tier TEXT NOT NULL,"
    " micro INTEGER NOT NULL, body_len INTEGER NOT NULL, body_sha TEXT NOT NULL, state TEXT NOT NULL, created_at INTEGER NOT NULL,"
    " in_price INTEGER NOT NULL, out_price INTEGER NOT NULL)",
    "CREATE TABLE IF NOT EXISTS calls(id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER NOT NULL, doc_sha TEXT, model_id TEXT, tier TEXT,"
    " in_tok INTEGER, out_tok INTEGER, cost_micro INTEGER NOT NULL, status TEXT NOT NULL, reservation_id INTEGER, stop_reason TEXT)",
)


def clock() -> float:
    """Epoch seconds (UTC). The ONE clock of the guard: reservation ages and the price-date check both use it."""
    return time.time()


def today() -> date:
    return datetime.fromtimestamp(clock(), UTC).date()


def _exists(p: Path) -> bool:
    """Does the path exist? (``resolve(strict=True)`` raises when it does not; the structural scan of path probing allows no ``exists``/``is_file`` here.)"""
    try:
        p.resolve(strict=True)
    except (OSError, RuntimeError):
        return False
    return True


def ledger_path(s: cfg.Settings) -> Path:
    return s.spend_dir / "spend.sqlite3"


def genesis_path(s: cfg.Settings) -> Path:
    """The second place that remembers the ledger existed (``meta.genesis`` in the ledger holds the same id): deleting the ledger cannot start the
    count again, because ``init`` refuses to create a ledger while this marker exists. The owner removes the marker only to start a NEW project."""
    return s.intake_home / "spend.genesis"


def _marker_id(s: cfg.Settings) -> str | None:
    try:
        return genesis_path(s).read_text(encoding="utf-8").strip() or None
    except (OSError, ValueError):
        return None


def _check_genesis(conn: sqlite3.Connection, s: cfg.Settings) -> None:
    gid = _meta(conn, "genesis")
    if gid is None or gid != _marker_id(s):
        raise Refused(
            "ledger_inconsistent", "the spend ledger does not match its genesis marker (replaced or deleted): restore the original ledger"
        )


@dataclass(frozen=True)
class Reservation:
    """Created only by ``reserve`` (a forged one fails the ledger lookup in ``begin_send`` and ``settle``). The state lives in the ledger."""

    id: int
    doc_sha: str
    tier: str
    micro: int
    body_len: int
    body_sha: str
    ledger: str
    mint: object = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.mint is not _MINT:
            raise Refused("ledger_inconsistent", "a reservation can only be created by reserve")


# ---- ledger plumbing ------------------------------------------------------------------------------------------------------------------------
@contextmanager
def _tx(path: Path, create: bool = False):
    """One ``BEGIN IMMEDIATE`` transaction; commit on success, rollback on any exception. Busy, locked or unreadable = ``Refused``."""
    if not create and not _exists(path):
        raise Refused("ledger_missing", "spend ledger not found (run intake init, then intake check)")
    conn = None
    try:
        if create:
            path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path, isolation_level=None, timeout=BUSY_MS / 1000)
        conn.execute(f"PRAGMA busy_timeout={int(BUSY_MS)}")
        conn.execute("PRAGMA synchronous=FULL")
        conn.execute("BEGIN IMMEDIATE")
        try:
            yield conn
            conn.execute("COMMIT")
        except BaseException:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
    except sqlite3.Error:
        raise Refused("ledger_missing", "spend ledger busy or unreadable: run intake check") from None
    finally:
        if conn is not None:
            conn.close()


def _meta(conn: sqlite3.Connection, k: str) -> str | None:
    row = conn.execute("SELECT v FROM meta WHERE k=?", (k,)).fetchone()
    return None if row is None else row[0]


def _set_meta(conn: sqlite3.Connection, k: str, v: object) -> None:
    conn.execute("INSERT INTO meta(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (k, str(v)))


def _settled_total(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COALESCE(SUM(cost_micro),0) FROM calls").fetchone()[0])


def _open_total(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COALESCE(SUM(micro),0) FROM reservations WHERE state IN ('open','sent')").fetchone()[0])


def queue_cost_micro(s: cfg.Settings) -> int:
    """Read-only ``SELECT COALESCE(SUM(cost_micro),0) FROM items`` on the queue. A missing queue file or a missing ``items`` table counts as 0."""
    p = s.intake_home / "queue.sqlite3"
    if not _exists(p):
        return 0
    try:
        c = sqlite3.connect(p.resolve().as_uri() + "?mode=ro", uri=True, timeout=BUSY_MS / 1000)
        try:
            return int(c.execute("SELECT COALESCE(SUM(cost_micro),0) FROM items").fetchone()[0])
        finally:
            c.close()
    except sqlite3.Error as e:
        if "no such table" in str(e):
            return 0
        raise Refused("ledger_inconsistent", "queue unreadable for the cross-check") from None


def _touch(conn: sqlite3.Connection, refuse_clock_back: bool) -> None:
    """Record the newest time the ledger saw. A clock set back by more than a day (to make stale prices look fresh) is refused."""
    now = int(clock())
    last = int(_meta(conn, "last_seen") or 0)
    if refuse_clock_back and now < last - CLOCK_BACK_S:
        raise Refused("ledger_inconsistent", "the clock is more than a day earlier than the ledger's last entry")
    _set_meta(conn, "last_seen", max(last, now))


def _check_consistent(conn: sqlite3.Connection, s: cfg.Settings) -> None:
    if _settled_total(conn) < queue_cost_micro(s):
        raise Refused("ledger_inconsistent", "the spend ledger total is below the costs recorded in the queue")


# ---- prices, cap, limits --------------------------------------------------------------------------------------------------------------------
def current_prices(s: cfg.Settings) -> cfg.Prices:
    """Re-read ``prices.json`` and compare ``prices_as_of`` with the UTC clock on EVERY call. Raises ``Refused('prices_missing')``."""
    p = cfg.load_prices(s.prices_path, today())
    if (p.read_model, p.fallback_model) != (s.model.tier_read, s.model.tier_fallback):  # the prices must belong to the models we call
        raise Refused("prices_missing", "prices.json model_ids do not match the model tiers in service.json")
    return p


def _owner_text(s: cfg.Settings) -> str:
    try:
        return s.owner_sentence_path.read_text(encoding="utf-8").strip()
    except (OSError, ValueError):
        raise Refused("owner_sentence_missing", "owner_sentence.txt missing or unreadable") from None


def current_cap(s: cfg.Settings, live: bool | None = None) -> int:
    """The project total in micro-USD: ``N x 1,000,000`` from the owner's sentence, re-read on every call (exactly one match and the consent
    prefix once, else ``owner_sentence_missing``). With the fake backend the cap is ``model.fake_total_cap_micro`` and no sentence is needed."""
    if not (is_live(s) if live is None else live or is_live(s)):
        return s.model.fake_total_cap_micro
    text = _owner_text(s)
    found = CAP_RE.findall(text)
    if (
        len(found) != 1 or text.count(s.model.consent_prefix) != 1
    ):  # the cap is not used without the recorded consent either (defence in depth)
        raise Refused("owner_sentence_missing", "owner_sentence.txt must hold the consent sentence once and exactly one cap sentence")
    return int(found[0]) * 1_000_000


def consent_recorded(s: cfg.Settings) -> bool:
    """The literal consent prefix exactly once AND exactly one cap sentence in ``owner_sentence.txt``."""
    try:
        text = _owner_text(s)
    except Refused:
        return False
    return text.count(s.model.consent_prefix) == 1 and len(CAP_RE.findall(text)) == 1


def is_live(s: cfg.Settings, backend=None) -> bool:
    """Live rules (owner sentence, provider limit) apply when the settings OR the backend object is live: the stricter reading wins, so a live backend
    can never run under the fake cap (a live backend also refuses fake settings at construction)."""
    return s.backend != "fake" or bool(getattr(backend, "live", False))


def effective_cap(conn: sqlite3.Connection | None, s: cfg.Settings, live: bool | None = None) -> int:
    """``min(owner total, provider limit)``; with the fake backend just the fake cap. Raises ``owner_sentence_missing`` or ``provider_limit_missing``."""
    live = is_live(s) if live is None else live or is_live(s)
    cap = current_cap(s, live)
    if not live:
        return cap
    lim = None if conn is None else _meta(conn, "provider_limit_micro")
    if lim is None:
        raise Refused("provider_limit_missing", "no provider limit recorded (intake confirm-limit)")
    return min(cap, int(lim))


def provider_limit_micro(s: cfg.Settings) -> int | None:
    p = ledger_path(s)
    if not _exists(p):
        return None
    try:
        c = sqlite3.connect(p.resolve().as_uri() + "?mode=ro", uri=True, timeout=BUSY_MS / 1000)
        try:
            lim = _meta(c, "provider_limit_micro")
        finally:
            c.close()
    except sqlite3.Error:
        return None
    return None if lim is None else int(lim)


def cap_now(s: cfg.Settings) -> int | None:
    """The effective cap for display (``check``); None when it cannot be computed."""
    p = ledger_path(s)
    try:
        if s.backend == "fake" or not _exists(p):
            return effective_cap(None, s) if s.backend == "fake" else None
        c = sqlite3.connect(p.resolve().as_uri() + "?mode=ro", uri=True, timeout=BUSY_MS / 1000)
        try:
            return effective_cap(c, s)
        finally:
            c.close()
    except (Refused, sqlite3.Error):
        return None


def worst_case(prices: cfg.Prices, tier: str, body_len: int, max_tokens: int, overhead_tokens: int) -> int:
    """``ceil((est_in * in_price + max_tokens * out_price) / 1_000_000)`` with ``est_in = body_len + overhead_tokens`` (a token is at least one
    byte of the body; output is assumed to be at most ``max_tokens``: when a model thinks that is an assumption the API decides, so a settle above
    the reservation halts the guard and the circuit breaker stops a systematic failure)."""
    pin, pout = tier_prices(prices, tier)
    return -(-((body_len + overhead_tokens) * pin + max_tokens * pout) // 1_000_000)


def tier_prices(prices: cfg.Prices, tier: str) -> tuple[int, int]:
    if tier == "read":
        return prices.read_in, prices.read_out
    if tier == "fallback":
        return prices.fallback_in, prices.fallback_out
    raise Refused("bad_config", "unknown tier")


def min_limit_micro(s: cfg.Settings, backend) -> int:
    """``18 x (worst(read) + worst(fallback))`` for the maximum-size MODEL text: the larger request body of ``mask.MASKED_MAX_CHARS`` characters of U+10FFFF
    (4 bytes each) and of U+0001 (6 bytes each once JSON-escaped), built by ``backend.request_body``. The bound is the masked-text cap, not the document
    cap: a hiding mark can be longer than the value it hides, and ``mask`` holds back any model text over the cap. Raises ``prices_missing``."""
    from .mask import MASKED_MAX_CHARS  # function-local: ``mask`` is a higher layer (the import graph stays acyclic)
    from .model import ExtractRequest

    prices = current_prices(s)
    n_chars = MASKED_MAX_CHARS
    docs = (chr(0x10FFFF) * n_chars, chr(1) * n_chars)
    total = 0
    for tier in TIERS:
        n = max(len(backend.request_body(ExtractRequest("0" * 64, tier, model_text=d))) for d in docs)
        total += worst_case(prices, tier, n, s.model.max_tokens, s.model.overhead_tokens)
    return MIN_FACTOR * total


def minimum_check(s: cfg.Settings, backend) -> None:
    """``cap_effective >= min_limit`` re-evaluated on every guarded call (so a deferred start, a lowered sentence or new prices cannot skip it).
    Raises ``cap_too_small_for_worst_case`` or the deferral code (``owner_sentence_missing``, ``provider_limit_missing``, ``prices_missing``)."""
    with _tx(ledger_path(s)) as c:
        cap = effective_cap(c, s, is_live(s, backend))
        need = min_limit_micro(s, backend)
    if cap < need:
        raise Refused("cap_too_small_for_worst_case", f"the cap is below the worst case for the maximum document ({need} micro-USD)")


def startup_check(s: cfg.Settings, backend) -> str | None:
    """Run once at construction of ``GuardedModel``: settle orphans older than 600 s, cross-check the ledger against the queue (refuses
    ``ledger_inconsistent``) and refuse ``cap_too_small_for_worst_case`` unless ``cap_effective >= min_limit`` (equality passes). A missing
    ledger, owner sentence, provider limit or prices defers (every reserve then refuses with that code). Returns the deferral code or None."""
    path = ledger_path(s)
    if not _exists(path):
        return "ledger_missing"
    settle_orphans(s)
    with _tx(path) as c:
        _check_genesis(c, s)
        _check_consistent(c, s)
        _touch(c, refuse_clock_back=True)
        try:
            cap = effective_cap(c, s, is_live(s, backend))
            need = min_limit_micro(s, backend)
        except Refused as e:
            if e.code in DEFERRED:
                return e.code
            raise
        if cap < need:
            raise Refused("cap_too_small_for_worst_case", f"the cap is below the worst case for the maximum document ({need} micro-USD)")
        _set_meta(c, "cap_effective_micro", cap)
    return None


# ---- lifecycle ------------------------------------------------------------------------------------------------------------------------------
def init(s: cfg.Settings, clear_halt: bool = False) -> None:
    """Create ``spend.sqlite3`` if absent. Idempotent: never resets. Refuses ``ledger_inconsistent`` on a ledger whose total is below the costs the
    queue already holds (a deleted ledger next to a costed queue)."""
    marker = _marker_id(s)
    existed = _exists(ledger_path(s))
    try:
        _init_tx(s, clear_halt, marker)
    except Refused:
        if not existed:  # a refused first creation leaves no empty ledger behind (and no marker it wrote itself)
            ledger_path(s).unlink(missing_ok=True)
            if marker is None:
                genesis_path(s).unlink(missing_ok=True)
        raise
    if sys.platform != "win32":  # owner-only on POSIX (on Windows the folder's inherited access list protects it)
        ledger_path(s).chmod(0o600)
        s.spend_dir.chmod(0o700)


def _init_tx(s: cfg.Settings, clear_halt: bool, marker: str | None) -> None:
    with _tx(ledger_path(s), create=True) as c:
        for ddl in _SCHEMA:
            c.execute(ddl)
        c.execute("INSERT OR IGNORE INTO meta(k,v) VALUES('halted','0')")
        gid = _meta(c, "genesis")
        if gid is None:
            if marker is not None:  # a ledger is being created although the marker says one existed: it was deleted
                raise Refused(
                    "ledger_inconsistent", "the spend ledger was deleted (its genesis marker exists): restore it instead of starting again"
                )
            gid = uuid.uuid4().hex
            _set_meta(c, "genesis", gid)
            s.intake_home.mkdir(parents=True, exist_ok=True)
            genesis_path(s).write_text(gid, encoding="utf-8")
        elif gid != marker:
            raise Refused("ledger_inconsistent", "the spend ledger does not match its genesis marker")
        if clear_halt:
            _set_meta(c, "halted", 0)
            _set_meta(c, "halt_reason", "")
            _set_meta(c, "fail_streak", 0)
            _set_meta(
                c, "last_seen", int(clock())
            )  # also the recovery after a forward clock jump (a clock set back is refused against last_seen)
        _check_consistent(c, s)


def confirm_limit(s: cfg.Settings, quote: str) -> int:
    """``LIMIT SET <N>`` or ``PREPAID <N>`` (whole US dollars, at least 1). Stores the quote and ``provider_limit_micro``; nothing about the
    owner's total. May be run again (a later quote replaces the earlier one). Returns N."""
    m = QUOTE_RE.fullmatch(quote.strip())
    if not m:
        raise ConfigError("bad_config", "quote must be 'LIMIT SET <n>' or 'PREPAID <n>' with n whole dollars, at least 1")
    n = int(m.group(2))
    init(s)
    with _tx(ledger_path(s)) as c:
        _check_consistent(c, s)
        _set_meta(c, "provider_quote", m.group(0))
        _set_meta(c, "provider_limit_micro", n * 1_000_000)
    return n


def is_halted(s: cfg.Settings) -> bool:
    with _tx(ledger_path(s)) as c:
        return _meta(c, "halted") == "1"


def halt_state(s: cfg.Settings) -> tuple[bool, str]:
    """(halted, reason) read-only for ``check``; an unreadable or missing ledger is (False, '')."""
    p = ledger_path(s)
    if not _exists(p):
        return False, ""
    try:
        c = sqlite3.connect(p.resolve().as_uri() + "?mode=ro", uri=True, timeout=BUSY_MS / 1000)
        try:
            return _meta(c, "halted") == "1", _meta(c, "halt_reason") or "unknown"
        finally:
            c.close()
    except sqlite3.Error:
        return False, ""


def halt_state_readonly(s: cfg.Settings) -> tuple[bool, str] | None:
    """Three states for the service (W-16, m3): ``(True, reason)`` halted, ``(False, "")`` not halted, ``None`` unreadable. ``None`` is returned for a
    missing ledger file, any database error and an absent ``halted`` key or any value other than ``"1"``/``"0"``; the caller refuses a scan and shows
    "status unavailable" (``halt_state`` answers "not halted" in all those cases, which is right for ``check`` but wrong for a service)."""
    p = ledger_path(s)
    if not _exists(p):
        return None
    try:
        c = sqlite3.connect(p.resolve().as_uri() + "?mode=ro", uri=True, timeout=BUSY_MS / 1000)
        try:
            v = _meta(c, "halted")
            reason = _meta(c, "halt_reason") or "unknown"
        finally:
            c.close()
    except sqlite3.Error:
        return None
    if v == "1":
        return True, reason
    return (False, "") if v == "0" else None


def files_state(s: cfg.Settings) -> str:
    """Read-only state of the two spend files for ``check``: ``ok``, ``ledger_missing``, ``marker_missing`` or ``mismatch`` (the ledger and its genesis
    marker must carry the same id; ``intake init`` creates both)."""
    p = ledger_path(s)
    if not _exists(p):
        return "ledger_missing"
    mid = _marker_id(s)
    if mid is None:
        return "marker_missing"
    try:
        c = sqlite3.connect(p.resolve().as_uri() + "?mode=ro", uri=True, timeout=BUSY_MS / 1000)
        try:
            gid = _meta(c, "genesis")
        finally:
            c.close()
    except sqlite3.Error:
        return "mismatch"
    return "ok" if gid == mid else "mismatch"


def total_settled_micro(s: cfg.Settings) -> int:
    with _tx(ledger_path(s)) as c:
        return _settled_total(c)


def total_settled_readonly(s: cfg.Settings) -> int | None:
    """The settled total for a page footer without ``BEGIN IMMEDIATE`` (a read never blocks ``settle``): ``mode=ro`` with the same busy timeout as
    ``halt_state``; ``None`` for a missing, locked or unreadable ledger. The ledger uses the default rollback journal, so no ``-shm`` file is needed."""
    p = ledger_path(s)
    if not _exists(p):
        return None
    try:
        c = sqlite3.connect(p.resolve().as_uri() + "?mode=ro", uri=True, timeout=BUSY_MS / 1000)
        try:
            return _settled_total(c)
        finally:
            c.close()
    except sqlite3.Error:
        return None


def reserve(s: cfg.Settings, doc_sha: str, tier: str, body: bytes, live: bool | None = None) -> Reservation:
    """Every call is one reserve. Refuses (``budget_halted``, ``prices_missing``, ``owner_sentence_missing``, ``provider_limit_missing``,
    ``ledger_missing``, ``ledger_inconsistent``, ``budget_total``) when settled + open reservations + worst case would pass the effective cap."""
    if tier not in TIERS or not isinstance(body, bytes) or not body:
        raise Refused("bad_config", "reserve needs a known tier and a non-empty body")
    with _tx(ledger_path(s)) as c:
        if _meta(c, "halted") == "1":
            raise Refused("budget_halted", "spend guard halted (intake init --clear-halt --yes after fixing the estimate)")
        until = _meta(c, "transport_cooldown_until")
        if until and clock() < float(until):  # mut:cooldown
            raise Refused("transport_cooldown", "too many connection failures in a row: new calls wait until the cooldown ends")
        _check_genesis(c, s)
        _touch(c, refuse_clock_back=True)
        prices = current_prices(s)
        cap = effective_cap(c, s, live)
        _check_consistent(c, s)
        worst = worst_case(prices, tier, len(body), s.model.max_tokens, s.model.overhead_tokens)
        if _settled_total(c) + _open_total(c) + worst > cap:
            raise Refused("budget_total", "this call could take the project total past the cap")
        _set_meta(c, "cap_effective_micro", cap)
        pin, pout = tier_prices(prices, tier)
        sha = hashlib.sha256(body).hexdigest()
        cur = c.execute(
            "INSERT INTO reservations(doc_sha,tier,micro,body_len,body_sha,state,created_at,in_price,out_price) VALUES(?,?,?,?,?,'open',?,?,?)",
            (doc_sha, tier, worst, len(body), sha, int(clock()), pin, pout),
        )
        return Reservation(cur.lastrowid, doc_sha, tier, worst, len(body), sha, str(ledger_path(s)), _MINT)


def begin_send(res: Reservation, body: bytes) -> None:
    """Raises unless the reservation is open in the ledger and ``sha256(body)`` and ``len(body)`` equal the reserved ones (so a body for another
    tier or document, or a bigger one, cannot ride it); then marks it ``sent`` before the first byte is written. A second send is refused."""
    if not isinstance(res, Reservation) or not isinstance(body, bytes):
        raise Refused("ledger_inconsistent", "begin_send needs a reservation and the body bytes")
    with _tx(Path(res.ledger)) as c:
        row = c.execute("SELECT doc_sha,tier,micro,body_len,body_sha,state FROM reservations WHERE id=?", (res.id,)).fetchone()
        if row is None or row[5] != "open":
            raise Refused("ledger_inconsistent", "reservation is not open (one send per reservation)")
        if (res.doc_sha, res.tier, res.micro, res.body_sha) != (row[0], row[1], row[2], row[4]):
            raise Refused("ledger_inconsistent", "reservation does not match the ledger")
        if len(body) != row[3] or hashlib.sha256(body).hexdigest() != row[4]:
            raise Refused("ledger_inconsistent", "body is not the priced body of this reservation")
        c.execute("UPDATE reservations SET state='sent' WHERE id=? AND state='open'", (res.id,))


def _valid_usage(usage: object) -> tuple[int, int] | None:
    if not isinstance(usage, tuple | list) or len(usage) != 2:
        return None
    for v in usage:
        if isinstance(v, bool) or not isinstance(v, int) or not 1 <= v <= MAX_TOKENS_SEEN:
            return None
    return usage[0], usage[1]


def _bump(c: sqlite3.Connection, key: str, limit: int, reason: str) -> None:
    n = int(_meta(c, key) or 0) + 1
    _set_meta(c, key, n)
    if n >= limit and _meta(c, "halted") != "1":
        _set_meta(c, "halted", 1)
        _set_meta(c, "halt_reason", reason)


valid_usage = _valid_usage  # public name for the guard: the ONE rule for "these token counts are billable"


def _apply_outcome(c: sqlite3.Connection, error: str | None, breaker: int, limits: tuple[int, int] | None = None) -> None:
    prose_limit, hostile_limit = limits or (PROSE_LIMIT, HOSTILE_LIMIT)
    if error is None:  # a valid tool reply resets all three counters
        _set_meta(c, "prose_streak", 0)
        _set_meta(c, "hostile_streak", 0)
    elif error == STOP_PROSE:  # mut:prose_counter
        _bump(c, "prose_streak", prose_limit, "prose_streak")
        return
    elif error == HOSTILE_SHAPE:  # mut:hostile_counter
        _bump(c, "hostile_streak", hostile_limit, "hostile_streak")
        return
    if error is not None and error not in BREAKER_CODES:
        return
    n = 0 if error is None else int(_meta(c, "fail_streak") or 0) + 1
    _set_meta(c, "fail_streak", n)
    if n >= breaker:
        _set_meta(c, "halted", 1)
        _set_meta(c, "halt_reason", "circuit_breaker")


def _ensure_stop_reason_column(c: sqlite3.Connection) -> None:
    """A ledger made before this column existed gets it once, inside the settling transaction."""
    if not any(r[1] == "stop_reason" for r in c.execute("PRAGMA table_info(calls)").fetchall()):
        c.execute("ALTER TABLE calls ADD COLUMN stop_reason TEXT")


def _settle_once(
    res: Reservation,
    usage: object,
    model_id: str | None,
    error: str | None,
    breaker: int | None,
    halt_reason: str | None,
    stop_reason: str | None = None,
    limits: tuple[int, int] | None = None,
) -> int:
    with _tx(Path(res.ledger)) as c:
        row = c.execute("SELECT doc_sha,tier,micro,state,in_price,out_price FROM reservations WHERE id=?", (res.id,)).fetchone()
        if row is None or row[3] not in ("open", "sent"):
            raise Refused("ledger_inconsistent", "settle needs an open or sent reservation (double settle or no reserve)")
        doc_sha, tier, reserved, _state, pin, pout = row
        u = _valid_usage(usage)
        status, cost = "settled_at_reserved", reserved
        if u is not None:
            cost = -(-(u[0] * pin + u[1] * pout) // 1_000_000)
            status = "settled"
            if cost > reserved:  # our estimate was wrong: settle the ACTUAL amount and halt
                _set_meta(c, "halted", 1)
                _set_meta(c, "halt_reason", "estimate_exceeded")
        _ensure_stop_reason_column(c)
        stop = stop_reason if stop_reason in KNOWN_STOPS else ("other" if stop_reason else None)
        c.execute(
            "INSERT INTO calls(ts,doc_sha,model_id,tier,in_tok,out_tok,cost_micro,status,reservation_id,stop_reason) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (int(clock()), doc_sha, model_id, tier, u[0] if u else None, u[1] if u else None, cost, status, res.id, stop),
        )
        c.execute("UPDATE reservations SET state='settled' WHERE id=?", (res.id,))
        _touch(c, refuse_clock_back=False)
        if breaker is not None:  # the circuit breaker moves in the SAME transaction as the settlement
            _apply_outcome(c, error, breaker, limits)
        if halt_reason:
            _set_meta(c, "halted", 1)
            _set_meta(c, "halt_reason", halt_reason)
        return cost


def settle(
    res: Reservation,
    usage: object = None,
    model_id: str | None = None,
    error: str | None = None,
    breaker: int | None = None,
    halt_reason: str | None = None,
    stop_reason: str | None = None,
    limits: tuple[int, int] | None = None,
) -> int:
    """Settle one reservation and return its cost in micro-USD. Usage missing, zero, negative, not an int, or any failure = settle at the reserved
    amount; valid usage below the reservation = the actual cost; valid usage ABOVE it = the actual cost and ``halted``. Retried once when the ledger
    is busy, then ``settle_failed`` (a ``ConfigError``, exit 3: it leaves ``GuardedModel.call`` on purpose and the process must stop; WP6 answers 503 and
    exits). ``error`` and ``breaker`` update the circuit-breaker streak in the same transaction; ``halt_reason`` halts the ledger in it. A reservation
    that the orphan sweep settled first is counted at its reserved amount and a later settle is refused, so such a row can hide a later overshoot."""
    if not isinstance(res, Reservation):
        raise Refused("ledger_inconsistent", "settle needs a reservation")
    for attempt in (1, 2):
        try:
            return _settle_once(res, usage, model_id, error, breaker, halt_reason, stop_reason, limits)
        except OverflowError:
            usage = None
        except Refused as e:
            if e.code != "ledger_missing":
                raise
            if attempt == 2:
                raise ConfigError("settle_failed", "could not write the settlement; the process must stop") from None
    raise ConfigError("settle_failed", "could not write the settlement; the process must stop")


def settle_orphans(s: cfg.Settings, max_age_s: int = ORPHAN_AGE_S) -> int:
    """Open or sent reservations older than ``max_age_s`` (a killed process left them) are settled at their reserved amount. Returns the count.
    The age is never below twice the call deadline, so a reservation of a call that is still running is never swept."""
    max_age_s = max(max_age_s, 2 * s.model.deadline_s + 5)
    n = 0
    with _tx(ledger_path(s)) as c:
        rows = c.execute(
            "SELECT id,doc_sha,tier,micro FROM reservations WHERE state IN ('open','sent') AND created_at<=?", (int(clock()) - max_age_s,)
        ).fetchall()
        for rid, doc_sha, tier, micro in rows:
            c.execute(
                "INSERT INTO calls(ts,doc_sha,model_id,tier,in_tok,out_tok,cost_micro,status,reservation_id) VALUES(?,?,NULL,?,NULL,NULL,?,?,?)",
                (int(clock()), doc_sha, tier, micro, "settled_at_reserved", rid),
            )
            c.execute("UPDATE reservations SET state='settled' WHERE id=?", (rid,))
            n += 1
    return n


def transport_record(s: cfg.Settings, failed: list[bool]) -> tuple[int, bool]:
    """Persist the connection-failure count (per CALL, because cost is per call): one entry per call of a document, True = it ended on a transport code.
    A pause longer than ``model.transport_window_s`` since the last failure restarts the count; a non-failing call resets it. At
    ``model.transport_streak_limit`` the cooldown starts (``reserve`` then refuses with ``transport_cooldown`` for ``model.transport_cooldown_s``).
    Returns (count, stop). Survives a restart because it lives in ``meta``."""
    m = s.model
    with _tx(ledger_path(s)) as c:
        n = int(_meta(c, "transport_n") or 0)
        last = float(_meta(c, "transport_last") or 0)
        now = clock()
        for f in failed:
            if not f:
                n = 0
                continue
            if now - last > m.transport_window_s:  # mut:transport_window
                n = 0
            n += 1
            last = now
            if n >= m.transport_streak_limit:
                _set_meta(c, "transport_cooldown_until", now + m.transport_cooldown_s)
        _set_meta(c, "transport_n", n)
        _set_meta(c, "transport_last", last)
        return n, n >= m.transport_streak_limit


def record_outcome(s: cfg.Settings, error: str | None) -> None:
    """Circuit breaker for LIVE calls: a success resets the streak; ``http_4xx``, ``bad_reply`` (unreadable) and ``over_cap`` add one (they mean the request shape
    is wrong, so more calls only burn budget); other errors (net, timeout, 429, 5xx) leave it. At ``model.breaker_failures`` in a row the ledger is
    halted (``halt_reason`` circuit_breaker) until ``intake init --clear-halt --yes``."""
    with _tx(ledger_path(s)) as c:
        _apply_outcome(c, error, s.model.breaker_failures)


class Budget:
    """The object ``GuardedModel`` holds: the module functions bound to one ``Settings``."""

    def __init__(self, s: cfg.Settings) -> None:
        self.settings = s

    def current_prices(self) -> cfg.Prices:
        return current_prices(self.settings)

    def reserve(self, doc_sha: str, tier: str, body: bytes, live: bool | None = None) -> Reservation:
        return reserve(self.settings, doc_sha, tier, body, live)

    def minimum_check(self, backend) -> None:
        return minimum_check(self.settings, backend)

    def record_outcome(self, error: str | None) -> None:
        return record_outcome(self.settings, error)

    def settle(
        self,
        res: Reservation,
        usage: object = None,
        model_id: str | None = None,
        error: str | None = None,
        live: bool = False,
        halt_reason: str | None = None,
        stop_reason: str | None = None,
    ) -> int:
        m = self.settings.model
        return settle(
            res,
            usage,
            model_id,
            error,
            m.breaker_failures if live else None,
            halt_reason,
            stop_reason,
            (m.prose_streak_limit, m.hostile_streak_limit),
        )

    def startup_check(self, backend) -> str | None:
        return startup_check(self.settings, backend)
