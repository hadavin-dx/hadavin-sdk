# Look-alike round 2 resolve: probes on the PR #50 snapshot 748849c

Run 2026-11-05 by the look-alike round-2 resolve (Opus). `python3 -I <script> <snapshot>/src`; no repository suite, no network. All values are made up (a made-up person name, digit runs built from a formula or the digits of pi, a value built from parts). Raw output below the scripts. What these probes do NOT show: anything about P1a/P1b code (not written), timings, the repository test suite after the proposed PHONE change.

## probe.py
```python
import sys
sys.path.insert(0, sys.argv[1])
from hadavin_sdk.guard import textnorm as t
import importlib; r = importlib.import_module("hadavin_sdk.guard.redact")
def ws(s): return "".join(s.split())
name = "Marta Kowalczyk"   # made-up
cyr = name.replace("a", "а").replace("o", "о")
cm = name[:3] + "́" + name[3:]
cap = name.upper()
acc = "Martá Kowalczyk"
print("A fold casefold=False keys equal:")
for lab, s in [("cyr",cyr),("comb",cm),("caps",cap),("accent",acc),("split","Marta\nKowalczyk"),("fw","".join(chr(ord(c)+0xFEE0) if c!=' ' else c for c in name))]:
    print(" ", lab, ws(t.fold(s)) == ws(t.fold(name)), repr(ws(t.fold(s))))
print("B Ze/z case-preserving:", repr(t.fold("з")), repr(t.fold("З")), "Eta:", repr(t.fold("Η")), repr(t.fold("η")))
print("C U+FFFD kept by snapshot fold:", "�" in t.fold("a�b"))
# PHONE / ACCOUNTID by digit length, contexts
def red(s): return r.redact(s).text
for n in (8,9,10,11,12,13,16,17,18):
    d = "".join(str((i*7+3)%10) for i in range(n))
    print("D", n, "plain:", red("ref "+d+" ok")!=("ref "+d+" ok"), "period-after:", red("ref "+d+".")!=("ref "+d+"."), "glued-letter:", red("ref X"+d+" ok")!=("ref X"+d+" ok"), "after-dash:", red("acct-"+d+" ok")!=("acct-"+d+" ok"))
# EMAIL case variant
e = "marta.k" + "@" + "example.com"
print("E email upper masked:", red("to "+e.upper()) != "to "+e.upper(), red("to "+e.upper()))
# NAME patterns case
print("F Dear caps:", red("DEAR MARTA KOWALCZYK"), "|", red("Dear Marta"), "|", red("full_name: MARTA KOWALCZYK"))
print("G ADDRESS caps:", red("12 HIGH STREET"), "|", red("12 High Street"))
print("H TENANT:", red("TENANT_ID=ACME_42"))
```

## phone.py
```python
import re
old = re.compile(r"(?<![\w.\-])(?!\d{4}-\d\d-\d\d)(?!(?:19|20)\d\d(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])(?:[01]\d|2[0-3])[0-5]\d[0-5]\d(?!\d))\+?\d(?:(?!\d{4}-\d\d-\d\d)[\d \-]){8,14}\d(?![\w.])")
new = re.compile(old.pattern.replace(r"\d(?![\w.])", r"\d(?!\w|\.\w)"))
d10 = "3141592653"  # made-up 10 digits (digits of pi)
cases = ["ref %s." % d10, "ref %s.5" % d10, "v %s.txt" % d10, "ref %s, ok" % d10, "%s.%s" % (d10, d10), "sha %sabc" % d10, "ref %s.\n" % d10, "1.%s" % d10]
for c in cases:
    print(repr(c), "old:", bool(old.search(c)), "new:", bool(new.search(c)))
```

## squeeze.py
```python
import sys
sys.path.insert(0, sys.argv[1])
from hadavin_sdk.guard import textnorm as t
v = "Qx7" + "Lm2" + "Rt9" + "Vb4" + "Kp"   # made-up, built from parts
k = t.squeeze(v)
for lab, s in [("dots", ".".join(v)), ("hyphens", "-".join(v)), ("underscores", "_".join(v)),
               ("fffd", "�".join(v)), ("cyrillic+dots", ".".join(v.replace("x", "х").replace("p", "р"))),
               ("markup", "<b>".join(v)), ("caps+spaces", " ".join(v.upper()))]:
    print(lab, k in t.squeeze("note: " + s + " end"))
print("key", len(k))
```

## Output
```
### probe.py
A fold casefold=False keys equal:
  cyr True 'MartaKowalczyk'
  comb True 'MartaKowalczyk'
  caps False 'MARTAKOWALCZYK'
  accent True 'MartaKowalczyk'
  split True 'MartaKowalczyk'
  fw True 'MartaKowalczyk'
B Ze/z case-preserving: '3' '3' Eta: 'H' 'n'
C U+FFFD kept by snapshot fold: True
D 8 plain: False period-after: False glued-letter: False after-dash: False
D 9 plain: False period-after: False glued-letter: False after-dash: False
D 10 plain: True period-after: False glued-letter: False after-dash: False
D 11 plain: True period-after: False glued-letter: False after-dash: False
D 12 plain: True period-after: True glued-letter: False after-dash: True
D 13 plain: True period-after: False glued-letter: False after-dash: False
D 16 plain: True period-after: False glued-letter: False after-dash: False
D 17 plain: False period-after: False glued-letter: False after-dash: False
D 18 plain: False period-after: False glued-letter: False after-dash: False
E email upper masked: True to <EMAIL_1>
F Dear caps: DEAR MARTA KOWALCZYK | Dear <NAME_1> | full_name: <NAME_1>
G ADDRESS caps: 12 HIGH STREET | <ADDRESS_1>
H TENANT: TENANT_ID=<TENANT_1>
### phone.py
'ref 3141592653.' old: False new: True
'ref 3141592653.5' old: False new: False
'v 3141592653.txt' old: False new: False
'ref 3141592653, ok' old: True new: True
'3141592653.3141592653' old: False new: False
'sha 3141592653abc' old: False new: False
'ref 3141592653.\n' old: False new: True
'1.3141592653' old: False new: False
dots True
hyphens True
underscores True
fffd True
cyrillic+dots True
markup False
caps+spaces True
key 14
```
