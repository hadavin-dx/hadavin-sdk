"""gap-proof-v33.py (round 5): shows the evidence-run gap. It applies the evidence run's content mutations (H04 to H38) one by one to a scratch copy of the v32 SOURCE,
rebuilds and runs check-v32.py (the v32 checker). A mutation that adds no new FAIL line is a gap of v32 (C01 passes because the pages are rebuilt from the mutated source).
Then the same mutation is applied to the v33 SOURCE and check-v33.py is run: it must print a new FAIL line. Prints counts only. Usage: python3 -B gap-proof-v33.py"""
import os, re, shutil, subprocess, sys, tempfile, ast
H = os.path.dirname(os.path.abspath(__file__)) + '/'
def banned_path():
    r = H
    while not os.path.exists(r + 'tests/test_no_reference_material.py'): r = os.path.dirname(r.rstrip('/')) + '/'
    return r + 'tests/test_no_reference_material.py'
BP = banned_path()
def files(v, ln, ol):
    return ['facts-%s.py' % v, 'build-%s.py' % v, 'check-%s.py' % v, 'newchecks-%s.py' % v, 'OWNER-SHEET-%s-SOURCE.md' % v, 'LEAD-RELEASE-NOTE-%s-SOURCE.md' % ln, '%s-OPEN-FOR-LEAD-SOURCE.md' % v, '%s-CHANGES.md' % v, 'pointers-%s.txt' % v, 'headings-%s.txt' % v, 'factuse-%s.txt' % v]
def run(d, v):
    rb = subprocess.run([sys.executable, '-B', d + 'build-%s.py' % v, d], capture_output=True, text=True)
    if rb.returncode: return None
    r = subprocess.run([sys.executable, '-B', d + 'check-%s.py' % v], capture_output=True, text=True, env=dict(os.environ, V27_DIR=d, V31_BANNED_TEST=BP))
    return set(re.sub(r'\d+ words', 'N words', l) for l in r.stdout.split('\n') if l.startswith('FAIL'))
# (id, old, new): the same eleven sentences as plants AA01 to AA13 of mut33.py
M = [('H04', 'until about {{bt_end}} if it starts', 'until about 18:21 UTC = 23:51 IST if it starts'), ('H05', 'both after the deadline (the two cases of the yes)', 'both before the deadline (the two cases of the yes)'),
 ('H07', 'Any other key, even one the owner mistyped the name of: touch nothing, write down its name', 'Any other key, even one the owner mistyped the name of: cancel it, write down its name'),
 ('H14', 'never by a tool, script, window or person', 'or by a tool, script, window or person'), ('H17', 'Right after `exit 0`, copy one harmless word such as `clear` (it replaces the clipboard).', ''),
 ('H18', 'Paste once (Ctrl+Shift+V', 'Paste as often as you like (Ctrl+Shift+V'), ('H19', 'starts `-rw-------`', 'starts `-rw-r--r--`'),
 ('H20', 'time or key state is never tolerated.', 'time or key state is tolerated.'), ('H23', "then cancel the older key by the card's L2, steps 2 to 4, only if its name and creation date equal the blanks", "then cancel the older key by the card's L2, steps 2 to 4"),
 ('H35', 'if key text appears, close it and tell the owner it appeared', 'if key text appears, keep it and tell the owner it appeared'), ('H38', 'even if a run was in progress (no run is planned on that day)', 'unless a run was in progress (no run is planned on that day)')]
def trial(v, ln, tmp):
    base = tmp + '/' + v + '/'; os.mkdir(base)
    for f in files(v, ln, None):
        if os.path.exists(H + f): shutil.copy(H + f, base + f)
    b0 = run(base, v); res = {}
    for i, o, n in M:
        d = tmp + '/%s-%s/' % (v, i); shutil.copytree(base, d); f = d + 'OWNER-SHEET-%s-SOURCE.md' % v
        s = open(f, encoding='utf-8').read()
        if o not in s: res[i] = 'anchor absent'; continue
        open(f, 'w', encoding='utf-8').write(s.replace(o, n, 1)); got = run(d, v)
        res[i] = 'build stopped' if got is None else ('caught (%d new FAIL line(s))' % len(got - b0) if got - b0 else 'NOT caught (no new FAIL line)')
    return res, len(b0)
tmp = tempfile.mkdtemp()
r32, b32 = trial('v32', 'v16', tmp); r33, b33 = trial('v33', 'v17', tmp)
print('baseline FAIL lines: v32 %d, v33 %d (v33 baseline counts only what is not yet written when this runs)' % (b32, b33))
for i, _, _ in M: print('%s  v32 checker: %-34s v33 checker: %s' % (i, r32[i], r33[i]))
print('v32 checker misses %d of %d; v33 checker misses %d of %d' % (sum(1 for x in r32.values() if x.startswith('NOT')), len(M), sum(1 for x in r33.values() if not x.startswith('caught')), len(M)))
shutil.rmtree(tmp)
