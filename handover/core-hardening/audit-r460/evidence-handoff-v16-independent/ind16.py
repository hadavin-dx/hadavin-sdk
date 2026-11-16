"""Independent v16 Postgres checks (EVIDENCE RUNNER: records, never judges). Written without reading pg_v16.py's checks.
Usage: ind16.py <socket_dir> <src_dir> <held_dir> <scratch_dir> <main|mut>   (HV_ADMIN_PW in env). Made-up data only."""
import sys, os, time, shutil, tempfile, secrets, re
from pathlib import Path
from datetime import date
from decimal import Decimal

sock, src, held, scr, mode = sys.argv[1:6]
sys.path.insert(0, src)
import psycopg
from psycopg import sql
import hadavin_sdk.store.migrate as m
HELD = Path(held)
SCR = Path(scr)
DAY, MONTH = date(2026, 11, 16), date(2026, 11, 1)
PW = {"postgres": os.environ["HV_ADMIN_PW"]}
QUIET = False
R = []


def check(name, ok, detail=""):
    R.append((name, bool(ok), detail))
    if not QUIET:
        print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""), flush=True)


def info(msg):
    if not QUIET:
        print("INFO " + msg, flush=True)


def dsn(user, db, stmt_ms=30000):
    return f"host={sock} dbname={db} user={user} password={PW[user]} options='-c statement_timeout={stmt_ms}'"


def conn(user, db, stmt_ms=30000):
    return psycopg.connect(dsn(user, db, stmt_ms), autocommit=True)


def st(fn):
    try:
        fn()
        return None
    except psycopg.Error as e:
        return f"{type(e).__name__}/{e.sqlstate}"


admin = psycopg.connect(dsn("postgres", "postgres"), autocommit=True)
for r in ("mig", "rt", "ar", "portal"):
    PW[r] = secrets.token_hex(16)
    admin.execute(sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(sql.Identifier(r), sql.Literal(PW[r])))


def build(db, files):
    """Fresh database owned by the non-superuser role mig; real migrations 0001-0005 then each (path, stem) in files via the REAL migrate()."""
    admin.execute(f"DROP DATABASE IF EXISTS {db} WITH (FORCE)")
    admin.execute(f"CREATE DATABASE {db} OWNER mig")
    tmp = Path(tempfile.mkdtemp(prefix="ind16_", dir=SCR))
    for p in m.MIGRATIONS.glob("*.sql"):
        shutil.copy(p, tmp / p.name)
    for p, stem in files:
        shutil.copy(p, tmp / f"{stem}.sql")
    return apply_dir(db, tmp)


def apply_dir(db, tmp, stmt_ms=30000):
    m._migration_files = lambda folder=tmp: sorted(Path(folder).glob("*.sql"))
    text = "".join(p.read_text() for p in Path(tmp).glob("*.sql"))
    added = []
    for t in ("spend_decrease_log", "kill_switch_log"):
        if re.search(rf"CREATE TABLE {t}\b", text):
            m.GRANTS[t] = m.Grant("table", "")  # the lead's move PR adds these entries (document 5.6 b); empty runtime list
            added.append(t)
    try:
        return m.migrate(dsn("mig", db, stmt_ms), runtime_role="rt")
    finally:
        for t in added:
            m.GRANTS.pop(t, None)


def defs(db):
    c = conn("mig", db)
    return dict(c.execute("SELECT conrelid::regclass::text||'.'||conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conname IN ('spend_usd_ok','spend_month_usd_ok')").fetchall())


VALS = ["-0.01", "-Infinity", "NaN", "Infinity", "0", "-0", "0.00", "99999999999999999999.99"]


