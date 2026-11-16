"""Round 14 builder: anchored patches of EDITS.md (every old string asserted to occur exactly once).
Reads EDITS.round14.md, writes EDITS.md. No vendor words, no secrets."""
import re, sys
D = '/home/user/hadavin-sdk/handover/core-hardening/steps-edits/'
T = open(D + 'EDITS.round14.md', encoding='utf-8').read()
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



exec(open(D + 'build-r15-e48.py', encoding='utf-8').read())

def set_block_line(rid, prefix, newtext, nth=0):
    global T
    i, j = row_span(rid)
    lines = T[i:j].split('\n')
    r = _find_new(lines, nth)
    if not r: errs.append(f'{rid}: NEW block not found'); return
    idx = [k for k in range(r[0], r[1]) if lines[k].startswith(prefix)]
    if len(idx) != 1:
        errs.append(f'{rid}: line prefix count {len(idx)}: {prefix[:50]!r}'); return
    lines[idx[0]:idx[0]+1] = newtext.split('\n')
    T = T[:i] + '\n'.join(lines) + T[j:]

R15WHY = ' Round 15 (security M1, M2, M3, minors; naive M1 to M9, minors; evidence r14): '

# ---------------- header ----------------
sub('exact edit list (round 14, batched fix pass after the round 13 reviews;', 'exact edit list (round 15, batched fix pass after the round 14 reviews;')
sub('`resolve-r14.md` and `resolve-r14-check-output.txt`)', '`resolve-r15.md` and `resolve-r15-check-output.txt`)')
sub('56 rows in total: E-01 to E-58 without E-10 and E-35. By file: OWNER-STEPS 37 rows,', '59 rows in total: E-01 to E-61 without E-10 and E-35. By file: OWNER-STEPS 40 rows,')
sub('**Apply now 44**', '**Apply now 47**')
sub('The Apply now ids (44) are:', 'The Apply now ids (47) are:')
sub('E-56, E-57, E-58. Round 14 added no row (the ids and the counts do not change).', 'E-56, E-57, E-58, E-59, E-60, E-61. Round 15 added E-59 (step 22 item 6, the old shred command with the sign `*`), E-60 (two UTC times without IST in the take-start paragraph, input line 171) and E-61 (the old date "By Mon 16" in the send table, input line 144), and rewrote E-48 (the lettered steps are now key steps A to K; the old parts 3a to 3j are A, C, D, E, F, G, H, I, J, K, with the new key step B), E-09, E-12, E-16, E-37, E-52, E-54, E-55 and E-57, the rules R7 and R11, ND15 and the confirmations h and o, and added the confirmation p. Round 14 added no row (the ids and the counts do not change).')
sub('STALE 15, UNCLEAR WORD 10, MISSING STEP 14, CONTRADICTION 16 (including', 'STALE 16, UNCLEAR WORD 11, MISSING STEP 14, CONTRADICTION 17 (including')
sub('DEFERRED 1 (E-13); total 56.', 'DEFERRED 1 (E-13); total 59.')
sub('letters run a to o without gaps', 'letters run a to p without gaps')

# the latest start we plan: 18:00 UTC = 23:30 IST
sub('**latest start we plan** = 18:04 UTC = 23:34 IST, the latest time at which the assistant asks for a take to start (confirmed by the studio lead, item L-23NOV; the take needs about 14 minutes 20 seconds, 860 seconds, so a start at that time ends about 40 seconds before the last time to revoke, on a duration that is a reading and not measured: confirmation o).',
    '**latest start we plan** = 18:00 UTC = 23:30 IST, the latest time at which the assistant asks for a take to start (the studio lead\'s item L-23NOV confirmed 18:04 UTC = 23:34 IST; round 15 moves it 4 minutes earlier because 18:04 left only about 40 seconds, confirmation o; the take needs about 14 minutes 20 seconds, 860 seconds, so a start at 18:00 UTC = 23:30 IST ends about 4 minutes 40 seconds before the last time to revoke, on a duration that is a reading and not measured).')
