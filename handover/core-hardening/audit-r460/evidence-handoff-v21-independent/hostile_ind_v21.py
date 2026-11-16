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

# ======================================================================= DB-3 spellings (target: ADD_PINS_BY_FILE and neighbours)
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
# -- ceiling and range rules
s(1, "ceiling 1e12 -> 1e30 on spend.usd", rep((L_GOK, L_GOK.replace("1000000000000", "1000000000000000000000000000000"))))
s(2, "ceiling -> 1e20 on spend.open_usd", rep((L_OPEN, L_OPEN.replace("open_usd < 1000000000000", "open_usd < 100000000000000000000"))))
s(3, "ceiling written as 1e12*1e9 (arithmetic)", rep((L_GOK, L_GOK.replace("1000000000000::numeric", "(1000000000000::numeric * 1000000000)"))))
s(4, "ceiling replaced by 'Infinity'::numeric", rep((L_GOK, L_GOK.replace("1000000000000::numeric", "'Infinity'::numeric"))))
s(5, "usd >= 0 -> usd >= -1e30 (negative totals allowed)", rep((L_GOK, L_GOK.replace("usd >= 0", "usd >= -1000000000000000000000000000000"))))
s(6, "month table ceiling -> 1e30", rep((M_GOK, M_GOK.replace("1000000000000", "1000000000000000000000000000000"))))
s(7, "CHECK ... OR open_usd > 0 appended (bypass by a second column)", rep((L_GOK, L_GOK.replace("::numeric);", "::numeric OR open_usd > 0);"))))
s(8, "CHECK (true)", rep((L_GOK, "ALTER TABLE spend ADD CONSTRAINT spend_guarded_ok CHECK (true);")))
s(9, "CHECK (usd IS NULL OR usd >= 0) and no ceiling", rep((L_GOK, "ALTER TABLE spend ADD CONSTRAINT spend_guarded_ok CHECK (usd IS NULL OR usd >= 0);")))
s(10, "ceiling comparison flipped: usd < 1e12 -> usd > -1e12 ", rep((L_GOK, L_GOK.replace("usd < 1000000000000::numeric", "usd > -1000000000000::numeric"))))
# -- agent id rule
s(11, "agent regex allows a space: [A-Za-z0-9._:@/+ -]", rep((L_AG, L_AG.replace("._:@/+-]{0,199}", "._:@/+ -]{0,199}"))))
s(12, "agent regex allows newline via \\n in the class", rep((L_AG, L_AG.replace("._:@/+-]{0,199}", "._:@/+\\n-]{0,199}"))))
s(13, "agent regex start anchor removed (unanchored)", rep((L_AG, L_AG.replace("'^[A-Za-z0-9]", "'[A-Za-z0-9]"))))
s(14, "agent regex end anchor removed", rep((L_AG, L_AG.replace("{0,199}$'", "{0,199}'"))))
s(15, "agent operator ~ -> ~* (case-insensitive: harmless) ", rep((L_AG, L_AG.replace("agent_id ~ ", "agent_id ~* "))))
s(16, "agent operator ~ -> !~ (inverted)", rep((L_AG, L_AG.replace("agent_id ~ ", "agent_id !~ "))))
s(17, "agent rule NOT VALID", rep((L_AG, L_AG.replace(");", ") NOT VALID;"))))
s(18, "agent rule: length {0,199} -> {0,99999}", rep((L_AG, L_AG.replace("{0,199}", "{0,9999}"))))
s(19, "agent rule E-string spelling (same meaning)", rep((L_AG, L_AG.replace("~ '^", "~ E'^"))))
s(20, "agent rule dollar-quoted regex (same meaning)", rep((L_AG, L_AG.replace(RX, "$q$^[A-Za-z0-9][A-Za-z0-9._:@/+-]{0,199}$$q$"))))
s(21, "agent rule OR whitespace alternative", rep((L_AG, L_AG.replace(f"~ {RX})", f"~ {RX} OR agent_id ~ '[[:space:]]')"))))
s(22, "agent rule on spend_month only weakened (space allowed)", rep((M_AG, M_AG.replace("._:@/+-]{0,199}", "._:@/+ -]{0,199}"))))
s(23, "agent rule dropped from spend (line deleted)", rep((L_AG, "")))
s(24, "agent rule replaced by CHECK (agent_id <> '')", rep((L_AG, "ALTER TABLE spend ADD CONSTRAINT spend_agent_len CHECK (agent_id <> '');")))
s(25, "agent rule: char_length(agent_id) BETWEEN 1 AND 200 only", rep((L_AG, "ALTER TABLE spend ADD CONSTRAINT spend_agent_len CHECK (char_length(agent_id) BETWEEN 1 AND 200);")))
s(26, "agent rule: IN (SELECT ...) is refused by server; test the guard text only", rep((L_AG, L_AG.replace(f"agent_id ~ {RX}", "agent_id ~ (SELECT 'x')"))))
# -- day window
s(27, "day window upper bound -> 9999-01-01", rep((L_DAY, L_DAY.replace("2100-01-01", "9999-01-01"))))
s(28, "day window lower bound -> 0001-01-01 (year 1)", rep((L_DAY, L_DAY.replace("2020-01-01", "0001-01-01"))))
s(29, "month window removed", rep((M_WIN, "")))
# -- statement spellings of the same constraints
s(30, "lowercase keywords: alter table ... add constraint ... check", rep((L_AG, L_AG.replace("ALTER TABLE", "alter table").replace("ADD CONSTRAINT", "add constraint").replace("CHECK", "check"))))
s(31, "ALTER TABLE ONLY spend ADD ... (agent rule)", rep((L_AG, L_AG.replace("ALTER TABLE spend", "ALTER TABLE ONLY spend"))))
s(32, "ALTER TABLE IF EXISTS spend ADD ... (agent rule)", rep((L_AG, L_AG.replace("ALTER TABLE spend", "ALTER TABLE IF EXISTS spend"))))
s(33, "schema-qualified public.spend (agent rule)", rep((L_AG, L_AG.replace("ALTER TABLE spend", "ALTER TABLE public.spend"))))
s(34, "constraint renamed (agent rule): spend_agent_len -> spend_agent_len2", rep((L_AG, L_AG.replace("spend_agent_len", "spend_agent_len2"))))
s(35, "two ADD CONSTRAINT actions in ONE statement (comma)", rep((L_GOK + "\n" + L_AG, "ALTER TABLE spend ADD CONSTRAINT spend_guarded_ok CHECK (usd >= 0 AND usd < 1000000000000::numeric), ADD CONSTRAINT spend_agent_len CHECK (agent_id ~ 'x');")))
s(36, "comment inside the statement (-- comment line)", rep((L_AG, L_AG.replace("ADD CONSTRAINT", "ADD -- hidden\n CONSTRAINT"))))
s(37, "block comment inside the CHECK expression", rep((L_GOK, L_GOK.replace("usd < 1000000000000", "usd < /* c */ 1000000000000"))))
s(38, "tab and newline whitespace between tokens (same meaning)", rep((L_AG, L_AG.replace("ADD CONSTRAINT", "ADD\t\nCONSTRAINT"))))
s(39, "NO INHERIT added (same meaning on a plain table)", rep((L_AG, L_AG.replace(");", ") NO INHERIT;"))))
s(40, "NOT   VALID with extra spaces and lowercase", rep((L_GOK, L_GOK.replace(");", ")  not   valid ;"))))
s(41, "Cyrillic a in the constraint name (lookalike)", rep((L_AG, L_AG.replace("spend_agent_len", "spend_аgent_len"))))
s(42, "fullwidth parenthesis lookalike inside a comment-only statement appended", lambda t: t + "\n-- ALTER TABLE spend DROP CONSTRAINT spend_agent_len；\n")
# -- extra statements that weaken afterwards
s(43, "DROP CONSTRAINT spend_agent_len appended", lambda t: t + "\nALTER TABLE spend DROP CONSTRAINT spend_agent_len;\n")
s(44, "DROP CONSTRAINT IF EXISTS spend_guarded_ok appended", lambda t: t + "\nALTER TABLE spend DROP CONSTRAINT IF EXISTS spend_guarded_ok;\n")
s(45, "DROP CONSTRAINT spend_month_window appended (lowercase)", lambda t: t + "\nalter table spend_month drop constraint spend_month_window;\n")
s(46, "DROP + ADD in one statement with a weaker CHECK (the upgrade shape)", lambda t: t + "\nALTER TABLE spend DROP CONSTRAINT spend_guarded_ok, ADD CONSTRAINT spend_guarded_ok CHECK (usd >= 0);\n")
s(47, "DISABLE TRIGGER ALL on spend", lambda t: t + "\nALTER TABLE spend DISABLE TRIGGER ALL;\n")
s(48, "ALTER COLUMN usd TYPE real (loses the numeric ceiling meaning)", lambda t: t + "\nALTER TABLE spend ALTER COLUMN usd TYPE double precision;\n")
s(49, "ALTER COLUMN usd DROP NOT NULL", lambda t: t + "\nALTER TABLE spend ALTER COLUMN usd DROP NOT NULL;\n")
s(50, "ADD COLUMN open_usd DEFAULT 1e20 (default over the ceiling)", rep(("ALTER TABLE spend ADD COLUMN open_usd numeric NOT NULL DEFAULT 0;", "ALTER TABLE spend ADD COLUMN open_usd numeric NOT NULL DEFAULT 100000000000000000000;")))
s(51, "ADD COLUMN IF NOT EXISTS open_usd (same meaning)", rep(("ALTER TABLE spend ADD COLUMN open_usd", "ALTER TABLE spend ADD COLUMN IF NOT EXISTS open_usd")))
s(52, "RENAME CONSTRAINT spend_agent_len TO old_len + new weak one", lambda t: t + "\nALTER TABLE spend RENAME CONSTRAINT spend_agent_len TO spend_agent_old;\nALTER TABLE spend ADD CONSTRAINT spend_agent_len CHECK (true);\nALTER TABLE spend DROP CONSTRAINT spend_agent_old;\n")
s(53, "DISABLE ROW LEVEL SECURITY / no-op policy", lambda t: t + "\nALTER TABLE spend DISABLE ROW LEVEL SECURITY;\n")
s(54, "CREATE RULE ... DO INSTEAD NOTHING on spend", lambda t: t + "\nCREATE RULE spend_noop AS ON INSERT TO spend DO INSTEAD NOTHING;\n")
# -- owner, grant and search_path changes
s(55, "ALTER TABLE spend OWNER TO rt17", lambda t: t + "\nALTER TABLE spend OWNER TO rt17;\n")
s(56, "GRANT INSERT, UPDATE ON spend TO rt17", lambda t: t + "\nGRANT INSERT, UPDATE ON spend TO rt17;\n")
s(57, "GRANT ALL ON ALL TABLES IN SCHEMA public TO PUBLIC", lambda t: t + "\nGRANT ALL ON ALL TABLES IN SCHEMA public TO PUBLIC;\n")
s(58, "GRANT EXECUTE ON FUNCTION kill_switch_release() TO rt17", lambda t: t + "\nGRANT EXECUTE ON FUNCTION kill_switch_release() TO rt17;\n")
s(59, "ALTER FUNCTION spend_reserve OWNER TO rt17", lambda t: t + "\nALTER FUNCTION spend_reserve(text, date, numeric) OWNER TO rt17;\n")
s(60, "ALTER FUNCTION spend_reserve SET search_path = public", lambda t: t + "\nALTER FUNCTION spend_reserve(text, date, numeric) SET search_path = public;\n")
s(61, "ALTER FUNCTION spend_settle SECURITY INVOKER", lambda t: t + "\nALTER FUNCTION spend_settle(text, date, numeric, numeric) SECURITY INVOKER;\n")
s(62, "ALTER FUNCTION ... RESET ALL (drops pinned search_path)", lambda t: t + "\nALTER FUNCTION spend_reserve(text, date, numeric) RESET ALL;\n")
s(63, "ALTER ROLE rt17 SET search_path = public (role-level setting)", lambda t: t + "\nALTER ROLE rt17 SET search_path = public;\n")
s(64, "SET search_path = public at the top of the file", lambda t: "SET search_path = public;\n" + t)
s(65, "SET LOCAL search_path = pg_temp, public after lock_timeout", rep(("SET LOCAL lock_timeout = '5s';", "SET LOCAL lock_timeout = '5s';\nSET LOCAL search_path = pg_temp, public;")))
s(66, "set_config('search_path', ..., true) via SELECT", lambda t: t + "\nSELECT pg_catalog.set_config('search_path', 'public', true);\n")
s(67, "ALTER DATABASE ... SET search_path via DO/EXECUTE", lambda t: t + "\nDO $$ BEGIN EXECUTE format('ALTER DATABASE %I SET search_path = public', current_database()); END $$;\n")
s(68, "DO block that drops a constraint via EXECUTE", lambda t: t + "\nDO $$ BEGIN EXECUTE 'ALTER TABLE spend DROP CONSTRAINT spend_agent_len'; END $$;\n")
s(69, "PREPARE + EXECUTE of a DROP CONSTRAINT", lambda t: t + "\nPREPARE hv AS SELECT 1;\n")
s(70, "UPDATE pg_constraint SET convalidated = false (needs a superuser)", lambda t: t + "\nUPDATE pg_catalog.pg_constraint SET convalidated = false WHERE conname = 'spend_agent_len';\n")
s(71, "lock_timeout 5s -> 0 (no timeout)", rep(("SET LOCAL lock_timeout = '5s';", "SET LOCAL lock_timeout = 0;")))
s(72, "statement_timeout 60s -> 0", rep(("SET LOCAL statement_timeout = '60s';", "SET LOCAL statement_timeout = 0;")))
s(73, "SET LOCAL role rt17 mid-file (identity change; later statements run as rt17)", rep(("SET LOCAL statement_timeout = '60s';", "SET LOCAL statement_timeout = '60s';\nSET LOCAL ROLE rt17;")))
# -- function-body spellings next to the pins
s(74, "reserve: guard p_worst > 0 -> p_worst <> 0 (negative reserve)", rep(("SELECT p_agent, p_day, p_worst, p_worst WHERE p_worst > 0", "SELECT p_agent, p_day, p_worst, p_worst WHERE p_worst <> 0")))
s(75, "settle: drop the p_actual >= 0 guard on the first UPDATE", rep(("AND p_worst >= 0 AND p_actual >= 0\n      AND EXISTS (SELECT 1 FROM spend_month y", "AND p_worst >= 0\n      AND EXISTS (SELECT 1 FROM spend_month y")))
s(76, "agent id lower() inside reserve (changes budget identity)", rep(("SELECT p_agent, p_day, p_worst, p_worst WHERE p_worst > 0\n    ON CONFLICT (agent_id, day)", "SELECT lower(p_agent), p_day, p_worst, p_worst WHERE p_worst > 0\n    ON CONFLICT (agent_id, day)")))
s(77, "REVOKE line for kill_switch_release removed", rep(("REVOKE ALL ON FUNCTION kill_switch_release() FROM PUBLIC;", "")))
s(78, "extra SELECT-only function with a SECURITY DEFINER body (data leak shape)", lambda t: t + "\nCREATE OR REPLACE FUNCTION leak_q(q text) RETURNS xml LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $f$ SELECT query_to_xml(q, true, false, '') $f$;\nREVOKE ALL ON FUNCTION leak_q(text) FROM PUBLIC;\nGRANT EXECUTE ON FUNCTION leak_q(text) TO rt17;\n")

