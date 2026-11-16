#!/usr/bin/env python3
"""Plant mutations in COPIES of EDITS.md; the own checker must exit 1 for each. Fake keys are built from parts."""
import re, subprocess, sys, os, shutil
EDITS, INPUTS, WORK, CHECKER = sys.argv[1:5]
os.makedirs(WORK, exist_ok=True)
base = open(EDITS, encoding='utf-8').read()

def sub_nth(t, old, new, n=1):
    idxs = [m.start() for m in re.finditer(re.escape(old), t)]
    assert len(idxs) >= n, 'precondition: %r found %d times' % (old[:50], len(idxs))
    i = idxs[n - 1]
    return t[:i] + new + t[i + len(old):]

def row_block(t, rid):
    a = t.index('### %s:' % rid)
    b = t.index('\n### ', a + 5) if '\n### ' in t[a + 5:] else len(t)
    return a, b

def in_row(t, rid, old, new):
    a, b = row_block(t, rid)
    seg = t[a:b]
    assert old in seg, 'precondition %s %r' % (rid, old[:40])
    return t[:a] + seg.replace(old, new, 1) + t[b:]

def dup_new(t, rid):
    a, b = row_block(t, rid)
    seg = t[a:b]
    m = re.search(r'(NEW \(exact\):\n~~~~\n.*?\n~~~~\n)', seg, re.S)
    return t[:a] + seg.replace(m.group(1), m.group(1) + m.group(1), 1) + t[b:]

def del_new(t, rid):
    a, b = row_block(t, rid)
    seg = t[a:b]
    m = re.search(r'(NEW \(exact\):\n~~~~\n.*?\n~~~~\n)', seg, re.S)
    return t[:a] + seg.replace(m.group(1), '', 1) + t[b:]

fake_aws = 'AKIA' + 'ABCDEFGH' + '12345678'
fake_sk = 'sk' + '-' + 'ant' + 'x' * 30
fake_gh = 'gh' + 'p_' + 'Z' * 36
M = []
def mut(name, fn): M.append((name, fn))
mut('01 remove HOLD label from E-04 (NEW (exact):)', lambda t: in_row(t, 'E-04', 'NEW [HOLD G1: DO NOT APPLY] (exact):', 'NEW (exact):'))
mut('02 HOLD label of E-40 loses brackets/prefix ("NEW HOLD G1 ...")', lambda t: in_row(t, 'E-40', 'NEW [HOLD G1: DO NOT APPLY] (exact):', 'NEW (exact) HOLD G1: DO NOT APPLY:'))
mut('03 HOLD word moved after prefix ("NEW (exact) [HOLD G5: ...]") E-49', lambda t: in_row(t, 'E-49', 'NEW [HOLD G5: DO NOT APPLY] (exact):', 'NEW (exact) [HOLD G5: DO NOT APPLY]:'))
mut('04 Apply row E-01 gets two NEW blocks', lambda t: dup_new(t, 'E-01'))
mut('05 Apply row E-02 loses its NEW block', lambda t: del_new(t, 'E-02'))
mut('06 changed UTC (18:19 -> 18:18, IST unchanged) one place', lambda t: sub_nth(t, '18:19 UTC = 23:49 IST', '18:18 UTC = 23:49 IST', 3))
mut('07 changed IST (23:59 -> 23:29) one place', lambda t: sub_nth(t, '18:29 UTC = 23:59 IST', '18:29 UTC = 23:29 IST', 2))
mut('08 stale count: 56 rows in total -> 57', lambda t: sub_nth(t, '56 rows in total', '57 rows in total'))
mut('09 stale count: Apply now 44 -> 45', lambda t: sub_nth(t, '**Apply now 44**', '**Apply now 45**'))
mut('10 stale count: OWNER-STEPS 37 rows -> 38', lambda t: sub_nth(t, 'OWNER-STEPS 37 rows', 'OWNER-STEPS 38 rows'))
mut('11 wrong weekday Mon 23 Nov 2026 -> Tue', lambda t: sub_nth(t, 'Mon 23 Nov 2026', 'Tue 23 Nov 2026'))
mut('12 wrong weekday Wed 18 Nov -> Thu 18 Nov', lambda t: sub_nth(t, 'Wed 18 Nov', 'Thu 18 Nov'))
mut('13 OLD block of E-03 changed by one character', lambda t: in_row(t, 'E-03', 'OLD (exact):\n~~~~\n', 'OLD (exact):\n~~~~\nX'))
mut('14 stated line of E-06 75 -> 76 in header', lambda t: sub_nth(t, '### E-06: OWNER-STEPS-realrun-v3.md, line 75,', '### E-06: OWNER-STEPS-realrun-v3.md, line 76,'))
mut('15 duplicate id: E-20 header renamed E-19', lambda t: sub_nth(t, '### E-20:', '### E-19:'))
mut('16 index table: E-20 status Apply now -> Hold', lambda t: sub_nth(t, '| E-20 | OWNER-STEPS-realrun-v3.md | 162 | Apply now', '| E-20 | OWNER-STEPS-realrun-v3.md | 162 | Hold'))
mut('17 index table: E-21 line 164 -> 165', lambda t: sub_nth(t, '| E-21 | OWNER-STEPS-realrun-v3.md | 164 |', '| E-21 | OWNER-STEPS-realrun-v3.md | 165 |'))
mut("18 overlap: E-18 OLD replaced by E-17 OLD", lambda t: _overlap(t))
def _overlap(t):
    a, b = row_block(t, 'E-17'); seg = t[a:b]
    o17 = re.search(r'OLD \(exact\):\n~~~~\n(.*?)\n~~~~', seg, re.S).group(1)
    a2, b2 = row_block(t, 'E-18'); seg2 = t[a2:b2]
    o18 = re.search(r'OLD \(exact\):\n~~~~\n(.*?)\n~~~~', seg2, re.S).group(1)
    return t[:a2] + seg2.replace(o18, o17, 1) + t[b2:]
