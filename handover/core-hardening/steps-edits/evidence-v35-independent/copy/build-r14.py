"""Round 14 builder: anchored patches of EDITS.md (every old string asserted to occur exactly once).
Reads EDITS.round13.md, writes EDITS.md. No vendor words, no secrets."""
import re, sys
D = '/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
T = open(D + 'EDITS.round13.md', encoding='utf-8').read()
errs = []

def sub(old, new, n=1):
    global T
    c = T.count(old)
    if c != n:
        errs.append(f'anchor count {c} (want {n}): {old[:70]!r}'); return
    T = T.replace(old, new)

def row_span(rid):
    i = T.index(f'\n### {rid}: ') + 1
    m = re.compile(r'\n### E-\d\d: |\n## Lines checked and found consistent').search(T, i + 5)
    return i, (m.start() + 1 if m else len(T))

def rsub(rid, old, new, n=1):
    global T
    i, j = row_span(rid)
    seg = T[i:j]
    c = seg.count(old)
    if c != n:
        errs.append(f'{rid}: anchor count {c} (want {n}): {old[:70]!r}'); return
    T = T[:i] + seg.replace(old, new) + T[j:]

def why_add(rid, text):
    global T
    i, j = row_span(rid)
    lines = T[i:j].split('\n')
    idx = [n for n, l in enumerate(lines) if l.startswith('Why:')]
    if len(idx) != 1:
        errs.append(f'{rid}: Why lines {len(idx)}'); return
    lines[idx[0]] = lines[idx[0]].rstrip() + ' ' + text
    T = T[:i] + '\n'.join(lines) + T[j:]

def set_why(rid, text):
    global T
    i, j = row_span(rid)
    lines = T[i:j].split('\n')
    idx = [n for n, l in enumerate(lines) if l.startswith('Why:')]
    if len(idx) != 1:
        errs.append(f'{rid}: Why lines {len(idx)}'); return
    lines[idx[0]] = text
    T = T[:i] + '\n'.join(lines) + T[j:]

def _find_new(lines, nth):
    n_new = -1
    for k, l in enumerate(lines):
        if re.match(r'^NEW[^\n]*:$', l) and k + 1 < len(lines) and lines[k + 1] == '~~~~':
            n_new += 1
            if n_new == nth:
                e = k + 2
                while lines[e] != '~~~~': e += 1
                return k + 2, e
    return None

def set_new(rid, body, nth=0):
    global T
    i, j = row_span(rid)
    lines = T[i:j].split('\n')
    r = _find_new(lines, nth)
    if not r: errs.append(f'{rid}: NEW block {nth} not found'); return
    lines[r[0]:r[1]] = body.split('\n')
    T = T[:i] + '\n'.join(lines) + T[j:]

def edit_new(rid, pairs, nth=0):
    global T
    i, j = row_span(rid)
    lines = T[i:j].split('\n')
    r = _find_new(lines, nth)
    if not r: errs.append(f'{rid}: NEW block {nth} not found'); return
    body = '\n'.join(lines[r[0]:r[1]])
    for old, new in pairs:
        c = body.count(old)
        if c != 1:
            errs.append(f'{rid} NEW: anchor count {c}: {old[:70]!r}'); return
        body = body.replace(old, new)
    lines[r[0]:r[1]] = body.split('\n')
    T = T[:i] + '\n'.join(lines) + T[j:]

def sub_line(prefix, newline):
    """replace the whole line that starts with prefix (exactly one)"""
    global T
    ls = T.split('\n')
    idx = [k for k, l in enumerate(ls) if l.startswith(prefix)]
    if len(idx) != 1:
        errs.append(f'line prefix count {len(idx)}: {prefix[:50]!r}'); return
    ls[idx[0]] = newline
    T = '\n'.join(ls)

def block_get(rid, nth=0):
    i, j = row_span(rid)
    lines = T[i:j].split('\n')
    r = _find_new(lines, nth)
    return lines[r[0]:r[1]]


exec(open(D + 'build-r14-e48.py', encoding='utf-8').read())

