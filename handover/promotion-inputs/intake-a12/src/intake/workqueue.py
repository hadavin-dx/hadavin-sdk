"""The work queue (spec 7, errata 32): ``INTAKE_HOME/queue.sqlite3``. Every function takes the ``Settings`` first. ``connect`` is the ONLY way the queue
is opened (a test scans for ``sqlite3.connect``); it creates the schema, verifies the table definitions and (re)creates the guard triggers on every
open. State moves are compare-and-set on ``version``. All SQL for the queue lives here and in ``queue_schema`` (a test scans for it; see "Queue store:
alternative and trigger" there). Callers (decisions, exporter, pages) use the functions below and never hand-write queue SQL.

Transactions: ``transaction(conn)`` is one ``BEGIN IMMEDIATE`` (it does not nest). ``decide``, ``purge`` and ``record_export`` accept an open connection
(``conn=``) whose caller already holds a transaction (they refuse a connection that has none); without ``conn`` ``decide`` and ``purge`` open their own.
The file must be on a local filesystem (WAL needs shared memory; a network share or WSL mount is refused as ``wal_unavailable``)."""

from __future__ import annotations

import getpass
import hashlib
import json
import os
import re
import sqlite3
import time
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType

from . import flags as flagtable
from . import phrases, queue_schema, settings, strictjson, trace_vocab, validators
from .codes import ConfigError, Refused
from .selfcheck_codes import PLAIN as _SELFCHECK_PLAIN
from .selfcheck_codes import SelfCheckFailed

__all__ = [
    "ACTOR_RE", "MaskSpan", "TraceRow", "Decision", "Duplicate", "Export", "Item", "apply_decision", "approved_unexported", "connect", "export_by_row_id", "exports_in_order",
    "connect_readonly", "get", "get_by_uid", "get_export", "get_in", "insert_flagged", "insert_received", "item_id", "known_sources", "latest_decision", "list_items", "now_utc", "opened",
    "purge", "queue_files_state", "queue_path", "recover_received", "record_export", "scope", "set_fixed_clock", "reset_clock", "set_result", "sum_cost_micro", "text_hash", "transaction", "unreadable_ids",
    "add_trace", "all_spans_for_scan", "item_key", "restore_map", "selfcheck_reason", "store_mask", "trace_rows",
]  # fmt: skip

PURGE_STATES = ("RECEIVED", "READY", "NEEDS_PERSON", "REJECTED")
ID_HEX = 8
BUSY_TIMEOUT_S = 10  # how long a writer waits for another writer
WAL_WAIT_S = 10  # how long the first open waits for another process that is switching the new file to WAL
RECOVERED_FLAG = "L02"  # a RECEIVED item found at start-up (no model reply was stored)
QUEUE_FILE_MODE = 0o600
QUEUE_DIR_MODE = 0o700
RESERVED_ACTORS = frozenset({"system", "cli"})  # names the program itself uses; a decision by a person never carries one
ACTOR_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._@-]{0,63}")  # a login name: the approver of a decision, the person who purged
_FILES = ("queue.sqlite3", "queue.sqlite3-wal", "queue.sqlite3-shm")
_REASON_FLAG = "X10"
_RECORD_FIELD = "record"


@dataclass(frozen=True)
class Item:
    """One queue row. ``repr`` never prints the invoice text or the extracted values."""

    uid: int
    id: str
    source_name: str
    source_sha256: str
    tenant_id: str
    state: str
    fields: dict | None = field(repr=False)
    flags: tuple[str, ...]
    failing_fields: tuple[str, ...]
    source_text: str = field(repr=False)
    model_id: str | None
    tier: str | None
    prompt_sha256: str | None
    cost_micro: int
    version: int
    created_at: str


@dataclass(frozen=True)
class Duplicate:
    item_id: str


@dataclass(frozen=True)
class Decision:
    seq: int
    item_uid: int
    decision: str
    approver: str
    reason: str | None = field(repr=False)
    content_code: str
    at: str


@dataclass(frozen=True)
class Export:
    seq: int
    row_id: str
    item_uid: int
    content_code: str
    row_json: str = field(repr=False)
    at: str


def _real_clock() -> datetime:
    return datetime.now(UTC)


_clock = _real_clock  # the clock seam (errata 41c); only ``set_fixed_clock`` replaces it, ``reset_clock`` puts the real one back


def now_utc() -> str:
    """UTC timestamp, ``YYYY-MM-DDTHH:MM:SSZ``, read from the clock seam (decision, export and purge times all come from here; spend time is separate)."""
    return _clock().astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def set_fixed_clock(s: settings.Settings, when: datetime) -> None:
    """Fix the queue clock (a recorded demo or a test). Refused unless the backend is the fake one, which ``settings.require_safe_backend`` already
    confines to a temporary folder: a live run can never carry a made-up time. ``when`` must be timezone-aware. A fixed demo clock does NOT move the
    spend ledger's time (``budget`` has its own clock)."""
    global _clock
    if s.backend != "fake":
        raise Refused("bad_config", "a fixed clock is allowed only with the fake backend (tests and recorded demos)")
    if when.tzinfo is None:
        raise ValueError("the fixed time needs a timezone")
    _clock = lambda: when  # noqa: E731


def reset_clock() -> None:
    """Put the real clock back (the end of a test or a recording)."""
    global _clock
    _clock = _real_clock


def queue_path(s: settings.Settings) -> Path:
    """Where the queue file lives."""
    return s.intake_home / "queue.sqlite3"


def _guard_refusal(e: sqlite3.IntegrityError) -> Refused:
    """Map a database refusal to a closed code (the message names the trigger or column; no invoice text is in it)."""
    msg = str(e)
    if msg.startswith(("NOT NULL constraint", "CHECK constraint")):
        return Refused("bad_config", "a stored value is missing or not allowed")
    return Refused("state_conflict", f"the database guard refused the change: {msg[:80]}")


