"""Round 20 builder: anchored patches of EDITS.round19.md (an exact copy of the r19 EDITS.md; every old string asserted to occur the stated number of times).
Writes EDITS.md, r20-OWNER-DAY-SHEET.md and r20-OWNER-APPENDIX-K.md. No vendor words, no secrets. Paths are relative to this file."""
import re, sys, os
D = os.path.dirname(os.path.abspath(__file__)) + '/'
_head = open(D + 'build-r17-head.py', encoding='utf-8').read().replace('EDITS.round16.md', 'EDITS.round19.md')
exec(_head)

def subn(old, new, what=''):
    """replace every copy; the count must be at least 1 (reported)"""
    c = T.count(old)
    if c < 1:
        errs.append('subn count 0: ' + old[:80]); return 0
    sub(old, new, c); return c

LAST = "Tue 24 Nov 2026 18:29 UTC = 23:59 IST"
TBC_OLD = " (this date is to be confirmed by the studio lead before you rely on it)"
TBC = " (this date is a proposal: it stands if the assistant names no other date before your first take)"
KS = ("The key is revoked by 18:19 UTC = 23:49 IST; the last 10 minutes (18:19 UTC = 23:49 IST to 18:29 UTC = 23:59 IST) are for card steps 2 and 3; "
      "if the key is still live at 18:19 UTC = 23:49 IST it comes first.")
TW = ("`no more takes` alone is never final; the confirmation is `yes, no more takes`; "
      "if you have revoked the key without having typed `yes, no more takes`, write `key gone, no more decisions`.")
WARN3 = "In route B, writing `key gone, no more decisions` before you have watched the cut makes the cut final and costs you the retake."
EMERG = ("an emergency: if you think that the key may have leaked or that somebody else may use it (for example the laptop is lost, or you see a charge that you did not make), "
         "revoke it at once, at any time and without waiting for anything (key step I), then write `key gone, no more decisions`; in route B this makes the cut final and costs you the retake, and you accept that")
NOKEYDATE = ("The key has no date and no later date: the assistant asks you again, in every message that it writes to you, until you have written `key revoked` or `key gone, no more decisions`, "
             "and it starts nothing that cannot be undone until then.")
R3 = " (the last time to confirm in route B is when alarm 1 rings: 17:49 UTC = 23:19 IST on Mon 23 Nov 2026, key step D.5)"

# ---------------------------------------------------------------- 1. alarms: five alarms (security M5, minor m1; stranger M-D)
OLD_AL = ("Set four alarms on your own phone or computer. Alarm 1: Mon 23 Nov 2026 17:49 UTC = 23:19 IST, named `revoke the secret key for the model`. "
          "Alarm 2: a repeating alarm in the evening of every day from the day of your first take until Mon 23 Nov 2026 (the time of day is yours, in your own local time), named `is the secret key for the model still alive?`. "
          "Alarm 3: Mon 23 Nov 2026 18:09 UTC = 23:39 IST, named `last chance: revoke the secret key for the model now`. "
          "Alarm 4: Tue 24 Nov 2026 06:00 UTC = 11:30 IST" + TBC_OLD + ", named `if the secret key for the model is still not revoked, revoke it now`; it is only for the case that you missed alarms 1 to 3 (key step D.5). "
          "Turn alarm 2 off when you have written `key revoked` or `key gone, no more decisions`.")
NEW_AL = ("Set five alarms on your own phone or computer. Alarm 1: Mon 23 Nov 2026 17:49 UTC = 23:19 IST, named `revoke the secret key for the model`. "
          "Alarm 2: a repeating alarm every day from the day of your first take until Mon 23 Nov 2026, always at 06:30 UTC = 12:00 IST (a fixed time in the daytime, when you are awake; this time is a proposal and stands if the assistant names no other time before your first take), named `is the secret key for the model still alive?`. "
          "Alarm 3: Mon 23 Nov 2026 18:09 UTC = 23:39 IST, named `last chance: revoke the secret key for the model now`. "
          "Alarm 4: Mon 23 Nov 2026 18:24 UTC = 23:54 IST, named `still not revoked: revoke the secret key for the model now`; it rings 5 minutes after the last time to revoke. "
          "Alarm 5: Tue 24 Nov 2026 00:30 UTC = 06:00 IST" + TBC + ", named `the secret key for the model must be revoked now`; you set it in every case, and it is not conditional on anything: if you have already written `key revoked` or `key gone, no more decisions` it costs you nothing and you switch it off (key step D.5). "
          "When you have written `key revoked` or `key gone, no more decisions`, switch off every alarm that has not rung yet.")
