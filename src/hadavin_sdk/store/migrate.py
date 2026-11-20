"""Forward-only schema migrations for the Postgres store (`hadavin-sdk migrate`).

Run under a migration role, never by the runtime. Every pending `migrations/NNNN_*.sql` file is applied in one
transaction under a transaction-scoped advisory lock, so two concurrent runs apply each file once. Pattern
ported from WARDEN `audit.py:migrate` (main a1e76cbf). Rollback = restore the snapshot taken before migrating.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from psycopg import errors, sql

from hadavin_sdk import defaults
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.models import MAX_SPEND_DECIMALS, MAX_SPEND_USD
from hadavin_sdk.store.postgres import connect, names_of
from hadavin_sdk.store.protocol import MAX_EXPIRY_AGE_S, MAX_RESERVATION_ID_CHARS

_LOG = logging.getLogger("hadavin_sdk.store")

_log = logging.getLogger("hadavin_sdk.migrate")
MIGRATIONS = Path(__file__).parent / "migrations"


@dataclass(frozen=True)
class Grant:
    """What the roles get on one relation. `runtime` is the privilege list for the runtime role; `portal` says the
    read-only portal role may SELECT it. A relation not in `GRANTS` gets nothing, so `check_grants` (run by
    `migrate` and by CI) refuses a migration that creates one."""

    kind: Literal["table", "view", "sequence"]
    runtime: str
    portal: bool = False
    purge: str = (
        ""  # table-level privileges of the purge role (the evidence deleter) on this relation
    )
    # Columns the purge role may SELECT (a DELETE's WHERE needs them) and nothing else: it cannot read a stored
    # original or a tool result.
    purge_cols: tuple[str, ...] = ()
    # Table-level privileges of the reset role: the only identity that may clear a stop (`migrate --reset-role`).
    reset: str = ""
    # Table-level privileges of the release role (0008): it releases expired spend holds through ONE function and
    # appends to the audit; it holds no right on any money table.
    release: str = ""
    # Table-level privileges of the caps role (`migrate --caps-role`): the only identity that may run `hadavin_set_cap`.
    # It appends to the audit (the cap change is audited as an intent and an outcome) and holds nothing on any money table.
    caps: str = ""


@dataclass(frozen=True)
class FunctionGrant:
    """Which named roles may EXECUTE one function of ours. Everything not named here is revoked (and PUBLIC too)."""

    runtime: bool = False
    purge: bool = False
    release: bool = False
    reset: bool = False
    portal: bool = False
    caps: bool = False


_RW = "SELECT, INSERT, UPDATE"
_APPEND = "SELECT, INSERT"  # written once, never changed
# The one grant map. Audit rows and checkpoints are read and appended only (their triggers also refuse UPDATE,
# DELETE and TRUNCATE to any role); reconcile deletes an outbox row once it is in the chain. A later PR adds its
# relations here (K5-core `redaction_maps`, K6 labels and reports, ...); the portal list never holds
# `redaction_maps`, `events`, `tick_state.detail` or secrets.
GRANTS: dict[str, Grant] = {
    "runs": Grant("table", _RW, portal=True, purge_cols=("run_id", "state", "updated_at")),
    "plans": Grant("table", _RW, portal=True),
    "gate_decisions": Grant("table", _APPEND, portal=True),
    "approval_requests": Grant("table", _RW, portal=True),
    "approval_decisions": Grant("table", _APPEND, portal=True),
    "dead_letters": Grant("table", _APPEND),
    # Step 4 of F-money-definer: no table of the money family is written by the runtime login; every booking is a
    # SECURITY DEFINER function (0011). `spend` and `spend_month` stay readable (`spend_totals` reads them as the
    # runtime); `spend_reservations` is not even readable (the ids of other agents' open holds stay private). The purge
    # role holds nothing on it: it runs the purge function.
    "spend_reservations": Grant("table", ""),
    "spend": Grant("table", "SELECT"),
    "spend_month": Grant("table", "SELECT"),
    # Stop state (0006): the runtime may add a stop and read; it holds no right that turns the switch off. Only
    # the reset role clears stops (and turns the old flag off), and it writes the reset into the audit chain.
    "kill_switch": Grant("table", "SELECT", reset="SELECT, UPDATE"),
    "kill_switch_stops": Grant("table", _APPEND, reset="SELECT"),
    "kill_switch_clears": Grant("table", "SELECT", reset=_APPEND),
    # Stop state hardening (0009): the reset's own record (the runtime role holds nothing on it) and the watermark
    # of cleared stops (the runtime role reads it; only the reset role writes it).
    "kill_switch_resets": Grant("table", "", reset=_APPEND),
    "kill_switch_watermark": Grant("table", "SELECT", reset="SELECT, INSERT, UPDATE"),
    "tick_state": Grant("table", _RW),
    "audit_entries": Grant(
        "table", _APPEND, portal=True, reset=_APPEND, release=_APPEND, caps=_APPEND
    ),
    "audit_checkpoints": Grant(
        "table", _APPEND, portal=True, reset="SELECT", release="SELECT", caps="SELECT"
    ),
    "audit_outbox": Grant("table", "SELECT, INSERT, DELETE"),
    # K5-core: append and purge only (no UPDATE); `redaction_maps` is never portal-readable.
    # The runtime role appends and reads evidence; only the purge role (its own identity) deletes it.
    "tool_calls": Grant(
        "table", _APPEND, purge="DELETE", purge_cols=("call_id", "run_id", "created_at")
    ),
    "redaction_maps": Grant("table", _RW, purge="DELETE", purge_cols=("run_id", "updated_at")),
    # 0011: the limits the money functions read (written by `migrate` from the Python constants on every run). Only
    # the owner touches it: the definer functions read it as owner.
    "hadavin_limits": Grant("table", ""),
    # 0011 step 6: the caps. Owner only; `hadavin_set_cap` and `hadavin_cap_matches` touch it as owner.
    "hadavin_caps": Grant("table", ""),
    "approval_decisions_seq_seq": Grant("sequence", "USAGE"),
    "dead_letters_seq_seq": Grant("sequence", "USAGE"),
}
# The function of 0008 that lowers expired holds; only the release role may run it (EXECUTE is revoked from PUBLIC
# in the migration and from every other named role here).
RELEASE_FUNCTION = "hadavin_release_expired_spend(text, date)"
# The trigger function of 0010 (SECURITY INVOKER) on spend, spend_month and spend_reservations: it refuses an UPDATE
# that lowers a booked amount unless current_user owns the release function, which only that function's body has.
MONEY_GUARD_FUNCTION = "hadavin_money_guard()"
# 0009: the audit seq guards; 0010: the money guard. Each is re-pinned (when it exists) on every migrate run.
TRIPWIRE_FUNCTIONS = (
    "hadavin_audit_seq_guard()",
    "hadavin_audit_checkpoint_guard()",
    MONEY_GUARD_FUNCTION,
)
# 0011: the SECURITY DEFINER money functions (five bookings, set_cap, cap_matches). Each is re-pinned on every migrate run (`_pin_money_functions`).
MONEY_FUNCTIONS = (
    "hadavin_reserve_spend(text, text, date, numeric, text)",
    "hadavin_settle_spend(text, numeric, text)",
    "hadavin_expire_spend_reservations(integer)",
    "hadavin_purge_spend_reservations(timestamptz)",
    "hadavin_add_spend(text, date, numeric)",
    "hadavin_set_cap(text, numeric, numeric, text)",
    "hadavin_cap_matches(text, numeric, numeric)",
    "hadavin_expired_holds(integer)",
)
# Who may EXECUTE each callable function of ours: the runtime books, settles, expires and adds; the purge role
# purges; the release role (0008) releases; the caps role (M4, one identity per function) sets caps and compares them
# (step 6); the reset role runs none of them. The portal role runs none. Every other role, PUBLIC included, is refused.
FUNCTION_GRANTS: dict[str, FunctionGrant] = {
    MONEY_FUNCTIONS[0]: FunctionGrant(runtime=True),
    MONEY_FUNCTIONS[1]: FunctionGrant(runtime=True),
    MONEY_FUNCTIONS[2]: FunctionGrant(runtime=True),
    MONEY_FUNCTIONS[3]: FunctionGrant(purge=True),
    MONEY_FUNCTIONS[4]: FunctionGrant(runtime=True),
    # Step 6 / M4: only the caps role sets a cap; the runtime (tick check) and the caps role compare one.
    MONEY_FUNCTIONS[5]: FunctionGrant(caps=True),
    MONEY_FUNCTIONS[6]: FunctionGrant(runtime=True, caps=True),
    MONEY_FUNCTIONS[7]: FunctionGrant(
        runtime=True
    ),  # read-only: the tick alert on unreleased expired holds
    RELEASE_FUNCTION: FunctionGrant(release=True),
}
# Trigger functions need no EXECUTE grant (the trigger runs them); every other hadavin_* function must be mapped.
EXCLUDED_FUNCTIONS = (
    *TRIPWIRE_FUNCTIONS,
    "hadavin_audit_append_only()",
    "hadavin_watermark_guard()",
)
# The relations the owner check compares with the function owner: a definer function that cannot write one of
# them fails every call with insufficient_privilege.
_OWNED_RELATIONS = (
    "spend",
    "spend_month",
    "spend_reservations",
    "runs",
    "hadavin_limits",
    "hadavin_caps",
)
_LOCK = int.from_bytes(b"hadvnmig", "big") >> 1  # one fixed key for every migrate run
_ROLE = re.compile(r"[a-z_][a-z0-9_]{0,62}")
# Names PostgreSQL reads as a keyword in a GRANT (everyone, nobody, the caller), not as one role.
_FORBIDDEN_ROLES = frozenset({"public", "none", "session_user", "current_user"})
_FILE = re.compile(r"(\d{4})_[a-z0-9_]+\.sql")
_CREATE = re.compile(
    r"CREATE\s+(?:OR\s+REPLACE\s+)?(?:MATERIALIZED\s+)?(TABLE|VIEW)\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)",
    re.IGNORECASE,
)
# Possessive quantifiers (Python 3.11+) plus a leading \b: no backtracking, linear time on long identifiers.
_SERIAL = re.compile(r"\b(\w++)\s++(?:(?:BIG|SMALL)?SERIAL|SERIAL[248])\b", re.IGNORECASE)
# Statements the guard does not read. Any of these in a migration is refused ("extend the guard") rather than
# skipped, so a relation or sequence it creates cannot go ungranted.
_SAFE_CREATE = re.compile(
    r"CREATE\s+(?:UNIQUE\s+)?INDEX\b|CREATE\s+OR\s+REPLACE\s+(?:FUNCTION|TRIGGER)\b"
    r"|CREATE\s+TRIGGER\b|CREATE\s+(?:TABLE|VIEW)\s+(?:IF\s+NOT\s+EXISTS\s+)?[a-z_]\w*\s*(?:\(|AS\b)"
    r"|CREATE\s+OR\s+REPLACE\s+VIEW\s+[a-z_]\w*\s*(?:\(|AS\b)",
    re.IGNORECASE,
)
_ANY_CREATE = re.compile(r"\bCREATE\b", re.IGNORECASE)
_UNREAD = re.compile(
    r"\bALTER\s+TABLE\b[^;]*\b(?:(?:BIG|SMALL)?SERIAL|SERIAL[248])\b|\bAS\s+IDENTITY\b|\bCREATE\s+SEQUENCE\b",
    re.IGNORECASE,
)


def _migration_files(folder: Path = MIGRATIONS) -> list[Path]:
    return sorted(folder.glob("*.sql"))


def check_ledger(paths: list[Path]) -> list[str]:
    """Problems with the file names: each is `NNNN_<name>.sql` and the numbers run 1, 2, 3 ... with no repeat or gap."""
    problems = [
        f"{p.name}: not named NNNN_<name>.sql" for p in paths if not _FILE.fullmatch(p.name)
    ]
    numbers = sorted(int(p.name[:4]) for p in paths if _FILE.fullmatch(p.name))
    for n in sorted({n for n in numbers if numbers.count(n) > 1}):
        problems.append(f"two migrations are numbered {n:04d}")
    missing = sorted(set(range(1, max(numbers, default=0) + 1)) - set(numbers))
    problems += [f"migration {n:04d} is missing" for n in missing]
    return problems


def _table_body(text: str, start: int) -> str:
    """The text of the parenthesised column list that opens at or after `start` (parentheses balanced)."""
    open_at = text.find("(", start)
    if open_at == -1:
        return ""
    depth = 0
    for i in range(open_at, len(text)):
        depth += (text[i] == "(") - (text[i] == ")")
        if depth == 0:
            return text[open_at : i + 1]
    return text[open_at:]


def _scan(paths: list[Path]) -> tuple[dict[str, str], list[str]]:
    """(relation name -> kind, unread statements). Kinds: every table, view and serial-column sequence the
    migrations create. A statement that could create a relation or sequence in a way this scan does not read
    (quoted or schema-qualified name, UNLOGGED/TEMP/FOREIGN tables, CREATE SEQUENCE, IDENTITY, ADD COLUMN ...
    SERIAL) is returned as a problem, never skipped: the guard fails closed."""
    found: dict[str, str] = {}
    unread: list[str] = []
    for path in paths:
        text = _strip_sql_comments(path.read_text(encoding="utf-8"))
        for m in _ANY_CREATE.finditer(text):
            if not _SAFE_CREATE.match(text, m.start()):
                snippet = " ".join(text[m.start() : m.start() + 40].split())
                unread.append(f"{path.name}: statement the guard does not read: {snippet!r}")
        unread += [
            f"{path.name}: {u.group(0)[:40]!r} is not read by the guard"
            for u in _UNREAD.finditer(text)
        ]
        for m in _CREATE.finditer(text):
            kind, name = m.group(1).lower(), m.group(2).lower()
            found[name] = kind
            if kind == "table":
                for col in _SERIAL.findall(_table_body(text, m.end())):
                    found[f"{name}_{col.lower()}_seq"] = "sequence"
    return found, unread


_FUNCTION = re.compile(
    r'CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+(?:"?\w+"?\s*\.\s*)?"?(hadavin_\w+)"?\s*\(',
    re.IGNORECASE,
)
_TYPE_ALIASES = {
    "int": "integer",
    "int4": "integer",
    "int8": "bigint",
    "bool": "boolean",
    "timestamp with time zone": "timestamptz",
    "character varying": "varchar",
    "double precision": "float8",
}
_MULTIWORD_TYPES = ("timestamp with time zone", "character varying", "double precision")


def _strip_sql_comments(text: str) -> str:
    """The text without `/* */` and `--` comments. A `--` or `/*` inside a '...' literal or a "..." identifier is
    NOT a comment (and an apostrophe inside a comment does not open a literal). Dollar quotes are plain text here:
    the code in them is read like the rest."""
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in "'\"":
            j = i + 1
            while j < n:
                if text[j] == c:
                    if j + 1 < n and text[j + 1] == c:  # a doubled quote stays inside
                        j += 2
                        continue
                    break
                j += 1
            out.append(text[i : j + 1])
            i = j + 1
        elif text.startswith("--", i):
            j = text.find("\n", i)
            i = n if j == -1 else j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j == -1 else j + 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _split_top_level(args: str) -> list[str]:
    parts, depth, cur = [], 0, []
    for ch in args:
        if ch == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
            continue
        depth += (ch == "(") - (ch == ")")
        cur.append(ch)
    if "".join(cur).strip():
        parts.append("".join(cur))
    return parts


def _normalise_signature(name: str, types: list[str]) -> str:
    norm = []
    for t in types:
        t = " ".join(t.lower().replace('"', "").split())
        norm.append(_TYPE_ALIASES.get(t, t).replace(" ", ""))
    return f"{name.lower()}({','.join(norm)})"


def _signature_key(signature: str) -> str:
    """`hadavin_x(text, numeric)` as the maps spell it, in the form `_functions_created` returns."""
    name, _, rest = signature.partition("(")
    return _normalise_signature(name, _split_top_level(rest.rstrip(")")))


def _arg_type(part: str) -> str:
    """The type of one `name type [DEFAULT ...]` argument of a CREATE FUNCTION."""
    part = re.split(r"\bDEFAULT\b|=", part.strip(), maxsplit=1, flags=re.IGNORECASE)[0].strip()
    tokens = part.split()
    if tokens and tokens[0].upper() in ("IN", "OUT", "INOUT", "VARIADIC"):
        tokens = tokens[1:]
    rest = " ".join(tokens)
    if len(tokens) > 1 and not any(rest.lower().startswith(t) for t in _MULTIWORD_TYPES):
        rest = " ".join(tokens[1:])
    return rest


def _functions_created(paths: list[Path]) -> set[str]:
    """Full signatures (`name(type,type)`, lower case, no spaces) of the hadavin_* functions the migrations create
    (comments left out; quoted and schema-qualified names are read)."""
    found: set[str] = set()
    for path in paths:
        text = _strip_sql_comments(path.read_text(encoding="utf-8"))
        for m in _FUNCTION.finditer(text):
            depth, i = 1, m.end()
            while i < len(text) and depth:
                depth += (text[i] == "(") - (text[i] == ")")
                i += 1
            types = [_arg_type(a) for a in _split_top_level(text[m.end() : i - 1])]
            found.add(_normalise_signature(m.group(1), types))
    return found


def money_limits() -> dict[str, int]:
    """The limits the money functions read from `hadavin_limits`, from the constants the Python validators use:
    one source, so SQL and Python cannot drift. Read at call time."""
    return {
        "max_amount": MAX_SPEND_USD,
        "max_decimals": MAX_SPEND_DECIMALS,
        "max_id_chars": MAX_RESERVATION_ID_CHARS,
        "max_expiry_age": MAX_EXPIRY_AGE_S,
        "min_expiry_age": defaults.MIN_EXPIRY_AGE_S,
        "max_day_skew": defaults.MAX_RESERVE_DAY_SKEW_DAYS,
    }


def check_grants(paths: list[Path]) -> list[str]:
    """Problems between the migrations and `GRANTS`: a relation they create with no entry (it would get no grant
    and fail at runtime), an entry for a relation no migration creates, or an entry of the wrong kind."""
    created, problems = _scan(paths)
    problems += [
        f"{n} ({k}) is created by a migration but is not in GRANTS"
        for n, k in sorted(created.items())
        if n not in GRANTS
    ]
    for name, grant in sorted(GRANTS.items()):
        if name not in created:
            problems.append(f"GRANTS names {name}, which no migration creates")
        elif created[name] != grant.kind:
            problems.append(
                f"GRANTS says {name} is a {grant.kind}; the migrations create a {created[name]}"
            )
    mapped = {_signature_key(sig) for sig in (*FUNCTION_GRANTS, *EXCLUDED_FUNCTIONS)}
    functions = _functions_created(paths)
    problems += [
        f"{n} (function) is created by a migration but is in neither FUNCTION_GRANTS nor EXCLUDED_FUNCTIONS"
        for n in sorted(functions - mapped)
    ]
    problems += [
        f"FUNCTION_GRANTS names {sig}, which no migration creates"
        for sig in sorted(FUNCTION_GRANTS)
        if _signature_key(sig) not in functions
    ]
    return problems


def _apply_grants(db, role_name: str, privileges, columns=None) -> None:
    """Reset the role's rights on every relation in `GRANTS`, then give back what `privileges(grant)` names."""
    role = sql.Identifier(role_name)
    schema = db.execute("SELECT current_schema()").fetchone()[0]
    db.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(sql.Identifier(schema), role))
    for name, grant in GRANTS.items():
        what = sql.SQL(
            "SEQUENCE" if grant.kind == "sequence" else "TABLE"
        )  # a view is granted as a table
        rel = sql.Identifier(name)
        db.execute(sql.SQL("REVOKE ALL ON {} {} FROM {}").format(what, rel, role))
        if wanted := privileges(grant):
            db.execute(sql.SQL("GRANT {} ON {} {} TO {}").format(sql.SQL(wanted), what, rel, role))
        if columns is not None and (cols := columns(grant)):
            db.execute(
                sql.SQL("GRANT SELECT ({}) ON {} TO {}").format(
                    sql.SQL(", ").join(sql.Identifier(c) for c in cols), rel, role
                )
            )


