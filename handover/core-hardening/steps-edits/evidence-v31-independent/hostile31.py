"""hostile31.py: plants hostile mutations on scratch copies, runs check-v31.py and my own indep31.py, records who catches what.
Usage: python3 -B -I hostile31.py <base folder (copy of the v31 files)> <scratch folder> .
mode 'src'  = edit a source or facts file, rebuild with build-v31.py (so the built pages differ in the meant way), then run both checkers
mode 'page' = edit a BUILT page only (no rebuild); check-v31 C01 compares built pages with the rebuild, so C01 alone catches every page edit: the codes beyond C01 are also listed
A catch = a FAIL/FINDING line that the unmodified copy does not print. Banned and key-shaped strings are built or read at run time; never printed."""
import os, re, sys, shutil, subprocess, ast, importlib.util
BASE = sys.argv[1].rstrip('/') + '/'; SCR = sys.argv[2].rstrip('/') + '/'
HERE = os.path.dirname(os.path.abspath(__file__)) + '/'
TESTFILE = '/home/user/hadavin-sdk/tests/test_no_reference_material.py'
def banned():
    t = ast.parse(open(TESTFILE, encoding='utf-8').read())
    for n in ast.walk(t):
        if isinstance(n, ast.Assign) and any(getattr(x, 'id', '') == 'BANNED' for x in n.targets): return [e.value for e in n.value.elts][0]
BAN = banned()
sp = importlib.util.spec_from_file_location('indep31', HERE + 'indep31.py'); ind = importlib.util.module_from_spec(sp); sp.loader.exec_module(ind)
SK1 = 'sk' + '-ant' + '-api03' + '-' + 'Ab12' * 6
SK2 = 'sk' + '-proj' + '-' + 'a1b2c3d4' + '-' + 'e5f6g7h8' + '-' + 'i9j0k1l2'
MAIL = 'jane' + '.doe' + '@' + 'gmail' + '.com'
AWS = 'AKIA' + 'ZZZZ' + 'YYYY' + 'XXXX' + 'WWWW'
SHEET = 'OWNER-SHEET-v31-SOURCE.md'; NOTE = 'LEAD-RELEASE-NOTE-v15-SOURCE.md'; OPEN = 'v31-OPEN-FOR-LEAD-SOURCE.md'; FACTS = 'facts-v31.py'
def fresh(name):
    d = SCR + name + '/'
    shutil.rmtree(d, ignore_errors=True); shutil.copytree(BASE, d); return d
def runcheck(d, rebuild):
    if rebuild:
        rb = subprocess.run([sys.executable, '-B', '-I', d + 'build-v31.py', d], capture_output=True, text=True)
        if rb.returncode: return 'BUILD-STOPPED', set(), ['build stopped: ' + (rb.stderr.strip().split('\n') or [''])[-1][:90]]
    r = subprocess.run([sys.executable, '-B', '-I', d + 'check-v31.py'], capture_output=True, text=True, env=dict(os.environ, V27_DIR=d, V31_BANNED_TEST=TESTFILE))
    return ('rc%d' % r.returncode), set(l for l in r.stdout.split('\n') if l.startswith('FAIL')), []