# ---- opening ------------------------------------------------------------------------------------------------------------------------------------
def connect(s: settings.Settings) -> sqlite3.Connection:
    """Open the queue and return the connection (the caller closes it; ``opened`` does). Creates the folder (0700), the file (0600, before the first
    write), the schema and the triggers; sets WAL, a busy timeout and ``recursive_triggers=ON``. Refused: a table that differs from the wanted
    definition or is missing from a non-new file (``bad_config``), a filesystem without WAL (``wal_unavailable``), a busy file (``db_busy``)."""
    s.intake_home.mkdir(mode=QUEUE_DIR_MODE, parents=True, exist_ok=True)
    _precreate(queue_path(s))
    conn = sqlite3.connect(queue_path(s), timeout=BUSY_TIMEOUT_S, isolation_level=None)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_S * 1000}")
        _enable_wal(conn)
        conn.execute("PRAGMA synchronous=FULL")
        conn.execute("PRAGMA recursive_triggers=ON")
        _ensure_schema(conn)
        _check_version(conn)
        _restrict_files(s)
    except BaseException:
        conn.close()
        raise
    return conn


def connect_readonly(s: settings.Settings) -> sqlite3.Connection:
    """A read-only connection for GET pages (W-16): ``mode=ro`` URI, the same busy timeout, no schema or trigger work, nothing is created (a missing file
    raises ``FileNotFoundError``). The file must already be WAL and carry the wanted ``schema_version`` (``bad_config`` otherwise): a reader never
    switches the journal mode. The caller closes it."""
    conn = sqlite3.connect(queue_path(s).resolve(strict=True).as_uri() + "?mode=ro", uri=True, timeout=BUSY_TIMEOUT_S, isolation_level=None)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_S * 1000}")
        if str(conn.execute("PRAGMA journal_mode").fetchone()[0]).lower() != "wal":
            raise ConfigError("bad_config", "the queue file is not in WAL mode; it is not trusted")
        _check_version(conn)
    except BaseException:
        conn.close()
        raise
    return conn


def _precreate(path: Path) -> None:
    """Create an empty queue file with the owner-only mode BEFORE sqlite writes to it (no window with the default umask)."""
    if not path.exists():
        os.close(os.open(path, os.O_CREAT | os.O_WRONLY, QUEUE_FILE_MODE))


def _enable_wal(conn) -> None:
    """Switch the file to WAL. SQLite does not wait for the exclusive moment (``database is locked`` at once when another process is switching the
    same new file), so retry until ``WAL_WAIT_S``; the deadline is checked on EVERY pass. A filesystem without shared memory answers another mode
    (``delete``): refused as ``wal_unavailable``, never retried."""
    deadline = time.monotonic() + WAL_WAIT_S
    while True:
        try:
            if str(conn.execute("PRAGMA journal_mode=WAL").fetchone()[0]).lower() == "wal":
                return
            raise ConfigError("bad_config", "wal_unavailable: the queue file must be on a local filesystem")
        except sqlite3.OperationalError as e:
            if "locked" not in str(e) and "busy" not in str(e):
                raise
        if time.monotonic() > deadline:
            raise ConfigError("bad_config", "wal_unavailable: the queue file stayed locked while switching to WAL")
        time.sleep(0.05)


def _have(conn: sqlite3.Connection) -> tuple[dict[str, str], dict[str, str]]:
    schema: dict[str, str] = {}
    triggers: dict[str, str] = {}
    for r in conn.execute("SELECT type, name, sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%'"):
        (triggers if r["type"] == "trigger" else schema)[r["name"]] = queue_schema.normalise_sql(r["sql"])
    return schema, triggers


def _ensure_schema(conn: sqlite3.Connection) -> None:
    want_schema = queue_schema.schema_sql()
    want_triggers = {k: queue_schema.normalise_sql(v) for k, v in queue_schema.trigger_sql().items()}
    if _have(conn) == (want_schema, want_triggers):
        return
    with transaction(conn):  # one writer at a time; read again inside the lock (another process may have just done this)
        have_schema, _ = _have(conn)
        new_file = not have_schema
        if have_schema and have_schema.keys() != want_schema.keys():
            raise ConfigError("bad_config", "the queue file lacks a table or holds an unknown one; it is not trusted and is not repaired")
        for ddl in queue_schema.TABLES:
            conn.execute(ddl)
        if new_file:  # only a brand-new file gets its version row: a missing row in an existing file is refused by ``_check_version``
            conn.execute("INSERT INTO meta (k, v) VALUES ('schema_version', ?)", (queue_schema.SCHEMA_VERSION,))
        schema, triggers = _have(conn)
        if schema != want_schema:
            raise ConfigError("bad_config", "a queue table or index definition differs from the wanted one; the queue file is not trusted")
        if triggers != want_triggers:
            for name in triggers:
                conn.execute('DROP TRIGGER IF EXISTS "' + name.replace('"', '""') + '"')
            for sql in queue_schema.trigger_sql().values():
                conn.execute(sql)


def _check_version(conn: sqlite3.Connection) -> None:
    """The queue file must carry ``schema_version`` = ``queue_schema.SCHEMA_VERSION``; anything else (another number, no row) is refused: this build has
    no migration path, so it never guesses at a file written by another version."""
    r = conn.execute("SELECT v FROM meta WHERE k = 'schema_version'").fetchone()
    if r is None or r["v"] != queue_schema.SCHEMA_VERSION:
        raise ConfigError("bad_config", "the queue file has an unknown schema version; it is not trusted and is not migrated")


def _restrict_files(s: settings.Settings) -> None:
    if os.name == "nt":
        return  # the mode bits do nothing on Windows; protection is the inherited access list of the profile folder (README)
    if s.intake_home.stat().st_mode & 0o077:
        s.intake_home.chmod(QUEUE_DIR_MODE)  # an intake folder that already existed with looser bits is tightened too
    for name in _FILES:
        p = s.intake_home / name
        if p.exists():
            p.chmod(QUEUE_FILE_MODE)


def queue_files_state(s: settings.Settings) -> str:
    """For ``intake check``: ``absent``, ``n/a (windows)``, ``ok`` or ``mode_too_open``."""
    if not queue_path(s).exists():
        return "absent"
    if os.name == "nt":
        return "n/a (windows)"
    bad = [n for n in _FILES if (s.intake_home / n).exists() and (s.intake_home / n).stat().st_mode & 0o077]
    return "mode_too_open" if bad else "ok"


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """One ``BEGIN IMMEDIATE`` transaction: commit on success, roll back on any exception (including a failing COMMIT). It does not nest. A writer that
    cannot get the lock within the busy timeout is refused ``db_busy``."""
    try:
        conn.execute("BEGIN IMMEDIATE")
    except sqlite3.OperationalError as e:
        if "locked" in str(e) or "busy" in str(e):
            raise Refused("db_busy", "the queue is busy; try again") from e
        raise
    try:
        yield conn
        conn.execute("COMMIT")
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise


