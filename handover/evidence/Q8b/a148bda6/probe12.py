"""EVIDENCE RUNNER own probe for Q8b batch 12 (round 12 report groups 1, 4, 8). Run with PYTHONPATH=<worktree>/src.
Prints JSON {cell: {in,out,readable}}. Secrets are made up from random letters at run time, never written as literals."""
import json, random, sys
from hadavin_sdk.guard.redact import redact
# the 15 ordinary words of the head's ORDINARY_WORDS table (main has no such table), copied by hand so all three trees get the same cells
ORDINARY_WORDS = frozenset("bypass compass encompass overpass underpass surpass trespass impass lowpass highpass bandpass obsession possession repossession supersession".split())
import hadavin_sdk.k1b.redaction as R

def mk(n, seed):
    rnd = random.Random(seed)
    return "".join(rnd.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(n))

def readable(secret, out, k=8):
    return secret in out if len(secret) < k else any(secret[i:i+k] in out for i in range(len(secret) - k + 1))

cells = {}
SCHEMES = ["Basic", "Bearer", "Token", "ApiKey", "Digest", "NTLM", "Negotiate", "OAuth", "Splunk", "Hawk", "AWS", "AWS4-HMAC-SHA256", "Custom-Scheme", "none"]
NAMES = ["Authorization", "authorization", "Proxy-Authorization", "AUTHORIZATION"]
BREAKS = {"lf": "\n", "crlf": "\r\n", "cr": "\r", "u2028": " ", "u2029": " ", "vt": "\x0b", "ff": "\x0c", "nel": "\x85", "fs": "\x1c", "gs": "\x1d", "rs": "\x1e"}
INDENTS = {"sp": " ", "sp4": "    ", "tab": "\t", "none": ""}
EXTRA = ["", " x", " x y", " x y z", " ab cd ef gh ij"]
# folded: name: scheme tok1 <extra words> BREAK INDENT tok2 BREAK INDENT tok3
for nm in NAMES[:3]:
    for sc in SCHEMES:
        for bn, b in BREAKS.items():
            for ind_n, ind in INDENTS.items():
                for ei, ex in enumerate(EXTRA):
                    t1, t2, t3 = mk(24, 1), mk(24, 2), mk(24, 3)
                    head = f"{nm}: " + (f"{sc} " if sc != "none" else "")
                    t = f"GET /x\n{head}{t1}{ex}{b}{ind}{t2}{b}{ind}{t3}\nHost: h.test\n"
                    shape = "C" if ind == "" else "B"
                    cells[f"fold12|{shape}|{nm}|{sc}|{bn}|{ind_n}|extra{ei}"] = (t, [t1, t2, t3])
# shape A: secret cut on the same line (space / tab / several spaces), with every scheme
for nm in NAMES[:3]:
    for sc in SCHEMES:
        for sp_n, sp in {"sp": " ", "sp2": "  ", "tab": "\t", "sp5": "     "}.items():
            for pieces in (2, 3):
                parts = [mk(16, 50 + i) for i in range(pieces)]
                head = f"{nm}: " + (f"{sc} " if sc != "none" else "")
                cells[f"shapeA|{nm}|{sc}|{sp_n}|{pieces}"] = (f"GET /x\n{head}{sp.join(parts)}\nHost: h.test\n", parts)
# bare ordinary words (the whole table of the head), every form (owner decision: they stay shown, record what is shown)
for w in sorted(ORDINARY_WORDS):
    v = mk(24, 7)
    for form, t in [("eq", f"{w}={v}"), ("colon", f"{w}: {v}"), ("json", json.dumps({w: v})), ("q", f'{w}="{v}"'), ("flag", f"cmd --{w} {v}"), ("jsonq", '{"%s": "%s"}' % (w.upper(), v))]:
        cells[f"bare15|{w}|{form}"] = (t, [v])
    try:
        s = R.sensitive(w)
    except Exception as e:
        s = f"ERR {e!r}"
    cells[f"bare15rec|{w}"] = (w, None, s)
# ordinary word + credential word pairs, quoted and json forms, digits and joiners between
ORD = sorted(ORDINARY_WORDS)
CRED = ["key", "secret", "token", "password", "passwd", "code", "id", "cookie", "auth", "credential"]
BETWEEN = ["", "_", "-", ".", "2", "_2", "2_", "-2-", ".2.", "__", "--", "12", "_-.", " "]
for o in ORD:
    for c in CRED:
        for b in BETWEEN:
            name = o + b + c
            v = mk(20, 11)
            for form, t in [("eq", f"{name}={v}"), ("q", f'{name}="{v}"'), ("json", json.dumps({name: v})), ("jsonsp", '{ "%s" : "%s" }' % (name, v)),
                            ("flag", f"cmd --{name} {v}"), ("single", f"{name}='{v}'"), ("upper", f"{name.upper()}={v}")]:
                cells[f"pair12|{name!r}|{form}"] = (t, [v])
            try:
                s = R.sensitive(name)
            except Exception as e:
                s = f"ERR {e!r}"
            cells[f"pair12rec|{name!r}"] = (name, None, s)
out = {}
for cid, cell in cells.items():
    if cell[1] is None:
        out[cid] = {"in": cell[0], "out": str(cell[2]), "readable": cell[2] is False}
    else:
        t, secrets = cell
        o = redact(t).text
        out[cid] = {"in": t, "out": o, "readable": any(readable(s, o) for s in secrets)}
json.dump(out, sys.stdout)
