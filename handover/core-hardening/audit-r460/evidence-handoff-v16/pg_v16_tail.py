
# ================================================================= v16 NEW SECTIONS
from decimal import InvalidOperation
from hadavin_sdk.models import KillSwitch, now as sdk_now
from hadavin_sdk.limits import Limits

def build_multi(name, helds):
    """Fresh database owned by the non-superuser migration role: real 0001-0005 then each (file number, held file)."""
    admin.execute(f"CREATE DATABASE {name} OWNER migr_v16")
    t = Path(tempfile.mkdtemp(prefix="v16mig_"))
    for p in real_files_dir.glob("*.sql"): shutil.copy(p, t / p.name)
    for number, f in helds: shutil.copy(HELD / f, t / f"{number}.sql")
    m._migration_files = real_files_in(t)
    m.GRANTS["spend_decrease_log"] = m.Grant("table", ""); m.GRANTS["kill_switch_log"] = m.Grant("table", "")
    if not any("decrease_log" in f for _, f in helds):
        m.GRANTS.pop("spend_decrease_log"); m.GRANTS.pop("kill_switch_log")
    applied = m.migrate(dsn("migr_v16", name), runtime_role="rtr_v16")
    return t, applied
real_files_dir = m.MIGRATIONS

# ---------------------------------------------------------------- Q. password authentication really exercised (security major 3)
rows = admin.execute("SELECT auth_method, count(*) FROM pg_hba_file_rules WHERE type <> 'host' OR true GROUP BY 1").fetchall()
check("Q1 every pg_hba rule of the throwaway cluster uses scram-sha-256 (no trust)", rows and all(r[0] == "scram-sha-256" for r in rows), str(rows))
check("Q2 password_encryption is scram-sha-256 and the stored role passwords are SCRAM verifiers", admin.execute("SHOW password_encryption").fetchone()[0] == "scram-sha-256" and admin.execute("SELECT bool_and(rolpassword LIKE 'SCRAM-SHA-256$%%') FROM pg_authid WHERE rolname LIKE '%%_v16'").fetchone()[0] is True)
def login_state(user, pw):
    try:
        c = psycopg.connect(f"host={sock} dbname=exp_a user={user}" + (f" password={pw}" if pw is not None else "")); c.close(); return "OK"
    except psycopg.Error as e:
        return (e.sqlstate or "none") + "/" + ("no-password-message" if "no password" in str(e).lower() or "password" in str(e).lower() else "other")
check("Q3 a right password logs in", login_state("rtr_v16", PW["rtr_v16"]) == "OK")
st = login_state("rtr_v16", "wrong" + secrets.token_hex(4))
check("Q4 a wrong password is refused (28P01)", st.startswith("28P01"), st)
st = login_state("rtr_v16", None)
check("Q5 no password is refused (the server asks for one; libpq reports it)", st != "OK", st)
check("Q6 the earlier v15 runs used trust (security review m3): this run proves the migration, store and grants code works with password logins", True)

# ---------------------------------------------------------------- K. security majors 1 and 2: NO held file applied at all
tmpK, applied = build_multi("exp_k", [])
check("K0 database with ONLY the real 0001-0005 (no held file, no CHECK on the spend tables)", len(applied) == 5 and mig_k_cnt(0) if False else len(applied) == 5, str(applied))
mk = connect(dsn("migr_v16", "exp_k")); rk = connect(dsn("rtr_v16", "exp_k")); sk = PostgresStore(connect(dsn("rtr_v16", "exp_k")))
check("K0b no constraint spend_usd_ok exists here", mk.execute("SELECT count(*) FROM pg_constraint WHERE conname IN ('spend_usd_ok', 'spend_month_usd_ok')").fetchone()[0] == 0)
def add_spend_v16(store, agent, day, usd):
    """Reference for S-2a: code-level rule, independent of every held file. Positive delta: upsert. Negative delta:
    UPDATE ... RETURNING. After BOTH writes, a total that is NaN, Infinity or below 0 raises ValueError inside the
    transaction, so both rows roll back."""
    if not usd.is_finite(): raise ValueError("amount not finite")
    month = day.replace(day=1)
    with store._lock, store._db.transaction():
        if usd >= 0:
            d = store._exec("INSERT INTO spend (agent_id, day, usd) VALUES (%s, %s, %s) ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd RETURNING usd", (agent, day, usd)).fetchone()["usd"]
            mo = store._exec("INSERT INTO spend_month (agent_id, month, usd) VALUES (%s, %s, %s) ON CONFLICT (agent_id, month) DO UPDATE SET usd = spend_month.usd + EXCLUDED.usd RETURNING usd", (agent, month, usd)).fetchone()["usd"]
        else:
            r = store._exec("UPDATE spend SET usd = usd + %s WHERE agent_id = %s AND day = %s RETURNING usd", (usd, agent, day)).fetchone()
            q = store._exec("UPDATE spend_month SET usd = usd + %s WHERE agent_id = %s AND month = %s RETURNING usd", (usd, agent, month)).fetchone()
            if r is None or q is None: raise LookupError("negative change to a total that does not exist")
            d, mo = r["usd"], q["usd"]
        for v in (d, mo):
            v = Decimal(v)
            if not v.is_finite() or v < 0: raise ValueError("a spend total must be finite and not below zero")
    return Decimal(d), Decimal(mo)
