"""Round 17 builder: anchored patches of EDITS.round16.md (every old string asserted to occur the stated number of times). Writes EDITS.md.
No vendor words, no secrets. Paths are relative to this file. Extends build-r16 (helpers in build-r17-head.py)."""
import re, sys, os
D = os.path.dirname(os.path.abspath(__file__)) + '/'
exec(open(D + 'build-r17-head.py', encoding='utf-8').read())

# ---------------------------------------------------------------- the seven steps of the one order (one wording, used in three places)
P = [
    "revoke the secret key for the model (key step I) and write `key revoked`",
    "shred the copy of the key in the take folder and the other copies of the old key on your own list (key step G, parts (a) and (b)) and write `shred done key copies`",
    "do your items 2, 3 and 4 (item 2: revoke both app passwords; item 3: delete both HubSpot apps; item 4: save the screenshots)",
    "do your item 5, the retire check",
    "do your item 6 (shred its two files) and shred the other secret files on your own list (key step G, parts (c) and (d)), and write `shred done other files`",
    "read the list of what the assistant will remove (the full paths and the container's name) and, if nothing in it is a file that you want to keep, write `start clean-up`",
    "the assistant does its item 1 (the clean-up)",
]
ORDER_INLINE = '; '.join('(%d) %s' % (k + 1, p) for k, p in enumerate(P))
START = ("Item 1 starts only when ALL of these are true, each as a message that you typed yourself: a confirmation (`yes, no more takes` or `key gone, no more decisions`; key step D.3); "
         "`key revoked` (or `key gone, no more decisions`, which counts as `key revoked`; or `key not revoked` and the reason, but item 1 never starts while a copy of the key exists and the key is not revoked); "
         "`shred done key copies` (or `shred not done key copies` and the reason); your items 2, 3, 4 and 5 done; `shred done other files` (or `shred not done other files` and the reason); "
         "you have read the list of what the assistant will remove; and `start clean-up`.")

# ---------------------------------------------------------------- E-48 (key steps)
edit_new('E-48', [
    # card
    ("and only after your `no more takes` has been confirmed (key step D). Make a screenshot", "and only after your `no more takes` has been confirmed (key step D.3). Make a screenshot"),
    ("In short: set three alarms (key step C); after your last take confirm `no more takes` (key step D); revoke the key (key step I); then shred the copies (key step G);",
     "In short: set three alarms (key step C); choose route A or route B and, after your last take that you accept, confirm `no more takes` (key step D; in route B after `cut accepted`); revoke the key (key step I); then shred the copies (key step G);"),
])
span_new('E-48', "The one order (the card; read it first).", "7. The assistant does its item 1 (it never starts while a copy of the key exists and the key is not revoked).",
    "The one order (the card; read it first). Do these seven things in this order and never a later one before an earlier one:\n"
    "   1. You: " + P[0] + ". Make new keys first only if key step H says so and at least 30 minutes remain. Normally this is right after your last take that you accept; on Mon 23 Nov 2026 it is at 18:19 UTC = 23:49 IST at the latest.\n"
    "   2. You: " + P[1] + ".\n"
    "   3. You: " + P[2] + ".\n"
    "   4. You: " + P[3] + ".\n"
    "   5. You: " + P[4] + ".\n"
    "   6. You: " + P[5] + ".\n"
    "   7. Then " + P[6] + ". It never starts while a copy of the key exists and the key is not revoked.\n"
    "   Key step J (other keys) is not one of the seven: do it at any time after card step 1; it holds nothing up.")
