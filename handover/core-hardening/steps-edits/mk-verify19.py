# builds verify19.py from verify18.py: re-anchors the old checks to the round 19 text (anchored patches, each asserted once) and swaps the round 18 section and plants for the round 19 ones
s = open('verify18.py', encoding='utf-8').read().replace('scratch18', 'scratch19')
def R(a, b, n=1):
    global s
    c = s.count(a)
    assert c == n, (c, n, a[:90])
    s = s.replace(a, b)
_KS = ("The key is revoked by 18:19 UTC = 23:49 IST; the last 10 minutes (18:19 UTC = 23:49 IST to 18:29 UTC = 23:59 IST) are for card steps 2 and 3; "
       "if the key is still live at 18:19 UTC = 23:49 IST it comes first.")
# ND: 17 items (new item 17)
R("if nums != list(range(1, 17)): F('ND numbers')", "if nums != list(range(1, 18)): F('ND numbers')")
R("if 'items 1 to 16' not in ndsec: F('ND header count')", "if 'items 1 to 17' not in ndsec: F('ND header count')")
R("if any(x < 1 or x > 16 for x in nn): F('ND number out of range')", "if any(x < 1 or x > 17 for x in nn): F('ND number out of range')")
R("if not re.search(r'(?m)^15\\. \\*\\*When the owner writes `no more takes`', ndsec): F('r12 ND15 missing')", "if not re.search(r'(?m)^15\\. \\*\\*When the owner types `yes, no more takes`', ndsec): F('r12 ND15 missing')")
R("neg('r12nd15', '15. **When the owner writes `no more takes`', '15. **Something else', 'r12 ND15 missing')", "neg('r12nd15', '15. **When the owner types `yes, no more takes`', '15. **Something else', 'r12 ND15 missing')")
# four alarms, alarm 3 renamed
R("if 'Set three alarms' not in t12n or 'not a control' not in t12n: F('r14 E-12 alarms')", "if 'Set four alarms' not in t12n or 'not a control' not in t12n: F('r14 E-12 alarms')")
R("neg('r15short', 'In short: set three alarms', 'Set three alarms', 'r15 E-48 intro lacks')", "neg('r15short', 'In short: set four alarms', 'Set four alarms', 'r15 E-48 intro lacks')")
R("neg('r16code', 'In short: set three alarms', 'In short (E-12): set three alarms', 'r16 internal code in owner text')", "neg('r16code', 'In short: set four alarms', 'In short (E-12): set four alarms', 'r16 internal code in owner text')")
R("if '10 minutes left' not in _m.group(1): F('r16 alarm 3 has the wrong name in %s: %r' % (_rid, _m.group(1)))", "if 'last chance' not in _m.group(1) or '10 minutes' in _m.group(1): F('r16 alarm 3 has the wrong name in %s: %r' % (_rid, _m.group(1)))\n    for _m in re.finditer(r'[Aa]larm 4[^`\\n]*?named `([^`]+)`', _b):\n        if 'still not revoked' not in _m.group(1): F('r19 alarm 4 has the wrong name in %s: %r' % (_rid, _m.group(1)))")
R("'named `10 minutes left: revoke the secret key for the model now`')", "'named `last chance: revoke the secret key for the model now`', 'Alarm 4: Tue 24 Nov 2026 06:00 UTC = 11:30 IST')")
# route prices: both are in D.1 and E-57; no tilt
R("need17('F-2 route B price in ' + _lab, _tx, 'up to five days', 'Route A is the safer one')", "need17('F-2 route B price in ' + _lab, _tx, 'up to five days', 'In route A the live key exists for hours, in route B for up to five days')\nneed17('r19 route A price in D.1', ks('D'), 'Route A: after your confirmation the clean-up removes the take\\'s set-up', 'a new secret key for the model and a new yes: step 20')")
R("neg('r17routeb', 'Route A is the safer one for keeping secrets safe;', 'Route B is fine;', 'r17 F-2 route B price')", "neg('r17routeb', 'In route A the live key exists for hours, in route B for up to five days. Write', 'Route B is fine. Write', 'r17 F-2 route B price')")
# F-8 D.5: the one sentence
R("need17('F-8 D.5', ks('D'), 'Between 18:19 UTC = 23:49 IST and 18:29 UTC = 23:59 IST there are only 10 minutes', 'then card step 2 (the app passwords and the HubSpot apps', 'only then card step 3 (the shred of the key copies')",
  "need17('F-8 D.5', ks('D'), " + repr(_KS) + ")")
