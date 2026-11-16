"""EVIDENCE RUNNER own hostile money cases on the v19 DB-3 held SQL. Records PASS/FAIL against stated properties and OBS lines. Made-up data.
usage: money_v19.py <socket> <src> <held19> <held16>   (HV_ADMIN_PW in env)"""
import sys, os, shutil, tempfile, secrets, unicodedata
from datetime import date
from decimal import Decimal as Dc
from pathlib import Path
sock, src, H19 = sys.argv[1], sys.argv[2], Path(sys.argv[3])
sys.path.insert(0, src); sys.path.insert(0, str(H19.parent))
import psycopg
from psycopg import sql
import hadavin_sdk.store.migrate as m
import secdef_audit_v19 as au
D = date(2026, 11, 16)
PW = {"postgres": os.environ["HV_ADMIN_PW"]}
adm = psycopg.connect(f"host={sock} dbname=postgres user=postgres password={PW['postgres']}", autocommit=True)
for r in ("mg", "rt", "op"):
    PW[r] = secrets.token_hex(16); adm.execute(sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(sql.Identifier(r), sql.Literal(PW[r])))
dsn = lambda u, db: f"host={sock} dbname={db} user={u} password={PW[u]}"
res = []
def ex(n, ok, d=""): res.append(bool(ok)); print(("EXPECT PASS " if ok else "EXPECT FAIL ") + n + (f"  [{d}]" if d else ""), flush=True)
def obs(s): print("OBS " + s, flush=True)
def code(f):
    try: f(); return None
    except psycopg.Error as e: return str(e.sqlstate)
SEL = {k: m.Grant("table", "SELECT") for k in ("spend", "spend_month", "kill_switch")}
adm.execute("CREATE DATABASE h OWNER mg")
tmp = Path(tempfile.mkdtemp(prefix="ev19mig_"))
for p in m.MIGRATIONS.glob("*.sql"): shutil.copy(p, tmp / p.name)
shutil.copy(H19 / "spend_decrease_log.sql", tmp / "0006_dec.sql"); shutil.copy(H19 / "spend_guarded_writes.sql", tmp / "0007_guard.sql")
for k in ("spend_decrease_log", "kill_switch_log"): m.GRANTS[k] = m.Grant("table", "")
m._migration_files = lambda folder=tmp: sorted(Path(folder).glob("*.sql"))
m.GRANTS.update(SEL)
m.migrate(dsn("mg", "h"), runtime_role="rt")
mg = psycopg.connect(dsn("mg", "h"), autocommit=True)
au.apply_function_grants(mg, roles={"runtime": "rt", "operator": "op"})
rt = psycopg.connect(dsn("rt", "h"), autocommit=True)
obs("server " + mg.execute("SHOW server_version").fetchone()[0])
R = lambda a, w, day=D: rt.execute("SELECT * FROM spend_reserve(%s,%s,%s)", (a, day, w)).fetchone()
S = lambda a, w, ac, day=D: rt.execute("SELECT * FROM spend_settle(%s,%s,%s,%s)", (a, day, w, ac)).fetchone()
tot = lambda a, day=D: mg.execute("SELECT usd,open_usd FROM spend WHERE agent_id=%s AND day=%s", (a, day)).fetchone()
mon = lambda a: mg.execute("SELECT usd,open_usd FROM spend_month WHERE agent_id=%s", (a,)).fetchone()
bad = lambda: mg.execute("SELECT (SELECT count(*) FROM spend WHERE usd<0 OR open_usd<0 OR usd<open_usd OR usd='NaN' OR open_usd='NaN')+(SELECT count(*) FROM spend_month WHERE usd<0 OR open_usd<0 OR usd<open_usd OR usd='NaN' OR open_usd='NaN')").fetchone()[0]
print("==== M1 reserve amounts")
for i, (nm, v) in enumerate([("0", Dc(0)), ("-0", Dc("-0")), ("0.0000001", Dc("1e-7")), ("1", Dc(1)), ("negative -0.01", Dc("-0.01")), ("negative huge -1e30", Dc("-1e30")), ("1e12 ceiling", Dc("1e12")),
        ("999999999999.999999", Dc("999999999999.999999")), ("1e15", Dc("1e15")), ("1e131071", Dc("1e131071")), ("1e131072", Dc("1e131072")), ("NaN", Dc("NaN")), ("Infinity", Dc("Infinity")), ("-Infinity", Dc("-Infinity")), ("NULL", None)]):
    a = f"m{i}"; c = code(lambda: R(a, v)); obs(f"M1 reserve {nm}: sqlstate={c} day={tot(a)} month={mon(a)}")
    ex(f"M1 reserve {nm}: no bad row", bad() == 0)
    if nm in ("negative -0.01", "negative huge -1e30", "1e12 ceiling", "1e15", "1e131071", "1e131072", "NaN", "Infinity", "-Infinity", "NULL"):
        ex(f"M1 reserve {nm} refused or inert", c is not None or tot(a) in (None,), f"{c} {tot(a)}")
    if nm in ("0", "-0"): ex(f"M1 reserve {nm} writes no row", tot(a) is None and mon(a) is None, f"{tot(a)} {mon(a)}")
