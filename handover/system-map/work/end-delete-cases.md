# What `end` does: replacement text for the owner cards (lead RETRACTION of 17:46Z applied: the take never deletes)
Written 16 Nov 2026; rewritten after the lead's retraction at 17:46Z (23:16 IST). Older layouts: work/end-delete-cases-history-8.md (the 16:50Z version, withdrawn by the lead 17:46Z; ignore it; earlier ones -history-1.md to -history-7.md and -history.md). The claims "the program archives" and "the take's key can archive" are withdrawn.

## The sentence (use exactly)
"The take never deletes contacts; it lists any left behind and the owner deletes them by a filtered list."
Expected case: after `end` the program lists the three made-up contacts still in HubSpot and changes nothing. UNVERIFIED.

## Status: UNVERIFIED
1. UNVERIFIED: no one on this side has read the program (scripts/run_real_check_n8n.py, not in our checkout). Source: the lead's RETRACTION (work/LEAD-ANSWERS.md, 17:46Z). Per the lead the final program (head r38 0cead2c) has no create, update, delete or archive call on HubSpot and prints "this script only reads HubSpot and never deletes: it counts and lists them at the end and you delete them by hand" and "left in HubSpot (this take never deletes): N contact(s)". It stays UNVERIFIED until the lead's loopback re-smoke on the merged head (Tue 17 or Wed 18 Nov; result in egm/duplicate-proof-lead-desk/wp6/). Where the tag first shows on screen: UNVERIFIED.
2. The owner is the only person. studio lead = the Claude session doing the technical steps.
3. Withdrawn: the program erasing contacts with a "contacts may be deleted" release phrase (kept only in work/end-delete-cases-history-5.md); "the program archives with the take's key" and "the program tries once to archive" (withdrawn by the lead 17:46Z).

## Words
- take = the one filmed demo run on made-up data. `end` = the word the owner types to close the film pause. The program does not enforce the 10-minute pause; the owner sets his own clock alarm.
- read-only key = the take's HubSpot key: it can look, not change or delete (decision 2 of 16 Nov 2026).
- run-day card = OWNER-RUN-DAY-CARD.md, the owner's typed steps for the day of the take.
- OWNER-VIEW row 3 = the "Run day" row of the table in OWNER-VIEW.md.
- clean-up card = OWNER-CLEANUP-CARD.md, the owner's steps after the take (step I).
- by-hand list = the list the program prints after `end` of contacts still in HubSpot ("left in HubSpot (this take never deletes)"), with the search text take-<tag>-a, -b, -c (example.com).
- lead id = the id the program gives each made-up sales request; contact id = the number HubSpot gives a contact.

## Rule (per the lead, unverified)
After `end` the program only reads and lists; all three contacts are expected on the list. The owner deletes them by a filtered list, matching only the three addresses take-<tag>-a, -b, -c at example.com. If the program changes anything in HubSpot, that is a program defect: the studio lead reports it to core-hardening; it is not a card variant.

## Replacement text, and the file that holds each
- OWNER-RUN-DAY-CARD.md, heading over the pause steps: "`end` CLOSES THE PAUSE. THE TAKE NEVER DELETES CONTACTS; IT LISTS ANY LEFT BEHIND AND YOU DELETE THEM BY A FILTERED LIST."
- OWNER-RUN-DAY-CARD.md, earlier notice step: "The take never deletes contacts; it lists any left behind and the owner deletes them by a filtered list. If the notice says the program deletes or archives, type nothing and tell the studio lead."
- OWNER-RUN-DAY-CARD.md, after `end`: "The program prints the contacts left in HubSpot (expected: all three). Tell the studio lead the count and the contact ids only."
- OWNER-RUN-DAY-CARD.md, by-hand step (the owner's own action, no release phrase): "In the demo HubSpot account, open Contacts and search for take-<tag>-a, take-<tag>-b, take-<tag>-c (example.com). Delete only contacts on the program's list whose email is exactly one of those three. If the count differs from the program's list, change nothing and tell the studio lead. Deleting cannot be undone. Reply 'contacts cleaned up' and the number." The number is the count deleted by hand.
- Release words: none for contacts. "demo mails may be deleted" stays for the Gmail demo mails only.
- OWNER-VIEW.md, row 3: "The one careful moment is the film pause: typing `end` closes it. The take never deletes contacts; it lists any left behind and the owner deletes them by a filtered list."
- OWNER-CLEANUP-CARD.md: add "Leftover made-up contacts: delete them once by hand from the program's printed list (search take-<tag>-a, -b, -c, example.com); never twice."
- Other pages (LEAD-PAGE, TAKE-BLOCKERS, README, QUESTIONS, QUEUE): use the original rows in work/end-sentence-for-owners-history-1.md.

## Open items
- Lead's loopback re-smoke on the merged head (Tue 17 or Wed 18 Nov): program prints the two lines above and makes no HubSpot write: not done, UNVERIFIED.
- Key rights: settled (read-only, decision 2).
