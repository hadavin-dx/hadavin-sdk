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


def fresh3(tag, pre_sql=None):
    db = f"dat_{tag}_{secrets.token_hex(2)}"
    tmp = mkdb(db, [(TXT[F2], "0006_dec"), (T3, "0007_x")], template="tpla" if pre_sql else "tplb")
    return db, tmp
def conns(db):
    return psycopg.connect(dsn("migr17", db), autocommit=True), psycopg.connect(dsn("rt17", db), autocommit=True)
def snap(mg): return (mg.execute("SELECT agent_id, day, usd, open_usd FROM spend ORDER BY 1,2").fetchall(), mg.execute("SELECT agent_id, month, usd, open_usd FROM spend_month ORDER BY 1,2").fetchall())
def call(rt, mg, label, q, args):
    before = snap(mg)
    try: rows = rt.execute(q, args).fetchall(); res = f"rows={len(rows)} {[tuple(str(x) for x in r) for r in rows][:1]}"; e = None
    except psycopg.Error as ex: res = "sqlstate=" + str(ex.sqlstate); e = ex.sqlstate
    print(f"DATA {label} | {res} | state_changed={snap(mg) != before}", flush=True)
    return e

print("DATA round 2: month-table rows that exist BEFORE DB-3 (the first run inserted a month that was not the first of a month, a slip of the runner)", flush=True)
grants_select_only(); m.GRANTS["spend_decrease_log"] = m.Grant("table", ""); m.GRANTS["kill_switch_log"] = m.Grant("table", "")
MO = date(2026, 11, 1)
for lbl, ins in (("spend_month row '-unattributed:x'", "INSERT INTO spend_month (agent_id, month, usd) VALUES ('-unattributed:x', %s, 2)"), ("spend_month row '-cli'", "INSERT INTO spend_month (agent_id, month, usd) VALUES ('-cli', %s, 2)"),
                 ("spend_month row with a newline agent", "INSERT INTO spend_month (agent_id, month, usd) VALUES (E'a\\nb', %s, 2)"), ("spend_month row usd 2e12", "INSERT INTO spend_month (agent_id, month, usd) VALUES ('big', %s, 2000000000000)"),
                 ("spend_month row month 1999-01-01", "INSERT INTO spend_month (agent_id, month, usd) VALUES ('old', '1999-01-01', 2)"), ("clean rows only (control: the file applies)", "INSERT INTO spend_month (agent_id, month, usd) VALUES ('fine', %s, 2)")):
    db, tmp = fresh3("p", pre_sql=True)
    mg = psycopg.connect(dsn("migr17", db), autocommit=True)
    try: mg.execute(ins, (MO,)) if "%s" in ins else mg.execute(ins)
    except psycopg.Error as e: print(f"DATA pre-existing {lbl} | could not be inserted before DB-3: {e.sqlstate}", flush=True); drop(db); continue
    res = run_migrate(db, tmp)
    col = mg.execute("SELECT count(*) FROM information_schema.columns WHERE table_name='spend' AND column_name='open_usd'").fetchone()[0]
    led = mg.execute("SELECT count(*) FROM schema_migrations").fetchone()[0]
    print(f"DATA pre-existing {lbl} | apply={res} | open_usd column present={col} | ledger rows={led}", flush=True)
    mg.close(); drop(db)
print("DATA DONE", flush=True)
