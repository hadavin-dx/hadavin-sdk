# ================= round 16 checks (security F1 to F4, m1 to m8; stranger M1 to M7; runner's nine missed mutations) =================
_r16n = 0
def need16(label, text, *needles):
    global _r16n
    for nd_ in needles:
        _r16n += 1
        if nd_ not in text: F('r16 %s lacks %r' % (label, nd_[:70]))
def absent16(label, text, *bad):
    global _r16n
    for b_ in bad:
        _r16n += 1
        if b_ in text: F('r16 %s still has %r' % (label, b_[:70]))
_own = [(r_['id'], b_) for r_ in rows if r_['file'].startswith('OWNER-STEPS') for b_ in r_['new']]
_ownall = '\n'.join(b_ for _, b_ in _own)
_full48 = newtxt['E-48']
# F1: a separate plain word, and key revoked counts only after the last time
need16('F1 word', ks('B'), '`key gone, no more decisions`')
need16('F1 D5', ks('D'), 'ONLY when you type it AFTER 18:19 UTC = 23:49 IST on Mon 23 Nov 2026', 'no `no more takes` before it', '`key gone, no more decisions`')
need16('F1 E-55', newtxt['E-55'], 'ONLY when you type it AFTER 18:19 UTC = 23:49 IST on Mon 23 Nov 2026', '`key gone, no more decisions`')
absent16('F1 old sentence', newtxt['E-55'], 'and your `key revoked` then counts as `no more takes`')
# F2: contacts only by the exact address, at most 3, in the three rows, and no made-up names
for rid_ in ('E-04', 'E-42', 'E-62'):
    need16('F2 ' + rid_, newtxt[rid_], '`take-<id>-a@example.com`', '`take-<id>-b@example.com`', '`take-<id>-c@example.com`', 'more than 3')
    absent16('F2 ' + rid_, newtxt[rid_], 'made-up names')
_r62 = [r_ for r_ in rows if r_['id'] == 'E-62']
if not _r62 or _r62[0]['line'] != 112 or 'delete any leftover HubSpot contacts the lead counted' not in _r62[0]['old'][0]: F('r16 E-62 header or old text')
if _r62 and _r62[0]['status'] != 'Apply now': F('r16 E-62 status')
# F3: shred part (d) and the own list
need16('F3 G', ks('G'), '(d)', 'password files and editor copies', 'every file that holds a secret you saved', '`shred done 2`')
need16('F3 E-59', newtxt['E-59'], '`shred done 2`', 'part (d)')
need16('F3 E-37', newtxt['E-37'], 'your own list of every file in which you saved a secret')
# F4: one numbered order (the card) and item 1 never early
_card = _full48[_full48.index('The one order'):]
_pos = []
for _k in ('1. Revoke the secret key', '2. Shred the copy of the key in the take folder', '3. Do your items 2 and 4', '4. Do your item 5', '5. Shred the two files of your item 6', '6. Read the list that the assistant sends', '7. The assistant does its item 1'):
    _pos.append(_card.find(_k))
if -1 in _pos or _pos != sorted(_pos): F('r16 F4 the numbered order is missing or out of order: %s' % _pos)
need16('F4 card', _card, '`shred done 1`', '`shred done 2`', '`start clean-up`', 'never starts while a copy of the key exists and the key is not revoked')
need16('F4 E-16', newtxt['E-16'], 'It does NOT start while a copy of the secret key for the model exists and the key is not revoked', 'The order of step 22 is the only order')
absent16('F4 E-16', newtxt['E-16'], 'your item 3 comes first', 'None of it can be undone and because', 'about doing items first')
# m1 take folder and list, m4 stop looking before the click, m5 ok words, m3 alarm 3, m6 counts, m8 other secret files
need16('m1 E-16', newtxt['E-16'], 'NEW, EMPTY folder', 'never your home folder', 'if a recording or a video file is inside, it stops, removes nothing and tells you', 'You read that list before you type `start clean-up`')
need16('m5 E-11', newtxt['E-11'], '`ok stand-in test`', '`ok flow rehearsal`')
need16('m3 alarms', ks('C') + newtxt['E-12'], 'Alarm 3: Mon 23 Nov 2026 18:09 UTC = 23:39 IST', 'alarm 3 for 18:09 UTC = 23:39 IST')
# stranger M2: margin arithmetic computed in the checker, not copied
_typing = _dt.datetime(2026, 11, 23, 18, 0); _prog = _typing + _dt.timedelta(seconds=60); _pend = _prog + _dt.timedelta(seconds=860); _rev2 = _dt.datetime(2026, 11, 23, 18, 19)
if _prog.strftime('%H:%M:%S') != '18:01:00' or _pend.strftime('%H:%M:%S') != '18:15:20' or (_rev2 - _pend).seconds != 220: F('r16 margin arithmetic')
need16('M2 E-12', newtxt['E-12'], '18:01:00 UTC = 23:31:00 IST', '18:15:20 UTC = 23:45:20 IST', '3 minutes 40 seconds before the last time to revoke', 'the time at which you START TYPING')
absent16('M2 old claim', _ownall, 'a take that lasts 4 minutes longer', '4 minutes 40 seconds before the last time to revoke')
# stranger M1: cross references
need16('M1 B refs', newtxt['E-12'] + newtxt['E-16'] + newtxt['E-55'], 'key step B')
absent16('M1 refs', newtxt['E-12'], 'only a message typed by you counts: step 22 item 3, key step C', 'key step F); the click path')
absent16('M1 refs', newtxt['E-16'] + newtxt['E-09'] + newtxt['E-52'], 'item 3, key step C)')
absent16('M1 revoke page', newtxt['E-12'], 'revoke the secret key for the model (step 22 item 3, key step F)')
# stranger minors: no internal codes or branch names in owner text; plain words
for _w in ('take/nlite', 'HEAD_PIN', 'r17', 'F-01', ' >= '):
    absent16('plain words', _ownall, _w)
