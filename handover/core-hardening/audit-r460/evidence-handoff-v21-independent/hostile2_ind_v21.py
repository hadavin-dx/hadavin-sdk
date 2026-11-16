"""EVIDENCE RUNNER (independent, hand-off v21): hostile spellings aimed at ADD_PINS_BY_FILE and the other pins, applied through the real migrate() on the
server the wrapper started, plus data cases. Records only; it never judges. Usage (through run_pg_v21.sh): python hostile_ind_v21.py <socket_dir> <src_dir> <held_v21> <held_v16>
One line per case: ID | file | guard problems | server result | runtime-login probes | direct (owner-role) probes | note.  Made-up data only."""
import sys, os, shutil, tempfile, secrets, atexit, re
from datetime import date
from decimal import Decimal
from pathlib import Path
sock, src, HELD = sys.argv[1], sys.argv[2], Path(sys.argv[3])
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, src)
import psycopg
from psycopg import sql
import hadavin_sdk.store.migrate as m
import secdef_guard_v21 as g
import allow_v21 as A
import secdef_audit_v21 as au

PW = {"postgres": os.environ["HV_ADMIN_PW"]}
D = date(2026, 11, 16)
ROLES = {"runtime": "rt17", "operator": "op17"}
def dsn(u, db): return f"host={sock} dbname={db} user={u} password={PW[u]}"
admin = psycopg.connect(dsn("postgres", "postgres"), autocommit=True)
for r in ("migr17", "rt17", "op17", "ar17"):
    PW[r] = secrets.token_hex(16)
    admin.execute(sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(sql.Identifier(r), sql.Literal(PW[r])))
print("SERVER " + admin.execute("SELECT version()").fetchone()[0][:60], flush=True)
SEL = {k: m.Grant("table", "SELECT") for k in ("spend", "spend_month", "kill_switch")}
ORIG = {k: m.GRANTS[k] for k in SEL}
def grants_select_only(): m.GRANTS.update(SEL)
def grants_original(): m.GRANTS.update(ORIG)
def st(fn):
    try: fn(); return None
    except psycopg.Error as e: return str(e.sqlstate)
def sub(t, old, new):
    assert old in t, "spelling does not apply: " + old[:40]
    return t.replace(old, new, 1)

F3, F2 = "spend_guarded_writes.sql", "spend_decrease_log.sql"
T3 = (HELD / F3).read_text(encoding="utf-8")
TXT = {n: (HELD / n).read_text(encoding="utf-8") for n in (F3, F2, "spend_nonneg.sql", "spend_nonneg_finite.sql", "spend_nonneg_upgrade.sql")}
BASE = list(m.MIGRATIONS.glob("*.sql"))

def mkdb(name, folder_files, template=None):
    if template: admin.execute(f"CREATE DATABASE {name} TEMPLATE {template} OWNER migr17")
    else: admin.execute(f"CREATE DATABASE {name} OWNER migr17")
    tmp = Path(tempfile.mkdtemp(prefix="indmig_")); atexit.register(shutil.rmtree, tmp, True)
    for p in BASE: shutil.copy(p, tmp / p.name)
    for text, n in folder_files: (tmp / f"{n}.sql").write_text(text, encoding="utf-8")
    return tmp
def run_migrate(db, tmp):
    m._migration_files = lambda folder=tmp: sorted(Path(folder).glob("*.sql"))
    try:
        m.migrate(dsn("migr17", db), runtime_role="rt17"); return "APPLIED"
    except psycopg.Error as e: return "REFUSED " + str(e.sqlstate)
    except Exception as e: return "ERROR " + type(e).__name__ + ":" + str(e)[:50].replace("\n", " ")

