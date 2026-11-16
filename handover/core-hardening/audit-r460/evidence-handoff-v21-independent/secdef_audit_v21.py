"""v21 reference (ONE signature, round 8: secdef_problems(db, *, roles, policy=None, owner=None); policy None = the policy of the files that are applied, see policy_for_applied; owner None = the owner of the database, pg_database.datdba;
the v20 text said three different signatures and two different owners). v21 also checks the operators and functions a BEGIN ATOMIC body was bound to (security minor m10: they bind at creation with the creating session's search_path).
v20 reference for the start-up and migrate-time audit of SECURITY DEFINER functions that exist IN THE DATABASE (security major MA2 of the v17
review: v17 text promised it and no query, owner or test existed). Not product code. Two callers use the one function:
  (1) `migrate()` (DB-3 PR), after it applied the grants of the runtime role, in the same transaction: a problem rolls the run back;
  (2) `PostgresStore.startup_checks` (S-2b, 5.5b item 3b), on the RUNTIME connection (pg_proc, pg_roles and aclexplode need no table privilege).
The guard of secdef_guard_v18.py reads .sql files; this reads what is really installed, so a function made in a console is seen.
POLICY: signature -> (kind, who may EXECUTE besides the owner). Roles are names from config, passed in `roles`."""
from __future__ import annotations
FUNCTION_POLICY = {
    "spend_reserve(text,date,numeric)": ("definer", {"runtime"}),
    "spend_settle(text,date,numeric,numeric)": ("definer", {"runtime"}),
    "kill_switch_engage()": ("definer", {"operator"}),   # v21 DEFAULT (least privilege, lead choice L22b): only the operator role stops the switch from the database; the runtime role refuses calls in its own process; the alternative {"runtime", "operator"} is owner-open
    "kill_switch_release()": ("definer", {"operator"}),
    # DB-2 (when applied): trigger functions run only by the trigger machinery; nobody is granted EXECUTE
    "spend_log_decrease()": ("definer", set()),
    "kill_switch_log_change()": ("definer", set()),
    "kill_switch_log_insert()": ("definer", set()),  # v20 (DB-2, security minor m1)
}
# every SECURITY DEFINER function in every non-system schema, with owner, settings, who can EXECUTE it (aclexplode of the real ACL, or of the default
# ACL when none is stored), whether it has a BEGIN ATOMIC body and the schemas of the relations that body was bound to (pg_depend)
SECDEF_SQL = """
SELECT n.nspname, p.proname, p.oid::regprocedure::text, pg_get_userbyid(p.proowner), r.rolsuper, p.proconfig, p.prosqlbody IS NOT NULL,
  ARRAY(SELECT DISTINCT CASE WHEN a.grantee = 0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END
        FROM aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) a WHERE a.privilege_type = 'EXECUTE' ORDER BY 1),
  ARRAY(SELECT DISTINCT CASE WHEN a.grantee = 0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END
        FROM aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) a WHERE a.privilege_type = 'EXECUTE' AND a.is_grantable AND a.grantee <> p.proowner ORDER BY 1),
  ARRAY(SELECT DISTINCT dn.nspname FROM pg_depend d JOIN pg_class c ON c.oid = d.refobjid AND d.refclassid = 'pg_class'::regclass
        JOIN pg_namespace dn ON dn.oid = c.relnamespace WHERE d.objid = p.oid AND d.classid = 'pg_proc'::regclass ORDER BY 1),
  ARRAY(SELECT DISTINCT x.nspname FROM (
          SELECT fn2.nspname FROM pg_depend d JOIN pg_proc q ON q.oid = d.refobjid AND d.refclassid = 'pg_proc'::regclass JOIN pg_namespace fn2 ON fn2.oid = q.pronamespace WHERE d.objid = p.oid AND d.classid = 'pg_proc'::regclass
          UNION ALL
          SELECT on2.nspname FROM pg_depend d JOIN pg_operator o ON o.oid = d.refobjid AND d.refclassid = 'pg_operator'::regclass JOIN pg_namespace on2 ON on2.oid = o.oprnamespace WHERE d.objid = p.oid AND d.classid = 'pg_proc'::regclass) x ORDER BY 1)
FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace JOIN pg_roles r ON r.oid = p.proowner
WHERE p.prosecdef AND n.nspname NOT IN ('pg_catalog', 'information_schema') AND n.nspname NOT LIKE 'pg\\_toast%%' ORDER BY 1, 3
"""
def _sig(regproc: str, proname: str) -> str:
    """'spend_settle(text,date,numeric,numeric)' from 'app.spend_settle(text,date,numeric,numeric)' (regprocedure prints names and types only)."""
    s = regproc.split("(", 1)
    return proname + "(" + s[1].replace(", ", ",")  # v20 (security minor m5): the name is pg_proc.proname, so a function called "x.spend_settle" is no longer read as spend_settle

DB3_FUNCTIONS = ("spend_reserve(text,date,numeric)", "spend_settle(text,date,numeric,numeric)", "kill_switch_engage()", "kill_switch_release()")
DB2_FUNCTIONS = ("spend_log_decrease()", "kill_switch_log_change()", "kill_switch_log_insert()")
def policy_for_applied(db, policy: dict = FUNCTION_POLICY) -> dict:
    """Which files are applied is read from the DATABASE, not from a file ledger (a hand-made function must not look like an applied file): DB-3 is applied when the column spend.open_usd exists (its first ALTER),
    DB-2 when the table spend_decrease_log exists. A function of an unapplied file is not on the policy, so if it exists anyway it is reported as unexpected."""
    db3 = db.execute("SELECT 1 FROM pg_attribute WHERE attrelid = to_regclass('spend') AND attname = 'open_usd' AND NOT attisdropped").fetchone() is not None
    db2 = db.execute("SELECT to_regclass('spend_decrease_log') IS NOT NULL").fetchone()[0]
    return {k: v for k, v in policy.items() if (k in DB3_FUNCTIONS and db3) or (k in DB2_FUNCTIONS and db2)}

