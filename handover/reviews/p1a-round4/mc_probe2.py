import sys, unicodedata
sys.path.insert(0, r"C:\Users\rakes\Downloads\Hadavin\_local\scratch\wt\pr63\src")
from hadavin_sdk.guard import textnorm as t
for ch in ("\u093e", "\u093f", "\u0903", "\u02b0", "\u00a8", "\u0300", "\u200b"):
    s = "pass" + ch + "word"
    print("U+%04X" % ord(ch), unicodedata.category(ch), "fold_views", ascii(sorted(t.fold_views(s))), "squeeze_views", ascii(sorted(t.squeeze_views(s))))
print("control plain", ascii(sorted(t.fold_views("password"))), ascii(sorted(t.squeeze_views("password"))))
print([n for n in dir(t) if not n.startswith("_")][:40])