PH = '`[LEAD FILLS at re-pin: start time of day for Wed 18 Nov 2026, in UTC and IST]`'
FALLBACK = (' If this is still in square brackets when you read it, the time of day is not yet chosen: the assistant then proposes a time of day, in UTC and IST, that is not later than the latest start we plan, and you answer it before any take; no take starts on a guess.')

# ---------------- header ----------------
sub('exact edit list (round 13, batched fix pass after the round 12 reviews;', 'exact edit list (round 14, batched fix pass after the round 13 reviews;')
sub('Round 13 (`resolve-r13.md`, same paths: no round cap) applies all of those findings in one batch. The result of round 13 is NOT reviewed yet.',
    'Round 13 (`resolve-r13.md`, same paths: no round cap) applied all of those findings in one batch; its result was reviewed (`review-r13-security.md`: 0 Blockers, 8 Majors, minors; `review-r13-naive.md`: 1 Blocker, 5 Majors, about 14 minors; independent evidence `review-r13-evidence.md` and `evidence-r13-independent/00-SUMMARY.md`). Round 14 (`resolve-r14.md`, same paths: no round cap) applies all of those findings in one batch. The result of round 14 is NOT reviewed yet.')
sub('`resolve-r13.md` and `resolve-r13-check-output.txt`)', '`resolve-r14.md` and `resolve-r14-check-output.txt`)')
sub('Round 13 added no row (the ids and the counts do not change). It rewrote E-09,',
    'Round 14 added no row (the ids and the counts do not change). It rewrote E-48 (new parts 3a to 3j), E-09, E-12, E-16, E-37, E-52, E-54, E-55 and E-57, renamed the plan\'s numbered tests "test items" and the counting program, and rewrote NOT DECIDED 9 and 15, the rules R7, R10 and R11, the confirmations h, m and n, and added the confirmation o. Round 13 added no row (the ids and the counts do not change). It rewrote E-09,')
sub('letters run a to n without gaps', 'letters run a to o without gaps')
sub('`EDITS.round12.md` (round 12).', '`EDITS.round12.md` (round 12) and `EDITS.round13.md` (round 13).') if 'EDITS.round12.md` (round 12).' in T else None

# words list: start-time labels and counting program
sub('so a start at that time ends before the last time to revoke).',
    'so a start at that time ends about 40 seconds before the last time to revoke, on a duration that is a reading and not measured: confirmation o).')
sub('about 18:14 UTC = 23:44 IST on 23 Nov, the time from which', 'about 18:14 UTC = 23:44 IST on 23 Nov (18:14:40 UTC = 23:44:40 IST, if the 860 seconds are right: the end of the spending window minus 860 seconds), the time from which')
T = T.replace('counting check', 'counting program')

# ND9, ND15
sub('Default: (a). Record: `ND9: a|b`.', 'Round 14 note: in route B of ND15 the file (and the key copy, E-48 part 3f) lives up to five days, not hours; the default (a) was set for hours, so the studio lead decides again if route B is chosen. Default: (a). Record: `ND9: a|b`.')
sub('and puts the recommendation in ONE sentence of E-48 part 3c ("The assistant recommends route B; the choice is yours") that the studio lead keeps, changes to A or deletes.',
    'and puts the recommendation in ONE sentence of E-48 part 3c ("the assistant recommends route B") that the studio lead keeps, changes to A or deletes. The spots that carry the recommendation, so that all change together: E-48 part 3c, that one sentence only; E-57 and E-52 are neutral (round 14 removed "(the one the assistant recommends)" and "(recommended)"). The owner selects the route by ONE message, `route A` or `route B` (E-48 part 3c); the words `no more takes` alone do not select it, because their effect depends on the time of the message.')
sub('Default: not chosen (see the conflict); until the studio lead answers, both routes are in the owner text with the recommendation sentence as written.', 'Default: not chosen (see the conflict); until the studio lead answers, both routes are in the owner text with the one recommendation sentence as written.')

# confirmations
sub('The 18:14 UTC = 23:44 IST (the program refusal limit) stays a reading of line 171, UNVERIFIED by code.',
    'The 18:14 UTC = 23:44 IST (the program refusal limit) stays a reading of line 171, UNVERIFIED by code. The margin that follows from the latest start we plan (18:04 UTC = 23:34 IST) is NOT confirmed: see o.')
