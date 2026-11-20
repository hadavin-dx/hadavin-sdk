"""Run all G8 rows on the tree in cwd; print JSON {rowid: output}. usage: cd TREE; PYTHONPATH=$PWD/src:$PWD python rows.py OUT.json"""
import json, sys, importlib
importlib.import_module("hadavin_sdk.guard.redact")
from hadavin_sdk.guard.redact import redact
from hadavin_sdk.guard import runmap
import tests.g8_cases as G
out = {}; idem = {}
def rec(k, t):
    r = redact(t); out[k] = r.text
    r2 = redact(r.text); idem[k] = (r2.text == r.text)
for c in G.CASES: rec(f"row{c['id']}", c["text"])
for k in G.KEEP: rec(k["id"], k["text"])
for f in G.FULL_STOP: rec(f[0], f[1])
for o in G.OPAQUE_LIMITS: rec(o[0], o[2])
for aid, text, now, after in G.AT_REST:
    r = redact(text); out[aid] = [r.text, sorted(r.mapping.items()), sorted(runmap.storable(dict(r.mapping)).items())]
for uid, call, text, want in G.UNTRUSTED:
    m = runmap.RunMap(); out[uid] = [getattr(runmap, call)(text, m), dict(m)]
json.dump({"out": out, "idem": idem}, open(sys.argv[1], "w"), indent=0, sort_keys=True)
print(len(out), "records;", sum(not v for v in idem.values()), "non-idempotent")