edit_new('E-48', [
    # key step A: the cap of the stage does not limit a copied key
    ("that is when the model stage must stop spending. Detail: appendix K-A.",
     "that is when the model stage must stop spending. The spending cap of the model stage limits the program only, not a copy of the key. Whether the company that provides the AI model can also limit this key is not checked, so until you revoke it the key can spend up to what your account at that company allows. Detail: appendix K-A."),
    # key step B
    ("By itself it confirms nothing (the one exception is key step D.5). `key gone, no more decisions` is a separate word with three meanings at once: the key is gone, you want no more takes, and (in route B) the cut is final. Use it only when all three are true.",
     "It never confirms anything, at any time. `key gone, no more decisions` is a separate word with three meanings at once: the key is gone, you want no more takes, and (in route B) the cut is final. Use it only when all three are true. It counts as `key revoked` and as the confirmation, so after it you do not type `key revoked` again."),
    # key step C
    ("Make no new key now unless at least 20 minutes remain after you have answered (key step H).",
     "Make no new key now unless at least 30 minutes remain after you have answered (key step H); alarm 1 gives exactly 30 minutes, so on the last day you normally make none."),
    ("When alarm 3 rings and the key is not yet revoked, stop everything else and do key step I now.",
     "When alarm 3 rings and the key is not yet revoked: if no take is running, stop everything else and do key step I now; if a take is running, let it finish (key step K), then revoke the key at once, and in every case by 18:19 UTC = 23:49 IST."),
    # D.1 route B price
    ("The choice is yours, and the assistant recommends route B.",
     "The choice is yours, and the assistant recommends route B. Know the price of route B before you choose: the secret key for the model and its copy stay alive on this laptop for up to five days (Wed 18 Nov to Mon 23 Nov 2026), and the revoke on the last day depends only on you and your alarms. Route A is the safer one for keeping secrets safe; route B keeps the chance of a retake."),
    # D.3 the confirmation
    ("D.3. The confirmation. Only a new message from you with the words `yes, no more takes` confirms it.",
     "D.3. The confirmation. A confirmation is exactly one of two messages, each typed by you as a new message: `yes, no more takes` or `key gone, no more decisions` (key step B). `key revoked` is never a confirmation."),
    ("that is why route B exists.", "that is why route B exists. The words `another take` and `no more takes` mean the opposite of each other: read your message again before you send it."),
    # D.4
    ("and then you do key steps E to I at once, normally on Wed 18 Nov 2026.", "and then you follow the one order (the card) at once, from card step 1, normally on Wed 18 Nov 2026."),
    # key step E
    ("In its next message after your confirmed `no more takes` (or after your `key gone, no more decisions`, or after a `key revoked` that counts under key step D.5), the assistant gives you",
     "In its next message after your confirmation (key step D.3), the assistant gives you"),
    ("(3) the steps of key steps G to I with the exact page of the key list,", "(3) the exact page of the key list (key step I) and the steps of key step G,"),
    # key step F
    ("Any other reply, including a bare `no`, counts as `not sure`.", "Any other reply, including a bare `no`, counts as `not sure` (this holds for these two questions only; in the yes-or-no questions of other steps `no` means no)."),
    # key step G
    ("Key step G. The shred rule (after the key is revoked). It is ONE rule for every file that you shred in this item.",
     "Key step G. The shred rule. It is ONE rule for every file that you shred in this item and in step 8 (sub-steps e and f). Parts (a) and (b) are shredded only after the key is revoked."),
    ("(b) the files on YOUR OWN LIST of copies of the old key, a list that you wrote",
     "(b) the files on YOUR OWN LIST that hold a copy of the OLD KEY for the model, a list that you wrote"),
    ("(d) the password files and editor copies made in step 8:", "(d) every other file on your own list: the password files and editor copies made in step 8:"),
    ("you add a file to it the moment you make it. Nothing else.", "you add a file to it the moment you make it and mark it `old key` (part (b)) or `other` (part (d)); a file is in exactly one part. Nothing else."),
    ("If you write neither, the assistant treats it as `shred not done`.", "If you write neither, the assistant treats it as `shred not done key copies` or `shred not done other files`."),
    # key step H, I: one number, 30
    ("(only if at least 20 minutes remain before 18:19 UTC = 23:49 IST;", "(only if at least 30 minutes remain before 18:19 UTC = 23:49 IST;"),
    ("and more than 20 minutes remain, tell the assistant", "and at least 30 minutes remain, tell the assistant"),
    ("When the key is gone from the list, write `key revoked`.", "When the key is gone from the list, write `key revoked`; if you have not confirmed `no more takes` and it is the last time to revoke (key step D.5), write `key gone, no more decisions` instead."),
])
span_new('E-48', "D.5. The last time to revoke.", "The assistant says in its next message how it treated your words.",
    "D.5. The last time to revoke. If you have not confirmed `no more takes` by Mon 23 Nov 2026 18:19 UTC = 23:49 IST, you revoke the key at that time anyway (key step I) and then write `key gone, no more decisions`: that one message tells the assistant that the key is gone, that there are no more takes and (in route B) that the cut is final. A `key revoked` is only a report, at any time, also after 18:19 UTC = 23:49 IST: the assistant answers it once with \"Do you also want no more takes? Then write `key gone, no more decisions`\" and starts nothing that cannot be undone until you do. Between 18:19 UTC = 23:49 IST and 18:29 UTC = 23:59 IST there are only 10 minutes: they are for card step 2 (shred the copies of the key). The other card steps do not fit into them; what you have not finished by 18:29 UTC = 23:59 IST the assistant lists in the handoff with a date to finish it (key step G.2). The assistant says in its next message how it treated your words.")