print(f"DB-3 SPELLINGS: {len(S)}", flush=True)
# control: unmodified file
case("C00", F3, T3, "tplb", "CONTROL: the unmodified DB-3 file")
for cid, note, fn in S:
    try: text = fn(T3)
    except AssertionError as e: print(f"{cid} | {F3} | NOT-RUN spelling does not apply: {e}", flush=True); continue
    case(cid, F3, text, "tplb", note)

# ======================================================================= other held files
N1 = TXT["spend_nonneg.sql"]; N2 = TXT["spend_nonneg_finite.sql"]; N3 = TXT["spend_nonneg_upgrade.sql"]
OS = []
def o(i, f, tpl, note, fn, kind="1"): OS.append((f"O{i:02d}", f, tpl, note, fn, kind))
a = "ALTER TABLE spend ADD CONSTRAINT spend_usd_ok CHECK (usd >= 0);"
b = "ALTER TABLE spend_month ADD CONSTRAINT spend_month_usd_ok CHECK (usd >= 0);"
o(1, "spend_nonneg.sql", "tpla", "DB-1 default: CHECK (usd >= -5)", lambda: N1.replace(a, a.replace("usd >= 0", "usd >= -5")))
o(2, "spend_nonneg.sql", "tpla", "DB-1 default: NOT VALID", lambda: N1.replace(a, a.replace(");", ") NOT VALID;")))
o(3, "spend_nonneg.sql", "tpla", "DB-1 default: CHECK (usd >= 0 OR true)", lambda: N1.replace(a, a.replace("usd >= 0", "usd >= 0 OR true")))
o(4, "spend_nonneg.sql", "tpla", "DB-1 default: month rule dropped", lambda: N1.replace(b, ""))
o(5, "spend_nonneg.sql", "tpla", "DB-1 default: lowercase + ONLY", lambda: N1.replace(a, a.replace("ALTER TABLE spend", "alter table only spend").replace("ADD CONSTRAINT", "add constraint")))
o(6, "spend_nonneg.sql", "tpla", "DB-1 default: DROP CONSTRAINT appended", lambda: N1 + "\nALTER TABLE spend DROP CONSTRAINT spend_usd_ok;\n")
o(7, "spend_nonneg.sql", "tpla", "DB-1 default: second statement ADD CONSTRAINT other name CHECK (true) plus DROP of first via comma", lambda: N1 + "\nALTER TABLE spend DROP CONSTRAINT spend_usd_ok, ADD CONSTRAINT spend_usd_ok CHECK (true);\n")
o(8, "spend_nonneg.sql", "tpla", "DB-1 default: lock_timeout removed", lambda: N1.replace("SET LOCAL lock_timeout = '5s';", ""))
o(9, "spend_nonneg_finite.sql", "tpla", "DB-1 finite: 'Infinity' -> 'NaN'::numeric bound", lambda: N2.replace("usd < 'Infinity'::numeric", "usd < 'NaN'::numeric"))
o(10, "spend_nonneg_finite.sql", "tpla", "DB-1 finite: bound 'Infinity' -> 1e300 (finite but huge)", lambda: N2.replace("'Infinity'::numeric", "1e300::numeric"))
o(11, "spend_nonneg_finite.sql", "tpla", "DB-1 finite: `OR usd IS NULL`", lambda: N2.replace("usd < 'Infinity'::numeric)", "usd < 'Infinity'::numeric OR usd IS NULL)"))
o(12, "spend_nonneg_finite.sql", "tpla", "DB-1 finite: block comment hides weaker bound", lambda: N2.replace("usd < 'Infinity'::numeric)", "usd /* < 'Infinity'::numeric */ < 'Infinity'::numeric)"))
o(13, "spend_nonneg_upgrade.sql", "tplc", "DB-1 upgrade: ADD part removed (constraint only dropped)", lambda: N3.replace(", ADD CONSTRAINT spend_usd_ok CHECK (usd >= 0 AND usd < 'Infinity'::numeric)", ""))
o(14, "spend_nonneg_upgrade.sql", "tplc", "DB-1 upgrade: re-added as CHECK (usd >= -1)", lambda: N3.replace("spend ADD", "spend ADD").replace("ADD CONSTRAINT spend_usd_ok CHECK (usd >= 0 AND", "ADD CONSTRAINT spend_usd_ok CHECK (usd >= -1 AND"))
o(15, "spend_nonneg_upgrade.sql", "tplc", "DB-1 upgrade: DROP CONSTRAINT IF EXISTS + ADD ... NOT VALID", lambda: N3.replace("DROP CONSTRAINT spend_usd_ok", "DROP CONSTRAINT IF EXISTS spend_usd_ok").replace("'Infinity'::numeric);", "'Infinity'::numeric) NOT VALID;", 1))
o(16, "spend_nonneg_upgrade.sql", "tplc", "DB-1 upgrade: month statement removed", lambda: N3.replace("ALTER TABLE spend_month DROP CONSTRAINT spend_month_usd_ok, ADD CONSTRAINT spend_month_usd_ok CHECK (usd >= 0 AND usd < 'Infinity'::numeric);", ""))
o(17, "spend_nonneg_upgrade.sql", "tplc", "DB-1 upgrade: ceiling 1e12 instead of Infinity (stricter, harmless: control of a legit change)", lambda: N3.replace("'Infinity'::numeric", "1000000000000::numeric"))
D2T = TXT[F2]
o(18, F2, "tpla", "DB-2: ALTER TABLE spend DISABLE TRIGGER ALL appended", lambda: D2T + "\nALTER TABLE spend DISABLE TRIGGER ALL;\n", "2")
o(19, F2, "tpla", "DB-2: ALTER TABLE spend_decrease_log DISABLE TRIGGER spend_decrease_log_append_only appended", lambda: D2T + "\nALTER TABLE spend_decrease_log DISABLE TRIGGER spend_decrease_log_append_only;\n", "2")
o(20, F2, "tpla", "DB-2: ADD CONSTRAINT CHECK (true) on spend_decrease_log appended", lambda: D2T + "\nALTER TABLE spend_decrease_log ADD CONSTRAINT x_ok CHECK (true);\n", "2")
o(21, F2, "tpla", "DB-2: ALTER TABLE spend_decrease_log OWNER TO rt17", lambda: D2T + "\nALTER TABLE spend_decrease_log OWNER TO rt17;\n", "2")
o(22, F2, "tpla", "DB-2: GRANT DELETE ON spend_decrease_log TO rt17", lambda: D2T + "\nGRANT DELETE ON spend_decrease_log TO rt17;\n", "2")
o(23, F2, "tpla", "DB-2: DROP TRIGGER spend_log_decrease ON spend", lambda: D2T + "\nDROP TRIGGER spend_log_decrease ON spend;\n", "2")
o(24, F2, "tpla", "DB-2: ALTER FUNCTION spend_log_decrease() SECURITY INVOKER", lambda: D2T + "\nALTER FUNCTION spend_log_decrease() SECURITY INVOKER;\n", "2")
o(25, F2, "tpla", "DB-2: ALTER FUNCTION spend_log_decrease() SET search_path = public", lambda: D2T + "\nALTER FUNCTION spend_log_decrease() SET search_path = public;\n", "2")
o(26, F2, "tpla", "DB-2: ALTER TABLE spend ADD CONSTRAINT stray CHECK (usd >= -1e30) (unrelated ADD in DB-2)", lambda: D2T + "\nALTER TABLE spend ADD CONSTRAINT stray CHECK (usd >= -1000000000000000000000000000000);\n", "2")
o(27, F2, "tpla", "DB-2: lock_timeout removed", lambda: D2T.replace("SET LOCAL lock_timeout = '5s';", ""), "2")
for cid, f, tpl, note, fn, kind in OS:
    try: text = fn()
    except Exception as e: print(f"{cid} | {f} | NOT-RUN {e}", flush=True); continue
    if text == TXT[f]: print(f"{cid} | {f} | NOT-RUN spelling did not change the file", flush=True); continue
    case(cid, f, text, tpl, note, kind=kind)

print(f"CASES RUN: {n_case}", flush=True)
print("SUMMARY-LINES (id, guard clean, applied by real migrate(), weakened by probes):")
gaps = [c for c in SUMMARY if c[1] and c[2] and c[3]]
print(f"  total={len(SUMMARY)} guard_clean={sum(1 for c in SUMMARY if c[1])} applied={sum(1 for c in SUMMARY if c[2])} weakened={sum(1 for c in SUMMARY if c[3])} CLEAN+APPLIED+WEAKENED={len(gaps)} {[c[0] for c in gaps]}", flush=True)
print("  guard clean AND applied (any): " + str([c[0] for c in SUMMARY if c[1] and c[2]]), flush=True)
