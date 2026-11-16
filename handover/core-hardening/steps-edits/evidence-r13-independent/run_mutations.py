# Plants mutations on a copy of EDITS.md (in memory; written to mut/ only when no banned/secret-shaped text is involved)
import re, os, sys, subprocess, importlib
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import chk13
BASE = open(chk13.HERE + 'steps-edits/EDITS.md', encoding='utf-8').read()
def sec(t, rid):
    i = t.index('### %s:' % rid); j = t.find('\n### ', i + 5); return i, (j if j != -1 else len(t))
def rs(rid, old, new, nth=0):
    def f(t):
        i, j = sec(t, rid); body = t[i:j]; k = body.index('\nNEW')
        assert old in body[k:], (rid, old[:50])
        pos = k
        for _ in range(nth + 1): pos = body.index(old, pos) if _ == 0 else body.index(old, pos + 1)
        return t[:i] + body[:pos] + new + body[pos + len(old):] + t[j:]
    return f
def g(old, new):
    def f(t):
        assert t.count(old) >= 1, old[:60]; return t.replace(old, new, 1)
    return f
def oldchar(rid):
    def f(t):
        i, j = sec(t, rid); body = t[i:j]; k = body.index('OLD (exact):\n~~~~\n') + len('OLD (exact):\n~~~~\n')
        ch = 'Z' if body[k] != 'Z' else 'Y'
        return t[:i] + body[:k] + ch + body[k+1:] + t[j:]
    return f
def swap(a, b):
    def f(t): return t.replace('### %s:' % a, '### TMP:', 1).replace('### %s:' % b, '### %s:' % a, 1).replace('### TMP:', '### %s:' % b, 1)
    return f
R13B = ("Route B (recommended): you write `no more takes` only after you have written `cut accepted` (step 21). Benefit of B: a retake is possible after a bad cut. Cost of B: the key and its copy in the take folder stay alive for up to five days (Wed 18 Nov to Mon 23 Nov 2026), and the revoke on the last day depends on you and your alarm (part 3b). In route B you must watch the cut and write `cut accepted` and `no more takes` before Mon 23 Nov 2026 18:19 UTC = 23:49 IST; if you have not by then, you revoke at that time anyway (part 3j).")
def routeA_only(t):
    t = rs('E-48', R13B, '')(t); return rs('E-48', 'The assistant recommends route B; the choice is yours. ', '')(t)