sub('the assistant asks for no start later than 18:04 UTC = 23:34 IST on any day (the latest start we plan; the program refusal limit',
    'the assistant asks for no start later than 18:00 UTC = 23:30 IST on any day (the latest start we plan; round 15 moved it 4 minutes earlier than the studio lead\'s 18:04 UTC = 23:34 IST, see o; the program refusal limit')
sub_line('o. The latest start we plan (18:04 UTC = 23:34 IST) leaves about 40 seconds',
 'o. The latest start we plan (18:00 UTC = 23:30 IST, moved in round 15 from the studio lead\'s 18:04 UTC = 23:34 IST) leaves 4 minutes 40 seconds before the last time to revoke (18:19 UTC = 23:49 IST) if the take lasts 860 seconds (it would end at 18:14:20 UTC = 23:44:20 IST); 860 seconds is a reading of the take program, not measured, and the margin ignores the time to type `y`, the confirmation number and the take id. At 18:04 UTC = 23:34 IST the margin was about 40 seconds, which a 15-minute take would have used up, and route B would have left no time to watch the cut. Round 15 applies the earlier time (security M3). Confirm 18:00 UTC = 23:30 IST, or give a later figure with a written reason, and measure the real duration of the first take; the owner text no longer asks the assistant to ask the studio lead about the margin.')
sub('- **R11 (E-12, E-54)**: before the sheet is given to the owner, the studio lead fills the placeholder (if it stays unfilled, the fallback sentence that follows the placeholder in E-12 and E-54 applies; the owner is not asked to read it as a time) `[LEAD FILLS at re-pin: ...]` (the time of day of the take on Wed 18 Nov 2026, in UTC and IST) in E-12 and E-54, and checks that the same time stands in both. Nothing here invents it.',
    '- **R11 (E-12, E-54)**: round 15 (naive M8): the owner texts carry no placeholder any more. They say that the time of day of the take on Wed 18 Nov 2026 is not yet chosen and that the assistant proposes one. If the studio lead fixes the time of day at re-pin, it replaces the sentence that starts "The time of day is not yet chosen" in E-12 and E-54 by the fixed time in UTC and IST (the same in both, not later than the latest start we plan, 18:00 UTC = 23:30 IST). Nothing here invents it.')
sub('- **R7 (E-48)**: the assistant must send', '- **R7 (E-48)**: round 15: the studio lead also checks in the chat record that every trigger word was typed by the owner himself as a new message (key step B), that `no more takes` was answered with the one question and confirmed by `yes, no more takes`, and that item 1 started only after `start clean-up`; the assistant must send')
sub('Record: `ND15: A|B <owner message>`.', 'Round 15: `no more takes` alone starts nothing; it needs the confirmation `yes, no more takes` (key step D; naive M5). Record: `ND15: A|B <owner message>`.')
# confirmation p
sub('\nRemoved in round 3 (each was answered by a decision', '\np. Round 15 additions of the builder, to confirm: (1) only a message that the owner types himself in the chat counts for every trigger word (E-48 key step B, E-52, E-12, E-16; security M1); the assistant cannot check who types, so this stays a promise; (2) `no more takes` needs a second message `yes, no more takes` and the clean-up needs `start clean-up` (naive M5, security M1); (3) the shred targets are the take folder (path copied by the owner from his own step 8 message) and the files on the owner\'s own list; never a recording, a video file or a path under `/mnt/c` that is not on the list (security M2); (4) the key in the HubSpot credential of n8n is the key of app 2 and the key in `~/take-secrets` is the one of app 1; both are the builder\'s reading of step 7, UNVERIFIED (naive M3; confirmation k); (5) the new rows E-59 to E-61.\n\nRemoved in round 3 (each was answered by a decision')