# templates: A = base only; B = base + DB-2 applied; C = base + DB-1 default applied
def template(name, files):
    m.GRANTS["spend_decrease_log"] = m.Grant("table", ""); m.GRANTS["kill_switch_log"] = m.Grant("table", "")
    if not any(F2 == f for f, _ in files):
        m.GRANTS.pop("spend_decrease_log", None); m.GRANTS.pop("kill_switch_log", None)
    tmp = mkdb(name, [(TXT[f], n) for f, n in files]); grants_select_only(); r = run_migrate(name, tmp)
    print(f"TEMPLATE {name} {files} -> {r}", flush=True)
    admin.execute(f"ALTER DATABASE {name} IS_TEMPLATE true")
    return tmp
template("tplb", [(F2, "0006_dec")])
template("tpla", [])
template("tplc", [("spend_nonneg.sql", "0006_a")])

def drop(db): admin.execute(f"DROP DATABASE IF EXISTS {db} WITH (FORCE)")

n_case = 0
SUMMARY = []   # (id, guard_clean, applied, weakened)
def probes3(db):
    mg = psycopg.connect(dsn("migr17", db), autocommit=True)
    try: au.apply_function_grants(mg, roles=ROLES); gnote = ""
    except Exception as e: gnote = "grants:" + type(e).__name__
    nf = mg.execute("SELECT count(*) FROM pg_proc WHERE proname IN ('spend_reserve','spend_settle','kill_switch_engage','kill_switch_release')").fetchone()[0]
    rt = psycopg.connect(dsn("rt17", db), autocommit=True)
    out = {}
    for key, ag, day, w in (("sp", "a b", D, 1), ("lead", " a", D, 1), ("nl", "a\nb", D, 1), ("big", "bigx", D, Decimal("1e20")), ("d1999", "d99", date(1999, 1, 1), 1), ("ok", "okagent", D, 1)):
        e = st(lambda: rt.execute("SELECT * FROM spend_reserve(%s,%s,%s)", (ag, day, w)).fetchall())
        out[key] = "ACC" if e is None else e
    direct = {}
    for key, ag, day, w in (("sp", "d b", D, 1), ("nl", "d\nb", D, 1), ("big", "dbig", D, Decimal("1e20")), ("neg", "dneg", D, -5)):
        e = st(lambda: mg.execute("INSERT INTO spend (agent_id, day, usd) VALUES (%s,%s,%s)", (ag, day, w)))
        direct[key] = "ACC" if e is None else e
    mg.execute("DELETE FROM spend WHERE agent_id IN ('d b', E'd\\nb', 'dbig', 'dneg')")
    # the DB-3 function-level ceiling on the open amount and the day window are probed through reserve above
    rt.close(); mg.close()
    weak = out["sp"] == "ACC" or out["lead"] == "ACC" or out["nl"] == "ACC" or out["big"] == "ACC" or out["d1999"] == "ACC" or direct["sp"] == "ACC" or direct["nl"] == "ACC" or direct["big"] == "ACC" or direct["neg"] == "ACC"
    return f"fn={nf}{(' ' + gnote) if gnote else ''} rt[space={out['sp']} lead={out['lead']} nl={out['nl']} 1e20={out['big']} day1999={out['d1999']} ok={out['ok']}]", f"owner[space={direct['sp']} nl={direct['nl']} 1e20={direct['big']} neg={direct['neg']}]", weak

