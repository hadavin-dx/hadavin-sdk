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