# ---------------- E-48 ----------------
set_new('E-48', E48)
why_add('E-48', R15WHY + '(a) the item is now eleven short lettered steps, key steps A to K, with capital letters, so that they are not mixed up with step 8\'s sub-steps or with items 1 to 6 (naive M9); key step B is new (only the owner\'s own typed message counts, security M1); (b) alarm 1 and alarm 2 say what to do in each route and with or without a session, and no longer say "do 3h at once" against a running take (naive M1, M2, security m1); (c) `no more takes` needs the question and `yes, no more takes` (naive M5); (d) the shred targets are only the take folder (path checked against the path of step 8), the owner\'s own list and the two files of item 6; never a recording, video file or `/mnt/c` path; `shred done` has a scope and silence counts as `shred not done` (security M2, naive M4); item 1 needs `start clean-up`; (e) the brand name is gone from key step I; (f) a short summary line opens the item (security m4). Old part tags: 3a=A, 3b=C, 3c=D, 3d=E, 3e=F, 3f=G, 3g=H, 3h=I, 3i=J, 3j=K.')

# ---------------- E-09 ----------------
edit_new('E-09', [
 ('(3) write `you may look again`. Any other reply from you keeps the assistant not looking.', '(3) write `you may look again`. Turn off the sharing of the clipboard between devices (Settings, System, Clipboard; this click path is not checked), do not type a secret inside a remote-desktop window, and answer no if a browser or a program offers to save the password. The words `please stop looking` and `you may look again` count only when you type them yourself, as a new message in the chat (step 22 item 3, part 3b). Any other reply from you keeps the assistant not looking.'),
 ('with the three names copied from its message:', 'with the two names `<password file name>` and `<folder>` copied from its message:'),
 ('(full path, the checks, then `shred -u`)', '(full path, the checks, then `shred -u`; write the old file\'s full path on your own list of files first)'),
 ('so that the password does not stay on the screen of the terminal.', 'so that the password does not stay on the screen of the terminal. `clear` may leave the old lines in the scrolling history of some terminal programs, so close the terminal window too. nano can leave a backup or save copy next to a file (a file whose name ends in `~` or `.save`): after nano, type `ls -a` and press Enter, and if you see such a file, tell the assistant its name and shred it by the shred rule (step 22 item 3, part 3f).'),
 ('Use the key of app 1 (read only) unless the assistant tells you in writing why the key of app 2 is needed; the key of app 2 may write to contacts (UNVERIFIED), so ask before you type it.', 'There are two different HubSpot keys. The key in your file in `~/take-secrets` (app 1, read only) is read by the counting program. The credential in n8n belongs to the flows that create the contacts, so it needs the key of app 2 (read and write, step 7). The assistant names the app in its message before you type; if it does not, do not type and ask. Never type the key of app 1 into n8n unless the assistant explains in writing why.'),
])
why_add('E-09', R15WHY + '(a) naive M3: the two HubSpot keys are named apart (app 1 read only for the counting program, app 2 read and write for the n8n credential) and there is no silent default; (b) naive minor: sub-step e says two names, as the reply form has; (c) security residue and m3: clipboard sharing between devices, remote desktop and browser save-password offers are named; `clear` may leave scrolling history and nano may leave a backup or save copy, so the owner closes the terminal and looks for such files; (d) the old password file goes on the owner\'s own list before it is shredded.')