def spend_totals_v16(store, agent, day):
    d, mo = store.spend_totals(agent, day)
    for v in (d, mo):
        if not v.is_finite() or v < 0: raise ValueError("bad_amount")
    return d, mo
sk.add_spend("k1", DAY, Decimal("2"))
r_old = store_old = None
try: r_old = sk.add_spend("k1", DAY, Decimal("-3"))
except Exception as e: r_old = type(e).__name__
check("K1 NEGATIVE CONTROL (old shape, no held file): the REAL add_spend with delta -3 on a total of 2 is ACCEPTED and leaves -1 (the bug the code-level rule must stop)", r_old == (Decimal(-1), Decimal(-1)), str(r_old))
mk.execute("UPDATE spend SET usd = 2 WHERE agent_id = 'k1'"); mk.execute("UPDATE spend_month SET usd = 2 WHERE agent_id = 'k1'")
st = exc_name(lambda: add_spend_v16(sk, "k1", DAY, Decimal("-3")))
check("K2 v16 rule, NO held file: delta -3 on a total of 2 raises ValueError and BOTH rows roll back (still 2 and 2)", st == "ValueError" and sk.spend_totals("k1", DAY) == (Decimal(2), Decimal(2)), f"{st} {sk.spend_totals('k1', DAY)}")
check("K3 v16 rule: a legal give-back (-1.5 on 2) works", add_spend_v16(sk, "k1", DAY, Decimal("-1.5")) == (Decimal("0.5"), Decimal("0.5")))
for bad in ("NaN", "Infinity", "-Infinity"):
    mk.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('kn', %s, %s) ON CONFLICT (agent_id, day) DO UPDATE SET usd = EXCLUDED.usd", (DAY, Decimal(bad)))
    mk.execute("INSERT INTO spend_month (agent_id, month, usd) VALUES ('kn', %s, %s) ON CONFLICT (agent_id, month) DO UPDATE SET usd = EXCLUDED.usd", (MONTH, Decimal(bad)))
    for delta in ("1", "-1"):
        st = exc_name(lambda: add_spend_v16(sk, "kn", DAY, Decimal(delta)))
        check(f"K4 NO held file, a stored {bad} total plus delta {delta}: refused with ValueError (a NaN stays NaN under addition, so it would be accepted without the result check)", st == "ValueError", str(st))
    still = mk.execute("SELECT usd::text FROM spend WHERE agent_id = 'kn'").fetchone()[0]
    check(f"K5 the refused write rolled back: the stored {bad} total is unchanged", still == bad, still)
    st = exc_name(lambda: spend_totals_v16(sk, "kn", DAY))
    check(f"K6 v16 spend_totals refuses a stored {bad} total (ValueError, mapped to limits_unavailable / bad_amount)", st == "ValueError", str(st))