def case(cid, fname, text, tpl, note="", kind="3", pre=None):
    global n_case; n_case += 1
    probs = A.check(g, fname, text)
    db = f"c{n_case:03d}_{secrets.token_hex(2)}"
    names = {"tplb": [(TXT[F2], "0006_dec"), (text, "0007_x")], "tpla": [(text, "0006_x")], "tplc": [(TXT["spend_nonneg.sql"], "0006_a"), (text, "0007_x")]}[tpl]
    tmp = mkdb(db, names, template=tpl)
    if kind == "3": grants_select_only()
    else: grants_original()
    if tpl == "tpla" and kind != "2": m.GRANTS.pop("spend_decrease_log", None); m.GRANTS.pop("kill_switch_log", None)
    elif tpl == "tpla": m.GRANTS["spend_decrease_log"] = m.Grant("table", ""); m.GRANTS["kill_switch_log"] = m.Grant("table", "")
    else:
        if tpl == "tplb": m.GRANTS["spend_decrease_log"] = m.Grant("table", ""); m.GRANTS["kill_switch_log"] = m.Grant("table", "")
    # when the case itself is the DB-2 file the template already holds a copy of the original: it is applied as a second file number, so names collide; keep tpl A for those
    res = run_migrate(db, tmp)
    pr = "-"; dr = "-"; weak = False
    if res == "APPLIED":
        try:
            if kind == "3": pr, dr, weak = probes3(db)
            elif kind == "1": pr, dr, weak = probes1(db)
            elif kind == "2": pr, dr, weak = probes2(db)
        except Exception as e: pr = "PROBE-ERROR " + type(e).__name__ + str(e)[:60].replace("\n", " ")
    first = (probs[0][len(fname) + 2:][:70] if probs else "")
    print(f"{cid} | {fname} | guard={'CLEAN' if not probs else str(len(probs)) + ' problems'}{(' [' + first + ']') if first else ''} | server={res} | {pr} | {dr} | {note}", flush=True)
    SUMMARY.append((cid, not probs, res == "APPLIED", weak))
    drop(db)

def probes1(db):
    mg = psycopg.connect(dsn("migr17", db), autocommit=True); d = {}
    for key, v in (("neg", "-5"), ("nan", "NaN"), ("inf", "Infinity"), ("ok", "3")):
        e = st(lambda: mg.execute(f"INSERT INTO spend (agent_id, day, usd) VALUES ('p{key}', %s, {chr(39)}{v}{chr(39)}::numeric)", (D,))); d[key] = "ACC" if e is None else e
    mg.execute("DELETE FROM spend")
    cons = [r[0] for r in mg.execute("SELECT conname FROM pg_constraint WHERE conrelid='spend'::regclass AND conname LIKE '%usd%' ORDER BY 1").fetchall()]
    weak = d["neg"] == "ACC"
    return f"cons={cons}", f"owner[neg={d['neg']} nan={d['nan']} inf={d['inf']} ok={d['ok']}]", weak

def probes2(db):
    mg = psycopg.connect(dsn("migr17", db), autocommit=True); rt = psycopg.connect(dsn("rt17", db), autocommit=True)
    mg.execute("INSERT INTO spend (agent_id, day, usd) VALUES ('p2', %s, 10)", (D,))
    before = mg.execute("SELECT count(*) FROM spend_decrease_log").fetchone()[0]
    e1 = st(lambda: rt.execute("UPDATE spend SET usd = 1 WHERE agent_id='p2'"))
    after = mg.execute("SELECT count(*) FROM spend_decrease_log").fetchone()[0]
    e2 = st(lambda: rt.execute("UPDATE spend SET agent_id='q2' WHERE agent_id='p2'"))
    e3 = st(lambda: rt.execute("DELETE FROM spend_decrease_log")); e4 = st(lambda: mg.execute("DELETE FROM spend_decrease_log"))
    e5 = st(lambda: rt.execute("UPDATE kill_switch SET \"on\"=true"))
    weak = (e1 is None and after == before) or e2 is None or e3 is None or e4 is None
    return f"log_rows {before}->{after}", f"decrease={e1} keychange={e2} rt_delete_log={e3} owner_delete_log={e4}", weak


# ---- round 2 of the hostile spellings: combined and hidden-statement spellings; DB-1 probes also test spend_month
def probes1(db):
    mg = psycopg.connect(dsn("migr17", db), autocommit=True); d = {}; MO = date(2026, 11, 1)
    for key, v in (("neg", "-5"), ("nan", "NaN"), ("inf", "Infinity"), ("ok", "3")):
        e = st(lambda: mg.execute(f"INSERT INTO spend (agent_id, day, usd) VALUES ('p{key}', %s, {chr(39)}{v}{chr(39)}::numeric)", (D,))); d[key] = "ACC" if e is None else e
        e = st(lambda: mg.execute(f"INSERT INTO spend_month (agent_id, month, usd) VALUES ('p{key}', %s, {chr(39)}{v}{chr(39)}::numeric)", (MO,))); d["m" + key] = "ACC" if e is None else e
    mg.execute("DELETE FROM spend"); mg.execute("DELETE FROM spend_month")
    cons = [r[0] for r in mg.execute("SELECT conname FROM pg_constraint WHERE conrelid IN ('spend'::regclass,'spend_month'::regclass) AND conname LIKE '%usd%' ORDER BY 1").fetchall()]
    weak = d["neg"] == "ACC" or d["mneg"] == "ACC"
    return f"cons={cons}", f"owner[neg={d['neg']} nan={d['nan']} inf={d['inf']} | month neg={d['mneg']} nan={d['mnan']} inf={d['minf']}]", weak