if re.search(r'\blease\b', _ownall): F('r16 the word lease is in owner text')
absent16('E-56 codes', newtxt['E-56'], 'Q23', '(r17)', 'F-01')
absent16('E-57 default', newtxt['E-57'], "is the assistant's default")
if '\n## Phase 1: the assistant checks.\n' not in '\n' + newtxt['E-54']: F('r16 E-54 heading is not on its own line')
need16('E-37', newtxt['E-37'], 'UNVERIFIED')
# runner mutation #15, #17: the wait for `not looking` follows every `please stop looking` (owner text and the rule that defines it)
for _rid, _b in [(r_['id'], b_) for r_ in rows for b_ in r_['new']]:
    for _m in re.finditer(r'please stop looking', _b):
        _win = _b[_m.end():_m.end() + 90]
        if 'not looking' not in _win and not _win.startswith('` and `you may look again`') and not _win.startswith('`, `you may look again`'):
            F('r16 stop-looking without the wait for `not looking` in %s: %r' % (_rid, _win[:60]))
if 'wait for its written reply `not looking`' not in txt: F('r16 typing rule definition lacks the wait for its written reply `not looking`')
# runner mutation #18: E-09 sub-step a lists every typing sub-step
if '(sub-steps c, f, g and h)' not in newtxt['E-09']: F('r16 E-09 a does not list sub-steps c, f, g and h')
for _sub in 'fgh':
    _mm = re.search(r'(?m)^   %s\. .*$' % _sub, newtxt['E-09'])
    if not _mm or not re.search(r'typing rule|not looking', _mm.group(0)): F('r16 E-09 sub-step %s does not call the typing rule' % _sub)
# runner mutations #19, #22, #24: the five checks of the shred rule and the command, in key step G
need16('shred rule', ks('G'), 'realpath', "`ls -l '<path>'`", "`shred -u -- '<path>'`", 'contains no `..`', 'starts with `/`', '/x/take-10', 'number `1` in its second column', 'a link is a shortcut', 'Never shred a recording')
# runner mutations #31, #32: the alarm names stay with their alarm, in every place
for _rid, _b in [(r_['id'], b_) for r_ in rows for b_ in r_['new']]:
    for _m in re.finditer(r'[Aa]larm 1[^`\n]*?named `([^`]+)`', _b):
        if 'revoke the secret key for the model' not in _m.group(1) or 'left' in _m.group(1): F('r16 alarm 1 has the wrong name in %s: %r' % (_rid, _m.group(1)))
    for _m in re.finditer(r'[Aa]larm 2[^`\n]*?named `([^`]+)`', _b):
        if 'still alive' not in _m.group(1): F('r16 alarm 2 has the wrong name in %s: %r' % (_rid, _m.group(1)))
    for _m in re.finditer(r'[Aa]larm 3[^`\n]*?named `([^`]+)`', _b):
        if '10 minutes left' not in _m.group(1): F('r16 alarm 3 has the wrong name in %s: %r' % (_rid, _m.group(1)))