sub('Confirm the narrowing and the figure, or restore Q19.5 in full.',
    'Confirm the narrowing and the figure, or restore Q19.5 in full. Round 14: the two choices of the item L-A/B are named `revoke it` and `leave it` in the owner text (not route A and route B, which belong to NOT DECIDED 15 only), so L-A/B is followed in meaning and not word for word; confirm.')
sub('Confirm the widening and the wording.',
    'Round 14 widens it again (security M-E): the sentence also names the copy of the secret key for the model in the take folder and the files in `~/take-secrets`, which the same Linux user can read. Confirm the widening and the wording.')
sub('E-12 widens the yes sentence beyond Q24: "and that it can reach n8n\'s encryption key and the credentials saved in the take\'s n8n".',
    'E-12 widens the yes sentence beyond Q24: "and that it can reach n8n\'s encryption key, the credentials saved in the take\'s n8n, the copy of the secret key for the model in the take folder and the files in `~/take-secrets`".')
sub_line('n. E-12 widens', T.split('\n')[[k for k,l in enumerate(T.split('\n')) if l.startswith('n. E-12 widens')][0]] + '\no. The latest start we plan (18:04 UTC = 23:34 IST) leaves about 40 seconds before the last time to revoke (18:19 UTC = 23:49 IST) if the take lasts 860 seconds; 860 seconds is a reading of the take program, not measured, and the margin ignores the time to type `y`, the confirmation number and the take id. If the real duration is 15 minutes the take ends at 18:19 UTC = 23:49 IST or a few seconds later, and route B leaves no time to watch the cut. Decide: move the latest start we plan (18:04 UTC = 23:34 IST) earlier, for example to 18:00 UTC = 23:30 IST (a figure I propose and cannot check), or accept the margin; until then the owner text says "about 40 seconds, on a duration that is not measured".')

# R7, R10, R11
sub('The key ends by 18:19 UTC = 23:49 IST on Mon 23 Nov 2026 in every case. The owner\'s alarm for 17:49 UTC = 23:19 IST (part 3b) is the only reminder on that day (the program has no timer, Q26); if a session of the assistant is open at that time it asks "Is the key revoked?" first.',
    'The key ends by 18:19 UTC = 23:49 IST on Mon 23 Nov 2026 in every case. The owner\'s two alarms (part 3b: 17:49 UTC = 23:19 IST on 23 Nov, and a repeating evening alarm from the first take) are the only reminders (the program has no timer, Q26); if a session of the assistant is open at the first alarm it asks "Is the key revoked?" first. The studio lead checks in the chat record that the assistant gave the owner the full paths and the steps (part 3d) and that item 1 started only after `key revoked` (or `key not revoked`) and `shred done` (or `shred not done`).')
sub('before the sheet is given to the owner, the studio lead fills the placeholder', 'before the sheet is given to the owner, the studio lead fills the placeholder (if it stays unfilled, the fallback sentence that follows the placeholder in E-12 and E-54 applies; the owner is not asked to read it as a time)')

# ---------------- E-48 ----------------
set_new('E-48', E48_NEW)
why_add('E-48', 'Round 14 (security M-A to M-F, M-H, minors; naive B1, M1, M2, M4, M6, minors; independent evidence r13): (a) ONE message selects the route, `route A` or `route B`; `no more takes` alone does not (3c); the recommendation is ONE sentence there; in route B the assistant asks again after `cut accepted`; the reply `more takes` or silence on the last take in route B is stated; (b) a revoke at the last time to revoke counts as `no more takes` and `cut accepted` (3c, 3d, M-A); (c) the owner sets a second, repeating alarm and the text calls the rule a promise and a procedure, not a control (3a, 3b, M-C); (d) 3h has a default when the owner is still unsure at the deadline (revoke the one key made for this take, M-B) and E-37 asks him to write the name and last four characters first; (e) ONE shred rule for every file, with the path checks (full path, no `..`, no space or `*`, `realpath`, `ls -l` with one name, trailing `/` for the take folder) and the item 6 `*` is replaced by file-by-file shredding (3f and the closing paragraph, M-D); (f) the clean-up (item 1) waits for `key revoked` or `key not revoked`, and `shred done` or `shred not done` (3f, naive B1); (g) costs of route A and route B are written completely (3c, M4); (h) 3i names its two options `revoke` and `leave` (confirmation m); (i) 3j no longer says "unless the assistant tells you otherwise" (naive M1); (j) the new key made in 3g lives only in the program that uses it and its file is shredded (M-F); (k) the alarm names say "secret key for the model" (naive minor). The new text is one block (item 3 with parts 3a to 3j). The old text is unchanged. Not proven: that the key list shows the last four characters, the click paths, shred on this disk, how the take behaves when its key is revoked.')

