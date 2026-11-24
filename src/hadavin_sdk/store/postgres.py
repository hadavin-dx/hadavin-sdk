"""Postgres store (`pip install hadavin-sdk[pg]`). Same Protocol as `memory`; compare-and-set is in SQL, so it
holds across processes. The schema comes from `hadavin-sdk migrate` (`store/migrate.py`), never from here.

Connect pattern ported from WARDEN `audit.py:_pg_connect` (main a1e76cbf): with `iam_auth` and no password in
the DSN, the login is a 15-minute RDS IAM token and TLS is required.

Neutral protocol: the PostgreSQL wire protocol and SQL (any Postgres: RDS, Cloud SQL, Azure, self-hosted).
"""

from __future__ import annotations

import ipaddress
import logging
import os
import re
import tempfile
import threading
import uuid
from collections.abc import Callable, Sequence
from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from pydantic import BaseModel

from hadavin_sdk import defaults
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.models import (
    OPEN_STATES,
    ApprovalDecision,
    ApprovalRequest,
    ApprovalStatus,
    AuditEvent,
    DeadLetter,
    GateDecision,
    KillSwitch,
    OpenStop,
    Plan,
    Run,
    RunState,
    SpendReservation,
    TickState,
    ToolCallRecord,
    now,
)
from hadavin_sdk.store.protocol import (
    BookingDayRefused,
    ExpiredHolds,
    NotFound,
    SpendCapExceeded,
    SpendRelease,
    StaleState,
    StoreUnavailable,
    check_expiry_age,
    check_purge_bound,
    check_reservation_id,
    check_spend_amount,
    check_spend_cap,
    check_spend_day,
    check_store_id,
    clean_spend_amount,
)

_LOG = logging.getLogger("hadavin_sdk.store")


_VERIFIED_TLS = frozenset({"verify-ca", "verify-full"})


def _is_local(parts: dict) -> bool:
    """Unix socket or loopback only. A host from PGHOST/hostaddr counts; anything unknown is remote."""
    hosts = str(parts.get("host") or parts.get("hostaddr") or os.environ.get("PGHOST") or "")
    if not hosts or hosts.startswith("/"):
        return True
    for h in hosts.split(","):
        if h == "localhost":
            continue
        try:
            if not ipaddress.ip_address(h).is_loopback:
                return False
        except ValueError:
            return False
    return True


def tls_mode(
    dsn: str, *, iam_auth: bool = False, sslmode: str | None = None, sslrootcert: str | None = None
) -> str | None:
    """The sslmode to connect with. Loopback and unix sockets keep the setting or the DSN's. Any other host
    defaults to `verify-full` (the server's certificate and name are checked, so credentials cannot be
    captured by an impostor); an explicit weaker `sslmode` is an opt-down for demo. With iam_auth (a bearer
    token) only `verify-full` or `verify-ca` is accepted. A verified mode needs the CA bundle."""
    parts = conninfo_to_dict(dsn)
    mode = sslmode or parts.get("sslmode")
    if not iam_auth and _is_local(parts):
        return mode
    mode = mode or "verify-full"
    if iam_auth and mode not in _VERIFIED_TLS:
        raise ConfigError(
            "store postgres: iam_auth needs a verified server "
            f"(sslmode verify-full or verify-ca), not {mode}"
        )
    if mode in _VERIFIED_TLS and not (sslrootcert or parts.get("sslrootcert")):
        raise ConfigError(
            f"store postgres: sslmode {mode} needs the server's CA bundle: set sslrootcert (a file) or "
            "sslrootcert_secret_name (a PEM in the secrets backend), or opt down with sslmode for demo"
        )
    return mode


def ca_file(settings, resolve) -> str | None:
    """The CA bundle path: the setting, or the PEM from the secrets backend written to a private temp file
    (a CA bundle is public; the file is 0600 only because mkstemp makes it so)."""
    if not settings.sslrootcert_secret_name:
        return settings.sslrootcert
    fd, path = tempfile.mkstemp(prefix="hadavin-ca-", suffix=".pem")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(resolve(settings.sslrootcert_secret_name))
    return path


PasswordSource = Callable[[str, int, str], str]  # (host, port, user) -> a short-lived password


def password_source(iam_auth: bool, region: str | None) -> PasswordSource | None:
    """The sign-in helper: None (the DSN's own password), or RDS IAM from `store/auth_aws.py`, the only
    module of the store that imports an AWS SDK (lock-in audit 2026-10-31 #5)."""
    if not iam_auth:
        return None
    try:
        from hadavin_sdk.store import auth_aws
    except ModuleNotFoundError as exc:
        if (exc.name or "").startswith("hadavin_sdk"):
            raise
        raise ConfigError(
            "store postgres with iam_auth needs: pip install hadavin-sdk[aws]"
        ) from exc
    return auth_aws.rds_iam(region)


# default_transaction_isolation is also set by SET SESSION CHARACTERISTICS above; listing it here reads it back, and
# the audit chain relies on it: its advisory-lock wait must end with a fresh snapshot (a repeatable-read snapshot
# taken before the wait would see a stale last seq: duplicate seq 23505 / guard 23514, quarantined as a poison row).
_SESSION_PINS = (
    ("default_transaction_read_only", "off"),
    ("synchronous_commit", "on"),
    ("default_transaction_isolation", "'read committed'"),
)


def connect(
    dsn: str,
    *,
    iam_auth: bool = False,
    region: str | None = None,
    sslmode: str | None = None,
    sslrootcert: str | None = None,
) -> psycopg.Connection:
    extra: dict[str, Any] = {}
    if mode := tls_mode(dsn, iam_auth=iam_auth, sslmode=sslmode, sslrootcert=sslrootcert):
        extra["sslmode"] = mode
    if sslrootcert:
        extra["sslrootcert"] = sslrootcert
    if iam_auth:
        parts = conninfo_to_dict(dsn)
        # The migration role may log in with a password; the runtime never (refused in build()).
        if not parts.get("password"):
            password = password_source(True, region)
            extra["password"] = password(
                parts["host"], int(parts.get("port") or 5432), parts["user"]
            )
    conn = psycopg.connect(dsn, autocommit=True, connect_timeout=10, **extra)
    # Plan hashes include created_at: datetimes must come back in UTC whatever the server's TimeZone is.
    conn.execute("SET TIME ZONE 'UTC'")
    # Every writer relies on READ COMMITTED (a conditional UPDATE re-checks its WHERE after a row-lock wait); a
    # server or role default of REPEATABLE READ would turn that wait into an error, so the session pins it.
    conn.execute("SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL READ COMMITTED")
    # A role or database default must not weaken the session after login: a read-only default would make a stop fail,
    # `synchronous_commit = off` could lose an acknowledged stop on a crash. SET at session level wins over those
    # defaults; each pin is read back with SHOW and a server that did not take it refuses the connection.
    for setting, value in _SESSION_PINS:
        conn.execute(f"SET {setting} = {value}")
        got = conn.execute(f"SHOW {setting}").fetchone()[0]
        if got != value.strip("'"):
            conn.close()
            raise ConfigError(f"the database session did not take {setting} = {value}")
    return conn


