import os, re, subprocess, sys, ast, shutil
SP = '/tmp/claude-0/-home-user/957f9d59-4d7f-59c1-9611-e85bd7c6c466/scratchpad/'
SRC = '/home/user/hadavin-sdk/handover/core-hardening/steps-edits/EDITS.md'
INP = '/home/user/hadavin-sdk/handover/core-hardening/inputs'
MIR = SP + 'mirror/handover/core-hardening/steps-edits/'
BSRC = '/home/user/hadavin-sdk/tests/test_no_reference_material.py'
txt = open(SRC, encoding='utf-8').read()
bt = open(BSRC, encoding='utf-8').read()
banned = ast.literal_eval('(' + re.search(r'BANNED = \((.*?)\n\)', bt, re.S).group(1) + ')')
def rep(old, new, n=1):
    def f(t):
        assert old in t, 'ANCHOR MISSING: ' + old[:50]
        return t.replace(old, new, n)
    return f
def block_of(t, rid):
    i = t.index('### %s:' % rid); j = t.index('\n### ', i + 5); return i, j
def delrow(rid):
    def f(t):
        i, j = block_of(t, rid); return t[:i] + t[j + 1:]
    return f
def alter_old(rid):
    def f(t):
        i, j = block_of(t, rid); seg = t[i:j]
        k = seg.index('OLD (exact):\n~~~~\n') + len('OLD (exact):\n~~~~\n')
        return t[:i] + seg[:k + 3] + 'Z' + seg[k + 4:] + t[j:]
    return f
def drop_holdlabel(t):
    return t.replace('NEW [HOLD G', 'NEW [hold g', 1)
def addwhy(s):
    def f(t):
        i = t.index('\nWhy:', t.index('### E-02:')); return t[:i] + '\nWhy: ' + s + t[i + 1 + 4 + 1:]  # replaces first chars
    return f
def addtext(s):
    def f(t):
        k = t.index('Why: ', t.index('### E-03:')) ; return t[:k] + s + ' ' + t[k:]
    return f
def newonly(rid, old, new):
    def f(t):
        i, j = block_of(t, rid); seg = t[i:j]
        k = seg.index('NEW'); assert old in seg[k:], 'ANCHOR MISSING in NEW ' + old[:40]
        return t[:i] + seg[:k] + seg[k:].replace(old, new, 1) + t[j:]
    return f
