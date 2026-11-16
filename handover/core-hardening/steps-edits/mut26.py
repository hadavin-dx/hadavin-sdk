"""Planting test (v25b) for check-v26.py: the 42 v25 plants P01-P45 plus the 54 v23 plants M01-M54 ported to the v25 sources. Each plant changes ONE thing in a scratch copy of a SOURCE (or facts) file, rebuilds, runs the checker;
CAUGHT = the checker prints a FAIL line that the unmodified package does not print. Prints caught and missed honestly."""
import os, re, shutil, subprocess, sys, tempfile
H = os.path.dirname(os.path.abspath(__file__)) + '/'
FILES = ['facts-v26.py', 'build-v26.py', 'check-v26.py', 'OWNER-SHEET-v26-SOURCE.md', 'LEAD-RELEASE-NOTE-v10-SOURCE.md', 'v26-OPEN-FOR-LEAD-SOURCE.md', 'v26-CHANGES.md', 'pointers-v26.txt', 'newchecks-v26.py']
def run(d):
    rb = subprocess.run([sys.executable, '-B', d + 'build-v26.py', d], capture_output=True, text=True)
    if rb.returncode: return {'FAIL BUILD stopped: ' + (rb.stderr.strip().split('\n') or [''])[-1][:80]}, rb       # the build's own assertions (marker left, run length below 860 s)
    r = subprocess.run([sys.executable, '-B', d + 'check-v26.py'], capture_output=True, text=True, env=dict(os.environ, V26_DIR=d))
    return set(l for l in r.stdout.split('\n') if l.startswith('FAIL')), r
# (id, file, old, new, what)
import ast
def _banned():
    t = ast.parse(open('/home/user/hadavin-sdk/tests/test_no_reference_material.py', encoding='utf-8').read())
    for n in ast.walk(t):
        if isinstance(n, ast.Assign) and any(getattr(x, 'id', '') == 'BANNED' for x in n.targets): return [e.value for e in n.value.elts][0]
BANNED_WORD = _banned()

