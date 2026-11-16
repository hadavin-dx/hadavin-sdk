# ================= round 20 checks (security M1-M5, m1-m9; stranger M-A to M-G and minors): every fix has a check that fails on r19 and passes on r20 =================
# (label, where, phrase). where: A = applied sheet, D = day sheet, P = appendix, T = EDITS.md as a whole
_NOKEY = "The key has no date and no later date: the assistant asks you again, in every message that it writes to you, until you have written `key revoked` or `key gone, no more decisions`"
NEED20 = [
    ('M1 key has no date (D.5, I)', 'A', _NOKEY), ('M1 key has no date on the day sheet', 'D', _NOKEY),
    ('M1 G.2 excludes the key', 'A', 'except the key (the key has no date: key step D.5)'),
    ('M1 G.2 no later date', 'A', 'as the date to finish (no later date)'),
    ('M1 E-58 row', 'A', 'the key has no later date than 18:19 UTC = 23:49 IST, so send `key revoked` as soon as it is revoked'),
    ('M1 item 3 note', 'A', 'The key is never one of these items.'),
    ('M2 item 5 counts as done (G.2)', 'A', 'and so does item 5 for the login that it concerns'),
    ('M2 item 5 counts as done (E-59)', 'A', 'item 5 counts as done for that login and item 1 does not wait for it (key step G.2)'),
    ('M3 rotate first', 'A', 'Rotate first, then delete, for an item that carries `used`'),
    ('M3 two n8n told apart', 'A', 'Two different n8n are named in this sheet'),
    ('M3 take-only word', 'A', '`take-only` means: you made it new for this take'),
    ('M3 entry end condition', 'A', 'the entry ends only when you tell the assistant in a message'),
    ('M3 app 2 goes to the take n8n', 'A', 'goes into the take\'s n8n only'),
    ('M3 Phase 0 list words', 'A', 'one word: `take-only` or `used`'),
    ('M3 words explain the two n8n', 'D', '`the take\'s n8n` is the new n8n that the assistant starts inside the take folder'),
    ('M4 emergency revoke', 'A', 'an emergency: if you think that the key may have leaked or that somebody else may use it'),
    ('M4 one rule for key gone (B)', 'A', 'Use it whenever you have revoked the key before you typed `yes, no more takes`'),
    ('M4 exceptions list', 'A', 'alarm 1, alarm 3, alarm 4, alarm 5, an emergency (key step D.3) and the last time to revoke (key step D.5) are the exceptions'),
    ('M5 five alarms', 'A', 'Set five alarms on your own phone or computer. Alarm 1:'),
    ('M5 alarm 4 at 18:24', 'A', 'Alarm 4: Mon 23 Nov 2026 18:24 UTC = 23:54 IST, named `still not revoked: revoke the secret key for the model now`'),
    ('M5 alarm 5 unconditional', 'A', 'Alarm 5: Tue 24 Nov 2026 00:30 UTC = 06:00 IST'),
    ('M5 alarm 5 not conditional', 'A', 'you set it in every case, and it is not conditional on anything'),
    ('M5 alarm 2 fixed daytime time', 'A', 'always at 06:30 UTC = 12:00 IST (a fixed time in the daytime'),
    ('M5 alarm 4 or 5 rings', 'A', 'When alarm 4 or alarm 5 rings and the key is not yet revoked'),
    ('M5 ND18', 'T', '18. **Alarm 2 time and the Tue 24 Nov 2026 date.**'),
    ('m1 alarm word', 'A', 'if you have not typed `yes, no more takes`, write `key gone, no more decisions` instead (key step B)'),
    ('m2 route B warning in the prompt', 'A', 'Then write `key gone, no more decisions` (in route B this makes the cut final)'),
    ('m3 In short repaired', 'A', 'Then you revoke the key (key step I)'),
    ('m4 app password page shows only a name', 'A', 'an app password page may show only the name'),
    ('m5 ND19 lists written', 'T', '19. **Typed word `lists written`'),
    ('m6 item 2 click path', 'D', 'at myaccount.google.com, Security, App passwords (this click path is not checked)'),
    ('m7 ND15 option B', 'T', '`cut accepted` and `yes, no more takes` are written before alarm 1 rings'),
    ('m8 no line break', 'A', 'no space, no line break, no quote sign'),
    ('m8 own list is the only check for (b) and (d)', 'A', 'they rest on your handwritten list'),
    ('m9 ND20 recommendation question', 'T', 'The question for the studio lead:'),
    ('MA day sheet holds key step B', 'D', '## Key step B: only you can write the words'),
    ('MA day sheet holds D.1 to D.4', 'D', '## Key step D: the route and the confirmation (D.1 to D.4)'),
    ('MA day sheet says it is not everything', 'D', 'It is NOT the whole retirement'),
    ('MB step 21 heading', 'A', '### Step 21. Watch the cut by Mon 23 Nov 2026 17:49 UTC = 23:19 IST (alarm 1)'),
    ('MB real latest time', 'A', 'The real latest time to confirm in route B is when alarm 1 rings, 17:49 UTC = 23:19 IST on Mon 23 Nov 2026'),
    ('MB K-D', 'P', 'before alarm 1 rings, 17:49 UTC = 23:19 IST on Mon 23 Nov 2026, key step D.5 applies'),
    ('MC G.2 dated Monday', 'A', 'If on Mon 23 Nov 2026, by 18:29 UTC = 23:59 IST'),
    ('MC how to show times', 'A', 'start every message that you write with the time in UTC'),
    ('MC other days', 'A', 'On any other day this time rule does not apply.'),
    ('MD hedge replaced by a rule', 'A', 'this date is a proposal: it stands if the assistant names no other date before your first take'),
    ('MD second person rule', 'A', 'if you named nobody there is no second person'),
    ('MF day sheet defines take and cut', 'D', 'a take is one real run on your test accounts that makes the recording; the cut is the edited video made from your takes (step 21)'),
    ('MF day sheet defines routes', 'D', 'route A and route B are the two ways to confirm that your last take is your last'),
    ('MG exact typing', 'A', 'Type every word exactly as it is written here, without the backticks'),
    ('MG replies of key step F in the table', 'A', 'your answer to a question of key step F'),
    ('min card step 1 time', 'A', '1. You: before 18:19 UTC = 23:49 IST on the last day (key step D.5)'),
    ('min plain words', 'A', 'In plain words: the key is revoked before 18:19 UTC = 23:49 IST'),
    ('min E-37 three questions', 'A', 'asks you three questions and asks you to write two lists'),
    ('min ND header', 'T', 'items 1 to 20'),
]
ABSENT20 = [
    ('M1 old handoff date for the key', 'A', 'the assistant lists it in the handoff with a date to finish it'),
    ('M1 later date', 'A', '(or a later date that you give)'),
    ('M3 old unknown-credential sentence', 'A', 'which key or password those credentials hold is not known (UNVERIFIED), so before the take you open each of them'),
    ('M4 old B sentence', 'A', 'Use it only when all three are true, or when you revoke at the last time to revoke'),
    ('M5 four alarms', 'A', 'Set four alarms'),
    ('M5 alarm 4 do not rely', 'A', 'if the secret key for the model is still not revoked, revoke it now'),
    ('M5 evening alarm', 'A', 'in the evening of every day from the day of your first take'),
    ('m3 double space', 'A', '.  revoke the key'),
    ('MA old claim', 'D', 'only key step A (the fixed rule), key step E'),
    ('MB old route B time', 'A', 'write `cut accepted` and then `yes, no more takes` before 18:19 UTC = 23:49 IST on Mon 23 Nov 2026'),
    ('MC old clock rule', 'A', 'it reads the time shown on your last message in the chat'),
    ('MD hedge', 'A', 'to be confirmed by the studio lead before you rely on it'),
    ('MD hedge on the day sheet', 'D', 'studio lead'),
    ('MD second person open', 'A', 'whether such a person exists is open'),
    ('MD builder word in owner text', 'D', 'the builder believes'),
    ('m7 ND15 stale', 'T', '`cut accepted` and `no more takes` are written before 18:19'),
]
def _where20(w, ap, day, app, tx):
    return {'A': ap, 'D': day, 'P': app, 'T': tx}[w]
