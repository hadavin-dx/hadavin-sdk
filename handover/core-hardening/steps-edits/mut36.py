"""Planting test (v25b) for check-v36.py: the 42 v25 plants P01-P45 plus the 54 v23 plants M01-M54 ported to the v25 sources. Each plant changes ONE thing in a scratch copy of a SOURCE (or facts) file, rebuilds, runs the checker;
CAUGHT = the checker prints a FAIL line that the unmodified package does not print. Prints caught and missed honestly."""
import os, re, shutil, subprocess, sys, tempfile
H = os.path.dirname(os.path.abspath(__file__)) + '/'
FILES = ['facts-v36.py', 'build-v36.py', 'check-v36.py', 'OWNER-SHEET-v36-SOURCE.md', 'LEAD-RELEASE-NOTE-v20-SOURCE.md', 'v36-OPEN-FOR-LEAD-SOURCE.md', 'v36-CHANGES.md', 'pointers-v36.txt', 'headings-v36.txt', 'factuse-v36.txt', 'newchecks-v36.py']
def run(d):
    rb = subprocess.run([sys.executable, '-B', d + 'build-v36.py', d], capture_output=True, text=True)
    if rb.returncode: return {'FAIL BUILD stopped: ' + (rb.stderr.strip().split('\n') or [''])[-1][:80]}, rb       # the build's own assertions (marker left, run length below 860 s)
    r = subprocess.run([sys.executable, '-B', d + 'check-v36.py'], capture_output=True, text=True, env=dict(os.environ, V27_DIR=d, V31_BANNED_TEST=BANNED_PATH))
    return set(l for l in r.stdout.split('\n') if l.startswith('FAIL')), r
ALLCOPIES = {'N01', 'R18', 'P30'}
# (id, file, old, new, what)
import ast
def _banned():
    global BANNED_PATH
    r = H
    while not os.path.exists(r + 'tests/test_no_reference_material.py') and r != os.path.dirname(r.rstrip('/')) + '/': r = os.path.dirname(r.rstrip('/')) + '/'
    BANNED_PATH = r + 'tests/test_no_reference_material.py'
    t = ast.parse(open(BANNED_PATH, encoding='utf-8').read())
    for n in ast.walk(t):
        if isinstance(n, ast.Assign) and any(getattr(x, 'id', '') == 'BANNED' for x in n.targets): return [e.value for e in n.value.elts][0]
BANNED_PATH = None
BANNED_WORD = _banned()