def suite_db1(kind, db, files, upgrade_fail=True):
    """kind: default | finite | upgrade. files: [(path, stem)...] applied in order as 0006, 0007."""
    build(db, files)
    refuse = {"-0.01", "-Infinity"} | ({"NaN", "Infinity"} if kind != "default" else set())
    d = defs(db)
    want_fin = "CHECK (((usd >= (0)::numeric) AND (usd < 'Infinity'::numeric)))"
    want_def = "CHECK ((usd >= (0)::numeric))"
    want = want_def if kind == "default" else want_fin
    check(f"DB1[{kind}] constraint text on both tables", d == {"spend.spend_usd_ok": want, "spend_month.spend_month_usd_ok": want}, str(d))
    rt = conn("rt", db)
    for tbl, key, k in (("spend", "day", DAY), ("spend_month", "month", MONTH)):
        for i, v in enumerate(VALS):
            a = f"i{i}"
            e = st(lambda: rt.execute(f"INSERT INTO {tbl} (agent_id,{key},usd) VALUES (%s,%s,%s)", (a, k, Decimal(v))))
            exp = "CheckViolation/23514" if v in refuse else None
            check(f"DB1[{kind}] INSERT {v} into {tbl} -> {exp or 'accepted'}", e == exp, str(e))
            rt.execute(f"INSERT INTO {tbl} (agent_id,{key},usd) VALUES (%s,%s,1) ON CONFLICT DO NOTHING", (f"u{i}", k))
            e = st(lambda: rt.execute(f"UPDATE {tbl} SET usd=%s WHERE agent_id=%s", (Decimal(v), f"u{i}")))
            check(f"DB1[{kind}] UPDATE to {v} on {tbl} -> {exp or 'accepted'}", e == exp, str(e))
        rt.execute(f"INSERT INTO {tbl} (agent_id,{key},usd) VALUES ('oc',%s,5) ON CONFLICT DO NOTHING", (k,))
        e = st(lambda: rt.execute(f"INSERT INTO {tbl} (agent_id,{key},usd) VALUES ('oc',%s,-3) ON CONFLICT (agent_id,{key}) DO UPDATE SET usd={tbl}.usd+EXCLUDED.usd", (k,)))
        check(f"DB1[{kind}] ON CONFLICT with a negative delta on {tbl} -> 23514 (the INSERT row is tested first)", e == "CheckViolation/23514", str(e))
        e = st(lambda: rt.execute(f"UPDATE {tbl} SET usd=usd-3 WHERE agent_id='oc'"))
        check(f"DB1[{kind}] plain UPDATE give-back of 3 from 5 on {tbl} works", e is None and rt.execute(f"SELECT usd FROM {tbl} WHERE agent_id='oc'").fetchone()[0] == 2, str(e))
        e = st(lambda: rt.execute(f"UPDATE {tbl} SET usd=usd-3 WHERE agent_id='oc'"))
        check(f"DB1[{kind}] give-back below zero on {tbl} -> 23514", e == "CheckViolation/23514", str(e))
    if kind == "finite":
        try:
            build(db + "b", [(HELD / "spend_nonneg.sql", "0006_a"), (HELD / "spend_nonneg_finite.sql", "0007_b")])
            e = None
        except Exception as ex:
            e = f"{type(ex).__name__}/{getattr(ex, 'sqlstate', None) or getattr(getattr(ex, '__cause__', None), 'sqlstate', None)}"
        check("DB1[finite] applying default AND variant together fails (same constraint names), 42710", e is not None and e.endswith("/42710"), str(e))
    if kind == "upgrade" and upgrade_fail:
        files_default = [files[0]]
        build(db + "f", files_default)
        c = conn("rt", db + "f")
        c.execute("INSERT INTO spend (agent_id,day,usd) VALUES ('nan',%s,'NaN')", (DAY,))
        tmp = Path(tempfile.mkdtemp(prefix="ind16_", dir=SCR))
        for p in m.MIGRATIONS.glob("*.sql"):
            shutil.copy(p, tmp / p.name)
        shutil.copy(files[0][0], tmp / f"{files[0][1]}.sql")
        shutil.copy(files[1][0], tmp / f"{files[1][1]}.sql")
        try:
            apply_dir(db + "f", tmp)
            e = None
        except Exception as ex:
            e = f"{type(ex).__name__}/{getattr(ex, 'sqlstate', None)}"
        d2 = defs(db + "f")
        led = [r[0] for r in conn("mig", db + "f").execute("SELECT version FROM schema_migrations ORDER BY 1").fetchall()]
        check("DB1[upgrade] with a NaN row the upgrade fails 23514, old rule stays on both tables, ledger lacks 0007", e is not None and e.endswith("/23514") and d2 == {"spend.spend_usd_ok": want_def, "spend_month.spend_month_usd_ok": want_def} and "0007_up" not in led, f"{e} {d2} {led[-1]}")


def lock_test(label, before, target, stem, expect_timeout_s=5.0):
    """Hold ROW EXCLUSIVE on spend in another session; run the real migrate with `target` as the next file. Record sqlstate, elapsed, rollback."""
    db = "lk_" + label
    build(db, before)
    holder = psycopg.connect(dsn("rt", db, 120000))
    holder.execute("LOCK TABLE spend IN ROW EXCLUSIVE MODE")
    tmp = Path(tempfile.mkdtemp(prefix="ind16_", dir=SCR))
    for p in m.MIGRATIONS.glob("*.sql"):
        shutil.copy(p, tmp / p.name)
    for p, s in before:
        shutil.copy(p, tmp / f"{s}.sql")
    shutil.copy(target, tmp / f"{stem}.sql")
    t0 = time.time()
    err = None
    try:
        apply_dir(db, tmp, stmt_ms=14000)
    except Exception as ex:
        err = ex
    el = time.time() - t0
    holder.rollback()
    holder.close()
    state = getattr(err, "sqlstate", None)
    led = [r[0] for r in conn("mig", db).execute("SELECT version FROM schema_migrations").fetchall()]
    ok = state == "55P03" and 4.0 < el < 9.0 and stem not in led
    check(f"LOCK[{label}] with a writer holding spend, the file fails 55P03 in about 5 s and rolls back", ok, f"{type(err).__name__ if err else None}/{state} after {el:.1f}s, ledger has {stem}: {stem in led}")
    return ok