# ---------------- E-12 ----------------
edit_new('E-12', [
 ('how their checks ended, in numbers. A check is one numbered test on the plan\'s list of checks.', 'how their test items ended, in numbers. A test item is one numbered test on the plan\'s list of test items.'),
 ('N1 is the number of checks of the stand-in test that ended "pass"', 'N1 is the number of test items of the stand-in test that ended "pass"'),
 ('Each must equal the number of checks on that test\'s list, not counting the crash check', 'Each must equal the number of test items on that test\'s list, not counting the crash check'),
 ('"Failed" means the check ran and showed a bad result. "Missed" means the check ran but could not see what it was looking for. "Not run" means the check was never carried out.', '"Failed" means the test item ran and showed a bad result. "Missed" means the test item ran but could not see what it was looking for. "Not run" means the test item was never carried out.'),
 ('- The list of checks of the plan, attached to the request.', '- The list of test items of the plan, attached to the request.'),
 ('`[LEAD FILLS at re-pin: start time of day for Wed 18 Nov 2026, in UTC and IST]`. The request states', PH + '.' + FALLBACK + ' The request states'),
 ('That margin is small, so the planned start for Wed 18 Nov is much earlier.', 'That margin is only about 40 seconds and rests on the 860 seconds, which is a reading and not measured; if the real take lasts 15 minutes it ends at 18:19 UTC = 23:49 IST or a few seconds later, which is too late, and a take that ends at 18:18 leaves you no time to watch the cut before 18:19 in route B. The assistant asks the studio lead to confirm this margin or to move the latest start we plan (18:04 UTC = 23:34 IST) earlier. The planned start for Wed 18 Nov is much earlier.'),
 ('Set an alarm on your own phone or computer for 17:49 UTC = 23:19 IST on Mon 23 Nov 2026 and name it `revoke the model key`: the assistant', 'Set two alarms on your own phone or computer (step 22 item 3, part 3b): alarm 1 for 17:49 UTC = 23:19 IST on Mon 23 Nov 2026, named `revoke the secret key for the model`, and alarm 2, which repeats every evening from the day of your first take, named `is the secret key for the model still alive?`. This is a promise by you backed by your alarms, not a control: the assistant'),
 ('"Passed" means both of these: every check ended "pass"', '"Passed" means both of these: every test item ended "pass"'),
 ('A check that ended "failed", "missed" or "not run" is not a pass.', 'A test item that ended "failed", "missed" or "not run" is not a pass.'),
 ('`<N1>` is the number that the request gives for the checks of the stand-in test that ended "pass"', '`<N1>` is the number that the request gives for the test items of the stand-in test that ended "pass"'),
 ('encryption key and the credentials saved in the take\'s n8n."\n- `<take id>`', 'encryption key, the credentials saved in the take\'s n8n, the copy of the secret key for the model in the take folder and the files in `~/take-secrets`."\n- `<take id>`'),
 ('encryption key and the credentials saved in the take\'s n8n.", is REQUIRED', 'encryption key, the credentials saved in the take\'s n8n, the copy of the secret key for the model in the take folder and the files in `~/take-secrets`.", is REQUIRED'),
 ('so they can read every file that you can read.', 'so they can read every file that you can read. That includes the copy of the secret key for the model that you place in the take folder, the two files in `~/take-secrets` (the app password of the receiver mailbox and the HubSpot read secret key), and anything that Docker or the Linux part of your laptop (WSL) keeps under your user.'),
 ('If a take is still running at 18:19 UTC = 23:49 IST, you revoke the secret key for the model anyway (step 22 item 3, part 3j);', 'If a take is still running at 18:19 UTC = 23:49 IST, you revoke the secret key for the model at that time, whatever the assistant says (step 22 item 3, parts 3h and 3j);'),
])
why_add('E-12', 'Round 14 (security M-C, M-E, M-G, minors; naive M1, M3, M5, M6): (a) the numbered tests of the plan are called "test items" here and in E-52 (the word "check" no longer means a numbered test; the crash check keeps its name); (b) the yes sentence and its explanation also name the copy of the key in the take folder, the files in `~/take-secrets` and what Docker and WSL keep under the owner\'s user (confirmation n); (c) the 40-second margin is said plainly, with the 15-minute case, and the assistant asks the studio lead to confirm or move the start (confirmation o); (d) two alarms (E-48 part 3b); (e) the placeholder stays, with a stated fallback sentence (rule R11); (f) "revoke anyway" has one instruction: whatever the assistant says (naive M1). Not done: the placeholder is not filled (it needs the studio lead); the long one-line reply with many parts and the example `1.50` (naive minor) are not changed because the form is checked part by part.')