_TABLE_PRIVS = ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER")


def effective_problems(db, role: str, expected_table, expected_cols=None) -> list[str]:
    """What the role can REALLY do, however it got it (a direct grant, a role it is a member of, PUBLIC, a default
    privilege, ownership), against the grant map: any relation of the schema, in GRANTS or not, on which it can do
    more than `expected_table(grant)` (and, for columns, `expected_cols(grant)`). A superuser, a role that can
    create roles or databases or bypass row security, a role that owns a relation or can CREATE in the schema is a
    problem too. The grants above are made first and this runs in the same transaction, so a problem rolls them back."""
    problems: list[str] = []
    row = db.execute(
        "SELECT rolsuper, rolcreaterole, rolcreatedb, rolbypassrls FROM pg_roles WHERE rolname = %s",
        (role,),
    ).fetchone()
    if row is None:
        return [f"{role}: the role does not exist"]
    if any(row):
        problems.append(
            f"{role}: is a superuser or can create roles or databases or bypass row security"
        )
    schema = db.execute("SELECT current_schema()").fetchone()[0]
    if db.execute("SELECT has_schema_privilege(%s, %s, 'CREATE')", (role, schema)).fetchone()[0]:
        problems.append(f"{role}: can CREATE in schema {schema}")
    rels = db.execute(
        "SELECT c.oid, c.relname, c.relkind, pg_get_userbyid(c.relowner) FROM pg_class c "
        "JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = %s AND c.relkind IN ('r','p','v','m','S')",
        (schema,),
    ).fetchall()
    for owner in sorted({o for _, _, _, o in rels if o != role}):
        # Membership, not inherited rights: a NOINHERIT member holds no rights today and can still SET ROLE to the owner.
        if db.execute("SELECT pg_has_role(%s, %s, 'MEMBER')", (role, owner)).fetchone()[0]:
            problems.append(f"{role}: is a member of {owner}, the owner of relations in {schema}")
    for oid, name, kind, owner in rels:
        if owner == role:
            problems.append(f"{role}: owns {name}")
        grant = GRANTS.get(name)
        if kind == "S":
            allowed = (
                {p.strip() for p in expected_table(grant).split(",") if p.strip()}
                if grant
                else set()
            )
            for p in ("USAGE", "SELECT", "UPDATE"):
                if (
                    p not in allowed
                    and db.execute(
                        "SELECT has_sequence_privilege(%s, %s, %s)", (role, oid, p)
                    ).fetchone()[0]
                ):
                    problems.append(f"{role}: can {p} sequence {name}")
            continue
        allowed = (
            {p.strip() for p in expected_table(grant).split(",") if p.strip()} if grant else set()
        )
        allowed_cols = set(expected_cols(grant)) if (grant and expected_cols) else set()
        for p in _TABLE_PRIVS:
            if (
                p not in allowed
                and db.execute("SELECT has_table_privilege(%s, %s, %s)", (role, oid, p)).fetchone()[
                    0
                ]
            ):
                problems.append(
                    f"{role}: can {p} {name}" + ("" if grant else " (not in the grant map)")
                )
        for (col,) in db.execute(
            "SELECT attname FROM pg_attribute WHERE attrelid = %s AND attnum > 0 AND NOT attisdropped",
            (oid,),
        ).fetchall():
            for p in ("SELECT", "INSERT", "UPDATE"):
                if p in allowed or (p == "SELECT" and col in allowed_cols):
                    continue
                if db.execute(
                    "SELECT has_column_privilege(%s, %s, %s, %s)", (role, oid, col, p)
                ).fetchone()[0]:
                    problems.append(f"{role}: can {p} {name}.{col}")
    return problems


