"""Plants one change per copy, runs indep_check.py, records caught/missed (caught = a FAIL line not in the baseline). Usage: python3 -B -I plant.py"""
import os, shutil, subprocess, sys
H = os.path.dirname(os.path.abspath(__file__)) + '/'
W = H + 'work/'
FILES = ['OWNER-SHEET-v29-A.md', 'OWNER-CARD-v29-A.md', 'OWNER-APPENDIX-v29-A.md', 'OWNER-SHEET-v29-B.md', 'OWNER-CARD-v29-B.md', 'OWNER-APPENDIX-v29-B.md', 'OWNER-FILM-PERSON-v29.md', 'LEAD-RELEASE-NOTE-v13.md', 'v29-OPEN-FOR-LEAD.md']
def run(d):
    r = subprocess.run([sys.executable, '-B', '-I', H + 'indep_check.py', d], capture_output=True, text=True)
    return set(l for l in r.stdout.split('\n') if l.startswith('FAIL'))
base = run(W)
SA, CA, AA, SB, CB, AB, FP, NT, OP = FILES
# (id, file, old, new, count (0 = all), description)
M = [
('M01', SA, 'Dated Mon 16 Nov 2026', 'Dated Tue 16 Nov 2026', 1, 'sheet A date weekday wrong (16 Nov)'),
('M02', SA, 'by Wed 25 Nov 2026 15:00 UTC = 20:30 IST', 'by Thu 25 Nov 2026 15:00 UTC = 20:30 IST', 1, 'post-by weekday wrong'),
('M03', SA, 'by Wed 25 Nov 2026 15:00 UTC = 20:30 IST', 'by Wed 25 Nov 2026 15:00 UTC = 20:00 IST', 1, 'post-by IST wrong'),
('M04', AA, 'Mon 23 Nov 2026 18:29 UTC = 23:59 IST', 'Mon 23 Nov 2026 18:29 UTC = 23:29 IST', 1, 'money stop IST wrong'),
('M05', AA, 'Mon 23 Nov 2026 18:29 UTC = 23:59 IST', 'Tue 23 Nov 2026 18:29 UTC = 23:59 IST', 1, 'money stop weekday wrong'),
('M06', AA, 'Mon 23 Nov 2026 18:29 UTC = 23:59 IST', 'Mon 23 Nov 2026 18:30 UTC = 23:59 IST', 1, 'money stop UTC minute changed'),
('M07', AA, '10:30 UTC = 16:00 IST, latest start', '10:30 UTC, latest start', 1, 'IST dropped from a time'),
('M08', NT, 'key revoked by 18:19 UTC = 23:49 IST', 'key revoked by 18:19 UTC = 23:19 IST', 1, 'key-end IST wrong'),
('M09', NT, 'refusal limit', 'limit', 0, 'refusal-limit label removed everywhere in lead note'),
('M10', OP, 'key revoked by 18:19 UTC = 23:49 IST', 'key revoked by 18:24 UTC = 23:54 IST', 0, 'key-end time moved to 18:24 (consistent pair)'),
('M11', SA, ': if the key was used less than 7 days ago, stop and take sheet B', '', 1, 'route A condition deleted'),
('M12', SB, 'This sheet is B: if you want sheet A instead, stop and take it.', '', 1, 'route B condition deleted'),
('M13', SA, '7 days (168 hours) or more before', '1 day (24 hours) or more before', 0, '7-day rule changed in sheet A'),
('M14', CA, '7 days (168 hours) or more before', '1 day (24 hours) or more before', 0, '7-day rule changed in card A'),
('M15', SA, 'rm -- "<key file>"', 'echo "<key file>"', 1, 'key-file delete step removed (A)'),
('M16', SB, 'rm -- "<key file>"', 'echo "<key file>"', 1, 'key-file delete step removed (B)'),
('M17', CA, "except the key's own one-time display at 5.9 and 6.3 and the paste at 6.4", '', 1, 'card W7 exception deleted'),
('M18', CA, 'W9', 'X9', 0, 'card danger sign W9 renamed'),
('M19', CB, '5. Send exactly: model key cancelled (not for a look key). Only now may you do anything else.', '', 1, 'card B step 5 deleted'),
('M20', SA, 'Do not use any older sheet', 'Q21 Do not use any older sheet', 1, 'banned code Q21 leaked into sheet'),
('M21', CA, '**Not danger signs', 'L-123 **Not danger signs', 1, 'banned code L-123 leaked into card'),
('M22', AA, '## Appendix part 1', 'E-12 ## Appendix part 1', 1, 'banned code E-12 leaked into appendix'),
('M23', FP, 'You are the **film person**', 'ORD: 4 You are the **film person**', 1, 'banned ORD: leaked into film page'),
('M24', SA, '[OWNER FILLS: ...', '[OWNER FILL: ...', 1, 'placeholder misspelled (owner)'),
('M25', SA, '[LEAD FILLS at re-pin: ...', '[LEAD FILLS at repin: ...', 1, 'placeholder misspelled (lead)'),
('M26', SA, '# Owner sheet v29, sheet A:', '# Owner sheet v29, sheet B:', 1, 'heading letter wrong'),
('M27', SA, 'End of sheet A (OWNER-SHEET-v29-A.md).', 'End of sheet B (OWNER-SHEET-v29-A.md).', 1, 'footer letter wrong'),
('M28', CB, 'End of the card, sheet B.', 'End of the card, sheet A.', 1, 'card B footer letter wrong'),
('M29', SA, '\n---\nEnd of sheet A', ' ' + ' '.join(['word'] * 200) + '\n---\nEnd of sheet A', 1, '200 words added (over 6,300)'),
('M30', SA, '0.81', '0.82', 1, 'expected total changed in sheet'),
('M31', NT, '13.21', '13.31', 0, 'limit changed in lead note'),
('M32', AA, 'Wed 18 Nov 2026', 'Tue 18 Nov 2026', 1, 'run-day weekday wrong'),
('M33', SA, 'Wed 18 Nov 2026', 'Wed 19 Nov 2026', 1, 'run-day date moved, weekday kept'),
('M34', SA, 'cancel it at 6.7', 'cancel it at 7.2', 1, 'sheet A older-key cancel step number changed'),
('M35', SB, 'older key stays valid and can spend until you cancel it at 7.11', 'older key stays valid and can spend until you cancel it at 6.7', 1, 'sheet B older-key rule changed'),
('M36', NT, '860 s', '840 s', 0, 'run length changed in lead note'),
('M37', SA, '20:30 IST', '20:00 IST', 0, 'IST offset wrong on all post-by pairs in sheet A'),
('M38', NT, '23:44:40 IST', '23:44:10 IST', 0, 'refusal-limit IST seconds wrong'),
('M39', SA, 'Mon 23 Nov 2026', 'Mon 24 Nov 2026', 0, 'deadline date moved, weekday kept (sheet A)'),
('M40', FP, '# Film person page (v29)', 'Be there at 12:00 UTC.\n# Film person page (v29)', 1, 'UTC time without IST added'),
('M41', AA, 'CALL_CEILING = 3', 'CALL_CEILING = 4', 1, 'call ceiling changed in appendix'),
('M42', NT, 'Wed 25 Nov', 'Tue 25 Nov', 0, 'post-by weekday wrong in lead note'),
('M43', SA, 'sheet A', 'sheet B', 0, 'all "sheet A" words turned into "sheet B" in sheet A'),
]
log = []
caught = 0
for mid, f, old, new, cnt, desc in M:
    d = H + 'mut/' + mid + '/'
    os.makedirs(d, exist_ok=True)
    for n in FILES: shutil.copy(W + n, d + n)
    t = open(d + f, encoding='utf-8').read()
    n_in = t.count(old)
    if n_in == 0: log.append((mid, 'NOT-APPLIED', desc, 'old text not found')); shutil.rmtree(d); continue
    t = t.replace(old, new) if cnt == 0 else t.replace(old, new, cnt)
    open(d + f, 'w', encoding='utf-8').write(t)
    new_f = run(d) - base
    ok = bool(new_f); caught += ok
    log.append((mid, 'CAUGHT' if ok else 'MISSED', desc, '%s | occurrences in file %d | %s' % (f, n_in, (sorted(new_f)[0][:110] if new_f else ''))))
    shutil.rmtree(d)
shutil.rmtree(H + 'mut', ignore_errors=True)
applied = [l for l in log if l[1] != 'NOT-APPLIED']
for l in log: print(' | '.join(l))
print('baseline fail lines: %d; planted %d, applied %d, caught %d, missed %d, not applied %d' % (len(base), len(M), len(applied), caught, len(applied) - caught, len(log) - len(applied)))