# ---------------- E-09 ----------------
edit_new('E-09', [
 ('(2) type the secret by hand, or paste it and then copy any made-up word so that the clipboard no longer holds it; (3)', '(2) type the secret by hand, or paste it and then copy any made-up word, and then open the Windows clipboard history (press the Windows key and V together) and delete the entry that holds the secret, or turn the clipboard history off (Settings, System, Clipboard; this click path is not checked); if you use a clipboard manager program, empty its history too; (3)'),
 ('Do it now for the first time: write `please stop looking` and wait for `not looking`.', 'Do it now for the first time: write `please stop looking` and wait for `not looking`. The wait is part of the rule every time: type nothing secret before you have the reply `not looking`.'),
 ('and shred the old file (`shred -u <old password file name>`; if shred is not installed, `rm <old password file name>`).', 'and shred the old file by the shred rule of step 22 item 3, part 3f (full path, the checks, then `shred -u`).'),
 ('apply the typing rule (parts 1 and 3 are at the start and the end of this sub-step); open a WSL terminal;', 'apply the typing rule (write `please stop looking`, wait for `not looking`, and at the end write `you may look again`); open a WSL terminal;'),
 ('press Ctrl+X to close nano without changing anything (if nano asks whether to save, press N).', 'press Ctrl+X to close nano without changing anything (if nano asks whether to save, press N), then type `clear` and press Enter so that the password does not stay on the screen of the terminal.'),
 ('afterwards copy any made-up word, so that the clipboard no longer holds the password.', 'afterwards copy any made-up word and delete the entry in the Windows clipboard history (see sub-step a).'),
 ('Instead: apply the typing rule; in the WSL terminal, in the same folder, type `nano n8n.env` and press Enter;', 'Instead: apply the typing rule (write `please stop looking` and wait for `not looking`); in the WSL terminal, in the same folder, type `umask 077` and press Enter (a new terminal window forgets it), then type `nano n8n.env` and press Enter;'),
 ('write `n8n.env done; you may look again`.', 'type `clear` and press Enter; write `n8n.env done; you may look again`.'),
 ('Which HubSpot private app the key must come from is UNVERIFIED (app 2, see the words list); the assistant tells you before you type. Each of the two typings is a separate typing rule, with its own `please stop looking`.', 'Which HubSpot private app the key must come from is UNVERIFIED (app 2, see the words list); the assistant tells you before you type. Use the key of app 1 (read only) unless the assistant tells you in writing why the key of app 2 is needed; the key of app 2 may write to contacts (UNVERIFIED), so ask before you type it. Each of the two typings is a separate typing rule, with its own `please stop looking` and its own wait for `not looking`.'),
])
why_add('E-09', 'Round 14 (security M-F, minors; evidence r13): each typing (f, g, h) now says in its own words to write `please stop looking` and to wait for `not looking`; the Windows clipboard history and clipboard managers are named (a cleared clipboard is not enough); `clear` after nano and `umask 077` before the second nano are added; the old password file is shredded by the one shred rule; the HubSpot key is the read-only one unless the assistant explains in writing why not. Not proven: the Windows click path, that `clear` removes the scrollback of every terminal program.')

