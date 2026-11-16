
# ================= round 19 checks (security M1-M3; naive B1-B4; runner: classes found in r17; per-occurrence checks over the applied text) =================
_r19n = 0
_AP = cp1['OWNER-STEPS-realrun-v3.md']
_DAYF = os.path.join(HERE_, 'r19-OWNER-DAY-SHEET.md'); _APPF = os.path.join(HERE_, 'r19-OWNER-APPENDIX-K.md')
_DAY = open(_DAYF, encoding='utf-8').read() if os.path.exists(_DAYF) else ''
_APP = open(_APPF, encoding='utf-8').read() if os.path.exists(_APPF) else ''
# the safety phrases and time pairs: exact number of copies in (applied sheet, day sheet, appendix); a change at ANY copy changes a count
_KS = ("The key is revoked by 18:19 UTC = 23:49 IST; the last 10 minutes (18:19 UTC = 23:49 IST to 18:29 UTC = 23:59 IST) are for card steps 2 and 3; "
       "if the key is still live at 18:19 UTC = 23:49 IST it comes first.")
_TW = ("`no more takes` alone is never final; the confirmation is `yes, no more takes`; "
       "if you have revoked the key without having typed `yes, no more takes`, write `key gone, no more decisions`.")
_WARN3 = "In route B, writing `key gone, no more decisions` before you have watched the cut makes the cut final and costs you the retake."
_CANON19 = {
    _KS: (3, 2, 2),
    _TW: (6, 2, 1),
    _WARN3: (3, 2, 0),
    'the last 10 minutes': (5, 4, 2),
    'to be confirmed by the studio lead before you rely on it': (11, 5, 1),
    'THE KEY IS NOT DEFERRABLE': (1, 1, 0),
    'last chance: revoke the secret key for the model now': (2, 1, 0),
    'if the secret key for the model is still not revoked, revoke it now': (2, 1, 0),
    '`web revokes not done`': (6, 4, 0),
    'Which one counts as used by your own n8n': (1, 1, 0),
    'In route A the live key exists for hours, in route B for up to five days': (2, 0, 1),
    'Why these two times': (1, 1, 0),
    'Words in this item:': (1, 1, 0),
    'it is not deferrable (key step D.5)': (1, 1, 0),
    'alarm 1, alarm 3 and the last time to revoke': (1, 1, 0),
    'A confirmation cannot be withdrawn once the key is revoked.': (2, 1, 0),
    'No default pick: the assistant does not recommend a route': (1, 0, 0),
    'touch nothing that you are not sure about': (1, 1, 0),
    'no reply counts as `another take`': (2, 0, 0),
    '`key revoked` is never a confirmation': (1, 0, 0),
    'It never confirms anything, at any time': (1, 0, 0),
    'Item 1 starts only when ALL the conditions of key step G.2 are true': (2, 0, 0),
    'It never starts while a copy of the key exists and the key is not revoked': (1, 1, 0),
    'asks you to type the words yourself in a new message': (1, 0, 0),
    'What you have not finished by 18:29 UTC = 23:59 IST you finish': (3, 2, 0),
    'Tue 24 Nov 2026 18:29 UTC = 23:59 IST': (10, 4, 1),
    'not all': (2, 0, 0),
    'if you have not typed `yes, no more takes` by 18:19 UTC = 23:49 IST, revoke the key at that time anyway': (1, 1, 0),
    'Only messages that you type yourself count': (1, 0, 0),
    '`not sure` never keeps it alive': (1, 0, 0),
    'The assistant never does an owner item for you': (1, 1, 0),
    'A confirmation is exactly one of two messages': (2, 0, 0),
    'touch NOTHING of that kind': (1, 1, 0),
    'your list says that your own n8n does not use it': (1, 1, 0),
    '18:19 UTC = 23:49 IST': (0, 0, 0),
    '18:29 UTC = 23:59 IST': (0, 0, 0),
    '17:49 UTC = 23:19 IST': (2, 1, 0),
    '18:09 UTC = 23:39 IST': (2, 1, 0),
    '06:00 UTC = 11:30 IST': (2, 1, 0),
    '`yes, no more takes`': (0, 0, 0),
    '`key gone, no more decisions`': (0, 0, 0),
    '`cut accepted`': (0, 0, 0),
    '`start clean-up`': (4, 3, 0),
    '`shred done key copies`': (6, 6, 0),
    '`shred done other files`': (7, 6, 0),
    '`key revoked`': (0, 0, 0),
    '`route A`': (4, 1, 0),
    '`route B`': (4, 1, 0),
}
_PAIR = re.compile(r'\b(\d\d):(\d\d)(?::(\d\d))? UTC (?:=|/) (\d\d):(\d\d)(?::(\d\d))? IST')
_BAREUTC = re.compile(r'\b\d\d:\d\d(?::\d\d)? UTC\b(?! (?:=|/) \d\d:\d\d(?::\d\d)? IST)')
_BAD19 = (r'\brevoke\b[^.\n,;]{0,100}\bby (?:Mon 23 Nov 2026 )?18:29', r'last time to revoke[^.]{0,80}18:29', r'18:29 UTC = 23:59 IST[^.]{0,40}last time to revoke',
          r'recommends? route B', r'\(recommended\)', r'can be withdrawn', r'\bnone of the (?:shreds|items) (?:is|are) (?:needed|required)', r'`more takes`', r'`shred done 1`', r'`shred done 2`',
          r'by 18:29 UTC = 23:59 IST[^.\n,;]{0,60}\brevoke the secret key', r'\brevoke the secret key[^.\n,;]{0,60}by 18:29',
          r'10 minutes left', r'Route A is the safer one', r'there are only 10 minutes', r'(?<!the last )10 minutes', r'safer one', r'three alarms', r'Set three', r'a question for the studio lead', r'not decided yet')