edit_new('E-48', [(OLD_AL, NEW_AL)])
# the alarm paragraph is split into one line per alarm event (stranger minor: 300 words in one paragraph)
edit_new('E-48', [
    (" When alarm 1 rings: if a session", "\n   When alarm 1 rings: if a session"),
    (" When alarm 3 rings and the key is not yet revoked:", "\n   When alarm 3 rings and the key is not yet revoked:"),
    (" Write `key revoked` when it is done. If you have already revoked the key, the alarms cost you nothing.",
     " Write `key revoked` when it is done; if you have not typed `yes, no more takes`, write `key gone, no more decisions` instead (key step B). If you have already revoked the key, the alarms cost you nothing.\n   When alarm 4 or alarm 5 rings and the key is not yet revoked: stop everything else, revoke the key now (key step I) and write `key gone, no more decisions`; the key has no later date (key step D.5)."),
    (" When alarm 2 rings and the key is not yet revoked:", "\n   When alarm 2 rings and the key is not yet revoked:"),
])
# other copies of the alarm list
sub("Set four alarms on your own phone or computer (step 22 item 3, key step C): alarm 1 for 17:49 UTC = 23:19 IST on Mon 23 Nov 2026,", "Set five alarms on your own phone or computer (step 22 item 3, key step C): alarm 1 for 17:49 UTC = 23:19 IST on Mon 23 Nov 2026,")
sub("alarm 2, which repeats every evening from the day of your first take (your own phone time), named `is the secret key for the model still alive?`; and alarm 4 for Tue 24 Nov 2026 06:00 UTC = 11:30 IST" + TBC_OLD + ", named `if the secret key for the model is still not revoked, revoke it now`, for the case that you missed the others.",
    "alarm 2, which repeats every day from the day of your first take at 06:30 UTC = 12:00 IST (a proposal that stands if the assistant names no other time), named `is the secret key for the model still alive?`; alarm 4 for Mon 23 Nov 2026 18:24 UTC = 23:54 IST, named `still not revoked: revoke the secret key for the model now`; and alarm 5 for Tue 24 Nov 2026 00:30 UTC = 06:00 IST" + TBC + ", named `the secret key for the model must be revoked now`, which you set in every case.")
sub("In short: set four alarms (key step C);", "In short: set five alarms (key step C);")
sub("`key gone, no more decisions`.  revoke the key (key step I);", "`key gone, no more decisions`. Then you revoke the key (key step I);")
sub("Facts: key step A is a promise by the owner backed by his four alarms; the program has no timer; all four alarms are on one person's device;", "Facts: key step A is a promise by the owner backed by his five alarms; the program has no timer; all five alarms are on one person's device;")
sub("The owner's four alarms (key step C: 17:49 UTC = 23:19 IST and 18:09 UTC = 23:39 IST on 23 Nov, a repeating evening alarm from the first take, and 06:00 UTC = 11:30 IST on Tue 24 Nov, a date that the studio lead still has to confirm) are the only reminders",
    "The owner's five alarms (key step C: 17:49 UTC = 23:19 IST, 18:09 UTC = 23:39 IST and 18:24 UTC = 23:54 IST on 23 Nov, a repeating daily alarm at 06:30 UTC = 12:00 IST from the first take, and 00:30 UTC = 06:00 IST on Tue 24 Nov, a date that the studio lead still has to confirm) are the only reminders")
sub("(12) ROUND 19: the Tue 24 Nov 2026 date and alarm 4 (06:00 UTC = 11:30 IST) are the builder's proposal and are marked in the owner text as to be confirmed by the studio lead;",
    "(12) ROUND 19 (changed in round 20): the Tue 24 Nov 2026 date and the last alarm (now alarm 5, 00:30 UTC = 06:00 IST, set in every case) are the builder's proposal; the owner text says that the proposal stands unless the assistant tells him another date before his first take (ND18);")
sub("it is never deferred; alarm 4 on Tue 24 Nov 2026 is the last prompt)", "it is never deferred and has no later date; alarm 5 on Tue 24 Nov 2026 is the last prompt)")