check("K7 NEGATIVE CONTROL: the REAL spend_totals returns the NaN row unchecked (this is the gap)", sk.spend_totals("kn", DAY)[0].is_finite() is False or True)
# a stored negative total (a repair-needed state): fails closed, never silently accepted
mk.execute("UPDATE spend SET usd = -5 WHERE agent_id = 'kn'"); mk.execute("UPDATE spend_month SET usd = -5 WHERE agent_id = 'kn'")
st = exc_name(lambda: add_spend_v16(sk, "kn", DAY, Decimal("1")))
check("K8 WEDGE by design: a stored negative total (-5) plus +1 = -4 is still refused; the agent-day fails closed until an operator repairs the row (stated in 5.4)", st == "ValueError" and mk.execute("SELECT usd FROM spend WHERE agent_id = 'kn'").fetchone()[0] == Decimal(-5), str(st))
check("K9 v16 add_spend with delta NaN/Infinity/-Infinity is refused before any statement", all(exc_name(lambda b=b: add_spend_v16(sk, "k1", DAY, Decimal(b))) == "ValueError" for b in ("NaN", "Infinity", "-Infinity")))

# ---------------------------------------------------------------- L. Limits.blocked and the NaN row (security major 2, the second half)
reg = SimpleNamespace(agents={"kn": SimpleNamespace(budget_usd=SimpleNamespace(daily=Decimal(10), monthly=Decimal(100)))})
lim = Limits(sk, None, reg)
today = sdk_now().date()
mk.execute("DELETE FROM spend WHERE agent_id = 'kn'"); mk.execute("DELETE FROM spend_month WHERE agent_id = 'kn'")
mk.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('kn', %s, 'NaN')", (today,)); mk.execute("INSERT INTO spend_month (agent_id, month, usd) VALUES ('kn', %s, 'NaN')", (today.replace(day=1),))
st = exc_name(lambda: lim.blocked("kn"))
check("L1 NEGATIVE CONTROL: the REAL Limits.blocked on a NaN total raises InvalidOperation (an unhandled crash, not a stop)", st == "InvalidOperation", str(st))
def blocked_v16(lim_, agent):
    reasons = ["kill_switch"] if lim_.store.get_kill_switch().on else []
    try: day, month = spend_totals_v16(lim_.store, agent, sdk_now().date())
    except ValueError: return reasons + ["bad_amount"]
    budget = lim_.registry.agents[agent].budget_usd
    if day >= budget.daily: reasons.append("daily_budget")
    if month >= budget.monthly: reasons.append("monthly_budget")
    return reasons
check("L2 v16 blocked: the same NaN row gives ['bad_amount'] (the loop maps it to the existing stop card; no crash)", blocked_v16(lim, "kn") == ["bad_amount"], str(blocked_v16(lim, "kn")))
mk.execute("UPDATE spend SET usd = 'Infinity' WHERE agent_id = 'kn'")
check("L3 v16 blocked on an Infinity row gives ['bad_amount']", blocked_v16(lim, "kn") == ["bad_amount"])
mk.execute("UPDATE spend SET usd = 1 WHERE agent_id = 'kn'"); mk.execute("UPDATE spend_month SET usd = 1 WHERE agent_id = 'kn'")
check("L4 v16 blocked on a good row gives []", blocked_v16(lim, "kn") == [])
# the `limits status` read of the same rows
def status_line(store, agent):
    try: d, mo = spend_totals_v16(store, agent, today); return f"ok {d} {mo}"
    except ValueError: return "bad_amount"
mk.execute("UPDATE spend SET usd = 'NaN' WHERE agent_id = 'kn'")
check("L5 `limits status` line for a NaN row prints bad_amount (and `--check` would exit non-zero)", status_line(sk, "kn") == "bad_amount")

