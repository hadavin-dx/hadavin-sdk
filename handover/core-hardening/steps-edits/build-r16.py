"""Round 16 builder: anchored patches of EDITS.round15.md (every old string asserted to occur exactly once). Writes EDITS.md. No vendor words, no secrets.
Paths are relative to this file."""
import re, sys
import os
D = os.path.dirname(os.path.abspath(__file__)) + '/'
T = open(D + 'EDITS.round15.md', encoding='utf-8').read()
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

exec(open(D + 'build-r16-e48.py', encoding='utf-8').read())

# ---------- helper: replace a span inside the NEW block between two anchors (both must occur once)
def cut_new(rid, start, end, new, nth=0):
    global T
    i, j = row_span(rid)
    lines = T[i:j].split('\n')
    r = _find_new(lines, nth)
    if not r: errs.append(f'{rid}: NEW block missing'); return
    body = '\n'.join(lines[r[0]:r[1]])
    a = body.count(start); 
    if a != 1: errs.append(f'{rid} cut start count {a}: {start[:50]!r}'); return
    s = body.index(start)
    if body.count(end, s) < 1: errs.append(f'{rid} cut end missing: {end[:50]!r}'); return
    e = body.index(end, s) + len(end)
    body = body[:s] + new + body[e:]
    lines[r[0]:r[1]] = body.split('\n')
    T = T[:i] + '\n'.join(lines) + T[j:]

# ---------- title and header
sub('(round 15, batched fix pass after the round 14 reviews;', '(round 16, batched fix pass after the round 15 reviews;')

# ---------- E-48
set_new('E-48', E48)
why_add('E-48', 'Round 16 (security F1 to F4, m1 to m8; stranger M1 to M7): (F1) a separate plain word `key gone, no more decisions` counts at any time, and `key revoked` counts as the confirmation only when typed after 18:19 UTC = 23:49 IST on Mon 23 Nov 2026 with no `no more takes` typed before it; otherwise the assistant asks again; (F3) shred part (d) = password files and editor copies, the own list = files that hold a secret you saved, `shred done 2` includes (d); (F4) ONE numbered order (the card): key revoked; shred (a),(b) = `shred done 1`; items 2, 3; item 5; item 6 and (c),(d) = `shred done 2`; `start clean-up`; item 1; item 1 never starts while the key copy exists and the key is not revoked; (m3) alarm 3 at 18:09 UTC = 23:39 IST; (m4) `please stop looking` before the click that creates a key; the key steps carry short text and the long detail is in Appendix K (nothing deleted); the words with several meanings are explained once; the cross-references now point at the right key steps (typed-message rule = key step B, revoke page = key step I).')

# ---------- E-12: arithmetic, alarms, cross-references
rsub('E-12', 'The reason: the take needs about 14 minutes 20 seconds (860 seconds, a reading of the take program, not measured), so a take that starts at 18:00 UTC = 23:30 IST ends at 18:14:20 UTC = 23:44:20 IST, which is 4 minutes 40 seconds before the last time to revoke the secret key for the model (18:19 UTC = 23:49 IST). Typing `y`, the confirmation number and the take id takes about a minute more, and a take that lasts 4 minutes longer than the reading still ends before 18:19 UTC = 23:49 IST.',
 'The reason, in numbers: 18:00 UTC = 23:30 IST is the time at which you START TYPING (the take id, the confirmation number and `y`; about 1 minute), so the take program itself starts about 18:01:00 UTC = 23:31:00 IST. The take needs about 14 minutes 20 seconds (860 seconds, a reading of the take program, not measured), so it ends about 18:15:20 UTC = 23:45:20 IST, which is 3 minutes 40 seconds before the last time to revoke the secret key for the model (18:19 UTC = 23:49 IST). If the take is longer than the reading by more than 3 minutes 40 seconds, it is still running at 18:19 UTC = 23:49 IST and you revoke the key anyway (step 22 item 3, key step K).')