span_new('E-48', "The assistant's item 1 starts only after all of these, in this order:", "and your message `start clean-up`. If by 18:29 UTC = 23:59 IST you have written none of these,",
    START + " If by 18:29 UTC = 23:59 IST (the assistant has no timer: it reads the time shown on your last message in the chat, and a message with no time shown counts as late) you have written none of these,")

# ---------------------------------------------------------------- E-16 (clean-up): one order, one start sentence, exception, copy first
span_new('E-16', "It does NOT start while a copy of the secret key for the model exists", "tells you before you do your own items.",
    "It does NOT start while a copy of the secret key for the model exists and the key is not revoked. The order of step 22 is the only order: " + ORDER_INLINE + ". " + START +
    " Only messages that you type yourself count (step 22 item 3, key step B). None of it can be undone, and a retake after it needs a new set-up. When it has finished, it reports each part as done or not done and tells you what is left, if anything.")
rsub('E-16', "What the assistant does first. Before it removes anything, it copies the take's result file and its counts (names and numbers only, no secret) into a folder of its own on the Linux disk, outside the take folder. It tells you that folder's name before the clean-up. It does this because removing the container deletes n8n's database and the take's table of enquiries too. It copies them BEFORE any shred, because shredding the take folder would also destroy the result file.",
     "What the assistant does first. In its next message after your confirmation (step 22 item 3, key step E), and BEFORE any shred, it copies the take's result file and its counts (names and numbers only, no secret) into a folder of its own on the Linux disk, outside the take folder, and tells you that folder's name. It does this because removing the container deletes n8n's database and the take's table of enquiries too, and shredding the take folder would also destroy the result file. At the start of item 1 it checks that this copy is there; if it is not, it stops and tells you.")
rsub('E-16', "(the folder in which the assistant made the take folder; it is a NEW, EMPTY folder made for the take, never your home folder)", "(the folder in which the assistant made the take folder; the take root is a NEW, EMPTY folder made for the takes, never your home folder)")

# ---------------------------------------------------------------- E-55 (heading of step 22)
span_new('E-55', "### Step 22. Retirement. Revoke the secret key", "so the key is normally revoked on that day.",
    "### Step 22. Retirement: the key revoked by Mon 23 Nov 2026 18:19 UTC = 23:49 IST, the rest by 18:29 UTC = 23:59 IST\n"
    "Revoke the secret key for the model right after you write `no more takes` (item 3 below; in route B of key step D, after `cut accepted`), and in every case by Mon 23 Nov 2026 18:19 UTC = 23:49 IST at the latest (the last time to revoke). Do the rest of the retirement by 18:29 UTC = 23:59 IST (the end of the spending window). The take is planned for Wed 18 Nov 2026, so the key is normally revoked on that day.")
span_new('E-55', "The one exception is the last time to revoke", "write `key gone, no more decisions` (key step B).",
    "A confirmation is exactly one of two messages: `yes, no more takes` or `key gone, no more decisions` (key step D.3); in route B also after `cut accepted`. `key revoked` alone is only a report. The one exception to the waiting is the last time to revoke the secret key for the model: at 18:19 UTC = 23:49 IST on Mon 23 Nov 2026 you revoke it whatever you have written, and then you write `key gone, no more decisions`.")
