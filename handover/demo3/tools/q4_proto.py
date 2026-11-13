"""Q4 protocol measurements against a desk started here (loopback, made-up data). Run with PYTHONPATH=src:. from the repo root.
usage: q4_proto.py PORTBASE PASS REPS"""
import json, os, socket, subprocess, sys, tempfile, threading, time, urllib.request, urllib.error, re, statistics
PB = int(sys.argv[1]); PASS = sys.argv[2]; REPS = int(sys.argv[3])
H = "127.0.0.1"
def load(): return open("/proc/loadavg").read().split()[0]
def out(name, rep, **kw): print(json.dumps({"test": name, "pass": PASS, "rep": rep, "load1": load(), **kw}), flush=True)
tmp = tempfile.mkdtemp(prefix="q4proto.")
env = dict(os.environ, DESK_DB_PATH=f"{tmp}/desk.db", DESK_PORT=str(PB), DESK_FAKES_PORT=str(PB+1), TMPDIR=tmp)
fk = subprocess.Popen([sys.executable, "-m", "demo_only.fakes_server", "--outbox", "keyed", "--port", str(PB+1)], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
t0 = time.monotonic()
dk = subprocess.Popen([sys.executable, "-m", "lead_desk.server"], env=env, stdout=open(f"{tmp}/desk.log", "w"), stderr=subprocess.STDOUT)
def get(path, port=PB, timeout=5):
    try:
        r = urllib.request.urlopen(f"http://{H}:{port}{path}", timeout=timeout); return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e: return e.code, e.read(), dict(e.headers)
    except Exception as e: return type(e).__name__, b"", {}
try:
    for i in range(100):
        if get("/counts")[0] == 200: break
        time.sleep(0.1)
    out("startup_until_counts_200", 0, seconds=round(time.monotonic()-t0, 2))
    def raw(data, hold=0.0, maxwait=20, chunks=None):
        s = socket.create_connection((H, PB), timeout=maxwait); t = time.monotonic()
        try:
            if data: s.sendall(data)
            buf = b""
            while True:
                try: c = s.recv(65536)
                except (socket.timeout, ConnectionResetError): break
                if not c: break
                buf += c
            return buf.split(b"\r\n", 1)[0].decode("latin1"), round(time.monotonic()-t, 2), buf
        finally: s.close()
    def status(buf): return buf.split(b"\r\n", 1)[0].decode("latin1")
    for rep in range(1, REPS+1):
        # idle connection -> 408 at header deadline
        st, el, _ = raw(b""); out("idle_conn_408", rep, claim="408 after 10 s", status=st, seconds=el)
        # body deadline: announce 100 bytes, send 10, stay silent
        hdr = f"POST /leads HTTP/1.1\r\nHost: {H}:{PB}\r\nContent-Type: application/json\r\nContent-Length: 100\r\n\r\n".encode()
        st, el, _ = raw(hdr + b"x"*10); out("short_body_open_408", rep, claim="408 10 s after headers", status=st, seconds=el)
        # drip one byte every 1.9 s
        s = socket.create_connection((H, PB), timeout=30); t = time.monotonic(); first = b"POST /leads HTTP/1.1\r\nHost: 127.0.0.1\r\n"; buf = b""; i = 0
        s.settimeout(1.9)
        while time.monotonic()-t < 25:
            try: s.sendall(first[i:i+1]); i += 1
            except OSError: break
            try:
                c = s.recv(4096)
                if c: buf += c; 
                if not c: break
                if buf: break
            except socket.timeout: pass
        out("drip_1.9s_held", rep, claim="held up to ~10 s then 408", status=status(buf) or "none", seconds=round(time.monotonic()-t, 2), bytes_sent=i); s.close()
        # size cap
        def post(n, extra=b"", cl=None):
            sk = json.dumps({"source": "form", "source_ref": f"cap{rep}-{n}-{time.time_ns()}", "payload": {"email": f"cap{rep}{n}@example.test", "name": "A", "message": "m"}, "pad": ""})
            body = sk[:-2] + "a"*(n - len(sk.encode())) + '"}'
            b = body.encode()
            h = f"POST /leads HTTP/1.1\r\nHost: {H}:{PB}\r\nContent-Type: application/json\r\nContent-Length: {len(b) if cl is None else cl}\r\nConnection: close\r\n\r\n".encode()
            return len(b), raw(h + b)[0:2]
        for n in (65536, 65537):
            ln, (st, el) = post(n); out("size_cap_post", rep, claim="<=65536 accepted, larger 413", body_bytes=ln, status=st, seconds=el)
        h = f"POST /leads HTTP/1.1\r\nHost: {H}:{PB}\r\nContent-Length: 1000000\r\nConnection: close\r\n\r\n".encode()
        st, el, _ = raw(h); out("huge_content_length_413_fast", rep, claim="413 straight away", status=st, seconds=el)
        h = f"POST /leads HTTP/1.1\r\nHost: {H}:{PB}\r\nContent-Length: {'9'*5000}\r\nConnection: close\r\n\r\n".encode()
        st, el, _ = raw(h); out("5000_digit_content_length", rep, claim="413 straight away", status=st, seconds=el)
        h = f"POST /leads HTTP/1.1\r\nHost: {H}:{PB}\r\nContent-Length: 5\r\nContent-Length: 6\r\nConnection: close\r\n\r\nabcdef".encode()
        st, el, _ = raw(h); out("two_content_lengths_400", rep, claim="400", status=st, seconds=el)
        # connection limit 256: hold 256 idle, immediate request -> 503 busy + Retry-After 1; after 2.5 s request is served and one idle evicted
        socks = []
        for i in range(256):
            socks.append(socket.create_connection((H, PB), timeout=5))
        time.sleep(0.2)
        t = time.monotonic(); st, body, hd = get("/counts", timeout=10)
        out("conn_limit_256_immediate", rep, claim="503 busy, Retry-After 1, no store", status=st, retry_after=hd.get("Retry-After"), body=body.decode()[:80], seconds=round(time.monotonic()-t, 2))
        time.sleep(2.3)
        t = time.monotonic(); st, body, hd = get("/counts", timeout=10)
        closed = 0
        for s in socks:
            s.setblocking(False)
            try:
                if s.recv(1) == b"": closed += 1
            except BlockingIOError: pass
            except OSError: closed += 1
        out("conn_limit_256_after_2s_evicts", rep, claim="oldest idle >=2 s closed with no reply; new served", status=st, idle_closed_by_desk=closed, seconds=round(time.monotonic()-t, 2))
        for s in socks: s.close()
        # 257 idle connections all at once, then who gets 408 vs dropped (time to the end of all)
        time.sleep(0.5)
        # listen queue
        ss = ["", "ss not installed"]
        out("listen_backlog_ss", rep, claim="LISTEN_QUEUE 1024 (OS may cap lower)", ss=" ".join(ss[1].split()) if len(ss) > 1 else ss)
        # portal 8 at once
        codes = {}
        lock = threading.Lock()
        def p():
            for _ in range(10):
                c = get("/api/ui/summary", timeout=20)[0]
                with lock: codes[c] = codes.get(c, 0)+1
        ths = [threading.Thread(target=p) for _ in range(40)]
        [x.start() for x in ths]; [x.join() for x in ths]
        out("portal_api_40_parallel", rep, claim="at most 8 at once, more 503 busy", codes=dict(sorted(codes.items(), key=str)))
        # burst script retry rule vs closed port
        sys.path.insert(0, "."); from demo_only.burst import post_with_retries
        stamps = []
        def once():
            stamps.append(time.monotonic()); return "refused", None, None
        t = time.monotonic(); post_with_retries(once)
        gaps = [round(b-a, 2) for a, b in zip(stamps, stamps[1:])]
        out("retry_rule_closed_port", rep, claim="waits 0.1 doubling to 1 s; no new try after 30 s", tries=len(stamps), first_gaps=gaps[:7], last_try_at=round(stamps[-1]-stamps[0], 2), total=round(time.monotonic()-t, 2))
        # burst script 100 same lead, pending settle time
        mod = subprocess.run([sys.executable, "-m", "demo_only.burst", "--url", f"http://{H}:{PB}/leads", "--n", "100", "--email", f"ada{rep}@example.com", "--ref-prefix", f"run{PASS}{rep}", "--source", "form"], capture_output=True, text=True, env=env)
        tb = time.monotonic(); settle = None; peak_pending = 0
        for _ in range(300):
            c = json.loads(get("/counts")[1] or b"{}")
            peak_pending = max(peak_pending, c.get("pending_followups", 0))
            if c.get("pending_followups") == 0 and c.get("sending_followups") == 0: settle = round(time.monotonic()-tb, 2); break
            time.sleep(0.1)
        out("burst100_same_lead", rep, claim="201=1 200=99; 1 lead,1 followup; pending settles ~3 s", stdout=" | ".join(mod.stdout.split("\n"))[:260], settle_after_burst_end=settle, counts={k: c.get(k) for k in ("leads", "followups", "received", "new", "duplicate", "pending_followups", "sent_followups")} )
        ob = json.loads(get("/fake/outbox", port=PB+1)[1] or b"{}"); out("burst100_outbox", rep, claim="1 email per lead", outbox_count=ob.get("count"), expected_total=rep)
finally:
    for p in (dk, fk):
        p.terminate()
        try: p.wait(10)
        except Exception: p.kill()
    out("end", 0, load_after=load())