rsub('E-12', 'Set two alarms on your own phone or computer (step 22 item 3, key step C): alarm 1 for 17:49 UTC = 23:19 IST on Mon 23 Nov 2026, named `revoke the secret key for the model`, and alarm 2, which repeats every evening from the day of your first take, named `is the secret key for the model still alive?`.',
 'Set three alarms on your own phone or computer (step 22 item 3, key step C): alarm 1 for 17:49 UTC = 23:19 IST on Mon 23 Nov 2026, named `revoke the secret key for the model`; alarm 3 for 18:09 UTC = 23:39 IST the same day, named `10 minutes left: revoke the secret key for the model now`; and alarm 2, which repeats every evening from the day of your first take (your own phone time), named `is the secret key for the model still alive?`.')
rsub('E-12', '(only a message typed by you counts: step 22 item 3, key step C)', '(only a message typed by you counts: step 22 item 3, key step B)')
rsub('E-12', 'Your reply is FIVE short numbered lines that you type yourself, in ONE new message in the chat (only a message typed by you counts: step 22 item 3, key step B).', 'Your reply is FIVE short numbered lines that you type yourself, in ONE new message in the chat (only a message typed by you counts: step 22 item 3, key step B). "Your reply" below always means these five lines.')
rsub('E-12', 'where you will revoke the secret key for the model (step 22 item 3, key step F)', 'where you will revoke the secret key for the model (step 22 item 3, key step I)')
rsub('E-12', 'The list of test items of the plan, attached to the request.', 'The list of test items of the plan (the numbered tests of the plan), attached to the request.')
rsub('E-12', 'Answer no if the request leaves out a fact, a file name or the list of checks,', 'Answer no if the request leaves out a fact, a file name or the list of test items,')
why_add('E-12', 'Round 16 (stranger M2, M5; security m3): the margin arithmetic is now right: 18:00 UTC = 23:30 IST is the start of TYPING, the program starts about 18:01:00 UTC = 23:31:00 IST and ends about 18:15:20 UTC = 23:45:20 IST, so the margin is 3 minutes 40 seconds (old text: 4 minutes 40 seconds, which ignored the minute of typing); the claim "4 minutes longer still ends before 18:19" is deleted because it was false; three alarms (alarm 3 at 18:09 UTC = 23:39 IST); the cross-references now say key step B (typed words) and key step I (revoke page); "list of checks" becomes "list of test items".')

# ---------- E-60 (plain words, no code names)
set_new('E-60', 'With the window end at 23 Nov 2026 18:29 UTC = 23:59 IST the take program accepts a start only until about 18:14 UTC = 23:44 IST (the "program refusal limit": it refuses a start if the start time plus 860 seconds would reach the end of the window, so a start before 18:14:40 UTC = 23:44:40 IST is accepted at the normal setting; this is a reading of the sheet, not checked in the code). The assistant asks for an earlier start: none after 18:00 UTC = 23:30 IST (the latest start we plan, step 16; the time at which you start typing).')
why_add('E-60', 'Round 16 (stranger minor): the signs ">=" and the word "lease" are out of the owner text; "latest start we plan" is tied to the start of typing.')

# ---------- E-11: the words that start the tests
rsub('E-11', 'Answer "ok" only if both are right', 'Write `ok stand-in test` (for the stand-in test) or `ok flow rehearsal` (for the flow rehearsal) only if both are right')
rsub('E-11', 'Your "ok" is about what the assistant says it will start.', 'Your `ok stand-in test` or `ok flow rehearsal` is about what the assistant says it will start.')
why_add('E-11', 'Round 16 (security m5): the bare "ok" becomes `ok stand-in test` and `ok flow rehearsal`, so that one word cannot be read as the answer to the other question.')

