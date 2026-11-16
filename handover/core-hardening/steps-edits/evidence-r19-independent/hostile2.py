import os, re, sys, subprocess, ast, collections, json
EV = os.path.dirname(os.path.abspath(__file__))
SE = EV + '/treeB/root/core-hardening/steps-edits/'
EDITS0 = open(SE + 'EDITS.md', encoding='utf-8').read()
DAY0 = open(SE + 'r19-OWNER-DAY-SHEET.md', encoding='utf-8').read()
APP0 = open(SE + 'r19-OWNER-APPENDIX-K.md', encoding='utf-8').read()
CHG0 = open(SE + 'r19-CHANGES.md', encoding='utf-8').read()
PIN0 = open(SE + 'r19-pins.txt', encoding='utf-8').read()
bt = open(EV + '/treeB/tests/test_no_reference_material.py', encoding='utf-8').read()
BANNED = ast.literal_eval('(' + re.search(r'BANNED = \((.*?)\n\)', bt, re.S).group(1) + ')')
def sentences(t):
    out = []
    for l in t.split('\n'):
        l = l.strip()
        if not l: continue
        out += [s.strip() for s in re.split(r'(?<=[.!?;]) +', l) if s.strip()]
    return out
def pins_for(t):
    c = collections.Counter(sentences(t))
    return ''.join('%d\t%s\n' % (n, s) for s, n in sorted(c.items()))
def nth(t, old, new, n=0):
    idx = [m.start() for m in re.finditer(re.escape(old), t)]
    assert len(idx) > n, ('anchor', old[:50], len(idx))
    s = idx[n]; return t[:s] + new + t[s + len(old):]
def run(name, edits=None, regen=False, day=None, app=None, chg=None):
    files = {'EDITS': edits}
    wr = {}
    if day is not None: wr['r19-OWNER-DAY-SHEET.md'] = (day, DAY0)
    if app is not None: wr['r19-OWNER-APPENDIX-K.md'] = (app, APP0)
    if chg is not None: wr['r19-CHANGES.md'] = (chg, CHG0)
    if regen: wr['r19-pins.txt'] = (pins_for(edits), PIN0)
    mp = SE + 'scratch19/hostile-' + name + '.md'
    os.makedirs(SE + 'scratch19', exist_ok=True)
    open(mp, 'w', encoding='utf-8').write(edits if edits is not None else EDITS0)
    try:
        for f, (new, old) in wr.items(): open(SE + f, 'w', encoding='utf-8').write(new)
        env = dict(os.environ); env['EDITS_PATH'] = mp; env['NO_NEG'] = '1'
        out = subprocess.run([sys.executable, '-I', SE + 'verify19.py'], env=env, capture_output=True, text=True, cwd=SE).stdout
    finally:
        for f, (new, old) in wr.items(): open(SE + f, 'w', encoding='utf-8').write(old)
    fails = [l for l in out.split('\n') if l.startswith('FAIL ') ]
    golden = [l for l in fails if 'golden' in l.lower()]
    other = [l for l in fails if l not in golden]
    # redact banned/secret-like content in the log: print only first 80 chars
    return fails, golden, other
M = []
E = EDITS0
KS = "The key is revoked by 18:19 UTC = 23:49 IST; the last 10 minutes (18:19 UTC = 23:49 IST to 18:29 UTC = 23:59 IST) are for card steps 2 and 3; if the key is still live at 18:19 UTC = 23:49 IST it comes first."
def add(name, edits=None, regen=False, **kw): M.append((name, edits if edits is not None else E, regen, kw))
sk = 'sk-' + 'ant-api03-' + 'A' * 24
akia = 'AKIA' + 'ABCDEFGHIJKLMNOP'
for regen in (False, True):
    r = '-regen' if regen else ''
    add('m01-pair-1819-2359-one-copy' + r, nth(E, '18:19 UTC = 23:49 IST', '18:19 UTC = 23:59 IST', 20), regen)
    add('m02-weekday-mon-to-tue-one' + r, nth(E, 'Mon 23 Nov 2026', 'Tue 23 Nov 2026', 7), regen)
    add('m03-tue24-to-wed24-one' + r, nth(E, 'Tue 24 Nov 2026', 'Wed 24 Nov 2026', 9), regen)
    add('m04-alarm4-1130-to-1100-one' + r, nth(E, '06:00 UTC = 11:30 IST', '06:00 UTC = 11:00 IST', 2), regen)
    add('m05-alarm4-time-consistent-pair-one' + r, nth(E, '06:00 UTC = 11:30 IST', '07:00 UTC = 12:30 IST', 3), regen)
    add('m06-1829-pair-wrong-one' + r, nth(E, '18:29 UTC = 23:59 IST', '18:29 UTC = 23:29 IST', 15), regen)
    add('m07-1819-to-1820-consistent-one' + r, nth(E, '18:19 UTC = 23:49 IST', '18:20 UTC = 23:50 IST', 30), regen)
    add('m08-KS-sentence-one-copy' + r, nth(E, KS, KS.replace('it comes first', 'it comes second'), 1), regen)
    add('m09-10min-to-15min-one-copy' + r, nth(E, 'the last 10 minutes (18:19', 'the last 15 minutes (18:19', 3), regen)
    add('m10-typed-yes-no-more-takes-one' + r, nth(E, '`yes, no more takes`', '`yes, no more take`', 4), regen)
    add('m11-typed-key-gone-one' + r, nth(E, '`key gone, no more decisions`', '`key gone, no decisions`', 5), regen)
    add('m12-routeB-condition-to-A' + r, E.replace('In route B, writing `key gone, no more decisions` before', 'In route A, writing `key gone, no more decisions` before', 1), regen)
    add('m13-delete-step21-heading' + r, re.sub(r'^### Step 21\..*\n', '', E, count=1, flags=re.M), regen)
    add('m14-never-opens-removed-one' + r, nth(E, 'The assistant never opens', 'The assistant opens', 0), regen)
    add('m15-nbsp-in-typed-phrase-one' + r, nth(E, '`yes, no more takes`', '`yes, no more takes`', 6), regen)
    add('m16-delete-cancel-line' + r, '\n'.join(l for l in E.split('\n') if not l.startswith('16. **Nobody but the owner can cancel')), regen)
    add('m17-zero-width-in-pair' + r, nth(E, '18:29 UTC = 23:59 IST', '18:29 UTC =​ 23:59 IST', 12), regen)
