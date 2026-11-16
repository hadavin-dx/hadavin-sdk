# ================= round 17 checks (security N1, minors; stranger F-1 to F-15; runner: 6 fresh + 15 missed mutations) =================
_r17n = 0
def need17(label, text, *needles):
    global _r17n
    for nd_ in needles:
        _r17n += 1
        if nd_ not in text: F('r17 %s lacks %r' % (label, nd_[:80]))
def absent17(label, text, *bad):
    global _r17n
    for b_ in bad:
        _r17n += 1
        if b_ in text: F('r17 %s still has %r' % (label, b_[:80]))
_nowhy = '\n'.join(l_ for l_ in txt.split('\n') if not l_.startswith('Why:'))
_E48 = newtxt['E-48']
_card17 = _E48[_E48.index('The one order'):]
_G17 = ks('G')
_P17 = ['revoke the secret key for the model (key step I) and write `key revoked`',
        'shred the copy of the key in the take folder and the other copies of the old key on your own list (key step G, parts (a) and (b)) and write `shred done key copies`',
        'do your items 2, 3 and 4 (item 2: revoke both app passwords; item 3: delete both HubSpot apps; item 4: save the screenshots)',
        'do your item 5, the retire check',
        'do your item 6 (shred its two files) and shred the other secret files on your own list (key step G, parts (c) and (d)), and write `shred done other files`',
        "read the list of what the assistant will remove (the full paths and the container's name) and, if nothing in it is a file that you want to keep, write `start clean-up`",
        'the assistant does its item 1 (the clean-up)']
_START17 = ('Item 1 starts only when ALL of these are true, each as a message that you typed yourself: a confirmation (`yes, no more takes` or `key gone, no more decisions`; key step D.3); '
            '`key revoked` (or `key gone, no more decisions`, which counts as `key revoked`; or `key not revoked` and the reason, but item 1 never starts while a copy of the key exists and the key is not revoked); '
            '`shred done key copies` (or `shred not done key copies` and the reason); your items 2, 3, 4 and 5 done; `shred done other files` (or `shred not done other files` and the reason); '
            'you have read the list of what the assistant will remove; and `start clean-up`.')
# F-1: ONE order in four places, same seven phrases in the same order; ONE start sentence in three places
for _lab, _tx in (('card', _card17), ('E-16', newtxt['E-16']), ('E-55', newtxt['E-55'])):
    _ps = [_tx.find(p_) for p_ in _P17]
    if -1 in _ps or _ps != sorted(_ps): F('r17 F-1 the seven steps are missing or out of order in %s: %s' % (_lab, _ps))
    _r17n += 1
for _lab, _tx in (('G.2', _G17), ('E-16', newtxt['E-16']), ('E-55', newtxt['E-55'])):
    need17('F-1 start sentence in ' + _lab, _tx, _START17)
absent17('F-1 old order forms', _nowhy, 'items 2 and 3', 'items 2 to 5', 'items 2 and 4 and the HubSpot', 'your items 2 to 6', 'your item 3 comes first')
absent17('F-8 old words', _nowhy, '`more takes`', '`shred done 1`', '`shred done 2`', '`shred not done 1`', '`shred not done 2`', 'ONLY when you type it AFTER', 'a `key revoked` that counts', 'counts as the confirmation')
# F-4: one number for the new-key rule
_mins = re.findall(r'at least (\d+) minutes remain', _nowhy)
if len(_mins) < 4 or set(_mins) != {'30'}: F('r17 F-4 the new-key rule has numbers %s' % sorted(set(_mins)))
_r17n += 1
absent17('F-4 old number', _nowhy, 'at least 20 minutes', 'exactly 20 minutes')
# F-3: alarm 3 yields to a running take, in key step C and in the request for the yes
need17('F-3 C', ks('C'), 'if a take is running, let it finish (key step K), then revoke the key at once')
need17('F-3 E-12', newtxt['E-12'], 'if a take is running when it rings, you let it finish')
# F-2: route B price in D.1 and in step 21 (E-57); Appendix K lands on the owner sheet
for _lab, _tx in (('D.1', ks('D')), ('E-57', newtxt['E-57'])):
    need17('F-2 route B price in ' + _lab, _tx, 'up to five days', 'Route A is the safer one')