# ---------- E-16: one order, take root, list before removal
cut_new('E-16', 'The assistant does all of this, and starts it only after', 'comes first, because it revokes the key and shreds its copy).',
 'The assistant does all of this. It does NOT start while a copy of the secret key for the model exists and the key is not revoked. The order of step 22 is the only order: (1) you revoke the key and write `key revoked`; (2) you shred the copy in the take folder and the copies on your own list and write `shred done 1`; (3) your items 2 and 3 (HubSpot apps, app passwords, screenshots); (4) your item 5, the retire check; (5) your item 6, shredding the two files, and the password files and editor copies, and `shred done 2`; (6) the assistant lists in one message what it will remove (the full paths and the container\'s name) and you read the list; (7) you type `start clean-up` as a new message; (8) this item starts. You must have confirmed `no more takes` with `yes, no more takes` in the chat before any of it (in route B of step 22 item 3, key step D, also after `cut accepted`). Only messages that you type yourself count (step 22 item 3, key step B). None of it can be undone, and a retake after it needs a new set-up. It reports each part as done or not done. If a part is not done, it tells you before you do your own items.')
rsub('E-16', 'is outside the take root that it recorded,', 'is not inside the take root (the folder in which the assistant made the take folder; it is a NEW, EMPTY folder made for the take, never your home folder),')
rsub('E-16', 'It never removes a recording or a video file.', 'It never removes a recording or a video file. Before it removes anything it lists every file in the take folder and in the folder of the take\'s own data; if a recording or a video file is inside, it stops, removes nothing and tells you. You read that list before you type `start clean-up`.')
rsub('E-16', 'It does this because removing the container deletes n8n\'s database and the take\'s table of enquiries too.', 'It does this because removing the container deletes n8n\'s database and the take\'s table of enquiries too. It copies them BEFORE any shred, because shredding the take folder would also destroy the result file.')
why_add('E-16', 'Round 16 (security F4, m1, m2; stranger M4): the broken sentence ("None of it can be undone and because ...") and the false promise ("your item 3 comes first") are replaced by the one numbered order; the clean-up never starts while the key copy exists and the key is not revoked; the take folder is new and empty and never the home folder; the owner reads the list of what will be removed and the clean-up stops if a recording is inside; the result file and the counts are copied before any shred.')

# ---------- E-55: F1 and the one order
rsub('E-55', 'at 18:19 UTC = 23:49 IST on Mon 23 Nov 2026 you revoke it, and your `key revoked` then counts as `no more takes` (and, in route B, as `cut accepted`).', 'at 18:19 UTC = 23:49 IST on Mon 23 Nov 2026 you revoke it. Your `key revoked` counts as the confirmation `yes, no more takes` (and, in route B, as `cut accepted`) ONLY when you type it AFTER 18:19 UTC = 23:49 IST on Mon 23 Nov 2026 and you have typed no `no more takes` before it; at any other time the assistant asks again. If you want the confirmation to hold at any time, write `key gone, no more decisions` (key step B).')
rsub('E-55', 'The assistant starts item 1 only after you have also written `key revoked` (or `key not revoked` and the reason) and `shred done` (or `shred not done` and the reason), and have typed `start clean-up`.', 'The assistant starts item 1 only after you have written `key revoked` (or `key not revoked` and the reason), `shred done 1` and `shred done 2` (or `shred not done 1` or `shred not done 2` and the reason), have read the list of what it will remove, and have typed `start clean-up`; item 1 never starts while the copy of the key exists and the key is not revoked.')
rsub('E-55', 'You do items 2 to 6 as listed below; item 3 comes first.', 'You do the items in the order of the card of item 3 (key revoked; shred 1; items 2 and 3; item 5; item 6 and shred 2; `start clean-up`; item 1).')
why_add('E-55', 'Round 16 (security F1, F4): `key revoked` counts as the confirmation only after 18:19 UTC = 23:49 IST on Mon 23 Nov 2026 with no earlier `no more takes`; the owner may write `key gone, no more decisions` at any time; the one order replaces "item 3 comes first".')

# ---------- E-57: route A default wording
rsub('E-57', '(watching the cut before the last time to revoke the secret key for the model is the assistant\'s default)', '(the assistant plans for you to watch the cut before the last time to revoke the secret key for the model; you may choose route A or route B as below)')
why_add('E-57', 'Round 16 (stranger minor): "default" is out; the route stays your choice.')