P = [
('P01', 'facts-v36.py', 'P_OUT_C, CEIL = 40000, 10000, 300, 1500, 3', 'P_OUT_C, CEIL = 40000, 10000, 300, 1500, 4', 'call ceiling changed'),
('P02', 'facts-v36.py', 'LEDGER_C = 1240', 'LEDGER_C = 1250', 'ledger changed (limit 13.21 to 13.31)'),
('P03', 'facts-v36.py', 'NEED_S = 860', 'NEED_S = 864', '860 s changed'),
('P04', 'facts-v36.py', 'DEADLINE = dt.datetime(2026, 11, 23, 18, 29)', 'DEADLINE = dt.datetime(2026, 11, 23, 18, 30)', 'deadline minute'),
('P05', 'facts-v36.py', "IST = dt.timedelta(hours=5, minutes=30)", "IST = dt.timedelta(hours=5, minutes=0)", 'IST offset'),
('P06', 'facts-v36.py', "'dl_day': 'Mon 23 Nov 2026'", "'dl_day': 'Tue 23 Nov 2026'", 'weekday of deadline'),
('P07', 'facts-v36.py', "'postby': 'Wed 25 Nov 2026 15:00 UTC = 20:30 IST'", "'postby': 'Wed 25 Nov 2026 15:00 UTC = 20:00 IST'", 'post-by pair'),
('P09', 'OWNER-SHEET-v36-SOURCE.md', "except the key's own one-time display at 5.9 and 6.3 and the paste at 6.4", '', 'card W7 exception removed'),
('P10', 'OWNER-SHEET-v36-SOURCE.md', 'switch it OFF yourself at once with the tool the numbers message names', 'say "stop" and wait', 'recording stop by voice'),
('P11', 'OWNER-SHEET-v36-SOURCE.md', 'all in IST: alarm 1 at the latest start, alarm 2 at the alarm time', 'all in IST: alarm 2 at the alarm time', 'first alarm removed'),
('P12', 'OWNER-SHEET-v36-SOURCE.md', 'Text between backticks is typed without the backticks; ', '', 'backtick sentence removed'),
('P13', 'OWNER-SHEET-v36-SOURCE.md', "only if the window's last line is `paste key, Enter:` ", '', 'paste condition removed'),
('P14', 'OWNER-SHEET-v36-SOURCE.md', ' with paper notes "READ" and "TEST"', '', 'window labels removed'),
('P15', 'OWNER-SHEET-v36-SOURCE.md', 'the lead checks it is new', 'the lead checks nothing', 'run-name reuse rule removed'),
('P16', 'OWNER-SHEET-v36-SOURCE.md', '[[A:, then the older key]]', '', 'A older key step renamed (no longer after 6.6)'),
('P17', 'OWNER-SHEET-v36-SOURCE.md', 'reverses `end` and the card, ', '', 'lead may reverse order'),
('P18', 'OWNER-SHEET-v36-SOURCE.md', 'within the "Minutes at Type y to start" of the message, counted from the time `date -u` shows when the notice appeared (note that time at once)', 'within the minutes the message names', 'no clock for the notice window'),
('P19', 'OWNER-SHEET-v36-SOURCE.md', 'if 7.4 never happened, send "none" for the time in 8.1. ', '', 'run that never started'),
('P20', 'OWNER-SHEET-v36-SOURCE.md', 'SAMPLE (made-up values, never real):\n', '', 'SAMPLE label removed'),
('P21', 'OWNER-SHEET-v36-SOURCE.md', 'never use rotate or any button that shows a new secret', 'rotate the secret', 'HubSpot rotate allowed'),
('P22', 'OWNER-SHEET-v36-SOURCE.md', 'or "{{ph_nokey}}" (only if', 'or "no key made" (only if', 'set phrase differs'),
('P23', 'OWNER-SHEET-v36-SOURCE.md', 'weekday, month, day and year must equal the run day', 'month and day must equal the run day', 'full date check weakened'),
('P24', 'OWNER-SHEET-v36-SOURCE.md', 'balance and auto-reload equal your yes (R4)', 'the balance looks fine (R4)', 'balance re-check weakened'),
('P25', 'OWNER-SHEET-v36-SOURCE.md', 'last-resort step <step>. ', '', 'last-resort step out of the yes'),
('P26', 'OWNER-SHEET-v36-SOURCE.md', 'one line only: a second', 'a second', 'one-line warning removed'),
('P27', 'OWNER-SHEET-v36-SOURCE.md', 'press the cancel button; if a box asks', 'press the cancel button (or at 7.8 click cancel); if a box asks', 'card step 3 gets a new pointer'),
('P29', 'OWNER-SHEET-v36-SOURCE.md', '(8.3, 8.4)', '(8.3, 8.9)', 'pointer to missing step'),
('P30', 'OWNER-SHEET-v36-SOURCE.md', '**Alive** = from the moment you press the create button', '**Alivee** = from the moment you press the create button', 'card term renamed'),
('P31', 'OWNER-SHEET-v36-SOURCE.md', 'Never "Select all", never empty Trash', 'Select all is fine', 'delete guard removed'),
('P32', 'OWNER-SHEET-v36-SOURCE.md', '**STOP RULE.**', '**RULE.**', 'STOP RULE renamed'),
('P33', 'OWNER-SHEET-v36-SOURCE.md', "`. _ / - : = @ + , '` only", "`. _ / - : = @ + , ' !` only", 'R8 character list gets a character'),
('P34', 'OWNER-SHEET-v36-SOURCE.md', 'I accept these risks: the look key', 'I accept these risks (ok): the look key', 'yes pattern gets a bracket char'),
('P35', 'OWNER-SHEET-v36-SOURCE.md', '; echo "exit $?"`. Paste once', '; echo exit`. Paste once', 'key-save line loses exit report'),
('P36', 'OWNER-SHEET-v36-SOURCE.md', 'set -C; umask 077; read -rs', 'set -C; umask 077; read -rs; (', 'key-save line breaks bash -n'),
('P37', 'LEAD-RELEASE-NOTE-v20-SOURCE.md', 'the final check', 'the re-pin', 'stale word back in note'),
('P38', 'LEAD-RELEASE-NOTE-v20-SOURCE.md', '14.33', '14.4', 'old minutes figure in note'),
('P39', 'LEAD-RELEASE-NOTE-v20-SOURCE.md', '18:19:00 UTC = 23:49 IST', '18:19:00 UTC = 23:59 IST', 'wrong pair in note'),
('P40', 'v36-OPEN-FOR-LEAD-SOURCE.md', 'Mon 16 Nov 2026', 'Tue 16 Nov 2026', 'wrong weekday in open list'),
('P41', 'v36-OPEN-FOR-LEAD-SOURCE.md', 'the card', 'card Part 2', 'Part 2 back in open list'),
('P43', 'OWNER-SHEET-v36-SOURCE.md', 'Mon 16 Nov 2026', 'Mon 17 Nov 2026', 'sheet date weekday'),
('P44', 'OWNER-SHEET-v36-SOURCE.md', '[[A: I will cancel the older key myself', '[[A: I will cancel the older key soon', 'A yes sentence changed'),
('P45', 'OWNER-SHEET-v36-SOURCE.md', 'Until then the older key stays valid and can spend.', '', 'B older key fate removed'),
]
S, N, O, C, FA = 'OWNER-SHEET-v36-SOURCE.md', 'LEAD-RELEASE-NOTE-v20-SOURCE.md', 'v36-OPEN-FOR-LEAD-SOURCE.md', 'v36-CHANGES.md', 'facts-v36.py'
BW = BANNED_WORD
V = [
('V01', S, 'silence at the y question, before the film cue, in the film pause and while waiting for `end` is normal', 'silence is never normal', 'silence rule exemptions removed (stranger BL1)'),
('V02', S, '9. **Look key (after "go", before the earliest key time).**', '9. **Key (after "go").**', 'look key step removed (stranger BL2)'),
('V03', S, 'Any other difference: press nothing, go to "If it fails". ', '', 'differing cancel word rule removed'),
('V04', S, '(the lead cannot see your screen); you see the real word at 5.9 and the lead answers "confirmed"', '(the lead cannot see your screen); the lead gives it', 'cancelled word no longer seen by the owner'),
('V05', S, ' passes 7.11 before 8.1.**', '.**', 'B 7.11 not reachable from every route (security B1)'),
('V06', S, ', alarm 4 at the older-key time (do 7.11 now, whatever else is open, even if the lead is silent)', '', 'B fourth alarm removed'),
('V07', S, ' The cancel-by time is before the older-key time.', '', 'cancel-by before older-key time no longer checked'),
('V08', S, 'Wait at least the "Minimum think time" of the message', 'Wait 10 seconds', 'minimum think time back to 10 seconds'),
('V09', S, 'In the test terminal type the printed line of 6.4 (R6 shape check of its key file path first): it waits at the paste line and nothing is alive yet. ', '', 'key-save line no longer typed before create'),
('V10', S, 'Test program asks you to type a figure: no', 'Test program asks you to type a figure: yes', 'typed-figure line changed'),
('V11', S, 'first read its last-used time in the key list and describe it to the lead (a use after', 'first read its time and describe it to the lead (a use after', 'B 7.11 last-used time dropped'),
('V12', S, 'a model key stored in n8n would spend without the spend lock', 'a model key in n8n is fine', 'n8n model key reason removed'),
('V13', O, 'No default pick: you do not choose for the owner', 'Money-safe default: B: you do not choose for the owner', 'open list names B as default'),
('V14', N, 'both sheets have four alarms, the fourth at', 'both sheets have alarms, the fourth at', 'note G30 loses the fourth alarm'),
('V15', O, 'WHEN IT FAILS (v36)', 'WHEN IT FAILS', 'A 7-day failure handling removed from open list'),
('V16', O, 'MET for the sheet page alone by', 'Word target not stated by', 'open list says word target met'),
('V17', S, 'If the run ends before 6.7 the older key is still valid: you cancel it at 7.11', 'If the run ends before 6.7 nothing more happens: 7.11', 'A older key: what happens after an early end no longer said'),
('V18', S, 'none within the silence minutes: describe, FREEZE; no key is alive then', '', 'no shell prompt: no action'),
('V19', S, 'Start only after the lead\'s word "post"', 'Start', 'posting without the lead word'),
('V20', S, 'say "filmed" and read both counts aloud', 'say "filmed"', 'film counts no longer read aloud'),
('V21', S, "your phone's clock (IST minus 5:30) is within 2 minutes of it, ", '', 'phone clock check removed'),
('NEG1', S, '9. **Look key (after "go", before the earliest key time).**', '9. **Key (after "go").**', 'NEGATIVE CONTROL: same plant as V02 but the meant check is a wrong one, so it must print MISSED'),
]
P += V
# ported from the 54 v23 plants (evidence-v23-independent/scripts/mut.py M01-M54); anchors rewritten for the v25 source; M-ids kept
M = [
('M01', S, 'Price per call at full size: USD {{price}}', 'Price per call at full size: USD 0.28', 'price line 0.27 to 0.28'),
('M02', S, 'Expected total: USD {{total}} (not a limit)', 'Expected total: USD 0.82 (not a limit)', 'expected total line 0.81 to 0.82'),
('M03', S, 'Price per call at full size: USD {{price}}', 'Price per call at full size: USD 0.28', 'sample notice price line'),
('M04', S, 'expected total USD <expected total>, balance USD', 'expected total USD 0.82, balance USD', 'yes pattern total'),
('M05', S, 'If you had typed `end`, proceed at 7.9;', 'If you had typed `end`, proceed at 7.5;', 'after-the-card pointer 7.9 to 7.5'),
('M06', S, 'back to the values on your paper in 8.7', 'back to the values on your paper in 8.5', 'pointer back on in 8.7 to 8.5'),
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
('M18', N, '(Open 2 and 31)', '(Open 2 and 199)', 'list-form pointer Open 199 (no such row)'),
('M19', S, 'minimise the test terminal; then call the film person in', 'minimise the test terminal: if you must stop it, click Cancel beside each key and refresh the page twice to see the cancelled state; then call the film person in', 'cancel rule paraphrased outside the card (7.6)'),
('M20', S, 'send "{{ph_hsr}}"', 'send "{{ph_apr}}"', 'wrong set phrase at 8.4'),
('M21', S, 'delete exactly those as R7 says', 'delete exactly those as R9 says', 'R7 to R9 in 5.4'),
('M22', S, 'The balance is at least the expected total.', 'The balance is at least the expected total plus 5.', 'check 3 changed'),
('M23', FA, 'Y, RL, FP, MG = 5, 15, 10, 10', 'Y, RL, FP, MG = 5, 15, 10, 15', 'margin changed in facts (sums)'),
('M24', S, 'L2 the older key named', '[[A: [[B: leftover]] L2 the older key named', 'nested marker left'),
('M25', S, 'The balance is at least the expected total.', 'The balance is at least the expected total. [[ left', 'stray marker left'),
('M26', N, "## 9. Kept from earlier appendices (lead's own use)", "## 9. Kept from earlier appendices (lead's own use) " + BW, 'banned word in note'),
('M27', O, '| 40 | Does the take program print', '| 41 | Does the take program print', 'open list numbering gap'),
('M28', N, '| G12 | Claims: the one sentence', '| G32 | Claims: the one sentence', 'note G pointer G12 to G32'),
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
('M39', S, 'Send exactly: {{ph_mkc}} (not for a look key).', 'Send exactly: model key canceled (not for a look key).', 'card step 5 phrase spelled differently'),
('M40', S, 'B submitted 10 times', 'B submitted 12 times', 'B submitted 12 times'),
('M41', N, '(IST = UTC + 5:30)', '(IST = UTC + 5:00)', 'IST definition in note'),
('M42', O, 'the take program needs at least 860 seconds (14.33 minutes)', 'the take program needs at least 860 seconds (14.5 minutes)', 'open list minutes figure'),
('M43', N, 'the spend lock (G33)', 'the spend lock (G38)', 'note G33 to G38'),
('M44', S, '"go" (5.8)', '"go" (5.7)', 'R8 pointer go (5.8) to 5.7'),
('M45', S, 'you read both at 6.2 and 6.7', 'you read both at 6.2 and 6.8', 'R4 pointer 6.7 to 6.8'),
('M46', S, 'after the model key\'s cancel press, card step 3)', 'after the model key\'s cancel press, card step 5)', '8.1 card step 3 to 5'),
('M47', S, '## 9. Posting (by {{postby}}', '## 9. Posting (by Wed 25 Nov 2026 15:00 UTC = 20:00 IST', 'post-by IST in sheet'),
('M48', C, 'may cancel the older key at 6.7; it never stops 7.11', 'may cancel the older key at 6.9; it never stops 7.11', 'CHANGES table pointer 6.7 to 6.9'),
('M49', O, "the sheet's 7.8 error sentence stays", "the sheet's 7.7 error sentence stays", 'open row pointer 7.8 to 7.7'),
('M50', N, 'gives 0.27; ceiling 3 gives expected total 0.81', 'gives 0.28; ceiling 3 gives expected total 0.81', 'note worked price'),
('M51', S, 'send "{{ph_dmd}}"', 'send "all done"', 'unlisted set phrase sent in 8.5'),
('M52', N, '(Open 2 and 31)', '(Open 2, 31 and 199)', 'Open 199 in a list form (no such row)'),
('M53', N, 'expected total 0.81. Ledger total 12.40', 'expected total 0.80. Ledger total 12.40', 'expected total in note'),
('M54', S, 'Deadline {{dl_full}}.', 'Deadline 2026-11-23 18:29 UTC = 23:29 IST.', 'yes deadline IST pair'),
]

