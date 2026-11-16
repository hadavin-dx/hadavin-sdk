"""EVIDENCE RUNNER own probe for Q8b batch 11, groups 3, 4, 5 and 8 of the r11 report. Run with PYTHONPATH=<worktree>/src.
Prints JSON {cell: {in,out,readable}}. Secrets are made up from random letters at run time."""
import json, random, sys, unicodedata
from hadavin_sdk.guard.redact import redact
import hadavin_sdk.k1b.redaction as R

def mk(n, seed):
    rnd = random.Random(seed)
    return "".join(rnd.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(n))

def readable(secret, out, k=8):
    return secret in out if len(secret) < k else any(secret[i:i+k] in out for i in range(len(secret) - k + 1))

cells = {}
SCH = ["Basic", "Token", "ApiKey", "Bearer", "Digest"]
# Group 8: continuation lines of a wrapped header, by shape
#   A = second word on the same line (space or tab), B = indented continuation line (fold), C = line break with no indent
SEP = {"A_sp": " ", "A_sp2": "  ", "A_tab": "\t", "B_lf_sp": "\n ", "B_lf_sp4": "\n    ", "B_crlf_tab": "\r\n\t", "B_lf_tab": "\n\t",
       "C_lf": "\n", "C_crlf": "\r\n", "C_cr": "\r", "C_lflf": "\n\n"}
for key in ["Authorization: ", "Proxy-Authorization: ", "X-Api-Key: ", "authorization="]:
    for sc in SCH:
        for sn, sp in SEP.items():
            for pieces in (2, 3, 4):
                parts = [mk(16, 100 * pieces + i) for i in range(pieces)]
                t = f"GET /x\n{key}{sc} " + sp.join(parts) + "\nHost: h.test\n"
                cells[f"wrap|{key.strip(': =')}|{sc}|{sn}|{pieces}"] = (t, parts)
    for sn, sp in SEP.items():  # header name, break, scheme, break, token
        tok = mk(24, 7)
        cells[f"nameBreak|{key.strip(': =')}|{sn}"] = (f"{key.strip(': =')}:{sp}Basic{sp}{tok}\n", [tok])
# Group 3/4: ordinary word + credential word pairs, digits _ . - between words
ORD = ["compass", "overpass", "encompass", "bypass", "possession", "obsession", "cookiejar", "cookiestore"]
CRED = ["key", "code", "value", "phrase", "secret", "token", "password", "id", "cookie", "direction"]
BETWEEN = ["", "_", "-", ".", "2", "_2", "2_", "-2-", ".2.", "__", "--", "1.", "12"]
for o in ORD:
    for c in CRED:
        for b in BETWEEN:
            name = o + b + c
            v = mk(20, 11)
            for form, t in [("eq", f"{name}={v}"), ("flag", f"cmd --{name} {v}"), ("flageq", f"cmd --{name}={v}"), ("json", json.dumps({name: v}))]:
                cells[f"pair|{name}|{form}"] = (t, [v])
            try:
                s = R.sensitive(name)
            except Exception as e:
                s = f"ERR {e!r}"
            cells[f"pairrec|{name}"] = (name, None, s)
# Group 5: capitals cookie check on the NFKC form: fullwidth, compat forms, mixed case, zero width, dotted
CAP = ["COOKIEJAR", "COOKIESTORE", "cookiejar", "CookieJar", "CookieJAR", "COOKIEjar",
       "ＣＯＯＫＩＥＪＡＲ",   # fullwidth COOKIEJAR
       "ｃｏｏｋｉｅｊａｒ",   # fullwidth cookiejar
       "COOKIE​JAR", "COOKIE_JAR", "COOKIE.JAR", "COOKIE-JAR", "COOKIEJAR2", "x.COOKIEJAR", "Set-COOKIESTORE",
       "ⒸOOKIEJAR", "KEY", "ΩASS", "COOKIE­JAR"]
for w in CAP:
    v = mk(20, 13)
    cells[f"cap|{ascii(w)}|eq"] = (f"{w}={v}", [v])
    cells[f"cap|{ascii(w)}|json"] = (json.dumps({w: v}), [v])
    try:
        s = R.sensitive(w)
    except Exception as e:
        s = f"ERR {e!r}"
    cells[f"caprec|{ascii(w)}|nfkc={ascii(unicodedata.normalize('NFKC', w))}"] = (w, None, s)

out = {}
for cid, cell in cells.items():
    if cell[1] is None:
        out[cid] = {"in": cell[0], "out": str(cell[2]), "readable": cell[2] is False}
    else:
        t, secrets = cell
        o = redact(t).text
        out[cid] = {"in": t, "out": o, "readable": any(readable(s, o) for s in secrets)}
json.dump(out, sys.stdout)