# ---------- E-59: shred done 2
rsub('E-59', 'These two files are part (c) of key step G: your `shred done` of item 3 includes them.', 'These two files are part (c) of key step G. After them you also shred part (d), the password files and editor copies of key step G, and then you write `shred done 2`.')
why_add('E-59', 'Round 16 (security F3): `shred done 2` includes part (d).')

# ---------- E-04 and E-42 (held): exact addresses
rsub('E-04', 'The assistant gives you the list: the enquiry key of each contact and its HubSpot contact number, if the program printed them; otherwise the made-up names to look for.', 'The assistant gives you the list: the enquiry key of each contact and its HubSpot contact number, if the program printed them; otherwise the exact addresses to look for. You delete a contact only if its e-mail address is exactly `take-<id>-a@example.com`, `take-<id>-b@example.com` or `take-<id>-c@example.com` (with this take\'s id). If you find more than 3 such contacts, or any other contact, you delete nothing and tell the assistant.')
rsub('E-42', 'and the assistant gives you the count and, if the program printed them, the list (enquiry key and contact id).', 'and the assistant gives you the count and, if the program printed them, the list (enquiry key and contact id). You delete a contact only if its e-mail address is exactly `take-<id>-a@example.com`, `take-<id>-b@example.com` or `take-<id>-c@example.com` (with this take\'s id); if you find more than 3, or any other contact, you delete nothing and tell the assistant.')
why_add('E-04', 'Round 16 (security F2): the owner deletes contacts only by the exact address; "made-up names" is out.')
why_add('E-42', 'Round 16 (security F2): same rule as E-04.')

# ---------- E-23, E-56, E-37, E-54, E-52 spot fixes are done by build-r16-more.py (exec below)
# E-23 plain words
rsub('E-23', '(at the time of writing fix round 3 on `take/nlite-int-r3`, fix round 4 on `take/nlite-int-r4`, fix round 5 being built on `take/nlite-int-r5`; source: the plan\'s own header notes of 2026-11-16)', '(at the time of writing the plan is at its fifth fix round; the names of the code branches are in the plan\'s header notes of 2026-11-16 and are not needed by you)')
why_add('E-23', 'Round 16 (stranger minor): branch names are out of the owner text.')

rsub('E-09', 'as a new message in the chat (step 22 item 3, key step C)', 'as a new message in the chat (step 22 item 3, key step B)')
rsub('E-52', 'step 22 item 3, key step C)', 'step 22 item 3, key step B)', 1)
why_add('E-09', 'Round 16 (stranger M1): the typed-message rule is key step B, not key step C.')
why_add('E-52', 'Round 16 (stranger M1): the typed-message rule is key step B, not key step C.')

# E-56 plain words, no codes
set_new('E-56', '''- UNVERIFIED: two statements later in this line (the clause that says the end of the take makes a delete request, and the note at the end of the MAY part of this line; the word "archive" in the next line of this file means the same) say that the end of the take removes the take's HubSpot contacts. That is an earlier reading of the code. A later independent review found no delete or archive path, and the decision of 16 Nov 2026 says the take never deletes contacts. Which reading is right is NOT SETTLED; the studio lead shows a search of the final code when the code version is fixed. Until then do not rely on either statement, and do not widen the HubSpot key.
- MAY: post this take's own generated lead keys (L plus hex);''')
why_add('E-56', 'Round 16 (stranger minor): the owner-facing text no longer carries the codes Q23, r17 and F-01 or file line numbers.')

# E-54 split heading and paragraph
set_new('E-54', '''## Phase 1: the assistant checks.
You only need to be reachable and to answer the questions it asks. The take is aimed at Wed 18 Nov 2026. The time of day is not yet chosen: the assistant proposes one, in UTC and IST, not later than the latest start we plan (18:00 UTC = 23:30 IST, the time at which you start typing), in the request for your yes (step 16), and you answer it before any take; no take starts on a guess.''')
why_add('E-54', 'Round 16 (stranger minor): the heading is only a heading; the paragraph is its own line.')

