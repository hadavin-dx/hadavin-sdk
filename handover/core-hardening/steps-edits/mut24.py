"""Planting test for check-v24.py. Each plant changes ONE thing in a scratch copy of a SOURCE (or facts) file, rebuilds, runs the checker;
CAUGHT = the checker prints a FAIL line that the unmodified package does not print. Prints caught and missed honestly."""
import os, re, shutil, subprocess, sys, tempfile
H = os.path.dirname(os.path.abspath(__file__)) + '/'
FILES = ['facts-v24.py', 'build-v24.py', 'check-v24.py', 'OWNER-SHEET-v24-SOURCE.md', 'LEAD-RELEASE-NOTE-v8-SOURCE.md', 'v24-OPEN-FOR-LEAD-SOURCE.md', 'v24-CHANGES.md']
def run(d):
    subprocess.run([sys.executable, '-B', d + 'build-v24.py', d], capture_output=True)
    r = subprocess.run([sys.executable, '-B', d + 'check-v24.py'], capture_output=True, text=True, env=dict(os.environ, V24_DIR=d))
    return set(l for l in r.stdout.split('\n') if l.startswith('FAIL')), r
# (id, file, old, new, what)
P = [
('P01', 'facts-v24.py', 'CEIL = 40000, 10000, 300, 1500, 3', None, ''),  # replaced below
]
P = [
('P01', 'facts-v24.py', 'P_OUT_C, CEIL = 40000, 10000, 300, 1500, 3', 'P_OUT_C, CEIL = 40000, 10000, 300, 1500, 4', 'call ceiling changed'),
('P02', 'facts-v24.py', 'LEDGER_C = 1240', 'LEDGER_C = 1250', 'ledger changed (limit 13.21 to 13.31)'),
('P03', 'facts-v24.py', 'NEED_S = 860', 'NEED_S = 864', '860 s changed'),
('P04', 'facts-v24.py', 'DEADLINE = dt.datetime(2026, 11, 23, 18, 29)', 'DEADLINE = dt.datetime(2026, 11, 23, 18, 30)', 'deadline minute'),
('P05', 'facts-v24.py', "IST = dt.timedelta(hours=5, minutes=30)", "IST = dt.timedelta(hours=5, minutes=0)", 'IST offset'),
('P06', 'facts-v24.py', "'dl_day': 'Mon 23 Nov 2026'", "'dl_day': 'Tue 23 Nov 2026'", 'weekday of deadline'),
('P07', 'facts-v24.py', "'postby': 'Wed 25 Nov 2026 15:00 UTC = 20:30 IST'", "'postby': 'Wed 25 Nov 2026 15:00 UTC = 20:00 IST'", 'post-by pair'),
('P09', 'OWNER-SHEET-v24-SOURCE.md', 'except the key\'s own one-time display at 6.3 and the paste at 6.4 (a long text anywhere else counts)', '', 'card (g) exception removed'),
('P10', 'OWNER-SHEET-v24-SOURCE.md', 'switch it OFF yourself at once with the tool the numbers message names', 'say "stop" and wait', 'recording stop by voice'),
('P11', 'OWNER-SHEET-v24-SOURCE.md', 'Three phone alarms on the run day, all in IST: one at the latest start, ', 'Two phone alarms on the run day, all in IST: ', 'third alarm removed'),
('P12', 'OWNER-SHEET-v24-SOURCE.md', 'Text between backticks is typed without the backticks. ', '', 'backtick sentence removed'),
('P13', 'OWNER-SHEET-v24-SOURCE.md', "only if the window's last line is `paste key, Enter:` (otherwise do not paste, copy a harmless word and tell in words what the last line says), ", '', 'paste condition removed'),
('P14', 'OWNER-SHEET-v24-SOURCE.md', 'and stick a paper note "READ" and "TEST" beside them', 'and keep them open', 'window labels removed'),
('P15', 'OWNER-SHEET-v24-SOURCE.md', 'ignore a `.used` ending', 'ignore nothing', '.used rule removed'),
('P16', 'OWNER-SHEET-v24-SOURCE.md', 'wait until the earliest key time has come, tell', 'tell', 'A older key cancelled early'),
('P17', 'OWNER-SHEET-v24-SOURCE.md', 'reverses the order of `end` and the card, ', '', 'lead may reverse order'),
('P18', 'OWNER-SHEET-v24-SOURCE.md', 'within {{y}} minutes of the time `date -u` shows when the notice appeared (note that time at once)', 'within the minutes the message names', 'no clock for the notice window'),
('P19', 'OWNER-SHEET-v24-SOURCE.md', 'if 7.4 never happened, tell "none" for the time in 8.1. ', '', 'run that never started'),
('P20', 'OWNER-SHEET-v24-SOURCE.md', 'SAMPLE (made-up values, never real):\n', '', 'SAMPLE label removed'),
('P21', 'OWNER-SHEET-v24-SOURCE.md', 'never use rotate or any button that shows a new secret', 'rotate the secret', 'HubSpot rotate allowed'),
('P22', 'OWNER-SHEET-v24-SOURCE.md', 'or "{{ph_nokey}}" (allowed only if', 'or "no key made" (allowed only if', 'set phrase differs'),
('P23', 'OWNER-SHEET-v24-SOURCE.md', 'weekday, month, day and year must equal the run day', 'month and day must equal the run day', 'full date check weakened'),
('P24', 'OWNER-SHEET-v24-SOURCE.md', 'the balance and auto-reload equal your yes (R4)', 'the balance looks fine (R4)', 'balance re-check weakened'),
('P25', 'OWNER-SHEET-v24-SOURCE.md', 'last-resort step <step>. ', '', 'last-resort step out of the yes'),
('P26', 'OWNER-SHEET-v24-SOURCE.md', 'one line only: a second', 'a second', 'one-line warning removed'),
('P27', 'OWNER-SHEET-v24-SOURCE.md', 'press the cancel button; if a box asks', 'press the cancel button (or at 7.8 click cancel); if a box asks', 'cancel rule is copied on top of the card'),
('P29', 'OWNER-SHEET-v24-SOURCE.md', '8.3 and 8.4 say where', '8.3 and 8.9 say where', 'pointer to missing step'),
('P30', 'OWNER-SHEET-v24-SOURCE.md', '**Key list** = the model account page', '**Key liszt** = the model account page', 'card term renamed'),
('P31', 'OWNER-SHEET-v24-SOURCE.md', 'Never "Select all", never empty Trash', 'Select all is fine', 'delete guard removed'),
('P32', 'OWNER-SHEET-v24-SOURCE.md', '**STOP RULE.**', '**RULE.**', 'STOP RULE renamed'),
('P33', 'OWNER-SHEET-v24-SOURCE.md', 'only letters, digits, single spaces and `. _ / - : = @ + ,`', 'only letters, digits, single spaces and `. _ / - : = @ + , !`', 'noop on yes charset (expected MISSED if yes unchanged)'),
('P34', 'OWNER-SHEET-v24-SOURCE.md', 'I accept the risks of R1 and R4:', 'I accept the risks of R1 and R4; (ok):', 'yes pattern gets a bracket char'),
('P35', 'OWNER-SHEET-v24-SOURCE.md', 'echo "exit $?"', 'echo exit', 'key-save line loses exit report'),
('P36', 'OWNER-SHEET-v24-SOURCE.md', 'set -C; umask 077; read -rs', 'set -C; umask 077; read -rs; (', 'key-save line breaks bash -n'),
('P37', 'LEAD-RELEASE-NOTE-v8-SOURCE.md', 'the final check', 'the re-pin', 'stale word back in note'),
('P38', 'LEAD-RELEASE-NOTE-v8-SOURCE.md', '14.33', '14.4', 'old minutes figure in note'),
('P39', 'LEAD-RELEASE-NOTE-v8-SOURCE.md', '18:19:00 UTC = 23:49 IST', '18:19:00 UTC = 23:59 IST', 'wrong pair in note'),
('P40', 'v24-OPEN-FOR-LEAD-SOURCE.md', 'Mon 16 Nov 2026', 'Tue 16 Nov 2026', 'wrong weekday in open list'),
('P41', 'v24-OPEN-FOR-LEAD-SOURCE.md', 'the card', 'card Part 2', 'Part 2 back in open list'),
('P43', 'OWNER-SHEET-v24-SOURCE.md', 'Mon 16 Nov 2026', 'Mon 17 Nov 2026', 'sheet date weekday'),
('P44', 'OWNER-SHEET-v24-SOURCE.md', '[[A: I will cancel the older key myself', '[[A: I will cancel the older key soon', 'A yes sentence changed'),
('P45', 'OWNER-SHEET-v24-SOURCE.md', 'Without (i) or (ii) the older key stays valid.', '', 'B older key fate removed'),
]
def main():
    tmp = tempfile.mkdtemp(); base = tmp + '/base/'; os.mkdir(base)
    for f in FILES:
        if os.path.exists(H + f): shutil.copy(H + f, base + f)
    b0, r0 = run(base); print('baseline failures: %d' % len(b0))
    cau = mis = anc = 0
    for pid, f, old, new, what in P:
        d = tmp + '/' + pid + '/'; shutil.copytree(base, d)
        s = open(d + f, encoding='utf-8').read()
        if old not in s: print(pid, 'ANCHOR-NOT-FOUND', what); anc += 1; continue
        open(d + f, 'w', encoding='utf-8').write(s.replace(old, new, 1))
        got, r = run(d); norm = lambda x: re.sub(r'\d+ words', 'N words', x); new_f = set(map(norm, got)) - set(map(norm, b0))
        if old == new: new_f = set()
        if new_f or 'Traceback' in r.stderr or 'rror' in r.stderr[:200]: cau += 1; print(pid, 'CAUGHT', what, '|', (sorted(new_f) or [r.stderr[-80:]])[0][:90])
        else: mis += 1; print(pid, 'MISSED', what)
    print('TOTAL plants %d: caught %d, missed %d, anchor-not-found %d' % (len(P), cau, mis, anc))
    shutil.rmtree(tmp)
main()
