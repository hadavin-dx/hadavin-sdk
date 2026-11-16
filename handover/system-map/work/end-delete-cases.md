# What `end` does: replacement text for the owner cards (decision 2 applied). Written 16 Nov 2026 about 10:15 UTC / 15:45 IST; rewritten about 12:05 UTC / 17:35 IST after a cold read. Status: NOT applied to any card. UNVERIFIED against the program: nobody has read scripts/run_real_check_n8n.py for this. Verifier: the studio lead (read the program), time not set; the studio lead will send it.

Words: **the pause** = the moment the program waits after the 3 made-up contacts exist so the owner can film HubSpot. **lead key** = the made-up lead's own id in the take. **contact id** = the number HubSpot gives a contact. **run name** = the short name the owner picks fresh for each run. **release word** = the exact words the studio lead writes in chat before the owner may do a step. **core-hardening** = the other cloud session that owns v5 (the steps file) and the program text. **QUESTIONS item 1** = the first question in QUESTIONS.md, now answered by decision 2.

Rule (decision 2 of inputs/DECISIONS-2026-11-16.md): `end` only closes the pause and deletes nothing. The owner deletes leftover made-up contacts by hand. The old option "`end` deletes the contacts" (case B) is WITHDRAWN. If the program still deletes, that is a program defect: the studio lead reports it to core-hardening; it is not a card variant.

Files that still say "end deletes up to 3 contacts" (core-hardening or the studio lead must change them; not mine): v5 lines 114, 124-130, 137; OWNER-RUN-DAY-CARD steps 9, 13-16; OWNER-VIEW row 3 and line 8; the program's own notice; OWNER-CLEANUP-CARD has no leftover-contact step.

Replacement text:
- Run-day step 9: "Up to 3 made-up contacts are left for you to delete by hand." Heading of steps 13-15: "`end` ONLY CLOSES THE PAUSE (it deletes nothing)".
- Run-day step 15 (new, STOP step): "STOP. `end` has closed the pause. The made-up contacts are still in HubSpot. Do nothing. Wait for the studio lead's chat message with the list. If no list arrives within 15 minutes of your `end` (look at the clock), message the studio lead and delete nothing."
- Run-day step 16 (new): "The studio lead's list gives, for each leftover contact, the lead id (the number the program gives each made-up test person; the program may print it as 'lead key') and the HubSpot contact id, at most 3, ids only, no names or addresses. The message shows its send time in UTC and IST."
- Run-day step 17 (STOP): "STOP. Wait for the exact words 'contacts may be deleted'. The studio lead writes them only after sending the list. Do not accept a similar phrase such as 'demo mails may be deleted'; that one is for Gmail mails only."
- Run-day step 18: "In the demo HubSpot account (the studio lead names it in the list message; never write its number in chat), open one listed contact by its contact id. Read its lead id. If it differs from the list, STOP: do not delete, tell the studio lead."
- Run-day step 19: "STOP. Deleting cannot be undone. Click Delete on that one contact only. Then go back to step 18 for the next listed contact."
- Run-day step 20: "Reply in chat: 'contacts deleted: N of M' (M = contacts on the list; N may be 0). If a listed contact is missing, delete nothing more and tell the studio lead."
- Release word (step 17 and this line agree): the one trigger is step 17: the owner's contact delete uses the studio lead's words "contacts may be deleted" (new). The existing word "demo mails may be deleted" stays for the Gmail demo mails. Two words, two jobs; the studio lead confirms.
- OWNER-VIEW row 3: "The one careful moment is the film pause: typing `end` closes it and deletes nothing; afterwards you delete the listed contacts by hand."
- OWNER-VIEW (the order-of-messages paragraph): add "step 7b: the studio lead sends the contact list; you delete the listed contacts and reply 'contacts deleted: N'."
- Clean-up card: new step 3a (only if the run-day steps 15 to 20 were not already done; they are the same deletes, never do them twice): "STOP. Do this only if the studio lead wrote 'contacts may be deleted'. Delete only the contacts the studio lead listed. Reply 'contacts deleted: N'."

Note (digest 380): UNVERIFIED whether the program deletes anything. These texts say `end` deletes nothing only because decision 2 says so; do not put them on a card until someone has read the program. Use 'lead id', not 'lead key' (a key reads as a secret).
