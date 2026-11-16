"""Round 19 builder: anchored patches of EDITS.round18.md (every old string asserted to occur the stated number of times).
Writes EDITS.md, r19-OWNER-DAY-SHEET.md and r19-OWNER-APPENDIX-K.md. No vendor words, no secrets. Paths are relative to this file."""
import re, sys, os
D = os.path.dirname(os.path.abspath(__file__)) + '/'
_head = open(D + 'build-r17-head.py', encoding='utf-8').read().replace('EDITS.round16.md', 'EDITS.round18.md')
exec(_head)

LAST = "Tue 24 Nov 2026 18:29 UTC = 23:59 IST"
TBC = " (this date is to be confirmed by the studio lead before you rely on it)"
# ONE sentence for the key and the last 10 minutes: copied exactly, never reworded
KS = ("The key is revoked by 18:19 UTC = 23:49 IST; the last 10 minutes (18:19 UTC = 23:49 IST to 18:29 UTC = 23:59 IST) are for card steps 2 and 3; "
      "if the key is still live at 18:19 UTC = 23:49 IST it comes first.")
# ONE wording for the three words around the confirmation
TW = ("`no more takes` alone is never final; the confirmation is `yes, no more takes`; "
      "if you have revoked the key without having typed `yes, no more takes`, write `key gone, no more decisions`.")
WARN3 = "In route B, writing `key gone, no more decisions` before you have watched the cut makes the cut final and costs you the retake."
WHY = ("Why these two times: 18:29 UTC = 23:59 IST is the end of the spending window (from then on the model stage may not spend money). "
       "18:19 UTC = 23:49 IST is the last time to revoke, set by the security decision of 16 Nov 2026, so that the key is dead before the window ends; "
       "the key can spend until the moment it is revoked, which is why it comes first in the last 10 minutes.")
WD = ("Words in this item: a step is a numbered step of this sheet; an item is one of the numbered items 1 to 6 of step 22; a key step is one of the lettered key steps A to K; "
      "a card step is one of the seven numbered lines of the card; `the key` always means the secret key for the model that the take used (every other key is named); "
      "`the last 10 minutes` means only the span that the last-day sentence of the card names; the retire check is your item 5 (it tries to log in with the two secrets that the take used, and every login must be refused); "
      "the retirement is the whole of step 22.")
ONELINES = [
    "One line each for items 2 to 6 (the full text of each item is in step 22; open it if a line is not enough):",
    "   Item 2 (app passwords): on the page of app passwords of each throwaway mailbox, revoke each app password that passes the identification check, then open the page again to see that it is gone.",
    "   Item 3 (HubSpot apps): in HubSpot (Settings, Integrations, Private Apps), delete each app that passes the identification check; a deleted app cannot come back; then make a cropped screenshot.",
    "   Item 4 (screenshots): save your cropped screenshots of the key list, the app passwords page and the HubSpot apps page; they show no key characters, no account name and no web address.",
    "   Item 5 (the retire check): run it as step 22 item 5 says; it must print \"refused as expected\" for the mailbox and for HubSpot; if it prints anything else, shred nothing of part (c) and tell the assistant what it printed (never a secret).",
    "   Item 6 (the two files in `~/take-secrets`): shred each of the two files, one at a time, by the shred rule of key step G, only after item 5 has passed.",
]

