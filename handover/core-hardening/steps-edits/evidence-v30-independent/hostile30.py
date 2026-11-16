"""10+ hostile mutations on a temp copy; whether check-v30.py catches each. Usage: python3 -B -I hostile30.py <steps-edits folder>. Writes only in a temp folder. Banned string read at run time, never printed."""
import os, re, sys, shutil, subprocess, tempfile, ast
H = sys.argv[1].rstrip('/') + '/'
def banned():
    t = ast.parse(open('/home/user/hadavin-sdk/tests/test_no_reference_material.py', encoding='utf-8').read())
    for n in ast.walk(t):
        if isinstance(n, ast.Assign) and any(getattr(x, 'id', '') == 'BANNED' for x in n.targets): return [e.value for e in n.value.elts][0]
BAN = banned(); SECRET = 'sk' + '-ant' + '-api03' + '-' + 'A' * 14
def fresh():
    d = tempfile.mkdtemp(prefix='hostile30-') + '/'
    for f in os.listdir(H):
        if os.path.isfile(H + f): shutil.copy(H + f, d + f)
    return d
def run(d, rebuild):
    if rebuild:
        rb = subprocess.run([sys.executable, '-B', '-I', d + 'build-v30.py', d], capture_output=True, text=True)
        if rb.returncode: return 'BUILD-STOPPED', ['build stopped: ' + (rb.stderr.strip().split('\n') or [''])[-1][:100]], 1
    r = subprocess.run([sys.executable, '-B', '-I', d + 'check-v30.py'], capture_output=True, text=True, env=dict(os.environ, V27_DIR=d))
    fl = [l for l in r.stdout.split('\n') if l.startswith('FAIL')]
    return ('CAUGHT' if (r.returncode or fl) else 'MISSED'), fl, r.returncode
base_state, base_fl, base_rc = run(fresh(), False)
print('baseline (unmodified copy): rc=%d FAIL lines=%d' % (base_rc, len(base_fl)))
M = [
 ('H01', 'facts-v30.py', "DEADLINE = dt.datetime(2026, 11, 23, 18, 29)", "DEADLINE = dt.datetime(2026, 11, 23, 18, 39)", True, 'deadline moved 10 minutes in the facts file, sources rebuilt'),
 ('H02', 'OWNER-SHEET-v30-SOURCE.md', 'OWNER FILLS: cancelled word', 'OWNER FILL: cancelled word', True, 'one [OWNER FILLS: ...] placeholder misspelled'),
 ('H03', 'OWNER-SHEET-v30-SOURCE.md', '{{dl_day}} {{dl}}: after it nothing', 'Tue 23 Nov 2026 {{dl}}: after it nothing', True, 'wrong weekday for deadline day in sheet'),
 ('H04', 'OWNER-SHEET-v30-A.md', '(appendix 7)', '(appendix 11)', False, 'built sheet A pointer to non-existent appendix part (built file edited, no rebuild)'),
 ('H05', 'OWNER-SHEET-v30-SOURCE.md', 'Dated Mon 16 Nov 2026.', 'Dated Mon 16 Nov 2026. key ' + SECRET + '.', True, 'secret-shaped key (built from parts) in the sheet'),
 ('H06', 'LEAD-RELEASE-NOTE-v14-SOURCE.md', 'Mon 23 Nov 2026', 'Mon 23 Nov 2026 (the lead sends the owner the words "cancel the older key now")', True, 'lead page tells owner by message to cancel the older key'),
 ('H07', 'OWNER-APPENDIX-v30-A.md', '18:29 UTC = 23:59 IST', '18:29 UTC = 23:39 IST', False, 'built appendix A: wrong IST pair for the deadline (built file edited)'),
 ('H08', 'LEAD-RELEASE-NOTE-v14-SOURCE.md', '{{ls23}}', '18:04 UTC = 23:44 IST', True, 'lead note: wrong IST pair literal for 18:04'),
 ('H09', 'OWNER-SHEET-v30-SOURCE.md', 'LEAD FILLS at re-pin: last-resort step', 'LEAD FILLS: last-resort step', True, 'second placeholder spelling changed'),
 ('H10', 'OWNER-SHEET-v30-SOURCE.md', 'Dated Mon 16 Nov 2026.', 'Dated Mon 16 Nov 2026. See ' + BAN + '.', True, 'banned vendor string added to sheet source (string not printed)'),
 ('H11', 'OWNER-CARD-v30-B.md', None, None, False, 'built card B truncated: last 15 lines removed'),
 ('H12', 'facts-v30.py', "'postby': 'Wed 25 Nov 2026 15:00 UTC = 20:30 IST'", "'postby': 'Wed 25 Nov 2026 15:00 UTC = 20:00 IST'", True, 'post-by IST pair wrong in facts'),
 ('H13', 'LEAD-RELEASE-NOTE-v14-SOURCE.md', 'Mon 23 Nov 2026', 'Mon 23 Nov 2026 (the lead sends: waits for your message "cancel the older key now")', True, 'lead page with the exact old wording the checker knows (C188 spelling)'),
 ('H14', 'OWNER-SHEET-v30-SOURCE.md', 'Dated Mon 16 Nov 2026.', 'Dated Mon 17 Nov 2026.', True, 'sheet date changed to Mon 17 (wrong weekday)'),
 ('H15', 'facts-v30.py', "'ls_t': t(LS)", "'ls_t': '11:31'", True, 'latest-start time literal differs from computed'),
]
res = []
for mid, f, old, new, rb, what in M:
    d = fresh()
    t = open(d + f, encoding='utf-8').read()
    if mid == 'H11': t = '\n'.join(t.split('\n')[:-15]) + '\n'
    else:
        if old not in t: print(mid, 'ANCHOR NOT FOUND'); res.append((mid, 'ANCHOR-NOT-FOUND', [], what)); continue
        t = t.replace(old, new, 1)
    open(d + f, 'w', encoding='utf-8').write(t)
    st, fl, rc = run(d, rb)
    new_fl = [l for l in fl if l not in base_fl]
    codes = sorted({l.split()[1] for l in new_fl})
    res.append((mid, st, codes, what)); print('%s %s rc=%d codes=%s | %s' % (mid, st, rc, ','.join(codes) or '-', what))
    shutil.rmtree(d, ignore_errors=True)
print('SUMMARY mutations %d: caught %d, missed %d, anchor-missing %d' % (len(res), sum(r[1] in ('CAUGHT', 'BUILD-STOPPED') for r in res), sum(r[1] == 'MISSED' for r in res), sum(r[1] == 'ANCHOR-NOT-FOUND' for r in res)))
