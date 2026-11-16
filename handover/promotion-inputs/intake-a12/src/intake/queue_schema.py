"""The queue database: tables and the guard triggers (spec 7, errata 32).

**Queue store: alternative and trigger.** The queue sits behind ``workqueue`` (every SQL statement lives there and in this file). SQLite is the
neutral default: one file, no server, WAL, ``BEGIN IMMEDIATE`` for writers. The alternative for a client build is PostgreSQL: the same tables, one
transaction per operation at ``SERIALIZABLE`` (or ``SELECT ... FOR UPDATE`` on the item row), the same guards written as ``BEFORE INSERT/UPDATE/DELETE``
trigger functions that ``RAISE EXCEPTION``, and the compare-and-set on ``version`` unchanged. Trigger to switch: more than one service process, a
client rule that data lives in a managed database, or write contention that the single-writer lock cannot carry.

The triggers are built from ``flags.reject_only_codes()`` and are (re)created by ``workqueue.connect``. They are a second line behind
``decisions.approve_refusal``; the exporter's own recompute (WP5: content code, ``may_approve``, validators) is the FINAL check, because a trigger only
sees stored text, not the recomputed content code. Someone who can edit the database file can drop the triggers."""

from __future__ import annotations

import re

from . import flags

STATES = ("RECEIVED", "READY", "NEEDS_PERSON", "APPROVED", "REJECTED", "EXPORTED")
_STATE_LIST = ", ".join(f"'{s}'" for s in STATES)

TABLES = (
    f"""CREATE TABLE IF NOT EXISTS items (
    uid INTEGER PRIMARY KEY AUTOINCREMENT,
    id TEXT UNIQUE NOT NULL,
    source_name TEXT NOT NULL,
    source_sha256 TEXT UNIQUE NOT NULL,
    tenant_id TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ({_STATE_LIST})),
    fields_json TEXT,
    flags_json TEXT NOT NULL DEFAULT '[]',
    failing_fields_json TEXT NOT NULL DEFAULT '[]',
    source_text TEXT NOT NULL DEFAULT '',
    text_sha256 TEXT NOT NULL DEFAULT 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    model_id TEXT,
    tier TEXT,
    prompt_sha256 TEXT,
    cost_micro INTEGER NOT NULL DEFAULT 0,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
)""",
    """CREATE TABLE IF NOT EXISTS decisions (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    item_uid INTEGER NOT NULL,
    decision TEXT NOT NULL CHECK (decision IN ('approve', 'reject')),
    approver TEXT NOT NULL,
    reason TEXT,
    content_code TEXT NOT NULL,
    at TEXT NOT NULL
)""",
    """CREATE TABLE IF NOT EXISTS exports (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    row_id TEXT UNIQUE NOT NULL,
    item_uid INTEGER UNIQUE NOT NULL,
    content_code TEXT NOT NULL,
    row_json TEXT NOT NULL,
    at TEXT NOT NULL
)""",
    """CREATE TABLE IF NOT EXISTS purges (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT NOT NULL,
    item_uid INTEGER NOT NULL,
    state TEXT NOT NULL,
    purged_by TEXT NOT NULL,
    at TEXT NOT NULL
)""",
    """CREATE TABLE IF NOT EXISTS meta (
    k TEXT PRIMARY KEY,
    v TEXT NOT NULL
)""",
    "CREATE INDEX IF NOT EXISTS decisions_item ON decisions (item_uid, seq)",
    """CREATE TABLE IF NOT EXISTS item_mask_map (
    item_uid INTEGER NOT NULL,
    placeholder TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('IBAN','BANK','ROUTING','CARD','EMAIL','PHONE','PERSON','ID','SECRET')),
    span_start INTEGER NOT NULL CHECK (span_start >= 0),
    span_end INTEGER NOT NULL CHECK (span_end > span_start),
    fingerprint TEXT NOT NULL CHECK (length(fingerprint) = 8 AND fingerprint NOT GLOB '*[^0-9a-f]*'),
    detector TEXT NOT NULL,
    PRIMARY KEY (item_uid, placeholder, span_start)
)""",
    """CREATE TABLE IF NOT EXISTS item_keys (
    item_uid INTEGER PRIMARY KEY,
    fp_key TEXT NOT NULL CHECK (length(fp_key) = 64)
)""",
    """CREATE TABLE IF NOT EXISTS item_trace (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    item_uid INTEGER NOT NULL,
    step TEXT NOT NULL,
    at TEXT NOT NULL,
    counts_json TEXT NOT NULL DEFAULT '{}',
    fingerprints_json TEXT NOT NULL DEFAULT '[]',
    result TEXT NOT NULL CHECK (result IN ('pass','fail','warn','info')),
    reason_plain TEXT NOT NULL DEFAULT ''
)""",
    "CREATE INDEX IF NOT EXISTS item_trace_item ON item_trace (item_uid, seq)",
)

