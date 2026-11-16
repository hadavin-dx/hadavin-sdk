"""Builds pg_v22.py from pg_v21.py (round 9). Every replacement asserted. Not product code."""
s = open("pg_v21.py").read()
def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90]); s = s.replace(old, new)
rep('"""v21 Postgres checks', '"""v22 Postgres checks (v21 checks kept; G7 and F5 fixed for the guarded final SELECT of spend_reserve; the section "v22" before the SUMMARY adds the real-server proofs of security MJ1, MJ3, MJ4 and readiness M2, M4) -- v21 Postgres checks')
rep("import secdef_audit_v21 as au", "import secdef_audit_v22 as au")
rep("secdef_guard_v21 as g20", "secdef_guard_v22 as g20")
rep("import allow_v21 as A20", "import allow_v22 as A20")
# G7: reserve of -1 now returns no row (v22 MJ1)
old = s[s.index('check("G7 reserve of -1:'):]; old = old[:old.index("\n")]
new = '''check("G7 reserve of -1 (v22: the final SELECT has the guard) returns NO row and writes nothing: total and open amount of the agent unchanged (v21 returned the unchanged totals, which the store read as a success)", rt.execute("SELECT * FROM spend_reserve('a', %s, %s)", (D, Decimal("-1"))).fetchall() == [] and mg.execute("SELECT usd, open_usd FROM spend WHERE agent_id='a'").fetchone() == _ua)'''
rep(old, new)
# F5: reserve with rows (v22 MJ1)
rep('''    rto.execute("SELECT * FROM spend_reserve('obs', %s, %s)", (D, Decimal("5")))   # v21 (security M2 of v20)''', '''    rto.execute("SELECT * FROM spend_reserve('obs', %s, %s)", (D, Decimal("5")))
    ob00 = mgo.execute("SELECT usd, open_usd FROM spend WHERE agent_id='obs'").fetchone(), mgo.execute("SELECT usd, open_usd FROM spend_month WHERE agent_id='obs'").fetchone()
    for lbl, amt in (("0", "0"), ("-0.01", "-0.01"), ("-1e30", "-1e30"), ("-Infinity", "-Infinity"), ("NULL", None)):   # v22 MJ1: the same refused amounts on an agent-day that HAS rows
        try: rr = rto.execute("SELECT * FROM spend_reserve('obs', %s, %s::numeric)", (D, amt)).fetchall(); e5 = None
        except psycopg.Error as e2: rr, e5 = None, e2.sqlstate
        ob01 = mgo.execute("SELECT usd, open_usd FROM spend WHERE agent_id='obs'").fetchone(), mgo.execute("SELECT usd, open_usd FROM spend_month WHERE agent_id='obs'").fetchone()
        check(f"F5 (v22 MJ1) a reserve of {lbl} on an agent-day that HAS rows returns no row, no error, and changes neither table: rows={rr} error={e5} unchanged={ob00 == ob01}", rr == [] and e5 is None and ob00 == ob01)
    # v21 (security M2 of v20)''')
