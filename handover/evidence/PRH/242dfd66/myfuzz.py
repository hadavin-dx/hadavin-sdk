"""EVIDENCE RUNNER own fuzz (typed by the runner from the brief's list). Usage: myfuzz.py <tree> <out.json>.
Prints counts only; made-up values are built from parts and never written out."""
import json, os, random, signal, sys, unicodedata, collections
tree, outp = sys.argv[1], sys.argv[2]
sys.path.insert(0, tree + "/src")
from hadavin_sdk import tools, defaults
from hadavin_sdk.guard import runmap
assert os.path.realpath(tools.__file__).startswith(os.path.realpath(tree)), tools.__file__
HAND = "".join(["vK4n", "Ts8Q", "w2Ld", "Rm6x", "Bf9H", "jYc3", "pZ5g"])            # a value handed to a tool (28 chars)
SHAPED = "".join(["gh", "p_", "Xr4Tn7Bq", "L2mVd9Ks", "Wf6HjC3z", "Pa8Ey5Nu"])       # token-shaped value
ESCS = ["\x1b[0m", "\\x1b[0m", "\\u001b[0m", "\\033[0m", "\\e[0m", "\\E[0m", "%1b[0m", "%1B[31m", "&#27;[0m", "&#x1b;[0m", "\\x1b", "\\e", "\x1b", "\x1b(B", "\x9b0m"]
CTRL = ["\x01", "\x07", "\x08", "\x7f", "\u200b", "\u2060", "\ufeff", "\u00ad", "\u202e", "\u200d", "\u034f", "\x0b", "\x0c"]
WRAP = list("`*_~<>{}|[]()#\"'") + ["**", "``", "<<", "[[", "(("]
SPLIT = ["\n", " and then ", "<b>", "\r\n", "...", " + ", '" + "', "\t", "-", " (see log) "]

