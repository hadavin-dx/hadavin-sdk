"""Builds allow_v21.py from allow_v20.py: every pin value is mapped from the v20 fingerprint of a statement to the v21 fingerprint of the SAME statement (same file, same statement index);
import sys; sys.path.insert(0, ".")
the settle pin of the DB-3 file is the one the author READ in the new text and pinned by hand (printed by the guard, listed in the hand-off). Prints each mapping."""
import re, os, sys, glob
import secdef_guard_v20 as g20, secdef_guard_v21 as g21
a = open("allow_v20.py").read()
files = {os.path.basename(f): f for f in glob.glob("held-sql/*.sql") + glob.glob("/home/user/hadavin-sdk/src/hadavin_sdk/store/migrations/*.sql")}
oldfiles = {"spend_guarded_writes.sql": "../evidence-handoff-v20/held-sql/spend_guarded_writes.sql"}
mp = {}
for b, f in files.items():
    f_old = oldfiles.get(b, f)
    t_old, t_new = open(f_old).read(), open(f).read()
    s_old, s_new = g20.split_statements(g20.tokenize(t_old)), g21.split_statements(g21.tokenize(t_new))
    if len(s_old) != len(s_new): print("STATEMENT COUNT DIFFERS", b); continue
    for x, y in zip(s_old, s_new):
        o, n = g20.fingerprint(x), g21.fingerprint(y)
        if o in mp and mp[o] != n: print("COLLISION", o)
        mp.setdefault(o, n)
        if o != n or True: pass
def sub(m):
    v = m.group(1)
    if v in mp: print("pin", v, "->", mp[v]); return '"' + mp[v] + '"'
    print("NO MAPPING for", v); return m.group(0)
b = re.sub(r'"([0-9a-f]{16})"', sub, a)
b = b.replace("v20", "v21").replace("secdef_guard_v21.fingerprint", "secdef_guard_v21.fingerprint")
open("allow_v21.py", "w").write(b)