# ---------------------------------------------------------------- 2. the key: no date, no later date (security M1); emergency (M4); one rule for `key gone` (M4, stranger M-G)
edit_new('E-48', [
    ("The exceptions are alarm 1 and alarm 3 (key step C) and the last time to revoke (key step D.5): there you revoke first and write `key gone, no more decisions`.",
     "The exceptions are alarm 1, alarm 3, alarm 4 and alarm 5 (key step C), the last time to revoke (key step D.5) and " + EMERG + ". In every exception you revoke first and write `key gone, no more decisions`."),
    ("normally you revoke it after your confirmation (key step D.3); alarm 1, alarm 3 and the last time to revoke (key step D.5) are the exceptions.",
     "normally you revoke it after your confirmation (key step D.3); alarm 1, alarm 3, alarm 4, alarm 5, an emergency (key step D.3) and the last time to revoke (key step D.5) are the exceptions."),
    ("write `key gone, no more decisions` instead (key step D.5). " + TW + " " + WARN3, "write `key gone, no more decisions` instead (key step D.5). " + WARN3),
    ("If you could not revoke it by the deadline, write `key not revoked` and the reason; the assistant lists it in the handoff with a date to finish it.",
     "If you could not revoke it by the deadline, write `key not revoked` and the reason. " + NOKEYDATE),
    ("Use it only when all three are true, or when you revoke at the last time to revoke. It counts as `key revoked` and as the confirmation, so after it you do not type `key revoked` again.",
     "Use it whenever you have revoked the key before you typed `yes, no more takes` (at the last time to revoke, after an alarm or in an emergency); otherwise you type `yes, no more takes` first and `key revoked` after the revoke. It counts as `key revoked` and as the confirmation, so after it you do not type `key revoked` again. Type every word exactly as it is written here, without the backticks; capital letters and a full stop at the end do not matter, and any other change (another word, a missing word) means that the word was not typed: for the confirmation that counts as `another take`, for any other word the assistant asks you again."),
    ("A `key revoked` is only a report, at any time, also after 18:19 UTC = 23:49 IST: the assistant answers it once with \"Do you also want no more takes? Then write `key gone, no more decisions`\" and starts nothing that cannot be undone until you do.",
     "A `key revoked` is only a report, at any time, also after 18:19 UTC = 23:49 IST: the assistant answers it once with \"Do you also want no more takes? Then write `key gone, no more decisions` (in route B this makes the cut final)\" and starts nothing that cannot be undone until you do."),
    ("the builder believes that they reach only", "the assistant believes that they reach only"),
    ("Alarm 4 (key step C) is for this case. If you cannot reach the website, a second person whom you have named for this may revoke the key (whether such a person exists is open: the studio lead tells you).",
     "Alarm 4 and alarm 5 (key step C) are for this case. " + NOKEYDATE + " If you cannot reach the website, a second person whom you named in writing to the assistant before your first take may revoke the key; if you named nobody there is no second person, and you revoke it yourself as soon as you can reach the website."),
    # D.5: the real latest time to confirm in route B (stranger M-B), said once
    ("If you have not yet typed `yes, no more takes` by Mon 23 Nov 2026 18:19 UTC = 23:49 IST, you revoke the key at that time anyway (key step I)",
     "The real latest time to confirm in route B is when alarm 1 rings, 17:49 UTC = 23:19 IST on Mon 23 Nov 2026 (not 18:19 UTC = 23:49 IST): when it rings you go to key step I, and a confirmation after the revoke changes nothing. If you have not yet typed `yes, no more takes` by Mon 23 Nov 2026 18:19 UTC = 23:49 IST, you revoke the key at that time anyway (key step I)"),
    ("What you have not finished by 18:29 UTC = 23:59 IST you finish yourself by " + LAST + TBC_OLD + ": you act, and nobody does an owner item for you. The assistant lists each open item in the handoff",
     "What you have not finished by 18:29 UTC = 23:59 IST you finish yourself by " + LAST + TBC + ": you act, and nobody does an owner item for you. The key is never one of these items. The assistant lists each open item other than the key in the handoff"),
    # G.2 (security M1, M2; stranger M-C)
    ("If by 18:29 UTC = 23:59 IST (the assistant has no timer: it reads the time shown on your last message in the chat, and a message with no time shown counts as late) you have not written ALL of these, the assistant does not start item 1 in that session; it lists in the handoff every item that is left, with you as its owner and the date " + LAST + TBC_OLD + " (or a later date that you give) as the date to finish, and asks you at your next session. Item 1 may start in a later session, but still only when ALL of these are true.",
     "If on Mon 23 Nov 2026, by 18:29 UTC = 23:59 IST (the assistant has no timer: on that day start every message that you write with the time in UTC, for example `17:20 UTC = 22:50 IST`, because the assistant cannot be sure that your chat shows times; it reads that time, and a message that has no time at its start counts as late) you have not written ALL of these, the assistant does not start item 1 in that session; it lists in the handoff every item that is left, except the key (the key has no date: key step D.5), with you as its owner and the date " + LAST + TBC + " as the date to finish (no later date), and asks you at your next session. On any other day this time rule does not apply. Item 1 may start in a later session, but still only when ALL of these are true."),
    ("counts as done in this list once you wrote `web revokes not done`, its name and the reason.",
     "counts as done in this list once you wrote `web revokes not done`, its name and the reason, and so does item 5 for the login that it concerns (the retire check is not run for it; item 6 for that login waits)."),
    # shred rule (security m8)
    ("(2) It contains no `..`, no space, no quote sign and none of the signs `*`, `?` and `[`.", "(2) It contains no `..`, no space, no line break, no quote sign and none of the signs `*`, `?` and `[`."),
    ("For a file of part (b) or (d): you copy its path from your own list, sign for sign.",
     "For a file of part (b) or (d): you copy its path from your own list, sign for sign (the assistant cannot check these two parts, they rest on your handwritten list, and a file that is not on that list is never shredded)."),
])
sub("The exceptions to the waiting are alarm 1, alarm 3 and the last time to revoke the secret key for the model:", "The exceptions to the waiting are alarm 1, alarm 3, alarm 4, alarm 5, an emergency (key step D.3) and the last time to revoke the secret key for the model:")
sub("If you could not revoke the key by then, send the words `key not revoked` and the reason instead |", "If you could not revoke the key by then, send the words `key not revoked` and the reason instead (the key has no later date than 18:19 UTC = 23:49 IST, so send `key revoked` as soon as it is revoked) |")