_STOP_TABLES = ("kill_switch", "kill_switch_stops", "kill_switch_clears")

# The right that clears or defeats a stop, per relation: flip or delete the legacy flag (UPDATE, DELETE, TRUNCATE),
# append a clear (INSERT), and TRIGGER on all three (a BEFORE INSERT trigger can swallow a stop, a trigger can
# be dropped). A column grant counts for UPDATE and INSERT (the only privileges a column can hold).
_CAN_CLEAR = """
WITH RECURSIVE want(relname, priv) AS (
    VALUES ('kill_switch', 'UPDATE'), ('kill_switch', 'DELETE'), ('kill_switch', 'TRUNCATE'),
           ('kill_switch', 'TRIGGER'), ('kill_switch_stops', 'TRIGGER'), ('kill_switch_clears', 'TRIGGER'),
           ('kill_switch_clears', 'INSERT')
), rel AS (
    SELECT c.oid, c.relacl, c.relowner, w.priv
    FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
         JOIN want w ON w.relname = c.relname
    WHERE n.nspname = pg_catalog.current_schema()
), acl AS (
    SELECT a.grantee FROM rel, pg_catalog.aclexplode(rel.relacl) a WHERE a.privilege_type = rel.priv
    UNION
    SELECT a.grantee FROM rel JOIN pg_catalog.pg_attribute att ON att.attrelid = rel.oid,
           pg_catalog.aclexplode(att.attacl) a
    WHERE att.attnum > 0 AND NOT att.attisdropped AND a.privilege_type = rel.priv
), outside AS (
    SELECT relowner AS oid FROM rel UNION SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolsuper
), vouched AS (
    -- Seeds of the membership walk, never listed for being vouched. Superusers and the owner are `outside`: never
    -- seeds, and their members are not followed. A vouched role that is only a member of another VOUCHED role stays
    -- unlisted (`listed` FALSE); a member that is not vouched, or any member of a LISTED role, is listed.
    SELECT r.oid FROM pg_catalog.pg_roles r WHERE {vouched} AND r.oid NOT IN (SELECT oid FROM outside)
), can(oid, listed) AS (
    SELECT s.oid, TRUE FROM (SELECT grantee AS oid FROM acl
                       UNION SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolname = %(reset)s
                       UNION SELECT r.oid FROM pg_catalog.pg_roles r WHERE {creators}) s
    WHERE s.oid NOT IN (SELECT oid FROM outside)
    UNION
    SELECT oid, FALSE FROM vouched
    UNION
    SELECT m.member, can.listed OR m.member NOT IN (SELECT oid FROM vouched)
    FROM pg_catalog.pg_auth_members m JOIN can ON m.roleid = can.oid
    WHERE m.member NOT IN (SELECT oid FROM outside) AND {usable}
)
SELECT name FROM (
    SELECT 'PUBLIC' AS name, 0 AS pos WHERE EXISTS (SELECT 1 FROM acl WHERE grantee = 0)
    UNION ALL
    SELECT r.rolname, 1 FROM pg_catalog.pg_roles r
    WHERE r.oid IN (SELECT oid FROM can WHERE listed) AND r.rolname IS DISTINCT FROM %(reset)s
) found ORDER BY pos, name
"""