_PIN = re.compile(r"search_path\s*=\s*(.*?)(?=\s+-c\s|\s+--|$)")
_STOP_TABLES = ("kill_switch", "kill_switch_stops", "kill_switch_clears")


def names_of(text: str) -> list[str]:
    """The schema names of a search_path value as the server reads them: a quoted name keeps its case and `""` is one
    quote, an unquoted name is folded to lower case; without the implicit pg_catalog and pg_temp."""
    out: list[str] = []
    for m in re.finditer(r'\s*(?:"((?:[^"]|"")*)"|([^,"]*?))\s*(?:,|$)', text):
        quoted, bare = m.group(1), m.group(2)
        name = quoted.replace('""', '"') if quoted is not None else (bare or "").strip().lower()
        if name and name != "pg_catalog" and not name.startswith("pg_temp"):
            out.append(name)
    return out


def _names(text: str) -> list[str]:
    return names_of(text)


def expected_schemas(dsn: str, schema: str | None) -> list[str]:
    """The schemas this store is configured for: `settings.db_schema`, else what the DSN pins, else `public`. A
    setting that disagrees with the DSN's pin is a configuration error."""
    pinned: list[str] = []
    options = re.sub(
        r"\\(.)", r"\1", conninfo_to_dict(dsn).get("options") or ""
    )  # libpq: \\<char> is <char>
    if m := _PIN.search(options):
        pinned = _names(m.group(1))
    if schema and pinned and pinned != [schema]:
        raise ConfigError(
            f"store postgres: backends.store.db_schema is {schema!r} but the DSN pins search_path to "
            f"{', '.join(pinned)}; make them the same"
        )
    return [schema] if schema else pinned or ["public"]


def verify_schema(conn: psycopg.Connection, expected: list[str]) -> str:
    """Refuse to start unless the connection's effective search_path is exactly `expected` and the stop tables are
    in `current_schema()`. A role may change its OWN default path (`ALTER ROLE r SET search_path`); without this
    a changed default would make the process read a decoy stop table. Returns current_schema()."""
    schema, effective = conn.execute(
        "SELECT pg_catalog.current_schema(), pg_catalog.current_schemas(false)"
    ).fetchone()
    if not schema:
        raise ConfigError(
            "store postgres: the search_path names no schema that exists (effective search_path of this login: "
            f"empty; the store is configured for {', '.join(expected)})"
        )
    effective = [n for n in effective if n != "pg_catalog" and not n.startswith("pg_temp")]
    if effective != expected or schema != expected[0]:
        raise ConfigError(
            f"store postgres: the effective search_path of this login is {', '.join(effective) or 'empty'} "
            f"(current_schema() is {schema!r}) but the store is configured for {', '.join(expected)}. "
            "backends.store.db_schema is the EXPECTED schema (the check), it does not choose the schema of the "
            "login. Make the login really use it: pin it in the DSN (options=-c search_path=<schema>), or make "
            "the role default equal to it (ALTER ROLE <login> SET search_path = <schema>; "
            "hadavin-sdk migrate does this for this database when it names the role), then set db_schema to "
            "the same schema"
        )
    found = {
        r[0]
        for r in conn.execute(
            "SELECT c.relname FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = %s AND c.relkind IN ('r','p') AND c.relname = ANY(%s)",
            (schema, list(_STOP_TABLES)),
        ).fetchall()
    }
    if missing := [t for t in _STOP_TABLES if t not in found]:
        raise ConfigError(
            f"store postgres: kill_switch not found in current_schema() = {schema!r} (missing relations: "
            f"{', '.join(missing)}): the stop state is not in the schema this store reads. Run hadavin-sdk migrate for that schema, or fix the "
            "search_path of the login"
        )
    return schema


_ALL_TABLE_RIGHTS = ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER")
_COLUMN_RIGHTS = ("SELECT", "INSERT", "UPDATE", "REFERENCES")  # what a column grant can give


_CLOSURE = (
    "WITH RECURSIVE closure(oid) AS ("
    " SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolname = current_user"
    " UNION SELECT m.roleid FROM pg_catalog.pg_auth_members m JOIN closure c ON m.member = c.oid)"
)
_WARNED_OWNER: set[str] = set()
_RIGHTS_QUERY = (
    _CLOSURE + " SELECT DISTINCT c.oid, p.priv FROM closure r CROSS JOIN pg_catalog.pg_class c"  # noqa: S608
    " CROSS JOIN unnest(%s::text[]) AS p(priv)"
    " WHERE c.oid = ANY(%s) AND (pg_catalog.has_table_privilege(r.oid, c.oid, p.priv)"
    " OR (p.priv = ANY(%s) AND pg_catalog.has_any_column_privilege(r.oid, c.oid, p.priv)))"
)
_EXECUTE_QUERY = (
    _CLOSURE  # noqa: S608
    + " SELECT s.sig, bool_or(p.oid IS NOT NULL AND pg_catalog.has_function_privilege(r.oid, p.oid, 'EXECUTE'))"
    " FROM unnest(%s::text[]) AS s(sig)"
    " CROSS JOIN LATERAL (SELECT pg_catalog.to_regprocedure(pg_catalog.quote_ident(%s) || '.' || s.sig)::oid AS oid)"
    " AS p CROSS JOIN closure r GROUP BY s.sig"
)


def _scoped_tables(conn: psycopg.Connection, schema: str, tables: Sequence[str]):
    """[(oid, name)] of `tables` in `schema` when the CURRENT login is a restricted one, else None (a superuser, or a
    member of the tables' owner: the single-role dev setup, outside the guarantee; the owner case logs a WARNING)."""
    rows = conn.execute(
        "SELECT c.oid, c.relname, pg_catalog.pg_has_role(current_user, c.relowner, 'MEMBER'),"
        " (SELECT r.rolsuper FROM pg_catalog.pg_roles r WHERE r.rolname = current_user)"
        " FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace"
        " WHERE n.nspname = %s AND c.relkind IN ('r','p') AND c.relname = ANY(%s) ORDER BY c.relname",
        (schema, list(tables)),
    ).fetchall()
    missing = sorted(set(tables) - {name for _, name, _, _ in rows})
    if missing and schema not in _WARNED_OWNER:
        _LOG.warning(
            "store postgres: tables not found in schema %r, their rights are not checked at start: %s",
            schema,
            ", ".join(missing),
        )
    if not rows or rows[0][3] is None:
        return None
    # judged table by table: a login that owns (or is a member of the owner of) some tables is exempt for those only
    kept = [(oid, name) for oid, name, owns, _ in rows if not owns]
    if (rows[0][3] or len(kept) < len(rows)) and schema not in _WARNED_OWNER:
        _WARNED_OWNER.add(schema)
        skipped = [name for _, name, owns, _ in rows if owns or rows[0][3]]
        _LOG.warning(
            "store postgres: the login is a superuser or owns (is a member of the owner of) tables of schema "
            "%r: the start checks of the stop and money rights are skipped for %s (single-role dev setup; run "
            "migrate with named roles for a production login)",
            schema,
            ", ".join(skipped),
        )
    return [] if rows[0][3] else kept