span_new('E-55', "The assistant starts item 1 only after you have written", "item 1 never starts while the copy of the key exists and the key is not revoked.", START)
span_new('E-55', "You do the items in the order of the card of item 3", "`start clean-up`; item 1).", "You do the items in this order: " + ORDER_INLINE + ".")

# ---------------------------------------------------------------- E-57 (step 21): route B price in the owner text
rsub('E-57', "The key and its copy stay alive, so a retake is possible.", "The key and its copy stay alive, so a retake is possible. The price: a live paid secret key and its copy stay on this laptop for up to five days (Wed 18 Nov to Mon 23 Nov 2026), and the revoke on the last day depends only on you and your alarms. Route A is the safer one for keeping secrets safe.")

# ---------------------------------------------------------------- E-12
rsub('E-12', "named `10 minutes left: revoke the secret key for the model now`; and alarm 2,", "named `10 minutes left: revoke the secret key for the model now` (if a take is running when it rings, you let it finish and then revoke at once, never later than 18:19 UTC = 23:49 IST); and alarm 2,")
rsub('E-12', "Your reply is FIVE short numbered lines that you type yourself", "Your reply is five numbered lines (lines 3 and 5 are long: you copy them) that you type yourself")

# ---------------------------------------------------------------- E-09: nano backup path, n8n.env on the list, K-8 move
rsub('E-09', "and if you see such a file, tell the assistant its name and shred it by the shred rule (step 22 item 3, key step G).", "and if you see such a file, write its full path on your own list (mark it `other`), tell the assistant its name, and then shred it by the shred rule (step 22 item 3, key step G).")
rsub('E-09', "type `clear` and press Enter; write `n8n.env done; you may look again`", "type `clear` and press Enter; add the full path of `n8n.env` to your own list (mark it `other`); write `n8n.env done; you may look again`")
_b = '\n'.join(block_get('E-09'))
_m = re.search(r'\n   What the assistant can reach\. [^\n]*', _b)
if not _m: errs.append('E-09 What the assistant can reach not found')
else:
    K8 = _m.group(0).strip()
    short = ("What the assistant can reach. The assistant shares your Linux user, your clipboard and your screen, so its programs can read n8n's encryption key and, with it, the three credentials saved in n8n, and the settings of the database server and n8n. "
             "So use throwaway accounts and the throwaway database of this take only, and nowhere else. Never type a password inside a command line, even if the assistant or an error message suggests it as a way out. If anything asks you to, answer no. Detail: appendix K-8.")
    set_new('E-09', _b.replace(_m.group(0), '\n   ' + short))
    sub('\n\n## Lines checked and found consistent', '\n\nK-8 (detail of step 8, "What the assistant can reach"). ' + K8[len('What the assistant can reach. '):] + '\n\n## Lines checked and found consistent')

# ---------------------------------------------------------------- E-37 (4): own list, marks, where the key copy goes
rsub('E-37', "It is the only source of the files outside the take folder that the shred rule lets you shred (step 22 item 3, key step G); add to it whenever you save a copy later.",
     "Mark each file `old key` (it holds a copy of the secret key for the model) or `other`. It is the only source of the files outside the take folder that the shred rule lets you shred (step 22 item 3, key step G). The copy of the secret key for the model that you put in the take folder (the assistant names that folder in its message of step 8, sub-step e) is shredded by the path that the assistant gives you, as part (a); write its full path on your list too from the moment you put it there. Add to the list whenever you save a copy later.")

# ---------------------------------------------------------------- Appendix K
sub('## Appendix K: the detail of the key steps (round 16)\nThe owner reads key steps A to K in row E-48. Where a key step says "Detail", the text is here. Nothing was deleted; the detail was moved.',
    '## Appendix K: the detail of the key steps\nThe owner reads key steps A to K in step 22 item 3 of his sheet. This appendix is the last page of the same sheet (the studio lead appends it unchanged to the end of the working copy of OWNER-STEPS together with the new text of step 22 item 3). Where a key step says "Detail", the text is here. Nothing was deleted; the detail was moved.')