need17('F-2 appendix landing', APPX_TEXT, 'a separate page, not part of the sheet', 'links it from step 22 item 3')
need17('F-2 link in owner text', _E48, 'the detail is on a separate page, Appendix K, which is linked from this step')
need17('F-2 header', txt, 'Appendix K (after the last row) is not a row and not part of the sheet')
# F-5: D.4 and key step E follow the order of the actions
need17('F-5 D.4', ks('D'), 'you follow the one order (the card) at once, from card step 1')
need17('F-5 E', ks('E'), "(4) the one order (the card above)", "copies the take's result file and counts out of the take folder first")
# F-8: confirmations and the ten minutes
need17('F-8 D.3', ks('D'), 'A confirmation is exactly one of two messages', '`key revoked` is never a confirmation', 'no reply counts as `another take`', 'mean the opposite of each other')
need17('F-8 D.5', ks('D'), 'Between 18:19 UTC = 23:49 IST and 18:29 UTC = 23:59 IST there are only 10 minutes', 'card step 2 (shred the copies of the key)')
need17('F-8 clock', _G17, 'the assistant has no timer: it reads the time shown on your last message')
need17('F-8 F', ks('F'), 'including a bare `no`, counts as `not sure`')
need17('F-8 B', ks('B'), '`another take`', '`shred done key copies`', '`shred done other files`', 'It never confirms anything, at any time')
# F-9: shred rule heading and the marks of part (b) and (d)
need17('F-9 G', _G17, 'It is ONE rule for every file that you shred in this item and in step 8', 'mark it `old key` (part (b)) or `other` (part (d))', 'a file is in exactly one part')
need17('F-9 E-37', newtxt['E-37'], 'Mark each file `old key`', 'as part (a)')
# security: N1 (owner-open) with three options and the accepted-risk sentence; minors 4, 5, 7; r16 NOT DONE items
need17('N1 ND16', txt, '16. **Nobody but the owner can cancel the secret key for the model', 'Options, not decided by the builder: (1)', '(2) name a second person', '(3) the owner accepts the exposure in writing', 'I accept that until I revoke the secret key for the model it can spend up to what my account at the company allows')
need17('N1 key step A', ks('A'), 'limits the program only, not a copy of the key', 'Whether the company that provides the AI model can also limit this key is not checked')
need17('r confirmation', txt, 'r. Round 17 additions of the builder, to confirm:')
need17('m4 E-09', newtxt['E-09'], 'write its full path on your own list (mark it `other`)', 'add the full path of `n8n.env` to your own list (mark it `other`)', 'Detail: appendix K-8')
need17('K-8 moved', APPX_TEXT, 'K-8 (detail of step 8')
need17('m7 E-62', why_of('E-62'), 'Round 17 (security m7)')
need17('E-16 copy first', newtxt['E-16'], 'At the start of item 1 it checks that this copy is there')
# scans over owner text and the appendix
_own17 = _ownall + '\n' + APPX_TEXT
for _m in re.finditer(r'(?<![\w~.\-])/(?:home|Users|root|tmp|var|etc|opt|usr)/|\b[A-Za-z]:\\\\', _own17): F('r17 absolute path in owner text: ' + _own17[max(0, _m.start()-20):_m.end()+20].replace('\n', ' '))
for _m in re.finditer(r'\b(?:ORD|DEC|WP\d*|L-[A-Z0-9]+)[:\-]|\brow E-\d\d|\bE-\d\d\b|\bND ?\d+\b|\bF-\d+\b', _own17): F('r17 internal code in owner text: ' + _m.group(0))
_r17n += 2
for _m in re.finditer(r'spending window ends(?: later,)? at (\d\d:\d\d) UTC = (\d\d:\d\d) IST', _own17 + '\n' + txt):
    if (_m.group(1), _m.group(2)) != ('18:29', '23:59'): F('r17 spending window end is wrong: ' + _m.group(0))
for _m in re.finditer(r'\bby (?:Mon 23 Nov 2026 )?(\d\d:\d\d) UTC = (\d\d:\d\d) IST at the latest', _own17):
    if (_m.group(1), _m.group(2)) != ('18:19', '23:49'): F('r17 last time to revoke is wrong: ' + _m.group(0))
