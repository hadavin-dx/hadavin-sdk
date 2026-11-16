# What `end` does: replacement text for the owner cards (decision 2 applied). Written 16 Nov 2026 about 10:15 UTC / 15:45 IST; rewritten about 12:05 UTC / 17:35 IST after a cold read. Status: NOT applied to any card. UNVERIFIED against the program: nobody has read scripts/run_real_check_n8n.py for this. Verifier: the studio lead (read the program), time not set; the studio lead will send it.

Words: **the pause** = the moment the program waits after the 3 made-up contacts exist so the owner can film HubSpot. **lead key** = the made-up lead's own id in the take. **contact id** = the number HubSpot gives a contact. **run name** = the short name the owner picks fresh for each run. **release word** = the exact words the studio lead writes in chat before the owner may do a step. **core-hardening** = the other cloud session that owns v5 (the steps file) and the program text. **QUESTIONS item 1** = the first question in QUESTIONS.md, now answered by decision 2.

Rule (decision 2 of inputs/DECISIONS-2026-11-16.md): `end` only closes the pause and deletes nothing. The owner deletes leftover made-up contacts by hand. The old option "`end` deletes the contacts" (case B) is WITHDRAWN. If the program still deletes, that is a program defect: the studio lead reports it to core-hardening; it is not a card variant.

Files that still say "end deletes up to 3 contacts" (core-hardening or the studio lead must change them; not mine): v5 lines 114, 124-130, 137; OWNER-RUN-DAY-CARD steps 9, 13-16; OWNER-VIEW row 3 and line 8; the program's own notice; OWNER-CLEANUP-CARD has no leftover-contact step.

Replacement text:
- Run-day step 9: "Up to 3 made-up contacts are left for you to delete by hand." Heading of steps 13-15: "`end` ONLY CLOSES THE PAUSE (it deletes nothing)".
- Run-day step 15 (new, STOP step): "`end` has closed the pause. The made-up contacts are still in HubSpot. Do nothing until the studio lead writes 'contacts may be deleted' in chat."
- Run-day step 16 (new): "The studio lead sends a list in chat: lead id (the number the program gives each made-up test person) and HubSpot contact id for each leftover contact, at most 3, ids only, no names or addresses. The studio lead sends it by <HH:MM> UTC / <HH:MM> IST (time not set; the studio head fills it). Delete only the listed contacts, by hand."
- Run-day step 17 (new): "Reply in chat: 'contacts deleted: N'."
- Release word (the one trigger for contact deletes; step 15 and this line now agree): the owner's contact delete uses the studio lead's words "contacts may be deleted" (new). The existing word "demo mails may be deleted" stays for the Gmail demo mails. Two words, two jobs; the studio lead confirms.
- OWNER-VIEW row 3: "The one careful moment is the film pause: typing `end` closes it and deletes nothing; afterwards you delete the listed contacts by hand."
- OWNER-VIEW line 8: add "step 7b: the studio lead sends the contact list; you delete the listed contacts and reply 'contacts deleted: N'."
- Clean-up card: new step 3a: "STOP. Do this only if the studio lead wrote 'contacts may be deleted'. Delete only the contacts the studio lead listed. Reply 'contacts deleted: N'."

Note (digest 380): UNVERIFIED whether the program deletes anything. These texts say `end` deletes nothing only because decision 2 says so; do not put them on a card until someone has read the program. Use 'lead id', not 'lead key' (a key reads as a secret).