RX = "'^[A-Za-z0-9][A-Za-z0-9._:@/+-]{0,199}$'"
L_OPEN = "ALTER TABLE spend ADD CONSTRAINT spend_open_ok CHECK (open_usd >= 0 AND open_usd < 1000000000000::numeric);"
L_GOK = "ALTER TABLE spend ADD CONSTRAINT spend_guarded_ok CHECK (usd >= 0 AND usd < 1000000000000::numeric);"
L_AG = f"ALTER TABLE spend ADD CONSTRAINT spend_agent_len CHECK (agent_id ~ {RX});"
L_DAY = "ALTER TABLE spend ADD CONSTRAINT spend_day_window CHECK (day >= DATE '2020-01-01' AND day < DATE '2100-01-01');"
M_AG = f"ALTER TABLE spend_month ADD CONSTRAINT spend_month_agent_len CHECK (agent_id ~ {RX});"
M_GOK = "ALTER TABLE spend_month ADD CONSTRAINT spend_month_guarded_ok CHECK (usd >= 0 AND usd < 1000000000000::numeric);"
M_WIN = "ALTER TABLE spend_month ADD CONSTRAINT spend_month_window CHECK (month >= DATE '2020-01-01' AND month < DATE '2100-01-01');"
for L in (L_OPEN, L_GOK, L_AG, L_DAY, M_AG, M_GOK, M_WIN): assert L in T3, L[:50]
def rep(*pairs):
    def f(t):
        for o, n in pairs: t = sub(t, o, n)
        return t
    return f
def add_after(anchor, extra): return lambda t: sub(t, anchor, anchor + "\n" + extra)
S = []   # (id, note, fn)
def s(i, note, fn): S.append((f"H{i:02d}", note, fn))

S = []
def s(i, note, fn): S.append((f"R{i:02d}", note, fn))
def dele(*ls):
    def f(t):
        for l in ls: t = sub(t, l, "")
        return t
    return f