# pins
R("('m34 word list', 'B', '| `key gone, no more decisions` | the key is gone AND there are no more takes AND the cut is final'),", "('m34 word list', 'B', '| `key gone, no more decisions` | THREE events at once, on purpose: the key is gone AND there are no more takes AND the cut is final'),")
R("('m37 window end', 'A', 'The spending window ends 10 minutes later, at 18:29 UTC = 23:59 IST'),", "('m37 window end', 'A', 'The spending window ends at 18:29 UTC = 23:59 IST; that is when the model stage must stop spending.'),")
R("('B04 ten minutes', 'APPX', 'the 10 minutes between go first to the key (card step 1)'),", "('B04 ten minutes', 'APPX', " + repr(_KS) + "),")
R("'m37 window end': ('The spending window ends 10 minutes later, at 18:29 UTC = 23:59 IST', 'The spending window ends 10 minutes later, at 18:19 UTC = 23:49 IST'),", "'m37 window end': ('The spending window ends at 18:29 UTC = 23:59 IST; that is when', 'The spending window ends at 18:19 UTC = 23:49 IST; that is when'),")
R("'B04 ten minutes': ('the 10 minutes between go first to the key (card step 1)', 'the 20 minutes between go first to the key (card step 1)'),", "'B04 ten minutes': ('the last 10 minutes (18:19 UTC = 23:49 IST to', 'the last 20 minutes (18:19 UTC = 23:49 IST to'),")
R("'m34 word list': ('the key is gone AND there are no more takes AND the cut is final', 'the key is gone AND there are no more takes'),", "'m34 word list': ('THREE events at once, on purpose: the key is gone AND there are no more takes AND the cut is final', 'THREE events at once, on purpose: the key is gone AND there are no more takes'),")
R("neg('r14rec2', 'Route B: you have not written', 'Route B (the one the assistant recommends): you have not written', 'r14 second recommendation spot')", "neg('r14rec2', 'Route B: you have not yet typed', 'Route B (the one the assistant recommends): you have not yet typed', 'r14 second recommendation spot')")
# the negative controls may run in anchor-only mode (cheap check that every planted string still exists)
R("    src = open(E, encoding='utf-8').read()\n    if src.count(old) < 1:\n        F('negative control anchor missing: ' + name); return\n", "    src = open(E, encoding='utf-8').read()\n    if src.count(old) < 1:\n        F('negative control anchor missing: ' + name); return\n    if os.environ.get('NEG_ANCHOR_ONLY'): return\n")
# resume mode for a negative-control run that a time limit cut off: skip every control up to and including the one named in NEG_AFTER
R("def neg(name, old, new, expect, count=1):\n    src = open(E, encoding='utf-8').read()\n", "_negskip = [bool(os.environ.get('NEG_AFTER'))]\ndef neg(name, old, new, expect, count=1):\n    if _negskip[0]:\n        if name == os.environ.get('NEG_AFTER'): _negskip[0] = False\n        return\n    src = open(E, encoding='utf-8').read()\n")
# round 19 changed the E-58 text: the old label 'E-58 times' is superseded; the mutation is still caught, by the round 19 count of 18:29 UTC = 23:59 IST
R("neg('r11e58', 'Mon 23 Nov 2026, by 18:29 UTC = 23:59 IST', 'Mon 23', 'E-58 times')", "neg('r11e58', 'Mon 23 Nov 2026, by 18:29 UTC = 23:59 IST', 'Mon 23', 'r19 count applied')")
# swap the round 18 section and plants
sec = open('r19-section.py', encoding='utf-8').read() + '\n' + open('r19-golden.py', encoding='utf-8').read(); pl = open('r19-plants.py', encoding='utf-8').read()
a = s.index('# ================= round 18 checks'); b = s.index("print('round 18 checks done')") + len("print('round 18 checks done')")
s = s[:a] + sec.strip('\n') + s[b:]
a = s.index('# ---- round 18 plants'); b = s.index("print('r18 plants (planted, caught):'"); b = s.index('\n', b)
s = s[:a] + pl.strip('\n') + s[b:]
open('verify19.py', 'w', encoding='utf-8').write(s)
print('verify19.py written', len(s.split('\n')), 'lines')