P = P + M

# the 15 plants that check-v24 missed in the independent run (own25.py Q01 Q02 Q03 Q08 Q09 Q10 Q11 Q12 Q13 Q15 Q16 Q18 Q20 Q22 Q24), anchors ported to the v25 sources
SECRET = 'sk' + '-' + 'ab12' * 10          # built from parts, never a real key
N = 'LEAD-RELEASE-NOTE-v20-SOURCE.md'
Q = [
('Q01', S, '/ 1,000,000 = {{price}}; expected total', '/ 1,000,000 = 0.28; expected total', 'wrong price per call hardcoded'),
('Q02', S, '{{ceil}} x {{price}} = {{total}}', '{{ceil}} x {{price}} = 0.84', 'wrong total hardcoded'),
('Q03', S, 'Tokens in and out per call: {{tok_in}} and {{tok_out}}', 'Tokens in and out per call: {{tok_in}} and 12,000', 'wrong output tokens in the sample'),
('Q08', S, '(1) if a key is alive, do the card now; (2) then FREEZE', '(2) then FREEZE', 'STOP RULE step 1 deleted'),
('Q09', S, 'W1 you typed `end`;', 'W1 you typed `end;', 'stray backtick in card gate W1'),
('Q10', S, 'press the cancel button; if a box asks, press the confirmation word', 'press the cancel button; if a box asks, press close', 'card cancel step changed'),
('Q11', S, 'W6 the test terminal shows a shell prompt before you typed `end`; ', '', 'card gate W6 deleted'),
('Q12', S, 'auto-reload off, balance at least the expected total', 'auto-reload on, balance at least the expected total', 'R4 auto-reload flipped to on'),
('Q13', S, 'Silence minutes: 3   Give-up minutes: 40', 'Silence minutes: 3   Give-up minutes: 40   Key: ' + SECRET, 'secret-shaped string (built from parts) in the sheet'),
('Q15', S, 'Give-up minutes: 40', 'Give-up minutes: 30', 'sample give-up minutes changed'),
('Q16', S, 'Silence minutes: 3', 'Silence minutes: 5', 'sample silence minutes changed'),
('Q18', S, 'or not ending `@example.com`', 'or not ending `@example.org`', 'one delete-domain guard changed'),
('Q20', N, 'program limit = 12.40 + 0.81 = 13.21', 'program limit = 12.40 + 0.81 = 13.12', 'lead note limit wrong'),
('Q22', S, 'Exit codes accepted: 0 only', 'Exit codes accepted: 0 or 1', 'accepted exit codes widened'),
('Q24', S, 'the seven words, which alone start or end a step', 'the six words, which alone start or end a step', 'R8 word count changed'),
]
P = P + Q
SLASHKEY = 'q' * 8 + '/' + 'Z' * 16 + '_' + 'k' * 12 + '-' + 'm' * 9           # 47 characters with a slash, built from parts, never a real key
# plants of v36: the v25 misses (N01 N05 N10 N11 N12 N14, security M4 x4, C55 slash gap) and 21 new kinds (R01-R21): each names the check MEANT to catch it
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
('R01', S, '7.11, always, by the older-key time of the message', '7.11, always, by 18:30 UTC = 00:00 IST', 'B older-key cancel time after 18:14 UTC'),
('R02', S, '**Older key point (cannot be undone;', '**Older key point (', 'B 7.11 title loses the irreversible warning'),
('R03', S, 'exactly the rows you wrote minus K', 'exactly N minus K', 'card proof uses N minus K again'),
('R04', S, '[[A:, then the older key]]', '', 'A older-key cancel before the key is saved'),
('R05', S, '`PRICE_OUT_CENTS`, `CALL_CEILING`,', '`PRICE_OUT_CENTS`,', 'one of the seven setting names dropped'),
('R06', S, '`-c@` or `prep-<run name>@example.com`', '`-c@`', 'R7 prep prefix dropped'),
('R07', S, 'in the read terminal must say no such file (', 'in the read terminal must say nothing (', '8.1 proof of the deleted key file weakened'),
('R08', S, '"restarted" (6.6), ', '', 'R8 loses the restarted word (and its count stays six)'),
('R09', S, 'one named human you can call', 'one named person', 'backup person no longer a human you can call'),
('R10', S, 'the only valid answer is their own written words "matches the sentences"', 'the answer can be a thumbs-up', 'post checker valid answer removed'),
('R11', S, '**Deadline** = the end of the period your spending approval covers', '**Deadline** = the end of the run', 'deadline definition changed'),
('R12', S, 'A differing printed count: send the counts, do not post, FREEZE.', 'A differing printed count: post anyway.', '7.10 mismatch action changed'),
('R13', S, 'remove only that profile, never your normal profile', 'remove your profiles', '8.7 profile removal widened'),
('R14', S, 'Gap before 8.1: <minutes>', '', 'sample numbers message loses the gap slot'),
('R15', S, 'the scopes the message names in "Key scopes"', 'any scopes', 'create-form scopes widened'),
('R16', S, 'W9 the text of the older key appeared on your screen', 'W9 the older key was seen', 'W9 older key exposure trigger weakened'),
('R17', S, 'plugged in; sleep Never', 'plugged in', 'laptop sleep value dropped'),
('R18', S, 'FREEZE is not a cancel: a live key is cancelled only by a danger sign', 'FREEZE is a cancel: a live key is cancelled only by a danger sign', 'FREEZE is called a cancel'),
('R19', S, '**Key** alone = a model key', '**Key** alone = any key', 'word key given a second meaning'),
('R20', S, 'make a Chrome profile `demo-take`', 'make a Chrome profile `demo-film`', 'profile name differs between steps'),
('R21', S, '(click your profile picture at the top right, Add profile, Continue without an account, name it; UNVERIFIED, tolerated)', '(name it)', 'Chrome profile how-to and ask-the-lead removed'),
('R22', S, 'no name known: describe, revoke nothing', 'no name known: revoke the newest entry', 'entry to revoke guessed'),
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
  'P05': ['C03', 'C04', 'C18', 'C79', 'C86', 'BUILD'],   # round 7: facts-v36.py asserts the sample pairs, so the build stops first
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
EXPECT['R22'] = ['C104']
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
EXPECT.update({'P20':['C14k','BUILD'],'P11':['C159'],'V01':['C105'],'V02':['C106'],'V03':['C107'],'V04':['C108'],'V05':['C137'],'V06':['C138'],'V07':['C139'],'V08':['C140'],'V09':['C111'],'V10':['C141'],'V11':['C142'],'V12':['C143'],'V13':['C149'],'V14':['C151'],'V15':['C154'],'V16':['C155'],'V17':['C126'],'V18':['C124'],'V19':['C125'],'V20':['C122'],'V21':['C121'],'NEG1':['C999']})
# ---- v36 plants (one per new check C171 to C184 of Part 6)
W = [
('W01', S, 'Four phone alarms on the run day', 'Three phone alarms on the run day', 'A or B: the fourth alarm word removed'),
('W02', S, '**Older key point (cannot be undone; every way the run ends passes here before 8.1).**', '**Older key note.**', 'older-key point step renamed'),
('W03', S, 'a FREEZE does not stop this', 'a FREEZE stops this', 'FREEZE stops the older-key cancel'),
('W04', S, '# Owner sheet v36, sheet [[A:A]][[B:B]]: one filmed run', '# Owner sheet v36: one filmed run', 'sheet letter removed from the heading'),
('W05', S, 'n8n credentials: exactly the three, by name', 'n8n credentials: exactly the three', 'n8n slot by name removed'),
('W06', S, 'alone (R1), with the narrowest scopes the create form offers', 'with the widest scopes the create form offers', 'look key scopes clause'),
('W07', S, 'a later use: use sheet B', 'a later use: use sheet A', 'A/B condition reversed'),
('W08', O, "give another before the program's refusal limit 18:14 UTC = 23:44 IST;", 'give another before 18:14 UTC;', '18:14 without its label'),
('W09', N, 'and nothing about a lease: the lease sentence is struck from the public post', 'plus "A gap longer than the lease is not claimed." (the lease sentence is struck from the public post', 'lease sentence put back in the public post'),
('W10', FA, 'LS23 = dt.datetime(2026, 11, 23, 18, 4)', 'LS23 = dt.datetime(2026, 11, 23, 18, 14)', 'latest start of 23 Nov changed'),
('W11', S, '[OWNER FILLS:', '[OWNER:', 'placeholder label changed'),
('W12', S, '"continue" (after a FREEZE)', '"carry on" (after a FREEZE)', 'R8 word set changed'),
('W13', S, 'The 7-day rule (worded the same everywhere in this package):', 'The 7-day rule is about a week:', '168 hours wording'),
('W14', N, 'Open 103', 'Open 99', 'open question reference removed'),
('W15', O, 'E-52', 'E-5', 'E-52 UNVERIFIED row changed'),
('W16', S, 'Use no older sheet.', 'Use no older sheet. ' + 'filler ' * 400, 'sheet grows over 6,300 words'),
]
P += W
EXPECT.update({'W01':['C172'],'W02':['C172'],'W03':['C172'],'W04':['C173'],'W05':['C174'],'W06':['C175'],'W07':['C176'],'W08':['C177'],'W09':['C178'],'W10':['C179'],'W11':['C180'],'W12':['C181'],'W13':['C182'],'W14':['C183'],'W15':['C184'],'W16':['C171']})
ALLCOPIES |= {'W05', 'W11', 'W12', 'W14', 'W15', 'W07', 'W06', 'W03'}