def build():
    C = []  # (label, secret_key, secret, text)
    for key, S in (("hand", HAND), ("shaped", SHAPED)):
        for i, c in enumerate(CTRL):
            for k in (1, 2, 4):
                C.append((f"ctrl/{key}/{i}/{k}", key, S, c.join(S[j:j+k] for j in range(0, len(S), k))))
            C.append((f"ctrlmid/{key}/{i}", key, S, "key=" + S[:len(S)//2] + c + S[len(S)//2:]))
        for i, e in enumerate(ESCS):
            C.append((f"esc_mid/{key}/{i}", key, S, S[:9] + e + S[9:]))
            C.append((f"esc_each/{key}/{i}", key, S, e.join(S)))
            C.append((f"esc_each2/{key}/{i}", key, S, e.join(S[j:j+2] for j in range(0, len(S), 2))))
            C.append((f"esc_ctx/{key}/{i}", key, S, f"token={e}{S}{e} done"))
        # backslash-e in paths with the secret after
        for i, p in enumerate(["C:\\env\\x", "C:\\Users\\err\\x", "C:\\Documents\\error_logs", "D:\\err\\env\\e", "\\env", "a\\e b"]):
            C.append((f"bslpath/{key}/{i}", key, S, f"open {p} then token={S}"))
            C.append((f"bslpath_in/{key}/{i}", key, S, f"{S[:12]}{p}{S[12:]}"))
        # spaced out, wrappers, combining marks
        for sepn, sep in (("sp", " "), ("tab", "\t"), ("nl", "\n"), ("zw", "\u200b"), ("dash", "-"), ("dot", ". ")):
            C.append((f"spaced/{key}/{sepn}", key, S, sep.join(S)))
            for wi, w in enumerate(WRAP):
                C.append((f"spaced_w/{key}/{sepn}/{wi}", key, S, w + sep.join(S) + w))
                C.append((f"spaced_wf/{key}/{sepn}/{wi}", key, S, "pw: " + w + sep.join(S)))
            C.append((f"spaced_cm/{key}/{sepn}", key, S, sep.join(ch + "\u0301" for ch in S)))
            C.append((f"spaced_cm2/{key}/{sepn}", key, S, sep.join(ch + "\u0308\u0323" for ch in S)))
            C.append((f"spaced_cm_w/{key}/{sepn}", key, S, "**" + sep.join(ch + "\u0301" for ch in S) + "**"))
        # split secrets
        for i, sp in enumerate(SPLIT):
            for k in (5, 10, 15, 20):
                C.append((f"split/{key}/{i}/{k}", key, S, S[:k] + sp + S[k:]))
            C.append((f"split3/{key}/{i}", key, S, S[:7] + sp + S[7:14] + sp + S[14:21] + sp + S[21:]))
        # run cap
        cap = defaults.MAX_REDACT_CHARS
        pad = "ordinary line of output\n"
        base = (pad * (cap // len(pad) + 3))
        C.append((f"cap_front/{key}", key, S, S + "\n" + base))
        C.append((f"cap_end/{key}", key, S, base + S))
        for off in (-40, -28, -14, -3, 0, 5):
            at = cap + off
            C.append((f"cap_straddle/{key}/{off}", key, S, base[:at] + S + base[at:]))
        C.append((f"cap_spaced_straddle/{key}", key, S, base[:cap-30] + " ".join(S) + base[cap-30:]))
        C.append((f"cap_esc_straddle/{key}", key, S, base[:cap-20] + "\x1b[0m".join(S) + base[cap-20:]))
        C.append((f"cap_exact/{key}", key, S, (pad * 9999)[:cap - 1] + S[0]))
    return C

def readable(S, out):
    norm = lambda t: "".join(ch for ch in unicodedata.normalize("NFKD", t) if ch.isalnum()).casefold()
    o = norm(out); n = norm(S)
    return any(n[j:j+8] in o for j in range(0, len(n) - 7))

def run_case(text, secret_key, S):
    class TO(Exception): pass
    def h(*a): raise TO()
    signal.signal(signal.SIGALRM, h); signal.alarm(60)
    try:
        secrets = [HAND] if secret_key == "hand" else []
        out = tools.prepare_output(text, {}, 4000, secrets)
        return "ok", out
    except TO:
        return "timeout", ""
    except BaseException as e:
        return "err:" + type(e).__name__, ""
    finally:
        signal.alarm(0)

res = collections.Counter(); rows = {}
for label, key, S, text in build():
    st, out = run_case(text, key, S)
    withheld = st == "ok" and out.startswith(tools.MARKER) and len(out) <= len(tools.MARKER) + len(tools.TRUNCATED)
    r = st == "ok" and not withheld and readable(S, out)
    cls = label.split("/")[0]
    rows[label] = "ERR:" + st if st != "ok" else ("READABLE" if r else ("withheld" if withheld else "masked"))
    res["total"] += 1
    res["readable" if r else ("withheld" if withheld else ("error" if st != "ok" else "masked"))] += 1
    if st != "ok": res["err/" + st] += 1
    res[f"{cls}:" + rows[label]] += 1

# redactor crash must stop the run (head only has RedactorCrash)
crash = {}
RC = getattr(runmap, "RedactorCrash", None)
real = runmap.redact_untrusted
for name, txt in (("hidden", "line one \x1b[0m line two " + HAND[:0]), ("plain", "plain text with nothing hidden"), ("spaced", " ".join("passwordx"))):
    def boom(*a, **k): raise RuntimeError("planted bug")
    runmap.redact_untrusted = boom
    st, out = run_case(txt, "hand", HAND)
    runmap.redact_untrusted = real
    crash[name] = st if st != "ok" else ("RETURNED:" + ("limit-marker" if out.startswith(tools.MARKER) else "text"))
for name in ("redact_bounded", "redact_layered"):
    if hasattr(runmap, name) or hasattr(tools, name):
        pass
mod = runmap if hasattr(runmap, "redact_bounded") else None
if mod is not None:
    realb = runmap.redact_bounded
    def boom2(*a, **k): raise RuntimeError("planted bug")
    runmap.redact_bounded = boom2
    try:
        r = tools.error_reason(ValueError("bad value"))
        crash["error_reason"] = "RETURNED"
    except BaseException as e:
        crash["error_reason"] = "err:" + type(e).__name__
    runmap.redact_bounded = realb
json.dump({"counts": dict(res), "crash": crash, "rows": rows}, open(outp, "w"), indent=0, sort_keys=True)
c = dict(res)
print(tree.split("/")[-1], {k: v for k, v in c.items() if ":" not in k}, crash)