def both(a, b): return lambda t: sub(sub(t, a[0], a[1]), b[0], b[1])
s(1, "delete BOTH agent-rule lines (spend and spend_month)", dele(L_AG, M_AG))
s(2, "delete BOTH usd ceiling lines", dele(L_GOK, M_GOK))
s(3, "delete BOTH day/month window lines", dele(L_DAY, M_WIN))
s(4, "delete ALL eight ADD CONSTRAINT lines (columns kept)", dele(L_OPEN, L_GOK, L_AG, L_DAY, "ALTER TABLE spend_month ADD CONSTRAINT spend_month_open_ok CHECK (open_usd >= 0 AND open_usd < 1000000000000::numeric);", M_GOK, M_AG, M_WIN))
s(5, "delete BOTH open_usd ceiling lines", dele(L_OPEN, "ALTER TABLE spend_month ADD CONSTRAINT spend_month_open_ok CHECK (open_usd >= 0 AND open_usd < 1000000000000::numeric);"))
s(6, "BOTH agent regexes allow space and newline", both((L_AG, L_AG.replace("._:@/+-]{0,199}", "._:@/+ \\n-]{0,199}")), (M_AG, M_AG.replace("._:@/+-]{0,199}", "._:@/+ \\n-]{0,199}"))))
s(7, "BOTH usd ceilings -> 1e30", both((L_GOK, L_GOK.replace("1000000000000", "1" + "0" * 30)), (M_GOK, M_GOK.replace("1000000000000", "1" + "0" * 30))))
s(8, "delete agent rule AND ceiling on BOTH tables (four lines)", dele(L_AG, M_AG, L_GOK, M_GOK))
s(9, "duplicate statement (agent rule twice): server must refuse", lambda t: sub(t, L_AG, L_AG + "\n" + L_AG))
s(10, "statement order swapped (day window before agent rule): same set of statements", lambda t: sub(t, L_AG + "\n" + L_DAY, L_DAY + "\n" + L_AG))
s(11, "dollar inside an identifier (x$$) hides two DROP CONSTRAINT statements from a naive dollar-quote scanner", lambda t: t + "\nALTER TABLE spend ADD COLUMN x$$ int; ALTER TABLE spend DROP CONSTRAINT spend_agent_len; ALTER TABLE spend_month DROP CONSTRAINT spend_month_agent_len; ALTER TABLE spend DROP COLUMN x$$;\n")
s(12, "E-string ending in backslash-backslash hides both DROPs (naive scanner sees \\' as an escaped quote)", lambda t: t + "\nSELECT E'\\\\'; ALTER TABLE spend DROP CONSTRAINT spend_agent_len; ALTER TABLE spend_month DROP CONSTRAINT spend_month_agent_len; SELECT E'\\\\';\n")
s(13, "standard string with a trailing backslash ('\\') hides both DROPs", lambda t: t + "\nSELECT '\\'; ALTER TABLE spend DROP CONSTRAINT spend_agent_len; ALTER TABLE spend_month DROP CONSTRAINT spend_month_agent_len; SELECT '\\';\n")
s(14, "nested block comment around a DROP (server: all comment)", lambda t: t + "\n/* a /* b */ ALTER TABLE spend DROP CONSTRAINT spend_agent_len; /* c */ */ SELECT 1;\n")
s(15, "vertical tab and form feed between tokens of a pinned ADD", rep((L_AG, L_AG.replace("ADD CONSTRAINT", "ADD\x0bCONSTRAINT").replace("ALTER TABLE", "ALTER\x0cTABLE"))))
s(16, "non-breaking space between tokens of a pinned ADD (server: syntax error)", rep((L_AG, L_AG.replace("ADD CONSTRAINT", "ADD\u00a0CONSTRAINT"))))
s(17, "plpgsql function that drops the agent rules, called by SELECT", lambda t: t + "\nCREATE FUNCTION hv_x() RETURNS void LANGUAGE plpgsql AS $f$ BEGIN EXECUTE 'ALTER TABLE spend DROP CONSTRAINT spend_agent_len'; EXECUTE 'ALTER TABLE spend_month DROP CONSTRAINT spend_month_agent_len'; END $f$;\nSELECT hv_x();\n")
s(18, "COMMENT ON TABLE spend (harmless)", lambda t: t + "\nCOMMENT ON TABLE spend IS 'x';\n")
s(19, "ADD CONSTRAINT CHECK (false) appended (fail closed: spend unwritable)", lambda t: t + "\nALTER TABLE spend ADD CONSTRAINT hv_false CHECK (false) NOT VALID;\n")
s(20, "TRUNCATE spend appended", lambda t: t + "\nTRUNCATE spend;\n")
s(21, "UPDATE spend SET usd = 0 appended (erase totals)", lambda t: t + "\nUPDATE spend SET usd = 0;\n")
s(22, "UPDATE kill_switch SET on = false appended (release in a migration)", lambda t: t + "\nUPDATE kill_switch SET \"on\" = false;\n")
s(23, "ALTER TABLE kill_switch DISABLE TRIGGER ALL appended", lambda t: t + "\nALTER TABLE kill_switch DISABLE TRIGGER ALL;\n")
s(24, "DROP FUNCTION spend_settle(text,date,numeric,numeric) appended", lambda t: t + "\nDROP FUNCTION spend_settle(text, date, numeric, numeric);\n")
s(25, "second CREATE OR REPLACE of spend_reserve with no ceiling guard (shape-equal, body different)", lambda t: t + "\nCREATE OR REPLACE FUNCTION spend_reserve(p_agent text, p_day date, p_worst numeric) RETURNS TABLE (day_usd numeric, month_usd numeric) LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp BEGIN ATOMIC SELECT 0::numeric, 0::numeric; END;\n")
s(26, "ALTER TABLE spend ADD CONSTRAINT with the ceiling spelled 10^12 via power()", rep((L_GOK, L_GOK.replace("1000000000000::numeric", "power(10::numeric, 20)"))))
s(27, "ceiling as an unqualified call to a user function in public (binding: search_path of the migration)", lambda t: sub(t, L_GOK, "CREATE FUNCTION public.hv_cap() RETURNS numeric LANGUAGE sql IMMUTABLE AS $f$ SELECT 1e30::numeric $f$;\nALTER TABLE spend ADD CONSTRAINT spend_guarded_ok CHECK (usd >= 0 AND usd < hv_cap());"))
s(28, "agent rule through a domain-free regex function: ~ replaced by textregexeq(agent_id, '.*')", rep((L_AG, L_AG.replace(f"agent_id ~ {RX}", "textregexeq(agent_id, '.*')"))))
case("C00", F3, T3, "tplb", "CONTROL: the unmodified DB-3 file")
for cid, note, fn in S:
    try: text = fn(T3)
    except AssertionError as e: print(f"{cid} | {F3} | NOT-RUN spelling does not apply: {e}", flush=True); continue
    case(cid, F3, text, "tplb", note)