# ---------------- E-16 ----------------
edit_new('E-16', [
 ('starts it only after you have written `no more takes` in the chat (in route B of step 22 item 3, part 3c, also after `cut accepted`), because none of it can be undone', 'starts it only after you have written `no more takes` in the chat (in route B of step 22 item 3, part 3c, also after `cut accepted`) and after you have written `key revoked` (or `key not revoked` and the reason) and `shred done` (or `shred not done` and the reason) for the secret key for the model (step 22 item 3, parts 3f and 3h), because none of it can be undone and because removing the take folder ends the path to the copy of the key that you shred'),
 ('If a part is not done, it tells you before you start your own steps (the numbered items 2 to 6 that follow this item).', 'If a part is not done, it tells you before you do your own items 2, 4, 5 and 6 (your item 3 comes first, because it revokes the key and shreds its copy).'),
 ('It touches no other container.', 'It touches no other container. Which folder: only the take folder, by the full path that it recorded when the run began. It removes nothing if that path is your home folder, is under `/mnt/c`, is outside the take root that it recorded, contains `..`, or is or contains a link (a link is a shortcut to another place); a link inside the take folder is removed as a link and never followed.'),
])
why_add('E-16', 'Round 14 (security M-H; naive B1): item 1 now waits for `key revoked` (or `key not revoked`) and `shred done` (or `shred not done`), so the path to the copy of the key still exists when the owner shreds it; the delete path has rules (recorded full path, refuse home folder, `/mnt/c`, outside the recorded root, `..`, links); "before you start your own steps" no longer contradicts item 3 first. Not verified: that the clean-up program enforces these path rules (they are a written instruction to the assistant, not a program check).')
sub('| E-16 | OWNER-STEPS-realrun-v3.md | 121 | Apply now | - | ND3 (default text) | STALE |', '| E-16 | OWNER-STEPS-realrun-v3.md | 121 | Apply now | - | ND3 (default text); E-48, E-55 (order) | STALE |')

# ---------------- E-37 ----------------
edit_new('E-37', [
 ('You then know both answers before the take day.', 'You then know both answers before the take day. Also, before the take, write down on paper or on your phone (never in a file on this laptop and never in the chat) the NAME of the secret key for the model and the LAST FOUR CHARACTERS of it as the key list shows them (whether the list shows the last four characters is UNVERIFIED; if it shows none, write the name and the day you made the key). Step 22 item 3, part 3h uses this note. If you have no note on the day, you revoke the one key that you made for this take, and no other.'),
])
why_add('E-37', 'Round 14 (security M-B; naive M2): the owner writes the key name and the last four characters before the take, and the text says what to do without the note. Not verified: that the key list shows the last four characters.')

# ---------------- E-52 ----------------
edit_new('E-52', [
 ('type it by hand, or paste it and then copy any made-up word so that the clipboard no longer holds it; then write `you may look again`.', 'type it by hand, or paste it, copy any made-up word and delete the entry in the Windows clipboard history (Windows key and V); then write `you may look again`.'),
 ('**Route A and route B**: the two ways of timing your `no more takes` (step 22 item 3, part 3c).', '**Route A and route B**: the two ways of timing your `no more takes` (step 22 item 3, part 3c); you choose one by writing `route A` or `route B` in the chat once, before your last take.'),
 ('**A check**: one numbered test on the plan\'s list of checks.', '**A test item**: one numbered test on the plan\'s list of test items (step 16). **The counting program**: our small program that counts mails, contacts and table rows (it is not part of n8n). **The assistant\'s own checks** are what the assistant does itself to see that something is right; none of them is a test item.'),
])
why_add('E-52', 'Round 14 (naive M6; security M-F): "check" is split into test item, counting program and the assistant\'s own checks; the route is chosen by one message; the clipboard history is named; the word "recommended" is not used here.')

