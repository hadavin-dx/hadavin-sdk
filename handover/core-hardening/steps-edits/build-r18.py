"""Round 18 builder: anchored patches of EDITS.round17.md (every old string asserted to occur the stated number of times).
Writes EDITS.md, r18-OWNER-DAY-SHEET.md and r18-OWNER-APPENDIX-K.md. No vendor words, no secrets. Paths are relative to this file."""
import re, sys, os
D = os.path.dirname(os.path.abspath(__file__)) + '/'
_head = open(D + 'build-r17-head.py', encoding='utf-8').read().replace('EDITS.round16.md', 'EDITS.round17.md')
exec(_head)

LAST = "Tue 24 Nov 2026 18:29 UTC = 23:59 IST"

# ---------------------------------------------------------------- the seven steps of the one order: ONE source (this list), printed in the card and in the day sheet only
P = [
    "make sure that you have confirmed your last take with `yes, no more takes` (key step D.3), then revoke the secret key for the model (key step I) and write `key revoked` (on Mon 23 Nov 2026, if you have not typed `yes, no more takes` by 18:19 UTC = 23:49 IST, revoke the key at that time anyway and write `key gone, no more decisions` instead of both)",
    "do your items 2 and 3, the quick web revokes, each only after the identification check of step 22 item 3 (item 2: revoke both app passwords; item 3: delete both HubSpot apps; touch nothing that you are not sure about)",
    "shred the copy of the key in the take folder and the other copies of the old key on your own list (key step G, parts (a) and (b)) and write `shred done key copies`",
    "do your item 4 (save the screenshots) and your item 5, the retire check",
    "do your item 6 (shred its two files) and shred the other secret files on your own list (key step G, parts (c) and (d)), and write `shred done other files`",
    "read the list of what the assistant will remove (the full paths and the container's name) and, if nothing in it is a file that you want to keep, write `start clean-up`",
    "the assistant does its item 1 (the clean-up)",
]
CARD_HEAD = "The one order (the card; read it first). Do these seven things in this order and never a later one before an earlier one:"
CARD_TAIL = "Key step J (other keys) is not one of the seven: do it at any time after card step 1; it holds nothing up."
CARD_LINES = [
    "   1. You: " + P[0] + ". Make new keys first only if key step H says so and at least 30 minutes remain. Normally you do this right after your last take that you accept.",
    "   2. You: " + P[1] + ".",
    "   3. You: " + P[2] + ".",
    "   4. You: " + P[3] + ".",
    "   5. You: " + P[4] + ".",
    "   6. You: " + P[5] + ".",
    "   7. Then " + P[6] + ". It never starts while a copy of the key exists and the key is not revoked.",
]
LASTDAY = ("   Last day, Mon 23 Nov 2026: the 10 minutes between 18:19 UTC = 23:49 IST and 18:29 UTC = 23:59 IST go in this order: card step 1 (the key), then card step 2 (the quick web revokes), then card step 3 (the shreds). "
           "What you have not finished by 18:29 UTC = 23:59 IST you finish by " + LAST + " (key step D.5).")
NEWCARD = CARD_HEAD + "\n" + "\n".join(CARD_LINES) + "\n" + LASTDAY + "\n   " + CARD_TAIL

# ---------------------------------------------------------------- E-48 card
span_new('E-48', "The one order (the card; read it first).", "Key step J (other keys) is not one of the seven: do it at any time after card step 1; it holds nothing up.", NEWCARD)