# DB-1 files with the month table probed too
N1 = TXT["spend_nonneg.sql"]; N2 = TXT["spend_nonneg_finite.sql"]; N3 = TXT["spend_nonneg_upgrade.sql"]
a = "ALTER TABLE spend ADD CONSTRAINT spend_usd_ok CHECK (usd >= 0);"; b = "ALTER TABLE spend_month ADD CONSTRAINT spend_month_usd_ok CHECK (usd >= 0);"
case("Q01", "spend_nonneg.sql", N1, "tpla", "CONTROL: DB-1 default unmodified (month probed too)", kind="1")
case("Q02", "spend_nonneg.sql", N1.replace(b, ""), "tpla", "DB-1 default: month rule deleted", kind="1")
case("Q03", "spend_nonneg.sql", N1.replace(a, ""), "tpla", "DB-1 default: spend rule deleted", kind="1")
case("Q04", "spend_nonneg_finite.sql", N2, "tpla", "CONTROL: DB-1 finite unmodified", kind="1")
case("Q05", "spend_nonneg_finite.sql", N2.replace("ALTER TABLE spend_month ADD CONSTRAINT spend_month_usd_ok CHECK (usd >= 0 AND usd < 'Infinity'::numeric);", ""), "tpla", "DB-1 finite: month statement deleted", kind="1")
case("Q06", "spend_nonneg_upgrade.sql", N3, "tplc", "CONTROL: DB-1 upgrade unmodified", kind="1")
case("Q07", "spend_nonneg_upgrade.sql", N3.replace("ALTER TABLE spend_month DROP CONSTRAINT spend_month_usd_ok, ADD CONSTRAINT spend_month_usd_ok CHECK (usd >= 0 AND usd < 'Infinity'::numeric);", ""), "tplc", "DB-1 upgrade: month statement deleted (month keeps the default rule: NaN and Infinity accepted)", kind="1")
print(f"CASES RUN: {n_case}", flush=True)
gaps = [c for c in SUMMARY if c[1] and c[2] and c[3]]
print(f"  total={len(SUMMARY)} guard_clean={sum(1 for c in SUMMARY if c[1])} applied={sum(1 for c in SUMMARY if c[2])} weakened={sum(1 for c in SUMMARY if c[3])} CLEAN+APPLIED+WEAKENED={len(gaps)} {[c[0] for c in gaps]}", flush=True)
print("  guard clean AND applied: " + str([c[0] for c in SUMMARY if c[1] and c[2]]), flush=True)