def suite_db2(db, files, full=True, nan=True):
    build(db, files)
    mig = conn("mig", db)
    mig.execute("GRANT SELECT ON spend_decrease_log, kill_switch_log TO ar")
    mig.execute("INSERT INTO spend (agent_id,day,usd) VALUES ('a',%s,10),('b',%s,10)", (DAY, DAY))
    mig.execute("INSERT INTO spend_month (agent_id,month,usd) VALUES ('a',%s,10),('b',%s,10)", (MONTH, MONTH))
    rt = conn("rt", db)
    ar = conn("ar", db)
    log = lambda: mig.execute("SELECT agent_id,period,scope,old_usd,new_usd,who,at FROM spend_decrease_log ORDER BY at, scope").fetchall()
    n = lambda t: mig.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
    # functions
    rows = {r[0]: r[1:] for r in mig.execute("SELECT proname, prosecdef, pg_get_userbyid(proowner), proconfig, has_function_privilege('rt', oid, 'EXECUTE'), (SELECT count(*) FROM aclexplode(coalesce(proacl, acldefault('f', proowner))) a WHERE a.grantee=0) FROM pg_proc WHERE proname IN ('spend_log_decrease','kill_switch_log_change','spend_keep_keys','audit_log_append_only') AND pronamespace='public'::regnamespace").fetchall()}
    for f in ("spend_log_decrease", "kill_switch_log_change"):
        r = rows.get(f)
        check(f"F[{f}] SECURITY DEFINER, owned by the non-superuser migration role, search_path = pg_catalog, pg_temp (pg_temp last), PUBLIC has no EXECUTE, runtime role has no EXECUTE",
              r is not None and r[0] is True and r[1] == "mig" and r[2] == ["search_path=pg_catalog, pg_temp"] and r[3] is False and r[4] == 0, str(r))
        e = st(lambda: rt.execute(f"SELECT {f}()"))
        check(f"F[{f}] the runtime role calling it directly is refused 42501", e == "InsufficientPrivilege/42501", str(e))
    for f in ("spend_keep_keys", "audit_log_append_only"):
        r = rows.get(f)
        check(f"F[{f}] not SECURITY DEFINER and search_path = pg_catalog, pg_temp", r is not None and r[0] is False and r[2] == ["search_path=pg_catalog, pg_temp"], str(r))
    ix = {r[0] for r in mig.execute("SELECT indexname FROM pg_indexes WHERE schemaname='public'").fetchall()}
    check("F[index] spend_decrease_log_by_agent and kill_switch_log_by_time exist", {"spend_decrease_log_by_agent", "kill_switch_log_by_time"} <= ix, str(sorted(i for i in ix if 'log' in i)))
    # decrease log behaviour
    base = n("spend_decrease_log")
    rt.execute("UPDATE spend SET usd = usd - 3 WHERE agent_id='a'")
    L = log()
    check("L1 a lowering of spend by the runtime role writes one row with the right agent, day, scope, old, new, login role, and a current time",
          len(L) == base + 1 and L[-1][:6] == ("a", DAY, "spend", Decimal(10), Decimal(7), "rt") and abs((time.time() - L[-1][6].timestamp())) < 120, str(L[-1:]))
    rt.execute("UPDATE spend_month SET usd = usd - 4 WHERE agent_id='a'")
    L = log()
    check("L2 a lowering of spend_month writes scope spend_month and period = first of month", len(L) == base + 2 and L[-1][:6] == ("a", MONTH, "spend_month", Decimal(10), Decimal(6), "rt"), str(L[-1:]))
    rt.execute("UPDATE spend SET usd = usd + 1 WHERE agent_id='a'")
    rt.execute("UPDATE spend SET usd = usd WHERE agent_id='a'")
    rt.execute("UPDATE spend_month SET usd = usd + 1 WHERE agent_id='a'")
    check("L3 a raise and a same-value update write no row", n("spend_decrease_log") == base + 2, str(n("spend_decrease_log")))
    b = n("spend_decrease_log")
    if nan:
        rt.execute("UPDATE spend SET usd = 'NaN' WHERE agent_id='b'")
        rt.execute("UPDATE spend_month SET usd = 'Infinity' WHERE agent_id='b'")
        check("L4 a total that becomes NaN (spend) or Infinity (spend_month) is logged", n("spend_decrease_log") == b + 2, str(n("spend_decrease_log") - b))
        b = n("spend_decrease_log")
        rt.execute("UPDATE spend SET usd = 'NaN' WHERE agent_id='b'")
        check("L5 NaN to NaN is not logged", n("spend_decrease_log") == b)
        rt.execute("UPDATE spend SET usd = 'Infinity' WHERE agent_id='b'")
        b = n("spend_decrease_log")
        rt.execute("UPDATE spend SET usd = 7 WHERE agent_id='b'")
        rt.execute("UPDATE spend_month SET usd = 7 WHERE agent_id='b'")
        check("L6 lowering from NaN/Infinity to a finite number is logged", n("spend_decrease_log") == b + 2, str(n("spend_decrease_log") - b))
    # kill switch
    kb = n("kill_switch_log")
    rt.execute("""UPDATE kill_switch SET "on"=true, "by"='opx' WHERE id=1""")
    K = mig.execute("SELECT old_on,new_on,old_by,new_by,who FROM kill_switch_log ORDER BY at").fetchall()
    check("K1 turning the kill switch on writes one row (old_on f, new_on t, old_by NULL, new_by opx, who rt)", len(K) == kb + 1 and K[-1] == (False, True, None, "opx", "rt"), str(K[-1:]))
    rt.execute("""UPDATE kill_switch SET "by"='other' WHERE id=1""")
    check("K2 a change of only the `by` column writes no row", n("kill_switch_log") == kb + 1)
    rt.execute("""UPDATE kill_switch SET "on"=false WHERE id=1""")
    K = mig.execute("SELECT old_on,new_on,old_by,new_by,who FROM kill_switch_log ORDER BY at").fetchall()
    check("K3 turning it off writes a row (old_on t, new_on f, old_by other)", len(K) == kb + 2 and K[-1][:3] == (True, False, "other"), str(K[-1:]))
    # privileges
    for t in ("spend_decrease_log", "kill_switch_log"):
        for who_, c in (("rt", rt), ("portal", conn("portal", db))):
            res = {}
            for stmt in (f"SELECT * FROM {t}", f"INSERT INTO {t} SELECT * FROM {t}", f"UPDATE {t} SET who='x'", f"DELETE FROM {t}", f"TRUNCATE {t}"):
                res[stmt.split()[0]] = st(lambda: c.execute(stmt))
            check(f"P[{who_}/{t}] SELECT, INSERT, UPDATE, DELETE, TRUNCATE all refused 42501", all(v == "InsufficientPrivilege/42501" for v in res.values()), str(res))
        res = {}
        for stmt in (f"INSERT INTO {t} SELECT * FROM {t}", f"UPDATE {t} SET who='x'", f"DELETE FROM {t}", f"TRUNCATE {t}"):
            res[stmt.split()[0]] = st(lambda: ar.execute(stmt))
        check(f"P[audit-reader/{t}] SELECT works; INSERT, UPDATE, DELETE, TRUNCATE refused 42501", st(lambda: ar.execute(f"SELECT count(*) FROM {t}")) is None and all(v == "InsufficientPrivilege/42501" for v in res.values()), str(res))
    check("P[audit-reader] cannot write the spend tables or the kill switch", all(st(lambda: ar.execute(x)) == "InsufficientPrivilege/42501" for x in ("UPDATE spend SET usd=0", "UPDATE kill_switch SET \"on\"=false", "INSERT INTO spend VALUES ('z',now(),1)")))
    # temp-table attack
    b1, b2 = n("spend_decrease_log"), n("kill_switch_log")
    rt.execute("CREATE TEMP TABLE spend_decrease_log (agent_id text, period date, scope text, old_usd numeric, new_usd numeric, at timestamptz DEFAULT now(), who text DEFAULT 'attacker')")
    rt.execute("CREATE TEMP TABLE kill_switch_log (at timestamptz DEFAULT now(), old_on boolean, new_on boolean, old_by text, new_by text, who text DEFAULT 'attacker')")
    rt.execute("SET search_path = pg_temp, pg_catalog, public")
    rt.execute("UPDATE spend SET usd = usd - 1 WHERE agent_id='a'")
    rt.execute("UPDATE spend_month SET usd = usd - 1 WHERE agent_id='a'")
    rt.execute("""UPDATE kill_switch SET "on"=true WHERE id=1""")
    tt = (rt.execute("SELECT count(*) FROM pg_temp.spend_decrease_log").fetchone()[0], rt.execute("SELECT count(*) FROM pg_temp.kill_switch_log").fetchone()[0])
    check("T1 temp-table attack with search_path pg_temp first: real logs gain 2 and 1 rows, the temporary tables stay empty", (n("spend_decrease_log") - b1, n("kill_switch_log") - b2) == (2, 1) and tt == (0, 0), f"{n('spend_decrease_log') - b1},{n('kill_switch_log') - b2} temp {tt}")
    rt.execute("""UPDATE kill_switch SET "on"=false WHERE id=1""")
    rt.execute("CREATE FUNCTION pg_temp.clock_timestamp() RETURNS timestamptz LANGUAGE sql AS $$ SELECT '2000-01-01'::timestamptz $$")
    rt.execute("CREATE FUNCTION pg_temp.session_user() RETURNS text LANGUAGE sql AS $$ SELECT 'forged' $$") if False else None
    rt.execute("UPDATE spend SET usd = usd - 1 WHERE agent_id='a'")
    last = log()[-1]
    check("T2 a temporary function named clock_timestamp does not change `at`, and `who` is still the login role", abs(time.time() - last[6].timestamp()) < 120 and last[5] == "rt", str(last[5:]))
    rt.execute("RESET search_path")
    e1 = st(lambda: rt.execute("CREATE SCHEMA evil"))
    e2 = st(lambda: rt.execute("CREATE TABLE public.spend_decrease_log (x int)"))
    e3 = st(lambda: rt.execute("SET ROLE mig"))
    check("T3 the runtime role cannot create a schema or a public table of the log's name or SET ROLE to the owner", (e1, e2, e3) == ("InsufficientPrivilege/42501",) * 3, str((e1, e2, e3)))
    # key guard
    e = {}
    e["spend.agent"] = st(lambda: rt.execute("UPDATE spend SET agent_id='zz' WHERE agent_id='a'"))
    e["spend.day"] = st(lambda: rt.execute("UPDATE spend SET day = day - 3650 WHERE agent_id='a'"))
    e["month.agent"] = st(lambda: rt.execute("UPDATE spend_month SET agent_id='zz' WHERE agent_id='a'"))
    e["month.month"] = st(lambda: rt.execute("UPDATE spend_month SET month = month - interval '1 year' WHERE agent_id='a'"))
    check("G1 key columns cannot change on either table (all 4 refused, SQLSTATE 42501 from the trigger)", all(v == "InsufficientPrivilege/42501" for v in e.values()), str(e))
    try:
        rt.execute("UPDATE spend SET day = day - 1 WHERE agent_id='a'")
        msg = ""
    except psycopg.Error as ex:
        msg = str(ex)
    check("G2 the refusal text is the trigger's own ('spend key columns may not change')", "spend key columns may not change" in msg, msg[:80])
    check("G3 a usd-only update still works", st(lambda: rt.execute("UPDATE spend SET usd = usd + 0.5 WHERE agent_id='a'")) is None)
    # append-only, owner and superuser
    sup = conn("postgres", db)
    res = {}
    for t in ("spend_decrease_log", "kill_switch_log"):
        for who_, c in (("owner", mig), ("superuser", sup)):
            for stmt in (f"UPDATE {t} SET who='x'", f"DELETE FROM {t}", f"TRUNCATE {t}"):
                res[f"{who_}/{t}/{stmt.split()[0]}"] = st(lambda: c.execute(stmt))
    bad = {k: v for k, v in res.items() if v != "InsufficientPrivilege/42501"}
    check("AO1 UPDATE, DELETE and TRUNCATE on both records are refused 42501 even for the owner and a superuser", not bad, str(bad))
    try:
        mig.execute("DELETE FROM spend_decrease_log")
    except psycopg.Error as ex:
        check("AO2 the refusal says append-only", "append-only" in str(ex), str(ex)[:60])
    check("AO3 the owner can still INSERT (positive control)", st(lambda: mig.execute("INSERT INTO spend_decrease_log (agent_id,period,scope,old_usd,new_usd) VALUES ('c',%s,'spend',2,1)", (DAY,))) is None)
    # fail closed
    mig.execute("ALTER TABLE spend_decrease_log RENAME TO sdl_x")
    before = rt.execute("SELECT usd FROM spend WHERE agent_id='b'").fetchone()[0]
    e = st(lambda: rt.execute("UPDATE spend SET usd = usd - 1 WHERE agent_id='b'"))
    after = rt.execute("SELECT usd FROM spend WHERE agent_id='b'").fetchone()[0]
    mig.execute("ALTER TABLE sdl_x RENAME TO spend_decrease_log")
    check("FC1 fail closed: when the log cannot be written the lowering fails and the total is unchanged", e is not None and before == after, f"{e} {before}->{after}")
    if full:
        info("owner can DISABLE a trigger: " + str(st(lambda: mig.execute("ALTER TABLE spend_decrease_log DISABLE TRIGGER spend_decrease_log_append_only"))) + " (None = allowed; expected, documented)")
        mig.execute("ALTER TABLE spend_decrease_log ENABLE TRIGGER spend_decrease_log_append_only")
        info("superuser with session_replication_role=replica bypasses: " + str(st(lambda: (sup.execute("SET session_replication_role=replica"), sup.execute("DELETE FROM kill_switch_log WHERE false")))))


