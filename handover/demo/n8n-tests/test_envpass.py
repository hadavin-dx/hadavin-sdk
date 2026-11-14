"""Fails if a child env built by the harness drops MF_*, DN1_* or RUN_ID (the 16:50Z defect: start_fakes lost MF_RUN_PORT).
Usage: python3 test_envpass.py <path to the patched lib.py>. Starts nothing; imports lib with made-up work paths."""
import sys, os, importlib.util, tempfile
src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "harness-patched", "lib.py.patched")
hdir = os.path.dirname(os.path.abspath(sys.argv[2])) if len(sys.argv) > 2 else None
t = tempfile.mkdtemp()
os.environ.update(N8N_EVD_WORK=t, N8N_EVD_NODE=t, MF_RUN_PORT="18790", MF_N8N_PORT="15679", DN1_MAIL_PORT="18791", RUN_ID="p2", MF_V4="1", SECRET_X="must-not-pass")
if hdir: sys.path.insert(0, hdir)
from importlib.machinery import SourceFileLoader
lib = SourceFileLoader("libundertest", src).load_module()
bad = []
for name, env in (("_base_env", lib._base_env()), ("n8n_env", lib.n8n_env(0))):
    for k, v in (("MF_RUN_PORT", "18790"), ("MF_N8N_PORT", "15679"), ("DN1_MAIL_PORT", "18791"), ("RUN_ID", "p2"), ("MF_V4", "1")):
        if env.get(k) != v: bad.append("%s dropped %s" % (name, k))
    if "SECRET_X" in env: bad.append(name + " passed an unrelated variable")
if lib.FAKE != "http://127.0.0.1:18790": bad.append("FAKE does not follow MF_RUN_PORT: " + lib.FAKE)
print("FAIL envpass: " + "; ".join(bad)) if bad else print("PASS envpass: MF_*, DN1_*, RUN_ID reach the child envs; unrelated variables do not; FAKE follows MF_RUN_PORT")
sys.exit(1 if bad else 0)