# E-37 (3) UNVERIFIED and (4) own list widened
rsub('E-37', 'must be the key of app 2, which can read and write contacts, because the flows create the contacts.', 'should be the key of app 2, which can read and write contacts, because the flows create the contacts (this reading of step 7 is UNVERIFIED; if you are not sure which app a key belongs to, tell the assistant and do not say yes).')
rsub('E-37', 'your own list of every file in which you saved a copy of the secret key for the model, each with its full path.', 'your own list of every file in which you saved a secret (the secret key for the model, a password, or any other secret that the take uses), each with its full path.')
why_add('E-37', 'Round 16 (stranger minor, security m8): which key belongs to which app is marked UNVERIFIED; the own list holds the files that hold a secret you saved, not only the key for the model.')

# ---------- E-62: input line 112
NEW62 = '''### E-62: OWNER-STEPS-realrun-v3.md, line 112, status Apply now, type CONTRADICTION
OLD (exact):
~~~~
delete any leftover HubSpot contacts the lead counted
~~~~
NEW (exact):
~~~~
delete any leftover HubSpot contacts that the assistant counted, and only those whose e-mail address is exactly `take-<id>-a@example.com`, `take-<id>-b@example.com` or `take-<id>-c@example.com` (with the id of the take that failed). If you find more than 3 such contacts, or any other contact, you delete nothing and tell the assistant
~~~~
Why: Security F2 of round 15: input line 112 (step 20) told the owner to delete "leftover HubSpot contacts the lead counted" with no limit on which contacts, while E-04 and E-42 (held on gate G1) limit them to the take's exact addresses. This row is Apply now because step 20 is about a failed take, which can leave contacts whatever the final code does; the rule is the same exact address, at most 3. The old text is part of line 112 and occurs once there; E-57 and E-12 do not overlap it.
'''
sub('\n## Lines checked and found consistent', '\n' + NEW62 + '\n## Lines checked and found consistent')
sub('| E-61 | OWNER-STEPS-realrun-v3.md | 144 | Apply now | - | - | STALE |', '| E-61 | OWNER-STEPS-realrun-v3.md | 144 | Apply now | - | - | STALE |\n| E-62 | OWNER-STEPS-realrun-v3.md | 112 | Apply now | - | - | CONTRADICTION |')

# ---------- counts
sub('## Counts (computed by script, `resolve-r15.md` and `resolve-r15-check-output.txt`)', '## Counts (computed by script, `resolve-r16.md` and `resolve-r16-check-output.txt`)')
sub('59 rows in total: E-01 to E-61 without E-10 and E-35. By file: OWNER-STEPS 40 rows,', '60 rows in total: E-01 to E-62 without E-10 and E-35. By file: OWNER-STEPS 41 rows,')
sub('**Apply now 47**', '**Apply now 48**')
sub('**Conditional 0**; total 56.', '**Conditional 0**; total 60 (48 Apply now and 12 Hold).')
sub('The Apply now ids (47) are:', 'The Apply now ids (48) are:')
sub('E-59, E-60, E-61. Round 15 added E-59', 'E-59, E-60, E-61, E-62. Round 16 added E-62 (step 20, input line 112: the owner deletes leftover contacts only by the exact take addresses) and rewrote E-48 (key steps A to K are shorter and their detail moved to Appendix K; the new word `key gone, no more decisions`; the one numbered order; shred done 1 and 2), E-04, E-11, E-12, E-16, E-23, E-37, E-42, E-54, E-55, E-56, E-57, E-59 and E-60 and the rules R7 and the confirmations o, p and q. Round 15 added E-59')

# ---------- definition of latest start (line 30)
sub('so a start at 18:00 UTC = 23:30 IST ends about 4 minutes 40 seconds before the last time to revoke, on a duration that is a reading and not measured)', 'and 18:00 UTC = 23:30 IST is the time at which the owner STARTS TYPING; the program starts about 1 minute later, 18:01 UTC = 23:31 IST, and ends about 18:15:20 UTC = 23:45:20 IST, 3 minutes 40 seconds before the last time to revoke, on a duration that is a reading and not measured)')