base_state, base_fail, _ = runcheck(BASE, False)
base_ind = set(ind.check(BASE))
print('baseline: check-v31 FAIL lines %d (all C19 in v31-CHANGES.md at this snapshot); indep31 findings %d' % (len(base_fail), len(base_ind)))
def code(l): return l.split()[1]
# (id, mode, file, old, new, count (0 = all), description)
W = lambda s: ' '.join(['word'] * s)
M = [
 ('H01', 'src', FACTS, 'DEADLINE = dt.datetime(2026, 11, 23, 18, 29)', 'DEADLINE = dt.datetime(2026, 11, 23, 18, 39)', 1, 'deadline moved 10 minutes in the facts'),
 ('H02', 'src', FACTS, "'postby': 'Wed 25 Nov 2026 15:00 UTC = 20:30 IST'", "'postby': 'Wed 25 Nov 2026 15:00 UTC = 20:00 IST'", 1, 'post-by IST wrong'),
 ('H03', 'src', FACTS, 'IST = dt.timedelta(hours=5, minutes=30)', 'IST = dt.timedelta(hours=5, minutes=0)', 1, 'IST offset 5:00 for every computed pair'),
 ('H04', 'src', SHEET, '{{ek}}', '10:30 UTC = 15:30 IST', 1, 'one IST time swapped (earliest key time) in the sheet source'),
 ('H05', 'src', SHEET, '{{rv23}}', '18:29 UTC = 23:59 IST', 1, 'revoke time 18:19 changed to 18:29 (both halves consistent) in the sheet'),
 ('H06', 'src', SHEET, 'alarm 3 at the cancel-by time, ', '', 0, 'the cancel-by alarm step deleted from both sheets'),
 ('H07', 'src', SHEET, '168 hours (7 days)', 'any time', 0, 'the 7-day rule dropped (wording)'),
 ('H08', 'src', SHEET, 'if used less than 7 days ago take B', 'if used long ago take B', 1, 'the "less than 7 days ago take B" sentence changed'),
 ('H09', 'src', NOTE, ' (warning beside it: A will probably fail on Wed 18 Nov (the facts file puts the key\'s last use at 11 to 13 Nov)', '', 1, 'the warning beside default A removed (lead note)'),
 ('H10', 'src', SHEET, 'Dated Mon 16 Nov 2026', 'Dated Mon 16 Nov 2026 key ' + SK1, 1, 'anthropic-style key built from parts, in the sheet'),
 ('H11', 'src', SHEET, 'Dated Mon 16 Nov 2026', 'Dated Mon 16 Nov 2026 key ' + SK2, 1, 'hyphenated sk- style key in the sheet'),
 ('H12', 'src', SHEET, 'Dated Mon 16 Nov 2026', 'Dated Mon 16 Nov 2026 ' + AWS, 1, 'AWS-shaped key (not the allowed example) in the sheet'),
 ('H13', 'src', SHEET, '{{dl_day}}', 'Tue 23 Nov 2026', 1, 'wrong weekday on deadline day'),
 ('H14', 'src', SHEET, '{{day}}', 'Thu 18 Nov 2026', 1, 'wrong weekday on run day'),
 ('H15', 'src', FACTS, "'postby': 'Wed 25 Nov 2026 15:00 UTC = 20:30 IST'", "'postby': 'Fri 25 Nov 2026 15:00 UTC = 20:30 IST'", 1, 'post-by day Fri 25 Nov'),
 ('H16', 'src', SHEET, 'Dated Mon 16 Nov 2026', 'Dated Mon 16 Nov 2026. See ' + BAN, 1, 'banned string added to the sheet (string never printed)'),
 ('H17', 'src', SHEET, 'Dated Mon 16 Nov 2026', 'Dated Mon 16 Nov 2026. Write to ' + MAIL, 1, 'real-shaped email address in the sheet'),
 ('H18', 'src', SHEET, 'Dated Mon 16 Nov 2026', 'Dated Mon 16 Nov 2026. File at /home/user/hadavin-sdk/handover/x.md', 1, 'absolute path in the sheet'),
 ('H19', 'src', SHEET, 'Dated Mon 16 Nov 2026', 'Dated Mon 16 Nov 2026 (see Q27)', 1, 'internal code Q27 in the owner sheet'),
 ('H20', 'src', SHEET, 'Dated Mon 16 Nov 2026', 'Dated Mon 16 Nov 2026 (ORD: L-23NOV)', 1, 'internal code ORD: in the owner sheet'),
 ('H21', 'src', SHEET, 'Dated Mon 16 Nov 2026', 'Dated Mon 16 Nov 2026 (DEC: 7)', 1, 'internal code DEC: in the owner sheet'),
 ('H22', 'src', SHEET, '## 1. What happens, and the words\n', '## 1. What happens, and the words\n' + W(130) + '\n', 1, 'sheet padded by 130 words (over the 6,300 cap)'),
 ('H23', 'src', SHEET, 'Four phone alarms', 'Three phone alarms', 1, 'alarm count changed'),
 ('H24', 'src', SHEET, 'Sheet B cancels the older key at 7.11 even if it was used a day ago. ', '', 1, 'sentence on sheet B older-key cancel removed'),
 ('H25', 'src', SHEET, 'The lead sends the numbers message for one letter only', 'The lead sends the numbers message', 1, 'one-letter rule shortened'),
 ('H26', 'src', NOTE, 'Mon 23 Nov 2026', 'Mon 23 Nov 2026 (the lead sends the owner the words "cancel the older key now")', 1, 'lead page: lead message releases the older-key cancel'),
 ('H27', 'src', NOTE, '{{ls23}}', '18:04 UTC = 23:44 IST', 1, 'lead note: wrong IST for 18:04'),
 ('H28', 'src', FACTS, "NEED_S = 860", "NEED_S = 900", 1, 'start margin 860 s changed to 900'),
 ('H29', 'src', FACTS, 'TOK_IN, TOK_OUT, P_IN_C, P_OUT_C, CEIL = 40000, 10000, 300, 1500, 3', 'TOK_IN, TOK_OUT, P_IN_C, P_OUT_C, CEIL = 50000, 10000, 300, 1500, 3', 1, 'input tokens changed (price per call)'),
 ('H30', 'src', SHEET, '{{ph_cf}}', 'failed', 0, 'the word "cancel failed" replaced everywhere'),
 ('H31', 'src', SHEET, '{{ph_mkc}}', 'done', 0, 'the word "model key cancelled" replaced everywhere'),
 ('H32', 'src', FACTS, "'last': pair(LAST, True)", "'last': pair(LAST, False)", 1, 'seconds dropped from the last-start pair'),
 ('H33', 'src', FACTS, 'SEVENBACK = EK - dt.timedelta(hours=168)', 'SEVENBACK = EK - dt.timedelta(hours=160)', 1, '7-day date computed with 160 hours'),
 ('H34', 'src', SHEET, '168 hours (7 days)', '120 hours (5 days)', 0, '7-day rule changed to 5 days'),
 ('H35', 'src', SHEET, 'if used less than 7 days ago take B', 'if used less than 7 days ago take A', 1, 'rule inverted (take A)'),
 ('H36', 'src', SHEET, 'W9 ', 'W8 ', 0, 'danger sign W9 label renamed W8'),
 ('H37', 'src', SHEET, 'L5 ', 'L4 ', 0, 'cancel-list label L5 renamed L4'),
 ('H38', 'src', SHEET, '## 6. The model key (R1 applies; UNVERIFIED)', '## 6. The model key (R1 applies)', 1, 'UNVERIFIED label removed from section 6 heading'),
 ('H39', 'src', SHEET, '## 9. Posting (by {{postby}})', '## 9. Posting (by Wed 25 Nov 2026 15:00 UTC)', 1, 'IST half dropped from post-by in heading'),
 ('H40', 'src', SHEET, '{{price}}', '0.28', 1, 'price per call changed to 0.28 in one place of the sheet'),
 ('H41', 'src', NOTE, 'Money-safe default if you do not choose: A', 'Default if you do not choose: A', 1, 'lead note: "Money-safe" removed from the default A sentence'),
 ('H42', 'src', SHEET, 'Dated Mon 16 Nov 2026', 'Dated Mon 16 Dec 2026', 1, 'sheet date Mon 16 Dec 2026 (a Wednesday)'),
 ('H43', 'src', OPEN, '{{bm}}', 'Mon 23 Nov 2026 18:09 UTC = 23:29 IST', 1, 'open list: reminder IST wrong'),
 ('H44', 'src', SHEET, '[OWNER FILLS', '[OWNER FILL', 1, 'one OWNER FILLS placeholder misspelled'),
 ('H45', 'src', SHEET, '[LEAD FILLS at re-pin', '[LEAD FILLS', 1, 'one LEAD FILLS placeholder misspelled'),
 ('H46', 'src', SHEET, '{{balance}}', '190.00', 1, 'prepaid balance 189.00 changed to 190.00 in one place'),
 ('H47', 'src', SHEET, '{{cb}}', '12:10 UTC = 17:30 IST', 1, 'cancel-by pair wrong (IST)'),
 ('H48', 'src', SHEET, '{{okb}}', '16:00 UTC = 21:00 IST', 1, 'older-key time pair wrong (IST)'),
 ('P01', 'page', 'OWNER-SHEET-v31-A.md', 'alarm 3 at the cancel-by time', 'alarm 3 at the time', 1, 'built sheet A: cancel-by alarm wording cut'),
 ('P02', 'page', 'OWNER-APPENDIX-v31-A.md', '18:19 UTC = 23:49 IST', '18:29 UTC = 23:59 IST', 1, 'built appendix A: 18:19 changed to 18:29 (pair stays consistent)'),
 ('P03', 'page', 'OWNER-APPENDIX-v31-A.md', '18:29 UTC = 23:59 IST', '18:29 UTC = 23:39 IST', 1, 'built appendix A: deadline IST wrong'),
 ('P04', 'page', 'OWNER-SHEET-v31-B.md', '(appendix 7)', '(appendix 12)', 1, 'built sheet B: pointer to a non-existent appendix part'),
 ('P05', 'page', 'OWNER-FILM-PERSON-v31.md', 'Mon 23 Nov', 'Tue 23 Nov', 1, 'built film page: wrong weekday'),
 ('P06', 'page', 'OWNER-CARD-v31-B.md', 'cancel-by', 'cutoff', 1, 'built card B: one cancel-by renamed'),
 ('P07', 'page', 'OWNER-SHEET-v31-A.md', '168 hours (7 days)', '168 hours', 1, 'built sheet A: "(7 days)" dropped'),
 ('P08', 'page', 'OWNER-SHEET-v31-A.md', 'Mon 23 Nov 2026', 'Tue 23 Nov 2026', 1, 'built sheet A: wrong weekday'),
 ('P09', 'page', 'LEAD-RELEASE-NOTE-v15.md', ' (warning beside it: A will probably fail on Wed 18 Nov', ' (A will probably fail on Wed 18 Nov', 1, 'built lead note: the "warning beside it" label removed (warning text stays)'),
 ('P10', 'page', 'OWNER-SHEET-v31-A.md', 'Dated Mon 16 Nov 2026', 'Dated Mon 16 Nov 2026 ' + SK1, 1, 'built sheet A: secret-shaped string'),
 ('P11', 'page', 'OWNER-CARD-v31-A.md', 'cancel failed', 'cancel did not work', 1, 'built card A: a "cancel failed" word changed'),
 ('P12', 'page', 'OWNER-SHEET-v31-B.md', 'before Wed 11 Nov 2026 10:30 UTC = 16:00 IST', 'before Thu 12 Nov 2026 10:30 UTC = 16:00 IST', 1, 'built sheet B: 7-day-back date changed (weekday right)'),
 ('P13', 'page', 'LEAD-RELEASE-NOTE-v15.md', '14.33', '14.03', 1, 'built lead note: 14.33 minutes changed'),
 ('H54', 'src', NOTE, 'Mon 23 Nov 2026', 'Mon 23 Nov 2026 (the lead sends you "cancel the older key" and you cancel it)', 1, 'v30 miss H06 variant 1: lead message releases older-key cancel'),
 ('H55', 'src', NOTE, 'Mon 23 Nov 2026', 'Mon 23 Nov 2026 (When the lead writes "go ahead and cancel the older key", cancel it)', 1, 'v30 miss H06 variant 2'),
 ('H56', 'src', FACTS, "'gap_max': str(GAP_MAX),", "'gap_max': str(GAP_MAX), 'ls_t': '11:31',", 1, 'v30 miss H15: a fact no source uses'),
 ('H57', 'src', SHEET, '[LEAD FILLS at re-pin: last-resort step', '[LEAD FILLS: last-resort step', 1, 'v30 miss H09 exact: one LEAD FILLS spelling'),
 ('H49', 'src', SHEET, '{{bs}}', 'Sun 22 Nov 2026 18:09 UTC = 23:49 IST', 1, 'Sunday reminder IST wrong'),
 ('H50', 'src', SHEET, '{{fp}}', '12', 1, 'longest film pause 10 changed to 12 in one place'),
 ('H51', 'src', SHEET, '{{ceil}}', '4', 1, 'call ceiling 3 changed to 4 in one place'),
 ('H52', 'src', SHEET, '{{ph_tp}}', 'late', 1, 'one "time passed" word changed'),
 ('H53', 'src', SHEET, '{{rl}}', '12', 1, 'run length 15 changed to 12 in one place'),
]
rows = []
ONLY = os.environ.get('ONLY'); ONLY = set(ONLY.split(',')) if ONLY else None
for mid, mode, f, old, new, cnt, what in M:
    if ONLY and mid not in ONLY: continue
    d = fresh(mid)
    p = d + f
    t = open(p, encoding='utf-8').read()
    if old not in t:
        rows.append((mid, 'ANCHOR-NOT-FOUND', '-', '-', what)); print(mid, 'ANCHOR NOT FOUND', f, '|', what); shutil.rmtree(d, ignore_errors=True); continue
    t = t.replace(old, new) if cnt == 0 else t.replace(old, new, cnt)
    open(p, 'w', encoding='utf-8').write(t)
    st, fl, stopped = runcheck(d, mode == 'src')
    newfl = {l for l in fl if l not in base_fail}
    codes_c = sorted({code(l) for l in newfl}) + (['BUILD'] if stopped else [])
    fi = {l for l in ind.check(d)} - base_ind
    codes_i = sorted({code(l) for l in fi})
    c_catch = bool(newfl or stopped); i_catch = bool(fi) or bool(stopped)
    rows.append((mid, mode, ','.join(codes_c) or '-', ','.join(codes_i) or '-', what, c_catch, i_catch))
    print('%s %-4s check-v31=%s [%s] | indep31=%s [%s] | %s' % (mid, mode, 'CAUGHT' if c_catch else 'MISSED', ','.join(codes_c[:6]) or '-', 'CAUGHT' if i_catch else 'MISSED', ','.join(codes_i[:6]) or '-', what), flush=True)
    shutil.rmtree(d, ignore_errors=True)
ok = [r for r in rows if len(r) == 7]
print('SUMMARY total %d, anchor-not-found %d' % (len(rows), len(rows) - len(ok)))
for md in ('src', 'page'):
    s = [r for r in ok if r[1] == md]
    print('mode %s: %d mutations; check-v31 caught %d; indep31 caught %d; both missed %d; only check-v31 %d; only indep31 %d' % (md, len(s), sum(r[5] for r in s), sum(r[6] for r in s), sum((not r[5]) and (not r[6]) for r in s), sum(r[5] and not r[6] for r in s), sum(r[6] and not r[5] for r in s)))
    if md == 'page': print('   page mode, check-v31 caught by a code other than C01 (and C19): %d of %d' % (sum(1 for r in s if set(r[2].split(',')) - {'C01', 'C19', '-'}), len(s)))
print('NEITHER catches: ' + (', '.join('%s (%s)' % (r[0], r[4]) for r in ok if not r[5] and not r[6]) or 'none'))
print('check-v31 misses: ' + (', '.join(r[0] for r in ok if not r[5]) or 'none'))
print('indep31 misses: ' + (', '.join(r[0] for r in ok if not r[6]) or 'none'))
