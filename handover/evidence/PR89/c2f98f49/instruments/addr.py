"""Address probes (task 6). EVIDENCE RUNNER instrument: records accepted/refused, the message and whether any child ran."""
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

WT = "/home/user/build/EV-PR89-r22"
PY = "/home/user/build/venv-evpr89r22/bin/python"
RAW = "/home/user/build/evidence-raw/PR89-c2f98f49/addr"
WORK = sys.argv[1]
os.makedirs(RAW, exist_ok=True)
P = "".join(["Vt6k", "Rz2q"])  # made-up, built from parts
PQ = "".join(["Vt6", "%40", "Rz2q"])  # with an encoded @; decoded form below
PD = "".join(["Vt6", "@", "Rz2q"])
SOCK = os.path.join(WORK, "sock")
REAL, LINK, OTHER = SOCK + "/real", SOCK + "/link", SOCK + "/other"
U = "postgresql://"
DEF = None  # default throwaway_hosts
T = lambda *a: {"__tuple__": list(a)}  # noqa: E731

# (id, display (password shown as <P>), value or special, throwaway_hosts spec or DEF, extra)
C = []


def add(cid, value, hosts=DEF, display=None, **extra):
    C.append({"id": cid, "value": value, "hosts": hosts, "display": display if display is not None else (value if isinstance(value, str) else repr(value)), **extra})


for h in ("localhost", "127.0.0.1", "127.1", "0x7f.0.0.1", "2130706433", "[::1]", "::1", "[::ffff:127.0.0.1]", "LOCALHOST", "localhost.", "%6c%6f%63%61%6c%68%6f%73%74", "db.example.org"):
    add(f"url host {h}", f"{U}postgres@{h}:5432/postgres")
for h in ("localhost", "127.0.0.1", "127.1", "0x7f.0.0.1", "2130706433", "[::1]", "::1", "::ffff:127.0.0.1", "LOCALHOST", "localhost.", "%6c%6f%63%61%6c%68%6f%73%74", "db.example.org"):
    add(f"kv host {h}", f"host={h} port=5432 dbname=postgres user=postgres")