@contextmanager
def opened(s: settings.Settings) -> Iterator[sqlite3.Connection]:
    """A connection for the block, closed afterwards."""
    conn = connect(s)
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def scope(s: settings.Settings, conn: sqlite3.Connection | None) -> Iterator[sqlite3.Connection]:
    """The caller's open connection (it must already be inside ``transaction``; a connection without one is refused with ``ValueError``) or a new
    connection with its own transaction, committed or rolled back when the block ends."""
    if conn is not None:
        if not conn.in_transaction:
            raise ValueError("conn= needs a connection that is inside a transaction")
        yield conn
        return
    with opened(s) as c, transaction(c):
        yield c


# ---- reading ------------------------------------------------------------------------------------------------------------------------------------
def _stored(r: sqlite3.Row) -> Refused:
    return Refused("stored_data_bad", f"item {str(r['id'])[:60]} has unreadable stored data")


def _item(r: sqlite3.Row) -> Item:
    """A row as an ``Item``. Stored JSON is read with the strict seam; a row whose JSON or shape is bad raises ``Refused('stored_data_bad')``."""
    try:
        fields = None if r["fields_json"] is None else strictjson.loads(r["fields_json"])
        flags = strictjson.loads(r["flags_json"])
        failing = strictjson.loads(r["failing_fields_json"])
    except ValueError:
        raise _stored(r) from None
    if r["text_sha256"] != text_hash(r["source_text"]):
        raise _stored(r)
    if (fields is not None and not isinstance(fields, dict)) or not all(
        isinstance(x, list) and all(isinstance(v, str) for v in x) for x in (flags, failing)
    ):
        raise _stored(r)
    return Item(
        uid=r["uid"],
        id=r["id"],
        source_name=r["source_name"],
        source_sha256=r["source_sha256"],
        tenant_id=r["tenant_id"],
        state=r["state"],
        fields=fields,
        flags=tuple(flags),
        failing_fields=tuple(failing),
        source_text=r["source_text"],
        model_id=r["model_id"],
        tier=r["tier"],
        prompt_sha256=r["prompt_sha256"],
        cost_micro=r["cost_micro"],
        version=r["version"],
        created_at=r["created_at"],
    )