def secdef_problems(db, *, roles: dict[str, str], policy: dict | None = None, owner: str | None = None) -> list[str]:
    """roles = {"runtime": name, "operator": name or ""}; policy None = policy_for_applied(db); owner None = the database owner (pg_database.datdba), or the dedicated NOLOGIN owner role when the lead chose L26 (then pass its name).
    An unset operator role is a problem when a listed function needs it (v20 raised KeyError). Returns problems (empty = clean)."""
    problems, seen = [], set()
    policy = policy_for_applied(db) if policy is None else policy
    owner = owner or db.execute("SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname = current_database()").fetchone()[0]
    schema = db.execute("SELECT current_schema()").fetchone()[0]
    for nsp, name, regproc, own, is_super, config, atomic, grantees, grantable, dep_schemas, dep_other in db.execute(SECDEF_SQL).fetchall():
        sig = _sig(regproc, name); where = f"{nsp}.{sig}"
        if nsp != schema or sig not in policy or policy[sig][0] != "definer":
            problems.append(f"unexpected SECURITY DEFINER function {where} (owner {own})"); continue
        seen.add(sig)
        if own != owner or is_super: problems.append(f"{where}: owned by {own}{' (a superuser)' if is_super else ''}, expected the migration role {owner}")
        if list(config or []) != ["search_path=pg_catalog, pg_temp"]: problems.append(f"{where}: settings {config} are not exactly search_path=pg_catalog, pg_temp")
        for w in policy[sig][1]:
            if not roles.get(w): problems.append(f"{where}: the {w} role is not configured, so EXECUTE cannot be checked")
        want = {roles[w] for w in policy[sig][1] if roles.get(w)}
        extra = (set(grantees) - {own}) - want
        lack = want - set(grantees)
        if grantable: problems.append(f"{where}: EXECUTE is held WITH GRANT OPTION by {sorted(grantable)} (it could pass the right on)")
        if extra: problems.append(f"{where}: EXECUTE is held by {sorted(extra)} (PUBLIC means everyone), expected only {sorted(want)}")
        if lack: problems.append(f"{where}: EXECUTE is missing for {sorted(lack)}")
        if atomic and set(dep_other) - {"pg_catalog"}: problems.append(f"{where}: bound to functions or operators in schema {sorted(set(dep_other) - {'pg_catalog'})}, not pg_catalog (they bind at creation with the creating session's search_path)")
        if atomic and set(dep_schemas) - {nsp}: problems.append(f"{where}: bound to relations in schema {sorted(set(dep_schemas) - {nsp})}, not only {nsp}")
    # a listed function that is missing is a problem only when its file is applied: the caller passes `policy` limited to the applied files
    for sig in sorted(set(policy) - seen): problems.append(f"{schema}.{sig}: listed but not installed as SECURITY DEFINER")
    # v21 (security review of v19 M2, v20 note): the audit triggers must exist and be ENABLED (tgenabled = 'O'); an owner can run ALTER TABLE ... DISABLE TRIGGER at run time and no file check sees it
    tnames = sorted({sig.split("(")[0] for sig, (_k, who) in policy.items() if not who})
    if tnames:
        trig = db.execute("SELECT p.proname, t.tgname, c.relname, t.tgenabled FROM pg_trigger t JOIN pg_proc p ON p.oid = t.tgfoid JOIN pg_class c ON c.oid = t.tgrelid WHERE NOT t.tgisinternal AND p.proname = ANY(%s)", (tnames,)).fetchall()
        for fn, tg, rel, en in trig:
            if en != "O": problems.append(f"trigger {tg} on {rel} (function {fn}) is not enabled (state {en!r}; 'D' = disabled, 'R'/'A' = fires only for some sessions)")
        for fn in tnames:
            if f"{fn}()" in seen and not any(x[0] == fn for x in trig): problems.append(f"{fn}() is installed but no trigger uses it")
    if roles.get("operator") and db.execute("SELECT pg_has_role(%s, %s, 'MEMBER')", (roles["runtime"], roles["operator"])).fetchone()[0]:
        problems.append(f"{roles['runtime']} is a member of {roles['operator']}: it would hold kill_switch_release")
    return problems

def apply_function_grants(db, *, roles: dict[str, str], policy: dict | None = None) -> None:
    """What migrate() does for the 'function' kind of GRANTS (prototype): per function, REVOKE from PUBLIC, the runtime and operator roles, then GRANT the exact roles.
    Run at EVERY migrate() call, after the table grants. Role names are config values, never SQL text of the file."""
    from psycopg import sql
    policy = policy_for_applied(db) if policy is None else policy
    for sig, (kind, who) in policy.items():
        name, args = sig.split("(", 1); args = args.rstrip(")")
        fn = sql.SQL("{}({})").format(sql.Identifier(name), sql.SQL(args.replace(",", ", ")))
        for r in {x for x in (roles["runtime"], roles.get("operator")) if x}: db.execute(sql.SQL("REVOKE ALL ON FUNCTION {} FROM {}").format(fn, sql.Identifier(r)))
        db.execute(sql.SQL("REVOKE ALL ON FUNCTION {} FROM PUBLIC").format(fn))
        for w in who: db.execute(sql.SQL("GRANT EXECUTE ON FUNCTION {} TO {}").format(fn, sql.Identifier(roles[w])))
