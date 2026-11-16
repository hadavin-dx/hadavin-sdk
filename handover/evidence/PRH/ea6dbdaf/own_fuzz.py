"""EVIDENCE RUNNER's own fuzz (PR H batch 8). All secrets are made-up and built from parts. Usage: python own_fuzz.py <tree-root>
Counts, per text, whether any 8-character stretch of a planted secret is still readable in the output of tools.prepare_output,
and whether the output is withheld. Controls: hidden controls, encoded ESC, a lone ESC beside a charset sequence, split
secrets (two cuts), and spaced-out secrets of 10 or more single characters."""
import json, random, sys
sys.path.insert(0, sys.argv[1] + "/src")
from hadavin_sdk import tools
from hadavin_sdk.guard import runmap
ESC = "\x1b"
HAND = "Zq4nWs" + "-8kLpv3Hd"
KEY = "AKIA" + "IOSFODNN7EXAMPLE"
PW = "password=" + "hunter" + "2secretXYZ"
LONG = "Tr0ub4dor" + "-3xyzQ" + "-Vb9mK2"
HIDDEN = {
 "esc_csi": ESC + "[0m", "esc_csi2": ESC + "[1;31m", "esc_nF": ESC + "(B", "esc_osc": ESC + "]0;t\x07", "esc_osc_st": ESC + "]0;t" + ESC + "\\",
 "esc_alone": ESC, "esc_charset_lone": ESC + ESC + "(B", "esc_lone_then_charset": ESC + "x" + ESC + "(B", "bel": "\x07", "bs": "\x08", "del": "\x7f", "nul": "\x00",
 "c1_csi": "\x9b0m", "c1_st": "\x9c", "c1_osc": "\x9d0;t\x07", "c1_dcs": "\x90",
 "zwsp": "​", "zwj": "‍", "bidi_rlo": "‮", "bidi_lri": "⁦", "wj": "⁠", "bom": "﻿", "shy": "­",
 "vs16": "️", "tag": "\U000e0041", "cgj": "͏", "hangul_filler": "ㅤ",
 "enc_pct": "%1b[0m", "enc_pct2": "%1B[31m", "enc_html": "&#27;[0m", "enc_hex": "&#x1b;[0m",
 "enc_u": "\\u001b[0m", "enc_x": "\\x1b[0m", "enc_json": json.dumps(ESC + "[0m")[1:-1], "enc_033": "\\033[0m", "enc_e": "\\e[0m",
}
def windows(secret, o):
    secret = secret.replace("password=", "")
    return [secret[i:i+8] for i in range(len(secret)-7) if secret[i:i+8] in o]
def spaced(s, sep=" "):
    return sep.join(s)
SEPS = {"sp": " ", "2sp": "  ", "tab": "\t", "nbsp": "\u00a0", "zw": "\u200b ", "mixed": " \t", "dash": " - "}
def spaced_windows(secret, o, sep):
    """a spaced-out 8-character stretch of the secret (characters joined by the separator) still readable in the output"""
    return [secret[i:i+8] for i in range(len(secret)-7) if sep.join(secret[i:i+8]) in o]
def cases():
    for sname, s in (("hand", HAND), ("key", KEY), ("pw", PW), ("long", LONG)):
        for hn, h in HIDDEN.items():
            for i in range(1, len(s)):
                yield f"{sname}/{hn}/{i}", s, "log: " + s[:i] + h + s[i:] + " end"
    r = random.Random(777)
    names = list(HIDDEN)
    for n in range(1500):
        s = r.choice([HAND, KEY, PW, LONG]); k = r.randrange(1, 4)
        cuts = sorted(r.sample(range(1, len(s)), k)); out = ""; p = 0
        for c in cuts:
            out += s[p:c] + HIDDEN[r.choice(names)]; p = c
        out += s[p:]
        yield f"rand/{n}", s, "x " + out + " y"
    # split secrets: two parts in different places of the text, hidden control between
    for n in range(300):
        s = r.choice([HAND, KEY, LONG]); i = r.randrange(2, len(s) - 2); h = HIDDEN[r.choice(names)]
        yield f"split/{n}", s, "a " + s[:i] + h + " mid text here " + s[i:] + " b"
    # spaced-out secrets of >= 10 single characters (separator variants), the handed-out one and an unknown one
    for sname, s in (("hand", HAND), ("key", KEY), ("long", LONG)):
        for sepn, sep in (("sp", " "), ("2sp", "  "), ("tab", "\t"), ("nbsp", " "), ("zw", "​ "), ("mixed", " \t"), ("dash", " - ")):
            yield f"spaced/{sname}/{sepn}", s, "log: " + spaced(s, sep) + " end"
            yield f"spaced_esc/{sname}/{sepn}", s, "log: " + spaced(s, sep).replace(sep, sep + ESC + "[0m", 3) + " end"
    UNK = "Mq8" + "Vw2Xz9" + "Lk4Pd7Rt"  # an unknown secret (not handed out), 17 chars
    for n in range(40):
        yield f"spaced_unknown/{n}", UNK, "log: " + spaced(UNK) + " end"
    yield "spaced_repeat/0", "", "log: " + " ".join("a" * 12) + " end"
def main():
    leaks = withheld = errs = tot = 0; bysec = {}; wcat = {}
    for name, s, t in cases():
        tot += 1
        cat = name.split("/")[0]
        try:
            o = tools.prepare_output(t, {}, 4000, [HAND, LONG])
        except runmap.RedactionError:
            errs += 1; continue
        if s:
            parts = name.split("/")
            if parts[0] in ("spaced", "spaced_esc"):
                w = spaced_windows(s, o, SEPS[parts[2]])
            elif parts[0] == "spaced_unknown":
                w = spaced_windows(s, o, " ")
            else:
                w = windows(s, o)
            if w:
                leaks += 1; bysec[cat] = bysec.get(cat, 0) + 1
                if "--list" in sys.argv: print("LEAK", name, w[:1])
        if o.replace(tools.MARKER, "").replace(tools.TRUNCATED, "").strip() == "" or "withheld" in o:
            withheld += 1; wcat[cat] = wcat.get(cat, 0) + 1
    print("tree", tools.__file__)
    print(f"texts={tot} readable_stretch_leaks={leaks} withheld={withheld} redaction_errors={errs}")
    print("leaks_by_category", dict(sorted(bysec.items())))
    print("withheld_by_category", dict(sorted(wcat.items())))
main()
