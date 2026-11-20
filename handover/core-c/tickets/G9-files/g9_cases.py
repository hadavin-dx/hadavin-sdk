"""G9 v3 evidence: the E10 cases of section 0 and the cases of 9.1 on tree argv[1] (the base: no `_overlaps`, no pass count)."""
import importlib, sys, os
sys.path.insert(0, sys.argv[1] + "/src")
R = importlib.import_module("hadavin_sdk.guard.redact")
sys.path.insert(0, sys.argv[0].rsplit("/", 1)[0])
import g9_probe  # noqa: E402

g9_probe.install(R)
from hadavin_sdk.guard import runmap
V = "ab" + "9x"
def mk(m, reg=True):
    r = R._Redactor(m); r._may_register = reg; return r
def P():
    s = dict(g9_probe.STATS["passes"]); g9_probe.reset(); return f" passes {s}" if s else ""
def run(name, f):
    try: print(name, f(), P())
    except Exception as e: print(name, "RAISED", type(e).__name__, e, P())
r = mk({"<SECRET_1>": V}); f1 = r._place("BEARER", V + "ab", "<SECRET_1>ab"); f2 = r._place("BEARER", "xyz" + V, "xyz<SECRET_1>")
run("(a1)", lambda: (r.sweep("see xyz" + V + "ab end"), {k: v for k, v in r.mapping.items()}))
p = mk({"<SECRET_1>": "abcdefgh", "<SECRET_2>": "efghijkl"})
run("(a2)", lambda: (p.sweep("abcdefghijkl"), p.mapping))
r = mk({"<SECRET_1>": V}); f1 = r._place("BEARER", V + "ab", "<SECRET_1>ab"); round2 = r.sweep("xyz<SECRET_1>ab"); P()
f2 = r._place("BEARER", "xyz" + V, "xyz<SECRET_1>")
run("(b)", lambda: (round2, (o := r.sweep(round2)), r.mapping.get(o), r.sweep(o) == o))
m = {"<SECRET_1>": "abcdefgh", "<SECRET_2>": "efghijkl"}
run("redact", lambda: ((res := R.redact("x abcdefghijkl y", mapping=dict(m))).text, res.restore(res.text)))
run("redact_many", lambda: R.redact_many(["x abcdefghijkl y", "z efghijkl"], dict(m)))
rm = runmap.RunMap(); rm.update(m)
run("redact_text", lambda: (runmap.redact_text("x abcdefghijkl y", rm), dict(rm)))
run("natural", lambda: ((res := R.redact("password=abcdefgh\ntoken=efghijkl\nsee abcdefghijkl")).text, res.mapping))
run("natural many", lambda: R.redact_many(["password=abcdefgh", "token=efghijkl", "see abcdefghijkl"]))
run("natural text", lambda: runmap.redact_text("password=abcdefgh\ntoken=efghijkl\nsee abcdefghijkl", runmap.RunMap()))
run("gate enforce_map", lambda: runmap.enforce_map("x abcdefghijkl y", dict(m)))
run("gate abcdef", lambda: [runmap.enforce_map("abcdef", {"<SECRET_1>": "abcd", "<SECRET_2>": "cdef"}), runmap.enforce_map("abcdef", {"<SECRET_2>": "cdef", "<SECRET_1>": "abcd"}), runmap.enforce_map("abcdefg", {"<SECRET_1>": "abcd", "<SECRET_2>": "cdefg"})])
idm = {"<TENANT_1>": "abcd", "<TENANT_2>": "cdef"}
run("gate identifiers", lambda: [runmap.enforce_map("abcdef", idm), runmap.enforce_map("abcdef abcd cdef", idm)])
hb = {"<SECRET_1>": "SECRET_1", "<SECRET_2>": "ET_1zz9"}
run("gate held", lambda: [runmap.enforce_map("SECRET_1zz9", hb), runmap.enforce_map("SECRET_1 zz9", hb)])
s = runmap.snapshot(hb)
run("held_value_left SECR<SECRET_2>", lambda: runmap.held_value_left("SECR<SECRET_2>", s))
s2 = runmap.snapshot(m)
run("held_value_left <SECRET_1>ijkl", lambda: runmap.held_value_left("x <SECRET_1>ijkl y", s2))
run("gate history <SECRET_1>ijkl", lambda: runmap.enforce_map("x <SECRET_1>ijkl y", dict(m)))
run("gate tenant overlap", lambda: runmap.enforce_map("acme-prod-01-eu", {"<TENANT_1>": "acme-prod-01", "<TENANT_2>": "prod-01-eu"}))
run("gate ip+secret", lambda: runmap.enforce_map("10.100.200.5-Xyz9 y", {"<IPV4_1>": "10.100.200.5", "<SECRET_1>": "0.5-Xyz9"}))
# kind: identifier first
k = mk({"<IPV4_1>": "10.100.200.5", "<SECRET_1>": "0.5-Xyz9"})
run("kind ip-first", lambda: (k.sweep("10.100.200.5-Xyz9 y"), k.mapping))
k2 = mk({"<TENANT_1>": "abcdefghijkl", "<SECRET_1>": "abcdefgh", "<SECRET_2>": "efghijkl"})
run("kind reverse weaker", lambda: (k2.sweep("zabcdefghijkl y"), k2.mapping))
k3 = mk({"<TENANT_1>": "acme-prod-01", "<TENANT_2>": "prod-01-eu"})
run("identifiers union", lambda: (k3.sweep("acme-prod-01-eu"), k3.mapping))
run("v1 D-3 input", lambda: ((k4 := mk({"<IPV4_1>": "10.0.0.5", "<SECRET_1>": "0.5xqzw"})).sweep("10.0.0.5xqzw"), k4.mapping))
run("natural ip", lambda: ((res := R.redact("password=0.5-Xyz9\nhost 10.100.200.5-Xyz9 up")).text, res.mapping))
run("B1 short run", lambda: (mk({"<SECRET_1>": "cdef", "<SECRET_2>": "abcdefgh"}).sweep("ab<SECRET_1>gh")))
run("fold", lambda: ((res := R.redact("password=abcdefgh token=efghijkl see ａbcdefghijkl")).text, res.mapping))