sub("(step 8 asks you to; whether the key list shows the last four characters is UNVERIFIED;", "(the Phase 0 note, point (2), asks you to; whether the key list shows the last four characters is UNVERIFIED;")
sub("the removal ends the path to the copy.", "the removal ends the path to the copy. What item 1 removes with a plain remove and not with a shred (n8n's own settings folder inside the take folder, which holds n8n's encryption key, and the take's database files) may stay in free space on the disk; whether item 1 should shred them is not decided yet and is a question for the studio lead.")

# ---------------------------------------------------------------- E-62 Why
why_add('E-62', "Round 17 (security m7): the exact address `take-<id>-a@example.com` is not checked against the take program (the id rule of E-12 is the builder's choice, UNVERIFIED); if the program writes another form, the owner deletes nothing and tells the assistant, which fails closed.")

# ---------------------------------------------------------------- front matter
sub("(round 16, batched fix pass after the round 15 reviews;", "(round 17, batched fix pass after the round 16 reviews;")
sub("Round 14 (`resolve-r14.md`, same paths: no round cap) applies all of those findings in one batch. The result of round 14 is NOT reviewed yet. Earlier files are kept as `EDITS.round5.md` to `EDITS.round9.md`, `EDITS.round10a.md` (the first pass of round 10), `EDITS.round10b.md` (the second pass) `EDITS.round11.md` (round 11) and `EDITS.round12.md` (round 12) and `EDITS.round13.md` (round 13).",
    "Round 14 (`resolve-r14.md`, same paths: no round cap) applied all of those findings in one batch; its result was reviewed (`review-r14-security.md`, `review-r14-naive.md`, `review-r14-evidence.md`). Round 15 (`resolve-r15.md`) and round 16 (`resolve-r16.md`) did the same: `review-r15-security.md`, `review-r15-naive.md`, `review-r15-evidence.md`; `review-r16-security.md` (0 Blockers, 1 Major, 8 Minors), `review-r16-naive.md` (0 Blockers, 9 Majors, minors F-10 to F-15) and `review-r16-evidence.md` (6 of 14 fresh planted mistakes missed by both checkers). Round 17 (`resolve-r17.md`, same paths: no round cap) applies all of those findings in one batch. The result of round 17 is NOT reviewed yet. Earlier files are kept as `EDITS.round5.md` to `EDITS.round9.md`, `EDITS.round10a.md` (the first pass of round 10), `EDITS.round10b.md` (the second pass), and `EDITS.round11.md` to `EDITS.round16.md` (rounds 11 to 16).")
sub("so the ids run E-01 to E-58 without E-10 and E-35 (E-49 to E-53 are new in round 8, E-54 in round 9, E-55 and E-56 in round 10, E-57 and E-58 in round 11).",
    "so the ids run E-01 to E-62 without E-10 and E-35 (E-49 to E-53 are new in round 8, E-54 in round 9, E-55 and E-56 in round 10, E-57 and E-58 in round 11, E-59 to E-61 in round 15, E-62 in round 16). Appendix K (after the last row) is part of the owner sheet, not a row: the studio lead appends it unchanged to the end of the working copy of OWNER-STEPS in the same step as row E-48, and it is carried into v4 with E-48.")
