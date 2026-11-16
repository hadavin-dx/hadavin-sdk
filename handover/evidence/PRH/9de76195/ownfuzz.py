"""Own fuzz (evidence runner, typed from the ticket's table). Usage: python ownfuzz.py <tree> <out.jsonl>. No readable value printed."""
import hashlib, json, signal, sys, glob, os
tree, outp = sys.argv[1], sys.argv[2]
sys.path.insert(0, tree + "/src")
from hadavin_sdk import tools
from hadavin_sdk.guard import runmap
assert os.path.realpath(tools.__file__).startswith(os.path.realpath(tree))
HAND = "".join(["qZ7k", "M3vR", "t9Lx", "P2wB", "n5Hc", "D8fJ", "s4Yg"])      # handed-out secret, 28 chars
SHAPED = "".join(["gh", "p_", "Ab3dE6gH", "9jK2mN5p", "Q8sT1vW4", "yZ7aC0eF"])   # token-shaped, made up from parts
VALUES = {"hand": HAND, "shaped": SHAPED}
CTRL = ["\x01", "\x07", "\x08", "\x7f", "​", "⁠", "﻿", "­", "‮", "\x00", "\x1b[0m", "\x1b[31m", "\x9b0m"]
ESC = ["\x1b[0m", "\\x1b[0m", "\\u001b[0m", "\\033[0m", "\\e[0m", "\\E[0m", "%1b[0m", "%1B[31m", "&#27;[0m", "&#x1b;[0m", "\\x1b", "\\e", "\x1b"]
CHARSET = ["\x1b(B", "\x1b)0", "\x1b#8", "\x1b%G", "\x1b(0", "\x1b*A", "\x1b+B", "\x1b-A", "\x1b.A", "\x1b/A", "\x1b ", "\x1b"]
SPLITS = ["\n", " ", "<b>", "</b>", "\r\n", "...", "+", '" + "', "'\n'", "\t", "\\n", "-"]
SEPS = {"space": " ", "zw": "​", "zwsp-sp": "​ ", "tab": "\t", "nbsp": " ", "nl": "\n", "esc": "\x1b[0m", "mix": " ​", "ctrl": "\x07", "dash-sp": " ⁠ "}
OPENERS = ["\x1b]0;title", "\x1bP", "\x1b_", "\x1b^", "\x1bX", "\x9d", "\x90", "\x9e", "\x9f", "\x98", "\x1b[", "\x1b]8;;http://x.invalid/", "\x1b]52;c;"]
FILL = ["noise word ", "ok\n", ""]
def cases():
    for vn, S in VALUES.items():
        for i, c in enumerate(CTRL):
            for k in (1, 2, 3, 5):
                yield f"hidden/{vn}/{i}/{k}", S, c.join(S[j:j+k] for j in range(0, len(S), k))
            yield f"hidden_mid/{vn}/{i}", S, S[:len(S)//2] + c + S[len(S)//2:]
        for i, e in enumerate(ESC):
            yield f"esc_mid/{vn}/{i}", S, S[:9] + e + S[9:]
            yield f"esc_each/{vn}/{i}", S, e.join(S)
            yield f"esc_pre/{vn}/{i}", S, e + S
            yield f"esc_ctx/{vn}/{i}", S, f"token={e}{S}"
        for i, c in enumerate(CHARSET):
            yield f"charset_mid/{vn}/{i}", S, S[:11] + c + S[11:]
            yield f"charset_pre/{vn}/{i}", S, c + S
            yield f"charset_pairs/{vn}/{i}", S, c.join(S[j:j+2] for j in range(0, len(S), 2))
            yield f"loneesc_then/{vn}/{i}", S, "\x1b" + c + S
            yield f"loneesc_end/{vn}/{i}", S, S + "\x1b" + c
        for i, sp in enumerate(SPLITS):
            for k in (4, 8, 12, 17, 22):
                yield f"split/{vn}/{i}/{k}", S, S[:k] + sp + S[k:]
            yield f"split3/{vn}/{i}", S, S[:7] + sp + S[7:15] + sp + S[15:]
        for sn, sp in SEPS.items():
            for n in (10, 12, 16, len(S)):
                yield f"spaced/{vn}/{sn}/{n}", S[:n], sp.join(S[:n])
            yield f"spaced_ctx/{vn}/{sn}", S, "password: " + sp.join(S)
            yield f"spaced_mixed/{vn}/{sn}", S, S[:9] + sp + sp.join(S[9:])
        for oi, o in enumerate(OPENERS):
            for fi, f in enumerate(FILL):
                yield f"opener/{vn}/{oi}/{fi}", S, f + o + " " + S + "\nmore text after\n"
                yield f"opener_spaced/{vn}/{oi}/{fi}", S, f + o + " " + " ".join(S) + "\nmore\n"
                yield f"opener_split/{vn}/{oi}/{fi}", S, f + o + S[:12] + "\n" + S[12:]
    # run cap: n made-up spaced runs (12 different characters each, no real value) then the planted secret spaced
    for n in (1, 16, 30, 31, 32, 33, 34, 40, 64, 200):
        runs = []
        for r in range(n):
            base = "".join(chr(97 + (r + j * 3) % 26) for j in range(12))
            runs.append(" ".join(base))
        for vn, S in VALUES.items():
            yield f"runcap/{vn}/{n}/end", S, "\n".join(runs) + "\nkey: " + " ".join(S)
            yield f"runcap/{vn}/{n}/front", S, "key: " + " ".join(S) + "\n" + "\n".join(runs)
            yield f"runcap/{vn}/{n}/none", "", "\n".join(runs)
def windows_in(S, out):
    low = out
    for sep in ("", " ", "​", "\t", "\n", "\x1b[0m", "\x07", "⁠", " "):
        flat = low.replace(sep, "") if sep else low
        for j in range(0, len(S) - 7):
            if S[j:j+8] in flat: return True
    return False
class TO(Exception): pass
def al(*a): raise TO()
signal.signal(signal.SIGALRM, al)
rows = []
for name, S, t in cases():
    err, o = "", ""
    signal.alarm(30)
    try:
        o = tools.prepare_output(t, {}, 4000, [HAND])
    except runmap.RedactorCrash as e: err = "RedactorCrash"
    except runmap.RedactionLimit as e: err = "RedactionLimit"
    except runmap.RedactionError as e: err = "RedactionError:" + type(e).__name__
    except TO: err = "TIMEOUT"
    except BaseException as e: err = "OTHER:" + type(e).__name__
    finally: signal.alarm(0)
    wh = err == "" and (o.replace(tools.MARKER, "").replace(tools.TRUNCATED, "").strip() == "" or "withheld" in o.lower())
    rd = bool(S) and err == "" and windows_in(S, o)
    rows.append({"cell": name, "readable": rd, "withheld": bool(wh), "err": err, "h": hashlib.sha256(t.encode("utf-8", "replace")).hexdigest()[:12]})
# clean corpus: files of the HEAD tree (same files for every tree), 3000-char chunks
corpus_root = sys.argv[3] if len(sys.argv) > 3 else tree
files = sorted(glob.glob(corpus_root + "/docs/**/*.md", recursive=True) + glob.glob(corpus_root + "/*.md") + glob.glob(corpus_root + "/src/hadavin_sdk/*.py"))
chunks = 0; cw = 0; cerr = 0
for f in files:
    try: txt = open(f, encoding="utf-8").read()
    except Exception: continue
    for i in range(0, min(len(txt), 30000), 3000):
        c = txt[i:i+3000]; chunks += 1
        signal.alarm(30)
        try:
            o = tools.prepare_output(c, {}, 4000, [HAND])
            if o.replace(tools.MARKER, "").replace(tools.TRUNCATED, "").strip() == "" or "withheld" in o.lower(): cw += 1
        except BaseException as e: cerr += 1
        finally: signal.alarm(0)
rows.append({"cell": "CLEAN", "files": len(files), "chunks": chunks, "withheld": cw, "errors": cerr})
with open(outp, "w") as fh:
    for r in rows: fh.write(json.dumps(r) + "\n")
cs = [r for r in rows if r["cell"] != "CLEAN"]
print(tree.rsplit("/", 1)[-1], "texts", len(cs), "readable", sum(r["readable"] for r in cs), "withheld", sum(r["withheld"] for r in cs), "errors", sum(1 for r in cs if r["err"]), "| clean chunks", chunks, "withheld", cw, "errors", cerr)