def main_run():
    # cluster hardening
    ph = admin.execute("SELECT count(*) FROM pg_hba_file_rules WHERE auth_method='trust'").fetchone()[0]
    sc = admin.execute("SELECT count(*) FROM pg_authid WHERE rolname IN ('mig','rt','ar','portal','postgres') AND rolpassword LIKE 'SCRAM-SHA-256$%'").fetchone()[0]
    sp = admin.execute("SELECT rolname FROM pg_roles WHERE rolsuper AND rolname IN ('mig','rt','ar','portal')").fetchall()
    check("C1 cluster: no trust rule, 5 of 5 role secrets are SCRAM-SHA-256, mig/rt/ar/portal are not superusers", ph == 0 and sc == 5 and not sp, f"trust={ph} scram={sc} super={sp}")
    bad = st(lambda: psycopg.connect(f"host={sock} dbname=postgres user=mig password=wrongpass{secrets.token_hex(4)}"))
    check("C2 a wrong password is refused (password authentication failed)", bad is not None, str(bad))
    # DB-1
    d, f, u, dl = HELD / "spend_nonneg.sql", HELD / "spend_nonneg_finite.sql", HELD / "spend_nonneg_upgrade.sql", HELD / "spend_decrease_log.sql"
    suite_db1("default", "i_def", [(d, "0006_def")])
    suite_db1("finite", "i_fin", [(f, "0006_fin")])
    suite_db1("upgrade", "i_up", [(d, "0006_def"), (u, "0007_up")])
    # DB-2 alone, with default, with variant
    suite_db2("i_d2alone", [(dl, "0006_log")])
    suite_db2("i_d2def", [(d, "0006_def"), (dl, "0007_log")], full=False)
    suite_db2("i_d2fin", [(f, "0006_fin"), (dl, "0007_log")], full=False, nan=False)
    # DB-2 alone: negative and -Infinity values (no DB-1 check present)
    c = conn("rt", "i_d2alone")
    b = conn("mig", "i_d2alone").execute("SELECT count(*) FROM spend_decrease_log").fetchone()[0]
    c.execute("INSERT INTO spend (agent_id,day,usd) VALUES ('neg',%s,2)", (DAY,))
    c.execute("UPDATE spend SET usd=-5 WHERE agent_id='neg'")
    c.execute("UPDATE spend SET usd='-Infinity' WHERE agent_id='neg'")
    a = conn("mig", "i_d2alone").execute("SELECT count(*) FROM spend_decrease_log").fetchone()[0]
    check("L7 DB-2 alone: lowering to -5 then to -Infinity logs two rows", a - b == 2, str(a - b))
    # lock timeouts
    lock_test("default", [], d, "0006_def")
    lock_test("finite", [], f, "0006_fin")
    lock_test("upgrade", [(d, "0006_def")], u, "0007_up")
    lock_test("decreaselog", [], dl, "0006_log")
    # idempotent re-run
    tmp = Path(tempfile.mkdtemp(prefix="ind16_", dir=SCR))
    for p in m.MIGRATIONS.glob("*.sql"):
        shutil.copy(p, tmp / p.name)
    shutil.copy(d, tmp / "0006_def.sql")
    shutil.copy(dl, tmp / "0007_log.sql")
    again = apply_dir("i_d2def", tmp)
    check("R1 running migrate again on the migrated database applies nothing", again == [], str(again))
    ok = sum(1 for r in R if r[1])
    print(f"INFO {ok} of {len(R)} checks passed")
    for name, good, det in R:
        if not good:
            print("FAILED: " + name + "  [" + det + "]")