# Below PostgreSQL 16: every non-superuser CREATEROLE login of the server, except the roles the operator vouches for.
_CREATORS = "(r.rolcreaterole AND r.rolname::text <> ALL(%(accepted)s::text[]))"
# The accepted CREATEROLE roles themselves are not listed, but they SEED the membership walk: a member can SET ROLE to
# one and use its CREATEROLE, so vouching covers the role, not its members (`listed` is FALSE for the seed row).
_VOUCHED = "(r.rolcreaterole AND r.rolname::text = ANY(%(accepted)s::text[]))"
_REFUSED_CATEGORIES = frozenset(
    {"Cc", "Cf", "Zl", "Zp"}
)  # control, format (zero-width, bidi), line and paragraph separator
_WILDCARDS = frozenset({"*", "%"})


def _accepted_name_ok(name) -> bool:
    """Format of a name in `accepted_admin_roles`: managed administrator logins are often named `Admin`, `my-admin` or
    `user@server`, so any text of 1 to 63 bytes (PostgreSQL's limit) with no control, format (zero-width, bidi) or line
    separator character and no space at either end. The name is only ever bound as a query parameter and compared as
    exact text, never built into SQL."""
    if not isinstance(name, str):
        return False
    try:
        size = len(name.encode("utf-8"))
    except UnicodeEncodeError:  # a lone surrogate (from a command-line argument)
        return False
    return (
        0 < size <= 63
        and name == name.strip()
        and not any(unicodedata.category(c) in _REFUSED_CATEGORIES for c in name)
    )


def _accepted_name_forbidden(name: str) -> bool:
    return name.lower() in _FORBIDDEN_ROLES or name in _WILDCARDS


def _server_is_16_or_later(db) -> bool:
    return db.execute(
        "SELECT pg_catalog.current_setting('server_version_num')::int >= 160000"
    ).fetchone()[0]


def _check_stop_relations(db) -> None:
    """The check below reads the grants of the three stop relations in `current_schema()`. It must find all three
    there, and their bare names must resolve to them: a search_path that names no schema, a schema without the
    tables, a missing table or a temporary table of the same name would leave the check reading nothing (or the
    wrong thing) and passing."""
    schema, path = db.execute(
        "SELECT pg_catalog.current_schema(), pg_catalog.current_setting('search_path')"
    ).fetchone()
    found = {}
    if schema:
        found = dict(
            db.execute(
                "SELECT c.relname, c.oid::int8 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n "
                "ON n.oid = c.relnamespace WHERE n.nspname = %s AND c.relkind IN ('r','p') "
                "AND c.relname = ANY(%s)",
                (schema, list(_STOP_TABLES)),
            ).fetchall()
        )
    missing = [t for t in _STOP_TABLES if t not in found]
    shadowed = [
        t
        for t in found
        if db.execute("SELECT pg_catalog.to_regclass(%s)::oid::int8", (t,)).fetchone()[0]
        != found[t]
    ]
    if not schema or missing or shadowed:
        raise ConfigError(
            f"cannot check who could clear a stop: the tables {', '.join(_STOP_TABLES)} must all be in the "
            f"schema the store uses, and they are not (schema {schema!r}, search_path {path!r}, missing "
            f"{missing or 'none'}, names that resolve to another relation {shadowed or 'none'}). Run migrate "
            "with a search_path whose first existing schema holds the stop tables"
        )


def who_else_can_clear(
    db, reset_role: str | None, accepted_admin_roles: tuple[str, ...] = ()
) -> list[str]:
    """Who, besides the reset role, could clear or defeat a stop IN THIS SCHEMA, read from the grants on this
    schema's `kill_switch` (UPDATE, DELETE, TRUNCATE), `kill_switch_clears` (INSERT) and the three stop tables
    (TRIGGER) only, so roles of other schemas or applications on the same server never change the answer. It
    raises ConfigError when the three tables are not all in `current_schema()` or a bare name resolves to
    something else: nothing to read is never a pass. Listed: every role those relations grant such a right to
    (table or column grant; `PUBLIC` is listed as PUBLIC), every role that is a member, directly or through other
    roles, with or without inheritance (a NOINHERIT member can SET ROLE), of such a role or of the reset role, and
    the roles that can hand themselves the reset role: below PostgreSQL 16 every non-superuser with CREATEROLE
    (except the roles the operator vouches for in `accepted_admin_roles`: they are left out of THIS listing only,
    never from a grant on the stop tables, never from a membership, never the reset role); from 16 a membership
    counts when its SET, INHERIT or ADMIN option is true, so the holder of the ADMIN option on the reset role (the
    login that created it has it) is listed. The listing is conservative: `usable` is judged per membership, not
    along the whole path, so a role whose chain mixes INHERIT-only and SET-only links is listed although it
    cannot reach the right (a rare, harmless false refusal).

    Outside the guarantee, never listed and never followed: the reset role itself, the owner of the relations
    (it can DROP and recreate them), superusers, managed-database admin roles that are not superusers
    (rds_superuser, azure_pg_admin, cloudsqlsuperuser; below PostgreSQL 16 listed only if they hold CREATEROLE),
    SECURITY DEFINER functions of another privileged role, and a role whose only path is membership in the owner,
    in a superuser, or in a PostgreSQL predefined role that holds no grant here (`pg_write_all_data` and the like
    can write every table of the server). Whoever hands out those memberships owns that risk;
    `effective_problems` still refuses the NAMED roles for them."""
    _check_stop_relations(db)
    # pg_auth_members has the option columns from PostgreSQL 16; before that every membership can SET ROLE and a
    # CREATEROLE login can grant any role to itself.
    new = _server_is_16_or_later(db)
    usable = "(m.inherit_option OR m.set_option OR m.admin_option)" if new else "TRUE"
    creators = "FALSE" if new else _CREATORS
    vouched = "FALSE" if new else _VOUCHED
    query = _CAN_CLEAR.format(usable=usable, creators=creators, vouched=vouched)
    params = {"reset": reset_role, "accepted": list(accepted_admin_roles)}
    return [r[0] for r in db.execute(query, params).fetchall()]


def _paths(config_value: str) -> list[str]:
    return names_of(config_value)


def _path_rows(db, named: list[str]):
    """(role oid, role name, database name or None, setting) of every search_path default that reaches the named
    roles: the role-wide row, the row for this database, and the database-wide and server-wide rows."""
    return db.execute(
        "SELECT s.setrole, pg_catalog.pg_get_userbyid(s.setrole), d.datname, c "
        "FROM pg_catalog.pg_db_role_setting s CROSS JOIN LATERAL unnest(s.setconfig) c "
        "LEFT JOIN pg_catalog.pg_database d ON d.oid = s.setdatabase "
        "WHERE c LIKE 'search\\_path=%%' AND (s.setdatabase = 0 OR d.datname = current_database()) "
        "AND (s.setrole = 0 OR s.setrole IN (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = ANY(%s)))",
        (named,),
    ).fetchall()


def _effective_rows(rows, schema: str):
    """The rows that decide a named role's path in this database, and are not the schema. The row for this
    database overrides the role-wide row (PostgreSQL applies role-in-database, then role, then database, then
    server), so a role-wide row under a pinned row is shadowed and does not count."""
    pinned = {r[1] for r in rows if r[0] and r[2] and _paths(r[3].split("=", 1)[1]) == [schema]}
    return [
        r
        for r in rows
        if _paths(r[3].split("=", 1)[1]) != [schema] and not (r[0] and not r[2] and r[1] in pinned)
    ]


def check_role_settings(db, named: list[str]) -> list[str]:
    """Per-role and per-database `search_path` defaults that reach the named logins (`pg_db_role_setting`). A role
    may change its OWN default (`ALTER ROLE r SET search_path`), so a login could be sent to a decoy schema it owns
    and read a decoy stop table. A role row is a role's setting for EVERY database of the cluster, so it is never
    erased: for a role-wide row that is not the migrated schema this database gets
    `ALTER ROLE r IN DATABASE <this database> SET search_path = <schema>` (it takes precedence here, other databases
    keep their setting). A row for this database only is reset. Roles that are not named are never touched. A
    database-wide or server-wide row cannot be repaired for one role and is refused. The result is read back.
    Returns one line per change (role, database scope, old value, new value)."""
    schema, dbname_now = db.execute(
        "SELECT pg_catalog.current_schema(), pg_catalog.current_database()"
    ).fetchone()
    rows = _path_rows(db, named)
    changes = []
    wide = {r[1] for r in _effective_rows(rows, schema) if r[0] and not r[2]}
    for setrole, role, dbname, config in _effective_rows(rows, schema):
        if setrole == 0:
            raise ConfigError(
                f"a {'database-wide' if dbname else 'server-wide'} search_path default ({config}) reaches the "
                f"named roles and is not the schema {schema!r}: a login would read the stop state of another "
                "schema. Run ALTER DATABASE ... RESET search_path (or ALTER ROLE ALL ... RESET search_path) as a "
                "role that may"
            )
        old = config.split("=", 1)[1]
        if dbname:
            if role in wide:
                continue  # overwritten by the SET below
            stmt = sql.SQL("ALTER ROLE {} IN DATABASE {} RESET search_path").format(
                sql.Identifier(role), sql.Identifier(dbname)
            )
            note = f"role {role} in database {dbname}: search_path {old} reset (was the decoy of this database)"
        else:
            stmt = sql.SQL("ALTER ROLE {} IN DATABASE {} SET search_path = {}").format(
                sql.Identifier(role), sql.Identifier(dbname_now), sql.Identifier(schema)
            )
            note = (
                f"role {role} (role-wide default, kept for other databases) in database {dbname_now}: "
                f"search_path {old} -> {schema}"
            )
        try:
            db.execute(stmt)
        except errors.InsufficientPrivilege as exc:
            raise ConfigError(
                f"cannot change the search_path default of role {role} (it is {old}, not the schema {schema!r}): "
                "ALTER ROLE needs a migrate login with CREATEROLE and the ADMIN OPTION on that role "
                "(PostgreSQL 16 and later; before 16 CREATEROLE or superuser). Run migrate with such a login, or "
                f"run ALTER ROLE {role} IN DATABASE {dbname_now} SET search_path = {schema} as a role that may"
            ) from exc
        changes.append(note)
    if left := _effective_rows(_path_rows(db, named), schema):
        raise ConfigError(
            "a search_path default of a named role could not be repaired: "
            + ", ".join(f"{r[1]}: {r[3]}" for r in left)
        )
    return changes