edit_new('E-48', [
    # item 3 first sentence: no "by 18:29", comes in card step 2, identified apps only
    ("3. You: delete BOTH HubSpot private apps (Settings, Integrations, Private Apps, Delete) by Mon 23 Nov 2026 18:29 UTC = 23:59 IST (the end of the spending window, the same as the rest of this step), and only after your `no more takes` has been confirmed (key step D.3). Make a screenshot",
     "3. You: delete BOTH HubSpot private apps (Settings, Integrations, Private Apps, Delete) in card step 2, right after the key for the model is revoked, only after your confirmation (key step D.3), and only the two apps that you have identified by the check below. On Mon 23 Nov 2026 the spending window ends at 18:29 UTC = 23:59 IST; what you have not finished by then you finish by " + LAST + " (key step D.5). Make a screenshot"),
    # identification paragraph before the second job
    ("   Item 3 has a second job with an EARLIER deadline:",
     "   Identify first, then revoke or delete (the rule for item 2 and item 3). Before the take you wrote on paper or on your phone a list of the two app passwords and of the two HubSpot private apps, with their names and the day each was made, and for each one whether your own n8n (the one at `http://localhost:5678`) uses it (the Phase 0 note, point (5)). On the day, open the page, compare each name and date with that list yourself, and revoke or delete an item only if it is on your list and your list says that your own n8n does not use it. If a name or date is not on your list, or your list says that your own n8n uses it, or you are not sure, touch NOTHING of that kind: tell the assistant the names and dates (never a key or a password) and write it down for the handoff. Deleting a private app cannot be undone (the app and its secret key are gone for good), and it breaks everything that uses it.\n"
     "   Item 3 has a second job with an EARLIER deadline:"),
    ("revoke the key (key step I); then shred the copies (key step G);",
     "revoke the key (key step I); then do your items 2 and 3, the quick web revokes; then shred the copies (key step G);"),
    ("Where a key step says `Detail: appendix K-` and a letter, the detail is on a separate page, Appendix K, which is linked from this step; you do not need it to follow the steps.",
     "Where a key step says `Detail: appendix K-` and a letter, the detail is on a separate page, Appendix K, which is linked from this step (the file `OWNER-APPENDIX-K.md` in the same folder as this sheet); you do not need it to follow the steps. The page for the day itself (the card, the alarms, the last-day plan and the table of typed words) is another separate file in the same folder, `OWNER-DAY-SHEET.md`: open it on the take day."),
    # key step B: one table
    ("Key step B. Only you can write the words. These words count only when you type them yourself, as a new message in your chat with the assistant: `no more takes`, `yes, no more takes`, `another take`, `cut accepted`, `route A`, `route B`, `key revoked`, `key not revoked`, `key gone, no more decisions`, `shred done key copies`, `shred not done key copies`, `shred done other files`, `shred not done other files`, `start clean-up`, `ok stand-in test`, `ok flow rehearsal`, `please stop looking`, `you may look again`, `new key typed; you may look again`, `n8n.env done; you may look again`, the other replies of step 8 and the reply of step 16. Words",
     "Key step B. Only you can write the words. The words in the table at the end of this step count only when you type them yourself, as a new message in your chat with the assistant (the other replies of step 8 and the reply of step 16 are in those steps). One word means one event. Words"),
    # key step C: alarm order, alarm 1 without a confirmation, alarm 2 route
    ("Alarm 1: Mon 23 Nov 2026 17:49 UTC = 23:19 IST, named `revoke the secret key for the model`. Alarm 3: Mon 23 Nov 2026 18:09 UTC = 23:39 IST, named `10 minutes left: revoke the secret key for the model now`. Alarm 2: a repeating alarm in the evening of every day from the day of your first take until Mon 23 Nov 2026 (the time of day is yours, in your own local time), named `is the secret key for the model still alive?`. When alarm 1 rings: if a session with the assistant is open, answer its two questions (key step F); if no session is open, go straight to key step I.",
     "Alarm 1: Mon 23 Nov 2026 17:49 UTC = 23:19 IST, named `revoke the secret key for the model`. Alarm 2: a repeating alarm in the evening of every day from the day of your first take until Mon 23 Nov 2026 (the time of day is yours, in your own local time), named `is the secret key for the model still alive?`. Alarm 3: Mon 23 Nov 2026 18:09 UTC = 23:39 IST, named `10 minutes left: revoke the secret key for the model now`. When alarm 1 rings: if a session with the assistant is open and it asks you its two questions (key step F), answer them, but do not wait for them; if no session is open or it does not ask, go straight to key step I."),
    ("When alarm 2 rings and the key is not yet revoked: if you have not chosen a route, choose one now (key step D.1), then do what your route says.",
     "When alarm 2 rings and the key is not yet revoked: if you have not chosen a route, choose one now (key step D.1); if you have chosen and your last take is done, do key step D.4 for your route (route A: confirm and follow the card; route B: watch the cut)."),
    # D.1: no default pick
    ("The choice is yours, and the assistant recommends route B. Know the price",
     "The choice is yours. No default pick: the assistant does not recommend a route, because nobody can yet limit what a copied key may spend if you miss your alarms (key step A). Know the price"),
    # D.3: no withdrawal, revoke after confirmation
    ("The words `another take` and `no more takes` mean the opposite of each other: read your message again before you send it.",
     "The words `another take` and `no more takes` mean the opposite of each other: read your message again before you send it. You revoke the key only after your confirmation, except at the last time to revoke (key step D.5). A confirmation cannot be withdrawn once the key is revoked: an `another take` typed after the revoke changes nothing, and a retake then needs a new secret key and a new yes (step 20)."),
    # D.4
    ("D.4. Route A: after your last take you write `no more takes`, confirm it, and then you follow the one order (the card) at once, from card step 1, normally on Wed 18 Nov 2026. Route B: after your last take you reply `another take` or send nothing; you watch the cut (step 21), write `cut accepted`, and only then `no more takes`.",
     "D.4. Route A: after your last take you write `no more takes`, the assistant asks the question of D.2 (2), you reply `yes, no more takes`, and then you follow the one order (the card) at once, from card step 1, normally on Wed 18 Nov 2026. Route B: after your last take you write `no more takes` (the assistant answers that in route B it counts only after `cut accepted`, case 3 of D.2) or you send nothing; you use the word `another take` only when you really want another take. You watch the cut (step 21), write `cut accepted`, the assistant asks the question of D.2 (2), and you reply `yes, no more takes`."),
    # D.5: last day plan
    ("D.5. The last time to revoke. If you have not confirmed `no more takes` by Mon 23 Nov 2026 18:19 UTC = 23:49 IST, you revoke the key at that time anyway (key step I) and then write `key gone, no more decisions`: that one message",
     "D.5. The last time to revoke, and the last day. If you have not yet typed `yes, no more takes` by Mon 23 Nov 2026 18:19 UTC = 23:49 IST, you revoke the key at that time anyway (key step I) and then write `key gone, no more decisions`: that one message"),
    ("Between 18:19 UTC = 23:49 IST and 18:29 UTC = 23:59 IST there are only 10 minutes: they are for card step 2 (shred the copies of the key). The other card steps do not fit into them; what you have not finished by 18:29 UTC = 23:59 IST the assistant lists in the handoff with a date to finish it (key step G.2).",
     "Between 18:19 UTC = 23:49 IST and 18:29 UTC = 23:59 IST there are only 10 minutes. Use them in this order: card step 1 (the key), then card step 2 (the app passwords and the HubSpot apps: quick clicks on websites that do not need the key for the model), and only then card step 3 (the shred of the key copies, which protects nothing once the key is dead). What you have not finished by 18:29 UTC = 23:59 IST you finish yourself by " + LAST + ": you act, and nobody does an owner item for you. The assistant lists each open item in the handoff with that date and asks you at your next session (key step G.2). Until you finish them, the HubSpot apps and the app passwords stay alive; they reach only the made-up data of your test accounts. A confirmation cannot be withdrawn once the key is revoked."),
    # G.2: not all
    ("you have written none of these, the assistant does not start item 1; it lists in the handoff everything that is left, with a date to finish, and tells you at your next session.",
     "you have not written ALL of these, the assistant does not start item 1 in that session; it lists in the handoff every item that is left, with the date " + LAST + " (or a later date that you give) as the date to finish, and asks you at your next session. Item 1 may start in a later session, but still only when ALL of these are true. The assistant never does an owner item for you (the web revokes, the shreds, the retire check)."),
    # H: one word per event
    ("copy any made-up word and delete the clipboard history entry; write `you may look again`; replace the old key in that credential",
     "copy any made-up word and delete the clipboard history entry; write `new key typed; you may look again`; replace the old key in that credential"),
    # I: state test, normal revoke after confirmation
    ("Revoke the key, ALWAYS, by 18:19 UTC = 23:49 IST on Mon 23 Nov 2026 at the latest. Revoke it on the website",
     "Revoke the key, ALWAYS, by 18:19 UTC = 23:49 IST on Mon 23 Nov 2026 at the latest; normally you revoke it after your confirmation (key step D.3). Revoke it on the website"),
    ("write `key revoked`; if you have not confirmed `no more takes` and it is the last time to revoke (key step D.5), write `key gone, no more decisions` instead.",
     "write `key revoked`; if you have not yet typed `yes, no more takes`, write `key gone, no more decisions` instead (the key is gone, so there can be no more takes: key step D.5)."),
])
# the Phase 0 note pointers: say where the point is
_n = len(re.findall(r'Phase 0 note, point \(', T))
if _n != 4: errs.append('Phase 0 note pointers %d' % _n)
T = T.replace('Phase 0 note, point (', 'Phase 0 note (under NOT YET CONFIRMED), point (')