# ---------------------------------------------------------------- mutations
def sub(old, new, count=1):
    def f(t):
        if t.count(old) != count:
            raise ValueError(f"anchor count {t.count(old)} != {count}: {old[:50]!r}")
        return t.replace(old, new)
    return f


def rx(pattern, new, flags=re.S):
    def f(t):
        t2, k = re.subn(pattern, new, t, count=1, flags=flags)
        if k != 1:
            raise ValueError("regex anchor missing")
        return t2
    return f


def sp_first(fname):
    return rx(rf"(FUNCTION {fname}\(\) RETURNS trigger LANGUAGE plpgsql[^$]*?SET search_path = )pg_catalog, pg_temp", r"\1pg_temp, pg_catalog")


def chain(*fs):
    def f(t):
        for g in fs:
            t = g(t)
        return t
    return f


SD = "SECURITY DEFINER"
MUT = [
    ("M01", "DB2: spend_log_decrease loses SECURITY DEFINER", "dl", sub("spend_log_decrease() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER", "spend_log_decrease() RETURNS trigger LANGUAGE plpgsql")),
    ("M02", "DB2: kill_switch_log_change loses SECURITY DEFINER", "dl", sub("kill_switch_log_change() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER", "kill_switch_log_change() RETURNS trigger LANGUAGE plpgsql")),
    ("M03", "DB2: spend_log_decrease search_path puts pg_temp first", "dl", sp_first("spend_log_decrease")),
    ("M04", "DB2: v13 shape (no schema qualification + pg_temp first) in spend_log_decrease", "dl", chain(sp_first("spend_log_decrease"), sub("%I.spend_decrease_log (agent_id, period, scope, old_usd, new_usd) VALUES ($1, $2, $3, $4, $5)', TG_TABLE_SCHEMA)", "spend_decrease_log (agent_id, period, scope, old_usd, new_usd) VALUES ($1, $2, $3, $4, $5)')", 2))),
    ("M05", "DB2: REVOKE on spend_log_decrease removed", "dl", sub("REVOKE ALL ON FUNCTION spend_log_decrease() FROM PUBLIC;", "")),
    ("M06", "DB2: REVOKE on kill_switch_log_change removed", "dl", sub("REVOKE ALL ON FUNCTION kill_switch_log_change() FROM PUBLIC;", "")),
    ("M07", "DB2: kill switch trigger fires on every update", "dl", sub('WHEN (NEW."on" IS DISTINCT FROM OLD."on")', "WHEN (TRUE)")),
    ("M08", "DB2: kill switch trigger condition inverted", "dl", sub('WHEN (NEW."on" IS DISTINCT FROM OLD."on")', 'WHEN (NEW."on" IS NOT DISTINCT FROM OLD."on")')),
    ("M09", "DB2: logs raises instead of lowerings", "dl", sub("NEW.usd < OLD.usd OR", "NEW.usd > OLD.usd OR", 2)),
    ("M10", "DB2: NaN/Infinity transitions not logged (both triggers)", "dl", sub(" OR NEW.usd >= 'Infinity'::numeric", "", 2)),
    ("M11", "DB2: spend_month decrease trigger removed", "dl", rx(r"CREATE TRIGGER spend_month_log_decrease AFTER UPDATE.*?EXECUTE FUNCTION spend_log_decrease\(\);", "")),
    ("M12", "DB2: spend decrease trigger removed", "dl", rx(r"CREATE TRIGGER spend_log_decrease AFTER UPDATE.*?EXECUTE FUNCTION spend_log_decrease\(\);", "")),
    ("M13", "DB2: key guard trigger on spend removed", "dl", sub("CREATE TRIGGER spend_keep_keys BEFORE UPDATE ON spend FOR EACH ROW EXECUTE FUNCTION spend_keep_keys();", "")),
    ("M14", "DB2: key guard trigger on spend_month removed", "dl", sub("CREATE TRIGGER spend_month_keep_keys BEFORE UPDATE ON spend_month FOR EACH ROW EXECUTE FUNCTION spend_keep_keys();", "")),
    ("M15", "DB2: key guard ignores day", "dl", sub(" OR NEW.day IS DISTINCT FROM OLD.day", "")),
    ("M16", "DB2: key guard ignores month", "dl", sub(" OR NEW.month IS DISTINCT FROM OLD.month", "")),
    ("M17", "DB2: key guard ignores agent_id in the spend branch", "dl", sub("IF NEW.agent_id IS DISTINCT FROM OLD.agent_id OR NEW.day IS DISTINCT FROM OLD.day THEN", "IF NEW.day IS DISTINCT FROM OLD.day THEN")),
    ("M18", "DB2: key guard error code changed", "dl", sub("'spend key columns may not change' USING ERRCODE = '42501'", "'spend key columns may not change' USING ERRCODE = '22000'", 2)),
    ("M19", "DB2: spend_decrease_log append-only drops UPDATE", "dl", sub("BEFORE UPDATE OR DELETE ON spend_decrease_log", "BEFORE DELETE ON spend_decrease_log")),
    ("M20", "DB2: kill_switch_log append-only drops DELETE", "dl", sub("BEFORE UPDATE OR DELETE ON kill_switch_log", "BEFORE UPDATE ON kill_switch_log")),
    ("M21", "DB2: spend_decrease_log truncate trigger removed", "dl", rx(r"CREATE TRIGGER spend_decrease_log_no_truncate.*?audit_log_append_only\(\);", "")),
    ("M22", "DB2: kill_switch_log truncate trigger removed", "dl", rx(r"CREATE TRIGGER kill_switch_log_no_truncate.*?audit_log_append_only\(\);", "")),
    ("M23", "DB2: append-only error code changed", "dl", sub("USING ERRCODE = '42501';\nEND $f$;\nCREATE TRIGGER spend_decrease_log_append_only", "USING ERRCODE = '22000';\nEND $f$;\nCREATE TRIGGER spend_decrease_log_append_only")),
    ("M24", "DB2: who defaults to current_user (the definer) not session_user", "dl", sub("who      text NOT NULL DEFAULT session_user", "who      text NOT NULL DEFAULT current_user")),
    ("M25", "DB2: old and new swapped in the decrease row", "dl", sub("OLD.day, TG_TABLE_NAME, OLD.usd, NEW.usd", "OLD.day, TG_TABLE_NAME, NEW.usd, OLD.usd")),
    ("M26", "DB2: scope hard-coded 'spend' for month rows", "dl", sub("OLD.month, TG_TABLE_NAME, OLD.usd, NEW.usd", "OLD.month, 'spend', OLD.usd, NEW.usd")),
    ("M27", "DB2: kill-switch row has old_on/new_on swapped", "dl", sub('USING OLD."on", NEW."on", OLD."by", NEW."by"', 'USING NEW."on", OLD."on", OLD."by", NEW."by"')),
    ("M28", "DB2: `at` defaults to a constant time", "dl", sub("at       timestamptz NOT NULL DEFAULT clock_timestamp()", "at       timestamptz NOT NULL DEFAULT '2000-01-01'")),
    ("M29", "DB2: index on spend_decrease_log removed", "dl", sub("CREATE INDEX spend_decrease_log_by_agent ON spend_decrease_log (agent_id, period, at);", "")),
    ("M30", "DB2: index on kill_switch_log removed", "dl", sub("CREATE INDEX kill_switch_log_by_time ON kill_switch_log (at);", "")),
    ("M31", "DB2: audit_log_append_only loses its search_path", "dl", rx(r"(FUNCTION audit_log_append_only\(\) RETURNS trigger LANGUAGE plpgsql\n)SET search_path = pg_catalog, pg_temp AS", r"\1AS")),
    ("M32", "DB2: spend_keep_keys loses its search_path", "dl", rx(r"(FUNCTION spend_keep_keys\(\) RETURNS trigger LANGUAGE plpgsql\n)SET search_path = pg_catalog, pg_temp AS", r"\1AS")),
    ("M33", "DB2: kill_switch_log_change search_path pg_temp first", "dl", sp_first("kill_switch_log_change")),
    ("M34", "DB2: append-only message changed", "dl", sub("'% is append-only'", "'% is read only'")),
    ("M35", "DB2: kill-switch row copies old_by into new_by", "dl", sub('OLD."by", NEW."by"', 'OLD."by", OLD."by"')),
    ("M36", "DB2: kill_switch_log truncate removed AND delete removed", "dl", chain(rx(r"CREATE TRIGGER kill_switch_log_no_truncate.*?audit_log_append_only\(\);", ""), sub("BEFORE UPDATE OR DELETE ON kill_switch_log", "BEFORE UPDATE ON kill_switch_log"))),
    ("M40", "DB1 default: > 0 instead of >= 0", "d", sub("CHECK (usd >= 0);", "CHECK (usd > 0);", 2)),
    ("M41", "DB1 default: spend_month allows >= -1", "d", sub("spend_month_usd_ok CHECK (usd >= 0)", "spend_month_usd_ok CHECK (usd >= -1)")),
    ("M42", "DB1 variant: <= Infinity", "f", sub("usd < 'Infinity'::numeric);", "usd <= 'Infinity'::numeric);", 2)),
    ("M43", "DB1 variant: spend_month loses the Infinity clause", "f", sub("spend_month_usd_ok CHECK (usd >= 0 AND usd < 'Infinity'::numeric)", "spend_month_usd_ok CHECK (usd >= 0)")),
    ("M44", "DB1 default: lock_timeout removed (lock test)", "d_lock", sub("SET LOCAL lock_timeout = '5s';", "")),
    ("M45", "DB1 variant: lock_timeout 5min (lock test)", "f_lock", sub("SET LOCAL lock_timeout = '5s';", "SET LOCAL lock_timeout = '5min';")),
    ("M46", "DB1 variant: constraint renamed on spend", "f", sub("ADD CONSTRAINT spend_usd_ok CHECK", "ADD CONSTRAINT spend_usd_ok2 CHECK")),
    ("M47", "DB1 upgrade: spend_month line removed", "u", rx(r"ALTER TABLE spend_month DROP CONSTRAINT.*?;\n?$", "", flags=re.S | re.M)),
    ("M48", "DB1 upgrade: <= Infinity", "u", sub("usd < 'Infinity'::numeric", "usd <= 'Infinity'::numeric", 2)),
    ("M49", "DB1 upgrade: drops the rule and adds nothing on spend", "u", rx(r"ALTER TABLE spend DROP CONSTRAINT spend_usd_ok, ADD CONSTRAINT spend_usd_ok CHECK \(usd >= 0 AND usd < 'Infinity'::numeric\);", "ALTER TABLE spend DROP CONSTRAINT spend_usd_ok;")),
    ("M50", "DB1 upgrade: lock_timeout removed (lock test)", "u_lock", sub("SET LOCAL lock_timeout = '5s';", "")),
]