X = [
('X01', S, 'the key list may show a last use hours late', 'the key list shows every use at once', '7-day lag sentence removed'),
('X02', S, 'then cancel anyway (the yes covers the cancel)', 'then cancel anyway unless you know something else uses it (the yes covers the cancel)', '7.11 escape put back'),
('X03', S, '**Deadline reminders (Sun 22 Nov and Mon 23 Nov):**', '**Deadline note:**', 'deadline backstop removed from the sheet'),
('X04', N, 'does NOT wait for a message from you', 'waits for a message from you', 'note says the older key in A waits for the lead'),
('X05', N, 'the 7-day time is {{sevenback}}', 'the 7-day time is long ago', '7-day warning removed from the default line'),
('X06', S, 'no such page: describe that there is no Recall page, then go on', 'if there is no such page this is a STOP', 'Recall page no longer a stop'),
('X07', S, 'no clipboard manager, remote-access or screen-capture tool running', 'no other program running', 'clipboard manager rule removed'),
('X08', S, 'never a file manager, a second terminal window or the clipboard (no copy and paste)', 'never a password', 'film person restrictions removed'),
('X09', S, 'the film person does not stop for', 'the film person stops for', 'film person stops for the From column'),
('X10', S, '**Name rule (8.3, 8.4):** revoke only an entry whose exact name', '**Name rule (8.3, 8.4):** revoke any entry whose exact name', 'revoke name rule removed'),
('X11', FA, 'GAP_MAX = 60', 'GAP_MAX = 90', 'gap cap changed in facts'),
('X12', S, 'after 18:30 UTC = 00:00 IST', 'after 18:30 UTC', 'UTC time without its IST pair'),
('X13', S, 'the three waits of the message added', 'the waits added', 'three waits not named'),
('X14', S, '(only that one person)', '', 'failed cancel calls more than one person'),
('X15', S, 'press Enter once; the line `exit 0` appears', 'the line `exit 0` appears', 'press Enter removed from 6.4'),
('X16', S, 'Step 7.3, matching a masked address', 'matching a masked address', 'orphaned appendix fragment'),
('X17', S, 'match each by its first two letters', ':: match each by its first two letters', 'double colon'),
('X18', S, '(((F10 Deadline backstop::', '(((F12 Deadline backstop::', 'appendix part number gap'),
('X19', S, "Retire check (the lead's own test", "Retire check (a test", 'retire check not defined'),
('X20', S, 'what "at re-pin" means', 'what the brackets mean', 'at re-pin not explained'),
('X21', O, '`[OWNER FILLS: ...]`', '`[OWNER FILLS ...]`', 'placeholder spelling in the open list'),
('X22', O, '| 109 | Still OWNER-OPEN', '| 110 | Still OWNER-OPEN', 'open row 109 missing'),
('X23', S, 'Right after the yes, set the two **deadline reminders** (7.11)', 'Right after the yes, do nothing more (7.11)', 'deadline reminder not set after the yes'),
('X24', N, '18:04 is a plan fact', '18:04 is a time', '18:04 plan-fact sentence removed from the note'),
('X25', S, 'and only if the 7-day rule of 5.1 holds', 'and only if the 7-day rule holds (at least 168 hours (7 days) before)', '7-day rule worded twice'),
('X26', S, 'send "{{ph_older711}}", then cancel', 'send "{{ph_older}}", then cancel', '7.11 forced cancel uses the claim phrase'),
('X27', S, 'press Enter at least 5 minutes before the latest start', 'press Enter at least 4 minutes before the latest start', '5-minute rule worded differently in 6.2'),
]
P += X
EXPECT.update({'X01':['C185'],'X02':['C186'],'X03':['C187'],'X04':['C188'],'X05':['C189'],'X06':['C190'],'X07':['C191'],'X08':['C192'],'X09':['C192'],'X10':['C193'],'X11':['C194'],'X12':['C195'],'X13':['C196'],'X14':['C197'],'X15':['C198'],'X16':['C199'],'X17':['C200'],'X18':['C201'],'X19':['C202'],'X20':['C203'],'X21':['C206'],'X22':['C207'],'X23':['C187'],'X24':['C209'],'X25':['C185'],'X26':['C186'],'X27':['C196']})

