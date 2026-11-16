"""EVIDENCE RUNNER's own fuzz: planted made-up secrets with hidden controls; counts readable 8-char stretches in the output."""
import itertools, json, random, sys
from hadavin_sdk import tools
from hadavin_sdk.guard import runmap
ESC = "\x1b"
HAND = "Zq4nWs" + "-8kLpv3Hd"
KEY = "AKIA" + "IOSFODNN7EXAMPLE"
PW = "password=" + "hunter" + "2secretXYZ"
HIDDEN = {
 "esc_csi": ESC + "[0m", "esc_csi2": ESC + "[1;31m", "esc_nF": ESC + "(B", "esc_osc": ESC + "]0;t\x07", "esc_osc_st": ESC + "]0;t" + ESC + "\\",
 "esc_alone": ESC, "bel": "\x07", "bs": "\x08", "del": "\x7f", "nul": "\x00", "c1_csi": "\x9b0m", "c1_st": "\x9c",
 "zwsp": "​", "zwj": "‍", "bidi_rlo": "‮", "bidi_lri": "⁦", "wj": "⁠", "bom": "﻿", "shy": "­",
 "vs16": "️", "tag": "\U000e0041", "enc_pct": "%1b[0m", "enc_pct2": "%1B[31m", "enc_html": "&#27;[0m", "enc_hex": "&#x1b;[0m",
 "enc_u": "\\u001b[0m", "enc_x": "\\x1b[0m", "enc_json": json.dumps(ESC + "[0m")[1:-1],
}
def windows(secret, o):
    secret = secret.replace("password=", "")
    return [secret[i:i+8] for i in range(len(secret)-7) if secret[i:i+8] in o]
def cases():
    for sname, s in (("hand", HAND), ("key", KEY), ("pw", PW)):
        for hn, h in HIDDEN.items():
            for i in range(1, len(s)):
                yield f"{sname}/{hn}/{i}", s, "log: " + s[:i] + h + s[i:] + " end"
    r = random.Random(777)
    names = list(HIDDEN)
    for n in range(1500):
        s = r.choice([HAND, KEY, PW]); k = r.randrange(1, 4)
        cuts = sorted(r.sample(range(1, len(s)), k)); out = ""; p = 0
        for c in cuts:
            out += s[p:c] + HIDDEN[r.choice(names)]; p = c
        out += s[p:]
        yield f"rand/{n}", s, "x " + out + " y"
def main():
    leaks = withheld = errs = tot = 0; bysec = {}
    for name, s, t in cases():
        tot += 1
        try:
            o = tools.prepare_output(t, {}, 4000, [HAND])
        except runmap.RedactionError as e:
            errs += 1; continue
        w = windows(s, o)
        if w:
            leaks += 1; bysec[name.split("/")[0]] = bysec.get(name.split("/")[0], 0) + 1
            if "--list" in sys.argv: print("LEAK", name, w[:1])
        if o.replace(tools.MARKER, "").replace(tools.TRUNCATED, "").strip() == "" or "withheld" in o: withheld += 1
    print("tree", tools.__file__); print(f"texts={tot} readable_stretch_leaks={leaks} withheld={withheld} redaction_errors={errs} leaks_by_secret={bysec}")
main()