def mut_run():
    global QUIET
    names = {"dl": "spend_decrease_log.sql", "d": "spend_nonneg.sql", "f": "spend_nonneg_finite.sql", "u": "spend_nonneg_upgrade.sql"}
    d, f, u, dl = (HELD / names[k] for k in ("d", "f", "u", "dl"))
    plans = {
        "dl": lambda p, i: suite_db2("m_" + i, [(p, "0006_log")], full=False),
        "d": lambda p, i: suite_db1("default", "m_" + i, [(p, "0006_def")]),
        "f": lambda p, i: suite_db1("finite", "m_" + i, [(p, "0006_fin")]),
        "u": lambda p, i: suite_db1("upgrade", "m_" + i, [(d, "0006_def"), (p, "0007_up")]),
        "d_lock": lambda p, i: lock_test("m_" + i, [], p, "0006_def"),
        "f_lock": lambda p, i: lock_test("m_" + i, [], p, "0006_fin"),
        "u_lock": lambda p, i: lock_test("m_" + i, [(d, "0006_def")], p, "0007_up"),
    }
    # unmutated controls through the same harness
    QUIET = True
    for key, src_f in (("dl", dl), ("d", d), ("f", f), ("u", u)):
        R.clear()
        plans[key](src_f, "ctl_" + key)
        QUIET = False
        print(f"CONTROL {key}: unmutated file, failures={sum(1 for r in R if not r[1])} of {len(R)} checks", flush=True)
        QUIET = True
    for key, src_f in (("d_lock", d), ("f_lock", f), ("u_lock", u)):
        R.clear()
        plans[key](src_f, "ctl_" + key)
        QUIET = False
        print(f"CONTROL {key}: unmutated file, failures={sum(1 for r in R if not r[1])} of {len(R)} checks", flush=True)
        QUIET = True
    caught = missed = invalid = 0
    for mid, desc, key, fn in MUT:
        base = {"dl": dl, "d": d, "f": f, "u": u, "d_lock": d, "f_lock": f, "u_lock": u}[key]
        try:
            text = fn(base.read_text())
        except Exception as ex:
            QUIET = False
            print(f"{mid} INVALID {desc} ({ex})", flush=True)
            invalid += 1
            QUIET = True
            continue
        if text == base.read_text():
            print(f"{mid} INVALID(no change) {desc}", flush=True)
            invalid += 1
            continue
        mp = SCR / f"mut_{mid}_{base.name}"
        mp.write_text(text)
        R.clear()
        try:
            plans[key](mp, mid.lower())
            err = None
        except Exception as ex:
            err = f"{type(ex).__name__}: {str(ex)[:90]!r}"
        fails = [r[0] for r in R if not r[1]]
        QUIET = False
        if err or fails:
            caught += 1
            how = ("migration/guard refused it: " + err) if err and not fails else (f"{len(fails)} failing checks, first: {fails[0][:110]}")
            print(f"{mid} CAUGHT  {desc} -> {how}", flush=True)
        else:
            missed += 1
            print(f"{mid} MISSED  {desc} (all {len(R)} checks passed)", flush=True)
        QUIET = True
    QUIET = False
    print(f"INFO mutations: {caught} caught, {missed} missed, {invalid} invalid, of {len(MUT)}")


try:
    main_run() if mode == "main" else mut_run()
finally:
    for db in [r[0] for r in admin.execute("SELECT datname FROM pg_database WHERE datname ~ '^(i_|lk_|m_)'").fetchall()]:
        admin.execute(f"DROP DATABASE IF EXISTS {db} WITH (FORCE)")