def check20(ap, day, app, tx):
    out = []
    for lab, w, ph in NEED20:
        if ph not in _where20(w, ap, day, app, tx): out.append('r20 need: ' + lab)
    for lab, w, ph in ABSENT20:
        if ph in _where20(w, ap, day, app, tx): out.append('r20 absent: ' + lab)
    # the day sheet is not longer than the order allows
    if len(day.split()) > 6300: out.append('r20 day sheet longer than 6300 words')
    # the one-liner of key step I and the alarm rows exist on the day sheet too
    for k_ in ('## Your five alarms', '## Key step I: revoke the key', '## The identification check', '## Table of the typed words'):
        if k_ not in day: out.append('r20 day sheet lacks ' + k_)
    return out
_c20 = check20(_AP, _DAY, _APP, txt)
for _f in _c20: F(_f)
# round order of the last lines of EDITS.md: 18, 19, 20
_ro = [txt.find('- Round %d added:' % n_) for n_ in (18, 19, 20)]
if -1 in _ro or _ro != sorted(_ro): F('r20 the round lines are not in the order 18, 19, 20: %s' % _ro)
# closure table: one row for every finding id of the two reviews of r18 and the two reviews of r19
_CLF = os.path.join(HERE_, 'r20-CLOSURE.md')
_IDS = (['r18 security ' + i_ for i_ in ('M1', 'M2', 'M3', 'M4', 'm1', 'm2', 'm3', 'm4', 'm5', 'm6')] +
        ['r18 stranger ' + i_ for i_ in ('B1', 'B2', 'B3', 'M1', 'M2', 'M3', 'M4', 'M5', 'm1', 'm2', 'm3', 'm4', 'm5', 'm6', 'm7', 'm8', 'm9')] +
        ['r19 security ' + i_ for i_ in ('M1', 'M2', 'M3', 'M4', 'M5', 'm1', 'm2', 'm3', 'm4', 'm5', 'm6', 'm7', 'm8', 'm9')] +
        ['r19 stranger ' + i_ for i_ in ('M-A', 'M-B', 'M-C', 'M-D', 'M-E', 'M-F', 'M-G')])
