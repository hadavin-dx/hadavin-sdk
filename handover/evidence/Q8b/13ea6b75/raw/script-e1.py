# E1: address or host directly followed by a credential key, several separators; walk path, card path, Slack block, redactor direct
import sys; from lib import *
print("## import", path_src())
SEC = "<made-up-value>"
lefts = ["bob.smith@example.com", "db01.corp.internal", "10.20.30.40", "https://example.com/x", "bob@example.com.", "a@b.io", "[bob.smith@example.com]", "bob.smith@example[.]com"]
seps = {"glued": "", "zwsp U+200B": "​", "zwj U+200D": "‍", "bom U+FEFF": "﻿", "word-joiner U+2060": "⁠", "soft-hyphen": "­", "space": " ", "newline": "\n", "comma": ",", "semicolon": ";"}
keys = ["password=", "token=", "secret=", "api_key=", "password: ", "Authorization: Bearer ", "passwd=", "client_secret="]
tot = {"walk": 0, "card": 0, "slack": 0, "n": 0}
rows = []
for l in lefts:
    for sn, s in seps.items():
        for k in keys:
            text = f"{l}{s}{k}{SEC}"
            n = {}
            n["walk"] = walk({"message": text})
            n["card"] = clean(text)
            n["slack"] = slack(text)
            tot["n"] += 1
            bad = [p for p, o in n.items() if readable(SEC, o)]
            for p in bad: tot[p] += 1
            if bad: rows.append((l, sn, k, bad, {p: n[p] for p in bad}))
print("cases", tot["n"], "readable walk/card/slack:", tot["walk"], tot["card"], tot["slack"])
for r in rows[:40]: print("READABLE", r[0], "|", r[1], "|", r[2], "|", r[3], "|", js(r[4])[:200])
if len(rows) > 40: print("... more readable rows:", len(rows) - 40)
# the 4 named cases
for sn in ["glued", "zwsp U+200B"]:
    for k in ["password=", "token="]:
        t = f"bob.smith@example.com{seps[sn]}{k}{SEC}"
        print("NAMED", sn, k, "walk=", js(walk({"message": t})), "card=", repr(clean(t)))