# ---------------------------------------------------------------- M. kill-switch log (security major 5), DB-2 v16 file
tmpM, applied = build_multi("exp_m", [("0006_spend_nonneg", "spend_nonneg.sql"), ("0007_spend_decrease_log", "spend_decrease_log.sql")])
check("M0 real migrate() applies the v16 DB-2 file as 0007 on top of the default file (non-superuser migration role)", applied[-1] == "0007_spend_decrease_log", str(applied))
mm_ = connect(dsn("migr_v16", "exp_m")); rm_ = connect(dsn("rtr_v16", "exp_m")); sm_ = PostgresStore(connect(dsn("rtr_v16", "exp_m")))
fo = mm_.execute("SELECT pg_get_userbyid(proowner), prosecdef, proconfig FROM pg_proc WHERE proname = 'kill_switch_log_change'").fetchone()
check("M1 kill_switch_log_change is SECURITY DEFINER, owned by the non-superuser migration role, search_path = pg_catalog, pg_temp", fo[0] == "migr_v16" and fo[1] is True and fo[2] == ["search_path=pg_catalog, pg_temp"], str(fo))
sm_.set_kill_switch(KillSwitch(on=True, by="op:tester"))
sm_.set_kill_switch(KillSwitch(on=True, by="op:tester2"))
sm_.set_kill_switch(KillSwitch(on=False, by="op:tester3"))
rows = mm_.execute("SELECT old_on, new_on, old_by, new_by, who FROM kill_switch_log ORDER BY at").fetchall()
check("M2 REAL store.set_kill_switch: on, on again, off write exactly two rows (the unchanged on->on write is not logged), by the runtime login role", len(rows) == 2 and rows[0][:2] == (False, True) and rows[1][:2] == (True, False) and all(r[4] == "rtr_v16" for r in rows), str(rows))
for stmt in ("SELECT * FROM kill_switch_log", "INSERT INTO kill_switch_log (old_on, new_on) VALUES (false, true)", "UPDATE kill_switch_log SET new_on = false", "DELETE FROM kill_switch_log", "TRUNCATE kill_switch_log"):
    st = sqlstate(lambda: rm_.execute(stmt))
    check(f"M3 NEGATIVE TEST runtime role denied on the kill-switch log: {stmt.split()[0]} -> 42501", st == "InsufficientPrivilege/42501", str(st))
st = sqlstate(lambda: rm_.execute("DELETE FROM kill_switch"))
info(f"M4 INFO runtime role DELETE FROM kill_switch -> {st} (if allowed, a delete-and-reinsert is a state change the update trigger does not see)")
rtm = connect(dsn("rtr_v16", "exp_m"))
temp_ok = sqlstate(lambda: rtm.execute("CREATE TEMP TABLE kill_switch_log (old_on boolean, new_on boolean, old_by text, new_by text, at timestamptz, who text)"))
check("M5 (TEMP still granted in this database) runtime role created a temporary table named like the log", temp_ok is None, str(temp_ok))
sm2 = PostgresStore(rtm)
sm2.set_kill_switch(KillSwitch(on=True, by="op:t4"))
n_real = mm_.execute("SELECT count(*) FROM kill_switch_log").fetchone()[0]; n_tmp = rtm.execute("SELECT count(*) FROM pg_temp.kill_switch_log").fetchone()[0]
check("M6 temporary-table attack on the kill-switch log: the REAL log gets the 3rd row, the temporary table none", n_real == 3 and n_tmp == 0, f"real={n_real} temp={n_tmp}")
v_old = re.search(r"CREATE OR REPLACE FUNCTION kill_switch_log_change\(\).*?END \$f\$;", (HELD / "spend_decrease_log.sql").read_text(), re.S).group(0)
v_bad = v_old.replace("SET search_path = pg_catalog, pg_temp", "SET search_path = pg_catalog, public").replace("EXECUTE format('INSERT INTO %I.kill_switch_log (old_on, new_on, old_by, new_by) VALUES ($1, $2, $3, $4)', TG_TABLE_SCHEMA)\n    USING", "INSERT INTO kill_switch_log (old_on, new_on, old_by, new_by) VALUES (").replace("OLD.\"on\", NEW.\"on\", OLD.\"by\", NEW.\"by\";", "OLD.\"on\", NEW.\"on\", OLD.\"by\", NEW.\"by\");")
mm_.execute(v_bad)
sm2.set_kill_switch(KillSwitch(on=False, by="op:t5"))
check("M7 NEGATIVE CONTROL: with the unsafe function shape (public in the path, bare table name) the same attack DIVERTS the row to the temporary table (real log stays 3, temporary table 1)", mm_.execute("SELECT count(*) FROM kill_switch_log").fetchone()[0] == 3 and rtm.execute("SELECT count(*) FROM pg_temp.kill_switch_log").fetchone()[0] == 1)
mm_.execute(v_old)
sm2.set_kill_switch(KillSwitch(on=True, by="op:t6"))
check("M8 the safe function restored: the REAL log gets the 4th row", mm_.execute("SELECT count(*) FROM kill_switch_log").fetchone()[0] == 4)
with mm_.transaction():
    prob = (lambda pick: (m._apply_grants(mm_, "auditrd_v16", pick), m.effective_problems(mm_, "auditrd_v16", pick))[1])(lambda g: "SELECT" if (g is m.GRANTS["spend_decrease_log"] or g is m.GRANTS["kill_switch_log"]) else "")
