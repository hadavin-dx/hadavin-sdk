"""v18 reference for the start-up and migrate-time audit of SECURITY DEFINER functions that exist IN THE DATABASE (security major MA2 of the v17
review: v17 text promised it and no query, owner or test existed). Not product code. Two callers use the one function:
  (1) `migrate()` (DB-3 PR), after it applied the grants of the runtime role, in the same transaction: a problem rolls the run back;
  (2) `PostgresStore.startup_checks` (S-2b, 5.5b item 3b), on the RUNTIME connection (pg_proc, pg_roles and aclexplode need no table privilege).
The guard of secdef_guard_v18.py reads .sql files; this reads what is really installed, so a function made in a console is seen.
POLICY: signature -> (kind, who may EXECUTE besides the owner). Roles are names from config, passed in `roles`."""
from __future__ import annotations
FUNCTION_POLICY = {
    "spend_reserve(text,date,numeric)": ("definer", {"runtime"}),
    "spend_settle(text,date,numeric,numeric)": ("definer", {"runtime"}),
    "kill_switch_engage()": ("definer", {"runtime"}),
    "kill_switch_release()": ("definer", {"operator"}),
    # DB-2 (when applied): trigger functions run only by the trigger machinery; nobody is granted EXECUTE
    "spend_log_decrease()": ("definer", set()),
    "kill_switch_log_change()": ("definer", set()),
}
# every SECURITY DEFINER function in every non-system schema, with owner, settings, who can EXECUTE it (aclexplode of the real ACL, or of the default
# ACL when none is stored), whether it has a BEGIN ATOMIC body and the schemas of the relations that body was bound to (pg_depend)
SECDEF_SQL = """
SELECT n.nspname, p.proname, p.oid::regprocedure::text, pg_get_userbyid(p.proowner), r.rolsuper, p.proconfig, p.prosqlbody IS NOT NULL,
  ARRAY(SELECT DISTINCT CASE WHEN a.grantee = 0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee) END
        FROM aclexplode(coalesce(p.proacl, acldefault('f', p.proowner))) a WHERE a.privilege_type = 'EXECUTE' ORDER BY 1),
  ARRAY(SELECT DISTINCT dn.nspname FROM pg_depend d JOIN pg_class c ON c.oid = d.refobjid AND d.refclassid = 'pg_class'::regclass
        JOIN pg_namespace dn ON dn.oid = c.relnamespace WHERE d.objid = p.oid AND d.classid = 'pg_proc'::regclass ORDER BY 1)
FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace JOIN pg_roles r ON r.oid = p.proowner
WHERE p.prosecdef AND n.nspname NOT IN ('pg_catalog', 'information_schema') AND n.nspname NOT LIKE 'pg\\_toast%%' ORDER BY 1, 3
"""
def _sig(regproc: str, schema_of_name: str) -> str:
    """'spend_settle(text,date,numeric,numeric)' from 'app.spend_settle(text,date,numeric,numeric)' (regprocedure prints names and types only)."""
    s = regproc.split("(", 1)
    return s[0].rsplit(".", 1)[-1].strip('"') + "(" + s[1].replace(", ", ",")

def secdef_problems(db, *, roles: dict[str, str], owner: str, policy: dict = FUNCTION_POLICY) -> list[str]:
    """roles = {"runtime": name, "operator": name}; owner = the migration role that must own every function. Returns problems (empty = clean)."""
    problems, seen = [], set()
    schema = db.execute("SELECT current_schema()").fetchone()[0]
    for nsp, name, regproc, own, is_super, config, atomic, grantees, dep_schemas in db.execute(SECDEF_SQL).fetchall():
        sig = _sig(regproc, nsp); where = f"{nsp}.{sig}"
        if nsp != schema or sig not in policy or policy[sig][0] != "definer":
            problems.append(f"unexpected SECURITY DEFINER function {where} (owner {own})"); continue
        seen.add(sig)
        if own != owner or is_super: problems.append(f"{where}: owned by {own}{' (a superuser)' if is_super else ''}, expected the migration role {owner}")
        if list(config or []) != ["search_path=pg_catalog, pg_temp"]: problems.append(f"{where}: settings {config} are not exactly search_path=pg_catalog, pg_temp")
        want = {roles[w] for w in policy[sig][1]}
        extra = (set(grantees) - {own}) - want
        lack = want - set(grantees)
        if extra: problems.append(f"{where}: EXECUTE is held by {sorted(extra)} (PUBLIC means everyone), expected only {sorted(want)}")
        if lack: problems.append(f"{where}: EXECUTE is missing for {sorted(lack)}")
        if atomic and set(dep_schemas) - {nsp}: problems.append(f"{where}: bound to relations in schema {sorted(set(dep_schemas) - {nsp})}, not only {nsp}")
    # a listed function that is missing is a problem only when its file is applied: the caller passes `policy` limited to the applied files
    for sig in sorted(set(policy) - seen): problems.append(f"{schema}.{sig}: listed but not installed as SECURITY DEFINER")
    if db.execute("SELECT pg_has_role(%s, %s, 'MEMBER')", (roles["runtime"], roles["operator"])).fetchone()[0]:
        problems.append(f"{roles['runtime']} is a member of {roles['operator']}: it would hold kill_switch_release")
    return problems

def apply_function_grants(db, *, roles: dict[str, str], policy: dict = FUNCTION_POLICY) -> None:
    """What migrate() does for the 'function' kind of GRANTS (prototype): per function, REVOKE from PUBLIC, the runtime and operator roles, then GRANT the exact roles.
    Run at EVERY migrate() call, after the table grants. Role names are config values, never SQL text of the file."""
    from psycopg import sql
    for sig, (kind, who) in policy.items():
        name, args = sig.split("(", 1); args = args.rstrip(")")
        fn = sql.SQL("{}({})").format(sql.Identifier(name), sql.SQL(args.replace(",", ", ")))
        for r in {roles["runtime"], roles["operator"]}: db.execute(sql.SQL("REVOKE ALL ON FUNCTION {} FROM {}").format(fn, sql.Identifier(r)))
        db.execute(sql.SQL("REVOKE ALL ON FUNCTION {} FROM PUBLIC").format(fn))
        for w in who: db.execute(sql.SQL("GRANT EXECUTE ON FUNCTION {} TO {}").format(fn, sql.Identifier(roles[w])))
