"""mut-i.py: plants mutations in COPIES of the v28 files and runs the evidence runner's own checker chk28i.py on each copy.
CAUGHT = the checker prints a FAIL line that the unmutated copy does not print AND that line carries the expected code.
Usage: python3 -I mut-i.py <original folder> <scratch folder> <chk28i.py>"""
import os, shutil, subprocess, sys
O, W, CK = sys.argv[1].rstrip('/') + '/', sys.argv[2].rstrip('/') + '/', sys.argv[3]
FILES = ['OWNER-SHEET-v28-A.md', 'OWNER-CARD-v28-A.md', 'OWNER-NUMBERS-v28-A.md', 'OWNER-SHEET-v28-B.md', 'OWNER-CARD-v28-B.md', 'OWNER-NUMBERS-v28-B.md',
         'OWNER-FILM-v28.md', 'LEAD-RELEASE-NOTE-v12.md', 'v28-OPEN-FOR-LEAD.md']
SA, SB, CA, CB, NA, NB, FM, LN, OL = FILES[0], FILES[3], FILES[1], FILES[4], FILES[2], FILES[5], FILES[6], FILES[7], FILES[8]
EXTRA = ['OWNER-SHEET-v16.md', 'v28-CHANGES.md', 'build-v28.py', 'check-v28.py', 'facts-v28.py', 'newchecks-v28.py', 'mut28.py', 'pointers-v28.txt', 'OWNER-SHEET-v28-SOURCE.md', 'LEAD-RELEASE-NOTE-v12-SOURCE.md', 'v28-OPEN-FOR-LEAD-SOURCE.md']
# secrets are built from parts here so this file holds no literal key
FAKE_ANT = 'sk-' + 'ant-' + 'api03-' + 'Zq7' * 12
FAKE_AKIA = 'AK' + 'IA' + 'QWERTY' + '1234567890'
FAKE_LONG = 'Ab3' * 14
MUT = [  # id, file, old, new, expected code, what
 ('M01', NA, '11:30 UTC = 17:00 IST', '11:30 UTC = 17:30 IST', 'K02', 'changed IST of latest start'),
 ('M02', SB, '18:29 UTC = 23:59 IST', '18:29 UTC = 23:29 IST', 'K02', 'changed IST of deadline'),
 ('M03', LN, '18:09:00 UTC = 23:39 IST', '18:09:00 UTC = 23:49 IST', 'K02', 'changed IST in the lead note'),
 ('M04', NB, 'Cancel-by time: 12:10 UTC = 17:40 IST', 'Cancel-by time: 12:20 UTC = 17:40 IST', 'K02', 'changed UTC of cancel-by'),
 ('M05', NA, 'Wed 18 Nov 2026', 'Tue 18 Nov 2026', 'K03', 'wrong weekday of run day'),
 ('M06', SA, 'Mon 23 Nov 2026', 'Sun 23 Nov 2026', 'K03', 'wrong weekday of deadline'),
 ('M07', FM, 'Wed 25 Nov 2026', 'Thu 25 Nov 2026', 'K03', 'wrong weekday of post-by'),
 ('M08', SB, 'Wed Nov 18', 'Thu Nov 18', 'K03', 'wrong weekday in date -u form'),
 ('M09', OL, '18:19 UTC = 23:49 IST agrees', '18:20 UTC = 23:50 IST agrees', 'K04', '18:19 changed where revoke-by time is stated'),
 ('M10', OL, '18:19 UTC = 23:49 IST agrees', '18:19 UTC = 23:59 IST agrees', 'K04', '18:19 paired with a wrong IST'),
 ('M11', OL, '18:19 UTC = 23:49 IST agrees', 'agrees', 'K04', '18:19 pair removed from the revoke-by line'),
 ('M12', LN, '\n', '\nStart by 18:04 UTC = 23:34 IST here.\n', 'K04', '18:04 time listed with no source'),
 ('M13', NB, '[OWNER FILLS: button words', '[button words', 'K05', 'placeholder label removed'),
 ('M14', SA, 'Dated Mon 16 Nov 2026.', 'Dated Mon 16 Nov 2026. [older key last-used time]', 'K05', 'unlabelled bracket placeholder'),
 ('M15', CB, 'If it fails.', 'TBD If it fails.', 'K05', 'TBD left in a page'),
 ('M16', FM, 'Same words as the sheet.', 'Same words as the sheet. Name: ________', 'K05', 'blank line outside the card'),
 ('M17', NA, 'SAMPLE (made-up values, never real):', 'VALUES:', 'K05', 'sample no longer labelled made-up'),
 ('M18', SA, 'OWNER-NUMBERS-v28-A.md', 'OWNER-NUMBERS-v28-Z.md', 'K07', 'broken link'),
 ('M19', SA, 'OWNER-CARD-v28-A.md', 'OWNER-CARD-v28-B.md', 'K07', 'sheet A points to card B'),
 ('M20', LN, 'v28-CHANGES.md', 'v28-CHANGEZ.md', 'K07', 'broken link in the open list'),
 ('M21', SA, 'look key of 5.9', 'look key of 5.19', 'K07', 'step reference to a step that does not exist'),
 ('M22', SB, '## 9. Posting', 'See section 4.\n## 9. Posting', 'K07', 'reference to a section that does not exist'),
 ('M23', SA, 'WORDS', ' ' + 'extra ' * 400, 'K01', 'sheet A over 6,300 words (400 words appended)'),
 ('M24', SB, 'People:', 'Persons:', 'K08', 'B differs from A outside the older-key parts'),
 ('M25', CB, 'Not danger signs', 'Safe signs', 'K08', 'B card differs from A card outside older-key parts'),
 ('M26', SA, 'Dated Mon 16 Nov 2026.', 'Dated Mon 16 Nov 2026. At the end the test program deletes the three contacts.', 'K09', 'deletion sentence (sheet)'),
 ('M27', NA, 'Your checks, by hand', 'The take archives all contacts. Your checks, by hand', 'K09', 'archive sentence (numbers)'),
 ('M28', FM, 'Same words as the sheet.', 'Same words as the sheet. Afterwards n8n deletes the contacts.', 'K09', 'deletion sentence (film page)'),
 ('M29', LN, '\n', '\nThe take deletes the made-up contacts when it ends.\n', 'K09', 'deletion sentence (lead note)'),
 ('M30', SA, 'Dated Mon 16 Nov 2026.', 'Dated Mon 16 Nov 2026. Also revoke the GitHub token.', 'K09', 'a fourth credential (token)'),
 ('M31', SB, 'Dated Mon 16 Nov 2026.', 'Dated Mon 16 Nov 2026. Also send the lead your n8n API key.', 'K09', 'a fourth credential (n8n API key)'),
 ('M32', CA, 'If it fails.', 'If it fails. Key: ' + FAKE_ANT, 'K09', 'fake model key built from parts'),
 ('M33', NA, 'Your checks, by hand', 'Key ' + FAKE_AKIA + '. Your checks, by hand', 'K09', 'fake AKIA-style key built from parts'),
 ('M34', FM, 'Same words as the sheet.', 'Same words as the sheet. ' + FAKE_LONG, 'K09', 'long random-looking text'),
 ('M35', SA, 'Dated Mon 16 Nov 2026.', 'Dated Mon 16 Nov 2026. Paste the model key into n8n at 6.4.', 'K09', 'model key typed into n8n'),
 ('M36', FM, 'Same words as the sheet.', 'Same words as the sheet. Send it to anna.k@gmail.com.', 'K09', 'real-looking mail address'),
 ('M37', CA, 'If it fails.', 'If it fails (see C07).', 'K06', 'internal check id in owner text'),
 ('M38', SB, 'Dated Mon 16 Nov 2026.', 'Dated Mon 16 Nov 2026. Rule R12 applies.', 'K06', 'undefined rule id R12'),
 ('M39', FM, 'Same words as the sheet.', 'Same words as the sheet. Run check-v28.py first.', 'K06', 'internal tool name in owner text'),
 ('M40', NA, 'Alarm time: 12:00 UTC = 17:30 IST', 'Alarm time: 12:05 UTC = 17:35 IST', 'K04', 'schedule arithmetic: alarm time wrong but pair correct'),
 ('M41', SA, 'Dated Mon 16 Nov 2026.', 'Dated Mon 16 Nov 2026. Be ready by 14:00 UTC.', 'K02', 'UTC time with no IST in owner text'),
 ('M42', NA, 'USD 0.27', 'USD 0.28', 'K10', 'price per call changed'),
]
def run(d):
    r = subprocess.run([sys.executable, '-I', '-B', CK, d], capture_output=True, text=True)
    return r.returncode, [l for l in r.stdout.split('\n') if l.startswith('FAIL')], r.stderr[-200:]
