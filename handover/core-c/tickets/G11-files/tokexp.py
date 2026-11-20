"""G11 token experiment. cd TREE; PYTHONPATH=... python tokexp.py N OUT.json
(1) the G8 v6 2.4b experiment: random base64url tokens, 4 length classes x N, after `key` and bare; leak = 8+ token characters readable outside
    placeholders next to a placeholder in the result. (2) injected: a UUID or a 10/11 digit number set off by `_` inside a random token of 20-60 other chars."""
import random, re, difflib, sys, json, importlib
importlib.import_module("hadavin_sdk.guard.redact")
from hadavin_sdk.guard.redact import redact
A = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
PH = re.compile(r"<[A-Z][A-Z0-9]*_\d+>")
N = int(sys.argv[1]); res = {}
def readable(tok, text):
    rest = PH.sub("\x00", text)
    if "\x00" not in rest: return 0
    return difflib.SequenceMatcher(None, tok, rest, autojunk=False).find_longest_match(0, len(tok), 0, len(rest)).size
for mode in ("key", "bare"):
    for lo, hi in ((40, 61), (62, 75), (76, 128), (129, 163)):
        rnd = random.Random(f"20261120|{lo}-{hi}|key|v6")
        leaks = []; ph = 0
        for i in range(N):
            tok = "".join(rnd.choice(A) for _ in range(rnd.randint(lo, hi)))
            r = redact(f"{mode} {tok} end" if mode == "key" else f"log {tok} end")
            ph += bool(r.mapping and any(not k.startswith("<HIGHENTROPY") and not k.startswith("<SECRET") for k in r.mapping))
            if readable(tok, r.text) >= 8: leaks.append(i)
        res[f"{mode}|{lo}-{hi}"] = {"leaks": leaks, "other_kind_masks": ph}
rnd = random.Random("g11inj")
H = "0123456789abcdef"
for kind in ("uuid", "ph10", "ph11"):
    leaks = []; tot = 0
    for i in range(N // 4):
        def seg(n): return "".join(rnd.choice(A.replace("-", "")) for _ in range(n))
        if kind == "uuid": v = "-".join("".join(rnd.choice(H) for _ in range(k)) for k in (8, 4, 4, 4, 12))
        else: v = "".join(rnd.choice("0123456789") for _ in range(10 if kind == "ph10" else 11)); v = "4" + v[1:]
        a, b = rnd.randint(0, 40), rnd.randint(0, 40)
        sep = rnd.choice(["_", ""]) if kind == "uuid" else "_"
        sepb = sep if kind == "uuid" else "_"
        tok = seg(a) + (sep if a else "") + v + (sepb if b else "") + seg(b)
        if len(tok) < 40 or not (re.search("[A-Z]", tok) and re.search("[a-z]", tok) and re.search(r"\d", tok)): continue
        tot += 1
        r = redact(f"log {tok} end")
        rest = PH.sub("\x00", r.text)
        if readable(tok, r.text) >= 8 or (v in rest): leaks.append(tok)
    res[f"inj|{kind}"] = {"n": tot, "leaks": len(leaks), "examples": leaks[:2]}
json.dump(res, open(sys.argv[2], "w"))
print({k: (len(v["leaks"]) if isinstance(v["leaks"], list) else v["leaks"], v.get("other_kind_masks", v.get("n"))) for k, v in res.items()})
