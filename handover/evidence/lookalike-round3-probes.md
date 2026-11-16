# Look-alike round 3 probes (resolve of draft 3; throwaway scripts; made-up values built from parts)

Run 2026-11-05 UTC by the round-3 resolve agent with `python3 -I <script> <snapshot src>` against the PR #50 snapshot `748849c` (`src/hadavin_sdk/guard/`), Python 3.13.18. No repository test suite was run. probe2.py is a PROTOTYPE of two proposed changes (a case-insensitive sweep; the check with the decoded form undo(out)); it uses the snapshot `fold` (casefold, whitespace removed) as a stand-in for P1b `scan_keyset`, which does not exist yet: its results say the idea works on these inputs, not that P2d-2 code works.

## probe.py
```python
"""Look-alike round 3 probes. Made-up values only, built from parts. Run: python3 -I probe.py <snapshot src>."""
import importlib
import json
import sys
import urllib.parse

sys.path.insert(0, sys.argv[1])
R = importlib.import_module("hadavin_sdk.guard.redact")
runmap = importlib.import_module("hadavin_sdk.guard.runmap")

print("python", sys.version.split()[0])
print("SECRET_KINDS", sorted(R.SECRET_KINDS))

# made-up NAME value, handed in a map
name = "Anna" + " " + "Schmidt-Kowalski"
ph = "<NAME_1>"

def show(label, text, mapping):
    m = dict(mapping)
    try:
        out = runmap.redact_text(text, m)
    except Exception as e:  # noqa
        out = "RAISED " + type(e).__name__
    print(f"[{label}] redact_text -> {out!r}")
    try:
        b = R.redact(text, mapping=dict(mapping)).text
    except Exception as e:  # noqa
        b = "RAISED " + type(e).__name__
    print(f"[{label}] bare redact  -> {b!r}")

print("\n== P1: case-only copies of a stored NAME (ADV-LK3-2) ==")
show("plain", "Dear team, " + name + " signed.", {ph: name})
show("upper", "Dear team, " + name.upper() + " signed.", {ph: name})
show("lower", "Dear team, " + name.lower() + " signed.", {ph: name})

print("\n== P2: planted password word, later other case (ADV-LK3-4) ==")
word = "produc" + "tion"
show("planted+Title", "password=" + word + "\nthe " + word.title() + " cluster is up", {})

print("\n== P3: bare path, percent-encoded copy with Cyrillic spelling (ADV-LK3-1) ==")
v = "ab" + "cz" + "9q" + "rt" + "x7" + "mz" + "k"  # 13 chars, made up
sph = "<SECRET_1>"
cyr = v.replace("a", "а").replace("c", "с")
pct = "".join("%%%02X" % b for b in cyr.encode("utf-8"))
show("pct-cyr", "token " + pct + " end", {sph: v})
print("undo(pct) == cyr:", runmap.undo(pct) == cyr)
js = "".join("\\u%04x" % ord(c) for c in cyr)
show("json-u-cyr", "token " + js + " end", {sph: v})
print("undo(json) == cyr:", runmap.undo(js) == cyr)

print("\n== P4: redact_many split across items (ADV-LK3-5) ==")
outs, m = R.redact_many([ "head " + v[:6], v[6:] + " tail"], {sph: v})
print("redact_many ->", outs)

print("\n== P5: _clean and a lone surrogate (ADV-LK3-9) ==")
s = v[:5] + "\ud800" + v[5:]
print("_clean ->", repr(runmap._clean(s)))
alt = s.encode("utf-8", "surrogatepass").decode("utf-8", "replace")
print("surrogatepass+replace ->", repr(alt))

print("\n== P6: lower() length alignment (case-insensitive sweep, no position map) ==")
for t in ["ANNA SCHMIDT-KOWALSKI", "İSTANBUL", "STRASSE vs Straße", "Σς"]:
    print(repr(t), "len", len(t), "lower len", len(t.lower()), repr(t.lower()))

def low1(s):
    lo = s.lower()
    if len(lo) == len(s):
        return lo
    return "".join(c if len(c.lower()) != 1 else c.lower() for c in s)

t = "x İ ANNA SCHMIDT-KOWALSKI y"
lo = low1(t)
i = lo.find(name.lower())
print("aligned:", len(lo) == len(t), "found at", i, "slice", repr(t[i:i + len(name)]))

print("\n== P7: redact_value run twice on benign multi-leaf JSON (ADV-LK3-7, idempotence) ==")
benign = {
    "to": "ops" + "@" + "example.com",
    "host": "10.0.0." + "7",
    "note": "Dear " + name + ", see ticket INV-2026-0042",
    "rows": [{"user": "u" + "1", "ip": "192.0.2." + "4"}, "card ref 1234 5678 9012", "plain words here"],
    "url": "https://example.com/a%20b?x=1&y=2",
}
m1 = runmap.RunMap()
o1 = runmap.redact_value(benign, m1)
n1 = len(m1)
o2 = runmap.redact_value(o1, m1)
print("map after pass 1:", n1, "after pass 2 over pass-1 output:", len(m1))
print("identical output:", o1 == o2)
print("pass1:", json.dumps(o1))
if o1 != o2:
    print("pass2:", json.dumps(o2))

print("\n== P8: 12-digit stored id inside a zero-padded 16-digit number (ADV-LK3-11) ==")
acct = "4021" + "7788" + "1350"
show("padded", "ref 0000" + acct + " ok", {"<ACCOUNTID_1>": acct})
```
## probe.py raw output
```
python 3.13.18
SECRET_KINDS ['APIKEY', 'AZURESAS', 'BASIC', 'BEARER', 'CREDITCARD', 'GCPTOKEN', 'HIGHENTROPY', 'IBAN', 'JWT', 'PRIVKEY', 'SECRET', 'URLCRED', 'WEBHOOK']

== P1: case-only copies of a stored NAME (ADV-LK3-2) ==
[plain] redact_text -> 'Dear team, <NAME_1> signed.'
[plain] bare redact  -> 'Dear team, <NAME_1> signed.'
[upper] redact_text -> 'Dear team, ANNA SCHMIDT-KOWALSKI signed.'
[upper] bare redact  -> 'Dear team, ANNA SCHMIDT-KOWALSKI signed.'
[lower] redact_text -> 'Dear team, anna schmidt-kowalski signed.'
[lower] bare redact  -> 'Dear team, anna schmidt-kowalski signed.'

== P2: planted password word, later other case (ADV-LK3-4) ==
[planted+Title] redact_text -> 'password=<SECRET_1>\nthe Production cluster is up'
[planted+Title] bare redact  -> 'password=<SECRET_1>\nthe Production cluster is up'

== P3: bare path, percent-encoded copy with Cyrillic spelling (ADV-LK3-1) ==
[pct-cyr] redact_text -> 'token %D0%B0%62%D1%81%7A%39%71%72%74%78%37%6D%7A%6B end'
[pct-cyr] bare redact  -> 'token %D0%B0%62%D1%81%7A%39%71%72%74%78%37%6D%7A%6B end'
undo(pct) == cyr: True
[json-u-cyr] redact_text -> 'token \\u0430\\u0062\\u0441\\u007a\\u0039\\u0071\\u0072\\u0074\\u0078\\u0037\\u006d\\u007a\\u006b end'
[json-u-cyr] bare redact  -> 'token \\u0430\\u0062\\u0441\\u007a\\u0039\\u0071\\u0072\\u0074\\u0078\\u0037\\u006d\\u007a\\u006b end'
undo(json) == cyr: True

== P4: redact_many split across items (ADV-LK3-5) ==
redact_many -> ['head abcz9q', 'rtx7mzk tail']

== P5: _clean and a lone surrogate (ADV-LK3-9) ==
_clean -> 'abcz9?qrtx7mzk'
surrogatepass+replace -> 'abcz9���qrtx7mzk'

== P6: lower() length alignment (case-insensitive sweep, no position map) ==
'ANNA SCHMIDT-KOWALSKI' len 21 lower len 21 'anna schmidt-kowalski'
'İSTANBUL' len 8 lower len 9 'i̇stanbul'
'STRASSE vs Straße' len 17 lower len 17 'strasse vs straße'
'Σς' len 2 lower len 2 'σς'
aligned: True found at 4 slice 'ANNA SCHMIDT-KOWALSKI'

== P7: redact_value run twice on benign multi-leaf JSON (ADV-LK3-7, idempotence) ==
map after pass 1: 5 after pass 2 over pass-1 output: 5
identical output: True
pass1: {"to": "<EMAIL_1>", "host": "<IPV4_1>", "note": "Dear <NAME_1>-Kowalski, see ticket INV-2026-0042", "rows": [{"user": "u1", "ip": "<IPV4_2>"}, "card ref <PHONE_1>", "plain words here"], "url": "https://example.com/a%20b?x=1&y=2"}

== P8: 12-digit stored id inside a zero-padded 16-digit number (ADV-LK3-11) ==
[padded] redact_text -> 'ref <PHONE_1> ok'
[padded] bare redact  -> 'ref <PHONE_1> ok'
```
## probe2.py
```python
"""Prototype probes (throwaway; NOT the P2d-2 code). Made-up values. Run: python3 -I probe2.py <snapshot src>.
(a) a length-preserving case-insensitive literal sweep of KNOWN originals (no position map: index i of the lowered
segment is index i of the segment); (b) the check on the bare path with the decoded form undo(out), using the
snapshot fold (casefold, whitespace removed) as a stand-in for P1b scan_keyset, which does not exist yet."""
import importlib
import sys

sys.path.insert(0, sys.argv[1])
R = importlib.import_module("hadavin_sdk.guard.redact")
runmap = importlib.import_module("hadavin_sdk.guard.runmap")
tn = importlib.import_module("hadavin_sdk.guard.textnorm")


def low1(s):
    lo = s.lower()
    if len(lo) == len(s):
        return lo
    return "".join(c.lower() if len(c.lower()) == 1 else c for c in s)


def sweep_ci(text, mapping):
    """Every copy (secret kinds) / every standalone copy (other kinds) of each known original, any simple case."""
    items = sorted(mapping.items(), key=lambda kv: -len(kv[1]))
    parts = R._PLACEHOLDER.split(text)
    for i in range(0, len(parts), 2):
        seg = parts[i]
        for ph, orig in items:
            rule = R._sweep(ph, orig)
            if rule is None:
                continue
            lo, key = low1(seg), low1(orig)
            assert len(lo) == len(seg)
            out, j = [], 0
            while True:
                k = lo.find(key, j)
                if k < 0:
                    break
                if rule is not R._EVERY_COPY:
                    before, after = seg[k - 1 : k], seg[k + len(orig) : k + len(orig) + 1]
                    if before in R._ALNUM or after in R._ALNUM:
                        out.append(seg[j : k + 1])
                        j = k + 1
                        continue
                out += [seg[j:k], ph]
                j = k + len(orig)
            out.append(seg[j:])
            seg = "".join(out)
        parts[i] = seg
    return "".join(parts)


name = "Anna" + " " + "Schmidt-Kowalski"
word = "produc" + "tion"
cases = [
    ("NAME upper", "Dear team, " + name.upper() + " signed.", {"<NAME_1>": name}),
    ("NAME lower", "cc: " + name.lower(), {"<NAME_1>": name}),
    ("NAME glued (not standalone)", "x" + name.upper(), {"<NAME_1>": name}),
    ("SECRET Title after plant", "password=<SECRET_1>\nthe " + word.title() + " cluster", {"<SECRET_1>": word}),
    ("dotted capital I before copy", "İ " + name.upper() + " end", {"<NAME_1>": name}),
    ("two values differ only in case", "see " + "ACME-" + "NORTH" + " now", {"<TENANT_1>": "Acme-" + "North", "<TENANT_2>": "acme-" + "north"}),
    ("sharp s upper (length changes)", "STRASSE " + "12", {"<ADDRESS_1>": "Straße 12"}),
]
print("== (a) case-insensitive sweep prototype ==")
for label, text, m in cases:
    print(f"[{label}] {text!r} -> {sweep_ci(text, m)!r}")


def key(s):
    return "".join(tn.fold(s, casefold=True).split())


def check(out, mapping, minimum=8):
    t = out
    for ph in mapping:
        t = t.replace(ph, " ")
    texts = {t, runmap.undo(t)}
    for ph, orig in mapping.items():
        k = key(orig)
        if len(k) >= minimum and any(k in key(x) for x in texts):
            return "REFUSE (" + ph + ")"
    return "pass"


print("\n== (b) bare path: check on out and undo(out) (snapshot fold stand-in) ==")
v = "ab" + "cz" + "9q" + "rt" + "x7" + "mz" + "k"
cyr = v.replace("a", "а").replace("c", "с")
pct = "".join("%%%02X" % b for b in cyr.encode("utf-8"))
js = "".join("\\u%04x" % ord(c) for c in cyr)
m = {"<SECRET_1>": v}
for label, text in [("pct cyr", "token " + pct), ("json cyr", "token " + js), ("plain pct", "token " + "".join("%%%02X" % b for b in v.encode())), ("benign", "token none here")]:
    out = R.redact(text, mapping=dict(m)).text
    print(f"[{label}] out={out!r} raw-only={check(out, m) if False else ''} check={check(out, m)}")
    t = out.replace("<SECRET_1>", " ")
    print(f"    raw key hit: {key(v) in key(t)}; decoded key hit: {key(v) in key(runmap.undo(t))}")

print("\n== (c) redact_many split across items: per item vs joined ==")
outs, mm = R.redact_many(["head " + v[:6], v[6:] + " tail"], dict(m))
print("per item:", [check(o, mm) for o in outs], "joined:", check(" ".join(outs), mm))
```
## probe2.py raw output
```
== (a) case-insensitive sweep prototype ==
[NAME upper] 'Dear team, ANNA SCHMIDT-KOWALSKI signed.' -> 'Dear team, <NAME_1> signed.'
[NAME lower] 'cc: anna schmidt-kowalski' -> 'cc: <NAME_1>'
[NAME glued (not standalone)] 'xANNA SCHMIDT-KOWALSKI' -> 'xANNA SCHMIDT-KOWALSKI'
[SECRET Title after plant] 'password=<SECRET_1>\nthe Production cluster' -> 'password=<SECRET_1>\nthe <SECRET_1> cluster'
[dotted capital I before copy] 'İ ANNA SCHMIDT-KOWALSKI end' -> 'İ <NAME_1> end'
[two values differ only in case] 'see ACME-NORTH now' -> 'see <TENANT_1> now'
[sharp s upper (length changes)] 'STRASSE 12' -> 'STRASSE 12'

== (b) bare path: check on out and undo(out) (snapshot fold stand-in) ==
[pct cyr] out='token %D0%B0%62%D1%81%7A%39%71%72%74%78%37%6D%7A%6B' raw-only= check=REFUSE (<SECRET_1>)
    raw key hit: False; decoded key hit: True
[json cyr] out='token \\u0430\\u0062\\u0441\\u007a\\u0039\\u0071\\u0072\\u0074\\u0078\\u0037\\u006d\\u007a\\u006b' raw-only= check=REFUSE (<SECRET_1>)
    raw key hit: False; decoded key hit: True
[plain pct] out='token %61%62%63%7A%39%71%72%74%78%37%6D%7A%6B' raw-only= check=REFUSE (<SECRET_1>)
    raw key hit: False; decoded key hit: True
[benign] out='token none here' raw-only= check=pass
    raw key hit: False; decoded key hit: False

== (c) redact_many split across items: per item vs joined ==
per item: ['pass', 'pass'] joined: REFUSE (<SECRET_1>)
```