# ---------------------------------------------------------------- the seven steps of the one order: ONE source (this list)
P = [
    "make sure that you have confirmed your last take with `yes, no more takes` (key step D.3), then revoke the secret key for the model (key step I) and write `key revoked` (on Mon 23 Nov 2026, if you have not typed `yes, no more takes` by 18:19 UTC = 23:49 IST, revoke the key at that time anyway and write `key gone, no more decisions` instead of `yes, no more takes` and `key revoked`)",
    "do your items 2 and 3, the quick web revokes, each only after the identification check of step 22 item 3 (item 2: revoke each app password that passes the check; item 3: delete each HubSpot app that passes the check; touch nothing that you are not sure about; for an item that you leave, write `web revokes not done`, its name and the reason)",
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
LASTDAY = ("   Last day, Mon 23 Nov 2026: " + KS + " What you have not finished by 18:29 UTC = 23:59 IST you finish by " + LAST + TBC + " (key step D.5); "
           "the key is never one of those things: it is not deferrable (key step D.5).")
NEWCARD = CARD_HEAD + "\n" + "\n".join(CARD_LINES) + "\n" + LASTDAY + "\n" + "\n".join("   " + l.strip() if i == 0 else l for i, l in enumerate(ONELINES)) + "\n   " + CARD_TAIL
span_new('E-48', "The one order (the card; read it first).", "Key step J (other keys) is not one of the seven: do it at any time after card step 1; it holds nothing up.", NEWCARD)

# ---------------------------------------------------------------- E-48 text patches
edit_new('E-48', [
    # item 3: only apps that pass the check
    ("3. You: delete BOTH HubSpot private apps (Settings, Integrations, Private Apps, Delete) in card step 2, right after the key for the model is revoked, only after your confirmation (key step D.3), and only the two apps that you have identified by the check below. On Mon 23 Nov 2026 the spending window ends at 18:29 UTC = 23:59 IST; what you have not finished by then you finish by " + LAST + " (key step D.5).",
     "3. You: delete the HubSpot private apps (Settings, Integrations, Private Apps, Delete): BOTH apps if both pass the identification check below, and only the apps that pass it. Do it in card step 2, right after the key for the model is revoked, only after your confirmation (key step D.3; the exceptions are named there). An app that does not pass stays, and you write `web revokes not done` (key step G.2). On Mon 23 Nov 2026 the spending window ends at 18:29 UTC = 23:59 IST; what you have not finished by then you finish by " + LAST + TBC + " (key step D.5)."),
    # the identification paragraph: which app counts as used; the typed word for "not deleted"
    ("and for each one whether your own n8n (the one at `http://localhost:5678`) uses it (the Phase 0 note (under NOT YET CONFIRMED), point (5)). On the day,",
     "and for each one whether your own n8n (the one at `http://localhost:5678`) uses it (the Phase 0 note (under NOT YET CONFIRMED), point (5)). Which one counts as used by your own n8n: a HubSpot app counts as used when the HubSpot credential in your own n8n (your statement says that it has one) holds that app's secret key; an app password counts as used when the Gmail credential in your own n8n holds it; which key or password those credentials hold is not known (UNVERIFIED), so before the take you open each of them and write beside each of the four items `used` or `not used`, and where you cannot tell you write `used`; the app that step 7 calls the app for n8n (app 2) is the one most likely to be used. On the day,"),
    ("touch NOTHING of that kind: tell the assistant the names and dates (never a key or a password) and write it down for the handoff.",
     "touch NOTHING of that kind: write `web revokes not done`, the names and dates and the reason (never a key or a password). The assistant lists each such item in the handoff with you as its owner and the date " + LAST + TBC + ", and item 1 may still start (key step G.2); the retire check is not run for it (your item 6 says what to do)."),
    # intro line: words, appendix wording
    ("Each key step is short. Where it says \"Detail\", the reasons and the long checks are in the appendix of this sheet, part K, under the same letter; you do not need the appendix to act.",
     "Each key step is short. Where it says \"Detail\", the reasons and the long checks are in Appendix K (a separate page, linked below), under the same letter; you do not need the appendix to act. " + WD),
    # in short
    ("In short: set three alarms (key step C); choose route A or route B and, after your last take that you accept, confirm `no more takes` (key step D; in route B after `cut accepted`);",
     "In short: set four alarms (key step C); choose route A or route B and, after your last take that you accept, confirm it (key step D; in route B after `cut accepted`): " + TW + " "),
    # key step A: 10 minutes meaning, why
    ("The spending window ends 10 minutes later, at 18:29 UTC = 23:59 IST; that is when the model stage must stop spending.",
     "The spending window ends at 18:29 UTC = 23:59 IST; that is when the model stage must stop spending. " + WHY),
    # key step B
    ("`key gone, no more decisions` is a separate word with three meanings at once: the key is gone, you want no more takes, and (in route B) the cut is final. Use it only when all three are true. It counts as `key revoked` and as the confirmation, so after it you do not type `key revoked` again.",
     "`key gone, no more decisions` is the one word with three meanings at once (the key is gone, you want no more takes, and in route B the cut is final; the table says so). Use it only when all three are true, or when you revoke at the last time to revoke. It counts as `key revoked` and as the confirmation, so after it you do not type `key revoked` again. " + TW + " " + WARN3),
    # key step C: four alarms, alarm 3 renamed, alarm 4, turn alarm 2 off
    ("Set three alarms on your own phone or computer. Alarm 1:", "Set four alarms on your own phone or computer. Alarm 1:"),
    ("Alarm 3: Mon 23 Nov 2026 18:09 UTC = 23:39 IST, named `10 minutes left: revoke the secret key for the model now`.",
     "Alarm 3: Mon 23 Nov 2026 18:09 UTC = 23:39 IST, named `last chance: revoke the secret key for the model now`. Alarm 4: Tue 24 Nov 2026 06:00 UTC = 11:30 IST" + TBC + ", named `if the secret key for the model is still not revoked, revoke it now`; it is only for the case that you missed alarms 1 to 3 (key step D.5). Turn alarm 2 off when you have written `key revoked` or `key gone, no more decisions`."),
    # D.1: both prices, no tilt
    ("Know the price of route B before you choose: the secret key for the model and its copy stay alive on this laptop for up to five days (Wed 18 Nov to Mon 23 Nov 2026), and the revoke on the last day depends only on you and your alarms. Route A is the safer one for keeping secrets safe; route B keeps the chance of a retake.",
     "Know the price of each route before you choose. Route A: after your confirmation the clean-up removes the take's set-up and you delete the HubSpot apps and the app passwords, so a retake after a bad cut needs a whole new set-up (new HubSpot apps with a new secret key, new app passwords, a new secret key for the model and a new yes: step 20). Route B: the secret key for the model and its copy stay alive on this laptop for up to five days (Wed 18 Nov to Mon 23 Nov 2026), and the revoke on the last day depends only on you and your alarms; in return a retake after a bad cut is possible. In route A the live key exists for hours, in route B for up to five days."),
    # D.3: exceptions, retake price
    ("You revoke the key only after your confirmation, except at the last time to revoke (key step D.5). A confirmation cannot be withdrawn once the key is revoked: an `another take` typed after the revoke changes nothing, and a retake then needs a new secret key and a new yes (step 20).",
     "You revoke the key only after your confirmation. The exceptions are alarm 1 and alarm 3 (key step C) and the last time to revoke (key step D.5): there you revoke first and write `key gone, no more decisions`. A confirmation cannot be withdrawn once the key is revoked: an `another take` typed after the revoke changes nothing, and a retake then needs the whole new set-up of the route A price in key step D.1 and a new yes (step 20)."),
    # D.5
    ("D.5. The last time to revoke, and the last day. If you have not yet typed `yes, no more takes` by Mon 23 Nov 2026 18:19 UTC = 23:49 IST, you revoke the key at that time anyway (key step I) and then write `key gone, no more decisions`: that one message tells the assistant that the key is gone, that there are no more takes and (in route B) that the cut is final.",
     "D.5. The last time to revoke, and the last day. If you have not yet typed `yes, no more takes` by Mon 23 Nov 2026 18:19 UTC = 23:49 IST, you revoke the key at that time anyway (key step I) and then write `key gone, no more decisions`: that one message tells the assistant that the key is gone, that there are no more takes and (in route B) that the cut is final. " + TW + " " + WARN3),
    ("Between 18:19 UTC = 23:49 IST and 18:29 UTC = 23:59 IST there are only 10 minutes. Use them in this order: card step 1 (the key), then card step 2 (the app passwords and the HubSpot apps: quick clicks on websites that do not need the key for the model), and only then card step 3 (the shred of the key copies, which protects nothing once the key is dead). What you have not finished by 18:29 UTC = 23:59 IST you finish yourself by " + LAST + ": you act, and nobody does an owner item for you. The assistant lists each open item in the handoff with that date and asks you at your next session (key step G.2). Until you finish them, the HubSpot apps and the app passwords stay alive; they reach only the made-up data of your test accounts. A confirmation cannot be withdrawn once the key is revoked.",
     KS + " What you have not finished by 18:29 UTC = 23:59 IST you finish yourself by " + LAST + TBC + ": you act, and nobody does an owner item for you. The assistant lists each open item in the handoff with you as its owner and that date, and asks you at your next session (key step G.2). Until you finish them, the HubSpot apps and the app passwords that you left stay alive; the builder believes that they reach only the made-up data of your test accounts, but that is UNVERIFIED (the permissions of the HubSpot apps are not checked, and that the mailbox accounts are throwaway rests on your statement only). THE KEY IS NOT DEFERRABLE: it is not one of the things that you may finish by Tue 24 Nov. If you missed 18:19 UTC = 23:49 IST: revoke the key at once, from any device that can open the website of the company that provides the AI model (a phone browser is enough), tell the assistant at once, and write `key gone, no more decisions`; every minute that the key lives it can spend (key step I). Alarm 4 (key step C) is for this case. If you cannot reach the website, a second person whom you have named for this may revoke the key (whether such a person exists is open: the studio lead tells you). A confirmation cannot be withdrawn once the key is revoked."),
    # G.2: web revokes not done, owner and date, item 1 may start
    ("Item 1 may start in a later session, but still only when ALL of these are true.",
     "Item 1 may start in a later session, but still only when ALL of these are true. An item 2 or item 3 that you left under the identification rule counts as done in this list once you wrote `web revokes not done`, its name and the reason."),
    ("it lists in the handoff every item that is left, with the date " + LAST + " (or a later date that you give) as the date to finish, and asks you at your next session.",
     "it lists in the handoff every item that is left, with you as its owner and the date " + LAST + TBC + " (or a later date that you give) as the date to finish, and asks you at your next session."),
    # H word
    # I: exceptions, late is not fine-but, one wording
    ("normally you revoke it after your confirmation (key step D.3). Revoke it on the website",
     "normally you revoke it after your confirmation (key step D.3); alarm 1, alarm 3 and the last time to revoke (key step D.5) are the exceptions. If it is already after 18:19 UTC = 23:49 IST, revoke it anyway and at once: 18:19 UTC = 23:49 IST is the last time that we plan, not a time after which revoking is useless, because the key can spend until it is revoked. Revoke it on the website"),
    ("write `key revoked`; if you have not yet typed `yes, no more takes`, write `key gone, no more decisions` instead (the key is gone, so there can be no more takes: key step D.5).",
     "write `key revoked`; if you have not yet typed `yes, no more takes`, write `key gone, no more decisions` instead (key step D.5). " + TW + " " + WARN3),
    # table
    ("   Table of the typed words (the one list; each word is one event):",
     "   Table of the typed words (the one list; each word is one event, except `key gone, no more decisions`, which is three events at once and is marked as such):"),
    ("   | `key gone, no more decisions` | the key is gone AND there are no more takes AND the cut is final; is the confirmation and also `key revoked` | D.5, I |",
     "   | `key gone, no more decisions` | THREE events at once, on purpose: the key is gone AND there are no more takes AND the cut is final; it is the confirmation and also `key revoked`; in route B, writing it before you watched the cut costs you the retake | D.5, I |"),
    ("   | `shred done key copies` | every file of parts (a) and (b) is shredded | G.2 |",
     "   | `web revokes not done` | you left an app password or a HubSpot app on purpose (it did not pass the identification check); write its name and the reason after it | item 3, G.2 |\n   | `shred done key copies` | every file of parts (a) and (b) is shredded | G.2 |"),
])

# ---------------------------------------------------------------- step 16 owner text: four alarms, the renamed alarm
sub("Set three alarms on your own phone or computer (step 22 item 3, key step C): alarm 1 for 17:49 UTC = 23:19 IST on Mon 23 Nov 2026, named `revoke the secret key for the model`; alarm 3 for 18:09 UTC = 23:39 IST the same day, named `10 minutes left: revoke the secret key for the model now` (if a take is running when it rings, you let it finish and then revoke at once, never later than 18:19 UTC = 23:49 IST); and alarm 2, which repeats every evening from the day of your first take (your own phone time), named `is the secret key for the model still alive?`.",
    "Set four alarms on your own phone or computer (step 22 item 3, key step C): alarm 1 for 17:49 UTC = 23:19 IST on Mon 23 Nov 2026, named `revoke the secret key for the model`; alarm 3 for 18:09 UTC = 23:39 IST the same day, named `last chance: revoke the secret key for the model now` (if a take is running when it rings, you let it finish and then revoke at once, never later than 18:19 UTC = 23:49 IST); alarm 2, which repeats every evening from the day of your first take (your own phone time), named `is the secret key for the model still alive?`; and alarm 4 for Tue 24 Nov 2026 06:00 UTC = 11:30 IST" + TBC + ", named `if the secret key for the model is still not revoked, revoke it now`, for the case that you missed the others.")
sub("The owner's three alarms (key step C: 17:49 UTC = 23:19 IST and 18:09 UTC = 23:39 IST on 23 Nov, and a repeating evening alarm from the first take) are",
    "The owner's four alarms (key step C: 17:49 UTC = 23:19 IST and 18:09 UTC = 23:39 IST on 23 Nov, a repeating evening alarm from the first take, and 06:00 UTC = 11:30 IST on Tue 24 Nov, a date that the studio lead still has to confirm) are")
sub("key step A is a promise by the owner backed by his three alarms; the program has no timer; all three alarms are on one person's device;",
    "key step A is a promise by the owner backed by his four alarms; the program has no timer; all four alarms are on one person's device;")

# ---------------------------------------------------------------- E-37 pointer
edit_new('E-37', [("and for each of the four whether your own n8n (the one at `http://localhost:5678`) uses it.",
                   "and for each of the four whether your own n8n (the one at `http://localhost:5678`) uses it (what counts as used is defined in the identification check of step 22 item 3; where you cannot tell, write `used`).")])

# ---------------------------------------------------------------- E-55: heading, exceptions, date
edit_new('E-55', [
    ("### Step 22. Retirement: the key revoked by Mon 23 Nov 2026 18:19 UTC = 23:49 IST, the rest by 18:29 UTC = 23:59 IST",
     "### Step 22. Retirement: the key revoked by Mon 23 Nov 2026 18:19 UTC = 23:49 IST (never later), the rest by 18:29 UTC = 23:59 IST, and what is still open then by Tue 24 Nov 2026 18:29 UTC = 23:59 IST" + TBC),
    ("Do the rest of the retirement by 18:29 UTC = 23:59 IST (the end of the spending window); what you have not finished by then you finish by " + LAST + " (key step D.5).",
     KS + " Do the rest of the retirement by 18:29 UTC = 23:59 IST (the end of the spending window); what you have not finished by then you finish by " + LAST + TBC + " (key step D.5); the key is not one of those things."),
    ("The one exception to the waiting is the last time to revoke the secret key for the model: at 18:19 UTC = 23:49 IST on Mon 23 Nov 2026 you revoke it whatever you have written, and then you write `key gone, no more decisions`.",
     "The exceptions to the waiting are alarm 1, alarm 3 and the last time to revoke the secret key for the model: at 18:19 UTC = 23:49 IST on Mon 23 Nov 2026 you revoke it whatever you have written, and then you write `key gone, no more decisions`. " + TW),
])
# ---------------------------------------------------------------- E-57 (step 21): one wording, both prices, no tilt
edit_new('E-57', [
    ("Route B: you have not written `no more takes` yet.", "Route B: you have not yet typed `yes, no more takes`."),
    ("Route A is the safer one for keeping secrets safe. Write `no more takes` only after `cut accepted`. In route B you must watch the cut and write both words before 18:19 UTC = 23:49 IST on Mon 23 Nov 2026, because the key is revoked at that time in every case.",
     "In route A the live key exists for hours, in route B for up to five days. Write `yes, no more takes` only after `cut accepted`. In route B you must watch the cut, write `cut accepted` and then `yes, no more takes` before 18:19 UTC = 23:49 IST on Mon 23 Nov 2026, because the key is revoked at that time in every case. " + TW),
])
# ---------------------------------------------------------------- E-58: send table after the last day
edit_new('E-58', [("| Mon 23 Nov 2026, by 18:29 UTC = 23:59 IST | the other retirement screenshots and the retire-check output (counts and words only) |",
                   "| Mon 23 Nov 2026, by 18:29 UTC = 23:59 IST (what is still open then is finished by " + LAST + TBC + ") | the other retirement screenshots and the retire-check output (counts and words only) |")])
# ---------------------------------------------------------------- E-59: retire check with a left item
edit_new('E-59', [("Do NOT delete the file `~/.hadavin-take-tags/<id>.used`",
                   "If you wrote `web revokes not done` for the mailbox or for HubSpot, that login cannot be refused: do not run the check for it, do not shred its file of part (c) yet (the check needs it), and write `shred not done other files` with the reason; the item stays in the handoff with you as its owner and the date " + LAST + TBC + ". Do NOT delete the file `~/.hadavin-take-tags/<id>.used`")])

# ---------------------------------------------------------------- Appendix K (outside the rows)
_k1 = "the 10 minutes between go first to the key (card step 1), then to the quick web revokes of the app passwords and the HubSpot apps (card step 2), then to the shred of the key copies (card step 3); what is not finished by then you finish by " + LAST + "."
sub(_k1, KS + " What is not finished by then you finish by " + LAST + TBC + "; the key is not one of those things (key step D.5).")
sub("The spending window ends at 18:29 UTC = 23:59 IST; " + KS + " What is not finished",
    "The spending window ends at 18:29 UTC = 23:59 IST. " + KS + " What is not finished")
_k2 = "then you have at most 10 minutes between 18:19 UTC = 23:49 IST and 18:29 UTC = 23:59 IST, and they go first to the key (card step 1), then to the quick web revokes (card step 2), then to the shred of the key copies (card step 3)."
sub(_k2, "then this applies: " + KS)
sub("If you have not written `no more takes` (in route B: `cut accepted` and `no more takes`) by 18:19 UTC = 23:49 IST on Mon 23 Nov 2026, key step D.5 applies.",
    "If you have not typed `yes, no more takes` (in route B: after `cut accepted`) by 18:19 UTC = 23:49 IST on Mon 23 Nov 2026, key step D.5 applies. " + TW)
sub("From the point of view of keeping secrets safe route A is the safer one. ", "In route A the live key exists for hours, in route B for up to five days. ")
sub("whether item 1 should shred them is not decided yet and is a question for the studio lead. ", "item 1 does not shred them (shred is not reliable on every disk). ")
sub("so that the sheet itself stays short (order L-LEN). Where a key step says",
    "so that the key steps in the sheet stay short; the sheet as a whole is NOT short (L-LEN is not met: see `r19-CHANGES.md`, section 1, item 1). Where a key step says")
sub("(the builder's copy is `r18-OWNER-APPENDIX-K.md`)", "(the builder's copy is `r19-OWNER-APPENDIX-K.md`)")
sub("`r18-OWNER-DAY-SHEET.md`, `r18-OWNER-APPENDIX-K.md`)", "`r18-OWNER-DAY-SHEET.md`, `r18-OWNER-APPENDIX-K.md`; round 19 writes `r19-OWNER-DAY-SHEET.md` and `r19-OWNER-APPENDIX-K.md`)")

# ---------------------------------------------------------------- lead-facing: ND15, ND17 (new item), R10, history, stale lines
sub("**When the owner writes `no more takes`: right after", "**When the owner types `yes, no more takes` (the confirmation; `no more takes` alone is never final): right after")
sub("- **R10 (E-48, E-55, E-57, E-58)**: two routes (ND15), one deadline per act: revoke the key (18:19 UTC = 23:49 IST at the latest), watch the cut (the same 18:19 UTC = 23:49 IST), the rest of the retirement (18:29 UTC = 23:59 IST).",
    "- **R10 (E-48, E-55, E-57, E-58)**: two routes (ND15), one deadline per act: revoke the key (18:19 UTC = 23:49 IST at the latest; it is never deferred; alarm 4 on Tue 24 Nov 2026 is the last prompt), watch the cut (the same 18:19 UTC = 23:49 IST), the rest of the retirement (18:29 UTC = 23:59 IST; what is still open then by " + LAST + ", a date that the studio lead still has to confirm). If an owner path of E-37 point (5) (the list of the app passwords and apps) is missing, the assistant treats items 2 and 3 as `web revokes not done` and says so (checked in the chat record).")
sub("Round 17 (`resolve-r17.md`, same paths: no round cap) applies all of those findings in one batch. The result of round 17 is NOT reviewed yet.",
    "Round 17 (`resolve-r17.md`, same paths: no round cap) applied all of those findings in one batch; its result was reviewed (`review-r17-security.md`, `review-r17-naive.md`, `review-r17-evidence.md`). Round 18 (`resolve-r18.md`) did the same; its result was reviewed (`review-r18-security.md`: 0 Blockers, 4 Majors, 6 Minors; `review-r18-stranger.md`: 3 Blockers, 5 Majors, 9 Minors; independent evidence in `evidence-r18-independent/`). Round 19 (`r19-CHANGES.md`, same paths: no round cap) applies all of those findings in one batch. The result of round 19 is NOT reviewed yet.")
sub("`EDITS.round11.md` to `EDITS.round16.md` (rounds 11 to 16).", "`EDITS.round11.md` to `EDITS.round18.md` (rounds 11 to 18).")
sub("# C4 steps versus decisions: exact edit list (round 18, batched fix pass after the round 17 reviews;", "# C4 steps versus decisions: exact edit list (round 19, batched fix pass after the round 18 reviews;")
sub("## Counts (computed by script, `resolve-r18.md` and `resolve-r18-check-output.txt`)", "## Counts (computed by script, `r19-CHANGES.md` and `resolve-r19-check-output.txt`)")
sub("- Dates and times (IST/UTC conversions, 14 versus 15 minutes) were not recomputed.",
    "- Dates and times: from round 16 on every UTC/IST pair is recomputed by script (`verify19.py`); the reading of the program's running time (860 seconds, 14 minutes 20 seconds) is not recomputed from code (UNVERIFIED).")
sub("the number of rows stays 56", "the number of rows stays 60")
sub("(numbered 1 to 16 in the list below the gates)", "(numbered 1 to 17 in the list below the gates)")
sub("## NOT DECIDED: studio lead or owner only (items 1 to 16).", "## NOT DECIDED: studio lead or owner only (items 1 to 17).")
# ND17 appended after item 16 (the line that starts "16. **Nobody but the owner")
_ls = T.split('\n'); _i16 = [k for k, l in enumerate(_ls) if l.startswith('16. **Nobody but the owner')]
if len(_i16) != 1: errs.append('ND16 line count %d' % len(_i16))
else:
    _ls.insert(_i16[0] + 1, "17. **Does item 1 (the clean-up) shred n8n's own settings folder (it holds n8n's encryption key) and the take's database files, or remove them with a plain remove?** (E-48 Appendix K-G; open since round 16, moved here from the owner text in round 19.) Who answers: the studio lead. Options: (a) plain remove (today: the content may stay in free space on the disk until it is overwritten); (b) shred them (cost: more clean-up time and a path check for each file; risk: shred is not reliable on every disk, so (b) does not prove removal). Default: (a), with the sentence of K-G as it stands. Record: `ND17: a|b`.")
    T = '\n'.join(_ls)
sub("- Round 18 added: nothing was run on a take;", "- Round 19 added: nothing was run on a take; no click path was opened; the text and counts were checked by `verify19.py` (see `resolve-r19-check-output.txt`). UNVERIFIED and unchanged: the rest of the list of round 18. New and UNVERIFIED: which key or password the credentials of your own n8n hold (the identification rule says what to do when that is unknown); that the HubSpot apps and the mailbox accounts reach only made-up data; whether a second person who may revoke the key exists (NOT DECIDED 16); the date Tue 24 Nov 2026 and alarm 4 (marked in the owner text as to be confirmed by the studio lead).\n- Round 18 added: nothing was run on a take;")

# Why additions
why_add('E-48', "Round 19 (security M1 to M4, minors 1 to 6; stranger B1 to B3, M1 to M5, minors 1 to 9): (a) ONE sentence for the key and the last 10 minutes, copied exactly (card, D.5, E-55, Appendix K-A and K-D); `the last 10 minutes` has one meaning; alarm 3 is renamed `last chance: ...` so that it no longer says `10 minutes left`; (b) the key is not deferrable; if missed: revoke at once from any device and tell the assistant; alarm 4 on Tue 24 Nov 2026 06:00 UTC = 11:30 IST; the Tue 24 date is marked in the owner text as to be confirmed by the studio lead; (c) the typed word `web revokes not done` lets item 1 start when the identification rule says touch nothing; `used by your own n8n` is defined; item 3 deletes only apps that pass the check; the leftover is in the handoff with the owner and the date; (d) the day sheet gets key step I, the shred rule (key step G), the identification check, one line each for items 2 to 6, the reason for 18:19 and 18:29, and the words used; (e) one wording (`TW`) for `no more takes`, `yes, no more takes` and `key gone, no more decisions`, a warning for route B, alarms 1 and 3 named as exceptions to revoke-after-confirmation; (f) route A's full price is in D.1; no sentence tilts to route A; (g) stale text and open questions moved out of owner text (ND17).")
why_add('E-55', "Round 19 (security M2, m1; stranger B1, M5): heading and body say what is open on Tue 24 Nov 2026 (to be confirmed); alarms 1 and 3 are exceptions; the key is not deferrable.")
why_add('E-57', "Round 19 (stranger M2, M3): route A's price is in key step D.1; `yes, no more takes` is the one word of the confirmation; no sentence tilts to a route.")
why_add('E-58', "Round 19 (stranger M5): the send row for the last day names Tue 24 Nov 2026 (to be confirmed) for what is still open.")
why_add('E-59', "Round 19 (security M1): the retire check is not run for an item left under `web revokes not done`; its file of part (c) stays until the check has passed.")
why_add('E-37', "Round 19 (security M1): what counts as used by your own n8n is defined in step 22 item 3; where the owner cannot tell, he writes `used`.")

if errs:
    print('ERRORS', len(errs))
    for e in errs: print(' ', e)
    sys.exit(1)

# ---------------------------------------------------------------- separate files (generated from the same lists)
_E48 = '\n'.join(block_get('E-48'))
_tab = _E48[_E48.index('   Table of the typed words'):_E48.index('   The assistant never opens the key file')]
_tab_title = _tab.split('\n')[0].strip()
_tab = '\n'.join(l[3:] if l.startswith('   ') else l for l in _tab.split('\n')[1:])
_alarm_i = _E48.index('Key step C. Your alarms.')
_alarm = _E48[_alarm_i:_E48.index('Detail: appendix K-C.', _alarm_i)].replace('Key step C. ', '')
_d5 = _E48[_E48.index('D.5. The last time to revoke'):_E48.index('Key step E.')].strip()
_gi = _E48.index('Key step G. The shred rule.'); _g = _E48[_gi:_E48.index('G.2. When you are done', _gi)].strip()
_g2i = _E48.index('G.2. When you are done')
_g2 = _E48[_g2i:_E48.index('Key step H.', _g2i)].strip()
_ii = _E48.index('Key step I. Revoke the key'); _i = _E48[_ii:_E48.index('Key step J.', _ii)].strip()
_idi = _E48.index('   Identify first, then revoke or delete'); _id = _E48[_idi:_E48.index('   Item 3 has a second job', _idi)].strip()
_wdi = _E48.index('Words in this item:'); _wd = _E48[_wdi:_E48.index('\n', _wdi)].strip()
_ai_ = _E48.index('Key step A. The fixed rule.'); _whyi = _E48.index('Why these two times:', _ai_); _why = _E48[_whyi:_E48.index(' Detail: appendix K-A.', _whyi)].strip()
DAY = ("# OWNER-DAY-SHEET: the page for the take day (saved in the same folder as the owner sheet)\n\n"
       "This page is for the day of the take. Everything on it is the same text as in step 22 item 3 of the owner sheet (key steps B to D, G and I, the card, the alarms and the table of typed words), and the full reasons are in `OWNER-APPENDIX-K.md`. "
       "From the owner sheet you need, besides this page, only key step A (the fixed rule), key step E (what the assistant gives you), key step F (the two questions), key step H (new keys, only if you need them), key step J (other keys) and key step K (a take still running). "
       "Only messages that you type yourself, as a new message in your chat with the assistant, count.\n\n"
       "## Words used on this page\n" + _wd + "\n\n"
       "## The card\n" + CARD_HEAD + "\n" + "\n".join(l.strip() for l in CARD_LINES) + "\n" + LASTDAY.strip() + "\n" + "\n".join(l.strip() for l in ONELINES) + "\n" + CARD_TAIL + "\n\n"
       "## Why 18:19 and 18:29\n" + _why + "\n\n"
       "## Your four alarms\nYour alarms. " + _alarm.split('Your alarms. ', 1)[1].strip() + "\n\n"
       "## The last day\n" + _d5 + "\n\n"
       "## Key step I: revoke the key\n" + _i + "\n\n"
       "## The identification check (before you revoke an app password or delete a HubSpot app)\n" + _id + "\n\n"
       "## The shred rule (key step G)\n" + _g + "\n\n"
       "## When the clean-up may start\n" + _g2 + "\n\n"
       "## Table of the typed words\n" + _tab_title + "\n\n" + _tab + "\n")
open(D + 'r19-OWNER-DAY-SHEET.md', 'w', encoding='utf-8').write(DAY)
_ai = T.index('\n## Appendix K'); _aj = T.index('\n## ', _ai + 5)
APPX = T[_ai:_aj].strip() + "\n"
open(D + 'r19-OWNER-APPENDIX-K.md', 'w', encoding='utf-8').write(APPX)
open(D + 'EDITS.md', 'w', encoding='utf-8').write(T)
print('written', len(T.split('\n')), 'lines; day sheet words', len(DAY.split()), '; appendix words', len(APPX.split()))