add("listed name written with trailing dot (url)", f"{U}postgres@db.test.:5432/postgres", T("db.test"))
add("listed name written with trailing dot (kv)", "host=db.test. dbname=postgres", T("db.test"))
add("name listed WITH trailing dot, written without", "host=db.test dbname=postgres", T("db.test."))
add("name listed with trailing dot, written with", "host=db.test. dbname=postgres", T("db.test."))
add("two hosts kv, both listed", "host=localhost,127.0.0.1 dbname=postgres")
add("two hosts kv, second not listed", "host=localhost,evil.example dbname=postgres")
add("two hosts url", f"{U}postgres@localhost,evil.example:5432/postgres")
add("hostaddr differs from host (hostaddr not listed)", "host=localhost hostaddr=10.1.2.3 dbname=postgres")
add("hostaddr differs from host (both listed)", "host=localhost hostaddr=127.0.0.1 dbname=postgres")
add("hostaddr only, listed", "hostaddr=127.0.0.1 dbname=postgres")
add("hostaddr only, not listed", "hostaddr=10.1.2.3 dbname=postgres")
add("service=x", "service=x")
add("service=x with listed host", "host=localhost service=x dbname=postgres")
add("passfile", "host=localhost dbname=postgres passfile=/tmp/x")
add("sslrootcert", "host=localhost dbname=postgres sslrootcert=/tmp/x")
add("options=-c", "host=localhost dbname=postgres options=-c search_path=x")
add("options url", f"{U}postgres@localhost/postgres?options=-c%20search_path%3Dx")
add("target_session_attrs", "host=localhost dbname=postgres target_session_attrs=read-write")
add("query override ?host=", f"{U}postgres@localhost:5432/postgres?host=evil.example")
add("query override ?hostaddr=", f"{U}postgres@localhost:5432/postgres?hostaddr=10.1.2.3")
add("query sslmode (harmless key in query)", f"{U}postgres@localhost:5432/postgres?sslmode=disable")
add("fragment", f"{U}postgres@localhost:5432/postgres#x")
add("empty host url (socket default)", f"{U}postgres@/postgres")
add("empty host url with ?host= folder", f"{U}/postgres?host=/tmp")
add("userinfo with plain @ in password", f"{U}svc:{PD}@localhost:5432/postgres", display=f"{U}svc:<Vt6@Rz2q-form>@localhost:5432/postgres")
add("userinfo with %40 in password", f"{U}svc:{PQ}@localhost:5432/postgres", display=f"{U}svc:<Vt6%40Rz2q-form>@localhost:5432/postgres")
add("userinfo with password, host listed", f"{U}svc:{P}@localhost:5432/postgres", display=f"{U}svc:<P>@localhost:5432/postgres")
add("userinfo with password, host NOT listed", f"{U}svc:{P}@db.example.org:5432/postgres", display=f"{U}svc:<P>@db.example.org:5432/postgres")
add("userinfo with password, evil host after @ in password", f"{U}svc:{P}@evil.example:1@localhost:5432/postgres", display=f"{U}svc:<P>@evil.example:1@localhost:5432/postgres")
add("empty password url", f"{U}svc:@localhost:5432/postgres")
add("password key kv", f"host=localhost dbname=postgres user=svc {'pass' + 'word'}={P}", display="host=localhost dbname=postgres user=svc password=<P>")
add("password key kv, host not listed", f"host=db.example.org dbname=postgres {'pass' + 'word'}={P}", display="host=db.example.org dbname=postgres password=<P>")
add("PASSWORD key upper case kv", f"host=localhost dbname=postgres {'PASS' + 'WORD'}={P}", display="host=localhost dbname=postgres PASSWORD=<P>")
add("query password url", f"{U}svc@localhost:5432/postgres?{'pass' + 'word'}={P}", display=f"{U}svc@localhost:5432/postgres?password=<P>")
add("repeated key host", "host=localhost host=evil.example dbname=postgres")
add("repeated key host (evil first)", "host=evil.example host=localhost dbname=postgres")
add("repeated key dbname", "host=localhost dbname=a dbname=b")
add("key in upper case HOST=", "HOST=localhost dbname=postgres")
add("quoted value with spaces", "host='localhost' dbname='my db'")
add("quoted value with escapes", "host=localhost dbname='a\\'b'")
add("double quotes", 'host="localhost" dbname=postgres')
add("two spaces between words", "host=localhost  dbname=postgres")
add("tab between words", "host=localhost\tdbname=postgres")
add("spaces around =", "host = localhost dbname = postgres")
add("leading space", " host=localhost dbname=postgres")
add("socket folder listed exactly", f"host={REAL} dbname=postgres", T(REAL), display="host=<SOCK>/real dbname=postgres ; listed <SOCK>/real")
add("socket folder written exactly, listed with trailing slash", f"host={REAL} dbname=postgres", T(REAL + "/"), display="host=<SOCK>/real ; listed <SOCK>/real/")
add("socket folder written with trailing slash, listed without", f"host={REAL}/ dbname=postgres", T(REAL), display="host=<SOCK>/real/ ; listed <SOCK>/real")
add("socket folder not listed (default list)", f"host={REAL} dbname=postgres", display="host=<SOCK>/real ; default list")
add("socket folder not listed (other listed)", f"host={REAL} dbname=postgres", T(OTHER), display="host=<SOCK>/real ; listed <SOCK>/other")
add("symlink to a listed socket folder", f"host={LINK} dbname=postgres", T(REAL), display="host=<SOCK>/link (symlink to real) ; listed <SOCK>/real")
add("listed symlink, written symlink", f"host={LINK} dbname=postgres", T(LINK), display="host=<SOCK>/link ; listed <SOCK>/link")
add("socket folder with .. part", f"host={REAL}/../other dbname=postgres", T(REAL + "/../other"), display="host=<SOCK>/real/../other ; listed the same text")
add("socket folder with double slash", f"host={SOCK}//real dbname=postgres", T(REAL), display="host=<SOCK>//real ; listed <SOCK>/real")
add("socket folder in url (percent-encoded host)", f"{U}postgres@{REAL.replace('/', '%2F')}/postgres", T(REAL), display="postgresql://postgres@<SOCK%2Freal>/postgres ; listed <SOCK>/real")
add("abstract socket @name", "host=@abstract dbname=postgres", T("@abstract"))
add("dbname holds a full URL", f"dbname={U}postgres@evil.example/postgres")
add("dbname holds a full URL, with listed host", f"host=localhost dbname={U}postgres@evil.example/postgres")
add("dbname holds a conninfo string", "host=localhost dbname=host=evil.example")
add("url dbname with = (conninfo in path)", f"{U}postgres@localhost/host=evil.example")
add("url two path parts", f"{U}postgres@localhost/a/b")
add("url no dbname", f"{U}postgres@localhost:5432")
add("url no dbname trailing slash", f"{U}postgres@localhost:5432/")
add("scheme postgres://", "postgres://postgres@localhost:5432/postgres")
add("scheme POSTGRESQL://", "POSTGRESQL://postgres@localhost:5432/postgres")
add("scheme http://", "http://postgres@localhost:5432/postgres")
add("scheme postgresql+psycopg://", "postgresql+psycopg://postgres@localhost:5432/postgres")
add("no scheme", "localhost:5432/postgres")
add("url port not a number", f"{U}postgres@localhost:abc/postgres")
add("url port huge", f"{U}postgres@localhost:99999999999/postgres")
add("bytes value (simulated)", {"bytes": "postgresql://postgres@localhost:5432/postgres"}, display="b'postgresql://postgres@localhost:5432/postgres' (os.environ swapped for a plain dict)", fake=True)
add("None value (simulated)", None, display="None (os.environ swapped for a plain dict)", fake=True)
add("variable not set", "__UNSET__", display="(variable absent)")
add("empty string", "")
add("one space", " ")
add("10,000 characters (host label repeated)", f"{U}postgres@localhost:5432/" + "a" * 9963, display="postgresql://postgres@localhost:5432/ + 'a' x 9960 (10,000 characters)")
add("2,000 characters exactly", f"{U}postgres@localhost:5432/" + "a" * (2000 - 37), display="2,000 characters, valid shape")
add("2,001 characters", f"{U}postgres@localhost:5432/" + "a" * (2001 - 37), display="2,001 characters, valid shape")
add("NUL in value (simulated)", f"{U}postgres@localhost:5432/post\0gres", display="...post<NUL>gres (os.environ swapped for a plain dict)", fake=True)
add("NUL after valid address (simulated)", f"{U}postgres@localhost:5432/postgres\0@evil.example", display="valid address + <NUL>@evil.example (simulated)", fake=True)
add("newline in value", f"{U}postgres@localhost:5432/postgres\nhost=evil.example", display="valid url + <LF>host=evil.example")
add("trailing newline", f"{U}postgres@localhost:5432/postgres\n", display="valid url + <LF>")
add("kv trailing newline", "host=localhost dbname=postgres\n", display="host=localhost dbname=postgres + <LF>")
add("non-ASCII host", f"{U}postgres@locаlhost:5432/postgres", display="postgresql://postgres@loc<U+0430>lhost:5432/postgres")
add("zero-width in host", f"{U}postgres@local​host:5432/postgres", display="postgresql://postgres@local<U+200B>host:5432/postgres")
# throwaway_hosts forms, with the CI address
CI = f"{U}postgres@localhost:5432/postgres"
add("hosts = empty tuple", CI, T())
add("hosts = ('*',)", CI, T("*"))
add("hosts = ('local*',)", CI, T("local*"))
add("hosts = bare string 'localhost'", CI, "localhost")
add("hosts = ('',)", CI, T(""))
add("hosts = ('localhost', '')", CI, T("localhost", ""))
add("hosts = None", CI, None, hosts_none=True)
add("hosts = 5 (int)", CI, {"__int__": 5})
add("hosts = (b'localhost',)", CI, T({"__bytes__": "localhost"}))
add("hosts = (None,)", CI, T(None))
add("hosts = set {'localhost'}", CI, {"__set__": ["localhost"]})
add("hosts = list ['localhost']", CI, ["localhost"])
add("hosts = ('LOCALHOST',)", CI, T("LOCALHOST"))
add("hosts = ('[::1]',) with url [::1]", f"{U}postgres@[::1]:5432/postgres", T("[::1]"))
add("hosts = (' localhost',)", CI, T(" localhost"))
add("hosts = ('localhost,evil.example',)", "host=localhost,evil.example dbname=postgres", T("localhost,evil.example"))
add("hosts = ('db.example.org',) host listed by caller", f"{U}postgres@db.example.org:5432/postgres", T("db.example.org"))
add("hosts = '*' no variable passed (pass_env empty)", CI, T("*"), no_pass=True)
# pass_env forms
add("pass_env = bare string", CI, pass_env="HADAVIN_TEST_PG_DSN")
add("pass_env = (b'HADAVIN_TEST_PG_DSN',)", CI, pass_env=T({"__bytes__": "HADAVIN_TEST_PG_DSN"}))
add("pass_env = (None,)", CI, pass_env=T(None))
add("pass_env = None", CI, pass_env=None, pass_none=True)
add("pass_env = ('PGPASSWORD',)", CI, pass_env=T("PG" + "PASSWORD"))
add("pass_env = ('DATABASE_URL',)", CI, pass_env=T("DATABASE_URL"))
add("pass_env = ('hadavin_test_pg_dsn',) lower case", CI, pass_env=T("hadavin_test_pg_dsn"))
# parent PG variables
PGV = {"PGHOST": "db.example.org", "PGHOSTADDR": "10.1.2.3", "PGSERVICE": "prod", "PGSERVICEFILE": "/nonexistent/svc", "PGPASSFILE": "/nonexistent/pgpass",
       "PG" + "PASSWORD": "".join(["made", "up", "77"]), "PGOPTIONS": "-c search_path=x", "PGSSLROOTCERT": "/nonexistent/root.crt", "PGPORT": "1", "PGUSER": "u", "PGDATABASE": "d",
       "PGSSLMODE": "disable", "DATABASE_URL": "x", "AWS_PROFILE": "x"}