# ---------------- E-12 ----------------
edit_new('E-12', [
 ('It has two parts. If any part is missing, you answer no.', 'It has two blocks. If any block is missing, you answer no.'),
 ('Part 1, the money figures, in US dollars:', 'Block 1, the money figures, in US dollars:'),
 ('Part 2 is this list:', 'Block 2 is this list:'),
 ('- The list of test items of the plan, attached to the request.\n', '- The list of test items of the plan, attached to the request.\n- The page of the key list at the company that provides the AI model, where you will revoke the secret key for the model (step 22 item 3, part 3e); the click path is not checked.\n'),
])
set_block_line('E-12', '- The days and times, in UTC and IST.', '- The days and times, in UTC and IST. UTC is the world time that computers use; IST (India Standard Time) is UTC plus 5 hours 30 minutes, so 18:00 UTC = 23:30 IST. The take is aimed at Wed 18 Nov 2026. The time of day is not yet chosen: the assistant proposes a time of day for that Wednesday, in UTC and IST, not later than the latest start we plan, and you answer it before any take; no take starts on a guess. The request states the planned start time and the latest start we plan. The latest start we plan is 18:00 UTC = 23:30 IST on any day, and the assistant asks for no start after it. The reason: the take needs about 14 minutes 20 seconds (860 seconds, a reading of the take program, not measured), so a take that starts at 18:00 UTC = 23:30 IST ends at 18:14:20 UTC = 23:44:20 IST, which is 4 minutes 40 seconds before the last time to revoke the secret key for the model (18:19 UTC = 23:49 IST). Typing `y`, the confirmation number and the take id takes about a minute more, and a take that lasts 4 minutes longer than the reading still ends before 18:19 UTC = 23:49 IST. A different figure is the program refusal limit: the take program itself is read to refuse a start only from about 18:14 UTC = 23:44 IST (a reading of the section "Refusals, deadline and exit codes" of this sheet, UNVERIFIED, not checked in the code). It is later than the latest start we plan, and the assistant never asks for a start between the two.')
edit_new('E-12', [
 ('it asks for no start later than the latest start we plan (18:04 UTC = 23:34 IST), so that the take is over before 18:19 UTC = 23:49 IST.', 'it asks for no start later than the latest start we plan (18:00 UTC = 23:30 IST), so that the take is over before 18:19 UTC = 23:49 IST.'),
])
set_block_line('E-12', 'Your reply is ONE line that you type in the chat.', 'Your reply is FIVE short numbered lines that you type yourself, in ONE new message in the chat (only a message typed by you counts: step 22 item 3, part 3b). Copy the five lines below as plain text (without backticks), replace every part in angle brackets and keep the rest as written:\n   1. Yes, take <take id>\n   2. tests: stand-in test <N1> pass, 0 failed, 0 missed, 0 not run; flow rehearsal <N2> pass, 0 failed, 0 missed, 0 not run; crash check <tested or untested>\n   3. files: result file <result file>; reviewers\' report <reviewers\' report file>; search file <search file or commit name>; test output file <test output file>\n   4. money: up to 3 model calls and up to US$<X>; spending window ends 2026-11-23 18:29 UTC = 23:59 IST; latest start we plan <time in UTC and IST>\n   5. I know that the assistant shares my Linux user, my clipboard and my screen, and that it can reach n8n\'s encryption key, the credentials saved in the take\'s n8n, the copy of the secret key for the model in the take folder and the files in `~/take-secrets`.')
edit_new('E-12', [
 ('typed as a number with two decimals and without a dollar sign (for example `1.50`; the form already has "US$" before it).', 'copied digit by digit from the request (two decimals, no dollar sign; line 4 already has "US$" before it); the assistant compares it with its own figure and refuses the reply if it differs.'),
 ('is copied from the request, in the form `18:04 UTC = 23:34 IST`.', 'is copied from the request, in the form `18:00 UTC = 23:30 IST`.'),
 ('- The last part, "I know that the assistant shares', '- Line 5, "I know that the assistant shares'),
 ('If a part of your reply is missing or wrong, the assistant does not start the take and tells you which part.', 'If a line of your reply is missing or wrong, the assistant does not start the take and tells you which line.'),
 ('only your reply in the form above can start a take.', 'only your reply in the form above, typed by you yourself in a new message, can start a take.'),
])
why_add('E-12', R15WHY + '(a) security M3: the latest start we plan is moved to 18:00 UTC = 23:30 IST, so a take of 860 seconds ends at 18:14:20 UTC = 23:44:20 IST, 4 minutes 40 seconds before the last time to revoke; the request to the studio lead is out of the owner text (confirmation o); the two bare times are paired with UTC and IST (evidence r14); "no start between the two" is now "no start after 18:00 UTC = 23:30 IST"; (b) naive M6: the reply is five short numbered lines, with no copyable example figure for the money (the assistant compares the figure) and the word "part" is kept for the lines of the reply, while the request has two "blocks"; (c) naive M8: no placeholder in the owner text; (d) security M1: only a typed message counts; (e) security minor: the page of the key list is given at the first take.')