def check_isolation_settings(db, named: list[str]) -> list[str]:
    """Role, database and server defaults of `default_transaction_isolation` that reach the named logins
    (`pg_db_role_setting`), reported when they are not `read committed`. The connection pins READ COMMITTED itself
    (`postgres.py` `_SESSION_PINS`, read back), so such a default changes nothing for the store; it is reported, not
    erased, because the audit chain and every conditional UPDATE rely on that level and a default that says otherwise
    is a sign someone tried to weaken the session. One line per row (role or `every role`, scope, value). The
    server-wide `postgresql.conf` value is not in this catalog; the pin covers it."""
    rows = db.execute(
        "SELECT pg_catalog.pg_get_userbyid(s.setrole), s.setrole, d.datname, c "
        "FROM pg_catalog.pg_db_role_setting s CROSS JOIN LATERAL unnest(s.setconfig) c "
        "LEFT JOIN pg_catalog.pg_database d ON d.oid = s.setdatabase "
        "WHERE c LIKE 'default\\_transaction\\_isolation=%%' "
        "AND (s.setdatabase = 0 OR d.datname = current_database()) "
        "AND (s.setrole = 0 OR s.setrole IN (SELECT oid FROM pg_catalog.pg_roles WHERE rolname = ANY(%s))) "
        "ORDER BY 1, 3, 4",
        (named,),
    ).fetchall()
    notes = []
    for role, setrole, dbname, config in rows:
        value = config.split("=", 1)[1].strip().strip("'\"").lower()
        if value == "read committed":
            continue
        who = f"role {role}" if setrole else "every role"
        where = f"in database {dbname}" if dbname else "in every database"
        notes.append(
            f"{who} {where}: default_transaction_isolation = {value} (not read committed). Not changed: the "
            "store's connection pins read committed itself; remove the default so nobody relies on it"
        )
    return notes


def _maintainers(db, schema: str):
    """(stop table, grantee) for every MAINTAIN grant on a stop table other than the owner's own (PUBLIC as 'PUBLIC')."""
    return db.execute(
        "SELECT c.relname, CASE WHEN a.grantee = 0 THEN 'PUBLIC' ELSE pg_catalog.pg_get_userbyid(a.grantee) END "
        "FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace, "
        "pg_catalog.aclexplode(c.relacl) a WHERE n.nspname = %s AND c.relname = ANY(%s) "
        "AND a.privilege_type = 'MAINTAIN' AND a.grantee <> c.relowner ORDER BY 1, 2",
        (schema, list(_STOP_TABLES)),
    ).fetchall()


def _holds(db, role: str, schema: str, table: str, privilege: str) -> bool:
    """Whether the role holds the privilege on schema.table; the relation name is built with quote_ident, so a
    schema with capitals or special characters resolves to itself."""
    return db.execute(
        "SELECT pg_catalog.has_table_privilege(%s, "
        "(pg_catalog.quote_ident(%s) || '.' || pg_catalog.quote_ident(%s))::regclass, %s)",
        (role, schema, table, privilege),
    ).fetchone()[0]


def check_maintain(db, named: list[str]) -> None:
    """PostgreSQL 17 added MAINTAIN, which also lets its holder LOCK a table in any mode: a runtime role that held it
    (a grant, PUBLIC, or membership in pg_maintain) could take ACCESS EXCLUSIVE on a stop table and block every read
    of the stop. Every MAINTAIN grant on the three stop tables other than the owner's is revoked, and a named role
    that can still maintain them (PUBLIC cannot be revoked per role; pg_maintain is a membership) is refused. Before
    17 the privilege does not exist and is not named."""
    if (
        db.execute("SELECT pg_catalog.current_setting('server_version_num')::int").fetchone()[0]
        < 170000
    ):
        return
    schema = db.execute("SELECT pg_catalog.current_schema()").fetchone()[0]
    for table, grantee in _maintainers(db, schema):
        who = sql.SQL("PUBLIC") if grantee == "PUBLIC" else sql.Identifier(grantee)
        db.execute(
            sql.SQL("REVOKE MAINTAIN ON TABLE {}.{} FROM {}").format(
                sql.Identifier(schema), sql.Identifier(table), who
            )
        )
    if left := _maintainers(db, schema):
        raise ConfigError(
            "MAINTAIN (which can LOCK a table) is still held on the stop tables by "
            + ", ".join(f"{g} on {t}" for t, g in left)
            + ": REVOKE it as the owner of the tables"
        )
    for role in named:
        for table in _STOP_TABLES:
            if _holds(db, role, schema, table, "MAINTAIN"):
                raise ConfigError(
                    f"{role} holds MAINTAIN on {table} (through pg_maintain or a role it is a member of), so it "
                    "could LOCK the stop tables and block every read of the stop: remove that membership"
                )


def _excess_privileges(db, role: str) -> list[str]:
    """Effective privileges (inherited ones too) the role holds beyond SELECT on the `portal` relations."""
    extra = []
    for name, grant in GRANTS.items():
        if grant.kind == "sequence":
            privs, q = ("USAGE", "SELECT", "UPDATE"), "SELECT has_sequence_privilege(%s, %s, %s)"
        else:
            privs = ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE")
            q = "SELECT has_table_privilege(%s, %s, %s)"
        allowed = {"SELECT"} if grant.portal else set()
        extra += [
            f"{name}:{p}"
            for p in privs
            if p not in allowed and db.execute(q, (role, name, p)).fetchone()[0]
        ]
    return extra


def _pin_search_path(db, signature: str) -> None:
    """Pin the search path of one function of ours to pg_catalog, this schema, pg_temp (temp schema LAST): the file
    cannot know the schema, so every migrate run does it again (a hand-run CREATE OR REPLACE resets it)."""
    fn = sql.SQL(signature)
    schema = db.execute("SELECT current_schema()").fetchone()[0]
    try:
        db.execute(
            sql.SQL("ALTER FUNCTION {} SET search_path = pg_catalog, {}, pg_temp").format(
                fn, sql.Identifier(schema)
            )
        )
    except errors.InsufficientPrivilege as exc:
        owner = db.execute(
            "SELECT pg_get_userbyid(proowner) FROM pg_proc WHERE oid = to_regprocedure(%s)",
            (signature,),
        ).fetchone()[0]
        raise ConfigError(
            f"cannot pin the search path of {signature}: it is owned by {owner}, and only its owner (or a "
            f"member of that role) may alter it. Run migrate as {owner}."
        ) from exc


def _pin_money_guard(db) -> None:
    """The trigger functions of 0009 (audit seq, checkpoint) and 0010 (money guard): each is pinned like the release
    function's. A database from before the migration that creates one has none, and nothing is done for it."""
    for signature in TRIPWIRE_FUNCTIONS:
        if db.execute("SELECT to_regprocedure(%s)", (signature,)).fetchone()[0] is not None:
            _pin_search_path(db, signature)


def _pin_money_functions(db) -> None:
    """The five money functions of 0011, pinned like the tripwire functions on EVERY run (also when 0011 is already
    applied). A database from before 0011 has none, and nothing is done for it."""
    for signature in MONEY_FUNCTIONS:
        if db.execute("SELECT to_regprocedure(%s)", (signature,)).fetchone()[0] is not None:
            _pin_search_path(db, signature)


