"""The execution path (controls C3 and C4). The only module that imports `psycopg`.

Rules, each with a test in tests/demo_askdata/test_pgsource_layers.py:

* Every statement this module sends travels the EXTENDED protocol, because a simple-protocol string can carry
  `COMMIT; BEGIN READ WRITE; INSERT ...; COMMIT` and escape the read-only transaction (verified, hazard test).
  The user query goes only through a named server-side cursor (`DECLARE ... CURSOR FOR <canonical>`, which
  rejects stacking with 42601); our own fixed queries use `prepare=True` (which rejects stacking too).
  `_send` holds the ONLY `execute` call in this file; an `ast` test fails if a second one appears.
* Order inside `run`: connect (read-only transaction), then `current_setting('transaction_read_only')` must be
  `on` (else raise and send nothing), then DECLARE and FETCH.
* Watchdog: a monotonic deadline checked before every fetch plus a timer thread calling `cancel()` for a
  statement blocked in the server; the timer is cancelled and joined BEFORE rollback and close.
* Caps: rows and bytes. Errors reach callers as SQLSTATE codes only, never the server's message (it can echo data).
* The SHA-256 and the shown SQL are of the canonical SELECT; the wire text is `DECLARE "<name>" CURSOR FOR `
  plus that canonical text.
"""

from __future__ import annotations

import hashlib
import secrets
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import psycopg

from askdata.safe_text import clean
from hadavin_sdk.store.postgres import tls_mode

VERIFY_SQL = Path(__file__).resolve().parent.parent / "db" / "verify_checks.sql"
WATCHDOG_NAME = "askdata-watchdog"


class PgError(Exception):
    """A database or guard failure. `sqlstate` is the 5-character code (or None for a connection failure)."""

    def __init__(self, sqlstate: str | None, what: str) -> None:
        super().__init__(f"{what} (SQLSTATE {sqlstate or 'none'})")
        self.sqlstate = sqlstate
        self.what = what


@dataclass(frozen=True)
class Limits:
    statement_timeout_s: float = 10.0
    max_rows: int = 1000
    max_bytes: int = 1_000_000
    batch: int = 200


@dataclass
class RunResult:
    columns: list[str]
    rows: list[tuple]  # string cells are cleaned for display; result_sha256 is over the raw values
    truncated: bool
    result_sha256: str
    sql_sha256: str
    elapsed_s: float = 0.0
    byte_count: int = 0
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CheckRow:
    check: str
    ok: bool
    detail: str


def _send(cur: Any, sql: str, *, prepare: bool) -> None:
    """The single call site that sends SQL. A server-side cursor takes no options (it sends DECLARE through the
    extended protocol); an ordinary cursor is told to prepare, which refuses multi-statement text."""
    cur.execute(sql, **({"prepare": True} if prepare else {}))


def _close(conn: psycopg.Connection) -> None:
    """Roll back and close. A late cancel from the watchdog can still reach the server and make the ROLLBACK fail;
    closing the connection ends the transaction anyway, so that failure is ignored."""
    try:
        conn.rollback()
    except psycopg.Error:
        pass
    finally:
        conn.close()


def _fail(err: psycopg.Error) -> PgError:
    return PgError(getattr(err, "sqlstate", None), type(err).__name__)


class PgSource:
    def __init__(self, dsn: str, *, limits: Limits | None = None) -> None:
        self._dsn = dsn
        self.limits = limits or Limits()

    def _connect(self) -> psycopg.Connection:
        kwargs: dict[str, Any] = {
            "autocommit": False,
            "connect_timeout": 5,
            "application_name": "askdata",
            "keepalives": 1,
            "keepalives_idle": 10,
            "keepalives_interval": 5,
            "keepalives_count": 3,
        }
        mode = tls_mode(self._dsn)
        if mode:
            kwargs["sslmode"] = mode
        try:
            conn = psycopg.connect(self._dsn, **kwargs)
        except psycopg.Error as err:
            raise _fail(err) from None
        conn.read_only = True  # the first statement psycopg sends is BEGIN READ ONLY
        return conn

    def _guard(self, conn: psycopg.Connection) -> None:
        with conn.cursor() as cur:
            _send(cur, "SELECT current_setting('transaction_read_only')", prepare=True)
            row = cur.fetchone()
        if not row or row[0] != "on":
            raise PgError("25006", "transaction is not read-only")

    def verify_readonly(self) -> list[CheckRow]:
        """Run db/verify_checks.sql (the same text the DBA script embeds) over this app's own connection."""
        conn = self._connect()
        try:
            self._guard(conn)
            with conn.cursor() as cur:
                _send(cur, VERIFY_SQL.read_text(encoding="utf-8"), prepare=True)
                return [CheckRow(str(r[0]), bool(r[1]), str(r[2])) for r in cur.fetchall()]
        except psycopg.Error as err:
            raise _fail(err) from None
        finally:
            _close(conn)

    def run(
        self, canonical_sql: str, *, sql_sha256: str | None = None, limits: Limits | None = None
    ) -> RunResult:
        """Run one canonical SELECT. Does NOT validate: the caller passes validator output (tests pass hostile
        text on purpose to prove the layers below the validator hold)."""
        lim = limits or self.limits
        digest = hashlib.sha256(canonical_sql.encode("utf-8")).hexdigest()
        if sql_sha256 is not None and sql_sha256 != digest:
            raise PgError(None, "hash mismatch between validated and executed SQL")
        start = time.monotonic()
        deadline = start + lim.statement_timeout_s
        conn = self._connect()
        timer = threading.Timer(lim.statement_timeout_s, conn.cancel)
        timer.name = WATCHDOG_NAME
        timer.daemon = True
        try:
            self._guard(conn)
            timer.start()
            return self._fetch(conn, canonical_sql, digest, lim, start, deadline)
        except psycopg.Error as err:
            raise _fail(err) from None
        finally:
            timer.cancel()
            if timer.is_alive():
                timer.join(5)  # cancel() can block on the network; do not hang the caller
            _close(conn)

    def _fetch(
        self,
        conn: psycopg.Connection,
        sql: str,
        digest: str,
        lim: Limits,
        start: float,
        deadline: float,
    ) -> RunResult:
        raw_hash = hashlib.sha256()
        rows: list[tuple] = []
        total_bytes, truncated = 0, False
        name = f"askdata_{secrets.token_hex(6)}"
        with conn.cursor(name) as cur:
            _send(cur, sql, prepare=False)
            columns = [clean(d.name) for d in (cur.description or [])]
            while not truncated:
                if time.monotonic() >= deadline:
                    raise PgError("57014", "statement timeout (watchdog)")
                want = min(lim.batch, lim.max_rows + 1 - len(rows))
                batch = cur.fetchmany(want)
                if not batch:
                    break
                for raw in batch:
                    size = sum(len(str(c)) for c in raw)
                    if len(rows) >= lim.max_rows or total_bytes + size > lim.max_bytes:
                        truncated = True
                        break
                    total_bytes += size
                    raw_hash.update(repr(raw).encode("utf-8"))
                    rows.append(tuple(clean(c) if isinstance(c, str) else c for c in raw))
        return RunResult(
            columns,
            rows,
            truncated,
            raw_hash.hexdigest(),
            digest,
            elapsed_s=time.monotonic() - start,
            byte_count=total_bytes,
        )