# Y series: one plant per class of the v36 Part 8 checks (C210 to C227)
BUILD_F = 'build-v36.py'
Y = [
('Y01', FA, "BM = dt.datetime(2026, 11, 23, 18, 9)", "BM = dt.datetime(2026, 11, 23, 18, 8)", 'Monday reminder time changed'),
('Y02', S, '## 7. The run (UNVERIFIED)', 'If your run day is Mon 23 Nov, do x.\n\n## 7. The run (UNVERIFIED)', 'dead Mon 23 Nov paragraph back'),
('Y03', O, 'No default pick', 'Safe default if you do not answer: A', 'old default wording back in the open list'),
('Y04', N, "## 9. Kept from earlier appendices (lead's own use)", "When the lead message says go, the owner may skip the older key cancel: the lead releases the older key cancel.\n\n## 9. Kept from earlier appendices (lead's own use)", 'lead message releases the older-key cancel (H06 phrasing)'),
('Y05', N, "## 9. Kept from earlier appendices (lead's own use)", "If the lead has not confirmed, the older key cancel waits for the lead's word.\n\n## 9. Kept from earlier appendices (lead's own use)", 'older-key cancel waits for a lead word (other phrasing)'),
('Y06', S, 'Entries to revoke later: app passwords <names, exact>', 'Entries to revoke: app passwords <names, exact>', 'numbers sample loses the row name'),
('Y07', S, 'Sheet B cancels the older key at 7.11 even if it was used a day ago', 'Sheet B cancels the older key at 7.11', 'B warning of 5.1 shortened'),
('Y08', S, 'It does not mean no valid key remains: the older key may still spend until it is cancelled', 'It means no valid key remains', 'card step 5 older-key sentence reversed'),
('Y09', S, 'The yes binds you to 7.11', 'The yes helps with 7.11', 'yes binding removed'),
('Y10', S, 'it is an instruction, not a technical guard', 'it is a technical guard', 'guard honesty sentence reversed'),
('Y11', S, 'a later use: use sheet B.', 'a later use: all is well.', 'run day for the first reading removed'),
('Y12', S, 'from 5 minutes before the latest start do not press Enter', 'from 5 minutes before the latest start press Enter', 'last-5-minutes rule reversed'),
('Y13', S, 'press F11', 'press F12', 'film page: how to show only the page area'),
('Y14', S, 'Remember my preferences', 'Remember me', 'sync path wording'),
('Y15', S, 'Words with one meaning here', 'Words', 'definitions heading'),
('Y16', S, 'are not an empty slot', 'are an empty slot', 'owner-fill rows described as empty slots'),
('Y17', O, 'the sheet checks only the maximum', 'the sheet checks both at 5.7', 'open list: the minimum is said to be checked'),
('Y18', S, '[LEAD FILLS at re-pin:', '[LEAD FILLS at repin:', 'a LEAD FILLS placeholder spelled differently (H09)'),
('Y19', FA, "'bm':", "'zz_dead': 'x', 'bm':", 'a fact no source uses (ls_t kind)'),
('Y20', S, '## 7. The run (UNVERIFIED)', 'Mail ann@corp.test with the list.\n\n## 7. The run (UNVERIFIED)', 'email-shaped text in the owner pages'),
('Y21', BUILD_F, '"""Builds every v36 text', '_X = "/ho' + 'me/x/k"\n"""Builds every v36 text', 'hard-coded absolute path in a script'),
]
P += Y
EXPECT.update({'Y01':['C210','BUILD'],'Y02':['C210'],'Y03':['C212'],'Y04':['C213'],'Y05':['C213'],'Y06':['C214'],'Y07':['C215'],'Y08':['C216'],'Y09':['C217'],'Y10':['C218'],'Y11':['C219'],'Y12':['C220'],'Y13':['C221'],'Y14':['C222'],'Y15':['C222'],'Y16':['C222'],'Y17':['C223'],'Y18':['C224'],'Y19':['C225'],'Y20':['C226'],'Y21':['C227']})
Z = [
('Z01', FA, 'SEVENBACK = EK - dt.timedelta(hours=168)', 'SEVENBACK = EK - dt.timedelta(hours=160)', 'H33: 7-day time computed with 160 hours'),
('Z02', S, ' L5 The last-resort step', ' L4 The last-resort step', 'H37: cancel-list label L5 renamed L4'),
('Z03', S, '## 6. The model key (R1 applies; UNVERIFIED)', '## 6. The model key (R1 applies)', 'H38: UNVERIFIED removed from the section 6 heading'),
('Z04', S, '{{fp}}', '12', 'H50: film pause 10 changed to 12 in one place'),
('Z05', S, '{{ceil}}', '4', 'H51: call ceiling 3 changed to 4 in one place'),
('Z06', S, '{{rl}}', '12', 'H53: run length 15 changed to 12 in one place'),
('Z07', N, 'will probably fail on Wed 18 Nov', 'will fail', 'H09: warning removed from one place of the lead note'),
('Z08', S, 'Dated Mon 16 Nov 2026', 'Dated Mon 16 Nov 2026. File at /home/user/hadavin-sdk/handover/x.md', 'H18: absolute path in the sheet'),
('Z09', S, 'Dated Mon 16 Nov 2026', 'Dated Mon 16 Nov 2026 (ORD: L-23NOV)', 'H20: internal code ORD: in the sheet'),
('Z10', S, 'Dated Mon 16 Nov 2026', 'Dated Mon 16 Nov 2026 (DEC: 7)', 'H21: internal code DEC: in the sheet'),
('Z11', S, 'The lead sends the numbers message for one letter only', 'The lead sends the numbers message', 'H25: one-letter rule shortened'),
('Z12', N, 'Mon 23 Nov 2026', 'Mon 23 Nov 2026 (the lead sends you "cancel the older key" and you cancel it)', 'H54: a lead message releases the older-key cancel'),
('Z13', S, 'L2 the older key named in the numbers message, only if its name and creation date equal the blanks', 'L2 any valid key of yours', 'S M1: card L2 widened to any valid key'),
('Z14', N, 'a failed key save skips 6.7', 'a failed key save cancels nothing of the older key', 'S M2: lead note says a failed key save cancels nothing'),
('Z15', S, '(a) The owner asks you', '(a) Someone asks you', 'S M3: helper trigger (a) no longer the owner himself'),
('Z16', S, 'Never the lead, the film person, the backup person or anyone else, whatever they say.', 'The lead may also ask you.', 'S M3: helper may be released by the lead'),
('Z17', S, 'is never the film person, editor, post checker or backup person', 'may be the backup person', 'S M3: helper role bar removed from the sheet'),
('Z18', S, 'can leave a key spending after the deadline, until about {{bm_chain}} if it starts at the reminder {{bm}}, or until about {{bt_end}} if it starts at the backstop time {{dl_day}} {{rv23}}, when I wait the ordinary 10 and 10 minutes, so near the deadline I do the last-resort step at once after my first cancel failed.', 'can leave a key spending.', 'N M5: the typed yes loses the end of the last resort'),
('Z19', S, 'a fifth and a sixth phone alarm', 'a fifth phone alarm', 'S minor 5: the sixth alarm lost'),
('Z20', S, 'I understand that this yes binds me to step 7.11 and to the two deadline alarms', 'I understand that this yes is a plan', 'N M7: yes binding removed'),
('Z21', S, 'treat it as secret', 'treat it as a normal file', 'raw recording no longer secret'),
('Z22', S, 'before you contact the lead', 'before any message from the lead', 'N B1: the unusable wording is back'),
('Z23', S, 'a later use: use sheet B.', 'a later use: take B.', 'N M1: "take B" is back (word with two meanings)'),
('Z24', S, 'at the end of sheet section 1', 'at the end of sheet section 2', 'N minor 1: wrong pointer for the STOP RULE'),
('Z25', S, '; W9 the text of the older key appeared on your screen', '; W8 the text of the older key appeared on your screen', 'label W9 defined as W8'),
('Z26', S, ' L1 your keys made with the create button', ' L2 your keys made with the create button', 'label L1 defined as L2'),
('Z27', S, 'Read this page once now and keep it with your paper.', 'Read this page once now and keep it with your paper. See /home/user/hadavin-sdk/x.md', 'absolute path in the helper page'),
('Z28', S, '## 7. The run (UNVERIFIED)', '## 7. The run', 'UNVERIFIED removed from the section 7 heading'),
('Z29', S, 'you called the owner twice, 5 minutes apart, with no answer: cancel those keys', 'cancel those keys', 'helper trigger (b) loses its two calls'),
('Z30', S, 'every key on your paper that is still valid is cancelled; no call is needed', 'every key is cancelled', 'helper trigger (d) widened'),
]
P += Z
EXPECT.update({'Z01':['C235'],'Z02':['C237'],'Z03':['C238'],'Z04':['C236'],'Z05':['C236'],'Z06':['C236'],'Z07':['C212'],'Z08':['C240'],'Z09':['C240'],'Z10':['C240'],'Z11':['C241'],'Z12':['C242'],'Z13':['C228'],'Z14':['C229'],'Z15':['C230'],'Z16':['C230'],'Z17':['C230'],'Z18':['C233'],'Z19':['C232'],'Z20':['C233'],'Z21':['C234'],'Z22':['C244'],'Z23':['C244'],'Z24':['C245'],'Z25':['C237'],'Z26':['C237'],'Z27':['C240'],'Z28':['C238'],'Z29':['C230'],'Z30':['C230']})