def _norm19(t):
    return [l_.strip() for l_ in t.split('\n') if l_.strip()]
def check19(ap, day=None, app=None, tag=''):
    """returns the list of failure labels for the applied owner sheet (and the two linked pages when given)"""
    out = []
    for lab, t, k in (('applied', ap, 0), ('day sheet', day, 1), ('appendix', app, 2)):
        if t is None: continue
        for p_, cnt in _CANON19.items():
            if t.count(p_) != cnt[k]: out.append('count %s %r is %d, expected %d' % (lab, p_[:60], t.count(p_), cnt[k]))
        for m_ in _BAREUTC.finditer(t): out.append('UTC time without its IST pair in %s: %s' % (lab, t[m_.start():m_.end() + 20]))
        for m_ in _PAIR.finditer(t):
            h1, m1, s1, h2, m2, s2 = m_.groups()
            tot = (int(h1) * 3600 + int(m1) * 60 + int(s1 or 0) + 19800) % 86400
            if (s1 is None) != (s2 is None) or tot != int(h2) * 3600 + int(m2) * 60 + int(s2 or 0): out.append('wrong UTC/IST pair in %s: %s' % (lab, m_.group(0)))
        for b_ in _BAD19:
            if re.search(b_, t): out.append('forbidden wording in %s: %s' % (lab, b_))
    if day is not None:
        apl = ap
        for l_ in _norm19(day.split('## The card', 1)[1] if '## The card' in day else day):
            if l_.startswith('#') : continue
            if l_ not in apl: out.append('day sheet line is not in the applied sheet: ' + l_[:70])
    if app is not None:
        ap_k = ap
        for l_ in _norm19(app):
            if l_.startswith('#') or len(l_) < 60: continue
            if l_ not in set(_norm19(ap)) and l_ not in set(_norm19(txt)): out.append('appendix line is not in the applied sheet or in EDITS: ' + l_[:70])
    return out
_r19f = check19(_AP, _DAY, _APP)
for _f in _r19f: F('r19 ' + _f)
_r19n += len(_CANON19) * 3 + 6
# owner text names the two linked files once each and says what each holds
need17('r19 link day sheet', _AP, '`OWNER-DAY-SHEET.md`', '`OWNER-APPENDIX-K.md`')
for _need in ('## Key step I: revoke the key', '## The identification check', '## The shred rule (key step G)', '## Why 18:19 and 18:29', '## Your four alarms', '## Words used on this page', 'Item 2 (app passwords)', 'Item 6 (the two files'):
    if _need not in _DAY: F('r19 day sheet lacks ' + _need)
if _AP.count('Alarm 4: Tue 24 Nov 2026 06:00 UTC = 11:30 IST') != 1: F('r19 alarm 4 in the sheet')
absent17('r19 the card exists once', _AP.replace(_AP[_AP.index('The one order'):_AP.index('Key step J (other keys)')], '', 1), '1. You: make sure that you have confirmed', '7. Then the assistant does its item 1')
if not _DAY or not _APP: F('r19 the linked day sheet or appendix file is missing')
if len(_DAY.split()) < 2500 or len(_DAY.split()) > 4800: F('r19 day sheet word count %d' % len(_DAY.split()))
# one typed word, one table row, one event: each word has exactly one row in the table (and the same row in the day sheet)
_rows18 = re.findall(r'^\s*\| (`[^|]+`(?: or `[^|]+`)?) \| ([^|]+) \| ([^|]+) \|', _AP, re.M)
_ev = [r_[1] for r_ in _rows18]
_wd = [w_ for r_ in _rows18 for w_ in re.findall(r'`([^`]+)`', r_[0])]
if len(_rows18) < 18 or len(set(_wd)) != len(_wd): F('r19 typed words: %d rows, or a word has two rows' % len(_rows18))
for _l in _norm19(_DAY.split('## Table of the typed words', 1)[1]) if _DAY else []:
    if _l.startswith('| `') and _l not in set(_norm19(_AP)): F('r19 day sheet table row differs: ' + _l[:60])
print('r19 applied sheet words (wc -w method): %d; day sheet %d; appendix %d' % (len(_AP.split()), len(_DAY.split()), len(_APP.split())))
print('r19 checks:', _r19n, 'count/pair/forbidden checks;', len(_r19f), 'failures in the section')
print('round 19 checks done')