mut('19 fake AWS-style key built from parts in an Apply NEW (E-48)', lambda t: in_row(t, 'E-48', 'NEW (exact', 'NEW (exact') if False else _insert_new(t, 'E-48', ' ' + fake_aws))
def _insert_new(t, rid, extra):
    a, b = row_block(t, rid); seg = t[a:b]
    m = re.search(r'(NEW \(exact[^\n]*\n~~~~\n)(.*?)(\n~~~~)', seg, re.S)
    seg = seg[:m.end(2)] + extra + seg[m.end(2):]
    return t[:a] + seg + t[b:]
mut('20 fake sk- key built from parts in Apply NEW E-09', lambda t: _insert_new(t, 'E-09', ' ' + fake_sk))
mut('21 fake ghp_ token built from parts in Apply NEW E-30', lambda t: _insert_new(t, 'E-30', ' ' + fake_gh))
mut('22 Hold gate letter mismatch: E-45 header G1 -> G5', lambda t: sub_nth(t, '### E-45: AGENT-SCOPE-DO-AND-DONT.md, line 23, status Hold (gate G1)', '### E-45: AGENT-SCOPE-DO-AND-DONT.md, line 23, status Hold (gate G5)'))
mut('23 a Hold NEW block deleted (12 blocks)', lambda t: _del_hold(t))
def _del_hold(t):
    a, b = row_block(t, 'E-42'); seg = t[a:b]
    m = re.search(r'(NEW \[HOLD G1: DO NOT APPLY\] \(exact\):\n~~~~\n.*?\n~~~~\n)', seg, re.S)
    return t[:a] + seg.replace(m.group(1), '', 1) + t[b:]
mut('24 Apply NEW of E-01 contains E-02 OLD text (second match later)', lambda t: _contam(t))
def _contam(t):
    a2, b2 = row_block(t, 'E-02'); o2 = re.search(r'OLD \(exact\):\n~~~~\n(.*?)\n~~~~', t[a2:b2], re.S).group(1)
    return _insert_new(t, 'E-01', ' ' + o2)
mut('25 wrong year: Mon 16 Nov 2026 -> Mon 16 Nov 2025', lambda t: sub_nth(t, 'Mon 16 Nov 2026', 'Mon 16 Nov 2025'))
mut('26 impossible ISO date 2026-11-23 -> 2026-11-31', lambda t: sub_nth(t, '2026-11-23', '2026-11-31'))
mut('27 Apply row status flipped to Hold in header only (E-19)', lambda t: sub_nth(t, '### E-19: OWNER-STEPS-realrun-v3.md, line 159, status Apply now', '### E-19: OWNER-STEPS-realrun-v3.md, line 159, status Hold (gate G1)'))
mut('28 stale type count: UNCLEAR WORD 10 -> 11', lambda t: sub_nth(t, 'UNCLEAR WORD 10', 'UNCLEAR WORD 11'))
mut('29 E-13 second OLD removed', lambda t: _del_old2(t))
def _del_old2(t):
    a, b = row_block(t, 'E-13'); seg = t[a:b]
    m = re.search(r'(OLD 2 \(exact\):\n~~~~\n.*?\n~~~~\n)', seg, re.S)
    return t[:a] + seg.replace(m.group(1), '', 1) + t[b:]
mut('30 ordering: a Hold row (E-53) status label word "Hold" -> "Held"', lambda t: sub_nth(t, '### E-53: AGENT-SCOPE-DO-AND-DONT.md, line 28, status Hold', '### E-53: AGENT-SCOPE-DO-AND-DONT.md, line 28, status Held'))
res = []
r0 = subprocess.run([sys.executable, '-I', CHECKER, EDITS, INPUTS, WORK + '/s0', '--quiet'], capture_output=True, text=True)
print('baseline exit', r0.returncode, r0.stdout.strip().splitlines()[-1])
caught = 0
for i, (name, fn) in enumerate(M, 1):
    try:
        mt = fn(base)
    except Exception as e:
        print('PLANT-ERROR', name, e); continue
    assert mt != base, 'mutation produced no change: ' + name
    p = '%s/mut%02d.md' % (WORK, i)
    open(p, 'w', encoding='utf-8').write(mt)
    r = subprocess.run([sys.executable, '-I', CHECKER, p, INPUTS, WORK + '/s%02d' % i, '--quiet'], capture_output=True, text=True)
    fl = [l for l in r.stdout.splitlines() if l.startswith('FAIL')]
    ok = r.returncode == 1 and bool(fl)
    caught += ok
    print('%s | %s | exit %d | first: %s' % ('CAUGHT' if ok else 'MISSED', name, r.returncode, (fl[0][:110] if fl else '-')))
print('mutations planted %d, caught %d, missed %d' % (len(M), caught, len(M) - caught))