ITEM_FLAGS_OF_ITEM = "(SELECT i.flags_json FROM items i WHERE i.uid = NEW.item_uid)"
SCHEMA_VERSION = "2"  # the one version there is; a file with another value is refused, there is no migration path
NULL_FIELDS_OF_ITEM = "(SELECT i.fields_json FROM items i WHERE i.uid = NEW.item_uid)"
_CODE = re.compile(r"[A-Z][A-Z0-9]{1,7}")
FROZEN_COLUMNS = (
    "uid", "id", "source_name", "source_sha256", "tenant_id", "fields_json", "flags_json", "failing_fields_json",
    "source_text", "text_sha256", "model_id", "tier", "prompt_sha256", "cost_micro", "created_at",
)  # fmt: skip


def _reject_only_expr(col: str) -> str:
    """SQL boolean over the text expression ``col``: it holds a reject-only code as an exact JSON-quoted string, or holds a backslash (a JSON escape
    could spell a code in a way the match would not see). ``instr`` is case-sensitive, unlike ``LIKE``."""
    parts = []
    for c in flags.reject_only_codes():
        if not _CODE.fullmatch(c):  # codes go into SQL text: refuse anything but a plain code
            raise ValueError("flag code is not a plain code")
        parts.append(f"instr({col}, '\"{c}\"') > 0")
    parts.append(f"instr({col}, char(92)) > 0")
    return " OR ".join(parts)


def normalise_sql(sql: str) -> str:
    """``CREATE TABLE IF NOT EXISTS`` is stored by SQLite without the clause; compare with whitespace collapsed."""
    return " ".join(sql.replace(" IF NOT EXISTS", "").split())


def schema_sql() -> dict[str, str]:
    """name -> normalised statement for every table and index (what ``sqlite_master`` must hold)."""
    out: dict[str, str] = {}
    for ddl in TABLES:
        norm = normalise_sql(ddl)
        m = re.match(r"CREATE (?:UNIQUE )?(?:TABLE|INDEX) (\w+)", norm)
        out[m.group(1)] = norm
    return out


