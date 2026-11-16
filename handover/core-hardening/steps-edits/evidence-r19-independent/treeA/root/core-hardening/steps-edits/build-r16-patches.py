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