# typed-word table at the end of the E-48 block (after key step K text, before the closing fence): placed after the line that starts "Your own copies"
_TABLE = """   Table of the typed words (the one list; each word is one event):
   | You type | The one event it tells the assistant | Key step |
   |---|---|---|
   | `route A` or `route B` | you choose the route (once, before your last take) | D.1 |
   | `no more takes` | you think this take was your last one; it is not final: the assistant asks the question of D.2 (in route B it says that the word counts only after `cut accepted`) | D.2 |
   | `yes, no more takes` | the confirmation (final); the answer to the question of D.2 (2) | D.3 |
   | `another take` | you want another take; no reply counts as this word | D.3 |
   | `cut accepted` | route B: you watched the whole cut and accept it | D.4 |
   | `key gone, no more decisions` | the key is gone AND there are no more takes AND the cut is final; is the confirmation and also `key revoked` | D.5, I |
   | `key revoked` | the key is gone from the list at the provider; a report only, it never confirms anything | I |
   | `key not revoked` | you could not revoke it; write the reason after it | I |
   | `shred done key copies` | every file of parts (a) and (b) is shredded | G.2 |
   | `shred not done key copies` | at least one is not; write the last part of its name and the reason | G.2 |
   | `shred done other files` | every file of parts (c) and (d) is shredded | G.2 |
   | `shred not done other files` | at least one is not; write the last part of its name and the reason | G.2 |
   | `start clean-up` | you have read the list of what the assistant will remove and you want the clean-up | card step 6 |
   | `ok stand-in test` or `ok flow rehearsal` | your yes to that one test, after you checked the web address and the key file path that the assistant named | step 16 |
   | `please stop looking` | you are about to type a secret: the assistant stops looking and answers `not looking` | step 8 a |
   | `you may look again` | you finished typing a secret; the assistant may look again | step 8 a |
   | `new key typed; you may look again` | you typed a new key for the model into the program that uses it (key step H) | H |
   | `n8n.env done; you may look again` | you added your line to `n8n.env` | step 8 g |"""