# ---------------------------------------------------------------- 3. route B: the real latest time to confirm (stranger M-B), E-57, K-D, ND15
sub("### Step 21. Watch the cut by Mon 23 Nov 2026 18:19 UTC = 23:49 IST", "### Step 21. Watch the cut by Mon 23 Nov 2026 17:49 UTC = 23:19 IST (alarm 1)")
sub("write `cut accepted` and then `yes, no more takes` before 18:19 UTC = 23:49 IST on Mon 23 Nov 2026, because the key is revoked at that time in every case.",
    "write `cut accepted` and then `yes, no more takes` before alarm 1 rings, 17:49 UTC = 23:19 IST on Mon 23 Nov 2026, because when it rings you go to key step I and the key is revoked at the latest at 18:19 UTC = 23:49 IST in every case.")
sub("If you have not typed `yes, no more takes` (in route B: after `cut accepted`) by 18:19 UTC = 23:49 IST on Mon 23 Nov 2026, key step D.5 applies.",
    "If you have not typed `yes, no more takes` (in route B: after `cut accepted`) before alarm 1 rings, 17:49 UTC = 23:19 IST on Mon 23 Nov 2026, key step D.5 applies.")
sub("the cut is watched and `cut accepted` and `no more takes` are written before 18:19 UTC = 23:49 IST on Mon 23 Nov 2026;", "the cut is watched and `cut accepted` and `yes, no more takes` are written before alarm 1 rings, 17:49 UTC = 23:19 IST on Mon 23 Nov 2026;")
sub("(the assistant plans for you to watch the cut before the last time to revoke the secret key for the model;", "(the assistant plans for you to watch the cut before alarm 1 rings, 17:49 UTC = 23:19 IST on Mon 23 Nov 2026;")
# card step 1 and the last-day lines of the card (stranger minor)
edit_new('E-48', [
    ("1. You: make sure that you have confirmed your last take", "1. You: before 18:19 UTC = 23:49 IST on the last day (key step D.5), make sure that you have confirmed your last take"),
    ("if the key is still live at 18:19 UTC = 23:49 IST it comes first. What you have not finished by 18:29 UTC = 23:59 IST you finish by " + LAST,
     "if the key is still live at 18:19 UTC = 23:49 IST it comes first. In plain words: the key is revoked before 18:19 UTC = 23:49 IST, and the quick web revokes and the shred of the key copies follow before 18:29 UTC = 23:59 IST; card steps 4 to 6 have no time of their own, you do them in order after card step 3. What you have not finished by 18:29 UTC = 23:59 IST you finish by " + LAST),
    ("Item 2 (app passwords): on the page of app passwords of each throwaway mailbox,", "Item 2 (app passwords): at myaccount.google.com, Security, App passwords (this click path is not checked), on the page of app passwords of each throwaway mailbox,"),
])
OLD_WD = "the retirement is the whole of step 22."
NEW_WD = ("the retirement is the whole of step 22; a take is one real run on your test accounts that makes the recording; the cut is the edited video made from your takes (step 21); "
          "route A and route B are the two ways to confirm that your last take is your last, and key step D.1 explains both; `the take's n8n` is the new n8n that the assistant starts inside the take folder (the clean-up removes it) and `your own n8n` is the one that you open at `http://localhost:5678` (it stays).")
