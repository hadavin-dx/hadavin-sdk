"""PR H errata rev 2: reproduce the design reviewer's inputs M1-M6, the _first_decoded point and the OSC/U+009C row.
Mode: main | proto | protofix (prototype + longest-first earlier-mask fix). Made-up data only, secrets built from parts.
Output shows verdict words and masked shapes only."""
import sys, re, random
sys.path.insert(0, "/home/user/build/prh-author/errata")
MODE = sys.argv[1]
from hadavin_sdk.guard import runmap
from hadavin_sdk import tools
from hadavin_sdk.approvals import channel
from hadavin_sdk.runtime import evidence
import importlib
R = importlib.import_module("hadavin_sdk.guard.redact")
if MODE != "main":
    import prh_proto as proto
    proto.install()
    if MODE == "protofix":
        import fix790; fix790.install()
    if MODE == "protofixes":
        import fixes; fixes.install()
ESC, BEL = "\x1b", "\x07"
KEY = "AKIA" + "IOSFODNN7EXAMPLE"
GEN = re.compile(r"<[A-Z][A-Z0-9]*_\d+>")
def v(out, secret_piece): return "LEAKED" if secret_piece in out else "MASKED"
def safe(f):
    try: return f()
    except Exception as e: return "RAISED " + type(e).__name__
print("MODE", MODE)
# M1: more than 256 distinct masked values plus one hidden item inside a word, and user+BEL+KEY
pad = " ".join(f"u{i}" + "@" + "example.com" for i in range(300))
for lab, t in (("M1a user+BEL+KEY + 300 addresses", pad + " user" + BEL + KEY),
               ("M1b user+BEL+KEY + 300 addresses + x ESC[0m y", pad + " x" + ESC + "[0my user" + BEL + KEY),
               ("M1c control: user+BEL+KEY alone", "user" + BEL + KEY)):
    for p, f in (("untrusted", lambda: runmap.redact_untrusted(t, {})), ("tool", lambda: tools.prepare_output(t, {}, 262144, []))):
        o = safe(f); print(lab, "|", p, ":", o if o.startswith("RAISED") else v(o, KEY[4:]))
# M2: an encoding token cut by a hidden item that decoding produces
for lab, t in (("M2a %4%1b[0m1KIA...", "id %4%1b[0m1KIA" + KEY[4:]),
               ("M2b %4\\x1b[0m1KIA...", "id %4\\x1b[0m1KIA" + KEY[4:]),
               ("M2c &#6&#27;[0m5;KIA...", "id &#6&#27;[0m5;KIA" + KEY[4:]),
               ("M2d control %41KIA...", "id %41KIA" + KEY[4:])):
    for p, f in (("untrusted", lambda: runmap.redact_untrusted(t, {})), ("tool", lambda: tools.prepare_output(t, {}, 262144, []))):
        o = safe(f); print(lab, "|", p, ":", o if o.startswith("RAISED") else v(o, KEY[4:]))
# M3: runs of two or more removed items between word characters
for lab, t in (("M3a user+BEL+BEL+KEY", "user" + BEL + BEL + KEY), ("M3b user+ESC[0m+ESC[1m+KEY", "user" + ESC + "[0m" + ESC + "[1m" + KEY),
               ("M3c user+BEL+ZWSP+BEL+KEY", "user" + BEL + "​" + BEL + KEY), ("M3d user+BEL+FF+KEY", "user" + BEL + "\x0c" + KEY)):
    for p, f in (("untrusted", lambda: runmap.redact_untrusted(t, {})), ("head", lambda: runmap.safe_head(t, 4000))):
        o = safe(f); print(lab, "|", p, ":", o if o.startswith("RAISED") else v(o, KEY[4:]))
if MODE != "main":
    for t in ("ab" + BEL + BEL + "cd", "ab" + ESC + "[0m" + ESC + "[1mcd", "ab" + BEL + "​" + BEL + "cd", "ab" + BEL + "-cd", "ab" + BEL + " cd", "ab" + "\x0c" + BEL + "cd"):
        print("M3 strip table", ascii(t), "-> joined", ascii(proto.strip(t)[0]), "spaced", ascii(proto.strip(t)[1]))
# M4: map clean-up drops an entry that protects a later text (search the run's own generator space)
def m4():
    if MODE == "main":
        print("M4 (main has no clean-up step; see proto modes)"); return
    rnd = random.Random(4)
    found = 0
    for k in range(3000):
        a = "".join(rnd.choice("qxzjkwvy") for _ in range(rnd.randint(6, 10)))
        b = "".join(rnd.choice("qxzjkwvy0123") for _ in range(rnd.randint(4, 8)))
        sep = rnd.choice(["%3B", "%2C", "&#59;", "\\x3b", "%20"])
        t = rnd.choice(["note password=", "note --passwd=", "x secret="]) + a + sep + b + rnd.choice([" end", " and %41KIA" + KEY[4:] + " end"])
        for prune in (True, False):
            proto.PRUNE = prune
            m = {}; safe(lambda: runmap.redact_untrusted(t, m))
            later = "the password " + a + " failed"
            o = safe(lambda: runmap.redact_untrusted(later, dict(m)))
            if prune: lp = v(o, a)
            else: lu = v(o, a)
        if lp != lu:
            found += 1
            if found <= 2: print("M4 case", ascii(t.replace(a, "[A]").replace(b, "[B]")), "| later text with pruned map:", lp, "| unpruned map:", lu)
    proto.PRUNE = True
    print("M4 count of inputs (of 3000) where the clean-up changes a later text's verdict:", found)
m4()
# M5: card forging a placeholder through a hidden item
for lab, t in (("M5a", "<" + ESC + "[0mIPV4_1> and 10.0.0.5"), ("M5b control plain", "<IPV4_1> and 10.0.0.5")):
    o = safe(lambda: channel.clean(t))
    print(lab, "card clean:", ascii(o.replace("10.0.0.5", "[IP]")), "| <IPV4_1> count", o.count("<IPV4_1>"))
# M6: grounding through canonical with U+FE0F / U+034F
for lab, val, txt in (("M6a id with U+FE0F", "pod-1️", "pod-1️ is running"), ("M6b evidence po+U+034F+d-1 grounds pod-1", "pod-1", "po͏d-1 is running"),
                      ("M6c id with ZWSP (Cf, unchanged)", "pod​-1", "pod-1 is running")):
    print(lab, "| canonical(value)==value:", runmap.canonical(val) == val, "| contains:", evidence.contains(txt, val))
# _first_decoded skip guard
for ch in ("\x07", ESC, "a", "%"):
    tools._first_decoded.cache_clear()
    d = tools._first_decoded(ch); print("_first_decoded", ascii(ch), "->", ascii(d), "| skip guard skips:", not (d in "&\\%"))
# OSC ended by U+009C (main's strip_ansi), and the gate
t = "a " + ESC + "]0;title\x9c" + "visible after" + "\nline two"
print("OSC+U+009C strip_ansi:", ascii(R.strip_ansi(t)))