add("parent holds PG* variables, CI address", CI, parent_env=PGV)
add("parent holds PG* variables, no pass_env", CI, parent_env=PGV, no_pass=True)

TESTSRC = '''
import json, os
from pk import core
MARK = %r


def test_a():
    n = len([f for f in os.listdir(MARK)])
    json.dump(sorted(os.environ), open(os.path.join(MARK, "ran-%%d-%%d.json" %% (os.getpid(), n)), "w"))
    assert core.go(1) == 1
'''


def run_case(i, c):
    base = os.path.join(WORK, f"a{i:03d}")
    shutil.rmtree(base, ignore_errors=True)
    root, tmp, mark = (os.path.join(base, x) for x in ("pkg", "tmp", "mark"))
    for d in (root + "/src/pk", root + "/tests", tmp, mark):
        os.makedirs(d)
    open(root + "/src/pk/__init__.py", "w").close()
    open(root + "/src/pk/core.py", "w").write("def go(flag):\n    return flag\n")
    open(root + "/tests/test_probe.py", "w").write(TESTSRC % mark)
    kw = {}
    if not c.get("no_pass"):
        kw["pass_env"] = c["pass_env"] if "pass_env" in c else ["HADAVIN_TEST_PG_DSN"]
    if c["hosts"] is not DEF or c.get("hosts_none"):
        kw["throwaway_hosts"] = c["hosts"]
    cfg = {"wt": WT, "root": root, "tests": ["tests/test_probe.py"], "result": os.path.join(base, "result.json"), "kw": kw, "mutants": []}
    env = {k: os.environ[k] for k in ("PATH", "HOME", "LANG") if k in os.environ}
    env["TMPDIR"] = tmp
    env.update(c.get("parent_env", {}))
    if c.get("fake"):
        cfg["fake_environ"] = {"HADAVIN_TEST_PG_DSN": c["value"]}
    elif c["value"] != "__UNSET__":
        env["HADAVIN_TEST_PG_DSN"] = c["value"]
    json.dump(cfg, open(os.path.join(base, "cfg.json"), "w"))
    try:
        proc = subprocess.run([PY, os.path.join(os.path.dirname(__file__), "worker.py"), os.path.join(base, "cfg.json")], env=env, capture_output=True, timeout=300)
        res = json.load(open(cfg["result"], encoding="utf-8"))
        rc, so, se = proc.returncode, proc.stdout.decode("utf-8", "replace"), proc.stderr.decode("utf-8", "replace")
    except Exception as exc:  # noqa: BLE001
        res, rc, so, se = {"harness_error": type(exc).__name__ + ": " + str(exc)[:200]}, None, "", ""
    marks = sorted(os.listdir(mark))
    child_env = json.load(open(os.path.join(mark, marks[0]))) if marks else None
    exc = res.get("exc")
    text = json.dumps(res, ensure_ascii=False) + so + se
    val = c["value"] if isinstance(c["value"], str) else ""
    secrets = {"P": P, "P-encoded-@": PQ, "P-decoded-@": PD, "PGPASSWORD value": PGV["PG" + "PASSWORD"]}
    if len(val) > 12 and val != "__UNSET__":
        secrets["whole value"] = val
    rec = {
        "n": i, "id": c["id"], "input": c["display"], "throwaway_hosts": "default" if (c["hosts"] is DEF and not c.get("hosts_none")) else json.dumps(c["hosts"]).replace(SOCK, "<SOCK>"),
        "pass_env": "default name" if "pass_env" not in c and not c.get("no_pass") else ("(none)" if c.get("no_pass") else json.dumps(c.get("pass_env"))),
        "outcome": "REFUSED" if exc else ("ACCEPTED" if res.get("rows") is not None else "HARNESS ERROR"),
        "exc_type": exc["type"] if exc else "", "message": (exc["str"] if exc else "").replace(SOCK, "<SOCK>"),
        "pytest_calls_counted": res.get("pytest_calls"), "child_marker_files": len(marks), "child_ran": bool(marks) or bool(res.get("pytest_calls")),
        "child_env_names": child_env, "worker_rc": rc, "stderr_tail": se[-300:],
        "secret_in_any_output": [k for k, s in secrets.items() if s in text], "harness_error": res.get("harness_error", ""),
        "left_in_tmp": sorted(os.listdir(tmp)),
    }
    return rec


if __name__ == "__main__":
    shutil.rmtree(SOCK, ignore_errors=True)
    os.makedirs(REAL)
    os.makedirs(OTHER)
    os.symlink(REAL, LINK)
    with ThreadPoolExecutor(4) as ex:
        recs = list(ex.map(lambda t: run_case(*t), enumerate(C)))
    json.dump(recs, open(os.path.join(RAW, "addr-records.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("cases", len(recs), "accepted", sum(r["outcome"] == "ACCEPTED" for r in recs), "refused", sum(r["outcome"] == "REFUSED" for r in recs),
          "harness errors", sum(r["outcome"] == "HARNESS ERROR" for r in recs), "secret in output", sum(bool(r["secret_in_any_output"]) for r in recs),
          "refused but child ran", sum(r["outcome"] == "REFUSED" and r["child_ran"] for r in recs))