P = [
('P01', 'facts-v26.py', 'P_OUT_C, CEIL = 40000, 10000, 300, 1500, 3', 'P_OUT_C, CEIL = 40000, 10000, 300, 1500, 4', 'call ceiling changed'),
('P02', 'facts-v26.py', 'LEDGER_C = 1240', 'LEDGER_C = 1250', 'ledger changed (limit 13.21 to 13.31)'),
('P03', 'facts-v26.py', 'NEED_S = 860', 'NEED_S = 864', '860 s changed'),
('P04', 'facts-v26.py', 'DEADLINE = dt.datetime(2026, 11, 23, 18, 29)', 'DEADLINE = dt.datetime(2026, 11, 23, 18, 30)', 'deadline minute'),
('P05', 'facts-v26.py', "IST = dt.timedelta(hours=5, minutes=30)", "IST = dt.timedelta(hours=5, minutes=0)", 'IST offset'),
('P06', 'facts-v26.py', "'dl_day': 'Mon 23 Nov 2026'", "'dl_day': 'Tue 23 Nov 2026'", 'weekday of deadline'),
('P07', 'facts-v26.py', "'postby': 'Wed 25 Nov 2026 15:00 UTC = 20:30 IST'", "'postby': 'Wed 25 Nov 2026 15:00 UTC = 20:00 IST'", 'post-by pair'),
('P09', 'OWNER-SHEET-v26-SOURCE.md', "except the key's own one-time display at 6.3 and the paste at 6.4 (a long text elsewhere counts)", '', 'card (g) exception removed'),
('P10', 'OWNER-SHEET-v26-SOURCE.md', 'switch it OFF yourself at once with the tool the numbers message names', 'say "stop" and wait', 'recording stop by voice'),
('P11', 'OWNER-SHEET-v26-SOURCE.md', 'Three phone alarms on the run day, all in IST: alarm 1 at the latest start, ', 'Two phone alarms on the run day, all in IST: ', 'first alarm removed'),
('P12', 'OWNER-SHEET-v26-SOURCE.md', 'Text between backticks is typed without the backticks. ', '', 'backtick sentence removed'),
('P13', 'OWNER-SHEET-v26-SOURCE.md', "only if the window's last line is `paste key, Enter:` (otherwise do not paste; copy a harmless word; describe the last line), ", '', 'paste condition removed'),
('P14', 'OWNER-SHEET-v26-SOURCE.md', ' with paper notes "READ" and "TEST"', '', 'window labels removed'),
('P15', 'OWNER-SHEET-v26-SOURCE.md', '(no earlier run used it or begins like it)', '(any run name will do)', 'run-name reuse rule removed'),
('P16', 'OWNER-SHEET-v26-SOURCE.md', 'only at 6.7, after 6.6 passed (new key saved, size checked)', 'at 6.4', 'A older key cancelled before the key is saved'),
('P17', 'OWNER-SHEET-v26-SOURCE.md', 'reverses `end` and the card, ', '', 'lead may reverse order'),
('P18', 'OWNER-SHEET-v26-SOURCE.md', 'within {{y}} minutes of the time `date -u` shows when the notice appeared (note that time at once)', 'within the minutes the message names', 'no clock for the notice window'),
('P19', 'OWNER-SHEET-v26-SOURCE.md', 'if 7.4 never happened, send "none" for the time in 8.1. ', '', 'run that never started'),
('P20', 'OWNER-SHEET-v26-SOURCE.md', 'SAMPLE (made-up values, never real):\n', '', 'SAMPLE label removed'),
('P21', 'OWNER-SHEET-v26-SOURCE.md', 'never use rotate or any button that shows a new secret', 'rotate the secret', 'HubSpot rotate allowed'),
('P22', 'OWNER-SHEET-v26-SOURCE.md', 'or "{{ph_nokey}}" (only if', 'or "no key made" (only if', 'set phrase differs'),
('P23', 'OWNER-SHEET-v26-SOURCE.md', 'weekday, month, day and year must equal the run day', 'month and day must equal the run day', 'full date check weakened'),
('P24', 'OWNER-SHEET-v26-SOURCE.md', 'balance and auto-reload equal your yes (R4)', 'the balance looks fine (R4)', 'balance re-check weakened'),
('P25', 'OWNER-SHEET-v26-SOURCE.md', 'last-resort step <step>. ', '', 'last-resort step out of the yes'),
('P26', 'OWNER-SHEET-v26-SOURCE.md', 'one line only: a second', 'a second', 'one-line warning removed'),
('P27', 'OWNER-SHEET-v26-SOURCE.md', 'press the cancel button; if a box asks', 'press the cancel button (or at 7.8 click cancel); if a box asks', 'card step 3 gets a new pointer'),
('P29', 'OWNER-SHEET-v26-SOURCE.md', '(8.3, 8.4)', '(8.3, 8.9)', 'pointer to missing step'),
('P30', 'OWNER-SHEET-v26-SOURCE.md', '**Key list** = the model account page', '**Key liszt** = the model account page', 'card term renamed'),
('P31', 'OWNER-SHEET-v26-SOURCE.md', 'Never "Select all", never empty Trash', 'Select all is fine', 'delete guard removed'),
('P32', 'OWNER-SHEET-v26-SOURCE.md', '**STOP RULE.**', '**RULE.**', 'STOP RULE renamed'),
('P33', 'OWNER-SHEET-v26-SOURCE.md', "`. _ / - : = @ + , '` only", "`. _ / - : = @ + , ' !` only", 'R8 character list gets a character'),
('P34', 'OWNER-SHEET-v26-SOURCE.md', 'I accept the risks of R1 and R4:', 'I accept the risks of R1 and R4; (ok):', 'yes pattern gets a bracket char'),
('P35', 'OWNER-SHEET-v26-SOURCE.md', 'echo "exit $?"', 'echo exit', 'key-save line loses exit report'),
('P36', 'OWNER-SHEET-v26-SOURCE.md', 'set -C; umask 077; read -rs', 'set -C; umask 077; read -rs; (', 'key-save line breaks bash -n'),
('P37', 'LEAD-RELEASE-NOTE-v10-SOURCE.md', 'the final check', 'the re-pin', 'stale word back in note'),
('P38', 'LEAD-RELEASE-NOTE-v10-SOURCE.md', '14.33', '14.4', 'old minutes figure in note'),
('P39', 'LEAD-RELEASE-NOTE-v10-SOURCE.md', '18:19:00 UTC = 23:49 IST', '18:19:00 UTC = 23:59 IST', 'wrong pair in note'),
('P40', 'v26-OPEN-FOR-LEAD-SOURCE.md', 'Mon 16 Nov 2026', 'Tue 16 Nov 2026', 'wrong weekday in open list'),
('P41', 'v26-OPEN-FOR-LEAD-SOURCE.md', 'the card', 'card Part 2', 'Part 2 back in open list'),
('P43', 'OWNER-SHEET-v26-SOURCE.md', 'Mon 16 Nov 2026', 'Mon 17 Nov 2026', 'sheet date weekday'),
('P44', 'OWNER-SHEET-v26-SOURCE.md', '[[A: I will cancel the older key myself', '[[A: I will cancel the older key soon', 'A yes sentence changed'),
('P45', 'OWNER-SHEET-v26-SOURCE.md', 'Until then the older key stays valid and can spend.', '', 'B older key fate removed'),
]
S, N, O, C, FA = 'OWNER-SHEET-v26-SOURCE.md', 'LEAD-RELEASE-NOTE-v10-SOURCE.md', 'v26-OPEN-FOR-LEAD-SOURCE.md', 'v26-CHANGES.md', 'facts-v26.py'
BW = BANNED_WORD
# ported from the 54 v23 plants (evidence-v23-independent/scripts/mut.py M01-M54); anchors rewritten for the v25 source; M-ids kept
M = [
('M01', S, 'Price per call at full size: USD {{price}}', 'Price per call at full size: USD 0.28', 'price line 0.27 to 0.28'),
('M02', S, 'Expected total: USD {{total}} (not a limit)', 'Expected total: USD 0.82 (not a limit)', 'expected total line 0.81 to 0.82'),
('M03', S, 'Price per call at full size: USD {{price}}', 'Price per call at full size: USD 0.28', 'sample notice price line'),
('M04', S, 'expected total USD <expected total>, balance USD', 'expected total USD 0.82, balance USD', 'yes pattern total'),
('M05', S, 'If you had typed `end`, proceed at 7.9.', 'If you had typed `end`, proceed at 7.5.', 'after-the-card pointer 7.9 to 7.5'),
('M06', S, 'back on in 8.7', 'back on in 8.5', 'pointer back on in 8.7 to 8.5'),
('M07', N, 'the HubSpot app secret revoke (G42, sheet 8.4)', 'the HubSpot app secret revoke (G42, sheet 8.3)', 'note pointer sheet 8.4 to 8.3'),
('M08', N, 'The order `end` then cancel (sheet 7.8)', 'The order `end` then cancel (sheet 7.6)', 'note pointer sheet 7.8 to 7.6'),
('M09', N, 'only the characters of owner sheet R8', 'only the characters of owner sheet R7', 'note R8 to R7'),
('M10', N, "The owner's method is owner sheet R7", "The owner's method is owner sheet R9", 'note R7 to R9'),
('M11', S, 'Dated Mon 16 Nov 2026', 'Dated Tue 16 Nov 2026', 'weekday of the sheet date'),
('M12', N, 'On Mon 23 Nov (no run is released', 'On Tue 23 Nov (no run is released', 'weekday in note'),
('M13', S, 'Cancel-by time: {{cb}}', 'Cancel-by time: 12:10 UTC = 17:50 IST', 'IST pair cancel-by in sheet'),
('M14', N, 'LF = 12:00 UTC = 17:30 IST', 'LF = 12:00 UTC = 17:00 IST', 'IST pair in note'),
('M15', O, 'alarm 12:00 UTC = 17:30 IST', 'alarm 12:00 UTC = 17:20 IST', 'IST pair in open list'),
('M16', S, '`run-<run name>`', '`run-<runname>`', 'placeholder renamed (one place)'),
('M17', S, 'older key <its name or none>', 'older key <its name or nome>', 'yes placeholder spelled differently'),
('M18', N, '(Open 2 and 31)', '(Open 2 and 91)', 'list-form pointer Open 91'),
('M19', S, 'minimise the test terminal. The film person alone', 'minimise the test terminal: if you must stop it, click Cancel beside each key and refresh the page twice to see the cancelled state. The film person alone', 'cancel rule paraphrased outside the card (6.6)'),
('M20', S, 'send "{{ph_hsr}}"', 'send "{{ph_apr}}"', 'wrong set phrase at 8.4'),
('M21', S, 'delete exactly those as R7 says', 'delete exactly those as R9 says', 'R7 to R9 in 5.4'),
('M22', S, 'The balance is at least the expected total.', 'The balance is at least the expected total plus 5.', 'check 3 changed'),
('M23', FA, 'Y, RL, FP, MG = 5, 15, 10, 10', 'Y, RL, FP, MG = 5, 15, 10, 15', 'margin changed in facts (sums)'),
('M24', S, '[[A: L2 the older key named', '[[A: [[B: leftover]] L2 the older key named', 'nested marker left'),
('M25', S, 'The balance is at least the expected total.', 'The balance is at least the expected total. [[ left', 'stray marker left'),
('M26', N, "## 9. Kept from earlier appendices (lead's own use)", "## 9. Kept from earlier appendices (lead's own use) " + BW, 'banned word in note'),
('M27', O, '| 40 | Does the take program print', '| 41 | Does the take program print', 'open list numbering gap'),
('M28', N, 'the lease wording (G12)', 'the lease wording (G32)', 'note G pointer G12 to G32'),
('M29', N, 'before it goes to the owner (Open 51)', 'before it goes to the owner (Open 15)', 'note Open 51 to 15'),
('M30', N, 'Shutdown order as in section 4', 'Shutdown order as in section 3', 'note section 4 to 3'),
('M31', FA, 'Y, RL, FP, MG = 5, 15, 10, 10', 'Y, RL, FP, MG = 5, 14, 10, 10', 'run length 15 to 14 (below 860 s)'),
('M32', FA, "'need_min': '%.2f' % (NEED_S / 60)", "'need_min': '14.4'", 'need minutes 14.33 to 14.4'),
('M33', S, '{{dl_day}} {{dl}}: after it', 'Tue 23 Nov 2026 18:29 UTC = 23:59 IST: after it', 'deadline weekday in glossary'),
('M34', S, ' A key alive: the card first. |', ' |', 'R8 loses "A key alive: the card first"'),
('M35', N, 'the HubSpot private-app page path (8.4), ', '', 'tolerated item dropped from note'),
('M36', N, '## 6. Contact list after the take', '## 6. Contact list after the take\nThe owner reloads the key list twice and sees the cancelled word each time before telling the lead.', 'cancel rule paraphrased in note'),
('M37', FA, "'limit': usd(LIMIT_C)", "'limit': '13.22'", 'program limit 13.22 in facts'),
('M38', S, 'TOKENS_OUT = {{tok_out}}', 'TOKENS_OUT = 12000', 'settings TOKENS_OUT 12000'),
('M39', S, '5. Send exactly: {{ph_mkc}}.', '5. Send exactly: model key canceled.', 'card step 5 phrase spelled differently'),
('M40', S, 'B submitted 10 times', 'B submitted 12 times', 'B submitted 12 times'),
('M41', N, '(IST = UTC + 5:30)', '(IST = UTC + 5:00)', 'IST definition in note'),
('M42', O, 'the take program needs at least 860 seconds (14.33 minutes)', 'the take program needs at least 860 seconds (14.5 minutes)', 'open list minutes figure'),
('M43', N, 'the spend lock (G33)', 'the spend lock (G38)', 'note G33 to G38'),
('M44', S, '"go" (5.8)', '"go" (5.7)', 'R8 pointer go (5.8) to 5.7'),
('M45', S, 'you read both at 6.2 and 6.7', 'you read both at 6.2 and 6.8', 'R4 pointer 6.7 to 6.8'),
('M46', S, 'after the model key\'s cancel press, card step 3)', 'after the model key\'s cancel press, card step 5)', '8.1 card step 3 to 5'),
('M47', S, '## 9. Posting (by {{postby}}', '## 9. Posting (by Wed 25 Nov 2026 15:00 UTC = 20:00 IST', 'post-by IST in sheet'),
('M48', C, 'sheet 8.2 no-key path', 'sheet 8.3 no-key path', 'CHANGES table pointer 8.2 to 8.3'),
('M49', O, "the sheet's 7.8 error sentence stays", "the sheet's 7.7 error sentence stays", 'open row pointer 7.8 to 7.7'),
('M50', N, 'gives 0.27; ceiling 3 gives expected total 0.81', 'gives 0.28; ceiling 3 gives expected total 0.81', 'note worked price'),
('M51', S, 'send "{{ph_dmd}}"', 'send "all done"', 'unlisted set phrase sent in 8.5'),
('M52', N, '(Open 2 and 31)', '(Open 2, 31 and 91)', 'Open 91 in a list form'),
('M53', N, 'expected total 0.81. Ledger total 12.40', 'expected total 0.80. Ledger total 12.40', 'expected total in note'),
('M54', S, 'Deadline {{dl_full}}.', 'Deadline 2026-11-23 18:29 UTC = 23:29 IST.', 'yes deadline IST pair'),
]