# ---------- confirmation o and p, q
sub('leaves 4 minutes 40 seconds before the last time to revoke (18:19 UTC = 23:49 IST) if the take lasts 860 seconds (it would end at 18:14:20 UTC = 23:44:20 IST); 860 seconds is a reading of the take program, not measured, and the margin ignores the time to type `y`, the confirmation number and the take id.', 'is the time at which the owner STARTS TYPING; with about 1 minute of typing the program starts at 18:01:00 UTC = 23:31:00 IST and, if the take lasts 860 seconds, ends at 18:15:20 UTC = 23:45:20 IST, which leaves 3 minutes 40 seconds before the last time to revoke (18:19 UTC = 23:49 IST) (round 15 said 4 minutes 40 seconds and ignored the typing; round 16 corrects it); 860 seconds is a reading of the take program, not measured. STILL OPEN: this confirmation is not answered; confirm 18:00 UTC = 23:30 IST or give an earlier time.')
sub('letters run a to p without gaps', 'letters run a to q without gaps')
T = T.replace('(5) the new rows E-59 to E-61.', '(5) the new rows E-59 to E-61.\n\nq. Round 16 additions of the builder, to confirm: (1) the word `key gone, no more decisions` counts at any time, and `key revoked` counts as the confirmation only after 18:19 UTC = 23:49 IST on Mon 23 Nov 2026 with no `no more takes` typed before it (security F1); (2) `shred done 1` = parts (a) and (b), `shred done 2` = parts (c) and (d) (security F3, F4); (3) the contacts the owner may delete are only `take-<id>-a`, `-b`, `-c` at the example domain, at most 3 (security F2, row E-62); (4) route B keeps a live paid key and its copy on the laptop for up to five days; the exposure is stated in ND15 and is not removed, because the retake value is the owner\'s choice; (5) the new row E-62.', 1)

# ---------- R7 and ND15
rsub_all = None
sub('The owner\'s two alarms (key step C: 17:49 UTC = 23:19 IST on 23 Nov, and a repeating evening alarm from the first take) are the only reminders', 'The owner\'s three alarms (key step C: 17:49 UTC = 23:19 IST and 18:09 UTC = 23:39 IST on 23 Nov, and a repeating evening alarm from the first take) are the only reminders')
sub('and `shred done` (or `shred not done`). The studio lead writes the outcome', '`shred done 1` and `shred done 2` (or `shred not done 1` or `shred not done 2`) in the order of the card (key step C). The studio lead writes the outcome')
sub('Risk of B:', 'Risk of B:') if False else None
sub('risk of B: a live paid key and its copy stay on the disk longer,', 'risk of B (exposure kept on purpose and stated): a live paid key and its copy stay on the disk and in the chat of this laptop for up to five days, where any program that runs under the owner\'s Linux user can read them;')

# ---------- what I did not check
T = T.rstrip('\n') + '\n- Round 16 added: nothing was run except text, count, weekday and time-pair checks by script (`resolve-r16-check-output.txt`; `verify16.py` has negative controls, among them the nine mutations that `verify15.py` missed). I did not run any program of the take, did not read the take code, and did not check any click path (the key list page of the model provider, the clipboard sharing setting). Not finished in round 16, stated plainly: see `r16-CHANGES.md` (the list of open items first).\n'

# ---------- Appendix K (detail text, nothing deleted)
APP = '\n## Appendix K: the detail of the key steps (round 16)\nThe owner reads key steps A to K in row E-48. Where a key step says "Detail", the text is here. Nothing was deleted; the detail was moved.\n\n' + '\n\n'.join(APPX.values()) + '\n'
sub('\n## Lines checked and found consistent', APP + '\n## Lines checked and found consistent')
sub('CONTRADICTION 17 (including the rows marked as code-change gated), DEFERRED 1 (E-13); total 59.', 'CONTRADICTION 18 (including the rows marked as code-change gated), DEFERRED 1 (E-13); total 60.')

if errs:
    print('ERRORS', len(errs))
    for e in errs: print(' ', e)
    sys.exit(1)
open(D + 'EDITS.md', 'w', encoding='utf-8').write(T)
print('written', len(T.split('\n')), 'lines')