need16('alarm names', ks('C'), 'Alarm 1: Mon 23 Nov 2026 17:49 UTC = 23:19 IST, named `revoke the secret key for the model`', 'named `is the secret key for the model still alive?`', 'named `10 minutes left: revoke the secret key for the model now`')
# runner mutation #51: the widened secret-shape scan (the sample in the controls is built from parts)
_pre = 'sk-' + 'ant-' + 'api03'
_secpats = [_pre + r'[-A-Za-z0-9_]{6,}', r'\bsk-[A-Za-z0-9_-]{16,}', r'AKIA[0-9A-Z]{16}', r'ghp_[A-Za-z0-9]{20,}', r'xox[bap]-[A-Za-z0-9-]{10,}', r'-----BEGIN [A-Z ]*PRIVATE KEY', r'(?i)\bpassword\s*[:=]\s*[^\s`]{6,}', r'\b[A-Fa-f0-9]{40,}\b', r'\beyJ[A-Za-z0-9_-]{15,}\.']
_sh2 = 0
for _p in _secpats:
    for _m in re.finditer(_p, txt):
        if _m.group(0) == 'AKIAIOSFODNN7EXAMPLE': continue
        _sh2 += 1; F('r16 secret-shaped text matches ' + _p[:18])
# runner's extra checks: index agrees with the row headers; every owner NEW has no internal code; hold labels; time pairs
_idx = {}
for _l in lines:
    _m = re.match(r'^\| (E-\d+) \| (\S+) \| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \|$', _l)
    if _m: _idx[_m.group(1)] = _m.groups()
if sorted(_idx) != sorted(r_['id'] for r_ in rows): F('r16 index rows differ from header rows')
for r_ in rows:
    _x = _idx.get(r_['id'])
    if not _x: continue
    _ln = str(r_['line']) + (' (and %d)' % r_['line2'] if r_['line2'] else '')
    _stt = re.split(r' \(', r_['status'])[0].strip()
    if _x[1] != r_['file'] or _x[2] != _ln or _x[3] != _stt or _x[6] != r_['type']: F('r16 index mismatch for ' + r_['id'])
_codes = re.compile(r'\b(Q\d{2}(?:\.\d)?|L-[A-Z0-9]{1,8}|ND ?\d{1,2}|E-\d\d|S9-\d|WP\d+|EL-\d|R\d{1,3}|F-\d\d|G[1-5]|D\d{1,2})\b')
for _rid, _b in _own:
    for _m in _codes.finditer(_b): F('r16 internal code in owner text %s: %s' % (_rid, _m.group(0)))
_np = 0
for _m in re.finditer(r'(\d{1,2}):(\d{2})(?::(\d{2}))? UTC = (\d{1,2}):(\d{2})(?::(\d{2}))? IST', txt):
    _np += 1
    _u = int(_m.group(1)) * 3600 + int(_m.group(2)) * 60 + int(_m.group(3) or 0); _i = int(_m.group(4)) * 3600 + int(_m.group(5)) * 60 + int(_m.group(6) or 0)
    if (_u + 19800) % 86400 != _i: F('r16 UTC/IST pair is wrong: ' + _m.group(0))
_wdn = 0
_wd16 = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
for _m in re.finditer(r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\.? (\d{1,2}) (Oct|Nov|Dec)(?: (\d{4}))?', txt):
    _wdn += 1
    _d = _dt.date(int(_m.group(4) or 2026), {'Oct': 10, 'Nov': 11, 'Dec': 12}[_m.group(3)], int(_m.group(2)))
    if _wd16[_d.weekday()] != _m.group(1) or _d.year != 2026: F('r16 weekday/date wrong: ' + _m.group(0))
_bt = open(os.path.join(os.path.dirname(HERE_), '..', '..', 'tests', 'test_no_reference_material.py'), encoding='utf-8').read()
_bm = re.search(r'BANNED = \((.*?)\n\)', _bt, re.S)
_banned = ast.literal_eval('(' + _bm.group(1) + ')')
_bh = sum(1 for b_ in _banned if b_ in txt)
if _bh: F('r16 banned strings present: %d of %d (counts only)' % (_bh, len(_banned)))
# mtimes are read at run time, never typed in
_mt = {n_: os.path.getmtime(os.path.join(IN, n_)) for n_ in ('OWNER-STEPS-realrun-v3.md', 'AGENT-SCOPE-DO-AND-DONT.md', 'DECISION-one-store.md')}
print('r16 checks:', _r16n, 'phrase checks; UTC=IST pairs', _np, '; weekday-date pairs', _wdn, '; banned', _bh, 'of', len(_banned), '; secret-shaped', _sh2, '; input mtimes read at run time', len(_mt))
print('round 16 checks done')