edit_new('E-48', [("   The assistant never opens the key file (this is a procedure, not enforced by a program).",
                   _TABLE + "\n   The assistant never opens the key file (this is a procedure, not enforced by a program).")])

# ---------------------------------------------------------------- E-16 and E-55: the order is printed once (the card); the start conditions once (key step G.2)
span_new('E-16', "The order of step 22 is the only order:", "and `start clean-up`.",
         "The order of step 22 is the only order: it is the card of step 22 item 3 (the seven steps printed there), and the assistant's item 1 is its card step 7. Item 1 starts only when ALL the conditions of key step G.2 are true (the list is there, once), each as a message that you typed yourself.")
span_new('E-55', "Item 1 starts only when ALL of these are true", "(7) the assistant does its item 1 (the clean-up).",
         "Item 1 starts only when ALL the conditions of key step G.2 are true (the list is there, once). Item 1 deletes the take's credentials and saved runs, stops n8n and removes the take folder and the container, and none of that can be undone, so a retake after it needs a new set-up. The order is the card of item 3 (the seven steps printed there), and you never do a later step before an earlier one.")
edit_new('E-55', [
    ("Revoke the secret key for the model right after you write `no more takes` (item 3 below; in route B of key step D, after `cut accepted`), and in every case by Mon 23 Nov 2026 18:19 UTC = 23:49 IST at the latest (the last time to revoke). Do the rest of the retirement by 18:29 UTC = 23:59 IST (the end of the spending window).",
     "Revoke the secret key for the model right after your confirmation `yes, no more takes` (item 3 below; in route B of key step D, after `cut accepted`), and in every case by Mon 23 Nov 2026 18:19 UTC = 23:49 IST at the latest (the last time to revoke). Do the rest of the retirement by 18:29 UTC = 23:59 IST (the end of the spending window); what you have not finished by then you finish by " + LAST + " (key step D.5)."),
    ("and then you write `key gone, no more decisions`.", "and then you write `key gone, no more decisions`. A confirmation cannot be withdrawn once the key is revoked."),
])

