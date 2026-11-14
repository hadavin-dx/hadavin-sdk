"""Test (no docker, no network, nothing started): two different RUN_IDs get disjoint ports, container names and labels; the DEFAULT config equals the old literal values; bad RUN_IDs are refused; cleanup is by label VALUE.  python test_runcfg.py   -> prints PASS or the problems"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import runcfg as r
OLD = dict(pg_name="n8n-publish-pg", label="n8n-evidence.run=1", stage=8770, crm=8771, desk=8765, fake=8766, model=48767, proxy=8760, mail=8791, n8n=5679, broker=5780, pg_port=55432, run=8790)
bad = []
d = r.config({})
for k, v in OLD.items():
    if d[k] != v: bad.append("default %s = %r, old value %r" % (k, d[k], v))
OTHER = dict(MF_STAGE_PORT="18770", MF_CRM_PORT="18771", DN1_DESK_PORT="18765", DN1_FAKE_PORT="18766", DN1_MODEL_PORT="58767", DN1_PROXY_PORT="18760", DN1_MAIL_PORT="18791", MF_N8N_PORT="15679", MF_N8N_BROKER_PORT="15780", MF_PG_PORT="65432", MF_RUN_PORT="18790")
a, b = r.config(dict(RUN_ID="a", **OTHER)), r.config(dict(RUN_ID="b", **{k: str(int(v) + 100) for k, v in OTHER.items()}))
for x, y, what in ((d, a, "default vs a"), (a, b, "a vs b"), (d, b, "default vs b")):
    p = r.disjoint(x, y)
    if p: bad.append("%s not disjoint: %s" % (what, p))
if r.disjoint(d, d) == []: bad.append("disjoint() did not see two identical configs as colliding")
if r.disjoint(d, r.config({"RUN_ID": "c"})) == []: bad.append("RUN_ID alone must NOT make ports disjoint (it only changes name and label): expected collisions on the default ports")
if a["pg_name"] != "n8n-publish-pg-a" or a["label"] != "n8n-evidence.run=a": bad.append("names for RUN_ID a: %s %s" % (a["pg_name"], a["label"]))
if a["label"] == d["label"] or a["label"] == b["label"]: bad.append("label values must differ")
for badid in ("1", "A", "x_y", "a" * 13, "-a", "a b"):
    try: r.config({"RUN_ID": badid}); bad.append("bad RUN_ID %r was accepted" % badid)
    except ValueError: pass
print("PASS runcfg: defaults = old values; RUN_IDs a and b: disjoint ports, names %s / %s, labels %s / %s" % (a["pg_name"], b["pg_name"], a["label"], b["label"]) if not bad else "FAIL: " + "; ".join(bad))
sys.exit(1 if bad else 0)