sub("## Counts (computed by script, `resolve-r16.md` and `resolve-r16-check-output.txt`)", "## Counts (computed by script, `resolve-r17.md` and `resolve-r17-check-output.txt`)")
sub("Round 16 added E-62 (step 20", "Round 17 added no row (the ids and the counts do not change). It rewrote E-48 (one order, one list of start conditions, one confirmation rule, one number of minutes), E-09 (the text on what the assistant can reach moved to Appendix K-8), E-12, E-16, E-37, E-55 and E-57, added NOT DECIDED 16 and the confirmation r, and changed the rule R7 and the confirmation h. Round 16 added E-62 (step 20")
sub("## NOT DECIDED: studio lead or owner only (items 1 to 15).", "## NOT DECIDED: studio lead or owner only (items 1 to 16).")
_nd15 = [l for l in T.split('\n') if l.startswith('15. **When the owner writes `no more takes`')]
if len(_nd15) != 1: errs.append('ND15 line')
else:
    ND16 = ("16. **Nobody but the owner can cancel the secret key for the model, and nothing limits what it can spend if he cannot be reached** (E-48 key steps A, C, I and K; security N1 of round 16). Who answers: the owner; the studio lead helps to check option (1). "
            "Facts: key step A is a promise by the owner backed by his three alarms; the program has no timer; all three alarms are on one person's device; if the alarms are missed the key stays alive, together with its copy in the take folder, n8n's encryption key and the saved credentials on the laptop; the spending cap of the model stage protects the program, not a copied or leaked key; a search of the inputs found no spending limit set at the company that provides the AI model (the company's own page was not checked). The exposure is longer in route B (up to five days). "
            "Options, not decided by the builder: (1) make the key inside a project or workspace at the company that provides the AI model, with a spending limit of its own that equals the cap of the take; cost: no money known, some set-up time; risk: UNVERIFIED that the company offers it and that the limit stops a leaked key; (2) name a second person who may revoke the key when the owner cannot be reached; cost: that person gets access to the key list at the provider account, which widens who can act; risk: one more identity to protect; (3) the owner accepts the exposure in writing. "
            "The accepted-risk sentence for option (3), which the owner types himself as a new message: `I accept that until I revoke the secret key for the model it can spend up to what my account at the company allows, that only I can revoke it, and that if I miss my alarms it stays alive.` "
            "Default: not chosen; until an answer exists the owner text states the exposure (key step A, D.1 and step 21) and hides nothing. Record: `ND16: 1|2|3 <owner message>`.")
    T = T.replace(_nd15[0], _nd15[0] + '\n' + ND16)
sub("letters run a to q without gaps)", "letters run a to r without gaps)")
sub("CONFIRMED by the studio lead (ORDERS.md, \"LEAD ANSWERS to your 15:49Z QUESTIONS block\", item L-23NOV, 2026-11-16): latest start we plan 18:04 UTC = 23:34 IST (Mon 23 Nov 2026), key revoked by 18:19 UTC = 23:49 IST even if a take runs, no take planned on 23 Nov (the take targets Wed 18 Nov).",
    "The studio lead's item L-23NOV (ORDERS.md, \"LEAD ANSWERS to your 15:49Z QUESTIONS block\", 2026-11-16) gave the latest start we plan 18:04 UTC = 23:34 IST; that figure is REPLACED by 18:00 UTC = 23:30 IST (see o). The rest of L-23NOV stands: key revoked by 18:19 UTC = 23:49 IST even if a take runs, no take planned on 23 Nov (the take targets Wed 18 Nov).")
_q = [l for l in T.split('\n') if l.startswith('q. Round 16 additions of the builder, to confirm:')]
if len(_q) != 1: errs.append('confirmation q line')
else:
    R_ = ("r. Round 17 additions of the builder, to confirm: (1) `key revoked` never confirms anything; at the last time to revoke the owner revokes and writes `key gone, no more decisions` (security r16 minors 2 and 3; naive F-8; this REPLACES the round 16 rule that a `key revoked` typed after 18:19 UTC = 23:49 IST counts); (2) the reply `more takes` is now `another take` (it was one word apart from `no more takes`) and `shred done 1` and `shred done 2` are now `shred done key copies` and `shred done other files` (naive F-8); (3) one number, 30 minutes, for making new keys (naive F-4); (4) between 18:19 UTC = 23:49 IST and 18:29 UTC = 23:59 IST only the shred of the key copies fits; the other owner items are listed in the handoff with a date if they are not done by 18:29 UTC = 23:59 IST, although the input's item 3 says to delete the HubSpot apps by 18:29 UTC = 23:59 IST (naive F-8); is that acceptable, or is a later finish for items 2 to 6 allowed on the last day; (5) Appendix K is appended unchanged to the end of the working copy (naive F-2); (6) alarm 3 yields to a running take (naive F-3); (7) the retire check (item 5) comes after the HubSpot apps are deleted (card step 4 after step 3): confirm that item 5 does not need the HubSpot read key (naive F-15; UNVERIFIED); (8) NOT DECIDED 16 is new (security N1).")
    T = T.replace(_q[0], _q[0] + '\n\n' + R_)
sub("in the order of the card (key step C).", "in the order of the card (step 22 item 3, the card).")

