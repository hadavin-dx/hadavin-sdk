"""EVIDENCE RUNNER probe (own, typed from Q8b ticket tables and the r10 report). Run with PYTHONPATH=<worktree>/src.
Prints JSON: {cell_id: {"in":..., "out":..., "readable": bool}}"""
import json, random, sys
from hadavin_sdk.guard.redact import redact
import hadavin_sdk.k1b.redaction as R

def mk(n, kind="mixed", seed=0):
    rnd = random.Random(seed * 1000 + n)
    if kind == "lower":
        a = "abcdefghijklmnopqrstuvwxyz"
    else:
        a = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    s = "".join(rnd.choice(a) for _ in range(n))
    if kind == "dot": s = s[:3] + "." + s[4:]
    if kind == "tilde": s = s[:4] + "~" + s[5:]
    if kind == "colon": s = s[:5] + ":" + s[6:]
    if kind == "dash": s = s[:6] + "-" + s[7:]
    return s

def readable(secret, out, k=8):
    # any k-gram of the secret that survives in the output
    if len(secret) < k: return secret in out
    return any(secret[i:i+k] in out for i in range(len(secret) - k + 1))

cells = {}
GAPS = {"sp1": " ", "sp2": "  ", "sp5": "     ", "tab": "\t", "lf": "\n", "crlf": "\r\n", "cr": "\r", "lflf": "\n\n",
        "crlfcrlf": "\r\n\r\n", "lf_sp": "\n    ", "crlf_tab": "\r\n\t", "vt": "\x0b", "pct0b": "%0b", "lf_tab_lf": "\n\t\n"}
SCHEMES = ["Basic", "Token", "ApiKey", "Digest", "Bearer", "Bearer-like"]
PREFIX = {"auth": "Authorization: ", "none": "", "proxy": "Proxy-Authorization: "}
LENS = [8, 9, 12, 15, 16, 17, 20, 32, 48, 64]
KINDS = ["mixed", "lower", "dot", "tilde", "colon", "dash"]
for pf, pt in PREFIX.items():
    for sc in SCHEMES:
        for gn, g in GAPS.items():
            for kd in KINDS:
                for n in LENS:
                    if kd in ("dot", "tilde", "colon", "dash") and n not in (8, 12, 16, 32): continue
                    tok = mk(n, kd)
                    t = f"GET /x\n{pt}{sc}{g}{tok}\nHost: example.test\n"
                    cells[f"hdr|{pf}|{sc}|{gn}|{kd}|{n}"] = (t, [tok])
# folded headers 2-4 lines
for sc in ["Digest", "Basic", "Token", "ApiKey", "Bearer"]:
    for nl, nm in [("\n", "lf"), ("\r\n", "crlf")]:
        for lines in (2, 3, 4):
            for ind in (" ", "    ", "\t"):
                parts = [mk(32, "mixed", i + 1) for i in range(lines)]
                if sc == "Digest":
                    t = f'Authorization: Digest username="u",{nl}' + "".join(f'{ind}f{i}="{p}",{nl}' for i, p in enumerate(parts[:-1])) + f'{ind}response="{parts[-1]}"\n'
                else:
                    t = f"Authorization: {sc} {parts[0]}{nl}" + "".join(f"{ind}{p}{nl}" for p in parts[1:])
                cells[f"fold|{sc}|{nm}|{lines}|{ind!r}"] = (t, parts)
# ordinary-word pairs
WORDS = ["compass", "overpass", "encompass", "possession_id", "obsession_id", "cookiejar", "COOKIEJAR", "COOKIESTORE", "cookiestore",
         "bypass", "protection_bypass", "compass_key", "overpass_key", "encompass_key", "compass_secret", "compass_token",
         "compass_password", "compass_code", "overpass_value", "encompass_phrase", "bypass_key", "bypass_token", "password", "api_key"]
for w in WORDS:
    v = mk(24, "mixed", 7)
    for form, t in [("eq", f"{w}={v}"), ("colon", f"{w}: {v}"), ("json", json.dumps({w: v})), ("q", f'{w}="{v}"'), ("flag", f"cmd --{w} {v}")]:
        cells[f"word|{w}|{form}"] = (t, [v])
    cells[f"wordshort|{w}|eq"] = (f"{w}=true", ["true"])
def run():
    out = {}
    for cid, (t, secrets) in cells.items():
        o = redact(t).text
        out[cid] = {"in": t, "out": o, "readable": any(readable(s, o) for s in secrets), "parts": [i for i, s in enumerate(secrets) if readable(s, o)]}
    # record path
    for w in WORDS:
        v = mk(24, "mixed", 9)
        try:
            sens = R.sensitive(w)
        except Exception as e:
            sens = f"ERR {e!r}"
        out[f"recordsens|{w}"] = {"in": w, "out": str(sens), "readable": sens is False}
    return out
if __name__ == "__main__":
    json.dump(run(), sys.stdout)