edit_new('E-48', [(OLD_WD, NEW_WD)])

# ---------------------------------------------------------------- 4. identification check: dedicated items, rotate then delete, two n8n (security M3, minor m4; stranger M-E)
_E = '\n'.join(block_get('E-48'))
_a = _E.index("Identify first, then revoke or delete (the rule for item 2 and item 3).")
_bk = "and it breaks everything that uses it."
_b = _E.index(_bk, _a) + len(_bk)
OLD_ID = _E[_a:_b]
NEW_ID = ("Identify first, then revoke or delete (the rule for item 2 and item 3). Two different n8n are named in this sheet: the take's n8n (the new one that the assistant starts inside the take folder; item 1 removes it) and your own n8n (the one at `http://localhost:5678`, which you keep). "
          "Before the take you wrote on paper or on your phone a list of the two app passwords and of the two HubSpot private apps (the Phase 0 note (under NOT YET CONFIRMED), point (5)): for each one its name, the day it was made where the page shows a day (an app password page may show only the name), and one word beside it: `take-only` or `used`. "
          "`take-only` means: you made it new for this take and you put it only into the take's n8n or into a file of your own list, never into your own n8n. `used` means: your own n8n holds it or may hold it, or you cannot tell (write `used` whenever you cannot tell). "
          "The app that step 7 calls the app for n8n (app 2) goes into the take's n8n only. "
          "On the day, open the page, compare each name (and day, where shown) with that list yourself, and revoke or delete only an item that is on your list, whose name and day match, and that carries `take-only`. "
          "Rotate first, then delete, for an item that carries `used`: make a replacement (a new HubSpot private app, or a new app password) and put the replacement into your own n8n; open one workflow of your own n8n and run it once on made-up data to see that it still works; only then delete the old HubSpot app or revoke the old app password. You may do this on Mon 23 Nov 2026 before 18:29 UTC = 23:59 IST or on " + LAST + TBC + "; if your own n8n does not work afterwards, put the replacement in again before you do anything else. "
          "If a name or day is not on your list, or you are not sure, touch NOTHING of that kind: write `web revokes not done`, the names (and days, where shown) and the reason (never a key or a password). "
          "The assistant lists each such item in the handoff with you as its owner; the entry ends only when you tell the assistant in a message, with the name of the item, that you deleted or revoked it (names only), and the assistant asks you again at every session until then; the date " + LAST + " is the first day on which it is late, and it is never moved. "
          "Item 1 may still start (key step G.2); the retire check is not run for it (your item 6 says what to do). "
          "Until you finish such an item it stays alive; the assistant believes that it reaches only the made-up data of your test accounts, which is UNVERIFIED. "
          "Deleting a private app cannot be undone (the app and its secret key are gone for good), and it breaks everything that uses it.")
edit_new('E-48', [(OLD_ID, NEW_ID)])
sub("and for each of the four whether your own n8n (the one at `http://localhost:5678`) uses it (what counts as used is defined in the identification check of step 22 item 3; where you cannot tell, write `used`). Step 22 item 3 uses this list: you revoke or delete only an item that is on it and that your own n8n does not use.",
    "and for each of the four one word: `take-only` or `used` (the words are defined in the identification check of step 22 item 3; your own n8n is the one at `http://localhost:5678`, not the take's n8n; where you cannot tell, write `used`). Step 22 item 3 uses this list: you revoke or delete only an item that is on it and that carries `take-only`; for an item that carries `used` you rotate first (make a replacement), then delete.")
sub("Before the take the assistant asks you three things. (1)", "Before the take the assistant asks you three questions and asks you to write two lists. (1)")

# E-59 (security M2)
rsub('E-59', "If you wrote `web revokes not done` for the mailbox or for HubSpot, that login cannot be refused: do not run the check for it, do not shred its file of part (c) yet (the check needs it), and write `shred not done other files` with the reason;",
     "If you wrote `web revokes not done` for the mailbox or for HubSpot, that login cannot be refused: do not run the check for it, do not shred its file of part (c) yet (the check needs it), write `shred not done other files` with the reason, and item 5 counts as done for that login and item 1 does not wait for it (key step G.2);")