def inmem_banned(t): return t + '\n' + chk13.load_banned()[0] + '\n'
def inmem_secret(t): return t + '\nAKIA' + 'ABCDEFGHIJKLMNOP' + '\n'
M = [
 ('M01 wrong IST: latest start 18:04 = 23:44', rs('E-12', '18:04 UTC = 23:34 IST', '18:04 UTC = 23:44 IST')),
 ('M02 wrong IST: key end 18:19 = 23:59 (E-48)', rs('E-48', '18:19 UTC = 23:49 IST', '18:19 UTC = 23:59 IST')),
 ('M03 wrong IST: window end 18:29 = 23:29 (E-58)', rs('E-58', '18:29 UTC = 23:59 IST', '18:29 UTC = 23:29 IST')),
 ('M04 wrong IST: alarm 17:49 = 23:49 (E-12)', rs('E-12', '17:49 UTC = 23:19 IST', '17:49 UTC = 23:49 IST')),
 ('M05 old label: "The latest start we plan is 18:04" -> "The latest start is 18:04" (E-12)', rs('E-12', 'The latest start we plan is 18:04', 'The latest start is 18:04')),
 ('M06 old label in index/header: "**latest start we plan** = " -> "**latest start** = "', g('**latest start we plan** = ', '**latest start** = ')),
 ('M07 refusal limit paired with 18:04/23:34', g('program refusal limit is about 18:14 UTC = 23:44 IST', 'program refusal limit is about 18:04 UTC = 23:34 IST')),
 ('M08 latest start we plan paired with 18:14/23:44 (E-12)', rs('E-12', 'latest start we plan (18:04 UTC = 23:34 IST)', 'latest start we plan (18:14 UTC = 23:44 IST)')),
 ('M09 label "program" dropped: "The program refusal limit is a different" (E-12)', rs('E-12', 'The program refusal limit is a different', 'The refusal limit is a different')),
 ('M10 key end 18:29Z in E-48 part 3h', rs('E-48', '3h. Revoke the key, ALWAYS, by 18:19 UTC = 23:49 IST', '3h. Revoke the key, ALWAYS, by 18:29 UTC = 23:59 IST')),
 ('M11 key end 18:29Z in E-55 first sentence', rs('E-55', 'in every case by Mon 23 Nov 2026 18:19 UTC = 23:49 IST', 'in every case by Mon 23 Nov 2026 18:29 UTC = 23:59 IST') if False else rs('E-55', 'and in every case by Mon 23 Nov 2026 18:19 UTC = 23:49 IST at the latest', 'and in every case by Mon 23 Nov 2026 18:29 UTC = 23:59 IST at the latest')),
 ('M12 missing not-looking step: owner does not wait for `not looking` (E-09)', rs('E-09', 'write to the assistant `please stop looking` and wait for its written reply `not looking`; (2)', 'write to the assistant `please stop looking`; (2)')),
 ('M13 route A only (E-48 route B text and recommendation removed)', routeA_only),
 ('M14 shred path without the no-.. rule (E-48 3f)', rs('E-48', 'it contains no `..`; and ', '')),
 ('M15 count 45 vs 44 in header', g('**Apply now 44**', '**Apply now 45**')),
 ('M16 count Hold 13 in header', g('**Hold 12**', '**Hold 13**')),
 ('M17 Apply-now id list drops E-58', g(', E-57, E-58. Round 13 added no row', ', E-57. Round 13 added no row')),
 ('M18 duplicate id: E-20 header renamed E-19', g('### E-20:', '### E-19:')),
 ('M19 ids out of order: E-21 and E-22 swapped', swap('E-21', 'E-22')),
 ('M20 OLD text first character changed (E-14)', oldchar('E-14')),
 ('M21 stated line wrong: E-14 line 107 -> 108', g('### E-14: OWNER-STEPS-realrun-v3.md, line 107,', '### E-14: OWNER-STEPS-realrun-v3.md, line 108,')),
 ('M22 weekday wrong: Mon 23 Nov 2026 -> Tue (E-48)', rs('E-48', 'Mon 23 Nov 2026', 'Tue 23 Nov 2026')),
 ('M23 weekday wrong: Wed 18 Nov 2026 -> Thu (E-12)', rs('E-12', 'Wed 18 Nov 2026', 'Thu 18 Nov 2026')),
 ('M24 same phrase two meanings: E-16 clean-up trigger `no more takes` -> `cut accepted`', rs('E-16', 'only after you have written `no more takes`', 'only after you have written `cut accepted`')),
 ('M25 phrase changed: E-58 `key revoked` -> `key kept` (first)', rs('E-58', 'Right after `key revoked`', 'Right after `key kept`')),
 ('M26 internal code E-nn in owner text (E-48)', rs('E-48', 'WHATEVER you answer', 'WHATEVER you answer (see E-12)')),
 ('M27 internal code ND in owner text (E-09)', rs('E-09', 'write to the assistant `please stop looking`', 'write to the assistant (ND4) `please stop looking`')),
 ('M28 internal code R-number in owner text (E-12)', rs('E-12', 'The program refusal limit is a different', 'The program refusal limit (R7) is a different')),
 ('M29 internal code Q-number in owner text (E-12)', rs('E-12', 'The program refusal limit is a different', 'The program refusal limit (Q25) is a different')),
 ('M30 internal code L-id in owner text (E-16)', rs('E-16', 'in the chat (in route B', 'in the chat (L-23NOV) (in route B')),
 ('M31 unpaired UTC time (E-48 3h)', rs('E-48', '3h. Revoke the key, ALWAYS, by 18:19 UTC = 23:49 IST', '3h. Revoke the key, ALWAYS, by 18:19 UTC')),
 ('M32 key kept alive: E-12 bullet "you revoke ... anyway" -> "you may keep"', rs('E-12', 'you revoke the secret key for the model anyway', 'you may keep the secret key for the model')),
 ('M33 HOLD label removed from E-13 block', rs('E-13', 'NEW [HOLD G3: DO NOT APPLY] (', 'NEW (')),
 ('M34 weekday wrong in text: Wed 18 Nov -> Tue 18 Nov (first, header region)', g('Wed 18 Nov', 'Tue 18 Nov')),
 ('M35 E-48 "WHATEVER you answer" weakened to a conditional', rs('E-48', 'WHATEVER you answer to any question below', 'if you answer yes to question 1')),
 ('M36 index row mismatch: E-14 index line 107 -> 108', g('| E-14 | OWNER-STEPS-realrun-v3.md | 107 |', '| E-14 | OWNER-STEPS-realrun-v3.md | 108 |')),
 ('M37 old single label "latest start" (no "we plan") in E-48/E-55 area: E-55 first sentence', rs('E-12', 'The request states the planned start time and the latest start we plan.', 'The request states the planned start time and the latest start.')),
 ('M38 banned vendor string appended (IN MEMORY ONLY, never written)', inmem_banned),
 ('M39 secret-shaped string built from parts appended (IN MEMORY ONLY)', inmem_secret),
]
INMEM = {'M38', 'M39'}
os.makedirs(HERE + '/mut', exist_ok=True)
v = open(HERE + '/verify13-copy.py').read()
out = []
for name, fn in M:
    tag = name.split()[0]
    try: mt = fn(BASE)
    except Exception as e: out.append((name, 'ANCHOR-ERROR ' + repr(e)[:80], '', '')); continue
    if mt == BASE: out.append((name, 'NO-CHANGE', '', '')); continue
    try:
        fails, _, _ = chk13.check(None, text=mt); mine = sorted(set(k for k, _ in fails)); mine_msg = fails[0][1][:90] if fails else ''
    except Exception as e: mine = ['CRASH']; mine_msg = repr(e)[:90]
    if tag in INMEM: theirs = 'not run (file would hold banned/secret-shaped text)'; tmsg = ''
    else:
        mp = HERE + '/mut/' + tag + '.md'; open(mp, 'w', encoding='utf-8').write(mt)
        env = dict(os.environ); env['EDITS_PATH'] = mp; env['NO_NEG'] = '1'
        pr = subprocess.run([sys.executable, '-B', '-I', HERE + '/verify13-copy.py'], env=env, capture_output=True, text=True, timeout=300)
        fl = [l for l in pr.stdout.split('\n') if l.startswith('FAIL ')]
        if fl: theirs = 'caught (%d FAIL)' % len(fl); tmsg = fl[0][:100]
        elif pr.returncode != 0: theirs = 'caught (crash/exit %d)' % pr.returncode; tmsg = (pr.stderr.strip().split('\n') or [''])[-1][:100]
        else: theirs = 'NOT CAUGHT'; tmsg = ''
    out.append((name, ('caught ' + ','.join(mine) + ' | ' + mine_msg) if mine else 'NOT CAUGHT', theirs, tmsg))
for o in out: print('\n'.join(['MUT ' + o[0], '   mine: ' + o[1], '   verify13: ' + o[2] + ((' | ' + o[3]) if o[3] else '')]))
n = len(out); mc = sum(1 for o in out if o[1].startswith('caught')); vc = sum(1 for o in out if o[2].startswith('caught')); vr = sum(1 for o in out if not o[2].startswith('not run'))
print('TOTAL', n, 'mine caught', mc, 'verify13 caught', vc, 'of', vr, 'run')