def _rights_held(
    conn: psycopg.Connection,
    oids: Sequence[int],
    rights: Sequence[str],
    column_rights: Sequence[str],
) -> set[tuple[int, str]]:
    """(table oid, right) pairs held by the login OR by any role in its membership closure, whatever the inherit
    option (a NOINHERIT login, or INHERIT FALSE with SET TRUE, can still SET ROLE to the group and write): table level
    and, for `column_rights`, column level."""
    rows = conn.execute(
        _RIGHTS_QUERY,
        (list(rights), list(oids), list(column_rights)),
    ).fetchall()
    return {(oid, right) for oid, right in rows}


def own_stop_rights_problems(conn: psycopg.Connection, schema: str) -> list[str]:
    """What the CURRENT login can do on the three stop tables beyond what `GRANTS` gives the runtime role, however
    it got it (a direct grant, a column grant, a role it is a member of with or without inheriting, PUBLIC). Strings
    like `UPDATE on kill_switch`: the right and the table, never a value. [] for a superuser or a member of the
    tables' owner: that login owns the tables and is outside the guarantee (migrate warns when no roles are named)."""
    from hadavin_sdk.store.migrate import GRANTS  # late: migrate imports this module

    scope = _scoped_tables(conn, schema, _STOP_TABLES)
    if not scope:
        return []
    rights = list(_ALL_TABLE_RIGHTS)
    if conn.info.server_version >= 170000:
        rights.append("MAINTAIN")
    held = _rights_held(conn, [oid for oid, _ in scope], rights, _COLUMN_RIGHTS)
    problems = []
    for oid, name in scope:
        allowed = {x.strip() for x in GRANTS[name].runtime.split(",") if x.strip()}
        problems += [f"{r} on {name}" for r in rights if r not in allowed and (oid, r) in held]
    return problems


_MONEY_TABLES = ("spend", "spend_month", "spend_reservations", "hadavin_caps", "hadavin_limits")
_MONEY_WRITE_RIGHTS = ("INSERT", "UPDATE", "DELETE", "TRUNCATE", "TRIGGER")
_RUNTIME_MARK_FUNCTION = "hadavin_reserve_spend(text, text, date, numeric, text)"
# The functions the runtime login must NOT run: the cap setter (caps role) and the two the release / purge roles run.
_MONEY_FORBIDDEN_FUNCTIONS = (
    "hadavin_set_cap(text, numeric, numeric, text)",
    "hadavin_release_expired_spend(text, date)",
    "hadavin_purge_spend_reservations(timestamptz)",
)


def own_money_rights_problems(conn: psycopg.Connection, schema: str) -> list[str]:
    """What the CURRENT login (or any role in its membership closure, inherit option or not) can do on the money
    tables (INSERT, UPDATE, DELETE, TRUNCATE, table or column level) and which money functions it may EXECUTE although
    only the owner-side roles may (set_cap, release, purge). Strings like `UPDATE on spend` or `EXECUTE on
    hadavin_set_cap`. [] for a superuser or a member of the tables' owner (same convention as the stop-table check)."""
    scope = _scoped_tables(conn, schema, _MONEY_TABLES)
    if not scope:
        return []
    held = _rights_held(conn, [oid for oid, _ in scope], _MONEY_WRITE_RIGHTS, ("INSERT", "UPDATE"))
    problems = [
        f"{r} on {name}" for oid, name in scope for r in _MONEY_WRITE_RIGHTS if (oid, r) in held
    ]
    # Function rights are judged only for a login that acts as the runtime (some role of its closure may EXECUTE the
    # booking): the purge, release and reset logins build a store too and legitimately hold their own function.
    signatures = (_RUNTIME_MARK_FUNCTION, *_MONEY_FORBIDDEN_FUNCTIONS)
    rows = conn.execute(
        _EXECUTE_QUERY,
        (list(signatures), schema),
    ).fetchall()
    may = {sig: ok for sig, ok in rows}
    if may.get(_RUNTIME_MARK_FUNCTION):
        problems += [
            f"EXECUTE on {sig.split('(')[0]}" for sig in _MONEY_FORBIDDEN_FUNCTIONS if may.get(sig)
        ]
    return problems


def build(settings, deps) -> PostgresStore:
    """Table factory: the DSN is a platform secret named in the settings (never the executor's)."""
    password_source(
        settings.iam_auth, settings.region
    )  # a missing `aws` extra fails here, with the hint
    dsn = deps.resolve(settings.dsn_secret_name)
    if settings.iam_auth and conninfo_to_dict(dsn).get("password"):
        raise ConfigError(
            "store postgres: with iam_auth the DSN must not carry a password (the login is an IAM token)"
        )
    try:
        conn = connect(
            dsn,
            iam_auth=settings.iam_auth,
            region=settings.region,
            sslmode=settings.sslmode,
            sslrootcert=ca_file(settings, deps.resolve),
        )
    except psycopg.OperationalError as exc:
        # The class only: driver messages can carry the host and user.
        raise StoreUnavailable(
            f"store postgres: cannot connect ({exc.__class__.__name__})"
        ) from None
    try:
        schema = verify_schema(conn, expected_schemas(dsn, settings.db_schema))
        if getattr(settings, "_login_role", "runtime") == "runtime" and (
            problems := own_stop_rights_problems(conn, schema)
        ):
            raise ConfigError(
                "store postgres: this login holds rights on the stop tables that only the reset role may hold ("
                + "; ".join(problems)
                + "). A login that can write there can clear a stop. Revoke them from the login and from the "
                "roles it is a member of, or run hadavin-sdk migrate with --runtime-role naming this login "
                "(it resets the grants and refuses what stays)"
            )
        if getattr(settings, "_login_role", "runtime") == "runtime" and (
            problems := own_money_rights_problems(conn, schema)
        ):
            raise ConfigError(
                "store postgres: this login holds rights on the money tables or functions that only the owner side "
                "may hold ("
                + "; ".join(problems)
                + "). A login that can write there can lower a booked amount or change a cap. Run hadavin-sdk "
                "migrate with --runtime-role naming this login (it resets the grants and refuses what stays)"
            )
    except BaseException:
        conn.close()
        raise
    # A store call that waits on a row lock for longer than this fails loudly instead of holding the process-wide
    # store lock. Set here, not in `connect()`: the migrate path shares `connect()` and its statements may run long.
    conn.execute(
        sql.SQL("SET lock_timeout = {}").format(sql.Literal(defaults.STORE_LOCK_TIMEOUT_MS))
    )
    return PostgresStore(conn)