# ---------------- E-16 ----------------
edit_new('E-16', [
 ('and starts it only after you have written `no more takes` in the chat (in route B of step 22 item 3, part 3c, also after `cut accepted`) and after you have written `key revoked` (or `key not revoked` and the reason) and `shred done` (or `shred not done` and the reason) for the secret key for the model (step 22 item 3, parts 3f and 3h), because none of it',
  'and starts it only after you have confirmed `no more takes` with `yes, no more takes` in the chat (in route B of step 22 item 3, part 3c, also after `cut accepted`) and after you have written `key revoked` (or `key not revoked` and the reason) and `shred done` (or `shred not done` and the reason) for the secret key for the model (step 22 item 3, parts 3f and 3h), and after you have typed `start clean-up` as a new message once the assistant has listed in one message what it will remove (the full paths and the container\'s name). Only messages that you type yourself count (step 22 item 3, part 3b). None of it'),
 ('It removes nothing if that path is your home folder, is under `/mnt/c`, is outside the take root that it recorded, contains `..`, or is or contains a link (a link is a shortcut to another place); a link inside the take folder is removed as a link and never followed.',
  'It removes nothing if that path is your home folder, is under `/mnt/c`, is outside the take root that it recorded, contains `..`, or if the path itself or any folder in front of it is a link (a link is a shortcut to another place). A link that lies INSIDE the take folder is removed as a link (only the shortcut goes) and is never followed. It removes only things whose full path starts with the full path of the take folder followed by `/`, so the take folder `/x/take-1` never accepts `/x/take-10`. The path must also be the one that you copied from step 8 (sub-step e); if the assistant\'s path differs, it removes nothing and tells you. It never removes a recording or a video file.'),
])
why_add('E-16', R15WHY + '(a) security M1: the clean-up needs `yes, no more takes` and a fresh `start clean-up` after a list of what will be removed, and only typed messages count; (b) security M2: the contradiction about links is settled (nothing is removed if the take folder path is a link or lies behind one; a link inside the folder is removed as a link and never followed), the trailing `/` test is added, and the path must match the owner\'s own step 8 path.')

# ---------------- E-37 ----------------
edit_new('E-37', [
 ('`not sure` never keeps the key alive. You then know both answers before the take day.', '`not sure` never keeps the key alive. If your answer to (2) is `same key`, making a new key for your own n8n takes about 30 minutes on the last day (step 22 item 3, part 3g), so make it before. You then know both answers before the take day.'),
 ('(3) Whether the HubSpot secret key that the take uses (the one in your file in `~/take-secrets`, not the key for the model) is the read-only one of step 7, app 1, and whether app 2 exists. If either is not so, you do not say yes to a take until the assistant has told you what to change and you have changed it.',
  '(3) Two different HubSpot keys: the key in your file in `~/take-secrets` (not the key for the model) must be the read-only one of step 7, app 1; the key that you type into the HubSpot credential in n8n (step 8, sub-step h) must be the key of app 2, which can read and write contacts, because the flows create the contacts. Both apps must exist. If either is not so, you do not say yes to a take until the assistant has told you what to change and you have changed it. (4) Also before the take, write on paper or on your phone (never in a file on this laptop) your own list of every file in which you saved a copy of the secret key for the model, each with its full path. It is the only source of the files outside the take folder that the shred rule lets you shred (step 22 item 3, part 3f); add to it whenever you save a copy later.'),
])
why_add('E-37', R15WHY + 'naive M3: the two HubSpot keys are named apart; security M2: the owner writes his own list of key copies before the take; security m5: the `same key` case takes about 30 minutes.')