def _dumps(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def text_hash(text: str) -> str:
    """sha256 of the stored (normalised) invoice text, UTF-8. ``source_sha256`` stays the hash of the RAW file bytes; this one lets a read prove the
    text was not changed after it was stored (trigger (b) freezes both)."""
    return hashlib.sha256(text.encode("utf-8", "surrogatepass")).hexdigest()


def item_id(stem: str, source_sha256: str) -> str:
    """``<stem>-<first 8 hex of the source hash>`` (spec 7)."""
    return f"{stem}-{source_sha256[:ID_HEX]}"


def get_in(conn: sqlite3.Connection, item_id_: str) -> Item | None:
    """The item with this id on an open connection, or None."""
    r = conn.execute("SELECT * FROM items WHERE id = ?", (item_id_,)).fetchone()
    return None if r is None else _item(r)


def get_by_uid(conn: sqlite3.Connection, uid: int) -> Item | None:
    """The item with this uid on an open connection, or None."""
    r = conn.execute("SELECT * FROM items WHERE uid = ?", (uid,)).fetchone()
    return None if r is None else _item(r)


def get(s: settings.Settings, item_id_: str, *, conn: sqlite3.Connection | None = None) -> Item | None:
    """The item with this id, or None (a damaged row raises ``stored_data_bad``). With ``conn`` (for example from ``connect_readonly``) it reads through
    that connection and never opens its own."""
    if conn is not None:
        return get_in(conn, item_id_)
    with opened(s) as own:
        return get_in(own, item_id_)


def _rows(conn: sqlite3.Connection, sql: str, params: Sequence = ()) -> list[Item]:
    out = []
    for r in conn.execute(sql, params).fetchall():
        try:
            out.append(_item(r))
        except Refused:
            continue  # one damaged row must not hide the rest; ``unreadable_ids`` names it
    return out


def list_items(s: settings.Settings, state: str | None = None, *, conn: sqlite3.Connection | None = None) -> list[Item]:
    """Items in ``created_at`` order, optionally of one state. A row with unreadable stored data is left out (see ``unreadable_ids``). With ``conn`` it
    reads through that connection and never opens its own."""
    if conn is None:
        with opened(s) as own:
            return list_items(s, state, conn=own)
    if state is None:
        return _rows(conn, "SELECT * FROM items ORDER BY created_at, uid")
    return _rows(conn, "SELECT * FROM items WHERE state = ? ORDER BY created_at, uid", (state,))


def unreadable_ids(s: settings.Settings, *, conn: sqlite3.Connection | None = None) -> list[str]:
    """Ids of rows whose stored JSON or shape cannot be read (the page shows a count; nothing here can approve them). With ``conn`` it reads through
    that connection and never opens its own."""
    if conn is None:
        with opened(s) as own:
            return unreadable_ids(s, conn=own)
    bad = []
    for r in conn.execute("SELECT * FROM items ORDER BY uid").fetchall():
        try:
            _item(r)
        except Refused:
            bad.append(r["id"])
    return bad


def known_sources(s: settings.Settings, *, conn: sqlite3.Connection | None = None) -> frozenset[str]:
    """The ``source_sha256`` of every stored item (the scan skips a duplicate before it takes a slot, without hand-written SQL in the caller). With
    ``conn`` it reads through that connection and never opens its own."""
    if conn is None:
        with opened(s) as own:
            return known_sources(s, conn=own)
    return frozenset(r[0] for r in conn.execute("SELECT source_sha256 FROM items"))


def latest_decision(conn: sqlite3.Connection, item_uid: int) -> Decision | None:
    """The decision with the highest ``seq`` for this item, or None."""
    r = conn.execute("SELECT * FROM decisions WHERE item_uid = ? ORDER BY seq DESC LIMIT 1", (item_uid,)).fetchone()
    return None if r is None else Decision(**dict(r))


def approved_unexported(conn: sqlite3.Connection) -> list[Item]:
    """APPROVED items with no export row, in ``created_at`` order (the exporter's work list)."""
    return _rows(
        conn, "SELECT * FROM items WHERE state = 'APPROVED' AND uid NOT IN (SELECT item_uid FROM exports) ORDER BY created_at, uid"
    )


def exports_in_order(conn: sqlite3.Connection) -> list[Export]:
    """Every export receipt in ``seq`` order (the CSV is regenerated from this)."""
    return [Export(**dict(r)) for r in conn.execute("SELECT * FROM exports ORDER BY seq")]


def get_export(conn: sqlite3.Connection, item_uid: int) -> Export | None:
    """The receipt of this item, or None."""
    r = conn.execute("SELECT * FROM exports WHERE item_uid = ?", (item_uid,)).fetchone()
    return None if r is None else Export(**dict(r))


def export_by_row_id(conn: sqlite3.Connection, row_id: str) -> Export | None:
    """The receipt that holds this row id, or None."""
    r = conn.execute("SELECT * FROM exports WHERE row_id = ?", (row_id,)).fetchone()
    return None if r is None else Export(**dict(r))


# ---- writing ------------------------------------------------------------------------------------------------------------------------------------
def _insert(
    s: settings.Settings,
    source_name: str,
    source_sha256: str,
    source_text: str,
    tenant_id: str,
    stem: str,
    state: str,
    flag_codes: Sequence[str],
) -> Item | Duplicate:
    if tenant_id != s.tenant_id:
        raise ValueError("tenant_id is the deployment's tenant, never a request value")
    if not settings.is_name_allowed(stem, s.service.name_regex):
        raise Refused("bad_name", "the item stem is not an allowed name")
    codes = flagtable.sorted_codes(flag_codes)
    iid = item_id(stem, source_sha256)
    # Dedup key is the bytes alone (source_sha256 UNIQUE, spec 7): one tenant per deployment; a second tenant needs (tenant_id, sha) first.
    with opened(s) as conn, transaction(conn):
        dup = conn.execute("SELECT id FROM items WHERE source_sha256 = ?", (source_sha256,)).fetchone()
        if dup is not None:
            return Duplicate(dup["id"])
        if conn.execute("SELECT 1 FROM items WHERE id = ?", (iid,)).fetchone() is not None:
            raise Refused("id_collision", "another file already holds this item id")
        try:
            cur = conn.execute(
                "INSERT INTO items (id, source_name, source_sha256, tenant_id, state, flags_json, source_text, text_sha256, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (iid, source_name, source_sha256, tenant_id, state, _dumps(codes), source_text, text_hash(source_text), now_utc()),
            )
        except sqlite3.IntegrityError as e:
            raise _guard_refusal(e) from e
        return _item(conn.execute("SELECT * FROM items WHERE uid = ?", (cur.lastrowid,)).fetchone())


def insert_received(
    s: settings.Settings,
    source_name: str,
    source_sha256: str,
    source_text: str,
    tenant_id: str,
    stem: str,
    state: str = "RECEIVED",
    flags: Sequence[str] = (),
) -> Item | Duplicate:
    """Insert before any model call. ``state`` is RECEIVED, or NEEDS_PERSON with ``flags`` (errata 22). Identical bytes = ``Duplicate``.
    ``tenant_id`` must equal ``s.tenant_id`` (``ValueError`` otherwise)."""
    if state not in ("RECEIVED", "NEEDS_PERSON") or (state == "RECEIVED") == bool(flags):
        raise ValueError("state must be RECEIVED without flags, or NEEDS_PERSON with flags")
    return _insert(s, source_name, source_sha256, source_text, tenant_id, stem, state, flags)


def insert_flagged(
    s: settings.Settings, source_name: str, source_sha256: str, source_text: str, tenant_id: str, stem: str, flag: str
) -> Item | Duplicate:
    """A reader-flagged file (X18, X28) becomes a NEEDS_PERSON item at once, with no fields and no model call (errata 5)."""
    return _insert(s, source_name, source_sha256, source_text, tenant_id, stem, "NEEDS_PERSON", (flag,))


def _checked_record(s: settings.Settings, fields: dict | None) -> tuple[str | None, list[str]]:
    """(canonical JSON, failing field names). A record that fails the 6.2 validators, or does not survive a strict-JSON round trip (lone surrogate,
    NaN, duplicate keys, deep nesting), is not stored: the caller turns it into a flagged result without fields."""
    if fields is None:
        return None, []
    failing = validators.validate_record(fields, s.service.currencies)
    if failing:
        return None, failing
    text = _dumps(fields)
    try:
        if strictjson.loads(text) != fields:
            return None, [_RECORD_FIELD]
    except ValueError:
        return None, [_RECORD_FIELD]
    return text, []


def set_result(
    s: settings.Settings,
    item_uid: int,
    state: str,
    *,
    fields: dict | None,
    flags: Sequence[str],
    failing_fields: Sequence[str] = (),
    model_id: str | None,
    tier: str | None,
    prompt_sha256: str | None,
    cost_micro: int,
) -> Item:
    """RECEIVED -> READY (no flags, a valid record) or NEEDS_PERSON (flags). A record that fails the validators or a strict-JSON round trip is NOT
    stored: the result becomes NEEDS_PERSON with X10 and the failing field names (the one choke point, whatever the caller passed). Compare-and-set
    on ``state = 'RECEIVED'`` (``state_conflict`` otherwise)."""
    codes = flagtable.sorted_codes(flags)
    if state not in ("READY", "NEEDS_PERSON") or (state == "READY") != (not codes) or (state == "READY" and fields is None):
        raise ValueError("READY needs fields and no flags; NEEDS_PERSON needs flags")
    text, bad = _checked_record(s, fields)
    if fields is not None and text is None:
        state, codes, failing_fields = "NEEDS_PERSON", flagtable.sorted_codes([*codes, _REASON_FLAG]), bad
    with opened(s) as conn:
        with transaction(conn):
            try:
                cur = conn.execute(
                    "UPDATE items SET state=?, fields_json=?, flags_json=?, failing_fields_json=?, model_id=?, tier=?, prompt_sha256=?, "
                    "cost_micro=?, version=version+1 WHERE uid=? AND state='RECEIVED'",
                    (
                        state,
                        text,
                        _dumps(codes),
                        _dumps([*(failing_fields or ())]),
                        model_id,
                        tier,
                        prompt_sha256,
                        int(cost_micro),
                        item_uid,
                    ),
                )
            except sqlite3.IntegrityError as e:
                raise _guard_refusal(e) from e
            if cur.rowcount != 1:
                raise Refused("state_conflict", "the item is not waiting for a result")
        return _item(conn.execute("SELECT * FROM items WHERE uid = ?", (item_uid,)).fetchone())


def recover_received(s: settings.Settings, *, serve_lock_held) -> list[str]:
    """Start-up repair ONLY: every RECEIVED item (a crash before the result) becomes NEEDS_PERSON with L02. No model call. ``serve_lock_held`` is a
    zero-argument callable that answers whether this process holds the single-writer ``serve.lock`` (``serve`` passes the lock module's check): a call
    from anywhere else is refused, so a running scan's RECEIVED item is never turned into L02 under it."""
    if not callable(serve_lock_held) or serve_lock_held() is not True:
        raise Refused("state_conflict", "start-up repair needs the serve lock")
    with opened(s) as conn, transaction(conn):
        ids = [r["id"] for r in conn.execute("SELECT id FROM items WHERE state='RECEIVED' ORDER BY uid")]
        conn.execute(
            "UPDATE items SET state='NEEDS_PERSON', flags_json=?, version=version+1 WHERE state='RECEIVED'", (_dumps([RECOVERED_FLAG]),)
        )
        return ids


def apply_decision(
    conn: sqlite3.Connection, item: Item, decision: str, new_state: str, approver: str, reason: str | None, content_code: str, version: int
) -> Decision:
    """Inside the caller's transaction: write the decision row, then move the state with a compare-and-set on the version the person saw. A mismatch
    raises and the caller's rollback removes the decision row."""
    at = now_utc()
    conn.execute(
        "SAVEPOINT apply_decision"
    )  # a caller that catches the refusal and still commits must not keep a decision row without its state move
    try:
        cur = conn.execute(
            "INSERT INTO decisions (item_uid, decision, approver, reason, content_code, at) VALUES (?, ?, ?, ?, ?, ?)",
            (item.uid, decision, approver, reason, content_code, at),
        )
        moved = conn.execute(
            "UPDATE items SET state=?, version=version+1 WHERE uid=? AND version=? AND state IN ('READY', 'NEEDS_PERSON')",
            (new_state, item.uid, version),
        )
        if moved.rowcount != 1:
            raise Refused("stale_content", "the item changed since the form was shown")
    except BaseException as e:
        conn.execute("ROLLBACK TO apply_decision")
        conn.execute("RELEASE apply_decision")
        if isinstance(e, sqlite3.IntegrityError):
            raise _guard_refusal(e) from e
        raise
    conn.execute("RELEASE apply_decision")
    return Decision(cur.lastrowid, item.uid, decision, approver, reason, content_code, at)


def record_export(conn: sqlite3.Connection, item: Item, row_id: str, content_code: str, row_json: str, version: int) -> Export:
    """Inside the caller's transaction (a connection without one raises ``ValueError``): write the receipt row FIRST, then move the item to EXPORTED
    with a compare-and-set on ``version`` (which it bumps). The triggers refuse a receipt unless the item is APPROVED and its latest decision is an
    approve with this content code, and refuse EXPORTED without a receipt. The caller (the exporter, WP5) has already recomputed the content code and
    the approval rule: this is the storage step, not the check. Refused: ``row_id_conflict`` (another item holds this row id), ``already_exported``
    (this item has a receipt), ``stale_content`` (the version moved), ``state_conflict`` (a database guard)."""
    if not conn.in_transaction:
        raise ValueError("record_export needs a connection that is inside a transaction")
    if get_export(conn, item.uid) is not None:
        raise Refused("already_exported", "this item already has a receipt")
    if export_by_row_id(conn, row_id) is not None:
        raise Refused("row_id_conflict", "another item holds this row id")
    try:
        cur = conn.execute(
            "INSERT INTO exports (row_id, item_uid, content_code, row_json, at) VALUES (?, ?, ?, ?, ?)",
            (row_id, item.uid, content_code, row_json, now_utc()),
        )
        moved = conn.execute(
            "UPDATE items SET state='EXPORTED', version=version+1 WHERE uid=? AND version=? AND state='APPROVED'", (item.uid, version)
        )
    except sqlite3.IntegrityError as e:
        raise _guard_refusal(e) from e
    if moved.rowcount != 1:
        raise Refused("stale_content", "the item changed since the export was prepared")
    return Export(cur.lastrowid, row_id, item.uid, content_code, row_json, now_utc())


def _os_user() -> str:
    """The operating-system user, cut to the login-name alphabet (the purge record says who ran the command)."""
    try:
        name = re.sub(r"[^A-Za-z0-9._@-]", "_", getpass.getuser())[:64].lstrip("._@-")
    except (OSError, KeyError, ImportError):
        name = ""
    return name or "unknown"


def sum_cost_micro(s: settings.Settings) -> int:
    """Total of ``cost_micro`` over every item: the spend ledger's cross-check against the queue (spec 5.5). The one read of the queue that the spend
    guard needs, so it asks here instead of reading the file itself."""
    with opened(s) as conn:
        return int(conn.execute("SELECT COALESCE(SUM(cost_micro), 0) FROM items").fetchone()[0])


def purge(s: settings.Settings, item_id_: str, by: str | None = None, conn: sqlite3.Connection | None = None) -> None:
    """Remove one item and its text (RECEIVED, READY, NEEDS_PERSON or REJECTED, no export row) in one ``BEGIN IMMEDIATE``. Never touches
    ``decisions`` or ``exports``; writes one ``purges`` row (item id, who, when, state: no text). ``by`` defaults to the operating-system user and
    must match the login-name pattern. APPROVED and EXPORTED items (and their text) have no purge path. With ``conn`` the caller holds the
    transaction."""
    who = _os_user() if by is None else by
    if not isinstance(who, str) or not ACTOR_RE.fullmatch(who):
        raise ValueError("by must be a login name")
    with scope(s, conn) as c:
        r = c.execute("SELECT uid, state FROM items WHERE id = ?", (item_id_,)).fetchone()
        if r is None:
            raise Refused("not_found", "no such item")
        if r["state"] not in PURGE_STATES or c.execute("SELECT 1 FROM exports WHERE item_uid = ?", (r["uid"],)).fetchone():
            raise Refused("purge_refused", "approved or exported items are never purged")
        try:
            c.execute(
                "DELETE FROM item_mask_map WHERE item_uid = ?", (r["uid"],)
            )  # spans and key go with the text; trace rows stay (append-only)
            c.execute("DELETE FROM item_keys WHERE item_uid = ?", (r["uid"],))
            c.execute(
                "INSERT INTO purges (item_id, item_uid, state, purged_by, at) VALUES (?, ?, ?, ?, ?)",
                (item_id_, r["uid"], r["state"], who, now_utc()),
            )
            c.execute("DELETE FROM items WHERE uid = ?", (r["uid"],))
        except sqlite3.IntegrityError as e:
            raise _guard_refusal(e) from e


# ---- masking: spans, per-item key, trace rows (design WP2c B3, errata 72) -----------------------------------------------------------------------
_FP_RE = re.compile(r"[0-9a-f]{8}")
_KEY_RE = re.compile(r"[0-9a-f]{64}")
_MARK_RE = re.compile(r"<?[A-Z][A-Z0-9]*_[0-9]+>?")
_AT_RE = re.compile(r"[0-9T:.\-]{1,30}Z?")
_KINDS = ("IBAN", "BANK", "ROUTING", "CARD", "EMAIL", "PHONE", "PERSON", "ID", "SECRET")


@dataclass(frozen=True)
class MaskSpan:
    """One hidden value's place in ``items.source_text``: the mark, its kind, the character range, a keyed 8-hex fingerprint (an index, not a proof)
    and the detector version. It holds no value (``restore_map`` slices the stored text)."""

    placeholder: str
    kind: str
    span_start: int
    span_end: int
    fingerprint: str
    detector: str

    def __post_init__(self) -> None:
        ok = (
            isinstance(self.placeholder, str) and _MARK_RE.fullmatch(self.placeholder) is not None
            and self.kind in _KINDS
            and isinstance(self.span_start, int) and isinstance(self.span_end, int) and not isinstance(self.span_start, bool)
            and 0 <= self.span_start < self.span_end
            and isinstance(self.fingerprint, str) and _FP_RE.fullmatch(self.fingerprint) is not None
            and isinstance(self.detector, str) and 0 < len(self.detector) <= 80
        )  # fmt: skip
        if not ok:
            raise ValueError("a mask span has a bad field")


class TraceRow:
    """One stored step of an item's trace, read-only by convention (the public names have no setters and ``counts`` is a read-only copy; the private
    slots and ``object.__setattr__`` are not guarded, so ``add_trace`` checks the values again). The vocabulary is closed in code (SQL checks only ``result``):
    ``step`` is a step of ``trace_vocab.STEPS`` other than the log-only one, ``counts`` keys are ``trace_vocab.COUNT_KEYS`` with int values,
    ``fingerprints`` are (mark, 8-hex) pairs, ``reason_plain`` is empty or one of ``phrases.texts()`` (the template sentences; filled-in values are
    added at display time). Every violation raises ``ValueError``; ``add_trace`` validates the values it is about to write again."""

    __slots__ = ("_at", "_counts", "_fingerprints", "_reason_plain", "_result", "_step")

    def __init__(
        self,
        step: str,
        at: str,
        counts: Mapping[str, int] | None = None,
        fingerprints: Sequence[tuple[str, str]] = (),
        result: str = "info",
        reason_plain: str = "",
    ) -> None:
        self._step, self._at, self._result, self._reason_plain = step, at, result, reason_plain
        self._counts = MappingProxyType(dict(counts) if isinstance(counts, Mapping) else {})
        self._fingerprints = (
            tuple(tuple(p) if isinstance(p, (tuple, list)) else p for p in fingerprints)
            if isinstance(fingerprints, (tuple, list))
            else None
        )
        if counts is not None and not isinstance(counts, Mapping):
            raise ValueError("a trace row count is not a mapping")
        if self._fingerprints is None:
            raise ValueError("a trace row fingerprint list is not a list")
        _validate_row(self._step, self._at, self._counts, self._fingerprints, self._result, self._reason_plain)

    step = property(lambda self: self._step)
    at = property(lambda self: self._at)
    counts = property(lambda self: self._counts)
    fingerprints = property(lambda self: self._fingerprints)
    result = property(lambda self: self._result)
    reason_plain = property(lambda self: self._reason_plain)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, TraceRow) and self._key() == other._key()

    __hash__ = None  # type: ignore[assignment]

    def _key(self) -> tuple:
        return (self._step, self._at, dict(self._counts), self._fingerprints, self._result, self._reason_plain)

    def __repr__(self) -> str:
        return f"TraceRow(step={self._step!r}, result={self._result!r}, at={self._at!r})"