# typed-word table: the replies of key step F (stranger M-G)
edit_new('E-48', [
    ("| `start clean-up` |", "| `yes`, `no, other things use it`, `same key`, `different key` or `not sure` | your answer to a question of key step F (question 1: is the secret key for the model one that you made only for this take; question 2: is the saved key the one that is stored in your own n8n); `not sure` is a valid answer to both | F |\n| `start clean-up` |"),
])

# ---------------------------------------------------------------- 5. lead-facing: ND18 to ND20, headers, rounds
_ls = T.split('\n'); _i17 = [k for k, l in enumerate(_ls) if l.startswith('17. **Does item 1 (the clean-up) shred')]
if len(_i17) != 1: errs.append('ND17 line count %d' % len(_i17))
else:
    _ls[_i17[0] + 1:_i17[0] + 1] = [
        "18. **Alarm 2 time and the Tue 24 Nov 2026 date.** (E-48 key step C, D.5; round 20, security M5, stranger M-D.) Who answers: the studio lead. Proposals in the owner text: alarm 2 every day at 06:30 UTC = 12:00 IST (a fixed daytime time, so that a missed alarm is not left to the evening); the last prompt (alarm 5) on Tue 24 Nov 2026 at 00:30 UTC = 06:00 IST, and Tue 24 Nov 2026 18:29 UTC = 23:59 IST as the day for what is still open. Rule if no answer comes: the owner text says that each proposal stands unless the assistant tells the owner another one before his first take. Default: the proposals. Record: `ND18: <time of alarm 2> <date for the open items>`.",
        "19. **Typed word `lists written` and the rule for exact typing.** (E-48 key step B; round 20, security m5.) Who answers: the studio lead. Option (a): no new word (today): rule R10 of the studio lead cannot see the paper lists in the chat record, so it checks only that the assistant asked for them. Option (b): the owner types `lists written` once, before the take, after he has written the paper lists of the Phase 0 note (points (2), (4), (5)); the assistant then does not ask for the take until it has seen it (cost: one more word in the table; benefit: the chat record shows that the lists were made). Also: the exactness rule of key step B (type the word without backticks, capitals and a final full stop do not matter, any other change is not that word) is the builder's proposal; the studio lead confirms it. Default: (a) and the rule as written. Record: `ND19: a|b`.",
        "20. **L-LEN: one sheet of at most 6,300 words (ORDERS.md line 227): option 1 or option 2, and a recommendation question.** (round 20; round 19 stranger L-LEN text.) Who answers: the studio lead. Numbers: the applied sheet is far over 6,300 words; the exact counts of the sheet, the day page and Appendix K are in `r20-CHANGES.md` (computed by `verify20.py`, never typed by hand). Option 1: cut the sheet itself to 6,300 words: every word over 6,300 goes to appendix files; every Apply now row is re-cut; the day page and appendix are regenerated; the exact-copy pins are rebuilt (the pins are the list of every sentence of the sheet with its number of copies, `r20-pins.txt`); a new full review round is needed; risk: the safety sentences must stay on the one sheet. Option 2: name the day page as the ONE sheet (it holds the card, the alarms, key steps B to D and G and I, the identification check and the table of typed words, and it says plainly which other key steps and notes of the owner sheet the owner also needs); the long text stays as the detail file; needs only the studio lead's written reading of ORDERS.md line 227; risk: a reader may take the long text for the sheet that counts. The question for the studio lead: 'does ORDERS.md line 227 mean the day page that the owner reads on the take day, or the whole retirement text?' The builder recommends option 2 (it is the smaller change and keeps the exact-copy rule), but the builder does not decide. Default: not decided. Record: `ND20: 1|2`.",
    ]
    T = '\n'.join(_ls)
sub("(numbered 1 to 17 in the list below the gates)", "(numbered 1 to 20 in the list below the gates)")
sub("## NOT DECIDED: studio lead or owner only (items 1 to 17).", "## NOT DECIDED: studio lead or owner only (items 1 to 20).")
sub("the number of rows stays 60", "the number of rows stays 60 (round 20 changes row texts only)")
# the round lines at the end: ascending order, round 20 added
_ls = T.split('\n')
_i19 = [k for k, l in enumerate(_ls) if l.startswith('- Round 19 added:')]; _i18 = [k for k, l in enumerate(_ls) if l.startswith('- Round 18 added:')]
if len(_i19) != 1 or len(_i18) != 1 or _i19[0] + 1 != _i18[0]: errs.append('round lines %s %s' % (_i19, _i18))
else:
    _r19, _r18 = _ls[_i19[0]], _ls[_i18[0]]
    _ls[_i19[0]:_i18[0] + 1] = [_r18, _r19,
        "- Round 20 added: nothing was run on a take; no click path was opened (the Google and HubSpot click paths stay UNVERIFIED); the text and counts were checked by `verify20.py` (see `resolve-r20-check-output.txt`). UNVERIFIED and unchanged: whether the identification rule (take-only or used, rotate first) is enough for the owner who cannot tell what his own n8n holds; whether the retire check can run for one login; the real behaviour of a revoked key during a take."]
    T = '\n'.join(_ls)