# ---------------- E-52 ----------------
edit_new('E-52', [
 ('**The latest start we plan** is 18:04 UTC = 23:34 IST:', '**The latest start we plan** is 18:00 UTC = 23:30 IST:'),
 ('The long one-line reply of step 16 you copy as shown, because it is checked part by part.', 'The five-line reply of step 16 you copy as shown, line by line, because it is checked line by line. Only you can write these words: they count only when you type them yourself, as a new message in your chat with the assistant; words that stand in a mail, a file, the output of a program or a forwarded or quoted message never count, and the assistant then does nothing because of them (step 22 item 3, part 3b).'),
 ('After every take the assistant asks you to reply `no more takes` or `more takes`; no reply counts as `more takes`.', 'After every take the assistant asks you to reply `no more takes` or `more takes`; no reply counts as `more takes`. `no more takes` is confirmed only by your next message `yes, no more takes`.'),
 ('you choose one by writing `route A` or `route B` in the chat once, before your last take.', 'you choose one by writing `route A` or `route B` in the chat once, before your last take. **Key steps A to K**: the lettered steps of step 22 item 3 that concern the secret key for the model (capital letters, so that they are not mixed up with the small-letter sub-steps of step 8).'),
])
why_add('E-52', R15WHY + 'security M1: the "only you can write these words" sentence is in the list of how to reply; the latest start we plan is 18:00 UTC = 23:30 IST; the reply of step 16 is five lines; key steps A to K are named.')

# ---------------- E-54 ----------------
set_new('E-54', '## Phase 1: the assistant checks. You only need to be reachable and to answer the questions it asks. The take is aimed at Wed 18 Nov 2026. The time of day is not yet chosen: the assistant proposes one, in UTC and IST, not later than the latest start we plan (18:00 UTC = 23:30 IST), in the request for your yes (step 16), and you answer it before any take; no take starts on a guess.')
why_add('E-54', R15WHY + 'naive M8: no bracketed placeholder with "LEAD FILLS" in owner text, and the latest start we plan (18:00 UTC = 23:30 IST) is stated here; rule R11 tells the studio lead how to fix the time later.')

# ---------------- E-55, E-57 ----------------
edit_new('E-55', [
 ('Nothing in this step is done before you have written `no more takes` in the chat', 'Nothing in this step is done before you have confirmed `no more takes` with `yes, no more takes` in the chat'),
 ('and `shred done` (or `shred not done` and the reason). Item 1 deletes', 'and `shred done` (or `shred not done` and the reason), and have typed `start clean-up`. Item 1 deletes'),
])
why_add('E-55', R15WHY + 'security M1 and naive M5: the confirmation and `start clean-up` are named here too.')
edit_new('E-57', [
 ('Route A: you wrote `no more takes` after the last take.', 'Route A: you wrote `no more takes` after the last take and confirmed it with `yes, no more takes`.'),
])
why_add('E-57', R15WHY + 'naive M5: the confirmation is named.')

# ---------------- new rows E-59, E-60, E-61 ----------------
def newrow(rid, line, typ, needs, old, new, why):
    return (f'### {rid}: OWNER-STEPS-realrun-v3.md, line {line}, status Apply now, type {typ}\nOLD (exact):\n~~~~\n{old}\n~~~~\nNEW (exact):\n~~~~\n{new}\n~~~~\nWhy: {why}\n\n')
rows_new = newrow('E-59', 126, 'CONTRADICTION', 'E-48',
 "6. Only after the check passed: delete the two secret files in WSL: `shred -u ~/take-secrets/*` (UNVERIFIED that shred is installed; otherwise `rm`). Do NOT delete `~/.hadavin-take-tags/<id>.used`.",
 "6. Only after the check passed: delete the two secret files in the Linux part of your laptop (WSL), one at a time, each by the shred rule of key step G. The two files are the one with the app password of the receiver mailbox and the one with the HubSpot read secret key, both in the folder `~/take-secrets`; type `realpath ~/take-secrets` once to see the full path of that folder, and write the full path of each file on your own list. Do not use the sign `*`. If shred is not installed, run the same five checks and then `rm -- '<path>'`. These two files are part (c) of key step G: your `shred done` of item 3 includes them. Do NOT delete `~/.hadavin-take-tags/<id>.used`.",
 "Security m2 and naive M4 of round 14 (resolve-r14 question 4): item 6 said `shred -u ~/take-secrets/*`, which E-48 forbids (the sign `*`, `~`) and which has no path checks. The row replaces it by the one shred rule (key step G). The part \"UNVERIFIED that shred is installed\" is covered by the rule's fallback (`rm --`). It needs E-48 (key step G).")
