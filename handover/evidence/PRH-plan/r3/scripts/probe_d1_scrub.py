"""D1 probe (PR H rev 3): a handed-out secret in the same tool result as a key that main masks only because a
hidden item acts as a word boundary (G2 shape), and the step-6 fallback reachability count.
Mode: main | proto (author's rev-2 prototype + rev-2 fixes) | rev3 (proto with the rev-3 _scrub rule: find on the
joined copy, return the SPACED copy with the gap-pattern mask, never the joined text)."""
import re, sys
sys.path.insert(0, "/home/user/build/prh-author/errata")
MODE = sys.argv[1]
from hadavin_sdk import tools
from hadavin_sdk.guard import runmap
print("MODE", MODE, "| hadavin_sdk from", sys.modules["hadavin_sdk"].__file__)
ESC, BEL = "\x1b", "\x07"
KEY = "AKIA" + "IOSFODNN7EXAMPLE"; HAND = "Tr0ub4dor" + "-3xyzQ"
if MODE in ("proto", "rev3"):
    import prh_proto as proto, fixes
    proto.install(); fixes.install()
if MODE == "rev3":
    _inner = tools._scrub_layers
    def gap(value):  # the step-5 gap pattern: at most one space between neighbouring characters
        return re.compile(" ?".join(re.escape(c) for c in value))
    def scrub(raw, long_enough, sc=tools._DEFAULT_SCRUB):
        joined, spaced = proto.strip(raw)
        try:
            found = _inner(joined, long_enough, sc)
        except runmap.TooDeep:
            return tools.MARKER + tools.TRUNCATED
        if found == joined:
            return raw
        masked = spaced
        for s in sorted(long_enough, key=len, reverse=True):
            masked = gap(s).sub(tools.MARKER, masked)
        try:
            out = _inner(masked, long_enough, sc)
        except runmap.TooDeep:
            return tools.MARKER + tools.TRUNCATED
        j = proto.strip(out)[0]
        if any(f in j or f in tools._decoded(j) for s in long_enough for f in tools._secret_forms(s)):
            return tools.MARKER + tools.TRUNCATED  # backstop: withheld, never the joined text
        return out
    tools._scrub = scrub
ROWS = [
    ("D1a handed-out secret + G2 key", "auth failed for " + HAND + " ; INFO user" + ESC + "[0m" + KEY, [HAND]),
    ("D1b handed-out secret cut + G1 key", "auth failed for " + HAND[:9] + ESC + "[0m" + HAND[9:] + " ; user" + BEL + KEY, [HAND]),
    ("D1c control: G2 key alone", "INFO user" + ESC + "[0m" + KEY, [HAND]),
    ("D1d control: handed-out secret alone, cut", "x " + HAND[:5] + "\x9b0m" + HAND[5:], [HAND]),
]
for lab, t, sec in ROWS:
    for path, f in (("tool", lambda: tools.prepare_output(t, {}, 4000, sec)), ("error", lambda: tools.error_reason(ValueError(t), sec))):
        try:
            o = f()
        except Exception as e:
            print(lab, "|", path, "| REFUSED", type(e).__name__); continue
        key = "LEAKED" if KEY[4:] in o else "MASKED"
        hand = "LEAKED" if any(p in o for p in (HAND, HAND[:9], HAND[9:], HAND[:5], HAND[5:])) else "MASKED"
        print(lab, "|", path, "| key", key, "| handed-out", hand)
