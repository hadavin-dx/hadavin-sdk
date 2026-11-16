"""EVIDENCE RUNNER probe H1-H3 (lead addition). Own script, made-up values built from parts."""
import sys
from hadavin_sdk import tools
from hadavin_sdk.guard import runmap

ESC, BEL = "\x1b", "\x07"
KEY = "AKIA" + "IOSFODNN7EXAMPLE"
HAND = "Qx7mLp" + "-9vRtzKw2"
IP = "10.20.30.44"
TR = tools.TRUNCATED

def fresh_map():
    m = {}
    runmap.redact_text("seen ip " + IP, m)  # the map already holds the IP
    return m

ROWS = {
 "H1a plain + ESC-prefixed copy": ("x " + HAND + " y " + ESC + HAND, {"HAND": HAND, "HAND[1:]": HAND[1:], "HAND[9:]": HAND[9:]}),
 "H1b plain + copy cut by ESC(B ESC[m": ("x " + HAND + " y " + HAND[:9] + ESC + "(B" + ESC + "[m" + HAND[9:], {"HAND": HAND, "HAND[9:]": HAND[9:], "HAND[:9]": HAND[:9]}),
 "H2 ends ESC+HAND[:11]+TRUNCATED": ("log " + ESC + HAND[:11] + TR, {"HAND[:11]": HAND[:11], "HAND[1:11]": HAND[1:11], "HAND": HAND}),
 "H3 key cut by ESC+letter, user BEL IP (map holds IP)": ("id " + KEY[:4] + ESC + "A" + KEY[4:] + " user" + BEL + IP, {"user+IP glued": "user" + IP, "KEY": KEY, "KEY[4:]": KEY[4:], "IP": IP}),
 "H3b same, no ESC-letter (control)": ("user" + BEL + IP, {"user+IP glued": "user" + IP, "IP": IP}),
}
def run(name, call, pieces):
    try:
        out = call()
    except Exception as e:
        return "R(" + type(e).__name__ + ")"
    got = ",".join(f"{n}={'yes' if p in out else 'no'}" for n, p in pieces.items())
    return "any=" + ("yes" if any(p in out for p in pieces.values()) else "no") + " {" + got + "}" + " out=" + repr(out)[:70]
print("python", sys.version.split()[0], "tree", tools.__file__)
for n, (t, pieces) in ROWS.items():
    handed = [HAND]
    res = [
     "untrusted: " + run(n, lambda: runmap.redact_untrusted(t, fresh_map()), pieces),
     "tool: " + run(n, lambda: tools.prepare_output(t, fresh_map(), 4000, handed), pieces),
     "error: " + run(n, lambda: tools.error_reason(ValueError(t), handed), pieces),
     "head: " + run(n, lambda: runmap.safe_head(t, 4000, fresh_map()), pieces),
    ]
    print(n, "||", " | ".join(res))
    print("   (no handed-out list on untrusted/head paths; error path has no map)")
