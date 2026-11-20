"""G9 v3 evidence: the property corpus (tests/test_redact_idempotent_property.py CORPUS) through redact(), a second redact() of its output with its
map, redact_text() and a second redact_text() of its output with the same RunMap, on tree argv[1]; dumps json to argv[2]; prints the passes."""
import importlib, json, sys
tree = sys.argv[1]; sys.path.insert(0, tree + "/src"); sys.path.insert(0, tree)
R = importlib.import_module("hadavin_sdk.guard.redact")
sys.path.insert(0, sys.argv[0].rsplit("/", 1)[0])
import g9_probe  # noqa: E402

g9_probe.install(R)
from hadavin_sdk.guard import runmap
P = importlib.import_module("tests.test_redact_idempotent_property")
out = {}
for cid, text in P.CORPUS:
    row = [text]
    for f in (lambda: (res := R.redact(text), res.text, res.restore(res.text) == text, R.redact(res.text, mapping=dict(res.mapping)).text == res.text)[1:],
              lambda: (m := runmap.RunMap(), once := runmap.redact_text(text, m), runmap.redact_text(once, m))[1:]):
        try: row.append(list(f()))
        except Exception as e: row.append("RAISED " + type(e).__name__ + str(e))
    out[cid] = row
json.dump(out, open(sys.argv[2], "w"))
print(len(out), "inputs;", g9_probe.summary())