def closure20(t):
    out = []
    rows = [l_ for l_ in t.split('\n') if l_.startswith('| ')]
    for i_ in _IDS:
        r_ = [l_ for l_ in rows if l_.startswith('| ' + i_ + ' |')]
        if len(r_) != 1: out.append('r20 closure: id %s has %d rows' % (i_, len(r_))); continue
        cells = [c_.strip() for c_ in r_[0].strip().strip('|').split('|')]
        if len(cells) < 4 or cells[2] not in ('CLOSED', 'LEAD-DECISION', 'UNVERIFIED', 'THIRD-PARTY', 'PARTLY') or len(cells[3]) < 20: out.append('r20 closure: id %s status or evidence cell wrong' % i_)
    return out
if os.path.exists(_CLF):
    _clt = open(_CLF, encoding='utf-8').read()
    for _f in closure20(_clt): F(_f)
else: F('r20 closure file r20-CLOSURE.md is missing')
# plants of round 20: every NEED phrase removed, every ABSENT phrase put in, each must be caught BY ITS OWN label; closure rows removed
_pl20 = [0, 0]
def _plant20(label, ap, day, app, tx):
    _pl20[0] += 1
    got = set(check20(ap, day, app, tx)) - set(_c20)
    if label in got: _pl20[1] += 1
    else: F('r20 plant not caught by its own check: ' + label)
for lab, w, ph in NEED20:
    ap, day, app, tx = _AP, _DAY, _APP, txt
    if w == 'A': ap = _AP.replace(ph, '#' + ph[1:], 1)
    elif w == 'D': day = _DAY.replace(ph, '#' + ph[1:], 1)
    elif w == 'P': app = _APP.replace(ph, '#' + ph[1:], 1)
    else: tx = txt.replace(ph, '#' + ph[1:], 1)
    if (ap, day, app, tx) == (_AP, _DAY, _APP, txt): F('r20 plant anchor missing: ' + lab); continue
    _plant20('r20 need: ' + lab, ap, day, app, tx)
for lab, w, ph in ABSENT20:
    ap, day, app, tx = _AP, _DAY, _APP, txt
    if w == 'A': ap = _AP + '\n' + ph
    elif w == 'D': day = _DAY + '\n' + ph
    elif w == 'P': app = _APP + '\n' + ph
    else: tx = txt + '\n' + ph
    _plant20('r20 absent: ' + lab, ap, day, app, tx)
if os.path.exists(_CLF):
    for _i_, _id_ in enumerate(_IDS):
        _pl20[0] += 1
        _t2 = '\n'.join(l_ for l_ in _clt.split('\n') if not l_.startswith('| ' + _id_ + ' |'))
        if closure20(_t2): _pl20[1] += 1
        else: F('r20 closure plant not caught: ' + _id_)
print('r20 checks: need %d, absent %d, closure ids %d; plants (planted, caught): %s' % (len(NEED20), len(ABSENT20), len(_IDS), tuple(_pl20)))