print("==== M2 settle cases")
for i, (nm, w, ac) in enumerate([("exact give-back 10->0", Dc(10), Dc(0)), ("settle at worst 10->10", Dc(10), Dc(10)), ("settle ABOVE worst 10->15", Dc(10), Dc(15)), ("worst above open 11", Dc(11), Dc(0)),
        ("negative worst", Dc(-1), Dc(0)), ("negative actual", Dc(10), Dc(-1)), ("NaN worst", Dc("NaN"), Dc(0)), ("NaN actual", Dc(10), Dc("NaN")), ("Infinity actual", Dc(10), Dc("Infinity")), ("-Infinity worst", Dc("-Infinity"), Dc(0)),
        ("actual 1e12", Dc(10), Dc("1e12")), ("actual 1e131072", Dc(10), Dc("1e131072")), ("NULL worst", None, Dc(0)), ("NULL actual", Dc(10), None), ("worst 0 actual 0", Dc(0), Dc(0)), ("worst 0 actual 3", Dc(0), Dc(3)), ("worst 0.5 of open 10", Dc("0.5"), Dc(0))]):
    a = f"s{i}"; R(a, Dc(10)); b = tot(a); bm = mon(a)
    c = code(lambda: S(a, w, ac)); aft = tot(a); am = mon(a)
    obs(f"M2 settle {nm}: sqlstate={c} before={b}/{bm} after={aft}/{am}")
    ex(f"M2 settle {nm}: settled money (usd-open) never falls (day and month)", aft[0]-aft[1] >= b[0]-b[1] and am[0]-am[1] >= bm[0]-bm[1] and bad() == 0, f"{b}->{aft}")
print("==== M3 settle above worst (over-report direction) and settled-total monotonic over 300 random operations")
import random; rnd = random.Random(19); lo = {}
for k in range(300):
    a = "r%d" % rnd.randrange(3); op = rnd.choice("RSS"); w = Dc(rnd.choice(["0","1","2.5","7","1e-6","100"])); ac = Dc(rnd.choice(["0","1","3","10","1e-6"]))
    b = tot(a) or (Dc(0), Dc(0)); code(lambda: R(a, w) if op == "R" else S(a, w, ac)); af = tot(a) or (Dc(0), Dc(0))
    if af[0]-af[1] < b[0]-b[1]: lo[a] = (b, af)
ex("M3 random 300 ops: settled money never fell for any agent, no bad row", not lo and bad() == 0, str(lo))
print("==== M4 agent id spellings")
nf = unicodedata.normalize
for nm, v in [("NFC cafe", nf("NFC", "café")), ("NFD cafe", nf("NFD", "café")), ("NFKC fullwidth A", "Ａ"), ("leading space", " a"), ("trailing space", "a "), ("tab inside", "a\tb"), ("newline", "a\nb"), ("NUL-free DEL 0x7f", "a\x7fb"),
        ("zero width space", "a​b"), ("NBSP lead", " a"), ("RTL override", "a‮b"), ("combining only", "́"), ("emoji ZWJ seq", "\U0001F468‍\U0001F469"), ("200 NFC é", "é"*200), ("201 NFC é", "é"*201),
        ("200 NFD (e+accent = 400 chars)", nf("NFD", "é")*100), ("sql quote", "x';DROP TABLE spend;--"), ("percent", "50%"), ("lone surrogate-free U+FFFD", "�"), ("NULL", None), ("empty", ""), ("only space", " ")]:
    c = code(lambda: R(v, Dc(1))); n = 0 if v is None else mg.execute("SELECT count(*) FROM spend WHERE agent_id=%s", (v,)).fetchone()[0]
    obs(f"M4 agent {nm!r}: sqlstate={c} rows={n}")
ex("M4 NFD spelling refused, NFC accepted", code(lambda: R(nf("NFD", "café"), Dc(1))) == "23514" and code(lambda: R(nf("NFC", "café"), Dc(1))) is None)
ex("M4 leading/trailing blank and control char refused", all(code(lambda: R(v, Dc(1))) == "23514" for v in (" a", "a ", "a\tb", "a\nb", "a\x7fb")))
ex("M4 NULL and empty refused", code(lambda: R(None, Dc(1))) is not None and code(lambda: R("", Dc(1))) == "23514")
obs("M4 agent ids that differ only by case, and NFKC fullwidth, are separate budgets: " + str(mg.execute("SELECT agent_id FROM spend WHERE agent_id IN ('Ａ','café') ORDER BY 1").fetchall()))
print("==== M5 days and months")
for nm, d in [("2019-12-31", "2019-12-31"), ("2020-01-01", "2020-01-01"), ("2099-12-31", "2099-12-31"), ("2100-01-01", "2100-01-01"), ("infinity", "infinity"), ("-infinity", "-infinity"), ("0001-01-01", "0001-01-01"), ("4713-01-01 BC", "4713-01-01 BC"), ("2024-02-29", "2024-02-29"), ("5874897-12-31 (pg max)", "5874897-12-31")]:
    a = "d_" + nm; c = code(lambda: rt.execute("SELECT * FROM spend_reserve(%s,%s::date,1)", (a, d))); obs(f"M5 reserve day {nm}: sqlstate={c} month rows={mg.execute('SELECT month::text FROM spend_month WHERE agent_id=%s', (a,)).fetchall()}")