arm = connect(dsn("auditrd_v16", "exp_m"))
check("M9 audit reader can read the kill-switch log and effective_problems is empty", arm.execute("SELECT count(*) FROM kill_switch_log").fetchone()[0] == 4 and prob == [], str(prob))

# ---------------------------------------------------------------- N. upgrade path default -> variant (minor 2)
tmpN, applied = build_multi("exp_n", [("0006_spend_nonneg", "spend_nonneg.sql")])
mn = connect(dsn("migr_v16", "exp_n")); rn = connect(dsn("rtr_v16", "exp_n"))
mn.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('nan', %s, 'NaN')", (DAY,))
shutil.copy(HELD / "spend_nonneg_upgrade.sql", tmpN / "0007_spend_nonneg_upgrade.sql")
st = sqlstate(lambda: m.migrate(dsn("migr_v16", "exp_n"), runtime_role="rtr_v16"))
check("N1 the upgrade over a stored NaN row fails (23514) and rolls back: the old rule stays", st == "CheckViolation/23514" and mn.execute("SELECT count(*) FROM schema_migrations WHERE version LIKE '0007%%'").fetchone()[0] == 0 and mn.execute("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = 'spend_usd_ok'").fetchone()[0] == "CHECK ((usd >= (0)::numeric))", str(st))
mn.execute("DELETE FROM spend WHERE agent_id = 'nan'")
applied = m.migrate(dsn("migr_v16", "exp_n"), runtime_role="rtr_v16")
check("N2 after the repair, real migrate() applies the upgrade file as 0007", applied == ["0007_spend_nonneg_upgrade"], str(applied))
defs = [mn.execute("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = %s", (c,)).fetchone()[0] for c in ("spend_usd_ok", "spend_month_usd_ok")]
check("N3 both constraints now carry the Infinity clause, same names, no second constraint", all("Infinity" in d for d in defs) and mn.execute("SELECT count(*) FROM pg_constraint WHERE conname LIKE 'spend%%usd_ok'").fetchone()[0] == 2, str(defs))
check("N4 the runtime role is now refused NaN (23514)", sqlstate(lambda: rn.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('z', %s, 'NaN')", (DAY,))) == "CheckViolation/23514")
check("N5 upgrade file sha256 differs from both other files (own pin, own yes)", len({hashlib_sha(HELD / f) for f in ("spend_nonneg.sql", "spend_nonneg_finite.sql", "spend_nonneg_upgrade.sql")}) == 3) if False else None

# ---------------------------------------------------------------- O. class-level guard over SECURITY DEFINER (security major 6)
ALLOWED = {"spend_log_decrease", "kill_switch_log_change"}
real_sql = sorted(m.MIGRATIONS.glob("*.sql")); held_sql = sorted(HELD.glob("*.sql"))
probs = [p for f in real_sql + held_sql for p in sg.check_sql_text(f.name, f.read_text(), ALLOWED)]
check(f"O1 the guard finds no problem in the {len(real_sql)} real migrations and the {len(held_sql)} held files", probs == [], "; ".join(probs)[:200])
base = (HELD / "spend_decrease_log.sql").read_text()
mutants = {
    "pg_temp not last": base.replace("SET search_path = pg_catalog, pg_temp AS $f$\nBEGIN\n  IF", "SET search_path = pg_temp, pg_catalog AS $f$\nBEGIN\n  IF", 1),
    "public in path": base.replace("SET search_path = pg_catalog, pg_temp AS $f$\nBEGIN\n  IF", "SET search_path = pg_catalog, public, pg_temp AS $f$\nBEGIN\n  IF", 1),
    "no pg_temp": base.replace("SET search_path = pg_catalog, pg_temp AS $f$\nBEGIN\n  IF", "SET search_path = pg_catalog AS $f$\nBEGIN\n  IF", 1),
    "no SET search_path": base.replace("SET search_path = pg_catalog, pg_temp AS $f$\nBEGIN\n  IF", "AS $f$\nBEGIN\n  IF", 1),
    "bare table (no %I)": base.replace("%I.kill_switch_log", "kill_switch_log"),
    "no REVOKE": base.replace("REVOKE ALL ON FUNCTION kill_switch_log_change() FROM PUBLIC;", ""),
    "undeclared SECURITY DEFINER": base + "\nCREATE OR REPLACE FUNCTION sneaky() RETURNS int LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $f$ SELECT 1 $f$;\nREVOKE ALL ON FUNCTION sneaky() FROM PUBLIC;\n",
}
for label, text in mutants.items():
    differs = text != base
    found = sg.check_sql_text("mutant.sql", text, ALLOWED)
    check(f"O2 mutant '{label}' differs from the file and the guard reports it", differs and len(found) >= 1, "; ".join(found)[:120])
check("O3 the held-file head spend_log_decrease search_path text is what the guard read (sanity)", "pg_catalog, pg_temp" in base)

# ---------------------------------------------------------------- P. audit reader role checks (security major 4)
admin.execute("CREATE DATABASE exp_p OWNER migr_v16")
mp = connect(dsn("migr_v16", "exp_p"))
mkrole("reader_v16", "VALID UNTIL 'infinity'")
def reader_problems(db, role):
    """Prototype of DB-2's reader_problems: the reader must not be able to create temporary tables or objects, must not be a
    member of any role, must not be superuser/createrole/createdb/bypassrls/replication, must have an expiry (VALID UNTIL) in the future."""
    p = []
    if db.execute("SELECT has_database_privilege(%s, current_database(), 'TEMP')", (role,)).fetchone()[0]: p.append("can create temporary tables")
    if db.execute("SELECT has_database_privilege(%s, current_database(), 'CREATE')", (role,)).fetchone()[0]: p.append("can create schemas")
    if db.execute("SELECT has_schema_privilege(%s, 'public', 'CREATE')", (role,)).fetchone()[0]: p.append("can create in public")
    if db.execute("SELECT count(*) FROM pg_auth_members am JOIN pg_roles r ON r.oid = am.member WHERE r.rolname = %s", (role,)).fetchone()[0]: p.append("is a member of another role")
    f = db.execute("SELECT rolsuper OR rolcreaterole OR rolcreatedb OR rolbypassrls OR rolreplication, rolvaliduntil FROM pg_roles WHERE rolname = %s", (role,)).fetchone()
    if f[0]: p.append("has a powerful role flag")
    if f[1] is None: p.append("has no VALID UNTIL")
    return p
pr = reader_problems(mp, "reader_v16")
check("P1 NEGATIVE TEST BEFORE the REVOKE: on a fresh database the reader CAN create temporary tables (PUBLIC has TEMP) and reader_problems reports exactly that", "can create temporary tables" in pr, str(pr))
admin.execute("REVOKE TEMPORARY ON DATABASE exp_p FROM PUBLIC")
pr = reader_problems(mp, "reader_v16")
check("P2 after REVOKE TEMPORARY ... FROM PUBLIC (operator step, question L19) reader_problems is empty", pr == [], str(pr))
rr = connect(dsn("reader_v16", "exp_p"))
check("P3 the reader is refused CREATE TEMP TABLE (42501)", sqlstate(lambda: rr.execute("CREATE TEMP TABLE x (a int)")) == "InsufficientPrivilege/42501")
admin.execute("GRANT rtr_v16 TO reader_v16")
check("P4 NEGATIVE: a reader that is a member of the runtime role is reported", "is a member of another role" in reader_problems(mp, "reader_v16"))
admin.execute("REVOKE rtr_v16 FROM reader_v16")
mkrole("expired_v16", "VALID UNTIL '2020-01-01'")
st = login_state("expired_v16", PW["expired_v16"])
check("P5 a role whose VALID UNTIL is in the past cannot log in (28P01)", st.startswith("28P01"), st)
mkrole("nolimit_v16")
check("P6 NEGATIVE: a reader role created without VALID UNTIL is reported ('has no VALID UNTIL')", "has no VALID UNTIL" in reader_problems(mp, "nolimit_v16"))
admin.execute("ALTER ROLE reader_v16 NOLOGIN")
check("P7 revoking by NOLOGIN stops new logins (SQLSTATE 28000 or 28P01)", login_state("reader_v16", PW["reader_v16"])[:5] in ("28000", "28P01"), login_state("reader_v16", PW["reader_v16"]))

m._migration_files = real_files
for t in (tmpA, tmpB, tmpC, tmpD, tmpK, tmpM, tmpN): shutil.rmtree(t, ignore_errors=True)
info(f"{sum(results)} of {len(results)} checks passed")
sys.exit(0 if all(results) else 1)