V33 = [
('AA01', S, 'or until about {{bt_end}} if it starts', 'or until about 18:21 UTC = 23:51 IST if it starts', 'H04: last-resort end changed to an earlier consistent pair'),
('AA02', S, 'both after the deadline (the two cases of the yes)', 'both before the deadline (the two cases of the yes)', 'H05: "after the deadline" changed to "before"'),
('AA03', S, 'Any other key, even one the owner mistyped the name of: touch nothing, write down its name', 'Any other key, even one the owner mistyped the name of: cancel it, write down its name', 'H07: helper told to cancel any other key'),
('AA04', S, 'never by a tool, script, window or person', 'or by a tool, script, window or person', 'H14: R6 allows a tool or script'),
('AA05', S, 'Right after `exit 0`, copy one harmless word such as `clear` (it replaces the clipboard).', '', 'H17: the clear clipboard step removed'),
('AA06', S, 'Paste once (Ctrl+Shift+V', 'Paste as often as you like (Ctrl+Shift+V', 'H18: paste once changed'),
('AA07', S, 'starts `-rw-------`', 'starts `-rw-r--r--`', 'H19: key file mode made world readable'),
('AA08', S, 'time or key state is never tolerated.\n- **Lead** = the AI session (an AI, not a person) in the chat where you got this sheet, ', 'time or key state is tolerated.\n- **Lead** = the AI session (an AI, not a person) in the chat where you got this sheet, ', 'H20 first copy: never tolerated changed'),
('AA09', S, 'time or key state is never tolerated.\n- **Lead** = the AI session (an AI, not a person) in the chat where you got this sheet; ', 'time or key state is tolerated.\n- **Lead** = the AI session (an AI, not a person) in the chat where you got this sheet; ', 'H20 second copy: never tolerated changed'),
('AA10', S, "then cancel the older key by the card's L2, steps 2 to 4, only if its name and creation date equal the blanks", "then cancel the older key by the card's L2, steps 2 to 4", 'H23: older-key cancel without the name and date condition (7.11)'),
('AA11', S, 'L2 the older key named in the numbers message, only if its name and creation date equal the blanks;', 'L2 the older key named in the numbers message;', 'H23 second place: card list L2 without the condition'),
('AA12', S, 'if key text appears, close it and tell the owner it appeared', 'if key text appears, keep it and tell the owner it appeared', 'H35: helper told to keep key text'),
('AA13', S, 'even if a run was in progress (no run is planned on that day)', 'unless a run was in progress (no run is planned on that day)', 'H38: backstop with an exception for a run'),
('AA14', S, 'do the last-resort step at once after your first "{{ph_cf}}" (retry', 'wait the 10 and 10 minutes after your first "{{ph_cf}}" (retry', 'M1: card waits the ordinary chain near the deadline'),
('AA15', S, 'type `cd ` and the Take folder of the message, nothing more', 'type `cd ` and the Take folder of the message', 'M2: cd line may hold more'),
('AA16', S, 'the `cd` line of 7.2 is exactly `cd ` plus the Take folder, nothing else (no `&&`, `;`, `|`, second command or space-separated word after the folder)', 'the `cd` line of 7.2 is checked', 'M2: R6 cd rule dropped'),
('AA17', 'v36-OPEN-FOR-LEAD-SOURCE.md', "No default pick: A or B is the owner's choice (row 71) |", 'Default: A |', 'M3: Default A back in the open list'),
('AA18', S, '(write VOID on it; a new paper replaces it)', '(write nothing on it)', 'helper paper VOID step removed'),
('AA19', S, 'and Mon 23 Nov 2026 {{rv23}}.', 'and {{rv23}}.', 'helper backstop date dropped'),
('AA20', S, ' or the film person says "stop"', '', 'W3 film person stop removed'),
('AA21', S, 'press cancel again on the same named row and reload', 'press cancel again and reload', 'card step 4 same named row removed'),
('AA22', S, 'Watch the edited video twice', 'Watch the video twice', '8.8 edited video wording'),
('AA23', S, 'Never copy, type or photograph key text; ', 'Copy, type or photograph key text; ', 'key text rule reversed'),
]
P = P + V33
EXPECT.update({'AA01': ['C255'], 'AA02': ['C256'], 'AA03': ['C257'], 'AA04': ['C258'], 'AA05': ['C259'], 'AA06': ['C259'], 'AA07': ['C260'], 'AA08': ['C260'], 'AA09': ['C260'], 'AA10': ['C261'], 'AA11': ['C261'], 'AA12': ['C257'], 'AA13': ['C262'], 'AA14': ['C246'], 'AA15': ['C247'], 'AA16': ['C247'], 'AA17': ['C248'], 'AA18': ['C249'], 'AA19': ['C249'], 'AA20': ['C249'], 'AA21': ['C250'], 'AA22': ['C250'], 'AA23': ['C257', 'C262']})
LN = 'LEAD-RELEASE-NOTE-v20-SOURCE.md'; OP = 'v36-OPEN-FOR-LEAD-SOURCE.md'
V34 = [
('AB01', S, 'tops itself up when low (must be off)', 'tops itself up when low (must be on)', 'X03: auto-reload rule reversed in the appendices'),
('AB02', S, 'search the exact address, see exactly one result whose page shows it, then delete', 'search the start of the address, then delete all results', 'X07: contact delete rule widened'),
('AB03', S, 'if nobody answers within 10 more minutes, do the last-resort step yourself, only in the model account', 'if nobody answers within 10 more minutes, wait', 'X08: ordinary waiting chain loses the last-resort step'),
('AB04', S, "Post only the video and the lead's exact sentences, after", "Post the video, the lead's exact sentences and a lease line, after", 'X10: public post allows extra text'),
('AB05', S, ', and a helper whose cancel fails does only the last-resort step on its paper or none,', ',', 'M1: the yes no longer names the failed helper case'),
('AB06', S, 'do at once the last-resort step on your paper', 'call the owner and wait', 'M1: failed helper cancel ends with no step'),
('AB07', LN, 'one sentence (lead answer Q22c)', 'two sentences', 'M2: lead note claim wording back to two sentences'),
('AB08', OP, 'Q22c is one sentence and it names no person', 'Q22 (c) is two sentences and neither names a person', 'M2: open list row 7 back to two sentences'),
('AB09', S, 'the owner phones them after step 5.9 on the run day', 'the owner gives them on the run day', 'B2: helper paper completion time removed'),
('AB10', S, 'no such page: describe that there is no Recall page, then go on', 'no such page: this is a STOP, wait for the lead\'s written answer', 'B3: Recall page missing is a stop again'),
('AB11', S, '(retry 2 minutes, phone fallback, send', '(retry 2 minutes, send', 'minor 4: near-deadline line drops the phone fallback'),
('AB12', S, 'sleep Never; screen off Never; lid close action', 'sleep Never; lid close action', 'M7: screen turn-off not set'),
('AB13', S, 'In those up to 22 minutes (2 of retry, then 10 and 10)', 'In those up to 20 minutes', 'M4: card says 20 minutes for a 22-minute chain'),
('AB14', S, 'so that no reminder or backstop time meets a live run key.', 'so that no reminder or backstop time meets a live run key; a reminder never cancels a live run key.', 'minor 1: the reminder contradiction back'),
('AB15', S, '(they differ: cancel nothing, send "{{ph_cf}}", call the backup person at once)', '', 'minor 5: 7.11 mismatch dead end back'),
('AB16', S, 'End of the numbers message part, sheet', ' '.join(['filler'] * 400) + ' End of the numbers message part, sheet', 'reading load: 400 words added'),
('AB17', S, '**Backstop time** = {{rv22}} or {{dl_day}} {{rv23}} (after the reminder that rang)', '**Backstop time** = {{dl_day}} {{rv23}} (after the reminder that rang)', 'minor 2: card backstop time loses the Sunday time'),
]
P = P + V34
EXPECT.update({'AB01': ['C263'], 'AB02': ['C264'], 'AB03': ['C265'], 'AB04': ['C266'], 'AB05': ['C267'], 'AB06': ['C267'], 'AB07': ['C268'], 'AB08': ['C268'], 'AB09': ['C269'], 'AB10': ['C270'], 'AB11': ['C271'], 'AB12': ['C272'], 'AB13': ['C271'], 'AB14': ['C271'], 'AB15': ['C271'], 'AB16': ['C273', 'C07'], 'AB17': ['C271']})
# round 7: plants whose anchor text was reworded by the round 7 edits are re-pointed to the new wording (same mutation idea, new anchor); each is still caught by the check meant for it
_REPOINT = {'V06': (', alarm 4 at the older-key time (do 7.11 now, whatever else is open, even if the lead is silent; set it to repeat every 10 minutes until you have done 7.11)', ''), 'V09': ('In the test terminal type the printed line of 6.4 (R6 shape check of its key file path first; compare the typed line with the printed one before Enter)', ''), 'M33': ('{{dl_day}} {{dl}}); the program', 'Tue 23 Nov 2026 18:29 UTC = 23:59 IST); the program'), 'Q09': ('P1 you typed `end` (7.8);', 'P1 you typed `end (7.8);'), 'Q11': ('W6 the test terminal shows a shell prompt before you typed `end`;\n', ''), 'N10': (' (else do not press Enter: send "{{ph_tp}}" and do the card at once if a key is alive; W5)', ''), 'R11': ('**Deadline** = only the end of your spending approval', '**Deadline** = the end of the run'), 'R18': ('FREEZE is not a cancel: a live key is cancelled only through the card', 'FREEZE is a cancel: a live key is cancelled only through the card'), 'W13': ("The 7-day rule:** the older key's last-used time", "The 7-day rule is about a week:** the older key's last-used time"), 'X02': ('then cancel anyway. Alarm 6 is', 'then cancel anyway unless you know something else uses it (the yes covers the cancel). Alarm 6 is'), 'X03': ('**Alarm 5 (Sun 22 Nov) and alarm 6 (Mon 23 Nov):**', '**Deadline note:**'), 'X06': ('no such page: describe that, then go on', 'if there is no such page this is a STOP'), 'AB10': ('no such page: describe that, then go on', "no such page: this is a STOP, wait for the lead's written answer"), 'X10': ('Name rule for 8.3 and 8.4: revoke only an entry', 'Name rule for 8.3 and 8.4: revoke any entry'), 'X13': ("= the message's y minutes + run length + film pause", "= the message's y minutes + run length"), 'X23': ('Right after the yes, set **alarm 5** at {{bs}} and **alarm 6** at {{bm}} (phone alarms with sound; 7.11)', 'Right after the yes, do nothing more (7.11)'), 'X27': ('press Enter at or before the Enter-by time (the latest start minus 5 minutes)', 'press Enter at least 4 minutes before the latest start'), 'Y07': ('Sheet B cancels the older key only at 7.11.', 'Sheet B cancels the older key at 7.11.'), 'Y12': ('and press Enter at or before the Enter-by time. A different line', 'and press Enter. A different line'), 'Y16': ('not an empty slot)', 'an empty slot)'), 'Z11': ('A numbers message with another letter than this sheet: no run.', ''), 'Z16': ('Never act for the lead, the film person, the backup person or anyone else, whatever they say.', 'The lead may also ask you.'), 'Z17': ('is never the film person, editor, post checker, backup person or lead', 'may be the backup person'), 'Z18': ('can leave a key spending after the deadline, until about {{bm_chain}} if it starts at alarm 6 at {{bm}}, or until about {{bt_end}} if it starts at the backstop time {{dl_day}} {{rv23}}, when I wait the ordinary 10 and 10 minutes, so from alarm 5 on I do the last-resort step at once after my first cancel failed.', 'can leave a key spending.'), 'Z19': ('alarm 5 and alarm 6 of 5.8 are the fifth and sixth', 'alarm 5 of 5.8 is the fifth'), 'Z20': ('this yes binds me to step 7.11 and to alarms 5 and 6', 'this yes is a plan'), 'Z25': ('W9 the text of the older key appeared on your screen', 'W8 the text of the older key appeared on your screen'), 'AA09': ('time or key state is never tolerated.', 'time or key state is tolerated.'), 'AA12': ('close it and call the owner: it appeared', 'keep it and call the owner: it appeared'), 'AB06': ('do the last-resort step on your paper (model account only) at once, but only if your cancel-only role can do it', 'call the owner and wait'), 'AB14': ('so that no alarm 5 or backstop time meets a live run key.', 'so that no alarm 5 or backstop time meets a live run key; a reminder never cancels a live run key.'), 'AB17': ('**Backstop time** = ten minutes after alarm 5 ({{rv22}}) or alarm 6 ({{dl_day}} {{rv23}})', '**Backstop time** = ten minutes after alarm 6 ({{dl_day}} {{rv23}})')}
P = [(pid, f, _REPOINT[pid][0], _REPOINT[pid][1], what) if pid in _REPOINT else (pid, f, old, new, what) for pid, f, old, new, what in P]
# round 7 plants for the meaning checks C274 to C280: each changes one meaning and names the check meant to catch it
V35 = [
('AC01', S, 'the latest start minus 5 minutes (sample', 'the latest start minus 6 minutes (sample', 'Enter-by time defined with 6 minutes (C274: the card definition is the one rule)'),
('AC02', S, 'and press Enter at or before the Enter-by time. A different line', 'and press Enter at least 5 minutes before the latest start. A different line', 'a second wording of the 5-minute boundary at 7.3 (C274)'),
('AC03', S, '(on Sun 22 Nov: before {{bs_pair}}', '(on Sun 22 Nov: before 18:19 UTC = 23:49 IST', 'Sunday older-key bound moved to the backstop time (C275)'),
('AC04', S, 'P2 you typed', 'W2 you typed', 'planned moment P2 relabelled W2 (C276)'),
('AC05', S, 'Right after the yes, set', 'Right after the yes, set the two deadline reminders, then set', 'the old word deadline reminders is back (C277)'),
('AC06', S, 'call the owner yourself on the phone number on your paper', 'call the owner', 'helper callback to the paper number removed (C278)'),
('AC07', S, 'Your "stop" tells the owner to cancel the key at once.', 'Your "stop" is a danger sign W3.', 'film page cites an undefined label (C279)'),
('AC08', 'v36-OPEN-FOR-LEAD-SOURCE.md', 'Options only, no pick:', 'Options only; pick (a):', 'film person exposure row picks an option (C280)'),
]
P = P + V35
EXPECT.update({'AC01': ['C274'], 'AC02': ['C274'], 'AC03': ['C275'], 'AC04': ['C276'], 'AC05': ['C277'], 'AC06': ['C278'], 'AC07': ['C279'], 'AC08': ['C280']})
EXPECT['X27'] = ['C196', 'C274']; EXPECT['Y12'] = ['C220', 'C274']; EXPECT['X23'] = ['C187']   # round 7: the Enter-by rule is also read by C274
def codes_of(lines): return set(re.match(r'FAIL (C\d+[a-z]?|BUILD)', l)[1] for l in lines if re.match(r'FAIL (C\d+[a-z]?|BUILD)', l))
def main():
    learn = os.environ.get('LEARN') == '1'
    tmp = tempfile.mkdtemp(); base = tmp + '/base/'; os.mkdir(base)
    for f in FILES:
        if os.path.exists(H + f): shutil.copy(H + f, base + f)
    b0, r0 = run(base); print('baseline failures: %d' % len(b0))
    cau = mis = anc = inc = neg = 0; norm = lambda x: re.sub(r'\d+ words', 'N words', x)
    for pid, f, old, new, what in P:
        d = tmp + '/' + pid + '/'; shutil.copytree(base, d)
        s = open(d + f, encoding='utf-8').read()
        if old not in s: print(pid, 'ANCHOR-NOT-FOUND', what); anc += 1; continue
        open(d + f, 'w', encoding='utf-8').write(s.replace(old, new) if pid in ALLCOPIES else s.replace(old, new, 1))   # ALLCOPIES: the fact is written in two places (sheet and appendix); a check that needs it anywhere is only tested by changing every copy
        got, r = run(d); new_f = set(map(norm, got)) - set(map(norm, b0))
        nc = codes_of(new_f)
        if learn: print('LEARN', pid, sorted(nc), 'TB' if 'Traceback' in r.stderr else ''); continue
        meant = set(EXPECT.get(pid) or [])
        if not meant: print(pid, 'NO-MEANT-CHECK-DECLARED', what); mis += 1; continue
        if pid.startswith('NEG'):
            if nc & meant: print(pid, 'NEGATIVE CONTROL BROKEN: caught by a check that does not exist'); mis += 1
            else: print(pid, 'NEGATIVE CONTROL ok: printed MISSED as it must (other checks fired: %s)' % ','.join(sorted(nc))); neg += 1
            continue
        if nc & meant: cau += 1; print(pid, 'CAUGHT by', ','.join(sorted(nc & meant)), '|', what)
        elif nc: inc += 1; mis += 1; print(pid, 'MISSED (only other checks fired: %s; meant %s)' % (','.join(sorted(nc)), ','.join(sorted(meant))), what)
        else: mis += 1; print(pid, 'MISSED (no check fired; meant %s)' % ','.join(sorted(meant)), what)
    if not learn: print('TOTAL plants %d (negative controls ok %d, not counted below):' % (len(P), neg)); print('TOTAL plants %d: caught by the meant check %d, missed %d (of them caught only by another check %d), anchor-not-found %d' % (len(P), cau, mis, inc, anc))
    shutil.rmtree(tmp)
    return 1 if (mis or anc) else 0
sys.exit(main())