def _owner_problems(db, named: list[str]) -> list[str]:
    """One owner for every hadavin_* function and for the money relations. Names only, never a value."""
    schema = db.execute("SELECT current_schema()").fetchone()[0]
    funcs = db.execute(
        "SELECT p.oid::regprocedure::text, pg_get_userbyid(p.proowner) FROM pg_proc p "
        "JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname = %s AND p.proname LIKE 'hadavin\\_%%' "
        "ORDER BY 1",
        (schema,),
    ).fetchall()
    if not funcs:
        return []
    fix = (
        "run ALTER FUNCTION ... OWNER TO <the one owner> (ALTER TABLE ... OWNER TO for a table) as that owner or a "
        "superuser, then run migrate again"
    )
    owners = sorted({o for _, o in funcs})
    if len(owners) > 1:
        listing = ", ".join(f"{f} owned by {o}" for f, o in funcs[:20])
        text = (
            f"the hadavin_* functions have more than one owner ({', '.join(owners)}): {listing}. The money guard "
            "lets through only the owner of the release function, so a mixed-owner database would refuse every "
            f"settle. {fix}"
        )
        return [text]
    owner = owners[0]
    problems = []
    for role in named:
        if role == owner:
            problems.append(
                f"{role} is the owner of the hadavin_* functions: a named role must not be"
            )
        elif db.execute("SELECT pg_has_role(%s, %s, 'MEMBER')", (role, owner)).fetchone()[0]:
            problems.append(
                f"{role} is a member of {owner}, the owner of the hadavin_* functions: remove the membership"
            )
    if db.execute("SELECT rolsuper FROM pg_roles WHERE rolname = %s", (owner,)).fetchone()[0]:
        return problems  # a superuser function owner can write every table
    for rel, rel_owner in db.execute(
        "SELECT c.relname, pg_get_userbyid(c.relowner) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname = %s AND c.relname = ANY(%s) AND c.relkind IN ('r','p') ORDER BY 1",
        (schema, list(_OWNED_RELATIONS)),
    ).fetchall():
        if rel_owner != owner:
            problems.append(
                f"the table {rel} is owned by {rel_owner}, the hadavin_* functions by {owner}: the functions "
                f"could not write it. {fix}"
            )
    return problems


def _unmapped_functions(db) -> list[str]:
    """hadavin_* functions of the schema in neither map, by FULL signature (an overload of a mapped name is
    unmapped: it would be unpinned and open to PUBLIC)."""
    schema = db.execute("SELECT current_schema()").fetchone()[0]
    known = set()
    for sig in (*FUNCTION_GRANTS, *EXCLUDED_FUNCTIONS):
        row = db.execute("SELECT to_regprocedure(%s)::oid", (sig,)).fetchone()[0]
        if row is not None:
            known.add(row)
    return [
        sig
        for (oid, sig) in db.execute(
            "SELECT p.oid, p.oid::regprocedure::text FROM pg_proc p JOIN pg_namespace n "
            "ON n.oid = p.pronamespace WHERE n.nspname = %s AND p.proname LIKE 'hadavin\\_%%' ORDER BY 2",
            (schema,),
        ).fetchall()
        if oid not in known
    ]


def _unnamed_money_executors(db, named: list[str]) -> list[str]:
    """Roles NOT named in this run (the owner, superusers and members of the owner are the documented exception) that
    can EXECUTE a function of `FUNCTION_GRANTS` however they got it (a direct grant, PUBLIC, a membership), and the
    default privileges that would hand EXECUTE to someone on every FUTURE function of the schema. Names only."""
    problems: list[str] = []
    sigs = list(FUNCTION_GRANTS)
    for sig in sigs:
        oid = db.execute("SELECT to_regprocedure(%s)::oid", (sig,)).fetchone()[0]
        if oid is None:
            continue
        if db.execute(
            "SELECT EXISTS (SELECT 1 FROM pg_proc p, pg_catalog.aclexplode(p.proacl) a "
            "WHERE p.oid = %s AND a.grantee = 0 AND a.privilege_type = 'EXECUTE')",
            (oid,),
        ).fetchone()[0]:
            problems.append(f"PUBLIC can run {sig}")
        for (role,) in db.execute(
            "SELECT r.rolname FROM pg_roles r, pg_proc p WHERE p.oid = %s AND NOT r.rolsuper "
            "AND r.oid <> p.proowner AND NOT pg_has_role(r.oid, p.proowner, 'MEMBER') "
            "AND r.rolname <> ALL(%s::text[]) AND r.rolname !~ '^pg_' "
            "AND has_function_privilege(r.oid, p.oid, 'EXECUTE') ORDER BY 1",
            (oid, [n for n in named if n]),
        ).fetchall():
            problems.append(f"role {role} (not named in this command) can run {sig}")
    schema = db.execute("SELECT current_schema()").fetchone()[0]
    for role, grantee in db.execute(
        "SELECT pg_get_userbyid(d.defaclrole), COALESCE(NULLIF(a.grantee, 0)::regrole::text, 'PUBLIC') "
        "FROM pg_default_acl d JOIN pg_namespace n ON n.oid = d.defaclnamespace, "
        "pg_catalog.aclexplode(d.defaclacl) a WHERE n.nspname = %s AND d.defaclobjtype = 'f' "
        "AND a.privilege_type = 'EXECUTE' AND a.grantee <> d.defaclrole",
        (schema,),
    ).fetchall():
        problems.append(
            f"default privileges of {role} in schema {schema} give EXECUTE on future functions to {grantee}"
        )
    return problems


def _money_table_writers(db) -> list[str]:
    """Every role other than the table owner and superusers that holds INSERT, UPDATE, DELETE or TRUNCATE on one of
    the three money tables (PUBLIC included), named in this command or not, by a direct grant or a membership. Only
    the definer functions (run as the owner) may write them. Names only."""
    problems: list[str] = []
    for table in ("spend", "spend_month", "spend_reservations"):
        oid = db.execute("SELECT to_regclass(%s)::oid", (table,)).fetchone()[0]
        if oid is None:
            continue
        if db.execute(
            "SELECT EXISTS (SELECT 1 FROM pg_class c, pg_catalog.aclexplode(c.relacl) a WHERE c.oid = %s "
            "AND a.grantee = 0 AND a.privilege_type IN ('INSERT', 'UPDATE', 'DELETE', 'TRUNCATE'))",
            (oid,),
        ).fetchone()[0]:
            problems.append(f"PUBLIC can write {table}")
        for role, priv in db.execute(
            "SELECT r.rolname, p.priv FROM pg_roles r, pg_class c, "
            "(VALUES ('INSERT'), ('UPDATE'), ('DELETE'), ('TRUNCATE')) AS p(priv) "
            "WHERE c.oid = %s AND NOT r.rolsuper AND r.oid <> c.relowner AND r.rolname !~ '^pg_' "
            "AND has_table_privilege(r.oid, c.oid, p.priv) ORDER BY 1, 2",
            (oid,),
        ).fetchall():
            problems.append(f"role {role} can {priv} {table}")
    return problems


def _seed_limits(db) -> None:
    """The rows the money functions read, from the Python constants, on every run (a changed default reaches the
    functions at the next migrate). A database without 0011 has no table, and nothing is done."""
    if db.execute("SELECT to_regclass('hadavin_limits')").fetchone()[0] is None:
        return
    limits = money_limits()
    for name, value in limits.items():
        db.execute(
            "INSERT INTO hadavin_limits (name, value) VALUES (%s, %s) "
            "ON CONFLICT (name) DO UPDATE SET value = EXCLUDED.value",
            (name, value),
        )
    # a row nobody reads (a planted one, or a limit an older package seeded) is removed, never left to look meaningful
    db.execute("DELETE FROM hadavin_limits WHERE name <> ALL(%s::text[])", (list(limits),))


def _apply_money_functions(db, roles: dict[str, str | None]) -> None:
    """EXECUTE on the money functions: pin first, then each named role gets what `FUNCTION_GRANTS` says and loses
    the rest; a named role that can still run one (PUBLIC, a membership) is refused. `roles` maps the Grant field
    name (runtime, purge, release, reset, portal) to the named role or None. The release function has its own
    apply (`_apply_release_function`); it is checked here too."""
    _pin_money_functions(db)
    for signature, grant in FUNCTION_GRANTS.items():
        if db.execute("SELECT to_regprocedure(%s)", (signature,)).fetchone()[0] is None:
            continue
        fn = sql.SQL(signature)
        for kind, role in roles.items():
            if not role:
                continue
            db.execute(
                sql.SQL("REVOKE ALL ON FUNCTION {} FROM {}").format(fn, sql.Identifier(role))
            )
            if getattr(grant, kind):
                db.execute(
                    sql.SQL("GRANT EXECUTE ON FUNCTION {} TO {}").format(fn, sql.Identifier(role))
                )
        for kind, role in roles.items():
            can = (
                db.execute(
                    "SELECT has_function_privilege(%s, to_regprocedure(%s), 'EXECUTE')",
                    (role, signature),
                ).fetchone()[0]
                if role
                else False
            )
            if role and can != getattr(grant, kind):
                raise ConfigError(
                    f"{role} {'cannot run' if getattr(grant, kind) else 'can run'} {signature}: only "
                    f"{', '.join(k for k in roles if getattr(grant, k)) or 'the owner'} may "
                    "(a grant through PUBLIC or a role it is a member of cannot be revoked here)"
                )


