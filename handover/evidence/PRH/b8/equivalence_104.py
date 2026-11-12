"""PR H batch 8, mutant 104 (`ignoring` in runmap.redact_text returns its argument): is it equivalent?
Run with the tree to compare as argv[1] (a `src` folder); prints a digest of the outputs of `runmap.redact_untrusted` and
`tools.prepare_output` over 6000 seeded texts (a key cut by 1 to 3 cuts drawn from escape, ignorable and string-opener items).
Equal digests on the unmutated and the mutated tree = no text tells them apart."""
import hashlib, random, sys
sys.path.insert(0, sys.argv[1])
from hadavin_sdk import tools
from hadavin_sdk.guard import runmap
E = "\x1b"
KEY = "AKIA" + "IOSFODNN7EXAMPLE"
CUTS = [E + "[0m", E + "(B", E + "M", E, "​", "‍", "️", "͏", "⁠", "﻿", "\x08", "\x9b0m", E + "]0;t\x07"]
r = random.Random(104)
h = hashlib.sha256(); n = 0
for _ in range(6000):
    pos = sorted(r.sample(range(1, len(KEY)), r.randint(1, 3)))
    out, last = "", 0
    for p in pos:
        out += KEY[last:p] + r.choice(CUTS); last = p
    t = "x " + out + KEY[last:] + " y"
    try: a = str(runmap.redact_untrusted(t, {})[0])
    except Exception as e: a = type(e).__name__
    b = tools.prepare_output(t, {}, 4000, [])
    h.update((a + "\0" + b + "\0").encode()); n += 1
    if "--list" in sys.argv: print(ascii(t), "=>", ascii(a), "|", ascii(b))
print(n, h.hexdigest()[:16])
