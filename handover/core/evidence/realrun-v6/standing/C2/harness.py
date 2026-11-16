import os, pty, sys, select, time, subprocess, random, re, json, signal, shutil
from pathlib import Path
RR = Path("/home/user/build/rr6"); T = RR/"tree-C2"; W = RR/"tmp-C2"; OUT = RR/"out"/"C2"
PY = str(RR/"venv312/bin/python"); LO = str(RR/"src-v6/drivers/lo_up-q4g.py")
random.seed(1)
FAKEKEY = "made-up-" + "key-" + "7431"   # built from parts
FAKEKEY2 = "made-up-" + "key-" + "9902"
ENV = {"PATH": os.environ["PATH"], "HOME": str(W), "TMPDIR": str(W), "PYTHONPATH": str(T/"src"), "LANG": "C.UTF-8", "PYTHONUNBUFFERED": "1"}
fx = W/"fx"; shutil.rmtree(fx, ignore_errors=True); fx.mkdir()
(fx/"key.txt").write_text(FAKEKEY+"\n"); (fx/"key2.txt").write_text(FAKEKEY2+"\n")
(fx/"dir").mkdir(); (fx/"empty").write_text("")
(fx/"big.txt").write_text("A"*1_000_000)
(fx/"bigkey.txt").write_text(FAKEKEY*60000+"\n")
(fx/"multiline.txt").write_text(FAKEKEY+"\n"+FAKEKEY2+"\n")
(fx/"binary.bin").write_bytes(bytes(range(1,256))*50)
(fx/"nul.txt").write_bytes(b"abc\x00def\n")
(fx/"uni-ключ-🔑.txt").write_text(FAKEKEY+"\n")
(fx/"ledger.json").write_text("{}")
os.mkfifo(fx/"fifo")
(fx/"lnk").symlink_to(fx/"lnk")   # symlink loop
(fx/"dangling").symlink_to(fx/"nowhere")
os.chmod(fx/"key.txt", 0o644)
(fx/"nokey.txt").write_text(FAKEKEY+"\n"); os.chmod(fx/"nokey.txt", 0)  # root ignores
# synthetic config
subprocess.run([PY, str(RR/"src-v6/drivers/make_synthetic_config.py"), str(T), str(fx/"cfg"), "REAL_IMAP_1_HOST=localhost", "REAL_IMAP_2_HOST=localhost", "DESK_HUBSPOT_BASE_URL=http://127.0.0.1:1", "DESK_HUBSPOT_ALLOW_ANY_BASE_URL=yes", "DESK_SMTPP_PORT=1", "REAL_IMAP_1_PORT=1", "REAL_IMAP_2_PORT=1", "REAL_DRAIN_SECONDS=5", "REAL_MAIL_WAIT_SECONDS=5", "REAL_MAIL_SETTLE_SECONDS=1"], check=True, capture_output=True, env=ENV)
CFG = fx/"cfg"/"real-run.env"; base = CFG.read_text()
def cfgfile(name, text, raw=None):
    p = fx/name
    p.write_bytes(raw if raw is not None else text.encode("utf-8", "surrogateescape")); return str(p)