# ---------------------------------------------------------------- E-59: retire check order, the unexplained path
edit_new('E-59', [
    ("Do NOT delete `~/.hadavin-take-tags/<id>.used`.",
     "Order of the retire check (your item 5): it tries to log in with the two secrets in `~/take-secrets` and must be REFUSED, so it needs those two files but no working key; that is why it runs after the HubSpot apps and the app passwords are gone and before these two files are shredded (whether the check needs anything else is UNVERIFIED). If it cannot run, or prints anything but \"refused as expected\" for the mailbox and for HubSpot, shred nothing of part (c), tell the assistant what it printed (never a secret), and finish it by " + LAST + "; item 1 waits until it has passed. Do NOT delete the file `~/.hadavin-take-tags/<id>.used` (a small file that the take program keeps in your Linux home folder for each take id; leave it where it is; what exactly it is for is not checked: UNVERIFIED)."),
])

# ---------------------------------------------------------------- E-62: which contacts
edit_new('E-62', [
    ("If you find more than 3 such contacts, or any other contact, you delete nothing and tell the assistant",
     "Search for `take-<id>-` (with the id of that take). If the search finds more than 3 contacts, or any contact whose e-mail address is not one of these three, you delete nothing and tell the assistant. Whether the take program writes exactly this form of e-mail address is not checked (UNVERIFIED): if the search finds none of these three addresses, delete nothing and tell the assistant"),
])

# ---------------------------------------------------------------- E-37: point (5), the list of the apps and app passwords
edit_new('E-37', [
    ("Add to the list whenever you save a copy later.",
     "Add to the list whenever you save a copy later. (5) Also before the take, write on paper or on your phone (never in a file on this laptop) the NAME of each of the two app passwords of your throwaway mailbox accounts (`desk-read` for the mailbox that receives the take's mails and `desk-send` for the mailbox that sends them, as the page of that account shows them: myaccount.google.com, Security, App passwords; this click path is not checked), and the NAME and the day made of each of the two HubSpot private apps (Settings, Integrations, Private Apps; not checked either), and for each of the four whether your own n8n (the one at `http://localhost:5678`) uses it. Step 22 item 3 uses this list: you revoke or delete only an item that is on it and that your own n8n does not use."),
])

# ---------------------------------------------------------------- Appendix K (outside the rows)
sub("the 10 minutes between are only for the shred of the key copies (card step 2); the other owner items do not fit into them.",
    "the 10 minutes between go first to the key (card step 1), then to the quick web revokes of the app passwords and the HubSpot apps (card step 2), then to the shred of the key copies (card step 3); what is not finished by then you finish by " + LAST + ".")
sub("the studio lead saves it as its own file next to the working copy of OWNER-STEPS and links it from step 22 item 3,",
    "the studio lead saves it as its own file `OWNER-APPENDIX-K.md` (the builder's copy is `r18-OWNER-APPENDIX-K.md`) next to the working copy of OWNER-STEPS and links it from step 22 item 3 by that name,")

# ---------------------------------------------------------------- lead-facing text
sub("(numbered 1 to 14 in the list below the gates)", "(numbered 1 to 16 in the list below the gates)")
sub('and puts the recommendation in ONE sentence of E-48 key step D ("the assistant recommends route B") that the studio lead keeps, changes to A or deletes.',
    'and (round 18, security M2, naive M3) no longer recommends a route: the owner text says "No default pick" and states the price of each route. The assistant must not recommend route B while ND16 is open (a missed alarm leaves a live paid key for up to five days); the studio lead may add a recommendation only after ND16 is answered with option 1 or 2, or after the owner typed the option-3 sentence.')
