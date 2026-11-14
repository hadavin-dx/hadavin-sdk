"""Apply the env-port patch to the harness folder given as argv[1]. Defaults equal the old literals. Idempotent."""
import sys, os, re
d = sys.argv[1]
def sub(fn, pairs, head=None):
    p = os.path.join(d, fn); s = open(p, encoding="utf-8").read()
    if re.search(r"MF_(N8N|RUN|PG)_PORT", s): print(fn, "already patched"); return
    for a, b in pairs:
        if a not in s: raise SystemExit(fn + ": literal not found: " + a)
        s = s.replace(a, b)
    if head: s = s.replace(head[0], head[1], 1)
    if not re.search(r"^import os|^import .*\bos\b", s, re.M): s = "import os\n" + s
    elif fn in ("api.py",) and not s.startswith("import os"): s = "import os\n" + s
    open(p, "w", encoding="utf-8").write(s); print(fn, "patched")
sub("lib.py", [
 ("N8N_PORTS = (5679, 5780)", "N8N_PORT_ = int(os.environ.get(\"MF_N8N_PORT\", \"5679\")); BROKER_PORT_ = int(os.environ.get(\"MF_N8N_BROKER_PORT\", \"5780\")); FAKE_PORT_ = int(os.environ.get(\"MF_RUN_PORT\", \"8790\"))\nN8N_PORTS = (N8N_PORT_, BROKER_PORT_)"),
 ('FAKE = "http://127.0.0.1:8790"', 'FAKE = "http://127.0.0.1:%d" % FAKE_PORT_'),
 ('"http://127.0.0.1:5679/healthz"', '"http://127.0.0.1:%d/healthz" % N8N_PORT_'),
 ('f"http://127.0.0.1:5679/webhook/{path}"', 'f"http://127.0.0.1:{N8N_PORT_}/webhook/{path}"'),
 ('N8N_PORT="5679", N8N_RUNNERS_BROKER_PORT="5780"', 'N8N_PORT=str(N8N_PORT_), N8N_RUNNERS_BROKER_PORT=str(BROKER_PORT_)'),
 ('_wait_port_free(5679, 20) or not port_free(5780): raise RuntimeError("port 5679 or 5780 is busy', '_wait_port_free(N8N_PORT_, 20) or not port_free(BROKER_PORT_): raise RuntimeError("the n8n port or its broker port is busy'),
 ('"http://127.0.0.1:5679/healthz/readiness"', '"http://127.0.0.1:%d/healthz/readiness" % N8N_PORT_'),
 ('not port_free(8790): raise RuntimeError("port 8790 is busy', 'not port_free(FAKE_PORT_): raise RuntimeError("the stand-in server port is busy'),
])
sub("fakes2.py", [('("127.0.0.1", 8790)', '("127.0.0.1", int(os.environ.get("MF_RUN_PORT", "8790")))')])
sub("setup.py", [('"port": 55432', '"port": int(os.environ.get("MF_PG_PORT", "55432"))')])
sub("api.py", [('B = "http://127.0.0.1:5679/rest"', 'B = "http://127.0.0.1:%s/rest" % os.environ.get("MF_N8N_PORT", "5679")')])
# second patch (16:50Z): child envs must keep MF_*, DN1_*, RUN_ID (start_fakes dropped MF_RUN_PORT; fakes2 then bound the default port)
p = os.path.join(d, "lib.py"); s = open(p, encoding="utf-8").read()
if "_pass_vars" not in s:
    a = "def _base_env():"
    if a not in s: raise SystemExit("lib.py: _base_env not found")
    s = s.replace(a, "def _pass_vars(): return {k: v for k, v in os.environ.items() if k.startswith((\"MF_\", \"DN1_\", \"N8N_EVD_\")) or k == \"RUN_ID\"}\ndef _base_env():\n    env = _base_env0(); env.update(_pass_vars()); return env\ndef _base_env0():", 1)
    open(p, "w", encoding="utf-8").write(s); print("lib.py env pass-through patched")