# ---------------------------------------------------------------- why lines (history)
why_add('E-48', "Round 17 (security N1, minors 1 to 6; naive F-1 to F-9, F-15; evidence r16): (a) the seven steps of the one order are ONE wording, used in the card, E-16 and E-55, and the start conditions of item 1 are ONE sentence used in key step G.2, E-16 and E-55; (b) a confirmation is exactly `yes, no more takes` or `key gone, no more decisions`; `key revoked` never confirms (the round 16 rule of a counted `key revoked` after 18:19 is gone, so the owner who obeys key step I is not left with an uncounted word); (c) alarm 3 yields to a running take; (d) 30 minutes is the one number for making new keys; (e) D.4 and key step E follow the order of the actions; (f) `more takes` became `another take`; `shred done 1` and `shred done 2` became `shred done key copies` and `shred done other files`; (g) a bare `no` is explained in key step F; (h) key step G is for every shred in the item and in step 8, parts (b) and (d) are told apart by the marks `old key` and `other`; (i) the exposure of route B is in D.1 and E-57; key step A says that the cap of the stage does not limit a copied key; (j) the clock for 18:29 is the time shown on the owner's last message; (k) 10 minutes after the last time to revoke fit only the shred of the key copies; (l) n8n.env and the nano backup copy go on the owner's own list.")
why_add('E-16', "Round 17 (naive F-1, F-6, F-7; security minor 3): the order is the card's seven steps in the same words; the start conditions are the one sentence of key step G.2; the copy of the result file is made in the assistant's next message after the confirmation, before any shred, and checked at the start of item 1; the final sentence no longer says that the assistant reports before the owner's items; the take root is described apart from the take folder.")
why_add('E-55', "Round 17 (naive F-1, F-7, F-13; security minors 2 and 3): the heading is one short line and the old sentences are the first line of the body; the confirmation is exactly two messages; the order and the start conditions are the same words as in the card and E-16.")
why_add('E-57', "Round 17 (naive F-2): the exposure of route B (a live key and its copy for up to five days; route A is safer) is in the owner text of step 21.")
why_add('E-12', "Round 17 (naive F-3, F-12): alarm 3 yields to a running take; the reply is five numbered lines, two of them long (the two blocks keep their names).")
why_add('E-09', "Round 17 (security minors 4 and 5; naive F-9; r16 NOT DONE item 2): the text on what the assistant can reach is short here and complete in Appendix K-8; the nano backup copy and `n8n.env` go on the owner's own list.")
why_add('E-37', "Round 17 (r16 NOT DONE item 4; naive F-9): the own list marks each file `old key` or `other`; the copy of the key in the take folder is named and its path goes on the list.")

# ---------------------------------------------------------------- renames of reply words (not in Why lines: they record history)
_ren = [("`more takes`", "`another take`"), ("`shred done 1`", "`shred done key copies`"), ("`shred done 2`", "`shred done other files`"),
        ("`shred not done 1`", "`shred not done key copies`"), ("`shred not done 2`", "`shred not done other files`")]
_ls = T.split('\n')
for k_, l_ in enumerate(_ls):
    if l_.startswith('Why:'): continue
    for a_, b_ in _ren: l_ = l_.replace(a_, b_)
    _ls[k_] = l_
T = '\n'.join(_ls)

sub("the 10 minutes between are for the rest of the retirement.", "the 10 minutes between are only for the shred of the key copies (card step 2); the other owner items do not fit into them.")
sub("23:59 IST for the rest of the retirement.", "23:59 IST only for the shred of the key copies (card step 2).")

rsub('E-55', "and for your items 2 to 6 (deleting", "and for each of your items 2, 3, 4, 5 and 6 (deleting")
sub("you delete the HubSpot apps and the app passwords (items 2 and 3).", "you delete the HubSpot apps and the app passwords (item 3 and item 2).")
sub("and `key revoked` counts as the confirmation only after", "and `key revoked` counted as the confirmation (REPLACED in round 17: see r (1)) only after")

if errs:
    print('ERRORS', len(errs))
    for e in errs: print(' ', e)
    sys.exit(1)
open(D + 'EDITS.md', 'w', encoding='utf-8').write(T)
print('written', len(T.split('\n')), 'lines')