sub("The spots that carry the recommendation, so that all change together: E-48 key step D, that one sentence only;",
    "The spot that would carry a recommendation, if the studio lead adds one: E-48 key step D.1 only;")
sub("until the studio lead answers, both routes are in the owner text with the one recommendation sentence as written.",
    'until the studio lead answers, both routes are in the owner text with "No default pick".')
sub_line("h. E-12 and E-48:",
         "h. E-12 and E-48: the assistant asks for no start later than 18:00 UTC = 23:30 IST on any day (the latest start we plan; defined in the words list above and confirmed or changed in o), and if a take is still running at 18:19 UTC = 23:49 IST the owner revokes the model key anyway. Both are the builder's choices from Q25. The studio lead's item L-23NOV (ORDERS.md, \"LEAD ANSWERS to your 15:49Z QUESTIONS block\", 2026-11-16) gave the latest start we plan 18:04 UTC = 23:34 IST; since round 15 that figure is REPLACED by 18:00 UTC = 23:30 IST (see o), and the margin that follows from 18:00 UTC = 23:30 IST is NOT confirmed: see o. The rest of L-23NOV stands: key revoked by 18:19 UTC = 23:49 IST even if a take runs, no take planned on 23 Nov (the take targets Wed 18 Nov). The program refusal limit, about 18:14 UTC = 23:44 IST, stays a reading of line 171 and is UNVERIFIED by code.")
sub_line("r. Round 17 additions of the builder",
         "r. Round 17 and round 18 additions of the builder, to confirm: (1) `key revoked` never confirms anything; the owner who has not yet typed `yes, no more takes` revokes and writes `key gone, no more decisions`, which counts as `key revoked` and as the confirmation (round 17, replacing the round 16 rule that a `key revoked` typed after 18:19 UTC = 23:49 IST counts); (2) the reply words were renamed in round 17 (the table of typed words in E-48 key step B is the one list); (3) one number, 30 minutes, for making new keys; (4) ROUND 18 CHANGE, to confirm: the one order has a new sequence: card step 1 = confirm and revoke the key, card step 2 = the quick web revokes (items 2 and 3, each only after the identification check), card step 3 = the shred of the key copies, card step 4 = items 4 and 5, card step 5 = item 6 and the other shreds, card step 6 = `start clean-up`, card step 7 = item 1; so that, on the last day, the 10 minutes between 18:19 UTC = 23:49 IST and 18:29 UTC = 23:59 IST go to the actions that matter first (naive B1, security M1); (5) ROUND 18, to confirm: what is not finished by 18:29 UTC = 23:59 IST on the last day the owner finishes by Tue 24 Nov 2026 18:29 UTC = 23:59 IST (the date is the builder's proposal; name another date if you want one), and item 1 waits for it; (6) ROUND 18: the retire check (item 5) tries to log in with the two secrets and must be refused, so it needs the two files and no working key (the input's own item 5 says so: \"the check needs the two files to try the logins\"); whether it needs anything else is UNVERIFIED; fallback: item 1 waits and the owner finishes it by that date (security M1, naive M2); (7) ROUND 18: the owner text no longer recommends route B (security M2, naive M3): `No default pick` until ND16 is answered; (8) ROUND 18: the owner identifies the app passwords and the HubSpot apps against a list written before the take, and deletes nothing that is not on it or that his own n8n uses (security M3; E-37 point (5)); (9) ROUND 18: Appendix K is the file `OWNER-APPENDIX-K.md` and the page for the day is the file `OWNER-DAY-SHEET.md`, both in the folder of the working copy (the builder's copies are `r18-OWNER-APPENDIX-K.md` and `r18-OWNER-DAY-SHEET.md`): confirm the names and the link; (10) NOT DECIDED 16 is new (security N1).")