SECRET_PAT = re.compile(r"made-up-key-\d{4}|sk-[A-Za-z0-9]{10,}|AKIA[0-9A-Z]{16}|Bearer [A-Za-z0-9._-]{10,}")
ADDR_PAT = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+|https?://\S+|\b\d{1,3}(?:\.\d{1,3}){3}\b|\b(?:localhost|[\w-]+\.(?:com|net|org|io|test|invalid|example))\b")
def execute(cmd, tty=False, stdin_text=None, env_extra=None, cwd=None):
    env = dict(ENV); env.update(env_extra or {})
    full = ["timeout", "30", "unshare", "-n", PY if False else "python3", LO] + cmd
    full = ["timeout", "30", "unshare", "-n", "/usr/bin/env", "python3", LO] + cmd
    t0 = time.time(); out = b""
    if tty:
        pid, fd = pty.fork()
        if pid == 0:
            os.chdir(cwd or str(W)); os.execvpe(full[0], full, env)
        end = time.time()+40; prompted = None
        while time.time() < end:
            r,_,_ = select.select([fd],[],[],1)
            if r:
                try: d = os.read(fd, 65536)
                except OSError: break
                if not d: break
                out += d
                if b"anything else stops: " in out and prompted is None:
                    prompted = time.time(); os.close(fd); fd = None  # hang up: never answer
                    break
        if fd is not None:
            try: os.close(fd)
            except OSError: pass
        _, st = os.waitpid(pid, 0); rc = os.waitstatus_to_exitcode(st)
        if prompted: out += b"\n[harness: reached the start question; hung up without typing]"
    else:
        p = subprocess.run(full, input=(stdin_text or "").encode(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, cwd=cwd or str(W))
        out = p.stdout; rc = p.returncode
    txt = out.decode("utf-8", "replace").replace("\r", "")
    return rc, txt, time.time()-t0
cases = []
def add(group, label, cmd, tty=False, **kw):
    if any(len(c)>120000 for c in cmd):
        label += " [argv capped at 120000 chars: Linux refuses a single argument over 131072 bytes]"
        cmd = [c[:120000] for c in cmd]
    for k,v in list(kw.get("env_extra",{}).items()): kw["env_extra"][k]=v[:100000]
    cases.append((group, label, cmd, tty, kw))
RRC = str(T/"scripts/run_real_check.py"); LIVE = str(T/"scripts/run_live_check.py")
def rr(*a): return [PY, RRC, *a]
def lv(*a): return [PY, LIVE, *a]
BIG = "A"*1_000_000
UNI = "ключ-密钥-🔑-é‮\u0000"[:-1]
GOODLIVE = ["--key-file", str(fx/"key.txt"), "--base-url", "http://127.0.0.1:9", "--ledger", str(W/"led1.json"), "--cap-run", "0.5", "--cap-total", "1", "--price-date", "2026-11-04", "--model", "m1=1,5"]
def live_with(**over):
    a = {"--key-file": str(fx/"key.txt"), "--base-url": "http://127.0.0.1:9", "--ledger": str(W/"led1.json"), "--cap-run": "0.5", "--cap-total": "1", "--price-date": "2026-11-04", "--model": "m1=1,5"}
    a.update(over); out=[]
    for k,v in a.items():
        if v is None: continue
        out += [k, v]
    return out
# ---- run_real_check argument combos (no tty first, then tty for config parsing)
add("rr","no args, no tty", rr())
add("rr","no args, tty", rr(), tty=True)
add("rr","empty string arg", rr(""))
add("rr","--config empty string, tty", rr("--config",""), tty=True)
add("rr","--config 1MB path string", rr("--config",BIG), tty=True)
add("rr","--config unicode+RTL path", rr("--config",UNI), tty=True)
add("rr","--config newline in path", rr("--config","a\nb"), tty=True)
add("rr","--config ../ traversal to /etc/passwd", rr("--config","../../../../../../etc/passwd"), tty=True)
add("rr","--config ../ traversal to missing", rr("--config","../../../nonexistent/x.env"), tty=True)
add("rr","--config is a directory", rr("--config",str(fx/"dir")), tty=True)
add("rr","--config is a FIFO", rr("--config",str(fx/"fifo")), tty=True)
add("rr","--config symlink loop", rr("--config",str(fx/"lnk")), tty=True)
add("rr","--config dangling symlink", rr("--config",str(fx/"dangling")), tty=True)
add("rr","--config empty file", rr("--config",str(fx/"empty")), tty=True)
add("rr","--config 1MB of A (no =)", rr("--config",str(fx/"big.txt")), tty=True)
add("rr","--config binary bytes", rr("--config",str(fx/"binary.bin")), tty=True)
add("rr","--config invalid UTF-8", rr("--config",cfgfile("bad-utf8.env","",b"DESK_DB_PATH=\xff\xfe\n")), tty=True)
add("rr","--config /dev/null", rr("--config","/dev/null"), tty=True)
add("rr","--config /proc/self/environ", rr("--config","/proc/self/environ"), tty=True)
add("rr","--config given twice (same file)", rr("--config",str(CFG),"--config",str(CFG)), tty=True)
add("rr","--config twice different files", rr("--config",str(fx/"empty"),"--config",str(CFG)), tty=True)
add("rr","--config valid synthetic, tty (hang up at question)", rr("--config",str(CFG)), tty=True)
add("rr","--config valid synthetic, no tty", rr("--config",str(CFG)))
add("rr","--config lower-case name", rr("--config",cfgfile("lc.env","desk_qualifier=live_claude\n"+base)), tty=True)
add("rr","--config NUL in value", rr("--config",cfgfile("nul.env",base+"DESK_DB_PATH=a\x00b\n")), tty=True)
add("rr","--config 1MB value DESK_DB_PATH", rr("--config",cfgfile("bigdb.env",base+"DESK_DB_PATH="+BIG+"\n")), tty=True)
add("rr","--config 1MB value key file path", rr("--config",cfgfile("bigkf.env",base+"DESK_HUBSPOT_KEY_FILE="+BIG+"\n")), tty=True)
add("rr","--config DB path ../ traversal", rr("--config",cfgfile("trav.env",base+"DESK_DB_PATH=../../../../tmp/x/desk.db\n")), tty=True)
add("rr","--config DB path = existing dir", rr("--config",cfgfile("dbdir.env",base+f"DESK_DB_PATH={fx/'dir'}\n")), tty=True)
add("rr","--config DB path in read-only mount", rr("--config",cfgfile("rodb.env",base+f"DESK_DB_PATH={W/'rodir'}/sub/desk.db\n")), tty=True)
add("rr","--config DB path :memory:", rr("--config",cfgfile("mem.env",base+"DESK_DB_PATH=:memory:\n")), tty=True)
add("rr","--config DB path under a file", rr("--config",cfgfile("dbfile.env",base+f"DESK_DB_PATH={fx/'key.txt'}/x/desk.db\n")), tty=True)
add("rr","--config key file = directory", rr("--config",cfgfile("kdir.env",base+f"DESK_HUBSPOT_KEY_FILE={fx/'dir'}\n")), tty=True)
add("rr","--config key file = multiline", rr("--config",cfgfile("kml.env",base+f"DESK_HUBSPOT_KEY_FILE={fx/'multiline.txt'}\n")), tty=True)
add("rr","--config key file with NUL bytes", rr("--config",cfgfile("knul.env",base+f"DESK_HUBSPOT_KEY_FILE={fx/'nul.txt'}\n")), tty=True)
add("rr","--config key file = FIFO", rr("--config",cfgfile("kfifo.env",base+f"DESK_HUBSPOT_KEY_FILE={fx/'fifo'}\n")), tty=True)
add("rr","--config key file unicode path", rr("--config",cfgfile("kuni.env",base+f"DESK_HUBSPOT_KEY_FILE={fx/'uni-ключ-🔑.txt'}\n")), tty=True)
add("rr","--config key file 1MB key", rr("--config",cfgfile("kbig.env",base+f"DESK_HUBSPOT_KEY_FILE={fx/'bigkey.txt'}\n")), tty=True)
add("rr","--config key file mode 000 (root ignores)", rr("--config",cfgfile("k000.env",base+f"DESK_HUBSPOT_KEY_FILE={fx/'nokey.txt'}\n")), tty=True)
add("rr","--config remote host without allow flag", rr("--config",cfgfile("remote.env",base+"DESK_HUBSPOT_BASE_URL=https://api.example.invalid\n")), tty=True)
add("rr","--config missing REQUIRED", rr("--config",cfgfile("miss.env","DESK_DB_PATH=x\n")), tty=True)
add("rr","--config recipients unicode newline", rr("--config",cfgfile("rcp.env",base+"DESK_SMTPP_RECIPIENTS=a@example.com,‮b@example.com\n")), tty=True)
add("rr","--config REAL_PERSONS huge/neg/unicode", rr("--config",cfgfile("pers.env",base+"REAL_PERSONS=٣٣\n")), tty=True)
add("rr","--config REAL_PERSONS -1", rr("--config",cfgfile("pers2.env",base+"REAL_PERSONS=-1\n")), tty=True)
add("rr","--config REAL_DRAIN_SECONDS nan", rr("--config",cfgfile("nan.env",base+"REAL_DRAIN_SECONDS=nan\n")), tty=True)
add("rr","--config REAL_DRAIN_SECONDS 1e999", rr("--config",cfgfile("inf.env",base+"REAL_DRAIN_SECONDS=1e999\n")), tty=True)
add("rr","--live-model without live settings", rr("--config",str(CFG),"--live-model"), tty=True)
add("rr","wrong order: --config before flag value missing", rr("--config","--dry-fakes"), tty=True)
add("rr","unknown flag", rr("--nope"), tty=True)
add("rr","--assume-yes alone", rr("--assume-yes"))
add("rr","--keep alone", rr("--keep"))
add("rr","--assume-yes with --config", rr("--assume-yes","--config",str(CFG)))
add("rr","--dry-port-base huge, no tty", rr("--dry-fakes","--dry-port-base","99999999999999999999"))
add("rr","--dry-port-base text, tty", rr("--dry-fakes","--dry-port-base",UNI), tty=True)
add("rr","--dry-smtp-script 1MB, assume-yes", rr("--dry-fakes","--assume-yes","--dry-smtp-script",BIG))
add("rr","--dry-smtp-script unicode newline, assume-yes", rr("--dry-fakes","--assume-yes","--dry-smtp-script","x\ny"+UNI))
add("rr","--dry-fakes --assume-yes --keep (ref. run, folder in tmp)", rr("--dry-fakes","--assume-yes","--keep"))
add("rr","--dry-fakes --assume-yes --cleanup", rr("--dry-fakes","--assume-yes","--cleanup"))
add("rr","--dry-fakes with TMPDIR read-only mount", rr("--dry-fakes","--assume-yes"), env_extra={"TMPDIR":str(W/"rodir")})
add("rr","--dry-fakes with TMPDIR missing", rr("--dry-fakes","--assume-yes"), env_extra={"TMPDIR":str(W/"does-not-exist")})
add("rr","env: hostile DESK_* env vars + --dry-fakes", rr("--dry-fakes","--assume-yes"), env_extra={"DESK_DB_PATH":"../../x","DESK_HUBSPOT_KEY_FILE":BIG[:200000],"DESK_QUALIFIER":"live_claude"})
# ---- run_live_check
add("live","no args", lv())
add("live","empty string args", lv("","",""))
add("live","good combo, no tty", lv(*live_with()))
add("live","good combo, tty (hang up at question)", lv(*live_with()), tty=True)
add("live","good combo + --assume-yes loopback", lv(*live_with(), "--assume-yes", "--leads","1","--runs","1"))
add("live","--assume-yes with remote url", lv(*live_with(**{"--base-url":"https://api.example.invalid"}), "--assume-yes"))
add("live","--base-url missing", lv(*live_with(**{"--base-url":None})))
add("live","--base-url 1MB", lv(*live_with(**{"--base-url":"http://127.0.0.1/"+BIG}), "--assume-yes"))
add("live","--base-url unicode host", lv(*live_with(**{"--base-url":"http://ключ.example/"})))
add("live","--base-url newline", lv(*live_with(**{"--base-url":"http://127.0.0.1\nHost: evil"}), "--assume-yes"))
add("live","--base-url bad port", lv(*live_with(**{"--base-url":"http://127.0.0.1:99999999"}), "--assume-yes"))
add("live","--base-url ipv6 bracket broken", lv(*live_with(**{"--base-url":"http://[::1"}), "--assume-yes"))
add("live","--key-file empty file", lv(*live_with(**{"--key-file":str(fx/"empty")}), "--assume-yes"))
add("live","--key-file directory", lv(*live_with(**{"--key-file":str(fx/"dir")}), "--assume-yes"))
add("live","--key-file FIFO", lv(*live_with(**{"--key-file":str(fx/"fifo")}), "--assume-yes"))
add("live","--key-file ../ traversal", lv(*live_with(**{"--key-file":"../../../../../../etc/shadow"}), "--assume-yes"))
add("live","--key-file 1MB path", lv(*live_with(**{"--key-file":BIG}), "--assume-yes"))
add("live","--key-file 1MB content", lv(*live_with(**{"--key-file":str(fx/"bigkey.txt")}), "--assume-yes"))
add("live","--key-file multiline", lv(*live_with(**{"--key-file":str(fx/"multiline.txt")}), "--assume-yes"))
add("live","--key-file NUL bytes", lv(*live_with(**{"--key-file":str(fx/"nul.txt")}), "--assume-yes"))
add("live","--key-file binary", lv(*live_with(**{"--key-file":str(fx/"binary.bin")}), "--assume-yes"))
add("live","--key-file unicode path", lv(*live_with(**{"--key-file":str(fx/"uni-ключ-🔑.txt")}), "--assume-yes","--leads","1","--runs","1"))
add("live","--key-file symlink loop", lv(*live_with(**{"--key-file":str(fx/"lnk")}), "--assume-yes"))
add("live","--key-file mode 000 (root ignores)", lv(*live_with(**{"--key-file":str(fx/"nokey.txt")}), "--assume-yes","--leads","1","--runs","1"))
add("live","--key-file same as --ledger", lv(*live_with(**{"--ledger":str(fx/"key.txt")}), "--assume-yes"))
add("live","--ledger directory", lv(*live_with(**{"--ledger":str(fx/"dir")}), "--assume-yes"))
add("live","--ledger FIFO", lv(*live_with(**{"--ledger":str(fx/"fifo")}), "--assume-yes"))
add("live","--ledger in read-only mount", lv(*live_with(**{"--ledger":str(W/"rodir"/"l.json")}), "--assume-yes","--leads","1","--runs","1"))
add("live","--ledger under a file", lv(*live_with(**{"--ledger":str(fx/"key.txt")+"/x/l.json"}), "--assume-yes"))
add("live","--ledger 1MB of A content", lv(*live_with(**{"--ledger":str(fx/"big.txt")}), "--assume-yes"))
add("live","--ledger ../ traversal", lv(*live_with(**{"--ledger":"../../../../tmp/zz/l.json"}), "--assume-yes","--leads","1","--runs","1"))
add("live","--ledger empty string", lv(*live_with(**{"--ledger":""}), "--assume-yes"))
add("live","--cap-run text / unicode", lv(*live_with(**{"--cap-run":UNI}), "--assume-yes"))
add("live","--cap-run negative", lv(*live_with(**{"--cap-run":"-1"}), "--assume-yes"))
add("live","--cap-run 1e999999", lv(*live_with(**{"--cap-run":"1e999999"}), "--assume-yes"))
add("live","--cap-run NaN", lv(*live_with(**{"--cap-run":"NaN"}), "--assume-yes"))
add("live","--cap-total 1MB digits", lv(*live_with(**{"--cap-total":"9"*1_000_000}), "--assume-yes"))
add("live","--cap-run > --cap-total", lv(*live_with(**{"--cap-run":"5","--cap-total":"1"}), "--assume-yes"))
add("live","--model empty id", lv(*live_with(**{"--model":"=1,2"}), "--assume-yes"))
add("live","--model bad prices", lv(*live_with(**{"--model":"m=a,b"}), "--assume-yes"))
add("live","--model 1MB id", lv(*live_with(**{"--model":BIG+"=1,2"}), "--assume-yes"))
add("live","--model unicode newline id", lv(*live_with(**{"--model":"mo\ndel-é=1,2"}), "--assume-yes"))
add("live","--price-date whitespace", lv(*live_with(**{"--price-date":"   "}), "--assume-yes"))
add("live","--leads 0 / huge", lv(*live_with(), "--leads","99999999999999999999","--assume-yes"))
add("live","--runs -1", lv(*live_with(), "--runs","-1","--assume-yes"))
add("live","--timeout nan", lv(*live_with(), "--timeout","nan","--assume-yes"))
add("live","--max-tokens 0", lv(*live_with(), "--max-tokens","0","--assume-yes"))
add("live","--effort 1MB", lv(*live_with(), "--effort",BIG,"--assume-yes"))
add("live","wrong order: value flag last without value", lv(*live_with(), "--model"))
add("live","--key-file given twice (same file)", lv(*live_with(), "--key-file", str(fx/"key.txt"), "--assume-yes","--leads","1","--runs","1"))
add("live","--model same model twice", lv(*live_with(), "--model","m1=1,5","--assume-yes","--leads","1","--runs","1"))
add("live","stray positional word", lv(*live_with(), "stray-"+FAKEKEY))
add("live","key text as flag value of wrong flag", lv(*live_with(**{"--cap-run":FAKEKEY}), "--assume-yes"))
# precheck helpers
def pc(expr): return ["python3","-I","-c", "import sys; sys.path.insert(0,%r); from precheck import *; import os; print(%s)" % (str(T/"scripts"), expr)]
# these go via PY directly
def pcx(expr): return [PY, "-c", "import sys; sys.path.insert(0,%r); from precheck import *; print(%s)" % (str(T/"scripts"), expr)]
add("pre","is_special_file(1MB path)", pcx("is_special_file('A'*1000000)"))
add("pre","is_special_file(NUL path)", pcx("is_special_file('a\\x00b')"))
add("pre","is_special_file(FIFO)", pcx("is_special_file(%r)" % str(fx/"fifo")))
add("pre","is_special_file(/dev/null)", pcx("is_special_file('/dev/null')"))
add("pre","is_special_file(empty string)", pcx("is_special_file('')"))
add("pre","is_special_file(None) wrong type", pcx("is_special_file(None)"))
add("pre","folder_part_is_a_file(under file)", pcx("folder_part_is_a_file(%r)" % (str(fx/"key.txt")+"/a/b")))
add("pre","folder_part_is_a_file(1MB)", pcx("folder_part_is_a_file('A'*1000000)"))
add("pre","folder_part_is_a_file(NUL)", pcx("folder_part_is_a_file('a\\x00b/c')"))
add("pre","folder_part_is_a_file(../ traversal)", pcx("folder_part_is_a_file('../../../../../../x/y')"))
add("pre","same_file(same twice)", pcx("same_file(%r,%r)" % (str(fx/"key.txt"),str(fx/"key.txt"))))
add("pre","same_file(dir, dir)", pcx("same_file(%r,%r)" % (str(fx/"dir"),str(fx/"dir"))))
add("pre","same_file(symlink loop twice)", pcx("same_file(%r,%r)" % (str(fx/"lnk"),str(fx/"lnk"))))
add("pre","same_file(NUL, 1MB)", pcx("same_file('a\\x00',  'B'*1000000)"))
add("pre","same_file(unicode, ../)", pcx("same_file('ключ-🔑','../ключ-🔑')"))
add("pre","run as script: precheck.py (no main)", [PY, str(T/"scripts/precheck.py"), "--help"])
print("cases:", len(cases), flush=True)
rows = []; raw = open(OUT/"raw-C2-run2.log","w")
for i,(g,label,cmd,tty,kw) in enumerate(cases,1):
    try: rc,txt,dt = execute(cmd, tty=tty, **kw)
    except Exception as e: rc,txt,dt = "HARNESS", f"{type(e).__name__}", 0
    tb = "yes" if "Traceback (most recent call last)" in txt else "no"
    sec = SECRET_PAT.findall(txt); adr = ADDR_PAT.findall(txt)
    first = next((l for l in txt.splitlines() if l.strip()), "(no output)")
    if tb=="yes":
        last = [l for l in txt.splitlines() if l.strip()][-1]; first = "TB: "+last
    first = first[:140]; lastl = [l for l in txt.splitlines() if l.strip()][-1][:140] if txt.strip() else "(no output)"
    raw.write(f"##### {i} [{g}] {label} | tty={tty} | rc={rc} | {dt:.1f}s\n  cmd: {' '.join(c if len(c)<150 else c[:60]+'...<%d chars>'%len(c) for c in cmd)}\n{txt[:6000]}\n\n"); raw.flush()
    rows.append((i,g,label,rc,first+" || LAST: "+lastl,tb,"yes" if (sec or adr) else "no", sorted(set(sec))[:2], sorted(set(adr))[:3], round(dt,1)))
    print(i, g, label[:50], rc, tb, "S" if sec else "-", "A" if adr else "-", flush=True)
json.dump(rows, open(OUT/"rows-run2.json","w"), default=str)
