# What `end` does: replacement text for the owner cards (lead answer 3 applied)
Written 16 Nov 2026. Older layouts: work/end-delete-cases-history-6.md (and -history.md to -history-5.md); ignore them. Pages that still carry old wording: work/end-sentence-for-owners.md.

## The sentence (use exactly)
"The take never deletes contacts; it lists any left behind and the owner deletes them by a filtered list."

## Status: UNVERIFIED
1. UNVERIFIED: no one on this side has read the program. Source: the lead's answer 3 (work/LEAD-ANSWERS.md, 16:23Z, 16 Nov 2026 / 21:53 IST). The program is scripts/run_real_check_n8n.py; it is not in our checkout. Before filming, run it with a test contact and confirm no delete call. Statements below about what the program does are "per the lead's answer 3, unverified". The cards must not claim more than the sentence.
2. The owner is the only person. studio lead = the Claude session doing the technical steps.
3. The old proposal (the program deleting, a "contacts may be deleted" release phrase, steps A to F with a 15-minute wait) is withdrawn. It is kept only in work/end-delete-cases-history-5.md.

## Words
- take = the one filmed demo run on made-up data. `end` = the word the owner types to close the film pause. The pause = the moment the program waits after the 3 made-up contacts exist so the owner can film HubSpot.
- run-day card = OWNER-RUN-DAY-CARD.md, the owner's typed steps for the day of the take.
- OWNER-VIEW row 3 = row 3 of the table in OWNER-VIEW.md (the plan page for the owner): the "Run day" row.
- clean-up card = OWNER-CLEANUP-CARD.md, the owner's steps after the take (step I).
- filtered list = the HubSpot contact list narrowed to emails starting with take-<run name>- (the three are take-<run name>-a@example.com, -b@example.com, -c@example.com), so only those contacts are ticked. Where the run name is shown in HubSpot: NOT KNOWN; the lead must name it.
- lead id = the id the program gives each made-up sales request; contact id = the number HubSpot gives a contact.

## Rule (per the lead's answer 3, unverified)
`end` only closes the pause. The program deletes nothing and archives nothing. It prints the made-up contacts still in HubSpot (lead id and contact id). The owner deletes any left behind by a filtered list. If the program ever deletes a contact, that is a program defect: the studio lead reports it to core-hardening (the Claude session that owns the take code); it is not a card variant.

## Replacement text, and the file that holds each
- OWNER-RUN-DAY-CARD.md, heading over the pause steps: "`end` ONLY CLOSES THE PAUSE (it deletes nothing)".
- OWNER-RUN-DAY-CARD.md, earlier notice step: "All 3 made-up contacts are left in HubSpot for you to delete by a filtered list, unless you have already deleted them."
- OWNER-RUN-DAY-CARD.md, after `end`: "The program lists the made-up contacts still in HubSpot. Tell the studio lead the count and the contact ids only." (No sample of masked addresses exists in our files, so no "replaced by X" phrase is used.)
- OWNER-RUN-DAY-CARD.md, delete step (the owner's own action, no release phrase): "In the demo HubSpot account, open Contacts and filter by emails starting with take-<run name>-. Tick only contacts whose email is exactly one of the three test addresses of this run, then More, Delete. If the count differs from the program's list, delete nothing and tell the studio lead. Deleting cannot be undone. Reply 'contacts deleted' and the number." The number is the count of contacts the owner deleted.
- Release words: none for contacts. "demo mails may be deleted" stays for the Gmail demo mails only.
- OWNER-VIEW.md, row 3: "The one careful moment is the film pause: typing `end` closes it. The take never deletes contacts; it lists any left behind and you delete them by a filtered list."
- OWNER-CLEANUP-CARD.md: add "Leftover made-up contacts: delete them by the filtered list from the run-day card, once; never twice."

## Open items
- Run the program with a test contact and confirm no delete call: not done.
- Where the run name is shown in HubSpot: NOT KNOWN; the lead names it.