sub("that `no more takes` was answered with the one question and confirmed by `yes, no more takes`", "that `no more takes` was answered with the one question and confirmed by `yes, no more takes`")
sub("in its next message after the owner's `no more takes` (E-48, key step E)", "in its next message after the owner's confirmation (`yes, no more takes` or `key gone, no more decisions`; E-48, key step E)")
sub("starts only after the owner's written `no more takes`. The studio lead writes the answer of ND15",
    "starts only after the owner's confirmation (`yes, no more takes` or `key gone, no more decisions`) and the other conditions of key step G.2. The studio lead writes the answer of ND15")
sub("and the revoke follows the owner's `no more takes`).", "and the revoke follows the owner's confirmation `yes, no more takes`, except at the last time to revoke).")
sub("The 18:04 UTC = 23:34 IST latest start we plan leaves only 40 seconds before 18:19 UTC = 23:49 IST (860 seconds is a reading of the program); the owner text says so and the studio lead decides whether to move it.",
    "The 18:04 UTC = 23:34 IST latest start we plan of that round left only 40 seconds before 18:19 UTC = 23:49 IST (860 seconds is a reading of the program); it was replaced in round 15 by 18:00 UTC = 23:30 IST (confirmation o).")
sub("the margin of the latest start we plan (18:04 UTC = 23:34 IST; confirmation o)", "the margin of the latest start we plan (18:00 UTC = 23:30 IST since round 15; confirmation o)")

# counts paragraph and title
sub("Round 17 added no row (the ids and the counts do not change).",
    "Round 18 added no row (the ids and the counts do not change); it rewrote E-48 (the new order of the card, the last-day plan, the table of typed words, the identification rule, no default pick), E-16, E-55, E-37, E-59, E-62 and the Appendix K intro, and made two separate files (`r18-OWNER-DAY-SHEET.md`, `r18-OWNER-APPENDIX-K.md`). Round 17 added no row (the ids and the counts do not change).")
sub("# C4 steps versus decisions: exact edit list (round 17, batched fix pass after the round 16 reviews;", "# C4 steps versus decisions: exact edit list (round 18, batched fix pass after the round 17 reviews;")
sub("## Counts (computed by script, `resolve-r17.md` and `resolve-r17-check-output.txt`)", "## Counts (computed by script, `resolve-r18.md` and `resolve-r18-check-output.txt`)")

# E-24 headings: OLD and NEW of one row, not a duplicate
why_add('E-24', "Round 18 (naive m9): the two headings that look alike (\"UNVERIFIED list (count: 13)\" and \"UNVERIFIED list (17 live items ...)\") are the OLD and the NEW text of this one row, not a duplicate; applying the row replaces the first by the second.")

# Why additions (history stays in the Why lines)
why_add('E-48', "Round 18 (security M1, M2, M3, minors 1 to 3; naive B1, M1 to M3, M5, M6, minors 3 to 5): (a) the card has a new order: confirm and revoke the key, then the quick web revokes (items 2 and 3, each after the identification check), then the shred of the key copies, then items 4 and 5, item 6, `start clean-up`, item 1; the card is printed once here and once, generated from the same list, in the day sheet; E-16 and E-55 point to it; (b) the last-day plan names who acts and by when: the 10 minutes go to the key, then the web revokes, then the shreds; what is open at 18:29 UTC = 23:59 IST the owner finishes by Tue 24 Nov 2026 18:29 UTC = 23:59 IST (the builder's proposal); item 3 no longer says \"by 18:29\"; (c) the revoke comes after the typed confirmation except at the last time to revoke, and a confirmation cannot be withdrawn once the key is revoked (D.3, D.5); (d) no default pick of a route while ND16 is open; (e) the owner identifies the app passwords and the HubSpot apps against his own list before he revokes or deletes (E-37 point (5)); (f) one table of typed words replaces the inline list; route B no longer uses `another take` for a take that is the last one; `new key typed; you may look again` is the only word after a new key; (g) `not all` replaces `none of these`; key step I uses a state test (not yet typed `yes, no more takes`) instead of the moment; the alarm order is 1, 2, 3; alarm 1 does not wait for the questions of key step F.")
why_add('E-16', "Round 18 (naive B2): the order and the start conditions are no longer printed here; they are the card of item 3 and key step G.2 (one source each).")
why_add('E-55', "Round 18 (security M1; naive B2, m9): the revoke follows the confirmation `yes, no more takes`; the order and the start conditions are no longer printed here; a confirmation cannot be withdrawn once the key is revoked; what is open on the last day is finished by Tue 24 Nov 2026 18:29 UTC = 23:59 IST.")
why_add('E-59', "Round 18 (security M1; naive M2, m1): the retire check needs the two files and no working key (the input's item 5 says that the check needs the two files to try the logins); the fallback is stated; the file `~/.hadavin-take-tags/<id>.used` is explained as far as it is known.")
why_add('E-62', "Round 18 (security m5): the search for `take-<id>-` is named; any contact in that search whose address is not one of the three means delete nothing; the address form is UNVERIFIED in the owner text too.")
why_add('E-37', "Round 18 (security M3): point (5) asks the owner to write the names and days of the app passwords and the HubSpot apps, and whether his own n8n uses each, before the take.")