def _apply_release_function(db, release_role: str | None, others: list[str]) -> None:
    """EXECUTE on the release function: the release role gets it, every other named role loses it, and a named
    role that can still run it (through PUBLIC or a role it is a member of) is refused."""
    if db.execute("SELECT to_regprocedure(%s)", (RELEASE_FUNCTION,)).fetchone()[0] is None:
        return
    fn = sql.SQL(RELEASE_FUNCTION)
    # SECURITY DEFINER: the search path is pinned with the catalog first and the temp schema last, so neither a
    # temp table of the caller nor a writable schema can stand in for a money table or a catalog function.
    _pin_search_path(db, RELEASE_FUNCTION)
    for role in others:
        db.execute(sql.SQL("REVOKE ALL ON FUNCTION {} FROM {}").format(fn, sql.Identifier(role)))
    if release_role:
        db.execute(
            sql.SQL("GRANT EXECUTE ON FUNCTION {} TO {}").format(fn, sql.Identifier(release_role))
        )
    for role in others:
        if db.execute(
            "SELECT has_function_privilege(%s, to_regprocedure(%s), 'EXECUTE')",
            (role, RELEASE_FUNCTION),
        ).fetchone()[0]:
            raise ConfigError(f"{role} can run {RELEASE_FUNCTION}: only the release role may")


# Unreleased migrations: a file here may still change before its release. A changed unreleased file is NOT re-run
# and nothing of it reaches a database that already applied it; migrate warns on EVERY run while the file and the
# ledger disagree (the ledger keeps the checksum of what was applied). The operator ends the warning with
# `reset_draft` (after dropping what the draft made) or `accept_changed_draft` (the database is known to match).
# A file NOT here must match store/migrations_released.json (shipped; tests/fixtures/migrations_released.json is
# a copy kept equal by a test). At merge of the release that ships them, the lead adds their hashes to both copies
# and empties this set (see docs/migration-checksums.md).
UNRELEASED_MIGRATIONS = frozenset(
    {
        "0008_release_expired_spend",
        "0009_stop_state_hardening",
        "0010_money_guard",
        "0011_money_definer",
    }
)
RELEASED_MANIFEST = Path(__file__).parent / "migrations_released.json"


def _released_hashes() -> dict[str, str]:
    return json.loads(RELEASED_MANIFEST.read_text(encoding="utf-8"))


def _draft_versions() -> frozenset[str]:
    """Versions an operator may reset or accept: unreleased AND not in the shipped manifest (if the lead forgets to
    empty UNRELEASED_MIGRATIONS at a release, the manifest still wins)."""
    return UNRELEASED_MIGRATIONS - _released_hashes().keys()


def _read_migration(path: Path) -> tuple[str, str]:
    """(text to execute, checksum), from ONE read of the file. The checksum is SHA-256 of the bytes with Windows line
    endings read as Unix ones (the released manifest's rule); the text is decoded the way `read_text` does it."""
    data = path.read_bytes()
    text = data.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return text, hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def _ensure_ledger(db) -> None:
    """The ledger table and its checksum column. The column is added here, not by a numbered migration, and only when
    it is missing (ALTER TABLE needs ownership and a heavy lock even when the column exists)."""
    db.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations "
        "(version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
    )
    has = db.execute(
        "SELECT 1 FROM information_schema.columns WHERE table_schema = current_schema() "
        "AND table_name = 'schema_migrations' AND column_name = 'checksum'"
    ).fetchone()
    if has:
        return
    try:
        db.execute("ALTER TABLE schema_migrations ADD COLUMN IF NOT EXISTS checksum TEXT")
    except errors.InsufficientPrivilege as exc:
        raise ConfigError(
            "the schema_migrations ledger has no checksum column and this login may not add it: run migrate once "
            "as the owner of schema_migrations"
        ) from exc


def _check_released(files: dict[Path, str]) -> None:
    """Every file of the shipped manifest must still hash to it, fresh install or not."""
    manifest = _released_hashes()
    for path, digest in files.items():
        want = manifest.get(path.stem)
        if want is not None and digest != want:
            raise ConfigError(
                f"migration {path.name} was changed after its release (hash {digest[:12]}, released {want[:12]}). "
                "A released migration never changes: restore the file, and put the change in a new numbered migration"
            )


def _reset_draft(db, version: str, files: list[Path]) -> None:
    """Delete the ledger rows of an UNRELEASED version and every later one, so the next step applies them again.
    It does not drop anything the draft made: do that first (the files would fail on what already exists)."""
    stems = [p.stem for p in files]
    if version not in _draft_versions() or version not in stems:
        raise ConfigError(
            f"reset_draft {version!r}: only an unreleased migration can be reset "
            f"({', '.join(sorted(_draft_versions())) or 'none now'})"
        )
    later = [v for v in stems if v >= version]
    db.execute("DELETE FROM schema_migrations WHERE version = ANY(%s)", (later,))
    _log.warning(
        "migrate: ledger rows deleted for %s; they are applied again now", ", ".join(later)
    )


def _verify_applied(db, files: dict[Path, str], accept: tuple[str, ...]) -> None:
    """Compare every applied file with the checksum recorded when it was applied (`files` maps path to its current
    checksum). A released file must also match the shipped manifest (a NULL checksum, from before checksums existed,
    is filled only from a file that does). A changed file that is not in UNRELEASED_MIGRATIONS is refused. For an
    unreleased file the ledger KEEPS the checksum of what was applied and migrate warns on every run while the file
    differs; nothing of the changed file reaches the database. A NULL checksum on an unreleased file is trusted on
    first use (logged). `accept` names unreleased versions whose recorded checksum is set to the file's now."""
    rows = dict(db.execute("SELECT version, checksum FROM schema_migrations").fetchall())
    for bad in sorted(set(accept) - _draft_versions()):
        raise ConfigError(
            f"accept_changed_draft {bad!r}: only an unreleased migration can be accepted"
        )
    for path, new in files.items():
        old = rows.get(path.stem, False)
        if old is False:
            continue
        if path.stem in accept:
            db.execute(
                "UPDATE schema_migrations SET checksum = %s WHERE version = %s", (new, path.stem)
            )
            continue
        if old == new:
            continue
        if old is None:
            if path.stem in UNRELEASED_MIGRATIONS:
                _log.warning(
                    "migrate: %s was applied before checksums were recorded; trusting the current file",
                    path.name,
                )
            db.execute(
                "UPDATE schema_migrations SET checksum = %s WHERE version = %s", (new, path.stem)
            )
        elif path.stem in UNRELEASED_MIGRATIONS:
            _log.warning(
                "migrate: UNRELEASED migration %s differs from what this database applied (applied %s, file now "
                "%s). NOTHING of the changed file reaches this database: the file is not run again, and its tables, "
                "functions and constraints stay as the old draft made them. To bring the database up to date: drop "
                "what %s and every later migration made, then run migrate with --reset-draft %s; if the database "
                "already matches the file, run migrate with --accept-changed-draft %s. This warning repeats on "
                "every run until then",
                path.name,
                old[:12],
                new[:12],
                path.stem,
                path.stem,
                path.stem,
            )
        else:
            raise ConfigError(
                f"applied migration {path.name} was changed after it was applied (recorded checksum {old[:12]}, "
                f"file now {new[:12]}). A released migration never changes: restore the file, and put the change in "
                "a new numbered migration"
            )