ex("M5 outside-window days refused 23514", all(code(lambda: rt.execute("SELECT * FROM spend_reserve('w',%s::date,1)", (d,))) == "23514" for d in ("2019-12-31", "2100-01-01", "infinity", "-infinity", "0001-01-01")))
ex("M5 boundary days accepted", all(code(lambda: rt.execute("SELECT * FROM spend_reserve('wb',%s::date,1)", (d,))) is None for d in ("2020-01-01", "2099-12-31")))
ex("M5 NULL day refused", code(lambda: rt.execute("SELECT * FROM spend_reserve('x',NULL,1)")) is not None)
ex("M5 settle of a day with no row changes neither day nor month", (lambda: (R("nr", Dc(5)), S("nr", Dc(5), Dc(0), date(2026, 11, 17)), mon("nr") == (Dc(5), Dc(5)))[-1])())
obs("M5 settle for another day of the same month: month row after = " + str(mon("nr")) + " (expected 5,5: unchanged)")
print("==== M6 shadowing and session tricks as the runtime role")
for lab, q in [("SET search_path=public", "SET search_path = public"), ("temp table named spend", "CREATE TEMP TABLE spend(agent_id text,day date,usd numeric,open_usd numeric)"),
               ("SET ROLE mg", "SET ROLE mg"), ("SET SESSION AUTHORIZATION mg", "SET SESSION AUTHORIZATION mg"), ("set_config role", "SELECT set_config('role','mg',false)"),
               ("CREATE VIEW", "CREATE VIEW v AS SELECT 1"), ("CREATE FUNCTION public", "CREATE FUNCTION public.spend_reserve(text,date,numeric) RETURNS int LANGUAGE sql AS 'SELECT 1'"),
               ("CREATE TRIGGER on spend", "CREATE TRIGGER t BEFORE INSERT ON spend FOR EACH ROW EXECUTE FUNCTION spend_keep_keys()"), ("ALTER FUNCTION owner", "ALTER FUNCTION spend_reserve(text,date,numeric) OWNER TO rt"),
               ("ALTER FUNCTION search_path", "ALTER FUNCTION spend_reserve(text,date,numeric) SET search_path = public"), ("GRANT execute to rt on settle", "GRANT ALL ON FUNCTION kill_switch_release() TO rt"),
               ("release as runtime", "SELECT kill_switch_release()"), ("DROP FUNCTION", "DROP FUNCTION spend_reserve(text,date,numeric)"), ("CREATE RULE on spend", "CREATE RULE r AS ON INSERT TO spend DO INSTEAD NOTHING")]:
    rtx = psycopg.connect(dsn("rt", "h"), autocommit=True)  # fresh session per case (the first run reused one session after the temp-table case: a shadowing artifact of my own test)
    c = code(lambda: rtx.execute(q)); obs(f"M6 runtime {lab}: sqlstate={c}")
    if lab in ("SET ROLE mg", "SET SESSION AUTHORIZATION mg", "set_config role", "CREATE VIEW", "CREATE TRIGGER on spend", "ALTER FUNCTION owner", "ALTER FUNCTION search_path", "GRANT execute to rt on settle", "release as runtime", "DROP FUNCTION", "CREATE RULE on spend", "CREATE FUNCTION public"):
        ex(f"M6 runtime {lab} refused", c is not None, f"sqlstate={c}")
rt.execute("RESET ALL") if False else None
rt2 = psycopg.connect(dsn("rt", "h"), autocommit=True); rt2.execute("CREATE TEMP TABLE spend(agent_id text,day date,usd numeric,open_usd numeric)")
rt2.execute("SET search_path = pg_temp, public"); before = tot("tmpx")
rt2.execute("SELECT * FROM spend_reserve('tmpx', %s, 2)", (D,)); ex("M6b with a temp table named spend first on search_path, the function still writes the REAL table", tot("tmpx") == (Dc(2), Dc(2)) and rt2.execute("SELECT count(*) FROM pg_temp.spend").fetchone()[0] == 0, str(tot("tmpx")))
ex("M7 final: no bad row anywhere", bad() == 0, str(bad()))
print(f"SUMMARY expectations {sum(res)} of {len(res)} passed")