rows_new += newrow('E-60', 171, 'UNCLEAR WORD', 'E-12',
 "With the window end at 23 Nov 2026 18:29Z the last start is about 18:14Z (the refusal is now + 860 s >= end, so before 18:14:40Z at the default lease).",
 "With the window end at 23 Nov 2026 18:29 UTC = 23:59 IST the program refusal limit (the last start that the take program accepts) is about 18:14 UTC = 23:44 IST (the refusal is now + 860 s >= end, so before 18:14:40 UTC = 23:44:40 IST at the default lease). The assistant asks for an earlier start: none after 18:00 UTC = 23:30 IST (the latest start we plan, step 16).",
 "Security m2 (input line 171 had UTC times with no IST pair and no word for the earlier start the assistant asks for). The program refusal limit stays a reading, UNVERIFIED by code (confirmation h).")
rows_new += newrow('E-61', 144, 'STALE', '-',
 "| By Mon 16 | the sentences of step 9; answers to the three decisions |",
 "| Before the first take (the old date, Mon 16 Nov 2026, no longer counts: see the note at the top of Phase 0) | the sentences of step 9; answers to the three decisions |",
 "Security m2 (input line 144 named a date with no year and no UTC or IST); E-37 says the Phase 0 deadline of Mon 16 Nov no longer counts. Whether step 9 and the three decisions are still needed is for the studio lead (confirmation e).")
k = T.index('## Lines checked and found consistent')
T = T[:k] + rows_new + T[k:]
# index lines
sub('| E-58 | OWNER-STEPS-realrun-v3.md | 147 | Apply now | - | E-48, E-55, E-57 | CONTRADICTION |\n', '| E-58 | OWNER-STEPS-realrun-v3.md | 147 | Apply now | - | E-48, E-55, E-57 | CONTRADICTION |\n| E-59 | OWNER-STEPS-realrun-v3.md | 126 | Apply now | - | E-48 | CONTRADICTION |\n| E-60 | OWNER-STEPS-realrun-v3.md | 171 | Apply now | - | E-12 | UNCLEAR WORD |\n| E-61 | OWNER-STEPS-realrun-v3.md | 144 | Apply now | - | - | STALE |\n')

# ---------------- part tags -> key steps (all lines except Why lines and round-history bullets) ----------------
MAP = dict(zip('abcdefghij', 'ACDEFGHIJK'))
def _one(m):
    a, conn, b = m.group(2), m.group(3), m.group(4)
    if b: return f'key steps {MAP[a]} {conn} {MAP[b]}'
    return f'key step {MAP[a]}'
RX = re.compile(r'\b(parts?) 3([a-j])\b(?: (and|to) 3([a-j])\b)?')
ls = T.split('\n'); inold = False
for n, l in enumerate(ls):
    if l.startswith('Why:') or l.startswith('- Round'): continue
    ls[n] = RX.sub(_one, l)
T = '\n'.join(ls)
# residual bare tags in non-Why lines
for n, l in enumerate(T.split('\n')):
    if not (l.startswith('Why:') or l.startswith('- Round')) and re.search(r'\b3[a-j]\b', l):
        errs.append('residual tag line %d: %s' % (n + 1, re.search(r'.{30}\b3[a-j]\b.{20}', l).group(0) if re.search(r'.{30}\b3[a-j]\b.{20}', l) else l[:60]))

T = T.rstrip('\n') + '\n- Round 15 added: nothing was run except text, count and weekday checks by script (`resolve-r15-check-output.txt`; `verify15.py` has negative controls for every new check). I did not run any program of the take, did not read the take code and did not check any click path (the key list page of the model provider, the clipboard sharing setting, the nano backup file names). The new rules (only the owner\'s typed message counts, the confirmation `yes, no more takes`, `start clean-up`, the owner\'s own list of key copies, the path checks) are written instructions: none is enforced by a program, and no test showed that an owner can follow them. 860 seconds is still a reading, not a measurement. The web address `http://localhost:5678` keeps its `http://` because the owner types it into a browser as written.\n'
open(D+'EDITS.md','w', encoding='utf-8').write(T)
print('errors:', len(errs))
for e in errs: print(' ', e)
sys.exit(1 if errs else 0)