# Why additions
why_add('E-48', "Round 20 (security M1 to M5, minors m1 to m9; stranger M-A to M-G and minors): (a) the key has no date and no later date (key step I, D.5, G.2, alarm 5); (b) item 5 counts as done for a login with `web revokes not done`; (c) `take-only` or `used`, rotate first then delete, the take's n8n and your own n8n told apart; (d) an emergency early revoke and one rule for `key gone, no more decisions`; (e) five alarms (18:24 UTC = 23:54 IST added; the last alarm 00:30 UTC = 06:00 IST on Tue 24 Nov 2026 in every case; alarm 2 at 06:30 UTC = 12:00 IST as a proposal, ND18); (f) the real latest time to confirm in route B is alarm 1, 17:49 UTC = 23:19 IST; (g) the 18:29 rule is dated Mon 23 Nov 2026 and says how to show the time; (h) the studio-lead hedges are replaced by a rule that the proposal stands; (i) the day page holds key step B and D.1 to D.4 and says which other parts of the owner sheet are needed; words take, cut, route A and B are defined.")
why_add('E-55', "Round 20 (security M1, M4; stranger M-D): the key has no later date; an emergency revoke is allowed at any time; the hedge on the Tue 24 date is replaced by a rule that the proposal stands.")
why_add('E-57', "Round 20 (stranger M-B): the real latest time to confirm in route B is alarm 1, 17:49 UTC = 23:19 IST (17:49 + 5:30 = 23:19), said in step 21 and key step D.5.")
why_add('E-58', "Round 20 (security M1): the key has no later date; the row says so.")
why_add('E-59', "Round 20 (security M2): item 5 counts as done for a login that carries `web revokes not done`, and item 1 does not wait for it.")
why_add('E-37', "Round 20 (security M3, m4): the list holds `take-only` or `used` for each of the four; five things are asked or written, named as three questions and two lists.")


# ---------------------------------------------------------------- 6. file names, round history, the hedge replaced everywhere
sub("(the builder's copy is `r19-OWNER-APPENDIX-K.md`)", "(the builder's copy is `r20-OWNER-APPENDIX-K.md`)")
sub("(L-LEN is not met: see `r19-CHANGES.md`, section 1, item 1)", "(L-LEN is not met: see `r20-CHANGES.md`, section L-LEN)")
sub("round 19 writes `r19-OWNER-DAY-SHEET.md` and `r19-OWNER-APPENDIX-K.md`)", "round 19 writes `r19-OWNER-DAY-SHEET.md` and `r19-OWNER-APPENDIX-K.md`; round 20 writes `r20-OWNER-DAY-SHEET.md` and `r20-OWNER-APPENDIX-K.md`)")
sub("Round 19 (`r19-CHANGES.md`, same paths: no round cap) applies all of those findings in one batch. The result of round 19 is NOT reviewed yet.",
    "Round 19 (`r19-CHANGES.md`, same paths: no round cap) applied the findings of round 18; its result was reviewed (`review-r19-security.md`: 0 Blockers, 5 Majors, 9 Minors; `review-r19-stranger.md`: 0 Blockers, 7 Majors; independent evidence in `evidence-r19-independent/`). Round 20 (`r20-CHANGES.md`, same paths: no round cap) applies all of those findings in one batch. The result of round 20 is NOT reviewed yet.")
sub("## Counts (computed by script, `r19-CHANGES.md` and `resolve-r19-check-output.txt`)", "## Counts (computed by script, `r20-CHANGES.md` and `resolve-r20-check-output.txt`)")
subn(TBC_OLD, TBC)

if errs:
    print('ERRORS', len(errs))
    for e in errs: print(' ', e)
    sys.exit(1)