def fresh(tag):
    top = W + tag + '/'
    shutil.rmtree(top, ignore_errors=True); os.makedirs(top + 'steps-edits'); os.symlink(os.path.abspath(O + '../inputs'), top + 'inputs')
    d = top + 'steps-edits/'
    for f in FILES + EXTRA: shutil.copy(O + f, d + f)
    return d
rc0, base, err0 = run(fresh('base'))
print('baseline unmutated copy: exit %d, FAIL lines %d' % (rc0, len(base)))
caught = missed = noanchor = 0
for mid, f, old, new, code, what in MUT:
    d = fresh(mid)
    s = open(d + f, encoding='utf-8').read()
    if old == 'WORDS': s = s.rstrip('\n') + '\n\n' + new + '\n'
    elif old == '\n':
        i = s.index('\n', len(s) // 2); s = s[:i] + new + s[i + 1:]
    else:
        if s.count(old) < 1: print('%s ANCHOR-NOT-FOUND %s in %s' % (mid, old[:40], f)); noanchor += 1; continue
        s = s.replace(old, new, 1)
    open(d + f, 'w', encoding='utf-8').write(s)
    rc, fl, err = run(d)
    newf = [x for x in fl if x not in base]
    hit = [x for x in newf if (' %s ' % code) in x]
    st = 'CAUGHT' if (rc == 1 and hit) else 'MISSED'
    if st == 'CAUGHT': caught += 1
    else: missed += 1
    print('%s %s expected %s | %s | new FAIL lines %d: %s' % (mid, st, code, what, len(newf), (newf[0][:150] if newf else 'none') + (' || stderr ' + err if err else '')))
print('TOTAL %d plants: caught %d, missed %d, anchor-not-found %d' % (len(MUT), caught, missed, noanchor))