def _row(model: BaseModel) -> dict[str, Any]:
    """Model -> column values: dicts/lists as JSONB, enums as their text, everything else as is."""
    py, js = model.model_dump(), model.model_dump(mode="json")
    out = {}
    for k, v in py.items():
        if isinstance(v, dict | list):
            out[k] = Jsonb(js[k])
        elif isinstance(v, Enum):
            out[k] = js[k]
        else:
            out[k] = v
    return out


_SCHEMA_TABLES = ("spend", "spend_month", "spend_reservations")


def _money_error(
    exc: psycopg.errors.DatabaseError, reservation_id: str | None = None
) -> BaseException:
    """Map what a money definer function raised to the store's exceptions. `HD***` has no named psycopg class, so
    the branch is on `exc.sqlstate`. Anything not listed is returned unchanged (the caller fails closed)."""
    code = exc.sqlstate
    if code == "HD001":  # cap reached; the message is `day` or `month`
        which = str(exc.diag.message_primary or "")
        return SpendCapExceeded(which if which in ("day", "month") else "day")
    if code == "HD002":  # unknown or another agent's id: the same error, nothing is revealed
        return NotFound(reservation_id)
    if code == "HD003":  # counter row missing; the transaction rolled back
        return RuntimeError("spend counter row missing")
    if code == "HD004":  # a limit row missing: fail closed, the schema is not set up
        return ConfigError(
            f"store postgres: money limits unavailable ({code}); run hadavin-sdk migrate"
        )
    if code == "HD005":  # no cap row for this agent: fail closed
        return ConfigError("store postgres: no cap for this agent: run limits sync-caps")
    if code == "23505":  # duplicate reservation id
        return StaleState(f"spend reservation exists: {reservation_id}")
    if code is not None and code.startswith(
        "HD"
    ):  # a code of this family nobody mapped: psycopg raises it as an
        # OperationalError (looks like a lost connection), so it is named here and fails closed
        return ConfigError(f"store postgres: unexpected money function error ({code})")
    if code == "22023":  # the function refused an argument the Python check let through
        if str(exc.diag.message_primary or "") == "invalid argument: p_day window":
            return BookingDayRefused("spend argument refused by the database (p_day)")
        return ValueError("spend argument refused by the database")
    return exc