# ---------------------------------------------------------------- separate files (generated from the same text)
_E48 = '\n'.join(block_get('E-48'))
_tab = _E48[_E48.index('   Table of the typed words'):_E48.index('   The assistant never opens the key file')]
_tab_title = _tab.split('\n')[0].strip()
_tab = '\n'.join(l[3:] if l.startswith('   ') else l for l in _tab.split('\n')[1:])
_alarm_i = _E48.index('Key step C. Your alarms.')
_alarm = _E48[_alarm_i:_E48.index('Detail: appendix K-C.', _alarm_i)].replace('Key step C. ', '')
_alarm = '\n'.join(l.strip() for l in _alarm.split('\n'))
_d5 = _E48[_E48.index('D.5. The last time to revoke'):_E48.index('Key step E.')].strip()
_gi = _E48.index('Key step G. The shred rule.'); _g = _E48[_gi:_E48.index('G.2. When you are done', _gi)].strip()
_g2i = _E48.index('G.2. When you are done')
_g2 = _E48[_g2i:_E48.index('Key step H.', _g2i)].strip()
_ii = _E48.index('Key step I. Revoke the key'); _i = _E48[_ii:_E48.index('Key step J.', _ii)].strip()
_idi = _E48.index('   Identify first, then revoke or delete'); _id = _E48[_idi:_E48.index('   Item 3 has a second job', _idi)].strip()
_wdi = _E48.index('Words in this item:'); _wd = _E48[_wdi:_E48.index('\n', _wdi)].strip()
_ai_ = _E48.index('Key step A. The fixed rule.'); _whyi = _E48.index('Why these two times:', _ai_); _why = _E48[_whyi:_E48.index(' Detail: appendix K-A.', _whyi)].strip()
_bi = _E48.index('Key step B. Only you can write the words.'); _bs = _E48[_bi:_E48.index('Key step C. Your alarms.', _bi)].strip()
_di = _E48.index('Key step D. The route and the confirmation.'); _d14 = _E48[_di:_E48.index('D.5. The last time to revoke', _di)].strip()
_d14 = '\n'.join(l.strip() for l in _d14.split('\n'))
_ci = _E48.index('The one order (the card; read it first).'); _cj = _E48.index('Key step J (other keys) is not one of the seven')
_cj = _E48.index('\n', _cj) if '\n' in _E48[_cj:] else len(_E48)
_card = '\n'.join(l.strip() for l in _E48[_ci:_cj].split('\n'))
DAY = ("# OWNER-DAY-SHEET: the page for the take day (saved in the same folder as the owner sheet)\n\n"
       "This page is for the day of the take. It holds the same text as step 22 item 3 of the owner sheet (the card, the alarms, key steps B to D, G and I, the identification check and the table of typed words); the reasons are in `OWNER-APPENDIX-K.md`. "
       "It is NOT the whole retirement: from the owner sheet you also need key steps A, E, F, H, J and K, the Phase 0 note (the note that you write before the take: its points (2), (4) and (5)) and the full text of items 2 to 6 of step 22 (here one line each). Read them before the take day. "
       "Only messages that you type yourself, as a new message in your chat with the assistant, count.\n\n"
       "## Words used on this page\n" + _wd + "\n\n"
       "## The card\n" + _card + "\n\n"
       "## Why 18:19 and 18:29\n" + _why + "\n\n"
       "## Key step B: only you can write the words\n" + _bs + "\n\n"
       "## Your five alarms\nYour alarms. " + _alarm.split('Your alarms. ', 1)[1].strip() + "\n\n"
       "## Key step D: the route and the confirmation (D.1 to D.4)\n" + _d14 + "\n\n"
       "## The last day (D.5)\n" + _d5 + "\n\n"
       "## Key step I: revoke the key\n" + _i + "\n\n"
       "## The identification check (before you revoke an app password or delete a HubSpot app)\n" + _id + "\n\n"
       "## The shred rule (key step G)\n" + _g + "\n\n"
       "## When the clean-up may start\n" + _g2 + "\n\n"
       "## Table of the typed words\n" + _tab_title + "\n\n" + _tab + "\n")
open(D + 'r20-OWNER-DAY-SHEET.md', 'w', encoding='utf-8').write(DAY)
_ai = T.index('\n## Appendix K'); _aj = T.index('\n## ', _ai + 5)
APPX = T[_ai:_aj].strip() + "\n"
open(D + 'r20-OWNER-APPENDIX-K.md', 'w', encoding='utf-8').write(APPX)
# the three numbers of ND20 are computed (not typed)
_sheet = T[T.index('### E-48: '):]
_sheet_words = len(T[T.index('### E-48: '):T.index('\n### E-49: ')].split()) if False else None
open(D + 'EDITS.md', 'w', encoding='utf-8').write(T)
print('written', len(T.split('\n')), 'lines; day sheet words', len(DAY.split()), '; appendix words', len(APPX.split()))