# the pins: one exact sentence per safety rule that a mutation was able to delete or reverse without a failure in round 16
_SC = {'A': ks('A'), 'B': ks('B'), 'C': ks('C'), 'D': ks('D'), 'E': ks('E'), 'F': ks('F'), 'G': _G17, 'H': ks('H'), 'I': ks('I'), 'K': ks('K'), 'CARD': _card17, 'CARD7': _card17[:_card17.index('Key step J')], 'E48': _E48, 'APPX': APPX_TEXT, 'E-57': newtxt['E-57'], 'WHY62': why_of('E-62')}
PINS17 = [
 ('m18 D.4 appendix ref', 'D', 'Detail with the full costs of both routes: appendix K-D'),
 ('m34 word list', 'B', '`key revoked`, `key not revoked`, `key gone, no more decisions`, `shred done key copies`'),
 ('m37 window end', 'A', 'The spending window ends 10 minutes later, at 18:29 UTC = 23:59 IST'),
 ('m40 not sure', 'F', 'Reply `yes`, `no, other things use it` or `not sure`'),
 ('m41 only yes', 'F', 'Only `yes` together with `different key` means that nothing has to be replaced first'),
 ('m43 stop looking', 'B', '`ok flow rehearsal`, `please stop looking`, `you may look again`'),
 ('m45 C', 'C', 'unless at least 30 minutes remain after you have answered'),
 ('m45 H', 'H', 'only if at least 30 minutes remain before 18:19 UTC = 23:49 IST'),
 ('m45 I', 'I', 'and at least 30 minutes remain'),
 ('m45 card', 'CARD', 'at least 30 minutes remain'),
 ('m48 G', 'G', 'Do not shred part (a) while a take is running'),
 ('m48 K', 'K', 'Do not shred part (a) until the take has stopped'),
 ('m51 why', 'WHY62', 'Security F2 of round 15: input line 112'),
 ('m53 unverified', 'K', 'is not proven (UNVERIFIED)'),
 ('m54 typed', 'E48', 'Only your own typed messages count (key step B)'),
 ('r17 card 7', 'CARD7', '7. Then the assistant does its item 1 (the clean-up). It never starts while a copy of the key exists and the key is not revoked.'),
 ('m60 card 1', 'CARD', 'on Mon 23 Nov 2026 it is at 18:19 UTC = 23:49 IST at the latest'),
 ('B03 no space', 'G', 'It contains no `..`, no space, no quote sign'),
 ('B04 ten minutes', 'APPX', 'the 10 minutes between are only for the shred of the key copies'),
 ('B05 step 21 heading', 'E-57', '### Step 21. Watch the cut by Mon 23 Nov 2026 18:19 UTC = 23:49 IST'),
 ('B08 never opens', 'E48', 'The assistant never opens the key file (this is a procedure, not enforced by a program).'),
 ('B09 default', 'D', 'no reply counts as `another take`'),
 ('B10 forced revoke', 'K', 'revoke the key at that time anyway (key step I)'),
 ('r17 key gone one word', 'B', 'so after it you do not type `key revoked` again'),
 ('r17 D.5 key gone', 'D', 'then write `key gone, no more decisions`'),
]
for _lab, _sc, _ph in PINS17:
    need17('pin ' + _lab, _SC[_sc], _ph)
absent17('B09 reversed', ks('D'), 'no reply counts as `no more takes`')
absent17('B10 reversed', ks('K'), 'wait for the take')
# word counts: ONE method, stated here: runs of non-space characters (str.split) inside the ~~~~ fences of the NEW blocks; the label line and the fence lines are not counted
_wc = lambda s_: len(s_.split())
_wo = sum(_wc(b_) for r_ in rows if r_['file'].startswith('OWNER-STEPS') for b_ in r_['new'])
_wa = sum(_wc(b_) for r_ in rows for b_ in r_['new'])
print('WORDS (non-space runs inside the NEW fences): E-48 NEW', _wc(newtxt['E-48']), '; Appendix K (whole section)', _wc(APPX_TEXT), '; OWNER-STEPS rows NEW', _wo, '; NEW of all rows', _wa, '; whole EDITS file', _wc(txt))
print('r17 checks:', _r17n, 'phrase checks;', len(PINS17), 'pins')
print('round 17 checks done')