P = P + M

# the 15 plants that check-v24 missed in the independent run (own25.py Q01 Q02 Q03 Q08 Q09 Q10 Q11 Q12 Q13 Q15 Q16 Q18 Q20 Q22 Q24), anchors ported to the v25 sources
SECRET = 'sk' + '-' + 'ab12' * 10          # built from parts, never a real key
N = 'LEAD-RELEASE-NOTE-v10-SOURCE.md'
Q = [
('Q01', S, '/ 1,000,000 = {{price}}; expected total', '/ 1,000,000 = 0.28; expected total', 'wrong price per call hardcoded'),
('Q02', S, '{{ceil}} x {{price}} = {{total}}', '{{ceil}} x {{price}} = 0.84', 'wrong total hardcoded'),
('Q03', S, 'Tokens in and out per call: {{tok_in}} and {{tok_out}}', 'Tokens in and out per call: {{tok_in}} and 12,000', 'wrong output tokens in the sample'),
('Q08', S, '(1) if a key is alive, do the card now; (2) then FREEZE', '(2) then FREEZE', 'STOP RULE step 1 deleted'),
('Q09', S, 'W1 you typed `end`;', 'W1 you typed `end;', 'stray backtick in card gate W1'),
('Q10', S, 'press the cancel button; if a box asks, press the confirmation word', 'press the cancel button; if a box asks, press close', 'card cancel step changed'),
('Q11', S, 'W6 the test terminal shows a prompt before you typed `end`; ', '', 'card gate W6 deleted'),
('Q12', S, 'auto-reload off, balance at least the expected total', 'auto-reload on, balance at least the expected total', 'R4 auto-reload flipped to on'),
('Q13', S, 'Silence minutes: 3   Give-up minutes: 40', 'Silence minutes: 3   Give-up minutes: 40   Key: ' + SECRET, 'secret-shaped string (built from parts) in the sheet'),
('Q15', S, 'Give-up minutes: 40', 'Give-up minutes: 30', 'sample give-up minutes changed'),
('Q16', S, 'Silence minutes: 3', 'Silence minutes: 5', 'sample silence minutes changed'),
('Q18', S, 'and ending `@example.com`', 'and ending `@example.org`', 'one delete-domain guard changed'),
('Q20', N, 'program limit = 12.40 + 0.81 = 13.21', 'program limit = 12.40 + 0.81 = 13.12', 'lead note limit wrong'),
('Q22', S, 'Exit codes accepted: 0 only', 'Exit codes accepted: 0 or 1', 'accepted exit codes widened'),
('Q24', S, 'Only six words in a lead message', 'Only five words in a lead message', 'R8 word count changed'),
]
P = P + Q
SLASHKEY = 'q' * 8 + '/' + 'Z' * 16 + '_' + 'k' * 12 + '-' + 'm' * 9           # 47 characters with a slash, built from parts, never a real key
# plants of v26: the v25 misses (N01 N05 N10 N11 N12 N14, security M4 x4, C55 slash gap) and 21 new kinds (R01-R21): each names the check MEANT to catch it
V26 = [
('N01', S, '**IST** = UTC + 5:30', '**IST** = UTC + 4:30', 'IST offset label wrong (v25 plant N01)'),
('N05', S, 'deleted or archived, or asking', 'deleted or deleted, or asking', 'R5 archived turned into deleted (N05)'),
('N10', S, ' (else do not press Enter: do the card)', '', 'warning before the start-line step removed (N10)'),
('N11', S, '## 9. Posting (by {{postby}})', '## 9. Posting (by Thu 26 Nov 2026 15:00 UTC = 20:30 IST)', 'post-by date moved with a consistent weekday (N11)'),
('N12', S, 'You delete only made-up contacts of this run and demo mails, by hand, one by one.', 'Only made-up contacts of this run and demo mails are deleted, one by one.', 'R7 second person turned passive (N12)'),
('N14', S, 'Run `date -u` in the read terminal: the run day still holds', 'Run `date` in the read terminal: the run day still holds', 'shortened command date -u to date (N14)'),
('M4a', S, 'Prices per million: in USD {{p_in}}, out USD {{p_out}}', 'Prices per million: in USD {{p_out}}, out USD {{p_in}}', 'price line swap (security M4)'),
('M4b', S, 'Tokens in and out per call: {{tok_in}} and {{tok_out}}', 'Tokens in and out per call: {{tok_out}} and {{tok_in}}', 'tokens swap in the sample (security M4)'),
('M4c', S, 'DEADLINE = {{dl_iso}}', 'DEADLINE = 2026-11-23T18:19:00Z', 'DEADLINE line wrong (security M4)'),
('M4d', S, 'Deadline {{dl_full}}.', 'Deadline 2026-11-23 18:19 UTC = 23:49 IST.', 'yes-line deadline pair changed to another valid pair (security M4)'),
('M4e', S, 'Silence minutes: 3   Give-up minutes: 40', 'Silence minutes: 3   Give-up minutes: 40   Key: ' + SLASHKEY, 'secret-shaped text with a slash, 47 characters (C55 slash gap)'),
('R01', S, '7.11, always, by {{okb}}', '7.11, always, by 18:30 UTC = 00:00 IST', 'B older-key cancel time after 18:14 UTC'),
('R02', S, '**Older key (cannot be undone).**', '**Older key.**', 'B 7.11 title loses the irreversible warning'),
('R03', S, 'exactly the rows you wrote minus K', 'exactly N minus K', 'card proof uses N minus K again'),
('R04', S, 'otherwise only at 6.7, after 6.6 passed (new key saved, size checked)', 'otherwise at once', 'A older-key cancel before the key is saved'),
('R05', S, '`PRICE_OUT_CENTS`, `CALL_CEILING`,', '`PRICE_OUT_CENTS`,', 'one of the seven setting names dropped'),
('R06', S, 'or `prep-` and ending', 'and ending', 'R7 prep prefix dropped'),
('R07', S, 'in the read terminal must say no such file. Send the two times', 'in the read terminal must say nothing. Send the two times', '8.1 proof of the deleted key file weakened'),
('R08', S, '"restarted" (6.6), ', '', 'R8 loses the restarted word (and its count stays six)'),
('R09', S, '(a human you can call who', '(a person who', 'backup person no longer a human you can call'),
('R10', S, 'the only valid answer is their own written words "matches the sentences"', 'the answer can be a thumbs-up', 'post checker valid answer removed'),
('R11', S, '**Deadline** = the end of the period your spending approval covers', '**Deadline** = the end of the run', 'deadline definition changed'),
('R12', S, 'A differing printed count: send the counts, do not post, FREEZE.', 'A differing printed count: post anyway.', '7.10 mismatch action changed'),
('R13', S, 'remove only that profile, never your normal profile', 'remove your profiles', '8.7 profile removal widened'),
('R14', S, 'Gap before 8.1: <minutes>', '', 'sample numbers message loses the gap slot'),
('R15', S, 'the narrowest scopes that allow model calls', 'any scopes', 'create-form scopes widened'),
('R16', S, 'W9 the text of the older key appeared on your screen', 'W9 the older key was seen', 'W9 older key exposure trigger weakened'),
('R17', S, 'plugged in; sleep Never', 'plugged in', 'laptop sleep value dropped'),
('R18', S, '**FREEZE** (a key alive: the card first)', '**FREEZE**', 'FREEZE loses the card-first rule'),
('R19', S, '**Key** alone = a model key', '**Key** alone = any key', 'word key given a second meaning'),
('R20', S, 'make a Chrome profile `demo-take`', 'make a Chrome profile `demo-film`', 'profile name differs between steps'),
('R21', S, 'without a Google account (how unknown: ask the lead)', 'without a Google account', 'Chrome profile how-to and ask-the-lead removed'),
]
P = P + V26
EXPECT = {
  'M01': ['C04', 'C17', 'C48'],
  'M02': ['C04', 'C17', 'C48'],
  'M03': ['C04', 'C17', 'C48'],
  'M04': ['C04', 'C17', 'C48'],
  'M05': ['C19'],
  'M06': ['C19'],
  'M07': ['C19'],
  'M08': ['C19'],
  'M09': ['C19'],
  'M10': ['C19'],
  'M11': ['C04'],
  'M12': ['C04'],
  'M13': ['C04'],
  'M14': ['C04'],
  'M15': ['C04'],
  'M16': ['C20'],
  'M17': ['C20'],
  'M18': ['C16'],
  'M19': ['C22'],
  'M20': ['C21'],
  'M21': ['C19'],
  'M22': ['C23'],
  'M23': ['C03', 'C18'],
  'M24': ['BUILD'],
  'M25': ['BUILD'],
  'M26': ['C06'],
  'M27': ['C16'],
  'M28': ['C19'],
  'M29': ['C19'],
  'M30': ['C19'],
  'M31': ['BUILD'],
  'M32': ['C03'],
  'M33': ['C04'],
  'M34': ['C23'],
  'M35': ['C23'],
  'M36': ['C22'],
  'M37': ['C03'],
  'M38': ['C17', 'C49', 'C77'],
  'M39': ['C21'],
  'M40': ['C17', 'C23'],
  'M41': ['C17'],
  'M42': ['C17'],
  'M43': ['C19'],
  'M44': ['C19'],
  'M45': ['C11'],
  'M46': ['C19'],
  'M47': ['C04', 'C73'],
  'M48': ['C19'],
  'M49': ['C19'],
  'M50': ['C17'],
  'M51': ['C12', 'C21'],
  'M52': ['C16'],
  'M53': ['C17'],
  'M54': ['C04', 'C79'],
  'P01': ['C03', 'C04', 'C17', 'C48'],
  'P02': ['C03'],
  'P03': ['C03'],
  'P04': ['C03', 'C79'],
  'P05': ['C03', 'C04', 'C18', 'C79', 'C86'],
  'P06': ['C04'],
  'P07': ['C03', 'C04', 'C73'],
  'P09': ['C14a'],
  'P10': ['C14b'],
  'P11': ['C14c', 'C25'],
  'P12': ['C14d'],
  'P13': ['C14e'],
  'P14': ['C14f', 'C23'],
  'P15': ['C102'],
  'P16': ['C89'],
  'P17': ['C14h'],
  'P18': ['C14i'],
  'P19': ['C14j', 'C46'],
  'P20': ['C14k'],
  'P21': ['C14m', 'C44'],
  'P22': ['C21'],
  'P23': ['C14q'],
  'P24': ['C14r'],
  'P25': ['C14o'],
  'P26': ['C14p'],
  'P27': ['C52'],
  'P29': ['C11'],
  'P30': ['C10'],
  'P31': ['C14s', 'C23'],
  'P32': ['C23'],
  'P33': ['C23'],
  'P34': ['C13', 'C24'],
  'P35': ['C15'],
  'P36': ['C15'],
  'P37': ['C05'],
  'P38': ['C04', 'C17'],
  'P39': ['C04'],
  'P40': ['C04'],
  'P41': ['C05'],
  'P43': ['C04'],
  'P44': ['C08'],
  'P45': ['C27', 'C61'],
  'Q01': ['C48'],
  'Q02': ['C48'],
  'Q03': ['C49', 'C77'],
  'Q08': ['C50'],
  'Q09': ['C51'],
  'Q10': ['C52'],
  'Q11': ['C53'],
  'Q12': ['C54'],
  'Q13': ['C55'],
  'Q15': ['C56'],
  'Q16': ['C56'],
  'Q18': ['C57', 'C83'],
  'Q20': ['C58'],
  'Q22': ['C59'],
  'Q24': ['C60'],
}
EXPECT['N01'] = ['C70']
EXPECT['N05'] = ['C71']
EXPECT['N10'] = ['C72']
EXPECT['N11'] = ['C73']
EXPECT['N12'] = ['C74']
EXPECT['N14'] = ['C75']
EXPECT['M4a'] = ['C76']
EXPECT['M4b'] = ['C77']
EXPECT['M4c'] = ['C78']
EXPECT['M4d'] = ['C79']
EXPECT['M4e'] = ['C55']
EXPECT['R01'] = ['C27', 'C86']
EXPECT['R02'] = ['C88']
EXPECT['R03'] = ['C28', 'C87']
EXPECT['R04'] = ['C89']
EXPECT['R05'] = ['C81']
EXPECT['R06'] = ['C83']
EXPECT['R07'] = ['C84']
EXPECT['R08'] = ['C60', 'C85']
EXPECT['R09'] = ['C92']
EXPECT['R10'] = ['C93']
EXPECT['R11'] = ['C96']
EXPECT['R12'] = ['C94']
EXPECT['R13'] = ['C97']
EXPECT['R14'] = ['C99']
EXPECT['R15'] = ['C100']
EXPECT['R16'] = ['C28']
EXPECT['R17'] = ['C101']
EXPECT['R18'] = ['C91']
EXPECT['R19'] = ['C98']
EXPECT['R20'] = ['C103']
EXPECT['R21'] = ['C95']
def codes_of(lines): return set(re.match(r'FAIL (C\d+[a-z]?|BUILD)', l)[1] for l in lines if re.match(r'FAIL (C\d+[a-z]?|BUILD)', l))
def main():
    learn = os.environ.get('LEARN') == '1'
    tmp = tempfile.mkdtemp(); base = tmp + '/base/'; os.mkdir(base)
    for f in FILES:
        if os.path.exists(H + f): shutil.copy(H + f, base + f)
    b0, r0 = run(base); print('baseline failures: %d' % len(b0))
    cau = mis = anc = inc = 0; norm = lambda x: re.sub(r'\d+ words', 'N words', x)
    for pid, f, old, new, what in P:
        d = tmp + '/' + pid + '/'; shutil.copytree(base, d)
        s = open(d + f, encoding='utf-8').read()
        if old not in s: print(pid, 'ANCHOR-NOT-FOUND', what); anc += 1; continue
        open(d + f, 'w', encoding='utf-8').write(s.replace(old, new, 1))
        got, r = run(d); new_f = set(map(norm, got)) - set(map(norm, b0))
        nc = codes_of(new_f)
        if learn: print('LEARN', pid, sorted(nc), 'TB' if 'Traceback' in r.stderr else ''); continue
        meant = set(EXPECT.get(pid) or [])
        if not meant: print(pid, 'NO-MEANT-CHECK-DECLARED', what); mis += 1; continue
        if nc & meant: cau += 1; print(pid, 'CAUGHT by', ','.join(sorted(nc & meant)), '|', what)
        elif nc: inc += 1; mis += 1; print(pid, 'MISSED (only other checks fired: %s; meant %s)' % (','.join(sorted(nc)), ','.join(sorted(meant))), what)
        else: mis += 1; print(pid, 'MISSED (no check fired; meant %s)' % ','.join(sorted(meant)), what)
    if not learn: print('TOTAL plants %d: caught by the meant check %d, missed %d (of them caught only by another check %d), anchor-not-found %d' % (len(P), cau, mis, inc, anc))
    shutil.rmtree(tmp)
    return 1 if (mis or anc) else 0
sys.exit(main())
