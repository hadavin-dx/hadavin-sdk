# What `end` does: replacement text for the owner cards (lead answer 3 applied)
Written 16 Nov 2026. Older layouts: work/end-delete-cases-history-5.md (and -history.md to -history-4.md); ignore them. Where the pages that still carry old wording are listed: work/end-sentence-for-owners.md.

## The sentence (use exactly)
"The take never deletes contacts; it lists any left behind and the owner deletes them by a filtered list."

## Status
1. SETTLED by lead answer 3 (work/LEAD-ANSWERS.md, 16 Nov 2026 16:23 UTC / 21:53 IST). Not verified by reading the program: scripts/run_real_check_n8n.py is not in our checkout and was not read. The cards still must not claim more than the sentence.
2. The owner is the only person. There is no "studio head". studio lead = the Claude session doing the technical steps.
3. The old proposal (a delete design: the program deleting, a "contacts may be deleted" release phrase, steps A to F with a 15-minute wait) is withdrawn. It is kept only in work/end-delete-cases-history-5.md.

## Words
- end = the word the owner types to close the film pause. The pause = the moment the program waits after the 3 made-up contacts exist so the owner can film HubSpot.
- filtered list = the HubSpot contact list narrowed to the made-up test addresses of this run (take-<run name>-a@example.com, -b@, -c@), so only those contacts are ticked.
- lead id = the id the program gives each made-up sales request; contact id = the number HubSpot gives a contact.

## Rule
`end` only closes the pause. The program deletes nothing and archives nothing. It prints the made-up contacts still in HubSpot (lead id and contact id). The owner deletes any left behind by a filtered list. If the program ever deletes a contact, that is a program defect: the studio lead reports it to core-hardening; it is not a card variant.

## Replacement text for the pause part of the run-day card
- Heading over the pause steps: "`end` ONLY CLOSES THE PAUSE (it deletes nothing)".
- Earlier notice step: "Up to 3 made-up contacts are left in HubSpot for you to delete by a filtered list."
- After `end`: "The program lists the made-up contacts still in HubSpot. Tell the studio lead the count and the contact ids only (addresses replaced by X)."
- Delete step (the owner's own action, no release phrase): "In the demo HubSpot account, open Contacts and filter by the three test addresses of this run. Tick only contacts whose email is exactly one of them, then More, Delete. If the count differs from the program's list, delete nothing and tell the studio lead. Deleting cannot be undone. Reply 'contacts deleted' and the number."
- Release words: none for contacts, because the program deletes nothing. "demo mails may be deleted" stays for the Gmail demo mails only.
- OWNER-VIEW row 3: "The one careful moment is the film pause: typing `end` closes it. The take never deletes contacts; it lists any left behind and you delete them by a filtered list."
- Clean-up card: add "Leftover made-up contacts: delete them by the filtered list from the run-day card, once; never twice."

## Caution
Rests on lead answer 3, not on a read of the program. The quoted-lines check of older versions is no longer a condition.