def _validate_row(step: object, at: object, counts: Mapping, fingerprints: object, result: object, reason_plain: object) -> None:
    """Raise ``ValueError`` unless every field is inside the closed vocabulary (used by ``TraceRow`` and again by ``add_trace`` on the values it writes)."""
    if step not in trace_vocab.STEPS or step in trace_vocab.LOG_ONLY_STEPS or result not in trace_vocab.RESULTS:
        raise ValueError("a trace row has a step or result outside the closed vocabulary")
    if not isinstance(at, str) or _AT_RE.fullmatch(at) is None:
        raise ValueError("a trace row has a bad time")
    if not isinstance(counts, Mapping) or not all(
        k in trace_vocab.COUNT_KEYS and isinstance(v, int) and not isinstance(v, bool) for k, v in counts.items()
    ):
        raise ValueError("a trace row count has a key outside the closed vocabulary or a value that is not an int")
    if not isinstance(fingerprints, tuple) or not all(
        isinstance(p, tuple) and len(p) == 2 and all(isinstance(x, str) for x in p)
        and _MARK_RE.fullmatch(p[0]) is not None and _FP_RE.fullmatch(p[1]) is not None
        for p in fingerprints
    ):  # fmt: skip
        raise ValueError("a trace row fingerprint pair is malformed")
    if not isinstance(reason_plain, str) or (
        reason_plain != "" and reason_plain not in phrases.texts()
    ):  # built per call: about 4 microseconds; the segregation scan bans module-level caches
        raise ValueError("a trace row reason is not one of the allowed sentences")