add('m20-secret-sk-ant', E + '\n' + sk + '\n')
add('m21-secret-akia', E + '\n' + akia + '\n')
add('m22-secret-sk-ant-regen', E + '\n' + sk + '\n', True)
add('m23-banned-in-edits', E + '\n' + BANNED[0] + '\n')
add('m24-banned-in-edits-regen', E + '\n' + BANNED[0] + '\n', True)
add('m25-banned-in-day', None, False, day=DAY0 + '\n' + BANNED[0] + '\n')
add('m26-secret-in-day', None, False, day=DAY0 + '\n' + sk + '\n')
add('m27-secret-in-appendix', None, False, app=APP0 + '\n' + sk + '\n')
add('m28-day-pair-changed', None, False, day=nth(DAY0, '18:19 UTC = 23:49 IST', '18:19 UTC = 23:59 IST', 2))
add('m29-day-weekday-changed', None, False, day=nth(DAY0, 'Tue 24 Nov 2026', 'Wed 24 Nov 2026', 1))
add('m30-day-alarm4-time', None, False, day=DAY0.replace('06:00 UTC = 11:30 IST', '06:00 UTC = 11:00 IST'))
add('m31-day-KS-one-word', None, False, day=nth(DAY0, KS, KS.replace('comes first', 'comes last'), 0))
add('m32-day-10min-15min', None, False, day=nth(DAY0, 'the last 10 minutes', 'the last 15 minutes', 0))
add('m33-day-typed-phrase', None, False, day=nth(DAY0, '`yes, no more takes`', '`yes, no more take`', 0))
add('m34-day-delete-key-step-I-line', None, False, day='\n'.join(l for l in DAY0.split('\n') if 'key step I' not in l))
add('m35-day-delete-18:29-line', None, False, day='\n'.join(l for l in DAY0.split('\n') if '18:29 UTC' not in l))
add('m36-app-pair-changed', None, False, app=nth(APP0, '18:19 UTC = 23:49 IST', '18:19 UTC = 23:59 IST', 0))
add('m37-app-typed-never-final-removed', None, False, app=APP0.replace('`no more takes` alone is never final; the confirmation is `yes, no more takes`;','`no more takes` alone is final; the confirmation is `yes, no more takes`;',1))
add('m39-app-never-content', None, False, app=APP0.replace('(never the content)','(and the content)',1))
add('m38-app-1829-pair', None, False, app=nth(APP0,'18:29 UTC = 23:59 IST','18:29 UTC = 23:29 IST',1))
n = re.search(r'\(wc -l\): (\d+)', CHG0).group(1)
add('m40-chg-forge-lines', None, False, chg=CHG0.replace('(wc -l): ' + n, '(wc -l): ' + str(int(n) + 1)))
add('m41-chg-forge-appliedwords', None, False, chg=CHG0.replace('23267', '23268', 1))
add('m42-chg-forge-daywords', None, False, chg=CHG0.replace('4323', '4324', 1))
add('m43-chg-forge-appendixwords', None, False, chg=CHG0.replace('1353', '1354', 1))
add('m44-chg-forge-partword', None, False, chg=CHG0.replace('437 words', '438 words', 1))
add('m45-chg-forge-16,967', None, False, chg=CHG0.replace('16,967', '16,968'))
add('m46-chg-forge-words-below-100', None, False, chg=CHG0.replace('NOT run', 'run', 1))
add('m47-chg-forge-time-plain-claim', None, False, chg=CHG0.replace('Not run: any EGM review', 'Run: EGM review', 1))
only = sys.argv[1:] 
res = []
for name, ed, regen, kw in M:
    if only and not any(name.startswith(o) for o in only): continue
    fails, golden, other = run(name, ed, regen, **kw)
    changed = (ed != EDITS0) or any(v is not None for v in kw.values())
    caught = len(fails) > 0
    heads = []
    for l in other:
        h = re.sub(r'[^\x20-\x7e]', '?', l)[:85]
        if h not in heads: heads.append(h)
    line = '%s | caught=%s | total_FAIL=%d | golden_only=%d | non_golden=%d | %s' % (name, caught, len(fails), len(golden), len(other), ' || '.join(heads[:3]))
    # redact: never echo banned/secret content
    for b in BANNED: line = line.replace(b, '<BANNED>')
    print(line, flush=True)