M = [
 ('key end 18:19 -> 18:29 (tied to 23:49)', rep('ends by Mon 23 Nov 2026 18:19 UTC = 23:49 IST at the latest', 'ends by Mon 23 Nov 2026 18:29 UTC = 23:49 IST at the latest')),
 ('key end tied 18:19 = 23:59', rep('revoke the key at that time anyway', 'revoke the key at that time anyway', 1) if False else rep('Key step I. Revoke the key, ALWAYS, by 18:19 UTC = 23:49 IST', 'Key step I. Revoke the key, ALWAYS, by 18:19 UTC = 23:59 IST')),
 ('window end 18:29 tied 23:49', rep('at 18:29 UTC = 23:59 IST (after that', 'at 18:29 UTC = 23:49 IST (after that')),
 ('wrong weekday Mon 23 Nov -> Tue', rep('ends by Mon 23 Nov 2026', 'ends by Tue 23 Nov 2026')),
 ('wrong weekday Wed 18 Nov -> Thu', rep('normally on Wed 18 Nov 2026', 'normally on Thu 18 Nov 2026')),
 ('wrong date Mon 16 Nov -> Mon 17 Nov', rep('Mon 16 Nov 2026', 'Mon 17 Nov 2026')),
 ('wrong weekday of Sun date', rep('Sun 22 Nov', 'Mon 22 Nov') if 'Sun 22 Nov' in txt else rep('Mon 23 Nov', 'Sun 23 Nov')),
 ('IST dropped from key rule', rep('ends by Mon 23 Nov 2026 18:19 UTC = 23:49 IST at the latest', 'ends by Mon 23 Nov 2026 18:19 UTC at the latest')),
 ('IST dropped in E-12 NEW time', newonly('E-12', '18:14 UTC = 23:44 IST', '18:14 UTC')),
 ('IST wrong +5:00', rep('Alarm 1: Mon 23 Nov 2026 17:49 UTC = 23:19 IST', 'Alarm 1: Mon 23 Nov 2026 17:49 UTC = 22:49 IST')),
 ('IST wrong 23:30 -> 23:34 only', rep('(18:00 UTC = 23:30 IST', '(18:00 UTC = 23:34 IST')),
 ('18:04 back in place of 18:00 (NEW heading)', rep('not later than the latest start we plan (18:00 UTC = 23:30 IST)', 'not later than the latest start we plan (18:04 UTC = 23:34 IST)')),
 ('18:04 UTC with 23:30 IST', rep('(18:00 UTC = 23:30 IST', '(18:04 UTC = 23:30 IST')),
 ('latest start text 18:30', rep('**The latest start we plan** is 18:00 UTC = 23:30 IST', '**The latest start we plan** is 18:30 UTC = 00:00 IST')),
 ('not-looking wait removed (E-48 step H)', rep('write `please stop looking`, wait for `not looking`, type or paste the new key', 'write `please stop looking`, type or paste the new key')),
 ('not-looking wait removed (E-09 f)', newonly('E-09', 'write `please stop looking` and wait for `not looking`); in the WSL terminal', 'write `please stop looking`); in the WSL terminal')),
 ('typing rule definition: wait removed', rep('wait for its written reply `not looking`', 'wait a moment')),
 ('E-09 a scope list dropped', rep('(sub-steps c, f, g and h)', '(sub-step c)')),
 ('shred ls -l check removed', rep("(4) `ls -l '<path>'` shows a line", "(4) the path shows a line")),
 ('shred realpath removed', rep("(3) `realpath '<path>'` prints exactly", "(3) the path prints exactly")),
 ('shred no .. rule removed', rep('(2) It contains no `..`, no space', '(2) It contains no space')),
 ('shred -u replaced by rm in rule', rep('Before you run `shred -u` on a file', 'Before you run `rm` on a file')),
 ('shred absolute path rule removed', rep('(1) The path is written in full and starts with `/`', '(1) The path is written')),
 ('shred take-10 prefix rule removed', rep('so that the take folder `/x/take-1` never accepts `/x/take-10/key`', 'so that the folder matches')),
 ('shred whole line (G intro) removed', lambda t: re.sub(r'(?m)^   Key step G\. The shred rule\..*\n', '', t, count=1)),
 ('item 6 wildcard shred back', newonly('E-43' if False else 'E-12', 'x', 'x') if False else rep('Do not use the sign `*`.', 'Use `shred -u ~/take-secrets/*`.')),
 ('yes, no more takes sentence removed', rep('Only a new message from you with the words `yes, no more takes` confirms it. ', '')),
 ('yes, no more takes whole confirmation line removed', lambda t: re.sub(r'(?m)^   The confirmation\. .*\n', '', t, count=1)),
 ('anything-else-counts-as-more-takes removed', rep('Anything else, or no reply, counts as `more takes`. ', '')),
 ('shred done scope (a) only', rep('`shred done` means that EVERY file of (a), (b) and (c) is shredded', '`shred done` means that the file of (a) is shredded')),
 ('alarm text swapped names', lambda t: t.replace('named `revoke the secret key for the model`', 'named @@A', 1).replace('named `is the secret key for the model still alive?`', 'named `revoke the secret key for the model`', 1).replace('named @@A', 'named `is the secret key for the model still alive?`', 1)),
 ('alarm 1 time moved 17:49 -> 18:49', rep('Alarm 1: Mon 23 Nov 2026 17:49 UTC = 23:19 IST', 'Alarm 1: Mon 23 Nov 2026 18:49 UTC = 00:19 IST')),
 ('row deleted (E-61)', delrow('E-61')),
 ('row deleted (E-30)', delrow('E-30')),
 ('duplicate id E-20 -> E-19', rep('### E-20:', '### E-19:')),
 ('id out of order (E-12 <-> E-13 header swap)', lambda t: t.replace('### E-12:', '### @@', 1).replace('### E-13:', '### E-12:', 1).replace('### @@', '### E-13:', 1)),
 ('OLD text altered (E-02)', alter_old('E-02')),
 ('OLD text altered (E-48)', alter_old('E-48')),
 ('OLD stated line wrong (E-02 line 3 -> 4)', lambda t: re.sub(r'(### E-02: \S+, line )3', r'\g<1>4', t, count=1)),
 ('count Apply now 47 -> 48', rep('**Apply now 47**', '**Apply now 48**')),
 ('count rows in total 59 -> 58', rep('59 rows in total', '58 rows in total')),
 ('count OWNER-STEPS 40 -> 39', rep('OWNER-STEPS 40 rows', 'OWNER-STEPS 39 rows')),
 ('Hold label removed (first Hold NEW)', drop_holdlabel),
 ('Hold gate removed from header (E-04)', rep('status Hold (', 'status Hold (')) if False else (lambda t: re.sub(r'(### E-04: [^\n]*?status Hold)[^\n]*?(, type)', r'\1\2', t, count=1)),
 ('index status flipped (E-01 -> Hold)', rep('| E-01 | OWNER-STEPS-realrun-v3.md | 3 | Apply now', '| E-01 | OWNER-STEPS-realrun-v3.md | 3 | Hold')),
 ('index line changed (E-03)', rep('| E-03 | OWNER-STEPS-realrun-v3.md | 5 |', '| E-03 | OWNER-STEPS-realrun-v3.md | 6 |')),
 ('E-nn code in owner text', newonly('E-48', 'Key step A. The fixed rule.', 'Key step A. The fixed rule (see E-12).')),
 ('ND code in owner text', newonly('E-48', 'Key step A. The fixed rule.', 'Key step A. The fixed rule (ND 7).')),
 ('Q code in owner text', newonly('E-48', 'Key step A. The fixed rule.', 'Key step A. The fixed rule (Q23).')),
 ('secret key sk-ant-api03 pattern added', lambda t: t.replace('Why: ', 'Why: ' + 'sk-' + 'ant-' + 'api03-' + 'A1b2C3d4' * 5 + ' ', 1)),
 ('AWS-like key added', lambda t: t.replace('Why: ', 'Why: AKIA' + 'ABCDEFGHIJKLMNOP' + ' ', 1)),
 ('banned string inserted (read at run time)', lambda t: t.replace('Why: ', 'Why: ' + banned[0] + ' ', 1)),
 ('fence line deleted', lambda t: t.replace('~~~~\n', '', 1) if False else t.replace('OLD (exact):\n~~~~\n', 'OLD (exact):\n', 1)),
 ('key step letter relabelled', rep('   Key step F. Two questions.', '   3e. Two questions.')),
 ('In short line removed', rep('   In short: set two alarms', '   Set two alarms')),
 ('whatever-you-answer removed', rep('WHATEVER you answer to any question below, and `not sure` never keeps it alive', 'what you answer to any question below')),
 ('only-typed-words rule weakened', rep('count only when you type them yourself', 'count also when others type them')),
 ('window end 23:59 -> 23:29 IST', rep('18:29 UTC = 23:59 IST (the end of the spending window', '18:29 UTC = 23:29 IST (the end of the spending window')),
 ('Hold row marked Apply now in header (E-04)', lambda t: re.sub(r'(### E-04: [^\n]*?status )Hold[^\n]*?(, type)', r'\1Apply now\2', t, count=1)),
]
os.makedirs(SP + 'mut', exist_ok=True)
res = []
for n, (name, fn) in enumerate(M, 1):
    try:
        m = fn(txt)
    except AssertionError as e:
        res.append((n, name, 'ANCHOR-MISSING', '', '')); print(n, name, 'ANCHOR MISSING', e); continue
    if m == txt:
        res.append((n, name, 'NO-CHANGE', '', '')); print(n, name, 'NO CHANGE'); continue
    p = SP + 'mut/m%02d.md' % n
    open(p, 'w', encoding='utf-8').write(m)
    e = dict(os.environ, BANNED_SRC=BSRC)
    a = subprocess.run([sys.executable, '-B', '-I', 'mychk.py', p, INP], capture_output=True, text=True, env=e, cwd='/home/user/hadavin-sdk/handover/core-hardening/steps-edits/evidence-r15-runner')
    af = [l for l in a.stdout.split('\n') if l.startswith('FAIL')]
    mine = 'caught' if a.returncode != 0 and af else ('CRASH' if a.returncode != 0 else 'MISSED')
    e2 = dict(os.environ, EDITS_PATH=p, NO_NEG='1')
    b = subprocess.run([sys.executable, '-B', '-I', 'verify15.py'], capture_output=True, text=True, env=e2, cwd=MIR)
    bf = [l for l in b.stdout.split('\n') if l.startswith('FAIL')]
    v = 'caught' if b.returncode != 0 and bf else ('CRASH' if b.returncode != 0 else 'MISSED')
    res.append((n, name, mine + ' [' + (af[0][5:60] if af else '') + ']', v + ' [' + (bf[0][5:60] if bf else (b.stderr.strip().split('\n')[-1][:50] if b.returncode else '')) + ']', ''))
    print(n, name, '| mine:', res[-1][2], '| verify15:', res[-1][3], flush=True)
with open('mutations.md', 'w') as f:
    f.write('| # | mutation | my checker | verify15.py |\n|---|---|---|---|\n')
    for r in res: f.write('| %d | %s | %s | %s |\n' % r[:4])
