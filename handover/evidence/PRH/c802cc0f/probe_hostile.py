"""EVIDENCE RUNNER own hostile rows (c802cc0f). Made-up values built from parts. readable = an 8-character window of the
secret stands in the output; squashed = same after removing spaces and zero-width/bidi/control characters."""
import re, sys
from hadavin_sdk import tools
from hadavin_sdk.guard import runmap
from hadavin_sdk.guard.redact import redact
ESC, BEL, ZW, RLO, LRI, PDI, BOM = "\x1b", "\x07", "​", "‮", "⁦", "⁩", "﻿"
KEY = "AKIA" + "IOSFODNN7EXAMPLE"
HEXC = "9F3A" + "C7B2" + "E1D04A6B" + "55C8F0123D7E9A4B"   # 32 capital hex
HEXL = HEXC.lower()
HAND = "Qx7mLp" + "-9vRtzKw2"
def cut(s, i, sep): return s[:i] + sep + s[i:]
ROWS = {
 "X1 capital hex under ENCRYPTION_KEY=": ("ENCRYPTION_KEY=" + HEXC, [HEXC]),
 "X1b lowercase hex control": ("ENCRYPTION_KEY=" + HEXL, [HEXL]),
 "X2 capital hex cut by ZW": ("ENCRYPTION_KEY=" + cut(HEXC, 13, ZW), [HEXC]),
 "X3 capital hex cut by RLO and LRI+PDI": ("ENCRYPTION_KEY=" + cut(cut(HEXC, 9, RLO), 20, LRI + PDI), [HEXC]),
 "X4 hex ZW+bidi+ESC[0m+BEL mix": ("ENCRYPTION_KEY=" + cut(cut(cut(cut(HEXC, 5, ZW), 11, RLO), 17, ESC + "[0m"), 26, BEL), [HEXC]),
 "X5 KEY 2 copies plain + ZW-cut": ("a " + KEY + " b " + cut(KEY, 7, ZW), [KEY]),
 "X6 KEY 3 copies plain, ZW, ESC[0m": ("a " + KEY + " b " + cut(KEY, 7, ZW) + " c " + cut(KEY, 10, ESC + "[0m"), [KEY]),
 "X7 KEY 3 copies all cut differently (ZW, RLO, BOM)": ("a " + cut(KEY, 4, ZW) + " b " + cut(KEY, 9, RLO) + " c " + cut(KEY, 14, BOM), [KEY]),
 "X8 KEY spaced out": ("id " + " ".join(KEY), [KEY]),
 "X9 KEY spaced out with ZW": ("id " + (" " + ZW).join(KEY), [KEY]),
 "X10 KEY spaced + copy ESC-cut": ("id " + " ".join(KEY) + " and " + cut(KEY, 6, ESC + "[m"), [KEY]),
 "X11 HAND 3 copies (plain, ESC-prefix, ESC(B ESC[m cut)": ("x " + HAND + " y " + ESC + HAND + " z " + HAND[:9] + ESC + "(B" + ESC + "[m" + HAND[9:], [HAND]),
 "X12 HAND ZW-cut + bidi-cut": ("x " + cut(HAND, 6, ZW) + " y " + cut(HAND, 4, RLO), [HAND]),
 "X13 HAND spaced out": ("x " + " ".join(HAND), [HAND]),
 "X14 mixed: HAND x2 + KEY x2 + HEXC cut": ("a " + HAND + " " + cut(HAND, 5, ZW) + " b " + KEY + " " + cut(KEY, 8, RLO) + " c ENCRYPTION_KEY=" + cut(HEXC, 14, ZW + ESC + "[0m"), [HAND, KEY, HEXC]),
 "X15 HAND cut by ZW at end, TRUNCATED tail": ("log " + cut(HAND, 11, ZW) + tools.TRUNCATED, [HAND]),
}
def win(s, n=8): return {s[i:i+n] for i in range(len(s)-n+1)}
def sq(o): return re.sub(r"[\s​-‏‪-‮⁦-⁩﻿\x00-\x1f\x7f]", "", o)
def verdict(out, secs, label):
    r = any(w in out for s in secs for w in win(s)); q = any(w in sq(out) for s in secs for w in win(s))
    return ("R" if r else ("sq" if q else "-"))
def m():
    d = {}; runmap.redact_text("seen ip 10.20.30.44", d); return d
print("tree", tools.__file__)
print("row | untrusted | tool | error | head | redact()   (R = readable window; sq = readable only after removing spaces/controls; - = none; E = exception)")
for n, (t, secs) in ROWS.items():
    res = []
    for name, f in [("u", lambda: runmap.redact_untrusted(t, m())), ("t", lambda: tools.prepare_output(t, m(), 4000, [HAND])),
                    ("e", lambda: tools.error_reason(ValueError(t), [HAND])), ("h", lambda: runmap.safe_head(t, 4000, m())),
                    ("r", lambda: (lambda x: x.text if hasattr(x,"text") else str(x))(redact(t)))]:
        try: out = f(); res.append(verdict(out, secs, name) + ("" if True else ""))
        except Exception as e: res.append("E:" + type(e).__name__); out = ""
    print(n, "|", " | ".join(res), "|| t-out=", repr(tools.prepare_output(t, m(), 4000, [HAND]))[:90])