def trigger_sql() -> dict[str, str]:
    """name -> ``CREATE TRIGGER`` statement (no trailing semicolon, so it equals what ``sqlite_master`` stores)."""
    ro_new = _reject_only_expr("NEW.flags_json")
    item_flags = "(SELECT i.flags_json FROM items i WHERE i.uid = NEW.item_uid)"
    ro_item = _reject_only_expr(item_flags)
    guarded = "NEW.state IN ('APPROVED', 'EXPORTED')"
    t: dict[str, str] = {}

    def add(name: str, when_on: str, msg: str) -> None:
        t[name] = f"CREATE TRIGGER {name} {when_on} BEGIN SELECT RAISE(ABORT, '{msg}'); END"

    # (a) a reject-only item never reaches APPROVED or EXPORTED
    add("intake_a_reject_only_insert", f"BEFORE INSERT ON items WHEN {guarded} AND ({ro_new})", "reject_only item cannot be approved")
    add("intake_a_reject_only_update", f"BEFORE UPDATE ON items WHEN {guarded} AND ({ro_new})", "reject_only item cannot be approved")
    # (b) once the result is stored only ``state`` and ``version`` may change (the decision and the export move those two)
    changed = " OR ".join(f"NEW.{c} IS NOT OLD.{c}" for c in FROZEN_COLUMNS)
    add("intake_b_immutable", f"BEFORE UPDATE ON items WHEN OLD.state <> 'RECEIVED' AND ({changed})", "item is immutable once processed")
    # (c) no fields, no READY, APPROVED or EXPORTED
    nf = "NEW.state IN ('READY', 'APPROVED', 'EXPORTED') AND NEW.fields_json IS NULL"
    add("intake_c_null_fields_insert", f"BEFORE INSERT ON items WHEN {nf}", "item without fields cannot be ready or approved")
    add("intake_c_null_fields_update", f"BEFORE UPDATE ON items WHEN {nf}", "item without fields cannot be ready or approved")
    # (d) append-only decisions, exports and purge records; approved or exported items cannot be deleted
    add("intake_d_items_delete", "BEFORE DELETE ON items WHEN OLD.state IN ('APPROVED', 'EXPORTED')", "approved item cannot be deleted")
    for tab in ("decisions", "exports", "purges", "meta"):
        add(f"intake_d_{tab}_update", f"BEFORE UPDATE ON {tab}", f"{tab} are append-only")
        add(f"intake_d_{tab}_delete", f"BEFORE DELETE ON {tab}", f"{tab} are append-only")
    # (e) an export row needs an APPROVED item whose latest decision is an approve with the same content code
    add(
        "intake_e_exports_insert",
        "BEFORE INSERT ON exports WHEN NOT EXISTS (SELECT 1 FROM items i WHERE i.uid = NEW.item_uid AND i.state = 'APPROVED' "
        "AND (SELECT d.decision || ':' || d.content_code FROM decisions d WHERE d.item_uid = i.uid ORDER BY d.seq DESC LIMIT 1) "
        "= 'approve:' || NEW.content_code)",
        "export needs the latest approve with the same content code",
    )
    # (f) states only move forward along the table of spec 7
    add(
        "intake_f_transitions",
        "BEFORE UPDATE ON items WHEN NEW.state <> OLD.state AND NOT ("
        "(OLD.state = 'RECEIVED' AND NEW.state IN ('READY', 'NEEDS_PERSON')) "
        "OR (OLD.state IN ('READY', 'NEEDS_PERSON') AND NEW.state IN ('APPROVED', 'REJECTED')) "
        "OR (OLD.state = 'APPROVED' AND NEW.state = 'EXPORTED'))",
        "state move not allowed",
    )
    # (g) APPROVED needs a latest approve decision, (h) EXPORTED needs an export row
    add(
        "intake_g_approved_needs_decision",
        "BEFORE UPDATE ON items WHEN NEW.state = 'APPROVED' AND OLD.state <> 'APPROVED' AND COALESCE((SELECT d.decision FROM decisions d "
        "WHERE d.item_uid = OLD.uid ORDER BY d.seq DESC LIMIT 1), '') <> 'approve'",
        "approved needs an approve decision",
    )
    add(
        "intake_h_exported_needs_export",
        "BEFORE UPDATE ON items WHEN NEW.state = 'EXPORTED' AND OLD.state <> 'EXPORTED' AND NOT EXISTS "
        "(SELECT 1 FROM exports e WHERE e.item_uid = OLD.uid)",
        "exported needs an export row",
    )
    # (g, h at INSERT time) a new item row is never APPROVED, REJECTED or EXPORTED (no decision or export row can exist yet), and never replaces
    # an existing row by uid, id or hash (so INSERT OR REPLACE cannot rewrite history)
    add(
        "intake_k_insert_states",
        "BEFORE INSERT ON items WHEN NEW.state IN ('APPROVED', 'REJECTED', 'EXPORTED')",
        "new item has a decided state",
    )
    add(
        "intake_k_insert_exists",
        "BEFORE INSERT ON items WHEN EXISTS (SELECT 1 FROM items x WHERE x.id = NEW.id OR x.source_sha256 = NEW.source_sha256 "
        "OR (NEW.uid IS NOT NULL AND x.uid = NEW.uid))",
        "item already exists",
    )
    # (i) a decision needs an existing undecided item and a plain content code; (j) an approve needs a record and no reject-only flag
    add(
        "intake_i_decisions_item",
        "BEFORE INSERT ON decisions WHEN NOT EXISTS (SELECT 1 FROM items i WHERE i.uid = NEW.item_uid AND i.state IN ('READY', 'NEEDS_PERSON'))",
        "decision needs an undecided item",
    )
    add(
        "intake_i_decisions_code",
        "BEFORE INSERT ON decisions WHEN length(NEW.content_code) <> 64 OR NEW.content_code GLOB '*[^0-9a-f]*'",
        "decision needs a content code",
    )
    j_when = ["BEFORE INSERT ON decisions WHEN NEW.decision = 'approve' AND (", NULL_FIELDS_OF_ITEM, " IS NULL OR (", ro_item, "))"]
    add("intake_j_approve_guard", "".join(j_when), "approve not allowed for this item")
    # (j2) an approve of an item that carries any flag needs a non-empty reason (the code rule is ``flags.approval_blocker``; this is the second line
    # for a statement that goes around the code)
    j2 = [
        "BEFORE INSERT ON decisions WHEN NEW.decision = 'approve' AND COALESCE(",
        ITEM_FLAGS_OF_ITEM,
        ", '[]') <> '[]' AND (NEW.reason IS NULL OR trim(NEW.reason) = '')",
    ]
    add("intake_j2_approve_reason", "".join(j2), "approve of a flagged item needs a reason")
    # (d) an explicit seq, row id or item uid that already exists is refused (INSERT OR REPLACE would delete the old row)
    for tab, keys in (("decisions", ("seq",)), ("exports", ("seq", "row_id", "item_uid")), ("purges", ("seq",)), ("meta", ("k",))):
        clash = " OR ".join(f"x.{k} = NEW.{k}" for k in keys)
        w = "".join(["BEFORE INSERT ON ", tab, " WHEN EXISTS (SELECT 1 FROM ", tab, " x WHERE ", clash, ")"])
        add(f"intake_d_{tab}_insert_exists", w, f"{tab} are append-only")
    # (l, m) the mask map and the per-item key: written only while the item is RECEIVED; an explicit clash on the primary key is refused (so
    # INSERT OR REPLACE cannot rewrite a span or swap the key); never updated; never deleted once the item is APPROVED or EXPORTED
    for tag, tab, clash in (
        (
            "l",
            "item_mask_map",
            "(x.item_uid = NEW.item_uid AND x.placeholder = NEW.placeholder AND x.span_start = NEW.span_start) OR x.rowid = NEW.rowid",
        ),
        ("m", "item_keys", "x.item_uid = NEW.item_uid"),
    ):
        add(
            f"intake_{tag}_{tab}_insert_state",
            "".join(
                ["BEFORE INSERT ON ", tab, " WHEN NOT EXISTS (SELECT 1 FROM items i WHERE i.uid = NEW.item_uid AND i.state = 'RECEIVED')"]
            ),
            f"{tab} are written only while the item is received",
        )
        add(
            f"intake_{tag}_{tab}_insert_exists",
            "".join(["BEFORE INSERT ON ", tab, " WHEN EXISTS (SELECT 1 FROM ", tab, " x WHERE ", clash, ")"]),
            f"{tab} rows are not replaced",
        )
        add(f"intake_{tag}_{tab}_update", f"BEFORE UPDATE ON {tab}", f"{tab} are not updated")
        add(
            f"intake_{tag}_{tab}_delete",
            "".join(
                [
                    "BEFORE DELETE ON ",
                    tab,
                    " WHEN EXISTS (SELECT 1 FROM items i WHERE i.uid = OLD.item_uid AND i.state IN ('APPROVED', 'EXPORTED'))",
                ]
            ),
            f"{tab} of a decided item are kept",
        )
    # (n) the trace is append-only (the delete trigger also stops INSERT OR REPLACE on an existing seq: ``connect`` sets recursive_triggers=ON),
    # needs an existing item, and takes no row once the item is APPROVED or EXPORTED
    add("intake_n_item_trace_update", "BEFORE UPDATE ON item_trace", "item_trace is append-only")
    add("intake_n_item_trace_delete", "BEFORE DELETE ON item_trace", "item_trace is append-only")
    add(
        "intake_n_item_trace_insert_item",
        "BEFORE INSERT ON item_trace WHEN NOT EXISTS (SELECT 1 FROM items i WHERE i.uid = NEW.item_uid) "
        "OR EXISTS (SELECT 1 FROM item_trace x WHERE x.seq = NEW.seq)",
        "item_trace needs an item and a new seq",
    )
    add(
        "intake_n_item_trace_insert_open",
        "BEFORE INSERT ON item_trace WHEN EXISTS (SELECT 1 FROM items i WHERE i.uid = NEW.item_uid AND i.state IN ('APPROVED', 'EXPORTED'))",
        "item_trace takes no row after a decision",
    )
    return t
