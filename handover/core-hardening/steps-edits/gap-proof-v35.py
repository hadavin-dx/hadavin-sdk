"""gap-proof-v35.py (round 5): shows the evidence-run gap. It applies the evidence run's content mutations (H04 to H38) one by one to a scratch copy of the v34 SOURCE,
rebuilds and runs check-v34.py (the v34 checker). A mutation that adds no new FAIL line is a gap of v34 (C01 passes because the pages are rebuilt from the mutated source).
Then the same mutation is applied to the v35 SOURCE and check-v35.py is run: it must print a new FAIL line. Prints counts only. Usage: python3 -B gap-proof-v35.py"""
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
# (id, old, new): the four evidence plants of review-v34-evidence.md (X03, X07, X08, X10) and the eleven earlier ones
M = [('X03', 'tops itself up when low (must be off)', 'tops itself up when low (must be on)'), ('X07', 'search the exact address, see exactly one result whose page shows it, then delete', 'search the start of the address, then delete all results'), ('X08', 'if nobody answers within 10 more minutes, do the last-resort step yourself, only in the model account', 'if nobody answers within 10 more minutes, wait'), ('X10', "Post only the video and the lead's exact sentences, after", "Post the video, the lead's exact sentences and a lease line, after"), ('H04', 'until about {{bt_end}} if it starts', 'until about 18:21 UTC = 23:51 IST if it starts'), ('H05', 'both after the deadline (the two cases of the yes)', 'both before the deadline (the two cases of the yes)'),
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
r32, b32 = trial('v34', 'v18', tmp); r34, b34 = trial('v35', 'v19', tmp)
print('baseline FAIL lines: v34 %d, v35 %d (v35 baseline counts only what is not yet written when this runs)' % (b32, b34))
for i, _, _ in M: print('%s  v34 checker: %-34s v35 checker: %s' % (i, r32[i], r34[i]))
print('v34 checker misses %d of %d; v35 checker misses %d of %d' % (sum(1 for x in r32.values() if x.startswith('NOT')), len(M), sum(1 for x in r34.values() if not x.startswith('caught')), len(M)))
shutil.rmtree(tmp)
