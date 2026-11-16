"""Builds secdef_audit_v22.py from secdef_audit_v21.py (round 9, security MJ3, MJ4, readiness M1, M2, M4). Every replacement is asserted. Not product code."""
s = open("secdef_audit_v21.py").read()
def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:80]); s = s.replace(old, new)
rep('"""v21 reference (ONE signature', '''"""v22 reference = v21 plus (MJ3) catalog checks that do not depend on the text of the files: the eight named DB-3 constraints exist, are validated and are CHECK constraints; the triggers on the
five spend and kill-switch tables and the four audit tables are exactly the expected ones (name, table, timing and events from pg_trigger.tgtype, function, enabled); the runtime and operator roles hold exactly the
table rights of the grant table (probe with has_table_privilege and has_any_column_privilege) and no rights on the two DB-2 records; the runtime role is not a superuser, does not own a table and is not a member of the owner role;
(MJ4) a dedicated owner (L26) is checked to be NOLOGIN, not a superuser, without CREATEROLE, CREATEDB or BYPASSRLS, and without any right on a table outside the eight it needs; the message for a wrong owner now says what the owner was
compared with (v21 said "the migration role" while the code compared the database owner); (M2) `l19_check_applies`: the L19 temporary-table check applies when the decrease record exists OR the audit-reader role exists; (M4) `inputs_from_config`:
the one function that turns the two settings objects into the arguments, so `startup_checks` has its inputs. The v21 text follows unchanged.

v21 reference (ONE signature''')
rep('''def secdef_problems(db, *, roles: dict[str, str], policy: dict | None = None, owner: str | None = None) -> list[str]:''', '''# ---- v22 (MJ3): the exact objects. Tables of the spend track: SPEND_TABLES hold the money (DB-3 gives the runtime role SELECT only); RECORD_TABLES are the two DB-2 records (the runtime role holds NOTHING).
SPEND_TABLES = ("spend", "spend_month", "kill_switch")
RECORD_TABLES = ("spend_decrease_log", "kill_switch_log")
DB3_CONSTRAINTS = {  # table -> the named CHECK constraints the DB-3 file adds (eight: four per table; the two open_usd columns are checked separately)
    "spend": ("spend_open_ok", "spend_guarded_ok", "spend_agent_len", "spend_day_window"),
    "spend_month": ("spend_month_open_ok", "spend_month_guarded_ok", "spend_month_agent_len", "spend_month_window"),
}
# tgtype bits (pg_trigger.tgtype): 1 = row level, 2 = BEFORE, 4 = INSERT, 8 = DELETE, 16 = UPDATE, 32 = TRUNCATE, 64 = INSTEAD OF
T_BU, T_AU, T_AI, T_BUD, T_BT = 1 | 2 | 16, 1 | 16, 1 | 4, 1 | 2 | 16 | 8, 2 | 32
TRIGGER_POLICY = {  # trigger name -> (table, tgtype, function name); the product migration 0002 and the held DB-2 file
    "audit_entries_append_only": ("audit_entries", T_BUD, "hadavin_audit_append_only"), "audit_checkpoints_append_only": ("audit_checkpoints", T_BUD, "hadavin_audit_append_only"),
    "audit_entries_no_truncate": ("audit_entries", T_BT, "hadavin_audit_append_only"), "audit_checkpoints_no_truncate": ("audit_checkpoints", T_BT, "hadavin_audit_append_only"),
    "spend_keep_keys": ("spend", T_BU, "spend_keep_keys"), "spend_month_keep_keys": ("spend_month", T_BU, "spend_keep_keys"),
    "spend_log_decrease": ("spend", T_AU, "spend_log_decrease"), "spend_month_log_decrease": ("spend_month", T_AU, "spend_log_decrease"),
    "kill_switch_log_change": ("kill_switch", T_AU, "kill_switch_log_change"), "kill_switch_log_insert": ("kill_switch", T_AI, "kill_switch_log_insert"),
    "spend_decrease_log_append_only": ("spend_decrease_log", T_BUD, "audit_log_append_only"), "spend_decrease_log_no_truncate": ("spend_decrease_log", T_BT, "audit_log_append_only"),
    "kill_switch_log_append_only": ("kill_switch_log", T_BUD, "audit_log_append_only"), "kill_switch_log_no_truncate": ("kill_switch_log", T_BT, "audit_log_append_only"),
}
DB2_TRIGGERS = {k for k, v in TRIGGER_POLICY.items() if not k.startswith("audit_")}
ALL_PRIV = ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER")
def _priv(db, role: str, table: str, priv: str) -> bool:
    """Table right of a role: INSERT, UPDATE and REFERENCES also count when held on one column only (has_any_column_privilege)."""
    f = "has_any_column_privilege" if priv in ("INSERT", "UPDATE", "REFERENCES", "SELECT") else "has_table_privilege"
    return bool(db.execute(f"SELECT {f}(%s, to_regclass(%s), %s)", (role, table, priv)).fetchone()[0])
def _exists(db, table: str) -> bool: return db.execute("SELECT to_regclass(%s) IS NOT NULL", (table,)).fetchone()[0]

def catalog_problems(db, *, roles: dict[str, str], owner: str, explicit_owner: bool, db2: bool, db3: bool) -> list[str]:
    """v22 MJ3 and MJ4: checks of the catalog that do not read the text of any file."""
    problems = []
    rt, op = roles["runtime"], roles.get("operator") or ""
    if db3:   # constraints: exist, validated, CHECK (a dropped or NOT VALID constraint is invisible to every file check)
        for tbl, names in DB3_CONSTRAINTS.items():
            got = {r[0]: (r[1], r[2]) for r in db.execute("SELECT conname, convalidated, contype FROM pg_constraint WHERE conrelid = to_regclass(%s)", (tbl,)).fetchall()}
            for nm in names:
                if nm not in got: problems.append(f"constraint {nm} on {tbl} is missing")
                elif got[nm][1] != "c": problems.append(f"constraint {nm} on {tbl} is not a CHECK constraint (type {got[nm][1]!r})")
                elif not got[nm][0]: problems.append(f"constraint {nm} on {tbl} is NOT VALID (it checks new rows only)")
            col = db.execute("SELECT 1 FROM pg_attribute WHERE attrelid = to_regclass(%s) AND attname = 'open_usd' AND NOT attisdropped AND attnotnull", (tbl,)).fetchone()
            if not col: problems.append(f"column {tbl}.open_usd is missing or allows NULL")
    # triggers: exactly the expected ones on the tables of the track (name, table, timing and events, function, enabled)
    schema = db.execute("SELECT current_schema()").fetchone()[0]
    expect = {k: v for k, v in TRIGGER_POLICY.items() if (k in DB2_TRIGGERS and db2) or (k not in DB2_TRIGGERS and _exists(db, v[0]))}
    tables = sorted({v[0] for v in TRIGGER_POLICY.values()} | set(SPEND_TABLES) | set(RECORD_TABLES))
    rows = db.execute("SELECT t.tgname, c.relname, t.tgtype, p.proname, t.tgenabled FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid JOIN pg_namespace n ON n.oid = c.relnamespace "
                      "JOIN pg_proc p ON p.oid = t.tgfoid WHERE NOT t.tgisinternal AND n.nspname = %s AND c.relname = ANY(%s)", (schema, tables)).fetchall()
    seen = set()
    for nm, rel, ty, fn, en in rows:
        seen.add(nm)
        if nm not in expect: problems.append(f"unexpected trigger {nm} on {rel} (function {fn})"); continue
        want = expect[nm]
        if (rel, ty, fn) != want: problems.append(f"trigger {nm} is {(rel, ty, fn)} but must be {want} (table, tgtype bits, function)")
        if en != "O": problems.append(f"trigger {nm} on {rel} is not enabled (state {en!r})")
    for nm in sorted(set(expect) - seen): problems.append(f"trigger {nm} on {expect[nm][0]} is missing")
    # the table rights of the grant table (5.6c item 5): probe, do not trust the GRANTS map
    if db3:
        for t in SPEND_TABLES:
            for p in ALL_PRIV:
                has = _priv(db, rt, t, p)
                if has != (p == "SELECT"): problems.append(f"runtime role {rt} {'holds' if has else 'lacks'} {p} on {t} (must hold SELECT only)")
                if op and _priv(db, op, t, p): problems.append(f"operator role {op} holds {p} on {t} (it holds no table right)")
    for t in RECORD_TABLES:
        if _exists(db, t):
            for p in ALL_PRIV:
                if _priv(db, rt, t, p): problems.append(f"runtime role {rt} holds {p} on {t} (it holds nothing on the records)")
                if op and _priv(db, op, t, p): problems.append(f"operator role {op} holds {p} on {t}")
    # the runtime role: not a superuser, owns none of the tables, not a member of the owner role
    r = db.execute("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = %s", (rt,)).fetchone()
    if r is None: problems.append(f"runtime role {rt} does not exist")
    else:
        if r[0]: problems.append(f"runtime role {rt} is a superuser")
        if r[1]: problems.append(f"runtime role {rt} has BYPASSRLS")
    for t in SPEND_TABLES + RECORD_TABLES:
        o = db.execute("SELECT pg_get_userbyid(relowner) FROM pg_class WHERE oid = to_regclass(%s)", (t,)).fetchone()
        if o and o[0] == rt: problems.append(f"runtime role {rt} owns table {t}")
    if rt != owner and db.execute("SELECT pg_has_role(%s, %s, 'MEMBER')", (rt, owner)).fetchone()[0]: problems.append(f"runtime role {rt} is a member of the owner role {owner}")
    if explicit_owner:   # MJ4: the dedicated owner (L26) must be as narrow as its design says
        o = db.execute("SELECT rolcanlogin, rolsuper, rolcreaterole, rolcreatedb, rolbypassrls FROM pg_roles WHERE rolname = %s", (owner,)).fetchone()
        if o is None: problems.append(f"owner role {owner} does not exist")
        else:
            for flag, lab in zip(o, ("can log in", "is a superuser", "has CREATEROLE", "has CREATEDB", "has BYPASSRLS")):
                if flag: problems.append(f"owner role {owner} {lab} (the dedicated owner is NOLOGIN and holds no role right)")
        allowed = {"spend": {"SELECT", "INSERT", "UPDATE"}, "spend_month": {"SELECT", "INSERT", "UPDATE"}, "kill_switch": {"SELECT", "INSERT", "UPDATE"}, "spend_decrease_log": {"INSERT"}, "kill_switch_log": {"INSERT"}}
        for (t,) in db.execute("SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relkind IN ('r', 'p') AND n.nspname = %s ORDER BY 1", (schema,)).fetchall():
            for p in ALL_PRIV:
                if p not in allowed.get(t, set()) and _priv(db, owner, t, p): problems.append(f"owner role {owner} holds {p} on {t} (the dedicated owner holds only the rights of 5.6c item 8)")
    return problems

def l19_check_applies(db, audit_reader_role: str) -> bool:
    """v22 readiness M2: the temporary-table check of 5.6 item 1(h) (L19) applies when the decrease record exists OR the audit-reader role exists. Runtime connection, no table right needed.
    An empty `audit_reader_role` means no role (that half is off)."""
    rec = db.execute("SELECT to_regclass('spend_decrease_log') IS NOT NULL").fetchone()[0]
    role = bool(audit_reader_role) and db.execute("SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = %s)", (audit_reader_role,)).fetchone()[0]
    return bool(rec or role)

def inputs_from_config(spend, postgres) -> dict:
    """v22 readiness M4: the one place that turns the settings into the arguments of `secdef_problems` and `l19_check_applies` (so `PostgresStore.startup_checks(self, environment, *, spend, postgres)` has its inputs):
    `spend.operator_role` (new, S-2b, default ''), `postgres.runtime_role` (the role the store connects as: the user part of its own connection settings, never a password), `postgres.audit_reader_role` (existing field
    named in 5.6 (g2)), `postgres.definer_owner_role` (new, S-2b, default '' = the database owner; set only when the lead chooses L26) and `spend.kill_switch_alert_minutes` (new, default 60)."""
    return {"roles": {"runtime": postgres.runtime_role, "operator": spend.operator_role or ""}, "owner": (postgres.definer_owner_role or None),
            "audit_reader_role": postgres.audit_reader_role or "", "alert_minutes": spend.kill_switch_alert_minutes}

def secdef_problems(db, *, roles: dict[str, str], policy: dict | None = None, owner: str | None = None) -> list[str]:''')
rep('''    owner = owner or db.execute("SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname = current_database()").fetchone()[0]''',
    '''    dba = db.execute("SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname = current_database()").fetchone()[0]
    explicit_owner = bool(owner) and owner != dba   # a dedicated owner (L26) is a role that is NOT the database owner; passing the database owner's own name is the default path
    owner = owner or dba''')
rep('''problems.append(f"{where}: owned by {own}{' (a superuser)' if is_super else ''}, expected the migration role {owner}")''',
    '''problems.append(f"{where}: owned by {own}{' (a superuser)' if is_super else ''}, expected {owner} ({'the dedicated owner role you passed' if explicit_owner else 'the database owner, pg_database.datdba'}) and not a superuser: on a database owned by a superuser, or a managed database whose migration role is not the database owner, the default owner can never pass; use the dedicated NOLOGIN owner role (lead choice L26)")''')
rep('''    return problems

def apply_function_grants''', '''    db3 = any(k in DB3_FUNCTIONS for k in policy); db2 = any(k in DB2_FUNCTIONS for k in policy)
    problems += catalog_problems(db, roles=roles, owner=owner, explicit_owner=explicit_owner, db2=db2, db3=db3)   # v22 MJ3 / MJ4
    return problems

def apply_function_grants''')
rep("expected {sorted(want)}\")\n        if lack", "expected {sorted(want)}\")\n        if lack", 0) if False else None
open("secdef_audit_v22.py", "w").write(s); print("written", len(s))