# ---------------- E-54 ----------------
rsub('E-54', PH + ', and the assistant confirms', PH + '.' + FALLBACK + ' The assistant confirms')
why_add('E-54', 'Round 14 (naive M3): the placeholder stays and a stated fallback sentence follows it (rule R11).')

# ---------------- E-55 ----------------
edit_new('E-55', [
 ('NEEDS-OWNER. The assistant starts item 1 below only after you have written `no more takes` in the chat (in route B also after `cut accepted`): item 1 deletes', 'NEEDS-OWNER. Nothing in this step is done before you have written `no more takes` in the chat (in route B also after `cut accepted`). That holds for the assistant\'s item 1 and for your items 2 to 6 (deleting the HubSpot apps, deleting the app passwords and shredding the files in `~/take-secrets` make a retake impossible). The one exception is the last time to revoke the secret key for the model: at 18:19 UTC = 23:49 IST on Mon 23 Nov 2026 you revoke it, and your `key revoked` then counts as `no more takes` (and, in route B, as `cut accepted`). The assistant starts item 1 only after you have also written `key revoked` (or `key not revoked` and the reason) and `shred done` (or `shred not done` and the reason). Item 1 deletes'),
])
why_add('E-55', 'Round 14 (security M-A, M-H; naive B1): the owner\'s own irreversible items 2 to 6 also wait for `no more takes` (and `cut accepted` in route B); a forced revoke at the last time counts as both; item 1 waits for the key and shred replies so that the shred path still exists.')
sub('| E-55 | OWNER-STEPS-realrun-v3.md | 119 (and 120) | Apply now | - | E-48 | CONTRADICTION |', '| E-55 | OWNER-STEPS-realrun-v3.md | 119 (and 120) | Apply now | - | E-48, E-16 | CONTRADICTION |')

# ---------------- E-57 ----------------
edit_new('E-57', [
 ('Two routes (step 22 item 3, part 3c). Route A:', 'Two routes. You choose one by writing `route A` or `route B` in the chat once, before your last take (step 22 item 3, part 3c). Route A:'),
 ('Route B (the one the assistant recommends): you have not written', 'Route B: you have not written'),
 ('no further take is possible with that key: you would first make a new secret key and give a new yes (step 20).', 'no further take is possible with that key: you would first make a new secret key and give a new yes (step 20). Route A also costs more than the key: after `no more takes` the assistant\'s clean-up has removed the take\'s n8n set-up and you have deleted the HubSpot apps and the app passwords, so a retake needs a whole new set-up (new HubSpot apps with a new secret key, new app passwords, a new key for the model and a new yes).'),
])
why_add('E-57', 'Round 14 (security minor; naive M4): the recommendation is not repeated here (ONE place: E-48 part 3c); the route is chosen by the message `route A` or `route B`; the full cost of route A is stated.')

T = T.rstrip('\n') + '\n- Round 14 added: nothing was run except text, count and weekday checks by script (`resolve-r14-check-output.txt`; `verify14.py` has negative controls, among them the seven mutations that `verify13.py` missed). I did not run any program of the take, did not read the take code, and did not check any click path (the Windows clipboard history, the key list of the model provider and whether it shows the last four characters, the page to revoke a key). The new parts 3a to 3j, the shred rule, the path rules of the clean-up and the two alarms are written instructions: none of them is enforced by a program, and no test showed that an owner can follow them. Not decided by me: the route recommendation (NOT DECIDED 15), the margin of the latest start we plan (18:04 UTC = 23:34 IST; confirmation o), the placeholder fill (rule R11), whether the owner reads AGENT-SCOPE, and whether the old step 22 item 6 (`shred -u ~/take-secrets/*`) and the old lines 144 and 171 of the input need their own rows (see `resolve-r14.md`). Finding ids that are not fixed or only partly fixed are listed in `resolve-r14.md` with the reason.\n'

open(D+'EDITS.md','w', encoding='utf-8').write(T)
print('errors:', len(errs))
for e in errs: print(' ', e)
sys.exit(1 if errs else 0)