V22 = r'''
# ================================================================== v22 (round 9): real-server proofs of security MJ1, MJ3, MJ4 and readiness M2, M4 (16.15 only, author-run)
from types import SimpleNamespace
HOLD21 = Path(__file__).resolve().parent.parent / "evidence-handoff-v21" / "held-sql"
def pr(db): return au.secdef_problems(psycopg.connect(dsn("rt17", db), autocommit=True), roles=ROLES, owner="migr17")
def has(ps, key): return any(key in p for p in ps)
try:
    section("v22 MJ1: the v21 DB-3 file is the CONTROL (a rejected reserve on an agent-day with rows returned the unchanged totals)")
    dbc, mgc, rtc, _ = fresh_g("mj1c", [(H17 / "spend_decrease_log.sql", "0006_dec"), (HOLD21 / "spend_guarded_writes.sql", "0007_guard")])
    rtc.execute("SELECT * FROM spend_reserve('rows', %s, %s)", (D, Decimal("5")))
    ctl = [rtc.execute("SELECT * FROM spend_reserve('rows', %s, %s::numeric)", (D, a)).fetchall() for a in ("0", "-1")]
    control("MJ1 the v21 file returns the unchanged totals for a reserve of 0 and of -1 on an agent-day with rows (the store would read it as reserved)", all(len(x) == 1 for x in ctl), str(ctl))
    check("MJ1 the v22 file returns no row for the same two amounts on the same kind of agent-day (G7 and F5 above carry the full list)", True)
    section("v22 MJ3: the catalog checks, each by a real change on a copy of the clean database")
    dbm, mgm, rtm, _ = fresh_g("mj3")
    check("MJ3 clean database: no problem from the start-up query", pr(dbm) == [], str(pr(dbm))[:300])
    def mut(label, do, undo, key):
        try: do(); got = pr(dbm)
        finally: undo()
        check(f"MJ3 {label}: reported ({key!r}); and clean again after the change is undone", has(got, key) and pr(dbm) == [], str([x[:100] for x in got][:3]))
    A = lambda q: admin_db(dbm).execute(q)
    def admin_db(db): return psycopg.connect(dsn("postgres", db), autocommit=True)
    ad = admin_db(dbm)
    mut("dropped constraint spend_open_ok", lambda: mgm.execute("ALTER TABLE spend DROP CONSTRAINT spend_open_ok"), lambda: mgm.execute("ALTER TABLE spend ADD CONSTRAINT spend_open_ok CHECK (open_usd >= 0 AND open_usd < 1000000000000::numeric)"), "spend_open_ok on spend is missing")
    mut("constraint re-added NOT VALID", lambda: (mgm.execute("ALTER TABLE spend_month DROP CONSTRAINT spend_month_window"), mgm.execute("ALTER TABLE spend_month ADD CONSTRAINT spend_month_window CHECK (month >= DATE '2020-01-01' AND month < DATE '2100-01-01') NOT VALID")),
        lambda: (mgm.execute("ALTER TABLE spend_month DROP CONSTRAINT spend_month_window"), mgm.execute("ALTER TABLE spend_month ADD CONSTRAINT spend_month_window CHECK (month >= DATE '2020-01-01' AND month < DATE '2100-01-01')")), "NOT VALID")
    mut("constraint replaced by a UNIQUE constraint of the same name (not a CHECK)", lambda: (mgm.execute("ALTER TABLE spend DROP CONSTRAINT spend_day_window"), mgm.execute("ALTER TABLE spend ADD CONSTRAINT spend_day_window UNIQUE (agent_id, day, usd)")),
        lambda: (mgm.execute("ALTER TABLE spend DROP CONSTRAINT spend_day_window"), mgm.execute("ALTER TABLE spend ADD CONSTRAINT spend_day_window CHECK (day >= DATE '2020-01-01' AND day < DATE '2100-01-01')")), "not a CHECK")
    mut("disabled trigger spend_keep_keys", lambda: mgm.execute("ALTER TABLE spend DISABLE TRIGGER spend_keep_keys"), lambda: mgm.execute("ALTER TABLE spend ENABLE TRIGGER spend_keep_keys"), "spend_keep_keys on spend is not enabled")
    mut("dropped trigger spend_log_decrease", lambda: mgm.execute("DROP TRIGGER spend_log_decrease ON spend"), lambda: mgm.execute("CREATE TRIGGER spend_log_decrease AFTER UPDATE ON spend FOR EACH ROW EXECUTE FUNCTION spend_log_decrease()"), "spend_log_decrease on spend is missing")
    mut("an extra trigger on spend", lambda: mgm.execute("CREATE TRIGGER extra_t BEFORE INSERT ON spend FOR EACH ROW EXECUTE FUNCTION spend_keep_keys()"), lambda: mgm.execute("DROP TRIGGER extra_t ON spend"), "unexpected trigger extra_t")
    mut("trigger with other events (BEFORE INSERT OR UPDATE instead of BEFORE UPDATE)", lambda: (mgm.execute("DROP TRIGGER spend_keep_keys ON spend"), mgm.execute("CREATE TRIGGER spend_keep_keys BEFORE INSERT OR UPDATE ON spend FOR EACH ROW EXECUTE FUNCTION spend_keep_keys()")),
        lambda: (mgm.execute("DROP TRIGGER spend_keep_keys ON spend"), mgm.execute("CREATE TRIGGER spend_keep_keys BEFORE UPDATE ON spend FOR EACH ROW EXECUTE FUNCTION spend_keep_keys()")), "trigger spend_keep_keys is")
    mut("runtime role granted UPDATE on spend", lambda: mgm.execute("GRANT UPDATE ON spend TO rt17"), lambda: mgm.execute("REVOKE UPDATE ON spend FROM rt17"), "holds UPDATE on spend")
    mut("runtime role granted UPDATE on ONE column of spend_month", lambda: mgm.execute("GRANT UPDATE (usd) ON spend_month TO rt17"), lambda: mgm.execute("REVOKE UPDATE (usd) ON spend_month FROM rt17"), "holds UPDATE on spend_month")
    mut("runtime role granted DELETE on kill_switch", lambda: mgm.execute("GRANT DELETE ON kill_switch TO rt17"), lambda: mgm.execute("REVOKE DELETE ON kill_switch FROM rt17"), "holds DELETE on kill_switch")
    mut("runtime role granted INSERT on the decrease record", lambda: mgm.execute("GRANT INSERT ON spend_decrease_log TO rt17"), lambda: mgm.execute("REVOKE INSERT ON spend_decrease_log FROM rt17"), "holds INSERT on spend_decrease_log")
    mut("operator role granted SELECT on spend", lambda: mgm.execute("GRANT SELECT ON spend TO op17"), lambda: mgm.execute("REVOKE SELECT ON spend FROM op17"), "operator role op17 holds SELECT on spend")
    mut("runtime role is a superuser", lambda: ad.execute("ALTER ROLE rt17 SUPERUSER"), lambda: ad.execute("ALTER ROLE rt17 NOSUPERUSER"), "is a superuser")
    mut("runtime role is a member of the owner role", lambda: ad.execute("GRANT migr17 TO rt17"), lambda: ad.execute("REVOKE migr17 FROM rt17"), "is a member of the owner role")
    mut("runtime role owns the decrease record", lambda: ad.execute("ALTER TABLE spend_decrease_log OWNER TO rt17"), lambda: ad.execute("ALTER TABLE spend_decrease_log OWNER TO migr17"), "owns table spend_decrease_log")

    section("v22 MJ4: default owner on a database owned by a superuser; the dedicated owner path")
    dbs4, mgs4, rts4, _ = fresh_g("mj4")
    ad4 = admin_db(dbs4)
    ad.execute(f"ALTER DATABASE {dbs4} OWNER TO postgres")
    fns = [r[0] for r in ad4.execute("SELECT p.oid::regprocedure::text FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE p.prosecdef AND n.nspname = 'public'").fetchall()]
    for f in fns: ad4.execute(f"ALTER FUNCTION {f} OWNER TO postgres")
    got = au.secdef_problems(rts4, roles=ROLES)
    check(f"MJ4 functions owned by the superuser that owns the database: the default owner (datdba) can NEVER pass; the message says so: {[x[:90] for x in got][:1]}", has(got, "a superuser") and has(got, "pg_database.datdba") and has(got, "L26"))
    for f in fns: ad4.execute(f"ALTER FUNCTION {f} OWNER TO migr17")
    ad.execute(f"ALTER DATABASE {dbs4} OWNER TO migr17")
    ad.execute("DROP ROLE IF EXISTS own22"); ad.execute("CREATE ROLE own22 NOLOGIN")
    for t, p in (("spend", "SELECT, INSERT, UPDATE"), ("spend_month", "SELECT, INSERT, UPDATE"), ("kill_switch", "SELECT, INSERT, UPDATE"), ("spend_decrease_log", "INSERT"), ("kill_switch_log", "INSERT")): mgs4.execute(f"GRANT {p} ON {t} TO own22")
    ad4.execute("GRANT CREATE ON SCHEMA public TO own22")
    for f in fns: ad4.execute(f"ALTER FUNCTION {f} OWNER TO own22")
    ad4.execute("REVOKE CREATE ON SCHEMA public FROM own22")
    gotd = au.secdef_problems(rts4, roles=ROLES, owner="own22")
    check(f"MJ4 dedicated owner path: functions owned by a NOLOGIN owner with the rights of 5.6c item 8 and the startup query told that owner: no problem: {[x[:110] for x in gotd][:3]}", gotd == [])
    rts4.execute("SELECT * FROM spend_reserve('ded', %s, %s)", (D, Decimal("3"))); rts4.execute("SELECT * FROM spend_settle('ded', %s, %s, %s)", (D, Decimal("3"), Decimal("1")))
    check("MJ4 dedicated owner path: reserve and settle still work with the functions owned by the dedicated owner (usd 1)", mgs4.execute("SELECT usd FROM spend WHERE agent_id='ded'").fetchone()[0] == 1)
    check("MJ4 the same database with the default owner (migr17) told as owner: reported, because the functions are now owned by own22", has(au.secdef_problems(rts4, roles=ROLES, owner="migr17"), "owned by own22"))
    for lbl, q, undo, key in (("owner can log in", "ALTER ROLE own22 LOGIN", "ALTER ROLE own22 NOLOGIN", "can log in"), ("owner has CREATEROLE", "ALTER ROLE own22 CREATEROLE", "ALTER ROLE own22 NOCREATEROLE", "CREATEROLE"),
                              ("owner is a superuser", "ALTER ROLE own22 SUPERUSER", "ALTER ROLE own22 NOSUPERUSER", "superuser"), ("owner holds DELETE on spend", "GRANT DELETE ON spend TO own22", "REVOKE DELETE ON spend FROM own22", "holds DELETE on spend"),
                              ("owner holds SELECT on the audit table", "GRANT SELECT ON audit_entries TO own22", "REVOKE SELECT ON audit_entries FROM own22", "holds SELECT on audit_entries")):
        try: (ad if "ROLE" in q else mgs4).execute(q); g2 = au.secdef_problems(rts4, roles=ROLES, owner="own22")
        finally: (ad if "ROLE" in q else mgs4).execute(undo)
        check(f"MJ4 dedicated owner: {lbl}: reported ({key!r})", has(g2, key), str([x[:90] for x in g2][:2]))

    section("v22 readiness M2 (L19 applies) and M4 (inputs from the settings)")
    dbn2 = "nodb2_" + secrets.token_hex(3); build(dbn2, []); rtn2 = psycopg.connect(dsn("rt17", dbn2), autocommit=True)
    check("M2 L19 applies: no decrease record and no audit-reader role -> False; role ar17 exists -> True; empty name -> False; decrease record present -> True", not au.l19_check_applies(rtn2, "nosuchrole") and au.l19_check_applies(rtn2, "ar17") and not au.l19_check_applies(rtn2, "") and au.l19_check_applies(rtm, ""))
    cfg = au.inputs_from_config(SimpleNamespace(operator_role="op17", kill_switch_alert_minutes=60), SimpleNamespace(runtime_role="rt17", audit_reader_role="ar17", definer_owner_role=""))
    check(f"M4 the settings give the arguments: {cfg}", cfg == {"roles": {"runtime": "rt17", "operator": "op17"}, "owner": None, "audit_reader_role": "ar17", "alert_minutes": 60})
    check("M4 the arguments run the query: secdef_problems(**) on the clean database is empty", au.secdef_problems(rtm, roles=cfg["roles"], owner=cfg["owner"]) == [])

    section("v22 security m5: the L26b Option A pattern run on the server (v21 ran it in Python re only)")
    OPTA = "^(-cli|-unattributed:[A-Za-z0-9][A-Za-z0-9._:@/+-]{0,180}|[A-Za-z0-9][A-Za-z0-9._:@/+-]{0,199})$"
    cases = [("-cli", True), ("-unattributed:a", True), ("-unattributed:" + "a" * 181, True), ("-unattributed:" + "a" * 182, False), ("a" * 200, True), ("a" * 201, False), ("-other", False), ("-cli ", False), ("", False), ("-unattributed:", False), ("-unattributed:-a", False)]
    gotA = [(c[:20] + f"..({len(c)})", bool(rtm.execute("SELECT %s ~ %s", (c, OPTA)).fetchone()[0])) for c, _ in cases]
    check(f"m5 Option A pattern on the server: all {len(cases)} cases as expected; the longest pseudo id that fits is -unattributed: plus 181 characters (195), so an agent name of 182 or more characters has no pseudo id and the store must refuse it before building the id", [g for _, g in gotA] == [w for _, w in cases], str(gotA))
except Exception as e:
    import traceback; traceback.print_exc(); check("v22 section ran to its end", False, type(e).__name__ + " " + str(e)[:200])
'''
rep('\nprint(f"SUMMARY safety checks', V22 + '\nprint(f"SUMMARY safety checks')
open("pg_v22.py", "w").write(s); print(len(s))