def migrate(
    dsn: str,
    *,
    runtime_role: str | None = None,
    portal_role: str | None = None,
    purge_role: str | None = None,
    reset_role: str | None = None,
    release_role: str | None = None,
    caps_role: str | None = None,
    no_roles: bool = False,
    iam_auth: bool = False,
    region: str | None = None,
    sslmode: str | None = None,
    sslrootcert: str | None = None,
    accepted_admin_roles: tuple[str, ...] = (),
    on_role_change: Callable[[str], None] | None = None,
    notes: list[str] | None = None,
    accept_changed_draft: tuple[str, ...] = (),
    reset_draft: str | None = None,
) -> list[str]:
    """Apply pending migrations; return the versions applied by this call. With `runtime_role`, give it the
    privileges `GRANTS` lists (never TRUNCATE; DELETE only on the outbox and the purged evidence tables). With `portal_role`, SELECT on the
    relations marked `portal` and nothing else. With `release_role`, EXECUTE on the release function of 0008 and the audit append (nothing on the money tables). With `reset_role`, what `Grant.reset` lists: clear stops, turn the
    old flag off, append the reset to the audit chain, and nothing else. The ledger and the grant map are checked first: a bad file name,
    a gap, or a relation with no `GRANTS` entry stops the run before it touches the database. A run that names no
    role is refused unless `no_roles=True` (CLI `--no-roles`): it would apply the schema and never look at who can
    clear a stop, and exit 0. Every search_path default of a named role that migrate changed is passed to
    `on_role_change` (role, database scope, old and new value) and logged (`hadavin_sdk.migrate`, warning).
    `accepted_admin_roles`: role names (1 to 63 bytes, no control, format, line-separator or paragraph-separator
    character, no space at either end, compared as exact text)
    the operator vouches for (cannot grant the reset role to itself; for
    example a managed service's administrator). Below PostgreSQL 16 they are left out of the CREATEROLE listing and
    nowhere else; each one is logged at warning level (logger `hadavin_sdk.store`) and the command line prints
    them (`notes`, when given, receives that line). Their members are still listed. It needs named roles, and a
    name that is also a named role is refused.
    `reset_draft`: an unreleased version whose ledger row and every later one are deleted before applying (the
    operator drops what they made first). `accept_changed_draft`: unreleased versions whose recorded checksum is set
    to the file's (the database is known to match). Both refuse a released version."""
    roles = (runtime_role, portal_role, purge_role, reset_role, release_role, caps_role)
    for role in roles:
        if role is not None and (not _ROLE.fullmatch(role) or role in _FORBIDDEN_ROLES):
            raise ConfigError(f"not a plain database role name: {role!r}")
    named = [r for r in roles if r is not None]
    if len(set(named)) != len(named):
        raise ConfigError(
            "the runtime, portal, purge, reset, release and caps roles must be different roles"
        )
    if no_roles and named:
        raise ConfigError("no_roles (--no-roles) says no role is named, and a role is named")
    bad_accepted = (
        "accepted_admin_roles must be database role names (1 to 63 bytes, no control, format or line separator "
        "character, no space at either end; not PUBLIC, none, session_user, current_user, * or %): "
        f"{accepted_admin_roles!r}"
    )
    if isinstance(accepted_admin_roles, str):
        raise ConfigError(bad_accepted)
    accepted = tuple(accepted_admin_roles)
    if not all(_accepted_name_ok(a) for a in accepted):
        raise ConfigError(bad_accepted)
    if any(_accepted_name_forbidden(a) for a in accepted):
        raise ConfigError(bad_accepted)
    if accepted and not named:
        raise ConfigError(
            "accepted_admin_roles is only read when roles are named: it changes the who-else check"
        )
    if overlap := sorted(set(accepted) & set(named)):
        raise ConfigError(
            f"accepted_admin_roles must not name a role this command grants: {', '.join(overlap)}"
        )
    files = _migration_files()
    if problems := check_ledger(files) + check_grants(files):
        raise ConfigError("migrations are inconsistent: " + "; ".join(problems))
    if not named and not no_roles:
        raise ConfigError(
            "no role is named, so the stop-state check (who could clear a stop) would be skipped. Name the "
            "runtime, portal, purge and reset roles in ONE migrate command, or pass --no-roles to apply the "
            "schema without checking any role (the first install, before the roles exist)"
        )
    applied = []
    with (
        connect(
            dsn, iam_auth=iam_auth, region=region, sslmode=sslmode, sslrootcert=sslrootcert
        ) as db,
        db.transaction(),
    ):
        db.execute("SELECT pg_advisory_xact_lock(%s)", (_LOCK,))
        _ensure_ledger(db)
        done = {r[0] for r in db.execute("SELECT version FROM schema_migrations").fetchall()}
        if gone := sorted(done - {p.stem for p in files}):
            raise ConfigError(
                f"applied migrations have no file in this release: {', '.join(gone)}. If a migration file was renamed "
                "and its tables already exist, rename the ledger row by hand (change the version of that row in the "
                "schema_migrations table to the new file name); if its content changed too, drop what it made and "
                "run migrate again"
            )
        texts = {
            p: _read_migration(p) for p in files
        }  # each file read ONCE: what is hashed is what runs
        _check_released({p: t[1] for p, t in texts.items()})
        if reset_draft is not None:
            _reset_draft(db, reset_draft, files)
            done = {r[0] for r in db.execute("SELECT version FROM schema_migrations").fetchall()}
        _verify_applied(db, {p: t[1] for p, t in texts.items()}, tuple(accept_changed_draft))
        for path in files:
            if path.stem in done:
                continue
            text, digest = texts[path]
            db.execute(text)  # a file shipped in this package
            db.execute(
                "INSERT INTO schema_migrations (version, checksum) VALUES (%s, %s)",
                (path.stem, digest),
            )
            applied.append(path.stem)
        q = "SELECT pg_has_role(%s, %s, 'MEMBER')"  # a member keeps the other's rights, whatever we REVOKE
        for a in named:
            for b in named:
                if a != b and db.execute(q, (a, b)).fetchone()[0]:
                    raise ConfigError(
                        "the runtime, portal, purge, reset, release and caps roles must not be members of each other"
                    )
        if unmapped := _unmapped_functions(db):
            raise ConfigError(
                "the schema has hadavin_* functions that are in neither FUNCTION_GRANTS nor EXCLUDED_FUNCTIONS: "
                + ", ".join(unmapped[:20])
            )
        if problems := _owner_problems(db, named):
            raise ConfigError("; ".join(problems))
        if (
            named
            and db.execute(
                "SELECT bool_or(r.rolsuper) FROM pg_proc p JOIN pg_roles r ON r.oid = p.proowner "
                "WHERE p.pronamespace = to_regnamespace(current_schema()) AND p.proname = %s",
                (RELEASE_FUNCTION.split("(")[0],),
            ).fetchone()[0]
        ):
            owner_note = (
                "the hadavin_* functions are owned by a superuser: allowed (test servers and some managed "
                "services), but a superuser owner is a wider key than a plain owner role"
            )
            _LOG.warning("migrate: %s", owner_note)
            if notes is not None:
                notes.append(owner_note)
        _seed_limits(db)
        if runtime_role:
            _apply_grants(db, runtime_role, lambda g: g.runtime)
            if bad := effective_problems(db, runtime_role, lambda g: g.runtime if g else ""):
                raise ConfigError(
                    "the runtime role holds more than the grant map: " + "; ".join(bad[:20])
                )
        if purge_role:
            _apply_grants(db, purge_role, lambda g: g.purge, lambda g: g.purge_cols)
            if bad := effective_problems(
                db, purge_role, lambda g: g.purge if g else "", lambda g: g.purge_cols if g else ()
            ):
                raise ConfigError(
                    "the purge role holds more than the grant map: " + "; ".join(bad[:20])
                )
        if reset_role:
            _apply_grants(db, reset_role, lambda g: g.reset)
            if bad := effective_problems(db, reset_role, lambda g: g.reset if g else ""):
                raise ConfigError(
                    "the reset role holds more than the grant map: " + "; ".join(bad[:20])
                )
        if release_role:
            _apply_grants(db, release_role, lambda g: g.release)
            if bad := effective_problems(db, release_role, lambda g: g.release if g else ""):
                raise ConfigError(
                    "the release role holds more than the grant map: " + "; ".join(bad[:20])
                )
        if caps_role:
            _apply_grants(db, caps_role, lambda g: g.caps)
            if bad := effective_problems(db, caps_role, lambda g: g.caps if g else ""):
                raise ConfigError(
                    "the caps role holds more than the grant map: " + "; ".join(bad[:20])
                )
        _pin_money_guard(db)
        _apply_release_function(db, release_role, [r for r in named if r != release_role])
        _apply_money_functions(
            db,
            {
                "runtime": runtime_role,
                "purge": purge_role,
                "release": release_role,
                "reset": reset_role,
                "portal": portal_role,
                "caps": caps_role,
            },
        )
        if any(roles) and (extra_exec := _unnamed_money_executors(db, [r for r in roles if r])):
            raise ConfigError(
                "roles not named in this command can run the money functions, or will for future functions: "
                + "; ".join(extra_exec[:20])
            )
        if portal_role:
            _apply_grants(db, portal_role, lambda g: "SELECT" if g.portal else "")
            if extra := _excess_privileges(db, portal_role):
                raise ConfigError(  # e.g. inherited from another role: REVOKE cannot take those away
                    f"the portal role holds privileges outside the portal grant map: {', '.join(extra)}"
                )
        if any(roles) and (writers := _money_table_writers(db)):
            raise ConfigError(
                "a role other than the owner can write a money table (only the definer functions may): "
                + "; ".join(writers[:20])
            )
        note = ""
        if named:
            for note in check_role_settings(db, named):
                _log.warning("migrate changed a role setting: %s", note)
                if on_role_change:
                    on_role_change(note)
            for note in check_isolation_settings(db, named):
                _log.warning("migrate: %s", note)
                if notes is not None:
                    notes.append(note)
            check_maintain(db, named)
        if accepted:
            names = ", ".join(accepted)
            if _server_is_16_or_later(db):
                note = f"accepted_admin_roles has no effect from PostgreSQL 16 on (named, not used: {names})"
            else:
                note = (
                    "accepted administrator roles (you vouch for them; not checked as able to clear a stop, but "
                    f"their members and any grant on the stop tables still are): {names}"
                )
            _LOG.warning("migrate: %s", note)
            if notes is not None:
                notes.append(note)
        if named and (others := who_else_can_clear(db, reset_role, accepted)):
            raise ConfigError(
                "roles other than the reset role could clear a stop (a right on kill_switch or "
                "kill_switch_clears, or membership in a role that holds one): "
                + ", ".join(others[:20])
                + ". Name the runtime, portal, purge and reset roles in ONE migrate command, and revoke the "
                "right or the membership of any other role. Below PostgreSQL 16 a role listed only because it holds "
                "CREATEROLE can be named with accepted_admin_roles (command line: --accept-admin-role) when you "
                "vouch that it cannot grant the reset role to itself (see docs/stop-state-runbook.md)"
                + (f". {note}" if note.startswith("accepted administrator") else "")
            )
    return applied
