# Q8b round 3 hostile probes. A = made-up value. READABLE = A (or A without whitespace) is in the output.
import sys, re
from lib import *
print("## import", path_src())
A = "<made-up-value>"
OUTS = []   # (path, text) outputs for the idempotence check
def three(text):
    return {"walk": walk({"message": text})["message"], "card": clean(text), "slack": slack(text)}
def show(label, text, shorten=None):
    r = three(text)
    for p, o in r.items():
        OUTS.append((p, o))
        mark = "READABLE" if readable(A, o) else "-"
        t = text if shorten is None else shorten(text)
        o2 = o if shorten is None else shorten(o)
        print(f"{label} | {p:5} | {mark:8} | in={t!r} | out={o2.replace(A, '<A>')!r}")
    return r

print("\n### (a) domain length before glued key")
def mk(n, dotted):
    if n == 1: return "d"
    if not dotted: return "d" * (n - 4) + ".com" if n > 4 else "d" * n
    out = ""; 
    while len(out) < n:
        out += ("d" * min(30, n - len(out) - 1) + ".") if n - len(out) > 1 else "d"
    return out[:n]
def shr(s):
    return re.sub(r"d{6,}", lambda m: f"d*{len(m.group(0))}", s)
for n in (1, 41, 100, 255, 300):
    for dotted in (False, True):
        d = mk(n, dotted); assert len(d) == n, (n, len(d))
        tag = f"dom{n}{'dotted' if dotted else 'single'}"
        show(tag + "+email", f"bob@{d}password={A}", shr)
        show(tag + "+host", f"{d}password={A}", shr)
        show(tag + "+email,token", f"bob@{d}token={A}", shr)

print("\n### (b) card text kept visible except the value")
bcases = {
 "b1": f"--password={A} --force --target prod",
 "b2": f"--password {A} word",
 "b3": f"token={A} on the primary",
 "b4": f"password={A} Plan 0123456789ab.",
 "b5": f"deploy --password={A} --force --target prod Plan 0123456789ab.",
 "b6": f"password={A} on orders-db. Plan 0123456789ab.",
}
for k, t in bcases.items():
    r = show(k, t)
    for p, o in r.items():
        words = [w for w in re.split(r"\s+", t) if A not in w and w]
        lost = [w for w in words if w not in o]
        print(f"   {k} | {p} | tokens of the input (other than the value) missing from output: {lost}")

print("\n### (b2) the real approval card (summary) and a multi-line card; Plan line is appended by the card builder")
import os
for root in ("/home/user/build/EV-Q8b-13ea6b75/wt", "/home/user/build/EV-Q8b-13ea6b75/fb_old", "/home/user/build/EV-Q8b-13ea6b75/fb_main"):
    pass
try:
    sys.path.insert(0, os.environ.get("TESTS_ROOT", "/home/user/build/EV-Q8b-13ea6b75/wt"))
    from tests.test_q8b_card_text import plan as _plan
    from hadavin_sdk.approvals.requests import summary
    for k, exp in {"c1": f"Expected: rotate token={A} on the primary", "c2": f"Expected: --password={A} --force --target prod", "c3": f"Expected: password={A} horse battery staple", "c4": f"Expected: --password {A} word"}.items():
        p_ = _plan("crm", {}).model_copy(update={"expected_outcome": exp})
        out = summary(p_, None)
        print(f"{k} | summary | {'READABLE' if readable(A, out) else '-':8} | expected_outcome={exp!r} | out={out.replace(A,'<A>')!r}")
except Exception as e:
    print("summary probe not run:", type(e).__name__, str(e)[:200])
for k, t in {"c5": f"Expected: rotate token={A} on the primary\nPlan 0123456789ab.", "c6": f"Expected: x password={A} on orders-db.\nPlan 0123456789ab."}.items():
    r = three(t)
    for pth, o in r.items(): print(f"{k} | {pth:5} | {'READABLE' if readable(A, o) else '-':8} | in={t!r} | out={o.replace(A,'<A>')!r}")

print("\n### (d) walk path value with spaces")
show("d1", f"password={A} horse battery staple")
show("d2", "passphrase=correct horse battery staple")
show("d3", f"password={A}")
for p, o in [("walk", walk({"message": f"password={A} horse battery staple"})["message"])]:
    pass
for w in ("horse", "battery", "staple", "correct"):
    pass

print("\n### (e) keys")
for k in ("dbpass", "mycredential", "usersession", "userauth", "dbaccess_key", "bypass", "compass", "oauth"):
    for sep in ("=", ": "):
        show(f"e:{k}{sep.strip()}", f"{k}{sep}{A}")
    # record path: key as dict key
    o = walk({k: A}); print(f"e:{k} | walkdict | {'READABLE' if readable(A, o) else '-':8} | out={js(o).replace(A, '<A>')}")

print("\n### (f) idempotence over every probe output")
nd = {"walk": 0, "card": 0, "slack": 0}; tot = dict(nd); ex = []
for p, o in OUTS:
    tot[p] += 1
    if p == "walk": again = walk({"message": o})["message"]
    elif p == "card": again = clean(o)
    else: again = None
    if again is not None and p == "walk": again = again.replace("\u2039", "<").replace("\u203a", ">")
    if again is not None and again != o:
        nd[p] += 1
        if len(ex) < 12: ex.append((p, o[:100], again[:100]))
print("outputs", tot, "differing on second pass (walk: after turning the escaped placeholder marks back)", nd)
for e in ex: print("   NONIDEM", e)
print("(slack outputs: second pass not applicable; the card path is applied to the Slack source text)")