class PostgresStore:
    # ponytail: one connection behind one lock per process; a pool (psycopg_pool) when throughput matters.
    # A dropped connection fails the call (the run ends safely); reconnect-on-error arrives with S11 hosting.
    def __init__(self, conn: psycopg.Connection) -> None:
        self._db = conn
        self._lock = threading.Lock()
        # Resolved once: the stop-state statements name this schema (`current_schema()` never answers pg_temp).
        self._schema = conn.execute("SELECT current_schema()").fetchone()[0]
        if not self._schema:
            raise ConfigError("store postgres: the search_path names no schema that exists")

    # --- generic helpers ---------------------------------------------------------------------------------

    def _exec(self, query, params=()) -> psycopg.Cursor:
        return self._db.cursor(row_factory=dict_row).execute(query, params)

    def _insert(self, table: str, model: BaseModel, upsert_on: str | None = None) -> None:
        row = _row(model)
        cols = [sql.Identifier(c) for c in row]
        query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
            sql.Identifier(table),
            sql.SQL(", ").join(cols),
            sql.SQL(", ").join(sql.Placeholder() * len(row)),
        )
        if upsert_on:
            query += sql.SQL(" ON CONFLICT ({}) DO UPDATE SET {}").format(
                sql.Identifier(upsert_on),
                sql.SQL(", ").join(sql.SQL("{0} = EXCLUDED.{0}").format(c) for c in cols),
            )
        with self._lock:
            self._exec(query, list(row.values()))

    def _select(self, model: type[BaseModel], table: str, where: str, params, tail: str = ""):
        """`where` and `tail` are fixed SQL text from this module; values always go through `params`."""
        cols = sql.SQL(", ").join(sql.Identifier(c) for c in model.model_fields)
        query = sql.SQL("SELECT {} FROM {} WHERE {}{}").format(
            cols, sql.Identifier(table), sql.SQL(where), sql.SQL(tail)
        )
        with self._lock:
            rows = self._exec(query, params).fetchall()
        return [model.model_validate(r) for r in rows]

    def _one(self, model: type[BaseModel], table: str, key: str, value: str):
        found = self._select(model, table, f"{key} = %s", (value,))
        if not found:
            raise NotFound(value)
        return found[0]

    # --- runs --------------------------------------------------------------------------------------------

    def create_run(self, run: Run) -> None:
        try:
            self._insert("runs", run)
        except psycopg.errors.UniqueViolation:
            raise StaleState(f"run exists: {run.run_id}") from None

    def get_run(self, run_id: str) -> Run:
        return self._one(Run, "runs", "run_id", run_id)

    def _missing_or_stale(self, table: str, key: str, value: str, stale: str) -> Exception:
        with self._lock:
            exists = self._exec(
                sql.SQL("SELECT 1 FROM {} WHERE {} = %s").format(
                    sql.Identifier(table), sql.Identifier(key)
                ),
                (value,),
            ).fetchone()
        return StaleState(stale) if exists else NotFound(value)

    def transition(
        self, run_id: str, expected: RunState, new: RunState, reason_code: str | None = None
    ) -> Run:
        with self._lock:
            row = self._exec(
                "UPDATE runs SET state = %s, reason_code = %s, updated_at = %s "
                "WHERE run_id = %s AND state = %s RETURNING run_id",
                (new.value, reason_code, now(), run_id, expected.value),
            ).fetchone()
        if row is None:
            raise self._missing_or_stale("runs", "run_id", run_id, f"{run_id}: expected {expected}")
        return self.get_run(run_id)

    def _update_run(self, query: str, value: Any, run_id: str) -> None:
        with self._lock:
            cur = self._exec(query, (value, run_id))
        if cur.rowcount == 0:
            raise NotFound(run_id)

    def add_cost(self, run_id: str, usd: Decimal) -> None:
        usd = clean_spend_amount(usd)
        self._update_run("UPDATE runs SET cost_usd = cost_usd + %s WHERE run_id = %s", usd, run_id)

    def touch(self, run_id: str) -> None:
        self._update_run("UPDATE runs SET updated_at = %s WHERE run_id = %s", now(), run_id)

    def list_runs(self, state: RunState, updated_before: datetime, limit: int = 100) -> list[Run]:
        return self._select(
            Run,
            "runs",
            "state = %s AND updated_at < %s",
            (state.value, updated_before, limit),
            " ORDER BY updated_at LIMIT %s",
        )

    # --- plans and gate decisions --------------------------------------------------------------------------

    def save_plan(self, plan: Plan) -> None:
        self._insert("plans", plan, upsert_on="run_id")

    def get_plan(self, run_id: str) -> Plan:
        return self._one(Plan, "plans", "run_id", run_id)

    def save_gate_decision(self, decision: GateDecision) -> None:
        try:
            self._insert("gate_decisions", decision)  # append-only: the runtime role has no UPDATE
        except psycopg.errors.UniqueViolation:
            raise StaleState(f"gate decision exists: {decision.run_id}") from None

    def get_gate_decision(self, run_id: str) -> GateDecision:
        return self._one(GateDecision, "gate_decisions", "run_id", run_id)

    # --- approvals -----------------------------------------------------------------------------------------

    def save_approval_request(self, req: ApprovalRequest) -> None:
        self._insert("approval_requests", req, upsert_on="approval_id")

    def get_approval_request(self, approval_id: str) -> ApprovalRequest:
        return self._one(ApprovalRequest, "approval_requests", "approval_id", approval_id)

    def update_approval_request(
        self, req: ApprovalRequest, expected_status: str, expected_step: int
    ) -> None:
        row = _row(req)
        sets = sql.SQL(", ").join(
            sql.SQL("{} = %s").format(sql.Identifier(c)) for c in row if c != "approval_id"
        )
        query = sql.SQL(
            "UPDATE approval_requests SET {} WHERE approval_id = %s AND status = %s AND current_step = %s"
        ).format(sets)
        values = [v for c, v in row.items() if c != "approval_id"]
        with self._lock:
            cur = self._exec(query, [*values, req.approval_id, expected_status, expected_step])
        if cur.rowcount == 0:
            raise self._missing_or_stale(
                "approval_requests",
                "approval_id",
                req.approval_id,
                f"{req.approval_id}: not {expected_status}/{expected_step}",
            )

    def record_decision(
        self,
        decision: ApprovalDecision,
        req: ApprovalRequest,
        expected_status: str,
        expected_step: int,
    ) -> None:
        drow, rrow = _row(decision), _row(req)
        insert = sql.SQL("INSERT INTO approval_decisions ({}) VALUES ({})").format(
            sql.SQL(", ").join(sql.Identifier(c) for c in drow),
            sql.SQL(", ").join(sql.Placeholder() * len(drow)),
        )
        update = sql.SQL(
            "UPDATE approval_requests SET {} WHERE approval_id = %s AND status = %s AND current_step = %s"
        ).format(
            sql.SQL(", ").join(
                sql.SQL("{} = %s").format(sql.Identifier(c)) for c in rrow if c != "approval_id"
            )
        )
        values = [v for c, v in rrow.items() if c != "approval_id"]
        lost = False
        try:
            with self._lock, self._db.transaction():
                self._exec(insert, list(drow.values()))
                cur = self._exec(update, [*values, req.approval_id, expected_status, expected_step])
                if cur.rowcount == 0:
                    lost = True
                    raise psycopg.Rollback()  # the insert above is undone with it
        except psycopg.errors.UniqueViolation:
            lost = True
        if lost:
            raise self._missing_or_stale(
                "approval_requests",
                "approval_id",
                req.approval_id,
                f"{req.approval_id}: not {expected_status}/{expected_step}",
            )

    def list_due_approvals(self, now: datetime) -> list[ApprovalRequest]:
        return self._select(
            ApprovalRequest,
            "approval_requests",
            "status = 'PENDING' AND step_expires_at <= %s",
            (now,),
        )

    def save_approval_decision(self, decision: ApprovalDecision) -> None:
        try:
            self._insert("approval_decisions", decision)
        except psycopg.errors.UniqueViolation:
            raise StaleState(f"decision exists: {decision.approval_id}/{decision.step}") from None

    def get_approval_decision(self, approval_id: str) -> ApprovalDecision | None:
        found = self._select(
            ApprovalDecision,
            "approval_decisions",
            "approval_id = %s",
            (approval_id,),
            " ORDER BY seq DESC LIMIT 1",
        )
        return found[0] if found else None

    def list_approvals(self, statuses: set[ApprovalStatus]) -> list[ApprovalRequest]:
        return self._select(
            ApprovalRequest,
            "approval_requests",
            "status = ANY(%s)",
            (sorted(statuses),),
            " ORDER BY created_at",
        )

    # --- dead letters, spend, kill switch ------------------------------------------------------------------

    def add_dead_letter(self, dl: DeadLetter) -> None:
        self._insert("dead_letters", dl)

    def list_dead_letters(self, run_id: str) -> list[DeadLetter]:
        return self._select(DeadLetter, "dead_letters", "run_id = %s", (run_id,), " ORDER BY seq")

    def add_spend(self, agent_id: str, day: date, usd: Decimal) -> tuple[Decimal, Decimal]:
        """Day and month counters, each one atomic upsert, in one transaction: exact under concurrency. The
        bookings are done by the definer function `hadavin_add_spend` (the function is the authority; the Python
        check is the early, friendly refusal)."""
        check_store_id(agent_id, "agent_id")  # the same early refusals as the memory store
        check_spend_day(day)
        usd = clean_spend_amount(usd)  # a bad amount is a ValueError before any SQL; -0 becomes 0
        try:
            with self._lock, self._db.transaction():
                row = self._exec(
                    self._money_call("hadavin_add_spend", "%s::text, %s::date, %s::numeric"),
                    (agent_id, day, usd),
                ).fetchone()
        except psycopg.errors.DatabaseError as exc:
            raise _money_error(exc) from None
        return Decimal(row["day_usd"]), Decimal(row["month_usd"])

    def spend_totals(self, agent_id: str, day: date) -> tuple[Decimal, Decimal]:
        with self._lock:
            d = self._exec(
                self._t("SELECT usd FROM {spend} WHERE agent_id = %s AND day = %s"), (agent_id, day)
            ).fetchone()
            m = self._exec(
                self._t("SELECT usd FROM {spend_month} WHERE agent_id = %s AND month = %s"),
                (agent_id, day.replace(day=1)),
            ).fetchone()
        return (Decimal(d["usd"]) if d else Decimal(0)), (Decimal(m["usd"]) if m else Decimal(0))

    def _t(self, text: str) -> sql.Composed:
        """A statement whose spend, spend_month and spend_reservations names carry the schema. An unqualified name
        is looked up in the session's temporary schema first, so a temporary table of that name would shadow it."""
        s = sql.Identifier(self._schema)
        return sql.SQL(text).format(
            **{t: sql.SQL("{}.{}").format(s, sql.Identifier(t)) for t in _SCHEMA_TABLES}
        )

    def _money_call(self, function: str, placeholders: str) -> sql.Composed:
        """`SELECT * FROM <schema>.<function>(<placeholders>)`: a definer function called by its schema-qualified
        name (the same reasoning as `_t`: an unqualified name is looked up in the temporary schema first)."""
        return sql.SQL("SELECT * FROM {}.{}({})").format(
            sql.Identifier(self._schema), sql.Identifier(function), sql.SQL(placeholders)
        )

    def _reserve_call(self) -> sql.Composed:
        """The ONE place that names `hadavin_reserve_spend` and its argument list (five arguments: the caps are read from `hadavin_caps` by the function, never passed)."""
        return self._money_call(
            "hadavin_reserve_spend",
            "%s::text, %s::text, %s::date, %s::numeric, %s::text",
        )

    def _stop_tables(self) -> dict[str, sql.Composed]:
        """The three stop-state relations with the schema named. An unqualified name is looked up in the session's
        temporary schema first, so a temporary table called `kill_switch` would shadow the real one."""
        s = sql.Identifier(self._schema)
        return {
            "flag": sql.SQL("{}.kill_switch").format(s),
            "stops": sql.SQL("{}.kill_switch_stops").format(s),
            "clears": sql.SQL("{}.kill_switch_clears").format(s),
            "resets": sql.SQL("{}.kill_switch_resets").format(s),
        }

    def get_kill_switch(self) -> KillSwitch:
        t = self._stop_tables()
        cols = sql.SQL(", ").join(sql.Identifier(c) for c in KillSwitch.model_fields)
        with self._lock:
            rows = self._exec(
                sql.SQL("SELECT {} FROM {flag} WHERE id = 1").format(cols, **t)
            ).fetchall()
        found = [KillSwitch.model_validate(r) for r in rows]
        if not found:  # migrate seeds the row: its absence means a broken schema, so fail closed
            _LOG.error(
                "kill_switch row missing: treating the kill switch as ON; run hadavin-sdk migrate"
            )
            return KillSwitch(on=True, by="system:kill_switch_row_missing")
        if found[0].on:
            return found[0]
        with (
            self._lock
        ):  # the flag is off: any stop with no clear still means ON (the oldest one is reported)
            # Every clear names one distinct stop (primary key plus foreign key), so "some stop has no clear" is
            # exactly count(stops) > count(clears): two index-only counts, however many cleared stops there are.
            # No time watermark: a stop hidden because its ts is at or below it (a planted old ts, a hand-inserted
            # stop after a reset) must still count as open, so there is no such table (0009, review N3). The
            # slow oldest-first anti-join runs only when a stop really is open (the switch is ON anyway).
            row = self._exec(
                sql.SQL(
                    "SELECT (SELECT count(*) FROM {stops}) > (SELECT count(*) FROM {clears}) AS any_open"
                ).format(**t)
            ).fetchone()
            stop = None
            if row["any_open"]:
                stop = self._exec(
                    sql.SQL(
                        'SELECT s."by", s.ts FROM {stops} s WHERE NOT EXISTS '
                        "(SELECT 1 FROM {clears} c WHERE c.stop_id = s.id) ORDER BY s.ts, s.id LIMIT 1"
                    ).format(**t)
                ).fetchone()
        if stop is not None:
            return KillSwitch(on=True, by=stop["by"], ts=stop["ts"])
        return found[0]

    def set_kill_switch(self, ks: KillSwitch) -> None:
        t = self._stop_tables()
        if ks.on:  # a stop is one INSERT: all the runtime role may do to the stop state
            with self._lock:  # no ts: the database clock sets it (the column default)
                self._exec(sql.SQL('INSERT INTO {stops} ("by") VALUES (%s)').format(**t), (ks.by,))
            return
        # A reset (the reset role only): the old flag off and one clear per stop the clear statement can see, in
        # one transaction. A stop committed after that statement began has no clear, so the switch stays ON; a
        # stop committed before it began (also one committed after the caller's audit intent) is cleared.
        with self._lock, self._db.transaction():
            flag = self._exec(
                sql.SQL('UPDATE {flag} SET "on" = FALSE, "by" = %s, ts = %s WHERE id = 1').format(
                    **t
                ),
                (ks.by, ks.ts),
            )
            if (
                flag.rowcount != 1
            ):  # a broken schema reads ON whatever is cleared: say so, clear nothing
                raise ConfigError(
                    "kill_switch row missing: the kill switch stays ON and nothing was cleared; "
                    "run hadavin-sdk migrate"
                )
            self._exec(
                sql.SQL(
                    'INSERT INTO {clears} (stop_id, "by", ts) SELECT s.id, %s, %s '
                    "FROM {stops} s WHERE NOT EXISTS "
                    "(SELECT 1 FROM {clears} c WHERE c.stop_id = s.id) "
                    "ON CONFLICT (stop_id) DO NOTHING"
                ).format(**t),
                (ks.by, ks.ts),
            )

    def open_stops(self) -> list[OpenStop]:
        t = self._stop_tables()
        with self._lock:
            rows = self._exec(
                sql.SQL(
                    'SELECT s.id::text AS id, s."by", s.ts FROM {stops} s WHERE NOT EXISTS '
                    "(SELECT 1 FROM {clears} c WHERE c.stop_id = s.id) ORDER BY s.ts, s.id"
                ).format(**t)
            ).fetchall()
        return [OpenStop.model_validate(r) for r in rows]

    def clear_stops(self, by: str, stop_ids: Sequence[str], audit_seq: int | None = None) -> None:
        """Compare-and-clear (the reset role only): the old flag off and one clear row for each of exactly these
        stop ids and one `kill_switch_resets` row (who, the ids it really cleared, the audit chain seq when the caller
        knows it), all in one transaction. A stop that is not in `stop_ids` (set after the caller read the open stops)
        gets no clear and keeps the switch ON."""
        t = self._stop_tables()
        ids = [
            str(uuid.UUID(str(i))) for i in stop_ids
        ]  # a malformed id is an error here, not in the database
        stamp = now()
        with self._lock, self._db.transaction():
            flag = self._exec(
                sql.SQL('UPDATE {flag} SET "on" = FALSE, "by" = %s, ts = %s WHERE id = 1').format(
                    **t
                ),
                (by, stamp),
            )
            if (
                flag.rowcount != 1
            ):  # a broken schema reads ON whatever is cleared: say so, clear nothing
                raise ConfigError(
                    "kill_switch row missing: the kill switch stays ON and nothing was cleared; "
                    "run hadavin-sdk migrate"
                )
            cleared: list[str] = []
            if ids:
                done = self._exec(
                    sql.SQL(
                        'WITH c AS (INSERT INTO {clears} (stop_id, "by", ts) SELECT s.id, %s, %s '
                        "FROM {stops} s WHERE s.id = ANY(%s::uuid[]) AND NOT EXISTS "
                        "(SELECT 1 FROM {clears} x WHERE x.stop_id = s.id) "
                        "ON CONFLICT (stop_id) DO NOTHING RETURNING stop_id) "
                        "SELECT array_agg(c.stop_id::text) AS ids FROM c"
                    ).format(**t),
                    (by, stamp, ids),
                ).fetchone()
                cleared = list(done["ids"] or [])
            # The reset's own record (the reset role holds INSERT only, so no RETURNING).
            self._exec(
                sql.SQL(
                    'INSERT INTO {resets} ("by", at, cleared_ids, audit_seq) VALUES (%s, %s, %s::uuid[], %s)'
                ).format(**t),
                (by, stamp, cleared, audit_seq),
            )

    def get_tick_state(self, step: str) -> TickState | None:
        found = self._select(TickState, "tick_state", "step = %s", (step,))
        return found[0] if found else None

    def save_tick_state(self, state: TickState) -> None:
        self._insert("tick_state", state, upsert_on="step")

    # --- evidence (K5) ------------------------------------------------------------------------------------------

    def add_tool_call(self, call: ToolCallRecord) -> None:
        try:
            self._insert("tool_calls", call)
        except psycopg.errors.UniqueViolation:
            raise StaleState(f"tool call exists: {call.call_id}") from None

    def list_tool_calls(self, run_id: str) -> list[ToolCallRecord]:
        return self._select(
            ToolCallRecord, "tool_calls", "run_id = %s", (run_id,), " ORDER BY created_at, call_id"
        )

    def _purge(self, table: str, column: str, before: datetime, keep: frozenset[str]) -> int:
        query = sql.SQL("DELETE FROM {} WHERE {} < %s AND NOT (run_id = ANY(%s))").format(
            sql.Identifier(table), sql.Identifier(column)
        )
        with self._lock:
            return self._exec(query, (before, sorted(keep))).rowcount

    def purge_tool_calls(self, before: datetime, *, keep_run_ids: frozenset[str]) -> int:
        return self._purge("tool_calls", "created_at", before, keep_run_ids)

    def put_redaction_map(self, run_id: str, mapping: dict[str, str]) -> None:
        with self._lock:
            self._exec(
                "INSERT INTO redaction_maps (run_id, mapping, updated_at) VALUES (%s, %s, %s) "
                "ON CONFLICT (run_id) DO UPDATE SET mapping = EXCLUDED.mapping, "
                "updated_at = EXCLUDED.updated_at",
                (run_id, Jsonb(mapping), now()),
            )

    def get_redaction_map(self, run_id: str) -> dict[str, str] | None:
        with self._lock:
            row = self._exec(
                "SELECT mapping FROM redaction_maps WHERE run_id = %s", (run_id,)
            ).fetchone()
        return dict(row["mapping"]) if row else None

    def purge_redaction_maps(
        self, before: datetime, *, keep_run_ids: frozenset[str], keep_open: bool = True
    ) -> int:
        """Aged from the run's last state change (the map's own time when the run is unknown); the maps of runs
        that can still move (OPEN_STATES) are kept unless `keep_open` is false. A run parked in NEEDS_PERSON cannot
        move, so its map ages like a finished run's."""
        with self._lock:
            if keep_open:
                open_states = sorted(s.value for s in OPEN_STATES)
                return self._exec(
                    "DELETE FROM redaction_maps m WHERE NOT (m.run_id = ANY(%s)) AND "
                    "COALESCE((SELECT r.updated_at FROM runs r WHERE r.run_id = m.run_id), "
                    "m.updated_at) < %s AND NOT EXISTS (SELECT 1 FROM runs r "
                    "WHERE r.run_id = m.run_id AND r.state = ANY(%s))",
                    (sorted(keep_run_ids), before, open_states),
                ).rowcount
            return self._exec(
                "DELETE FROM redaction_maps m WHERE NOT (m.run_id = ANY(%s)) AND "
                "COALESCE((SELECT r.updated_at FROM runs r WHERE r.run_id = m.run_id), "
                "m.updated_at) < %s",
                (sorted(keep_run_ids), before),
            ).rowcount

    # --- spend reservations (0007) --------------------------------------------------------------------------
    # The cap check and the booking are one conditional UPDATE per counter, in the transaction that adds the
    # reservation row. The UPDATE relies on READ COMMITTED (its re-check after a row-lock wait), which
    # `connect()` sets for the whole session.

    def reserve_spend(
        self,
        reservation_id: str,
        agent_id: str,
        day: date,
        usd: Decimal,
        *,
        day_cap: Decimal,
        month_cap: Decimal,
        run_id: str | None = None,
    ) -> None:
        check_store_id(agent_id, "agent_id")
        if run_id is not None:
            check_store_id(run_id, "run_id")
        check_spend_day(day)
        check_reservation_id(reservation_id)
        check_spend_amount(usd)
        check_spend_cap(day_cap)  # before any SQL: a NaN cap would compare as no cap
        check_spend_cap(month_cap)
        # The two caps are validated and then IGNORED: on Postgres the `hadavin_caps` row of the agent wins (the
        # runtime cannot write it). The memory store compares the argument: a documented divergence.
        try:
            with self._lock, self._db.transaction():
                self._exec(
                    self._reserve_call(),
                    (reservation_id, agent_id, day, usd, run_id),
                )
        except psycopg.errors.DatabaseError as exc:
            raise _money_error(exc, reservation_id) from None

    def settle_spend(
        self, reservation_id: str, actual_usd: Decimal, *, agent_id: str
    ) -> tuple[SpendReservation, bool]:
        check_reservation_id(reservation_id)
        check_spend_amount(actual_usd)
        check_store_id(agent_id, "agent_id")
        try:
            with self._lock, self._db.transaction():
                # The claim comes first, inside the function: a second caller waits on the row lock, finds the
                # row settled, claims nothing and gets the stored row back unchanged (claimed = false).
                row = self._exec(
                    self._money_call("hadavin_settle_spend", "%s::text, %s::numeric, %s::text"),
                    (reservation_id, actual_usd, agent_id),
                ).fetchone()
        except psycopg.errors.DatabaseError as exc:
            raise _money_error(exc, reservation_id) from None
        claimed = row.pop("claimed")
        return SpendReservation.model_validate(row), bool(claimed)

    def expire_spend_reservations(self, older_than_s: int) -> int:
        """The age is measured on the database clock; the counters do not move."""
        check_expiry_age(older_than_s)
        try:
            with self._lock, self._db.transaction():
                row = self._exec(
                    self._money_call("hadavin_expire_spend_reservations", "%s::integer"),
                    (older_than_s,),
                ).fetchone()
        except psycopg.errors.DatabaseError as exc:
            raise _money_error(exc) from None
        return int(row["hadavin_expire_spend_reservations"])

    def expired_holds(self, older_than_s: int) -> list[ExpiredHolds]:
        """Read-only (the runtime login may call it): the expired, unreleased holds closed more than
        `older_than_s` seconds ago on the database clock, grouped by agent and day, at most 1000 groups."""
        check_expiry_age(older_than_s)
        try:
            with self._lock, self._db.transaction():
                rows = self._exec(
                    self._money_call("hadavin_expired_holds", "%s::integer"),
                    (older_than_s,),
                ).fetchall()
        except psycopg.errors.DatabaseError as exc:
            raise _money_error(exc) from None
        return [ExpiredHolds(r["agent_id"], r["day"], int(r["holds"]), r["usd"]) for r in rows]

    def purge_spend_reservations(self, before: datetime) -> int:
        """SETTLED rows only (a settled row, or one released by 0008: settled at 0). An expired hold nobody
        settled is KEPT: it is still booked, and a late settle must find it (E11 M3). Run by the purge role,
        which reads `status` and `closed_at` and nothing else."""
        check_purge_bound(before)
        try:
            with self._lock, self._db.transaction():
                row = self._exec(
                    self._money_call("hadavin_purge_spend_reservations", "%s::timestamptz"),
                    (before,),
                ).fetchone()
        except psycopg.errors.DatabaseError as exc:
            raise _money_error(exc) from None
        return int(row["hadavin_purge_spend_reservations"])

    def release_expired_spend(
        self, agent_id: str, day: date, actor: str, audit: Any
    ) -> SpendRelease:
        """Release the EXPIRED holds of one agent and one day (migration 0008). Order: the audit intent row is
        written first (if that fails, nothing changed and the error is raised); then ONE transaction lowers the
        expired rows to settled at 0 and moves the day and the month counter by the same sum, never below zero;
        then the outcome row (its failure is logged, never raised: the release is committed). Live (open) holds,
        settled rows and other days are not touched. Runs only under the release login: any other login gets
        InsufficientPrivilege and a `release_failed` outcome. `audit` is the chain audit of the same login."""
        check_store_id(agent_id, "agent_id")
        check_store_id(actor, "actor")
        check_spend_day(day)
        ref = f"{agent_id}:{day.isoformat()}"
        intent_id = audit.write_intent(_release_event(actor, ref, "intent"))
        try:
            with self._lock, self._db.transaction():
                row = self._exec(
                    self._money_call("hadavin_release_expired_spend", "%s, %s"), (agent_id, day)
                ).fetchone()
        except Exception as exc:
            _write_outcome(audit, _release_event(actor, ref, "release_failed", type(exc).__name__))
            raise
        done = SpendRelease(
            agent_id=agent_id,
            day=day,
            reservations=int(row["reservations"]),
            released_usd=row["released_usd"],
            day_usd=row["day_usd"],
            month_usd=row["month_usd"],
            applied_usd=row["applied_usd"] if row["applied_usd"] is not None else Decimal(0),
            intent_id=str(intent_id),
        )
        # requested = the sum of the expired holds; applied = what the day counter really fell by (a lower
        # applied than requested is drift that the counter clamp at zero would otherwise hide)
        audited = _write_outcome(
            audit,
            _release_event(
                actor,
                ref,
                f"released rows={done.reservations} requested_usd={done.released_usd} "
                f"applied_usd={done.applied_usd}",
            ),
        )
        return replace(done, outcome_audited=audited)

    def set_cap(self, agent_id: str, day_cap: Decimal, month_cap: Decimal, by: str) -> None:
        """Write the day and month cap of one agent through `hadavin_set_cap` (migration 0011). Runs only under
        the reset login: any other login gets InsufficientPrivilege. The audit lines are the CLI's (intent first,
        outcome after), not this method's. Arguments are checked before any SQL."""
        check_store_id(agent_id, "agent_id")
        check_store_id(by, "by")
        check_spend_cap(day_cap)
        check_spend_cap(month_cap)
        try:
            with self._lock, self._db.transaction():
                self._exec(
                    self._money_call(
                        "hadavin_set_cap", "%s::text, %s::numeric, %s::numeric, %s::text"
                    ),
                    (agent_id, day_cap, month_cap, by),
                )
        except psycopg.errors.DatabaseError as exc:
            raise _money_error(exc) from None

    def cap_matches(self, agent_id: str, day_cap: Decimal, month_cap: Decimal) -> str:
        """'same', 'differs' or 'missing': whether the table holds exactly this pair for the agent (read-only;
        the runtime login and the reset login may call it)."""
        check_store_id(agent_id, "agent_id")
        check_spend_cap(day_cap)
        check_spend_cap(month_cap)
        try:
            with self._lock, self._db.transaction():
                row = self._exec(
                    self._money_call("hadavin_cap_matches", "%s::text, %s::numeric, %s::numeric"),
                    (agent_id, day_cap, month_cap),
                ).fetchone()
        except psycopg.errors.DatabaseError as exc:
            raise _money_error(exc) from None
        state = row["hadavin_cap_matches"]
        if state not in ("same", "differs", "missing"):
            raise RuntimeError("the cap table answered with an unknown state")
        return state


def _release_event(actor: str, ref: str, result: str, error: str | None = None) -> AuditEvent:
    return AuditEvent(
        run_id="-",
        domain="limits",
        operation="release_expired",
        principal=actor,
        source="cli",
        object_ref=ref,
        result=result,
        error_code=error,
    )


def _write_outcome(audit: Any, event: AuditEvent) -> bool:
    """True only when the outcome row reached the chain. The audit contract is "never raises": a failed append is
    parked (outbox table, which the release login cannot write, or memory of this process) and `write_outcome`
    returns None, so a None key means the row is NOT in the chain and the process may end before it is drained.
    An exception is the same answer (the release is already committed or already failed: logged, not raised)."""
    try:
        key = audit.write_outcome(event)
    except Exception as exc:  # noqa: BLE001
        _LOG.warning("release outcome not audited error_kind=%s", type(exc).__name__)
        return False
    if key is None:
        _LOG.warning("release outcome parked, not in the chain event_id=%s", event.event_id)
        return False
    return True
