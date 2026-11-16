import json, os, socket, sqlite3, subprocess, sys, threading, time, urllib.request, shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).parent
PY = r"C:\Users\rakes\Downloads\Hadavin\_local\scratch\venv-dpld-int\Scripts\python.exe"
DP, FP = 18701, 18702
OUT = ROOT / "_hostile_rows.jsonl"
DBDIR = ROOT / "_hdata"
procs = {}
ROWS = []
N = [0]


def env():
    e = dict(os.environ)
    e["PYTHONPATH"] = f"{ROOT/'src'}{os.pathsep}{ROOT}"
    e.update(DESK_PORT=str(DP), DESK_FAKES_PORT=str(FP), DESK_BIND="127.0.0.1")
    return e


def start_fakes():
    procs["f"] = subprocess.Popen([PY, "-m", "demo_only.fakes_server", "--outbox", "blind", "--crm", "blind", "--port", str(FP)],
                                  cwd=ROOT, env=env(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{FP}/fake/info", timeout=1).read(); return
        except Exception:
            time.sleep(0.2)
    raise SystemExit("fakes did not start")


def start_desk():
    N[0] += 1
    DBDIR.mkdir(exist_ok=True)
    e = env(); e["DESK_DB_PATH"] = str(DBDIR / f"d{N[0]}.sqlite3")
    procs["d"] = subprocess.Popen([PY, "-m", "lead_desk.server"], cwd=ROOT, env=e,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    procs["db"] = e["DESK_DB_PATH"]
    for _ in range(50):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{DP}/counts", timeout=1).read(); return
        except Exception:
            time.sleep(0.2)
    raise SystemExit("desk did not start")


def stop_desk():
    p = procs.get("d")
    if p and p.poll() is None:
        p.terminate()
        try: p.wait(5)
        except Exception: p.kill()


def fresh():
    stop_desk()
    urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{FP}/fake/reset", data=b"{}", method="POST"), timeout=3).read()
    start_desk()


def raw(data, timeout=8, shutdown=False, chunks=None):
    """send bytes, read until close/timeout. returns (head, body, elapsed, state)"""
    t = time.time(); buf = b""; st = "closed"
    try:
        s = socket.create_connection(("127.0.0.1", DP), timeout=timeout)
        s.settimeout(timeout)
        if chunks:
            for c in chunks: s.sendall(c)
        else:
            s.sendall(data)
        if shutdown: s.shutdown(socket.SHUT_WR)
        while True:
            b = s.recv(65536)
            if not b: break
            buf += b
            if len(buf) > 2_000_000: break
    except socket.timeout:
        st = "timeout"
    except OSError as e:
        st = "err:" + type(e).__name__
    finally:
        try: s.close()
        except Exception: pass
    el = time.time() - t
    head, _, body = buf.partition(b"\r\n\r\n")
    line = head.split(b"\r\n")[0].decode("latin1") if head else ""
    return line, body.decode("utf8", "replace"), el, st


def post(path, body, extra=b"", ctype=True, **kw):
    req = b"POST " + path.encode() + b" HTTP/1.1\r\nHost: x\r\n" + (b"Content-Type: application/json\r\n" if ctype else b"") + \
          b"Content-Length: " + str(len(body)).encode() + b"\r\n" + extra + b"\r\n" + body
    return raw(req, **kw)


def get(path, **kw):
    return raw(b"GET " + path.encode("latin1") + b" HTTP/1.1\r\nHost: x\r\n\r\n", **kw)


def env_(ref, payload, source="form"):
    return json.dumps({"source": source, "source_ref": ref, "payload": payload}).encode()


def js(url):
    try: return json.loads(urllib.request.urlopen(url, timeout=5).read())
    except Exception as e: return {"err": type(e).__name__}


def state():
    time.sleep(0.6)
    c = js(f"http://127.0.0.1:{DP}/counts")
    try:
        con = sqlite3.connect("file:" + procs["db"].replace("\\", "/") + "?mode=ro", uri=True, timeout=3)
        r = con.execute("select count(*) from receipts").fetchone()[0]
        o = con.execute("select count(*) from receipts where outcome is null").fetchone()[0]
        l = con.execute("select count(*) from leads").fetchone()[0]
        dk = con.execute("select count(*) from (select email_key from leads group by email_key having count(*)>1)").fetchone()[0]
        fs = dict(con.execute("select state,count(*) from followups group by state").fetchall())
        con.close()
    except Exception as e:
        r = o = l = dk = fs = "db:" + type(e).__name__
    crm = js(f"http://127.0.0.1:{FP}/fake/crm").get("count")
    ob = js(f"http://127.0.0.1:{FP}/fake/outbox").get("count")
    alive = procs["d"].poll() is None
    return dict(receipts=r, open=o, leads=l, dupkeys=dk, fu=fs, crm=crm, outbox=ob, alive=alive,
                counts={k: c.get(k) for k in ("received", "new", "duplicate", "review", "open", "rejected_envelopes")})


def sstr(s):
    return f"rcpt={s['receipts']} open={s['open']} leads={s['leads']} crm={s['crm']} mail={s['outbox']} fu={s['fu']} alive={s['alive']}"


def rec(cls, attack, line, body, el, st, snap=True, note=""):
    s = state() if snap else None
    an = []
    code = line.split(" ")[1] if line.count(" ") >= 1 else ""
    if code.startswith("5") and code != "501": an.append(f"5xx {code}")
    if el > 5: an.append(f"slow {el:.1f}s")
    if st != "closed": an.append(f"conn {st}")
    if not line and st == "closed": an.append("no reply")
    if s:
        if not s["alive"]: an.append("DESK DEAD")
        if isinstance(s["crm"], int) and isinstance(s["leads"], int) and s["crm"] > s["leads"]: an.append("CRM rows>leads")
        if isinstance(s["outbox"], int) and isinstance(s["leads"], int) and s["outbox"] > s["leads"]: an.append("mails>leads")
        if s["dupkeys"]: an.append("dup email_key")
    row = dict(cls=cls, attack=attack, resp=f"{line} | {body[:300]!r} | {el:.2f}s {st}", state=sstr(s) if s else "-", anomaly="; ".join(an) or "-", note=note)
    ROWS.append(row)
    with OUT.open("a", encoding="utf8") as f: f.write(json.dumps(row) + "\n")
    print(cls, attack[:60], line, an, flush=True)
    return s


def alive_note(cls):
    ok = False
    try:
        t = time.time(); urllib.request.urlopen(f"http://127.0.0.1:{DP}/counts", timeout=5).read(); ok = True; d = time.time() - t
    except Exception as e:
        d = -1
    a = procs["d"].poll() is None
    row = dict(cls=cls, attack="[class end] liveness", resp=f"/counts ok={ok} {d:.2f}s", state=f"process alive={a}", anomaly="-" if ok and a else "NOT RESPONDING", note="restart needed: " + ("no" if ok and a else "yes"))
    ROWS.append(row)
    with OUT.open("a", encoding="utf8") as f: f.write(json.dumps(row) + "\n")
    print(cls, "liveness", ok, a, flush=True)
    if not (ok and a):
        stop_desk(); start_desk()


GOOD = {"name": "Ada", "email": "ada@example.test"}


def lead(ref, payload=None, **kw):
    return post("/leads", env_(ref, payload if payload is not None else GOOD), **kw)


def main():
    OUT.write_text("") if not os.environ.get("SKIPA") else None
    shutil.rmtree(DBDIR, ignore_errors=True)
    start_fakes()
    try:
        classes()
    finally:
        stop_desk()
        if procs.get("f"): procs["f"].terminate()


def classes():
    if not os.environ.get("SKIPA"):
        # ---- A size and framing
        fresh(); C = "A size/framing"
        pad = lambda n: env_("a1", {"name": "Ada", "email": "ada@example.test", "message": "x" * 1}).replace(b'"x"', b'"' + b"x" * n + b'"')
        base = len(env_("a1", {"name": "Ada", "email": "ada@example.test", "message": ""}))
        cap = 65536
        b_cap = env_("a-cap", {"name": "Ada", "email": "cap@example.test", "message": "x" * (cap - len(env_("a-cap", {"name": "Ada", "email": "cap@example.test", "message": ""})))})
        rec(C, f"body exactly {len(b_cap)} bytes (cap 65536), valid envelope but message>2000", *post("/leads", b_cap))
        b_cap1 = b_cap + b" "
        rec(C, f"body {len(b_cap1)} bytes (cap+1)", *post("/leads", b_cap1))
        rec(C, "body 10 MB of 'x'", *post("/leads", b"x" * 10_000_000, timeout=20))
        rec(C, "chunked, no Content-Length", *raw(b"POST /leads HTTP/1.1\r\nHost: x\r\nTransfer-Encoding: chunked\r\n\r\n" + hex(len(env_("c1", GOOD)))[2:].encode() + b"\r\n" + env_("c1", GOOD) + b"\r\n0\r\n\r\n"))
        body = env_("cl1", GOOD)
        rec(C, "Content-Length larger than body (+50), client keeps socket open", *raw(b"POST /leads HTTP/1.1\r\nHost: x\r\nContent-Length: " + str(len(body) + 50).encode() + b"\r\n\r\n" + body, timeout=40))
        rec(C, "Content-Length smaller than body (-10)", *raw(b"POST /leads HTTP/1.1\r\nHost: x\r\nContent-Length: " + str(len(body) - 10).encode() + b"\r\n\r\n" + body, timeout=10))
        rec(C, "Content-Length: -5", *raw(b"POST /leads HTTP/1.1\r\nHost: x\r\nContent-Length: -5\r\n\r\n" + body))
        rec(C, "Content-Length: abc", *raw(b"POST /leads HTTP/1.1\r\nHost: x\r\nContent-Length: abc\r\n\r\n" + body))
        rec(C, "Content-Length: 99999999999999999999", *raw(b"POST /leads HTTP/1.1\r\nHost: x\r\nContent-Length: 99999999999999999999\r\n\r\n" + body, timeout=10))
        rec(C, "two Content-Length headers (len, len+5)", *raw(b"POST /leads HTTP/1.1\r\nHost: x\r\nContent-Length: " + str(len(body)).encode() + b"\r\nContent-Length: " + str(len(body) + 5).encode() + b"\r\n\r\n" + body, timeout=10))
        rec(C, "no Content-Length on POST /leads", *raw(b"POST /leads HTTP/1.1\r\nHost: x\r\n\r\n" + body, timeout=6))
        rec(C, "Content-Length: 0", *raw(b"POST /leads HTTP/1.1\r\nHost: x\r\nContent-Length: 0\r\n\r\n"))
        rec(C, "Content-Length with unicode digit (arabic-indic 5)", *raw(b"POST /leads HTTP/1.1\r\nHost: x\r\nContent-Length: \xd9\xa5\r\n\r\n" + body))
        rec(C, "header block 100 KB", *raw(b"GET /counts HTTP/1.1\r\nHost: x\r\nX-A: " + b"a" * 100_000 + b"\r\n\r\n"))
        rec(C, "200 headers", *raw(b"GET /counts HTTP/1.1\r\nHost: x\r\n" + b"".join(b"X-%d: 1\r\n" % i for i in range(200)) + b"\r\n"))
        rec(C, "request line 70 KB", *raw(b"GET /" + b"a" * 70000 + b" HTTP/1.1\r\nHost: x\r\n\r\n"))
        alive_note(C)

    # ---- B slow clients / many connections
    fresh(); C = "B slowloris/connections"
    socks = []
    for i in range(20):
        s = socket.create_connection(("127.0.0.1", DP)); s.sendall(b"POST /leads HTTP/1.1\r\nHost: x\r\nContent-Le"); socks.append(s)
    t = time.time(); r = get("/counts", timeout=10)
    rec(C, "20 stuck connections (partial header); GET /counts meanwhile", *r)
    socks2 = []
    for i in range(20):
        s = socket.create_connection(("127.0.0.1", DP)); s.sendall(b"POST /leads HTTP/1.1\r\nHost: x\r\nContent-Length: 500\r\n\r\n{\"source\":"); socks2.append(s)
    rec(C, "20 more stuck connections (slow body, CL 500); POST valid lead meanwhile", *lead("b1", {"name": "Ada", "email": "b1@example.test"}, timeout=10))
    t0 = time.time()
    # wait for server socket timeout (30s) to reap
    time.sleep(33)
    closed = 0
    for s in socks + socks2:
        s.settimeout(1)
        try:
            d = s.recv(1000)
            closed += 1 if d == b"" or d.startswith(b"HTTP") else 0
        except Exception: pass
        s.close()
    rec(C, "after 33 s: how many of the 40 stuck sockets were closed/answered by server", "", f"closed_or_answered={closed}/40", time.time() - t0, "closed", note="server socket timeout is 30 s")
    alive_note(C)
    socks = []
    ok = 0; fail = 0
    for i in range(200):
        try:
            s = socket.create_connection(("127.0.0.1", DP), timeout=3); socks.append(s); ok += 1
        except Exception: fail += 1
    t = time.time(); r = get("/counts", timeout=12)
    rec(C, f"200 idle connections left open (connected {ok}, failed {fail}); GET /counts", *r)
    rec(C, "same: POST valid lead", *lead("b2", {"name": "Ada", "email": "b2@example.test"}, timeout=12))
    time.sleep(32)
    r = get("/counts", timeout=10)
    rec(C, "200 idle sockets after 32 s; GET /counts", *r)
    for s in socks: s.close()
    alive_note(C)

    # ---- C encoding / parser
    fresh(); C = "C encoding/parser"
    E = lambda ref, b: post("/leads", b)
    rec(C, "invalid UTF-8 in name (\\xff\\xfe)", *post("/leads", b'{"source":"form","source_ref":"c1","payload":{"name":"A\xff\xfe","email":"c1@example.test"}}'))
    rec(C, "UTF-8 BOM before JSON", *post("/leads", b"\xef\xbb\xbf" + env_("c2", {"name": "Ada", "email": "c2@example.test"})))
    rec(C, "NUL byte inside name (raw)", *post("/leads", b'{"source":"form","source_ref":"c3","payload":{"name":"A\x00da","email":"c3@example.test"}}'))
    rec(C, "NUL escaped (\\u0000) in name", *lead("c4", {"name": "A\u0000da", "email": "c4@example.test"}))
    rec(C, "NUL in source_ref", *post("/leads", env_("c\u00005", {"name": "Ada", "email": "c5@example.test"})))
    rec(C, "lone surrogate escape in name", *post("/leads", b'{"source":"form","source_ref":"c6","payload":{"name":"\\ud800","email":"c6@example.test"}}'))
    for d in (100, 10000, 100000):
        nested = b'{"a":' * d + b"1" + b"}" * d
        rec(C, f"nested JSON depth {d} as whole body", *post("/leads", nested, timeout=15))
        pl = b'{"source":"form","source_ref":"cn%d","payload":{"name":"Ada","email":"cn%d@example.test","x":' % (d, d) + b"[" * d + b"]" * d + b"}}"
        rec(C, f"nested array depth {d} inside payload", *post("/leads", pl, timeout=15))
    rec(C, "huge number 1e999 / 10^5000 digits in extra field", *post("/leads", b'{"source":"form","source_ref":"c7","payload":{"name":"Ada","email":"c7@example.test","n":1e999,"m":' + b"9" * 5000 + b"}}"))
    rec(C, "huge int as name", *post("/leads", b'{"source":"form","source_ref":"c8","payload":{"name":' + b"9" * 4500 + b',"email":"c8@example.test"}}'))
    rec(C, "duplicate keys (email twice, different values)", *post("/leads", b'{"source":"form","source_ref":"c9","payload":{"name":"Ada","email":"first@example.test","email":"second@example.test"}}'))
    rec(C, "duplicate source key (webhook then form)", *post("/leads", b'{"source":"webhook","source":"form","source_ref":"c10","payload":{"name":"Ada","email":"c10@example.test"}}'))
    rec(C, "payload is list / string / null", *post("/leads", b'{"source":"form","source_ref":"c11","payload":[1]}'))
    rec(C, "source_ref int / 129 chars / 128 chars / empty", *post("/leads", b'{"source":"form","source_ref":5,"payload":{}}'))
    rec(C, "source_ref 129 chars", *lead("r" * 129))
    rec(C, "source_ref 128 chars", *lead("r" * 128, {"name": "Ada", "email": "c12@example.test"}))
    rec(C, "name is number / email is list", *lead("c13", {"name": 5, "email": ["a@b.com"]}))
    rec(C, "name 201 chars", *lead("c14", {"name": "n" * 201, "email": "c14@example.test"}))
    rec(C, "message 2001 chars", *lead("c15", {"name": "Ada", "email": "c15@example.test", "message": "m" * 2001}))
    rec(C, "Content-Type text/plain with valid JSON", *post("/leads", env_("c16", {"name": "Ada", "email": "c16@example.test"}), ctype=False))
    rec(C, "JSON top-level array / string / number", *post("/leads", b"[1,2]"))
    rec(C, "empty object {}", *post("/leads", b"{}"))
    rec(C, "emoji + RTL override in name", *lead("c17", {"name": "\u202eAda\U0001F600", "email": "c17@example.test"}))
    alive_note(C)

    # ---- D email identity
    fresh(); C = "D email twins"
    def L(tag, email, ref=None, name="Ada"):
        return lead(ref or f"d-{tag}", {"name": name, "email": email})
    rec(C, "base ada@example.test", *L("base", "ada@example.test"))
    rec(C, "ADA@EXAMPLE.TEST (uppercase)", *L("up", "ADA@EXAMPLE.TEST"))
    rec(C, "' ada@example.test ' (spaces)", *L("sp", "  ada@example.test  "))
    rec(C, "tab-wrapped email", *L("tab", "\tada@example.test\t"))
    rec(C, "ada+tag@example.test (plus)", *L("plus", "ada+tag@example.test"))
    rec(C, "a.da@example.test vs ada (dots)", *L("dot", "a.da@example.test"))
    rec(C, "trailing CRLF in email (JSON \\r\\n)", *L("crlf", "ada@example.test\r\n"))
    rec(C, "CRLF injection a@b.com\\r\\nBcc: v@evil.test", *L("inj", "a@b.com\r\nBcc: v@evil.test"))
    rec(C, "CRLF injection in name", *lead("d-injname", {"name": "Ada\r\nBcc: v@evil.test", "email": "inj2@example.test"}))
    rec(C, "email with embedded space", *L("esp", "ada @example.test"))
    rec(C, "NFC vs NFD: josé@example.test NFC", *L("nfc", "jos\u00e9@example.test"))
    rec(C, "NFD josé@example.test (e + U+0301)", *L("nfd", "jose\u0301@example.test"))
    rec(C, "full-width @ (U+FF20): ada＠example.test", *L("fw", "ada\uff20example.test"))
    rec(C, "full-width letters ａｄａ@example.test", *L("fwl", "\uff41\uff44\uff41@example.test"))
    rec(C, "Turkish dotted İ: İ@example.test", *L("tri", "\u0130@example.test"))
    rec(C, "dotless ı@example.test vs i@example.test", *L("dl", "\u0131@example.test"))
    rec(C, "i@example.test", *L("i", "i@example.test"))
    rec(C, "zero-width space in local part", *L("zw", "ad\u200ba@example.test"))
    rec(C, "zero-width joiner / BOM in email", *L("zwj", "\ufeffada@example.test"))
    rec(C, "NBSP around email", *L("nbsp", "\u00a0ada@example.test\u00a0"))
    rec(C, "Kelvin sign K@example.test (lowercases to k)", *L("kel", "\u212a@example.test"))
    rec(C, "k@example.test", *L("k", "k@example.test"))
    rec(C, "ß@example.test vs SS@example.test", *L("ss", "\u00df@example.test"))
    rec(C, "IDN domain ada@exämple.test vs punycode", *L("idn", "ada@ex\u00e4mple.test"))
    rec(C, "punycode ada@xn--exmple-cua.test", *L("puny", "ada@xn--exmple-cua.test"))
    loc = "a" * 64
    e254 = loc + "@" + "b" * 63 + "." + "c" * 63 + "." + "d" * (254 - 64 - 1 - 64 - 64 - 1)  # build to 254
    e254 = (loc + "@" + "b" * 63 + "." + "c" * 63 + "." + "dd")
    pad = 254 - len(e254)
    e254 = loc + "@" + "b" * 63 + "." + "c" * 63 + "." + "d" * (2 + pad)
    rec(C, f"email {len(e254)} chars", *L("254", e254))
    rec(C, f"email {len(e254)+1} chars", *L("255", e254 + "d"))
    rec(C, "email 300 chars", *L("300", "x" * 290 + "@example.test"))
    rec(C, "email with angle brackets <a@b.com>", *L("ang", "<a@b.com>"))
    rec(C, "email 'a@b' (no dot)", *L("nodot", "a@b"))
    rec(C, "two @", *L("2at", "a@b@c.com"))
    rec(C, "quoted local \"a b\"@x.com", *L("quo", '"a b"@x.com'))
    rec(C, "trailing dot ada@example.test.", *L("tdot", "ada@example.test."))
    rec(C, "email keys 'İ' lower() length twin: ß->ss? (done above)", "", "see rows above", 0, "closed", snap=True)
    alive_note(C)

    # ---- E SQL / path chars
    fresh(); C = "E SQL metachar/%00"
    sql = "'; DROP TABLE leads;--"
    rec(C, "SQL in every field", *lead("e1", {"name": sql, "email": "e1@example.test", "phone": sql, "company": sql, "message": sql}))
    rec(C, "SQL in email local part", *lead("e2", {"name": "Ada", "email": "x'or'1'='1@example.test"}))
    rec(C, "SQL in source_ref", *lead("e3' OR '1'='1", {"name": "Ada", "email": "e3@example.test"}))
    rec(C, "source_ref with %00 literal text and NUL", *lead("e4%00x\u0000y", {"name": "Ada", "email": "e4@example.test"}))
    rec(C, "%00 in email field", *lead("e5", {"name": "Ada%00", "email": "e5%00@example.test"}))
    rec(C, "double quotes/backslash/LIKE chars % _ in name", *lead("e6", {"name": '"\\%_', "email": "e6@example.test"}))
    rec(C, "GET /leads/L' OR '1'='1", *get("/leads/L'%20OR%20'1'='1"))
    rec(C, "GET /leads/%00", *get("/leads/%00"))
    rec(C, "GET /leads/L%00abc", *get("/leads/L%00abc"))
    rec(C, "GET /leads/ (trailing slash)", *get("/leads/"))
    rec(C, "GET /leads/%25 /leads/%", *get("/leads/%25"))
    rec(C, "GET /leads/<script>", *get("/leads/%3Cscript%3E"))
    rec(C, "POST /review/F' OR 1=1--/resolve", *post("/review/F'%20OR%201=1--/resolve", b'{"decision":"sent"}'))
    rec(C, "POST /review/R%00/retry", *post("/review/R%00/retry", b""))
    rec(C, "GET /counts?expected=1;DROP", *get("/counts?expected=1;DROP"))
    rec(C, "GET /counts?expected=99999999999999999999999", *get("/counts?expected=99999999999999999999999"))
    rec(C, "GET /counts?expected=%00", *get("/counts?expected=%00"))
    rec(C, "GET /counts?expected=٥ (arabic digit)", *get("/counts?expected=%D9%A5"))
    rec(C, "GET /counts?expected=5&expected=x", *get("/counts?expected=5&expected=x"))
    rec(C, "GET /leads/ with 100k id", *get("/leads/" + "L" * 100000))
    rec(C, "state after SQL attempts: GET /review", *get("/review"))
    alive_note(C)

    # ---- F routes, methods, traversal
    fresh(); C = "F routes/methods/traversal"
    lead("f0", {"name": "Ada", "email": "f0@example.test"}); time.sleep(1)
    for p in ["/review/../..", "/review/%2e%2e/", "/review/%2e%2e/%2e%2e/etc/passwd", "/review/..%2f..%2fcounts", "/leads/../counts", "/leads/%2e%2e/counts", "/review/..;/", "//review", "/review//", "/counts/", "/counts/../review", "/%2e%2e/%2e%2e/windows/win.ini", "/leads/..\\..\\x", "/review/F1/../retry", "/review/%252e%252e/retry", "/leads/a/b", "/review/x/y/z", "/COUNTS", "/leads%00", "/counts%3Fexpected=1", "/ ", "/counts#frag", "http://evil.test/counts", "*"]:
        rec(C, f"GET {p}", *raw(b"GET " + p.encode("latin1", "replace") + b" HTTP/1.1\r\nHost: x\r\n\r\n"))
    routes = [("/leads", "POST"), ("/leads/Lxxxxxxxxxxxx", "GET"), ("/review", "GET"), ("/review/F1/retry", "POST"), ("/review/F1/resolve", "POST"), ("/counts", "GET")]
    for path, ok in routes:
        for m in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE", "CONNECT", "FOO"]:
            if m == ok: continue
            rec(C, f"{m} {path}", *raw(f"{m} {path} HTTP/1.1\r\nHost: x\r\nContent-Length: 2\r\n\r\n{{}}".encode(), timeout=8), snap=False)
    rec(C, "(state after all wrong-method calls)", "", "", 0, "closed")
    rec(C, "HTTP/0.9 'GET /counts' (no version)", *raw(b"GET /counts\r\n", timeout=6))
    rec(C, "HTTP/0.9 'GET /counts' LF only", *raw(b"GET /counts\n", timeout=6))
    rec(C, "garbage bytes", *raw(b"\x00\x01\x02\xff\xfe\r\n\r\n"))
    rec(C, "HTTP/2 preface PRI * HTTP/2.0", *raw(b"PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n"))
    rec(C, "HTTP/9.9 version", *raw(b"GET /counts HTTP/9.9\r\nHost: x\r\n\r\n"))
    rec(C, "pipelined: two GET /counts in one packet", *raw(b"GET /counts HTTP/1.1\r\nHost: x\r\n\r\nGET /counts HTTP/1.1\r\nHost: x\r\n\r\n"))
    b1 = env_("p1", {"name": "Ada", "email": "p1@example.test"}); b2 = env_("p2", {"name": "Bob", "email": "p2@example.test"})
    rq = lambda b: b"POST /leads HTTP/1.1\r\nHost: x\r\nContent-Length: " + str(len(b)).encode() + b"\r\n\r\n" + b
    rec(C, "pipelined: two POST /leads in one packet (p1,p2)", *raw(rq(b1) + rq(b2)))
    rec(C, "smuggling: CL body followed by 2nd request inside body", *raw(rq(env_("p3", {"name": "Ada", "email": "p3@example.test"}) ) + rq(env_("p4", {"name": "Eve", "email": "p4@example.test"}))))
    rec(C, "header injection: bare LF in header / folded header", *raw(b"GET /counts HTTP/1.1\r\nHost: x\nX-Y: a\r\n b\r\n\r\n"))
    rec(C, "header with CR only, NUL in header value", *raw(b"GET /counts HTTP/1.1\r\nHost: x\r\nX-Y: a\x00b\rc\r\n\r\n"))
    rec(C, "Expect: 100-continue on POST /leads", *post("/leads", env_("p5", {"name": "Ada", "email": "p5@example.test"}), extra=b"Expect: 100-continue\r\n"))
    rec(C, "Host header missing / duplicate / huge", *raw(b"GET /counts HTTP/1.1\r\n\r\n"))
    rec(C, "Connection: keep-alive then 2nd request on same socket", *raw(b"GET /counts HTTP/1.1\r\nHost: x\r\nConnection: keep-alive\r\n\r\nGET /review HTTP/1.1\r\nHost: x\r\n\r\n"))
    alive_note(C)

    # ---- G concurrency / replay
    fresh(); C = "G concurrency/replay"
    A = {"name": "Ada", "email": "g1@example.test", "phone": "111"}
    rec(C, "replay: first g-rep", *lead("g-rep", A))
    rec(C, "replay same id, changed payload (phone 222, name Eve)", *lead("g-rep", {"name": "Eve", "email": "g1@example.test", "phone": "222"}))
    rec(C, "replay same id, changed email", *lead("g-rep", {"name": "Ada", "email": "other@example.test"}))
    rec(C, "replay same id, other source (webhook) same ref", *post("/leads", env_("g-rep", A, source="webhook")))
    rec(C, "replay same id, key order changed", *post("/leads", b'{"payload":{"phone":"111","email":"g1@example.test","name":"Ada"},"source_ref":"g-rep","source":"form"}'))
    rec(C, "replay same id, whitespace-changed values", *lead("g-rep", {"name": " Ada ", "email": " g1@example.test ", "phone": "111"}))
    rec(C, "new id, same email, new phone", *lead("g-new", {"name": "Ada", "email": "g1@example.test", "phone": "333"}))
    # 1000 ids same email parallel
    def one(i):
        try:
            l, b, el, st = lead(f"par-{i}", {"name": "Par", "email": "par@example.test"}, timeout=40)
            return l.split(" ")[1] if " " in l else l or st
        except Exception as e:
            return "EXC"
    t = time.time()
    with ThreadPoolExecutor(100) as ex: res = list(ex.map(one, range(1000)))
    from collections import Counter
    cnt = Counter(res)
    rec(C, "1000 distinct request ids, same email, 100 parallel workers", "", f"status counts {dict(cnt)}", time.time() - t, "closed")
    # retry the failed/busy ones until all received
    retry_n = 0
    for i, r in enumerate(res):
        if r not in ("200", "201"):
            retry_n += 1
            for _ in range(5):
                l, *_ = lead(f"par-{i}", {"name": "Par", "email": "par@example.test"}, timeout=20)
                if " " in l and l.split(" ")[1] in ("200", "201"): break
                time.sleep(0.2)
    rec(C, f"re-sent the {retry_n} non-2xx ids of the 1000 (up to 5 tries)", "", f"retried={retry_n}", 0, "closed")
    rec(C, "GET /counts?expected=1002 after 1000 + 2 earlier lead rows", *get("/counts"))
    # concurrent same id, same payload x50
    def same(_): return lead("g-same", {"name": "Same", "email": "same@example.test"}, timeout=40)[0]
    with ThreadPoolExecutor(50) as ex: r2 = Counter(ex.map(same, range(50)))
    rec(C, "50 parallel posts of ONE request id, same payload", "", f"{dict(r2)}", 0, "closed")
    def sameDiff(i): return lead("g-same2", {"name": "Same%d" % i, "email": "same2@example.test"}, timeout=40)[0]
    with ThreadPoolExecutor(50) as ex: r3 = Counter(ex.map(sameDiff, range(50)))
    rec(C, "50 parallel posts of ONE request id, 50 different names", "", f"{dict(r3)}", 0, "closed")
    # resolve twice: need an unknown follow-up
    ctrl = lambda d: urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{FP}/fake/control", data=json.dumps(d).encode(), method="POST"), timeout=3).read()
    ctrl({"fail_next": "record_then_drop", "target": "outbox"})
    r = lead("g-unk", {"name": "Unk", "email": "unk@example.test"})
    time.sleep(2)
    rv = js(f"http://127.0.0.1:{DP}/review")
    unk = [x for x in rv if isinstance(x, dict) and x.get("kind") == "unknown"]
    rec(C, "setup: lead with mail reply lost -> unknown follow-up", *r, note=f"unknown items: {[(x['item_id']) for x in unk]}")
    if unk:
        iid = unk[0]["item_id"]
        def res_(dec): return post(f"/review/{iid}/resolve", json.dumps({"decision": dec}).encode(), timeout=15)[:2]
        with ThreadPoolExecutor(10) as ex:
            outs = list(ex.map(res_, ["sent", "not_sent"] * 5))
        rec(C, f"resolve {iid} 10x concurrently (5 sent, 5 not_sent)", "", f"{Counter((o[0], o[1][:40]) for o in outs)}", 0, "closed")
        rec(C, f"GET /leads for that lead", *get("/leads/" + iid[1:]))
        rec(C, f"resolve {iid} again after final", *post(f"/review/{iid}/resolve", b'{"decision":"sent"}'))
        rec(C, f"retry {iid} after final", *post(f"/review/{iid}/retry", b""))
    # second unknown for weird resolve bodies
    ctrl({"fail_next": "record_then_drop", "target": "outbox"})
    lead("g-unk2", {"name": "Unk2", "email": "unk2@example.test"}); time.sleep(2)
    unk = [x for x in js(f"http://127.0.0.1:{DP}/review") if isinstance(x, dict) and x.get("kind") == "unknown"]
    if unk:
        iid = unk[0]["item_id"]
        for label, b in [("empty body", b""), ("not json", b"decision=sent"), ("decision list", b'{"decision":["sent"]}'), ("decision SENT upper", b'{"decision":"SENT"}'), ("decision ' sent'", b'{"decision":" sent"}'),
                         ("decision with NUL", b'{"decision":"sent\\u0000"}'), ("nested depth 10000", b'{"a":' * 10000 + b"1" + b"}" * 10000), ("duplicate keys", b'{"decision":"sent","decision":"not_sent"}'), ("decision null", b'{"decision":null}'), ("invalid utf8", b'{"decision":"\xff"}'), ("array body", b"[\"sent\"]"), ("10 MB body", b"x" * 10_000_000)]:
            rec(C, f"resolve {iid} body: {label}", *post(f"/review/{iid}/resolve", b, timeout=20))
        rec(C, f"resolve on R/D/O/F-missing ids", *post("/review/R1/resolve", b'{"decision":"sent"}'))
        rec(C, "retry F of sent lead / unknown", *post(f"/review/{iid}/retry", b""))
    alive_note(C)

    # ---- H restart durability after hard kill during attack
    fresh(); C = "H kill and restart"
    def blast(i): return lead(f"k-{i}", {"name": "K", "email": f"k{i%7}@example.test"}, timeout=20)[0]
    th = threading.Thread(target=lambda: list(ThreadPoolExecutor(40).map(blast, range(300))))
    th.start(); time.sleep(0.6)
    procs["d"].kill(); procs["d"].wait()
    th.join(timeout=60)
    s_before = None
    try:
        con = sqlite3.connect("file:" + procs["db"].replace("\\", "/") + "?mode=ro", uri=True, timeout=3)
        s_before = (con.execute("select count(*) from receipts").fetchone()[0], con.execute("select count(*) from receipts where outcome is null").fetchone()[0]); con.close()
    except Exception as e:
        s_before = str(e)
    # restart on same DB
    e = env(); e["DESK_DB_PATH"] = procs["db"]
    procs["d"] = subprocess.Popen([PY, "-m", "lead_desk.server"], cwd=ROOT, env=e, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3)
    def blast2(i): return lead(f"k-{i}", {"name": "K", "email": f"k{i%7}@example.test"}, timeout=20)[0]
    with ThreadPoolExecutor(20) as ex: rr = Counter(ex.map(blast2, range(300)))
    rec(C, "kill -9 desk mid-burst (300 posts, 7 emails), restart same DB, resend all 300 ids", "", f"db before restart (receipts, open)={s_before}; resend statuses {dict(rr)}", 0, "closed")
    alive_note(C)


if __name__ == "__main__":
    main()