# ---------------------------------------------------------------- the end of the file: what was not checked in round 18
T = T.rstrip('\n') + "\n- Round 18 added: nothing was run on a take; no click path was opened; the text and counts were checked by `verify18.py` (see `resolve-r18-check-output.txt`). UNVERIFIED and unchanged: that a take stops safely when its key is revoked; that the retire check needs no working key (the input says it needs the two files; the code was not read); the form of the take contact addresses; the purpose of the `.used` file; whether the company that provides the AI model can limit a key (N1). Owner-open: ND15 route, ND16, the date Tue 24 Nov 2026 for what is open after 18:29 UTC = 23:59 IST on the last day, confirmation o.\n"

if errs:
    print('ERRORS', len(errs))
    for e in errs: print(' ', e)
    sys.exit(1)

# ---------------------------------------------------------------- separate files (generated from the same lists)
_E48 = '\n'.join(block_get('E-48'))
_tab = _TABLE.replace('   Table of the typed words (the one list; each word is one event):\n', '')
_tab = '\n'.join(l[3:] if l.startswith('   ') else l for l in _tab.split('\n'))
_alarm_i = _E48.index('Key step C. Your alarms.')
_alarm = _E48[_alarm_i:_E48.index('Detail: appendix K-C.', _alarm_i)].replace('Key step C. ', '')
_d5 = _E48[_E48.index('D.5. The last time to revoke'):_E48.index('Key step E.')].strip()
_g2i = _E48.index('G.2. When you are done')
_g2 = _E48[_g2i:_E48.index('Key step H.', _g2i)].strip()
DAY = ("# OWNER-DAY-SHEET: the page for the take day (saved in the same folder as the owner sheet)\n\n"
       "This page is for the day of the take. It repeats nothing new: the card, the alarms, the last-day plan and the table of typed words are the same text as in step 22 item 3 of the owner sheet (key steps B to D and G), and the full reasons are in `OWNER-APPENDIX-K.md`. "
       "Only messages that you type yourself, as a new message in your chat with the assistant, count.\n\n"
       "## The card\n" + CARD_HEAD + "\n" + "\n".join(l.strip() for l in CARD_LINES) + "\n" + LASTDAY.strip() + "\n" + CARD_TAIL + "\n\n"
       "## Your three alarms\nYour alarms. " + _alarm.split('Your alarms. ', 1)[1].strip() + "\n\n"
       "## The last day\n" + _d5 + "\n\n"
       "## When the clean-up may start\n" + _g2 + "\n\n"
       "## Table of the typed words\n\n" + _tab + "\n")
open(D + 'r18-OWNER-DAY-SHEET.md', 'w', encoding='utf-8').write(DAY)
_ai = T.index('\n## Appendix K'); _aj = T.index('\n## ', _ai + 5)
APPX = T[_ai:_aj].strip() + "\n"
open(D + 'r18-OWNER-APPENDIX-K.md', 'w', encoding='utf-8').write(APPX)
open(D + 'EDITS.md', 'w', encoding='utf-8').write(T)
print('written', len(T.split('\n')), 'lines; day sheet words', len(DAY.split()), '; appendix words', len(APPX.split()))