def _fp(key: bytes, value: str) -> str:
    return hashlib.blake2b(value.encode("utf-8", "surrogatepass"), key=key, digest_size=4).hexdigest()


@contextmanager
def _snapshot(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """All reads of the block see one snapshot (a deferred BEGIN; WAL pins it at the first read), so a purge between two statements cannot give a
    half-read answer. A connection that is already inside a transaction is used as it is."""
    if conn.in_transaction:
        yield conn
        return
    conn.execute("BEGIN")
    try:
        yield conn
    finally:
        if conn.in_transaction:
            conn.execute("ROLLBACK")


def _read_spans(c: sqlite3.Connection, uid: int) -> list[MaskSpan]:
    """The stored spans of one item by position. A damaged row (a value outside what ``MaskSpan`` allows) raises ``ValueError``."""
    rows = c.execute(
        "SELECT placeholder, kind, span_start, span_end, fingerprint, detector FROM item_mask_map WHERE item_uid = ? ORDER BY span_start, placeholder",
        (uid,),
    ).fetchall()
    return [MaskSpan(*tuple(r)) for r in rows]


def _stored_by_id(item_id_: str) -> Refused:
    return Refused("stored_data_bad", f"item {str(item_id_)[:60]} has unreadable stored data")


def _key_of(c: sqlite3.Connection, item_id_: str) -> bytes | None:
    r = c.execute("SELECT k.fp_key FROM item_keys k JOIN items i ON i.uid = k.item_uid WHERE i.id = ?", (item_id_,)).fetchone()
    if r is None:
        return None
    if not isinstance(r[0], str) or _KEY_RE.fullmatch(r[0]) is None:  # a BLOB, an integer, upper case or a wrong length is damage
        raise _stored_by_id(item_id_)
    return bytes.fromhex(r[0])


def item_key(s: settings.Settings, item_id_: str, *, conn: sqlite3.Connection | None = None) -> bytes | None:
    """The per-item fingerprint key (32 bytes) of this item, or None (no key stored: reader-flagged items, unknown ids). A stored key that is not 64
    hex characters raises ``stored_data_bad``. Callers are limited to ``workqueue.py``, ``pipeline.py`` and ``tracelog.py`` (a repo test)."""
    if conn is None:
        with opened(s) as own:
            return item_key(s, item_id_, conn=own)
    with _snapshot(conn):
        return _key_of(conn, item_id_)


def store_mask(
    s: settings.Settings, item_uid: int, document_text: str, key: bytes, spans: Sequence[MaskSpan], conn: sqlite3.Connection | None = None
) -> None:
    """Store the spans and the key of a RECEIVED item. Refused as ``SelfCheckFailed('mask_failed')``: a text whose hash differs from the item's
    ``text_sha256``, a span outside the text or whose fingerprint is not the keyed one of its slice, a bad key, an item that is not RECEIVED, stored
    rows that are damaged. Idempotent: the same key and spans again is a no-op; anything different is ``mask_failed`` (the code rule; the triggers are
    the second line)."""
    if not isinstance(key, bytes) or len(key) != 32 or not all(isinstance(x, MaskSpan) for x in spans):
        raise SelfCheckFailed("mask_failed")
    with scope(s, conn) as c:
        r = c.execute("SELECT state, text_sha256 FROM items WHERE uid = ?", (item_uid,)).fetchone()
        if r is None or r["state"] != "RECEIVED" or r["text_sha256"] != text_hash(document_text):
            raise SelfCheckFailed("mask_failed")
        for sp in spans:
            if sp.span_end > len(document_text) or sp.fingerprint != _fp(key, document_text[sp.span_start : sp.span_end]):
                raise SelfCheckFailed("mask_failed")
        stored_key = c.execute("SELECT fp_key FROM item_keys WHERE item_uid = ?", (item_uid,)).fetchone()
        want = sorted(spans, key=lambda x: (x.span_start, x.placeholder))
        if stored_key is not None:
            try:
                same = stored_key[0] == key.hex() and _read_spans(c, item_uid) == want
            except ValueError:  # a damaged stored span row
                raise SelfCheckFailed("mask_failed") from None
            if not same:
                raise SelfCheckFailed("mask_failed")
            return
        if c.execute("SELECT 1 FROM item_mask_map WHERE item_uid = ? LIMIT 1", (item_uid,)).fetchone() is not None:
            raise SelfCheckFailed("mask_failed")
        try:
            c.execute("INSERT INTO item_keys (item_uid, fp_key) VALUES (?, ?)", (item_uid, key.hex()))
            c.executemany(
                "INSERT INTO item_mask_map (item_uid, placeholder, kind, span_start, span_end, fingerprint, detector) VALUES (?, ?, ?, ?, ?, ?, ?)",
                [(item_uid, x.placeholder, x.kind, x.span_start, x.span_end, x.fingerprint, x.detector) for x in want],
            )
        except sqlite3.IntegrityError:
            raise SelfCheckFailed("mask_failed") from None


def restore_map(s: settings.Settings, item_id_: str, *, conn: sqlite3.Connection | None = None) -> Mapping[str, str] | None:
    """APPROVER-ONLY reader (a repo test limits its callers to ``review_page.py`` and tests): mark -> original text, sliced from the stored text. None
    when the item is unknown or has no stored key (never masked); an empty mapping when it was masked with no span. A span whose slice no longer
    matches its keyed fingerprint, a damaged span row, or two spans of one mark with different text raise ``stored_data_bad``. One snapshot."""
    if conn is None:
        with opened(s) as own:
            return restore_map(s, item_id_, conn=own)
    with _snapshot(conn):
        item = get_in(conn, item_id_)
        key = None if item is None else _key_of(conn, item_id_)
        if item is None or key is None:
            return None
        out: dict[str, str] = {}
        try:
            spans = _read_spans(conn, item.uid)
        except ValueError:
            raise _stored_by_id(item_id_) from None
        for sp in spans:
            value = item.source_text[sp.span_start : sp.span_end]
            if (
                len(value) != sp.span_end - sp.span_start
                or _fp(key, value) != sp.fingerprint
                or out.setdefault(sp.placeholder, value) != value
            ):
                raise _stored_by_id(item_id_)
        return MappingProxyType(out)


def all_spans_for_scan(s: settings.Settings, *, conn: sqlite3.Connection | None = None) -> list[tuple[int, str, str]]:
    """OPERATOR-ONLY reader (callers limited to ``logscan.py`` and tests): (item_uid, mark, original text) for every distinct hidden surface string of
    every item, for ``intake logscan``. A span that no longer fits its stored text is skipped (the scan then has one value fewer, never a crash).
    One snapshot."""
    if conn is None:
        with opened(s) as own:
            return all_spans_for_scan(s, conn=own)
    out: list[tuple[int, str, str]] = []
    seen: set[tuple[int, str]] = set()
    with _snapshot(conn):
        rows = conn.execute(
            "SELECT m.item_uid, m.placeholder, m.span_start, m.span_end, i.source_text FROM item_mask_map m JOIN items i ON i.uid = m.item_uid "
            "ORDER BY m.item_uid, m.span_start, m.placeholder"
        ).fetchall()
    for r in rows:
        value = r[4][r[2] : r[3]]
        if (r[0], r[1]) not in seen and value:
            seen.add((r[0], r[1]))
            out.append((r[0], r[1], value))
    return out


def add_trace(s: settings.Settings, item_uid: int, row: TraceRow, conn: sqlite3.Connection | None = None) -> bool:
    """Append one trace row. The row's values are read once, copied and validated again here (a ``TraceRow`` is read-only by convention, and a subclass or a forged object could lie). Returns
    False, writing nothing, when the item is APPROVED or EXPORTED (a decided item takes no row; the trigger is the second line). The state is read in
    the same transaction as the insert. An unknown item raises ``not_found``."""
    if not isinstance(row, TraceRow):
        raise ValueError("add_trace takes a TraceRow")
    # read each property ONCE and copy the containers; check the copies; write the same copies (a subclass that answers differently the second
    # time cannot get a different value past the check)
    step, at, result, reason = row.step, row.at, row.result, row.reason_plain
    raw_counts, raw_fps = row.counts, row.fingerprints
    counts = dict(raw_counts) if isinstance(raw_counts, Mapping) else raw_counts
    fps = tuple(tuple(p) if isinstance(p, (tuple, list)) else p for p in raw_fps) if isinstance(raw_fps, (tuple, list)) else raw_fps
    _validate_row(step, at, counts, fps, result, reason)
    if step in trace_vocab.DERIVED_STEPS:
        raise ValueError("decision and export rows are derived, never stored")
    with scope(s, conn) as c:
        r = c.execute("SELECT state FROM items WHERE uid = ?", (item_uid,)).fetchone()
        if r is None:
            raise Refused("not_found", "no such item")
        if r["state"] in ("APPROVED", "EXPORTED"):
            return False
        try:
            c.execute(
                "INSERT INTO item_trace (item_uid, step, at, counts_json, fingerprints_json, result, reason_plain) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (item_uid, step, at, _dumps(counts), _dumps([list(p) for p in fps]), result, reason),
            )
        except sqlite3.IntegrityError as e:
            raise _guard_refusal(e) from e
    return True


def _stored_trace(r: sqlite3.Row, item_id_: str) -> TraceRow:
    try:
        counts = strictjson.loads(r["counts_json"])
        fps = strictjson.loads(r["fingerprints_json"])
        return TraceRow(r["step"], r["at"], counts, tuple(tuple(p) for p in fps), r["result"], r["reason_plain"])
    except (ValueError, TypeError):
        raise _stored_by_id(item_id_) from None


def trace_rows(s: settings.Settings, item_id_: str, *, conn: sqlite3.Connection | None = None) -> list[TraceRow]:
    """The item's trace: stored rows by ``seq``, then the decision rows (derived from ``decisions``, by their ``seq``), then the export rows (derived
    from ``exports``). Unknown item: an empty list. A damaged stored row raises ``stored_data_bad``. One snapshot. Trace rows are kept when an item is
    purged and are never shown for an item that does not exist; a raw INSERT that re-uses the uid of a purged item would re-attach them (nothing in
    this code does that: ``uid`` is AUTOINCREMENT and every insert goes through ``insert_received``)."""
    if conn is None:
        with opened(s) as own:
            return trace_rows(s, item_id_, conn=own)
    with _snapshot(conn):
        u = conn.execute("SELECT uid FROM items WHERE id = ?", (item_id_,)).fetchone()
        if u is None:
            return []
        uid = u[0]
        text = phrases.phrases()
        out = [_stored_trace(r, item_id_) for r in conn.execute("SELECT * FROM item_trace WHERE item_uid = ? ORDER BY seq", (uid,))]
        for d in conn.execute("SELECT decision, at FROM decisions WHERE item_uid = ? ORDER BY seq", (uid,)):
            out.append(TraceRow("decision", d["at"], {}, (), "pass", text["approved" if d["decision"] == "approve" else "rejected"]))
        for e in conn.execute("SELECT at FROM exports WHERE item_uid = ? ORDER BY seq", (uid,)):
            out.append(TraceRow("export", e["at"], {}, (), "pass", text["exported"]))
        return out


def selfcheck_reason(s: settings.Settings, item_id_: str, *, conn: sqlite3.Connection | None = None) -> str | None:
    """The self-check code (one of ``selfcheck_codes.SELFCHECK_CODES``) behind an M01/M02 item: scanning the item's rows from the latest back, the
    first row with result ``fail`` whose ``reason_plain`` is the plain sentence of a self-check code gives that code. Failed rows with any other
    reason are skipped. None when no such row exists."""
    by_text = {v: k for k, v in _SELFCHECK_PLAIN.items()}
    for row in reversed([x for x in trace_rows(s, item_id_, conn=conn) if x.result == "fail"]):
        if row.reason_plain in by_text:
            return by_text[row.reason_plain]
    return None
